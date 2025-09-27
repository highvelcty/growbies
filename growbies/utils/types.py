from uuid import UUID
from typing import Any, Annotated

Pickleable_t = Any
Serial_t = Annotated[str, 'Serial_t']
WorkerID_t = Annotated[int, 'WorkerID_t']
ModelNumber_t = Annotated[str, 'ModelNumber_t']

# Table IDs
AccountID_t = Annotated[UUID, 'AccountID_t']
DataPointID_t = Annotated[UUID, 'DataPointID_t']
DeviceID_t = Annotated[UUID, 'DeviceID_t']
GatewayID_t = Annotated[UUID, 'GatewayID_t']
ProjectID_t = Annotated[UUID, 'ProjectID_t']
SessionID_t = Annotated[UUID, 'SessionID_t']
TagID_t = Annotated[UUID, 'TagID_t']
TareID_t = Annotated[UUID, 'TareID_t']
UserID_t = Annotated[UUID, 'UserID_t']

# Composites
SerialOrDeviceID_t = DeviceID_t | Serial_t