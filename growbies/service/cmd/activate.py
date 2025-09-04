from argparse import ArgumentParser
from sqlmodel import Field
import logging

from ..common import BaseServiceCmd, PositionalParam, ServiceCmd
from growbies.db.engine import get_db_engine
from growbies.service.common import serials_to_devices
from growbies.utils.types import Serial_t
from growbies.worker.pool import get_pool

logger = logging.getLogger(__name__)

def make_cli(parser: ArgumentParser):
    parser.add_argument(PositionalParam.SERIALS, nargs='+', type=str,
                        help=PositionalParam.get_help_str(PositionalParam.SERIALS))


class ActivateServiceCmd(BaseServiceCmd):
    serials: list[Serial_t] = Field(default_factory=list, min_length=1)
    def __init__(self, **kw):
        super().__init__(cmd=ServiceCmd.ACTIVATE, **kw)

class DeactivateServiceCmd(BaseServiceCmd):
    serials: list[Serial_t] = Field(default_factory=list, min_length=1)
    def __init__(self, **kw):
        super().__init__(cmd=ServiceCmd.DEACTIVATE, **kw)

def activate(cmd: ActivateServiceCmd):
    devices = serials_to_devices(*cmd.serials)
    device_ids = [dev.id for dev in devices]
    engine = get_db_engine().devices
    worker_pool = get_pool()
    engine.set_active(*device_ids)
    worker_pool.connect(*device_ids)

def deactivate(cmd: DeactivateServiceCmd):
    devices = serials_to_devices(*cmd.serials)
    device_ids = [dev.id for dev in devices]
    engine = get_db_engine().devices
    worker_pool = get_pool()
    engine.clear_active(*device_ids)
    worker_pool.disconnect(*device_ids)
    worker_pool.join_all(*device_ids)
