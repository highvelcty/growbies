import matplotlib.pyplot as plt
import numpy as np
from prettytable import PrettyTable

from growbies.db.engine import get_db_engine
from growbies.db.models import Session

class CalData:
    _REF_TEMP = 25.0

    def __init__(self, data: np.ndarray):
        self._data = data
        self._coeffs = self._fit_coeffs()

    @property
    def coeffs(self) -> 'Coeffs':
        return self._coeffs

    @property
    def ref_mass(self) -> np.ndarray:
        return self._data[:, 0]

    @property
    def temperature(self) -> np.ndarray:
        return self._data[:, 1]

    def sensor_mass(self, idx: int) -> np.ndarray:
        return self._data[:, 2 + idx]

    @property
    def n_sensors(self) -> int:
        return self._data.shape[1] - 2

    def predicted_mass(self, idx: int) -> np.ndarray:
        """Return predicted sensor mass in grams."""
        c = self.coeffs.coeffs(idx)
        dt = self.temperature - self._REF_TEMP
        scale = self.coeffs.scale_factor(idx)
        return (c[0] + c[1]*self.ref_mass + c[2]*dt + c[3]*(self.ref_mass*dt)) * scale

    def residuals(self, idx: int) -> np.ndarray:
        """Residuals in grams: measured minus predicted."""
        return self.sensor_mass(idx) - self.predicted_mass(idx)

    def plot(self):
        """Generate diagnostic plots in real grams."""
        for i in range(self.n_sensors):
            measured = self.sensor_mass(i)
            predicted = self.predicted_mass(i)
            res = self.residuals(i)

            fig, axes = plt.subplots(2, 2, figsize=(12, 8))
            fig.suptitle(f"Sensor {i} Calibration Diagnostics", fontsize=16)

            # Top-left: Measured vs Predicted
            ax = axes[0, 0]
            ax.scatter(self.ref_mass, measured, label="Measured", alpha=0.6)
            ax.plot(self.ref_mass, predicted, 'r-', label="Predicted", linewidth=2)
            ax.set_xlabel("Reference Mass (g)")
            ax.set_ylabel("Measured Mass (g)")
            ax.set_title("Measured vs Predicted Mass")
            ax.legend()
            ax.grid(True)

            # Top-right: Residuals vs Reference Mass
            ax = axes[0, 1]
            ax.scatter(self.ref_mass, res, alpha=0.6)
            ax.axhline(0, color='r', linestyle='--')
            ax.set_xlabel("Reference Mass (g)")
            ax.set_ylabel("Residual (g)")
            ax.set_title("Residuals vs Reference Mass")
            ax.grid(True)

            # Bottom-left: Residuals vs Temperature
            ax = axes[1, 0]
            ax.scatter(self.temperature, res, alpha=0.6)
            ax.axhline(0, color='r', linestyle='--')
            ax.set_xlabel("Temperature (°C)")
            ax.set_ylabel("Residual (g)")
            ax.set_title("Residuals vs Temperature")
            ax.grid(True)

            # Bottom-right: Residual histogram
            ax = axes[1, 1]
            ax.hist(res, bins=20, alpha=0.7, color='g')
            ax.set_xlabel("Residual (g)")
            ax.set_ylabel("Count")
            ax.set_title("Residual Histogram")
            ax.grid(True)

            plt.tight_layout(rect=(0, 0.03, 1, 0.95))
            plt.show()

    def __str__(self):
        return str(self.coeffs)

    def _fit_coeffs(self, auto_scale: bool = True) -> 'Coeffs':
        ref_mass = self.ref_mass
        dt = self.temperature - self._REF_TEMP
        n_sensors = self.n_sensors

        coeffs_array = np.zeros((n_sensors, 4), dtype=float)
        residuals_list = []
        ranks = []
        singular_values_list = []
        scale_factors = []

        for sensor_idx in range(n_sensors):
            sensor = self.sensor_mass(sensor_idx)

            # Compute per-sensor scale factor
            nonzero = sensor != 0
            if auto_scale and np.any(nonzero):
                scale_factor = np.median(sensor[nonzero] / ref_mass[nonzero])
            else:
                scale_factor = 1.0
            scale_factors.append(scale_factor)

            y_scaled = sensor / scale_factor
            X = np.column_stack([np.ones_like(ref_mass), ref_mass, dt, ref_mass*dt])
            coeffs, residuals, rank, s = np.linalg.lstsq(X, y_scaled, rcond=None)
            coeffs_array[sensor_idx] = coeffs

            residuals_list.append(y_scaled - X @ coeffs)
            ranks.append(rank)
            singular_values_list.append(s)

        return Coeffs(coeffs_array, residuals_list, ranks, singular_values_list, len(ref_mass), scale_factors)


