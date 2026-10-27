import logging
from .worker import Worker
from growbies.db.engine import get_db_engine
from growbies.service.common import ServiceCmdError
from growbies.service.cmd.ls import DeviceMonitor
from growbies.common.utils.types import DeviceID, WorkerID

logger = logging.getLogger(__name__)

class Pool:
    _JOIN_TIMEOUT_SECONDS = 3

    def __init__(self):
        self._workers: dict[DeviceID | WorkerID, Worker] = dict()

    @property
    def workers(self) -> dict[DeviceID | WorkerID, Worker]:
        return self._workers

    def disconnect_all(self):
        for worker in self._workers.values():
            worker.stop()

        self._join_all()

    def get_if_active_only(self, device_id: DeviceID) -> Worker:
        try:
            return  self.workers[device_id]
        except KeyError:
            raise ServiceCmdError(f'Device ID "{device_id}" is inactive.')

    def synchronize(self, device_monitor: DeviceMonitor):
        db_device_engine = get_db_engine().device

        discovered_serials = {
            device.serial
            for device in device_monitor.devices
        }

        device_ids_to_connect = [
            db_device.id
            for db_device in db_device_engine.list()
            if db_device.is_active() and db_device.serial in discovered_serials
        ]

        self._connect(*device_ids_to_connect)

        device_ids_to_disconnect = [
            device_id
            for device_id, worker in self.workers.items()
            if worker.id not in device_ids_to_connect
        ]
        self._disconnect(*device_ids_to_disconnect)

    def _connect(self, *device_ids: DeviceID):
        for device_id in device_ids:
            worker = self._workers.get(device_id)
            if worker is None or not worker.is_stopping_or_stopped():
                worker = Worker(device_id)
                worker.start()
                self._workers[device_id] = worker

    def _disconnect(self, *worker_ids:  WorkerID):
        for worker_id in worker_ids:
            worker = self._workers.get(worker_id)
            if worker:
                worker.stop()

    def _join_all(self):
        for worker_id, worker in list(self._workers.items()):
            worker.join(timeout=self._JOIN_TIMEOUT_SECONDS)
            if not worker.is_alive():
                del self._workers[worker_id]
            else:
                logger.warning(
                    'Worker %s did not exit within %s seconds.',
                    worker_id,
                    self._JOIN_TIMEOUT_SECONDS,
                )

_pool = None
def get_pool() -> Pool:
    global _pool
    if _pool is None:
        _pool = Pool()
    return _pool
