import logging

from growbies.db.engine import get_db_engine
from growbies.service.cmd.serials_to_device_ids import serials_to_device_ids
from growbies.service.cmd.structs import ActivateServiceCmd, DeactivateServiceCmd
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

def activate(cmd: ActivateServiceCmd):
    device_ids = serials_to_device_ids(*cmd.serials)
    engine = get_db_engine().devices
    worker_pool = get_pool()
    engine.set_active(*device_ids)
    worker_pool.connect(*device_ids)

def deactivate(cmd: DeactivateServiceCmd):
    device_ids = serials_to_device_ids(*cmd.serials)
    engine = get_db_engine().devices
    worker_pool = get_pool()
    engine.clear_active(*device_ids)
    worker_pool.disconnect(*device_ids)
    worker_pool.join_all(*device_ids)
