from uuid import UUID
from typing import Any, Annotated

Pickleable_t = Any
Serial_t = Annotated[str, 'Serial_t']
ModelNumber_t = Annotated[str, 'ModelNumber_t']

# Table IDs
class AccountID(UUID): pass
class DataPointID(UUID): pass
class DataPointMassSensorID(UUID): pass
class DataPointTemperatureSensorID(UUID): pass
class DeviceID(UUID): pass
class FuzzyID(UUID): pass
class GatewayID(UUID): pass
class ProjectID(UUID): pass
class SessionID(UUID): pass
class TagID(UUID): pass
class TareID(UUID): pass
class UserID(UUID): pass
class WorkerID(UUID): pass

# Composites
SerialOrDeviceID_t = DeviceID | Serial_t
