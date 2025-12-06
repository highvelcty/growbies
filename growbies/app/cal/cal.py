"""
cli:
    - start session
        - save identify state
        - set identify state
    - read_sensors(ref_masses)
    - read(ref_mass)
    - stop session
        - restore identify state
"""
import re

__all__ = ['DefaultCalSessionName']

class DefaultCalSessionName(str):
    DELIMITER = '-'
    TAG = 'calibration'
    SEARCH_TAG = f'{TAG}{DELIMITER}'
    FMT = f'{SEARCH_TAG}{{:d}}'
    _PATTERN = re.compile(rf"^{TAG}{DELIMITER}(\d+)$")

    def __new__(cls, value: int | str | None = None):
        # create the string value before returning
        if value is None:
            return super().__new__(cls, cls.FMT.format(0))

        if isinstance(value, int):
            return super().__new__(cls, cls.FMT.format(value))

        if isinstance(value, str):
            m = cls._PATTERN.match(value)
            if not m:
                raise ValueError(
                    f'Invalid default calibration session name "{value}", '
                    f'expected format: "{cls.SEARCH_TAG}<int>"'
                )
            return super().__new__(cls, value)

        raise TypeError(
            f"Expected int, str, or None; got {value!r} ({type(value).__name__})"
        )

    @property
    def idx(self) -> int:
        # parse the numeric suffix
        return int(self.split(self.DELIMITER)[-1])
