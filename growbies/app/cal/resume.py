import logging

from growbies.cli.common import Param as CommonParam
from growbies.db.engine import get_db_engine
from growbies.service.common import ServiceCmd

logger = logging.getLogger(__name__)

def execute(cmd: ServiceCmd):
    engine = get_db_engine()
    fuzzy_id = cmd.kw.pop(CommonParam.FUZZY_ID)

    session = engine.session.get(fuzzy_id)

    session.active = True
    engine.session.upsert(session)
