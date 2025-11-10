from unittest import TestCase

from growbies.device.common.calibration import Calibration, Calibration2

class Test(TestCase):
    def test(self):
        cal = Calibration()

        matrix = list()
        counter = 0
        for row in range(Calibration.MASS_SENSOR_COUNT):
            matrix.append(list())
            for col in range(Calibration.MAX_COEFF_COUNT):
                matrix[row].append(counter)
                counter += 1

        cal.mass_temp_coeff = matrix

        self.assertEqual(matrix, cal.mass_temp_coeff)
        self.assertAlmostEqual(cal.mass_temp_coeff[0][0], 0)
        self.assertAlmostEqual(cal.mass_temp_coeff[1][0], Calibration.MAX_COEFF_COUNT)
        self.assertAlmostEqual(cal.mass_temp_coeff[0][-1], Calibration.MAX_COEFF_COUNT - 1)
        self.assertAlmostEqual(cal.mass_temp_coeff[-1][-1],
                               (Calibration.MASS_SENSOR_COUNT * Calibration.MAX_COEFF_COUNT) - 1)

    def test2(self):
        cal = Calibration2()

        matrix = list()
        counter = 0
        for row in range(Calibration2.MASS_SENSOR_COUNT):
            matrix.append(list())
            for col in range(Calibration2.MAX_COEFF_COUNT):
                matrix[row].append(counter)
                counter += 1

        cal.mass_temp_coeff = matrix

        self.assertEqual(matrix, cal.mass_temp_coeff)
        self.assertAlmostEqual(cal.mass_temp_coeff[0][0], 0)
        self.assertAlmostEqual(cal.mass_temp_coeff[1][0], Calibration2.MAX_COEFF_COUNT)
        self.assertAlmostEqual(cal.mass_temp_coeff[0][-1], Calibration2.MAX_COEFF_COUNT - 1)
        self.assertAlmostEqual(cal.mass_temp_coeff[-1][-1],
                               (Calibration2.MASS_SENSOR_COUNT * Calibration2.MAX_COEFF_COUNT) - 1)