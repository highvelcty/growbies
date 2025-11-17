from unittest import TestCase
import ctypes

from growbies.device.common.calibration import (Calibration, CalibrationHdr, NvmCalibration,
                                                SensorCalibration)
from growbies.device.common.nvm import NvmHdr

class Test(TestCase):
    def test_calibration_hdr(self):
        hdr = CalibrationHdr()
        self.assertEqual(hdr.mass_sensor_count, hdr.MAX_MASS_SENSOR_COUNT)
        self.assertEqual(hdr.coeff_count, hdr.MAX_COEFFS_COUNT)
        self.assertEqual(hdr.ref_temperature, hdr.REF_TEMPERATURE)

    def test_calibration(self):
        exp = """\
+--------------------------------------------------------------------------+
|                      Mass Calibration Coefficients                       |
+--------+----------+----------+----------+----------+----------+----------+
| Sensor | M Off    | M Slope  | T Slope  | M x T    | T^2      | M^2      |
+--------+----------+----------+----------+----------+----------+----------+
| 0      | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 1      | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2      | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 3      | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 4      | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
+--------+----------+----------+----------+----------+----------+----------+"""
        cal = Calibration()
        self.assertEqual(exp, str(cal))
        cal.hdr.coeff_count = 4
        exp = """\
+----------------------------------------------------+
|           Mass Calibration Coefficients            |
+--------+----------+----------+----------+----------+
| Sensor | M Off    | M Slope  | T Slope  | M x T    |
+--------+----------+----------+----------+----------+
| 0      | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 1      | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2      | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 3      | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 4      | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
+--------+----------+----------+----------+----------+"""
        self.assertEqual(exp, str(cal))

        cal.hdr.mass_sensor_count = 3
        exp = """\
+----------------------------------------------------+
|           Mass Calibration Coefficients            |
+--------+----------+----------+----------+----------+
| Sensor | M Off    | M Slope  | T Slope  | M x T    |
+--------+----------+----------+----------+----------+
| 0      | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 1      | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2      | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
+--------+----------+----------+----------+----------+"""
        self.assertEqual(exp, str(cal))

    def test_calibration_setting(self):
        cal = Calibration()

        for sensor in range(cal.hdr.mass_sensor_count):
            cal.sensor[sensor].coeffs.mass_offset = float(sensor)
            cal.sensor[sensor].raw[1] = float(sensor)
            cal.sensor[sensor].coeffs.temperature_slope = float(sensor)
        exp = """\
+--------------------------------------------------------------------------+
|                      Mass Calibration Coefficients                       |
+--------+----------+----------+----------+----------+----------+----------+
| Sensor | M Off    | M Slope  | T Slope  | M x T    | T^2      | M^2      |
+--------+----------+----------+----------+----------+----------+----------+
| 0      | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| 1      | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.000000 |
| 2      | 2.000000 | 2.000000 | 2.000000 | 0.000000 | 0.000000 | 0.000000 |
| 3      | 3.000000 | 3.000000 | 3.000000 | 0.000000 | 0.000000 | 0.000000 |
| 4      | 4.000000 | 4.000000 | 4.000000 | 0.000000 | 0.000000 | 0.000000 |
+--------+----------+----------+----------+----------+----------+----------+"""
        self.assertEqual(exp, str(cal))

    def test_sizes(self):
        exp_hdr_size = 8
        exp_coeffs_size = 24
        exp_cal_size = exp_hdr_size + (exp_coeffs_size * CalibrationHdr.MAX_MASS_SENSOR_COUNT)
        exp_nvm_hdr_size = 8
        exp_nvm_cal_size = exp_nvm_hdr_size + exp_cal_size
        self.assertEqual(exp_hdr_size, ctypes.sizeof(CalibrationHdr))
        self.assertEqual(exp_coeffs_size, ctypes.sizeof(SensorCalibration))
        self.assertEqual(exp_cal_size, ctypes.sizeof(Calibration))
        self.assertEqual(exp_nvm_hdr_size, ctypes.sizeof(NvmHdr))
        self.assertEqual(exp_nvm_cal_size, ctypes.sizeof(NvmCalibration))
