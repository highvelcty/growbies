from datetime import datetime
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Field, Relationship
from typing import List, Optional, TYPE_CHECKING
import logging
import uuid

from .common import BaseTable, BaseTableEngine
from .link import SessionDataPointLink
if TYPE_CHECKING:
    from .session import Session
from growbies.device.common.read import DataPoint as DeviceDataPoint
from growbies.utils.types import DataPointID, DeviceID, TareID

logger = logging.getLogger(__name__)

class DataPoint(BaseTable, table=True):
    id: Optional[DataPointID] = Field(default_factory=uuid.uuid4, primary_key=True)
    # Foreign keys
    device_id: DeviceID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey('device.id', ondelete='CASCADE'),
                         nullable=False)
    )
    tare_id: TareID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey('tare.id', ondelete='CASCADE'),
                         nullable=False)
    )

    timestamp: datetime = Field(nullable=False, index=True)
    mass: float = Field(nullable=False)
    temperature: float = Field(nullable=False)

    # Relationships
    mass_sensors: list['DataPointMassSensor'] = Relationship(back_populates='datapoint')
    temperature_sensors: 'DataPointTemperatureSensor' = Relationship(back_populates='datapoint')
    sessions: List['Session'] = Relationship(back_populates='datapoints',
                                             link_model=SessionDataPointLink)

class DataPointMassSensor(BaseTable, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    datapoint_id: Optional[uuid.UUID] = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey('datapoint.id', ondelete='CASCADE'),
                         nullable=False)
    )
    idx: int = Field(nullable=False)
    mass: float = Field(nullable=False)
    error: int = Field(nullable=True)

    datapoint: DataPoint | None = Relationship(back_populates='mass_sensors')

class DataPointTemperatureSensor(BaseTable, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    datapoint_id: DataPointID = Field(
        sa_column=Column(UUID(as_uuid=True), ForeignKey('datapoint.id', ondelete='CASCADE'),
                         nullable=False)
    )
    idx: int = Field(nullable=False)
    temperature: float = Field(nullable=False)
    error: int = Field(nullable=True)

    datapoint: DataPoint | None = Relationship(back_populates='temperature_sensors')


# --- Engine for inserting datapoints ---
class DataPointEngine(BaseTableEngine):
    def insert(self, device_id: DeviceID, tare_id: TareID, device_dp: DeviceDataPoint) \
            -> DataPoint:
        with self._engine.new_session() as session:
            # Insert main DataPoint row
            dp_row = DataPoint(
                timestamp=device_dp.timestamp,
                device_id=device_id,
                mass=device_dp.mass,
                tare_id=tare_id,
                temperature=device_dp.temperature
            )
            session.add(dp_row)
            session.commit()
            session.refresh(dp_row)

            # Bulk insert per-sensor mass rows
            mass_rows = [
                DataPointMassSensor(
                    datapoint_id=dp_row.id,
                    idx=idx,
                    mass=mass,
                    error=device_dp.get_mass_error_at_idx(idx)
                )
                for idx, mass in enumerate(device_dp.mass_sensors)
            ]
            session.add_all(mass_rows)

            # Bulk insert per-sensor temperature rows
            temp_rows = [
                DataPointTemperatureSensor(
                    datapoint_id=dp_row.id,
                    idx=idx,
                    temperature=temp,
                    error=device_dp.get_temperature_error_at_idx(idx)
                )
                for idx, temp in enumerate(device_dp.temperature_sensors)
            ]
            session.add_all(temp_rows)

            session.commit()
            session.refresh(dp_row)
            return dp_row
