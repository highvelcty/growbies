from typing import Optional
import logging
import time

from .transport import ArduinoTransport
from .structs import command

logger = logging.getLogger(__name__)


class Arduino(ArduinoTransport):
    EXEC_RETRIES = 3

    RESET_COMMUNICATION_LOOPS = 3
    RESET_COMMUNICATION_LOOP_DELAY = 0.33
    MANUAL_CALIBRATION_SAMPLES = 25
    SET_BASE_OFFSET_TIMEOUT_SEC = 15

    def execute(self, cmd: command.TBaseCommand, *,
                retries: int = EXEC_RETRIES,
                read_timeout_sec: int = ArduinoTransport.DEFAULT_READ_TIMEOUT_SEC) \
            -> Optional[command.TBaseResponse]:
        for retry in range(retries):
            if retry:
                logger.error(f'Execution layer attempt {retry+1}/{self.EXEC_RETRIES}')
                self.reset_communication()

            # Send
            self._send_cmd(cmd)

            # Receive
            resp = self._recv_resp(read_timeout_sec=read_timeout_sec)
            if resp is None:
                logger.error(f'Execution layer no response.')
            elif isinstance(resp, command.RespError):
                logger.error(f'Execution layer error response 0x{resp.error:04X} received.')
            else:
                return resp
        else:
            logger.error(f'Execution layer retries exhausted executing command:\n{cmd}')
            return None

    def get_tare(self) -> list[int]:
        resp: command.RespGetTare = self.execute(command.CmdGetTare())
        return resp.offset

    def set_tare(self):
        self.execute(command.CmdSetTare(), read_timeout_sec=self.SET_BASE_OFFSET_TIMEOUT_SEC)

    def get_scale(self) -> float:
        return self.execute(command.CmdGetScale()).data

    def set_scale(self, scale: float = command.CmdSetScale.DEFAULT_SCALE):
        self.execute(command.CmdSetScale(scale=scale))

    def read_dac(self, times: int = command.CmdReadDAC.DEFAULT_TIMES) \
            -> command.RespMassDataPoint:
        cmd = command.CmdReadDAC(times=times)
        resp: command.RespMassDataPoint = self.execute(cmd, read_timeout_sec=10)
        return resp

    def read_grams(self, times: int = command.CmdReadDAC.DEFAULT_TIMES) \
            -> command.RespMassDataPoint:
        cmd = command.CmdReadGrams(times=times)
        resp: command.RespMassDataPoint = self.execute(cmd, read_timeout_sec=10)
        return resp

    def reset_communication(self):
        for _ in range(self.RESET_COMMUNICATION_LOOPS):
            self._slip_send_end()

            startt = time.time()
            while time.time() - startt < self.RESET_COMMUNICATION_LOOP_DELAY:
                bytes_in_waiting = self.in_waiting
                if bytes_in_waiting:
                    _ = self.read(bytes_in_waiting)

    def wait_for_ready(self):
        cmd = command.CmdLoopback()
        resp: Optional[command.RespVoid] = self.execute(cmd, retries=self.READY_RETRIES)
        if resp is None:
            raise ConnectionError(f'Arduino serial port was not ready with {self.READY_RETRIES} '
                                  f'retries, {self.READY_RETRY_DELAY_SEC} second delay per retry.')
