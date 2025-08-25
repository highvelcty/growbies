from typing import Optional
import logging

from growbies.db.engine import get_db_engine
from growbies.service.cmd.serials_to_device_ids import serials_to_device_ids
from growbies.service.cmd.structs import ActivateServiceCmd, DeactivateServiceCmd
from growbies.service.resp.structs import ServiceCmdError
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

def activate(cmd: ActivateServiceCmd) -> Optional[ServiceCmdError]:
    try:
        device_ids = serials_to_device_ids(*cmd.serials)
    except ServiceCmdError as err:
        return err

    engine = get_db_engine().devices
    worker_pool = get_pool()

    engine.set_active(*device_ids)
    worker_pool.connect(*device_ids)
    return None

def deactivate(cmd: DeactivateServiceCmd) -> Optional[ServiceCmdError]:
    try:
        device_ids = serials_to_device_ids(*cmd.serials)
    except ServiceCmdError as err:
        return err

    engine = get_db_engine().devices
    worker_pool = get_pool()

    engine.clear_active(*device_ids)
    worker_pool.disconnect(*device_ids)
    worker_pool.join_all(*device_ids)
    return None
