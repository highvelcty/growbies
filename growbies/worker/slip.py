"""
An LSB-first implementation of SLIP with a two byte CRC.

See: https://en.wikipedia.org/wiki/Serial_Line_Internet_Protocol
"""
import ctypes
from abc import ABC, abstractmethod
from typing import Optional
import logging
import threading
import time
import queue

import serial

from growbies.device.cmd import TDeviceCmd, CmdPacketHdr
from growbies.device.resp import TDeviceResp, DeviceRespOp, RespPacketHdr
from growbies.session import log
from growbies.utils.bufstr import BufStr
from growbies.utils.crc import crc_ccitt16
from growbies.utils.report import format_dropped_bytes

logger = logging.getLogger(__name__)

SLIP_END = 0xC0
SLIP_ESC = 0xDB
SLIP_ESC_END = 0xDC
SLIP_ESC_ESC = 0xDD

class BaseDataLink(threading.Thread, ABC):
    # In normal operation, it is expected that no more than 1-2 frames are typically outstanding.
    # This will buffer some history if the consumer becomes outpaced, but this is only expected
    # in an exception case.
    _Q_SIZE = 64
    _MAX_FRAME_BYTES = 4096
    _SERIAL_POLLING_INTERVAL_SECONDS = 0.1
    _JOIN_TIMEOUT_SECONDS = 3

    @abstractmethod
    def __init__(self, thread_name: Optional[str] = None):
        super().__init__()
        self._thread_name = thread_name
        self._frames: queue.Queue[bytearray] = queue.Queue(maxsize=self._Q_SIZE)
        self._do_continue = True
        # Prevent log flooding.
        self._do_log_queue_full = True

    @abstractmethod
    def close(self):
        ...

    @property
    @abstractmethod
    def in_waiting(self) -> int:
        ...

    @abstractmethod
    def read(self, size=1):
        ...

    @abstractmethod
    def write(self, data: bytes):
        ...

    def recv_frame(self, block=True, timeout: Optional[float] = None) -> memoryview:
        return memoryview(self._frames.get(block=block, timeout=timeout))

    def send_frame(self, buf: bytes):
        encoded = bytearray()

        if not buf:
            return  # do not send empty frames

        for byte_ in buf:
            if byte_ == SLIP_END:
                encoded.extend([SLIP_ESC, SLIP_ESC_END])
            elif byte_ == SLIP_ESC:
                encoded.extend([SLIP_ESC, SLIP_ESC_ESC])
            else:
                encoded.append(byte_)
        encoded.append(SLIP_END)
        self.write(encoded)

    def stop(self):
        self._do_continue = False
        self.join(self._JOIN_TIMEOUT_SECONDS)
        if self.is_alive():
            logger.error(f'Thread did not die after {self._JOIN_TIMEOUT_SECONDS} seconds.')
        self.close()

    def run(self):
        if self._thread_name:
            log.thread_local.name = self._thread_name

        buf = bytearray()
        escaping = False

        logger.info(f'Thread start.')

        while self._do_continue:
            try:
                if self.in_waiting:
                    chunk = self.read(self.in_waiting)
                else:
                    time.sleep(self._SERIAL_POLLING_INTERVAL_SECONDS)
                    continue

                mv_chunk = memoryview(chunk)

                for byte_ in mv_chunk:
                    if len(buf) >= self._MAX_FRAME_BYTES:
                        logger.warning(f'Slip buffer overflow. Dropping data: '
                                       f'{format_dropped_bytes(buf)}')
                        buf.clear()
                    if byte_ == SLIP_END:
                        self._put_not_wait(buf)
                        buf.clear()
                        escaping = False
                    elif byte_ == SLIP_ESC:
                        escaping = True
                    else:
                        if escaping:
                            if byte_ == SLIP_ESC_END:
                                buf.append(SLIP_END)
                            elif byte_ == SLIP_ESC_ESC:
                                buf.append(SLIP_ESC)
                            else:
                                logger.warning(f'SLIP escaping protocol violation. Expected '
                                               f'0x{SLIP_ESC_END:X} or 0x{SLIP_ESC_ESC:X},  '
                                               f'observed 0x{byte_:X}. Dropping data: '
                                               f'{format_dropped_bytes(buf)}')
                                buf.clear()
                            escaping = False
                        else:
                            buf.append(byte_)
            except serial.SerialException as err:
                logger.exception(err)
                break
        logger.info('Thread exit.')

    def _put_not_wait(self, frame: bytearray):
        try:
            # Must make a copy, otherwise clearing the buffer will propagate, even through the
            # queue.
            self._frames.put_nowait(bytearray(frame))
            self._do_log_queue_full = True
        except queue.Full:
            logger.error('SLIP queue is full.')
            self._do_log_queue_full = False
            # drop the newest frame if queue is full
            pass