class Coeffs:
    def __init__(self, coeffs, residuals_list, ranks, singular_values_list, n_points, scale_factors):
        self._coeffs = coeffs
        self._residuals_list = residuals_list
        self._ranks = ranks
        self._singular_values_list = singular_values_list
        self._scale_factors = scale_factors
        self._n_points = n_points

        # RMS errors in grams per sensor
        self._rms_errors = []
        for idx, r in enumerate(residuals_list):
            self._rms_errors.append(np.sqrt(np.mean(r**2)))

    @property
    def n_sensors(self) -> int:
        return self._coeffs.shape[0]

    def scale_factor(self, idx: int) -> float:
        return self._scale_factors[idx]

    def coeffs(self, idx: int) -> np.ndarray:
        return self._coeffs[idx]

    @property
    def array(self) -> np.ndarray:
        return self._coeffs

    def residuals(self, idx: int) -> float:
        r = self._residuals_list[idx]
        return float(np.sum(r ** 2))

    def rank(self, idx: int) -> int:
        return self._ranks[idx]

    def singular_values(self, idx: int) -> np.ndarray:
        return self._singular_values_list[idx]

    def rms_error(self, idx: int) -> float:
        return self._rms_errors[idx]

    def __str__(self) -> str:
        table = PrettyTable()
        table.field_names = ["Sensor", "c0", "c1", "c2", "c3", "Residuals", "RMS Error (g)",
                             "Rank", "Min(SV)"]
        for i in range(self.n_sensors):
            coeffs_row = [f"{v:.6g}" for v in self._coeffs[i]]
            residuals_val = f"{self.residuals(i):.3g}"
            rms_val = f"{self.rms_error(i):.3g}"
            rank_val = self.rank(i)
            min_sv = f"{np.min(self.singular_values(i)):.3g}" if self.singular_values(i).size > 0 else "N/A"
            table.add_row([i] + coeffs_row + [residuals_val, rms_val, rank_val, min_sv])
        return str(table)

def extract_to_numpy(
    fuzzy_device_id: str,
    tag: SessionNameToken = SessionNameToken.CAL,
) -> CalData:
    """
    Returns a CalData object wrapping a NumPy array with columns:
        [ref_mass, temperature, mass_sensor_0, mass_sensor_1,...]
    """
    engine = get_db_engine()
    device = engine.device.get(fuzzy_device_id)
    sessions = [sess for sess in device.sessions if sess.name.startswith(tag)]

    rows = []

    for sess in sessions:
        ref_mass = _get_ref_mass(sess)
        for datapoint in engine.session.get_datapoints(sess.id):
            # Concatenate reference mass, temperature, and all load cell masses
            row = [ref_mass, datapoint.temperature, *datapoint.mass_sensors]
            rows.append(row)

    if not rows:
        # Ensure consistent shape even if empty; assume at least 1 sensor
        n_sensors = 1  # fallback
        return CalData(np.empty((0, 2 + n_sensors), dtype=float))

    arr = np.array(rows, dtype=float)
    return CalData(arr)


def _get_ref_mass(session: Session):
    """Requires a shared session naming convention.

    E.g:  cal-4576-A0:85:E3:0D:BD:EC
        where
            - `cal` is a tag
            - `4576` is the reference mass
            - `A0:85:E3:0D:BD:EC` is the serial number
    """
    return int(session.name.split('-')[1])

if __name__ == '__main__':
    cal_data_ = extract_to_numpy('48166f3')
    print(cal_data_)
    cal_data_.plot()

