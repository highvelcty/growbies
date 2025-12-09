from uuid import UUID
from typing import Any, Annotated

Pickleable_t = Any
Serial_t = Annotated[str, 'Serial_t']
ModelNumber_t = Annotated[str, 'ModelNumber_t']

# Table IDs
class DeviceID(UUID): pass
class SessionID(UUID): pass
class TareID(UUID): pass
class WorkerID(UUID): pass

# Composites
FuzzyID = UUID | str
SerialOrDeviceID_t = DeviceID | Serial_t