class SerialDatalink(BaseDataLink):
    _RESET_COMMUNICATION_LOOPS = 3
    _RESET_COMMUNICATION_LOOP_DELAY = 3

    def __init__(self, *args, port='/dev/ttyACM0', baudrate=57600, timeout=0.5, **kw):
        """
        The following settings seem to work with arduino uno, but it also seems that they don't
        need to be set explicitly::

           dsrdtr=False, rtscts=False, xonxoff=False, parity=serial.PARITY_NONE
           bytesize=serial.EIGHTBITS, stopbits=serial.STOPBITS_ONE
        """
        super().__init__(thread_name=kw.pop('thread_name', None))
        self._serial = serial.Serial(*args, port=port, baudrate=baudrate, timeout=timeout,
                                     # dsrdtr=False, # Do not reset arduino on connect
                                     **kw)

    def close(self):
        self._serial.close()

    @property
    def in_waiting(self) -> int:
        return self._serial.in_waiting

    def read(self, size=1) -> bytes:
        return self._serial.read(size)

    def write(self, data: bytes) -> int:
        return self._serial.write(data)

class Network(BaseDataLink, ABC):
    DEBUG = True
    _CRC_BYTES = 2
    def recv_packet(self, block=True, timeout: Optional[float] = None) -> Optional[memoryview]:
        frame = super().recv_frame(block=block, timeout=timeout)
        if self._valid_crc(frame):
            return frame[:-self._CRC_BYTES]
        else:
            logger.error(f'Invalid CRC. Dropping frame: {format_dropped_bytes(frame)}')
            if self.DEBUG:
                logger.debug(BufStr(frame))
            return None

    def send_packet(self, buf: bytes):
        crc = crc_ccitt16(buf).to_bytes(self._CRC_BYTES, 'little')
        super().send_frame(buf + crc)

    def _valid_crc(self, frame: memoryview) -> bool:
        if len(frame) < self._CRC_BYTES:
            return False
        data, chk = frame[:-self._CRC_BYTES], frame[-self._CRC_BYTES:]
        calc_bytes = crc_ccitt16(data).to_bytes(self._CRC_BYTES, byteorder='little')
        return chk == calc_bytes

class Transport(Network, ABC):
    DEBUG = True
    def recv_resp(self, block=True, timeout: Optional[float] = None) \
            -> tuple[Optional[RespPacketHdr], Optional[TDeviceResp]]:
        frame = super().recv_packet(block=block, timeout=timeout)
        if frame is None:
            logger.error(f'Transport Receive None')
            return None, None

        try:
            hdr = RespPacketHdr.from_buffer(frame)
            resp = frame[ctypes.sizeof(hdr):]
        except ValueError as err:
            logger.error(f'Response packet header deserialization exception: {err}')
            return None, None

        if self.DEBUG:
            logger.debug(BufStr(bytes(hdr), title='Transport Recv Header'))
            logger.debug(BufStr(resp, title='Transport Recv Payload'))
        return hdr, DeviceRespOp.from_frame(hdr, resp)

    def send_cmd(self, cmd: TDeviceCmd):
        """
        raises:
            :class:`ServiceCmdError`
        """
        hdr = CmdPacketHdr(type=cmd.OP, version=cmd.VERSION, id=1)
        if self.DEBUG:
            logger.debug(BufStr(bytes(hdr), title='Transport Send Header'))
            logger.debug(BufStr(bytes(cmd), title='Transport Send Payload'))
        self.send_packet(bytes(hdr) + bytes(cmd))

class SerialIntf(Transport, SerialDatalink): pass
