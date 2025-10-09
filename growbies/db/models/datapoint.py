from datetime import datetime
from sqlalchemy import ARRAY, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Column, Field, Relationship
from typing import List, Optional, TYPE_CHECKING
import uuid

from .common import BaseTable, BaseTableEngine
from .link import SessionDataPointLink
if TYPE_CHECKING:
    from .session import Session
from growbies.device.common.read import DataPoint as DeviceDataPoint
from growbies.utils.types import DataPointID, DeviceID, TareID

class DataPoint(BaseTable, table=True):
    id: Optional[DataPointID] = Field(default_factory=uuid.uuid4, primary_key=True)

    # Timestamp for the measurement
    timestamp: datetime = Field(nullable=False, index=True)

    # Associated device
    device_id: DeviceID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey("device.id", ondelete="CASCADE"),
                         nullable=False)
    )

    # Total mass
    mass: float = Field(nullable=False)
    mass_sensors: List[float] = Field(sa_column=Column(ARRAY(Float), nullable=False))
    mass_errors: List[int] = Field(sa_column=Column(ARRAY(Integer), nullable=False))

    # Tare foreign key
    tare_id: TareID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey('tare.id', ondelete='CASCADE'),
                         nullable=False)
    )

    # Average temperature
    temperature: float = Field(nullable=False)

    # Individual temperature sensor readings
    temperature_sensors: List[float] = Field(sa_column=Column(ARRAY(Float), nullable=False))
    temperature_errors: List[int] = Field(sa_column=Column(ARRAY(Integer), nullable=False))

    # Relationship, not a field/column.
    sessions: List['Session'] = Relationship(
        back_populates='datapoints',
        link_model=SessionDataPointLink
    )

class DataPointEngine(BaseTableEngine):
    def insert(self, device_id: DeviceID, tare_id: TareID, device_dp: DeviceDataPoint) \
            -> DataPoint:
        with self._engine.new_session() as session:
            tare_row = DataPoint(timestamp = device_dp.timestamp,
                                 device_id = device_id,
                                 mass = device_dp.mass,
                                 mass_sensors = device_dp.mass_sensors,
                                 mass_errors = device_dp.mass_errors,
                                 tare_id = tare_id,
                                 temperature = device_dp.temperature,
                                 temperature_sensors = device_dp.temperature_sensors,
                                 temperature_errors = device_dp.temperature_errors)
            session.add(tare_row)
            session.commit()
            session.refresh(tare_row)
            return tare_row
