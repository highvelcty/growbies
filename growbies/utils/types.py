from typing import Any, Annotated

Pickleable_t = Any
DeviceID_t = Annotated[int, 'DeviceID_t']
Serial_t = Annotated[str, 'Serial_t']
SerialOrDeviceID_t = DeviceID_t | Serial_t
WorkerID_t = Annotated[int, 'WorkerID_t']
ModelNumber_t = Annotated[str, 'ModelNumber_t']
