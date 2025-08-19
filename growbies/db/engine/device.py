from typing import TYPE_CHECKING
from sqlmodel import select
from sqlmodel import Session as DBSession
import logging

if TYPE_CHECKING:
    from growbies.db.engine import DBEngine
from growbies.db.models import ConnectionState, Device, Devices
from growbies.utils.types import Serial_t, DeviceID_t, SerialOrDeviceID_t

logger = logging.getLogger(__name__)


class DevicesEngine:
    def __init__(self, engine: 'DBEngine'):
        self._engine = engine

    def merge_with_discovered(self, discovered_devices: Devices) -> Devices:
        with self._engine.new_session() as db_session, db_session.begin():
            merged_devices = self._merge_with_discovered(discovered_devices, db_session)
            for device in merged_devices:
                self._overwrite(device, db_session)
            return Devices(devices=[dev.model_copy() for dev in merged_devices])

    def set_active(self, *serials_or_ids: SerialOrDeviceID_t):
        with self._engine.new_session() as db_session, db_session.begin():
            self._set_flag(*serials_or_ids, flag=ConnectionState.ACTIVE, value=True,
                           db_session=db_session)

    def clear_active(self, *serials_or_ids: Serial_t):
        with self._engine.new_session() as db_session, db_session.begin():
            self._set_flag(*serials_or_ids, flag=ConnectionState.ACTIVE, value=False,
                           db_session=db_session)

    def get(self, serial_or_id: SerialOrDeviceID_t) -> Device:
        with self._engine.new_session() as db_session:
            return self._get(serial_or_id, db_session).model_copy()

    def get_engine(self, device_id: DeviceID_t) -> 'DeviceEngine':
        return DeviceEngine(self._engine, device_id)

    @staticmethod
    def _get(serial_or_id: SerialOrDeviceID_t, db_session: DBSession) -> Device:
        if isinstance(serial_or_id, str):
            stmt = select(Device).where(Device.serial == serial_or_id)
        else:
            stmt = select(Device).where(Device.id == serial_or_id)
        return db_session.exec(stmt).first()

    @staticmethod
    def _get_all(db_session: DBSession) -> Devices:
        stmt = select(Device)
        results = db_session.exec(stmt).all()
        return Devices(devices=list(results))

    def _merge_with_discovered(self, discovered_devices: Devices, db_session: DBSession) -> Devices:
        merged_devices = self._get_all(db_session)

        # Update existing in DB.
        for existing_device in merged_devices:
            existing_device.init_discovery_info()
            existing_device.initialize_discovered_info()
            discovered_device = discovered_devices.get(existing_device.serial)
            if discovered_device is not None:
                existing_device.gateway = discovered_device.gateway
                existing_device.serial = discovered_device.serial
                existing_device.vid = discovered_device.vid
                existing_device.pid = discovered_device.pid
                existing_device.path = discovered_device.path
                # Set the bit.
                existing_device.state |= ConnectionState.DISCOVERED

        # Add new
        new_serials = set((dev.serial for dev in discovered_devices))
        existing_serials = set((dev.serial for dev in merged_devices))
        for serial in (new_serials - existing_serials):
            merged_devices.append(discovered_devices.get(serial))

        return merged_devices

    @staticmethod
    def _overwrite(device: Device, db_session: DBSession) -> Device:
        # Lock the row by unique key
        stmt = (
            select(type(device))
            .where(getattr(type(device), Device.Key.NAME) == device.name)
            .with_for_update()
        )
        # Must assign to something to acquire the "with_for_update" lock
        _ = db_session.exec(stmt).first()
        db_session.add(device)
        db_session.flush()
        db_session.refresh(device)
        return device

    def _set_flag(self, *serials_or_ids: SerialOrDeviceID_t, flag: ConnectionState, value: bool,
                  db_session: DBSession):
        for serial_or_id in serials_or_ids:
            device = self._get(serial_or_id, db_session=db_session)
            if value:
                # set the bit
                device.state |= flag
            else:
                # clear the bit
                device.state &= ~flag

        db_session.flush()

class DeviceEngine:
    def __init__(self, engine: 'DBEngine', device_id: DeviceID_t):
        self._device_id = device_id
        self._engine = engine

    def get(self, serial_or_id: SerialOrDeviceID_t) -> Device:
        with self._engine.new_session() as db_session:
            return self._get(serial_or_id, db_session).model_copy()

    def set_active(self):
        with self._engine.new_session() as db_session, db_session.begin():
            self._set_flag(flag=ConnectionState.ACTIVE, value=True, db_session=db_session)

    def clear_active(self):
        with self._engine.new_session() as db_session, db_session.begin():
            self._set_flag(flag=ConnectionState.ACTIVE, value=False, db_session=db_session)

    def set_connected(self):
        with self._engine.new_session() as db_session, db_session.begin():
            self._set_flag(flag=ConnectionState.CONNECTED, value=True, db_session=db_session)

    def clear_connected(self):
        with self._engine.new_session() as db_session, db_session.begin():
            self._set_flag(flag=ConnectionState.CONNECTED, value=False, db_session=db_session)

    def init_start_connection(self):
        with self._engine.new_session() as db_session, db_session.begin():
            device = self._get(self._device_id, db_session)
            device.init_start_connection()

    @staticmethod
    def _get(serial_or_device_id: SerialOrDeviceID_t, db_session: DBSession) -> Device:
        if isinstance(serial_or_device_id, str):
            stmt = select(Device).where(Device.serial == serial_or_device_id)
        else:
            stmt = select(Device).where(Device.id == serial_or_device_id)
        return db_session.exec(stmt).first()

    def _set_flag(self, flag: ConnectionState, value: bool, db_session: DBSession):
        # Attached model
        device = db_session.get(self._device_id, db_session)
        if value:
            # set the bit
            device.state |= flag
        else:
            # clear the bit
            device.state &= ~flag

        db_session.flush()