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
            return None

    def power_on_hx711(self) -> None:
        self.execute(command.CmdPowerOnHx711())

    def power_off_hx711(self) -> None:
        self.execute(command.CmdPowerOffHx711())

    def get_calibration(self) -> command.Calibration:
        resp: command.RespGetCalibration = self.execute(command.CmdGetCalibration())
        return resp.calibration


    def set_mass_temperature_coeff(self, sensor: int, *coeff):
        cmd = command.CmdSetCalibration()
        cmd.calibration = self.get_calibration()
        cmd.calibration.set_sensor_data(command.Calibration.Field.MASS_TEMPERATURE_COEFF, sensor,
                                    *coeff)
        self.execute(cmd)

    def set_mass_coeff(self, *coeff):
        cmd = command.CmdSetCalibration()
        cmd.calibration = self.get_calibration()
        cmd.calibration.mass_coeff = coeff
        self.execute(cmd)

    def set_tare(self, tare_idx: int, value: float):
        cmd = command.CmdSetCalibration()
        cmd.calibration = self.get_calibration()
        mod_values = cmd.calibration.tare
        mod_values[tare_idx] = value
        cmd.calibration.tare = mod_values
        self.execute(cmd)

    def read_dac(self, times: int = 1):
        return self.read_units(times, command.Unit.UNIT_MASS_DAC | command.Unit.UNIT_TEMP_DAC)

    def read_units(self, times: int = command.CmdReadUnits.DEFAULT_TIMES,
                   units: command.Unit = command.Unit.UNIT_GRAMS | command.Unit.UNIT_CELSIUS) \
            -> command.RespMultiDataPoint:
        cmd = command.CmdReadUnits(times=times, units=units)
        resp: command.RespMultiDataPoint = self.execute(cmd, read_timeout_sec=10)
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
