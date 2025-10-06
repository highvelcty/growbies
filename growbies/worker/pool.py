from .worker import Worker
from growbies.utils.types import DeviceID_t, WorkerID_t
import logging

logger = logging.getLogger(__name__)

class Pool:
    def __init__(self):
        self._workers: dict[WorkerID_t, Worker] = dict()

    @property
    def workers(self) -> dict[DeviceID_t | WorkerID_t, Worker]:
        return self._workers

    def connect(self, *device_ids: DeviceID_t):
        for device_id in device_ids:
            worker = self._workers.get(WorkerID_t(device_id))
            if worker is None:
                worker = Worker(device_id)
                worker.start()
                self._workers[WorkerID_t(device_id)] = worker
            elif not worker.is_alive():
                worker = Worker(device_id)
                worker.start()
                self._workers[WorkerID_t(device_id)] = worker

    def disconnect(self, *worker_ids:  WorkerID_t):
        for worker_id in worker_ids:
            worker = self._workers.get(worker_id)
            if worker:
                worker.stop()

    def disconnect_all(self):
        for worker in self._workers.values():
            worker.stop()

    def join_all(self, *worker_ids: WorkerID_t, timeout=None):
        for worker_id in worker_ids:
            worker = self._workers.get(worker_id)
            if worker:
                worker.join(timeout=timeout)
                del self._workers[worker_id]

_pool = None
def get_pool() -> Pool:
    global _pool
    if _pool is None:
        _pool = Pool()
    return _pool
