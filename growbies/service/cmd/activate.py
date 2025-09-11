from argparse import ArgumentParser
import logging

from ..common import ServiceCmd, PositionalParam
from growbies.db.engine import get_db_engine
from growbies.service.serials_to_devices import serials_to_devices
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

def make_cli(parser: ArgumentParser):
    parser.add_argument(PositionalParam.SERIALS, nargs='+', type=str,
                        help=PositionalParam.get_help_str(PositionalParam.SERIALS))

def activate(cmd: ServiceCmd):
    devices = serials_to_devices(*cmd.kw[PositionalParam.SERIALS])
    device_ids = [dev.id for dev in devices]
    engine = get_db_engine().devices
    worker_pool = get_pool()
    engine.set_active(*device_ids)
    worker_pool.connect(*device_ids)

def deactivate(cmd: ServiceCmd):
    devices = serials_to_devices(*cmd.kw[PositionalParam.SERIALS])
    device_ids = [dev.id for dev in devices]
    engine = get_db_engine().devices
    worker_pool = get_pool()
    engine.clear_active(*device_ids)
    worker_pool.disconnect(*device_ids)
    worker_pool.join_all(*device_ids)
