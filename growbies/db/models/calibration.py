from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum
import uuid

from .common import BaseTable
from growbies.utils.types import CalibrationID

from .link import DataPointCalibrationLink
if TYPE_CHECKING:
    from .datapoint import DataPoint

class CalibrationType(str, Enum):
    ASSEMBLY = 'assembly'
    SENSOR = 'sensor'


class Calibration(BaseTable, table=True):
    id: Optional[CalibrationID] = Field(default_factory=uuid.uuid4, primary_key=True)

    cal_type: CalibrationType = Field(nullable=False)
    idx: int | None = Field(default=None, nullable=True)   # NULL for assembly

    # Calibration coefficients
    ref_mass: float
    ref_temperature: float
    mass_offset: float
    mass_slope: float
    temperature_slope: float
    mass_cross_temperature: float
    quadratic_temperature: float
    quadratic_mass: float

    # link to datapoints
    datapoints: list["DataPoint"] = Relationship(
        back_populates='calibrations',
        link_model=DataPointCalibrationLink
    )

