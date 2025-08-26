import logging

from .cmd import *
from .resp import *
from .slip import Transport, SerialDatalink

logger = logging.getLogger(__name__)


class Intf(Transport, SerialDatalink):
    EXEC_RETRIES = 3

    RESET_COMMUNICATION_LOOPS = 3
    RESET_COMMUNICATION_LOOP_DELAY = 0.33
    DEFAULT_READ_TIMEOUT_SEC = 5

    def execute(self, cmd_: TDeviceCmd, *,
                retries: int = EXEC_RETRIES,
                timeout: float = DEFAULT_READ_TIMEOUT_SEC) \
            -> Optional[TDeviceResp]:
        resp_ = None
        for retry in range(retries):
            if retry:
                logger.debug(f'Execution layer attempt {retry+1}/{retries}')
                self.reset_communication()

            # Send
            self.send_cmd(cmd_)

            # Receive
            resp_ = self.recv_resp(timeout=timeout)
            if resp_:
                break
        else:
            logger.error(f'Execution layer retries {retries} exhausted executing {cmd_.type} '
                         f'command.')
        return resp_

    def power_on_hx711(self) -> None:
        self.execute(PowerOnHx711DeviceCmd())

    def power_off_hx711(self) -> None:
        self.execute(PowerOffHx711DeviceCmd())

    def get_calibration(self) -> Calibration:
        resp_: GetCalibrationDeviceRespGetCalibration = self.execute(GetCalibrationDeviceCmd())
        return resp_.calibration

    def set_mass_temperature_coeff(self, sensor: int, *coeff):
        cmd_ = SetCalibrationDeviceCmd()
        cmd_.calibration = self.get_calibration()
        cmd_.calibration.set_sensor_data(Calibration.Field.MASS_TEMPERATURE_COEFF, sensor,
                                    *coeff)
        self.execute(cmd_)

    def set_mass_coeff(self, *coeff):
        cmd_ = SetCalibrationDeviceCmd()
        cmd_.calibration = self.get_calibration()
        cmd_.calibration.mass_coeff = coeff
        self.execute(cmd_)

    def set_tare(self, tare_idx: int, value: float):
        cmd_ = SetCalibrationDeviceCmd()
        cmd_.calibration = self.get_calibration()
        mod_values = cmd_.calibration.tare
        mod_values[tare_idx] = value
        cmd_.calibration.tare = mod_values
        self.execute(cmd_)

    def get_raw_datapoint(self, times: int = 1) -> DataPointDeviceResp:
        cmd_ = GetDatapointDeviceCmd(times=times, raw=True)
        resp_: DataPointDeviceResp = self.execute(cmd_, timeout=10)
        return resp_

    def get_datapoint(self, times: int = GetDatapointDeviceCmd.DEFAULT_TIMES) \
            -> DataPointDeviceResp:
        cmd_ = GetDatapointDeviceCmd(times=times)
        resp_: DataPointDeviceResp = self.execute(cmd_, timeout=10)
        return resp_
