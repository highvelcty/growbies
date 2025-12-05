import logging

from . import CalibrateSession
from growbies.cli.common import Param as CommonParam
from growbies.db.engine import get_db_engine
from growbies.device.common.identify import Identify
from growbies.service.common import ServiceCmd
from growbies.service.cmd.nvm import identify

logger = logging.getLogger(__name__)

def execute(cmd: ServiceCmd):
    engine = get_db_engine()
    fuzzy_id = cmd.kw.pop(CommonParam.FUZZY_ID)

    session = engine.session.get(fuzzy_id)

    for device in session.devices:
        CalibrateSession(device.id).save()
        identify.update(device.id, {Identify.Field.TELEMETRY_INTERVAL: 0})

    session.active = True
    engine.session.upsert(session)
