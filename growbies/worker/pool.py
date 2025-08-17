from .worker import Worker
from growbies.service.cmd.structs import TBaseCmd
from growbies.service.resp.structs import TBaseResp
from growbies.utils.types import DeviceID_t, WorkerID_t

class Pool:
    _workers: dict[WorkerID_t: Worker]

    def start(self, device_id: DeviceID_t) -> Worker:
        worker = self._workers.get(device_id)
        if worker is None:
            worker = Worker(device_id)
            worker.start()
        return worker

    def stop(self, worker_id: WorkerID_t):
        worker = self._workers[worker_id]
        worker.stop()
        worker.join()

    def cmd(self, worker_id: WorkerID_t, cmd: TBaseCmd) -> TBaseResp:
        return self._workers[worker_id].cmd(cmd)
