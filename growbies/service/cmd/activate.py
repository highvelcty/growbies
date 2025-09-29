import logging

from ..common import ServiceCmd
from growbies.cli.common import PositionalParam
from growbies.db.engine import get_db_engine
from growbies.service.utils import serials_to_devices
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

def execute(cmd: ServiceCmd):
    devices = serials_to_devices(*cmd.kw[PositionalParam.SERIALS])
    device_ids = [dev.id for dev in devices]
    engine = get_db_engine().devices
    worker_pool = get_pool()
    engine.set_active(*device_ids)
    worker_pool.connect(*device_ids)


