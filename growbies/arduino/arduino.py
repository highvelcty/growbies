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

    def manual_calibration(self):
        self.set_scale()
        self.tare()
        while True:
            value = input('Place a known weight and enter grams here:')
            try:
                value = int(value)
                break
            except ValueError:
                print('Invalid integer, please try again.')
        known_weight = self.get_units(times=self.MANUAL_CALIBRATION_SAMPLES)
        self.set_scale(value / known_weight)

    def get_channel(self) -> int:
        resp: command.RespByte = self.execute(command.CmdGetChannel())
        return resp.data

    def get_scale(self) -> float:
        return self.execute(command.CmdGetScale()).data

    def get_units(self, times: int = command.CmdGetUnits.DEFAULT_TIMES) -> int:
        resp: command.RespLong = self.execute(command.CmdGetUnits(times=times))
        return resp.data

    def power_up(self):
        cmd = command.CmdPowerUp()
        _: command.RespVoid = self.execute(cmd)

    def power_down(self):
        cmd = command.CmdPowerDown()
        _: command.RespVoid = self.execute(cmd)

    def read_median_filter_avg(self,
                               times: int = command.CmdReadMedianFilterAvg.DEFAULT_TIMES) \
            -> command.RespMassDataPoint:
        cmd = command.CmdReadMedianFilterAvg(times=times)
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

    def set_channel(self, channel: int):
        self.execute(command.CmdSetChannel(channel=channel))

    def set_gain(self, gain: command.CmdSetGain.Gain):
        self.execute(command.CmdSetGain(gain=gain))

    def set_scale(self, scale: float = command.CmdSetScale.DEFAULT_SCALE):
        self.execute(command.CmdSetScale(scale=scale))

    def tare(self, times: int = command.CmdTare.DEFAULT_TIMES):
        self.execute(command.CmdTare(times=times))


    def wait_for_ready(self):
        cmd = command.CmdLoopback()
        resp: Optional[command.RespVoid] = self.execute(cmd, retries=self.READY_RETRIES)
        if resp is None:
            raise ConnectionError(f'Arduino serial port was not ready with {self.READY_RETRIES} '
                                  f'retries, {self.READY_RETRY_DELAY_SEC} second delay per retry.')
