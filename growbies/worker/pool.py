from .worker import Worker
from growbies.service.cmd.structs import TBaseCmd
from growbies.service.resp.structs import TBaseResp
from growbies.utils.types import DeviceID_t, WorkerID_t


class Pool:
    def __init__(self):
        self._workers: dict[WorkerID_t: Worker] = dict()

    def cmd(self, worker_id: WorkerID_t, cmd: TBaseCmd) -> TBaseResp:
        return self._workers[worker_id].cmd(cmd)

    def start(self, *device_ids: DeviceID_t):
        for device_id in device_ids:
            worker = self._workers.get(device_id)
            if worker is None:
                worker = Worker(device_id)
                worker.start()
            self._workers[device_id] = worker

    def stop(self, *worker_ids: WorkerID_t):
        for worker_id in worker_ids:
            self._workers[worker_id].stop()

    def stop_all(self):
        for worker in self._workers.values():
            worker.stop()

    def wait(self, *worker_ids: WorkerID_t, timeout=None):
        for worker_id in worker_ids:
            self._workers[worker_id].join(timeout=timeout)
            del self._workers[worker_id]

pool = None
def get_pool() -> Pool:
    global pool
    if pool is None:
        pool = Pool()
    return pool
