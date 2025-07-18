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

    def set_phase_a(self):
        cmd = command.CmdSetPhase()
        cmd.phase = command.Phase.A
        self.execute(cmd)

    def set_phase_b(self):
        cmd = command.CmdSetPhase()
        cmd.phase = command.Phase.B
        self.execute(cmd)

    def get_calibration(self) -> command.Calibration:
        resp: command.RespGetCalibration = self.execute(command.CmdGetCalibration())
        return resp.calibration

    def power_on_hx711(self) -> None:
        self.execute(command.CmdPowerOnHx711())

    def power_off_hx711(self) -> None:
        self.execute(command.CmdPowerOffHx711())

    def set_mass_coefficients(self, sensor: int, *coefficients):
        calibration = self.get_calibration()
        calibration.set_sensor_data(command.Calibration.Field.MASS_COEFFICIENT, sensor, *coefficients)
        cmd = command.CmdSetCalibration()
        cmd.calibration = calibration
        self.execute(cmd)

    def set_temperature_coefficients(self, sensor: int, *coefficients):
        calibration = self.get_calibration()
        calibration.set_sensor_data(command.Calibration.Field.TEMPERATURE_COEFFICIENT, sensor, *coefficients)
        cmd = command.CmdSetCalibration()
        cmd.calibration = calibration
        self.execute(cmd)

    def set_tare(self, sensor: int, tare_idx: int, value):
        calibration = self.get_calibration()
        mod_values = calibration.tare[sensor]
        mod_values[tare_idx] = value
        calibration.set_sensor_data(command.Calibration.Field.TARE, sensor, *mod_values)
        cmd = command.CmdSetCalibration()
        cmd.calibration = calibration
        self.execute(cmd)

    def read_dac(self, times: int = command.CmdReadDAC.DEFAULT_TIMES) \
            -> command.RespMultiDataPoint:
        cmd = command.CmdReadDAC(times=times)
        resp: command.RespMultiDataPoint = self.execute(cmd, read_timeout_sec=10)
        return resp

    def read_units(self, times: int = command.CmdReadUnits.DEFAULT_TIMES) \
            -> command.RespMultiDataPoint:
        cmd = command.CmdReadUnits(times=times)
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

    def test(self):
        resp: command.RespLong = self.execute(command.CmdTest())
        return resp.data

    def wait_for_ready(self):
        cmd = command.CmdLoopback()
        resp: Optional[command.RespVoid] = self.execute(cmd, retries=self.READY_RETRIES)
        if resp is None:
            raise ConnectionError(f'Arduino serial port was not ready with {self.READY_RETRIES} '
                                  f'retries, {self.READY_RETRY_DELAY_SEC} second delay per retry.')
