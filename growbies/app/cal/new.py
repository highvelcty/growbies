import logging

from . import DefaultCalSessionName
from growbies.cli.common import Param as CommonParam
from growbies.cli.cal import SubCmd
from growbies.cli.cal.new import Param
from growbies.cli.session import Entity
from growbies.db.engine import get_db_engine
from growbies.db.models.session import Session
from growbies.db.models.common import BuiltinTagName
from growbies.service.common import NoResultsServiceCmdError, ServiceCmd, ServiceCmdError

logger = logging.getLogger(__name__)

def execute(cmd: ServiceCmd) -> None:
    engine = get_db_engine()
    fuzzy_id = cmd.kw.pop(CommonParam.FUZZY_ID)
    device = engine.device.get(fuzzy_id)
    session_name = cmd.kw.pop(Param.SESSION_NAME)

    if session_name is None:
        existing = engine.session.prefix_list(f'{DefaultCalSessionName.SEARCH_TAG}%')
        if existing:
            session_name = DefaultCalSessionName(DefaultCalSessionName(existing[-1].name).idx + 1)
        else:
            session_name = DefaultCalSessionName()
        sess = Session(name=session_name)
    else:
        try:
            engine.session.get(session_name)
        except NoResultsServiceCmdError:
            sess = Session(name=session_name)
        else:
            raise ServiceCmdError(f'Session "{session_name}" already exists. See also '
                                  f'the "{SubCmd.RESUME}" sub-command.')

    sess.active = True
    engine.session.upsert(sess)

    engine.session.add_entity(sess.id, Entity.DEVICE, device.id)
    tag = engine.tag.get(BuiltinTagName.CALIBRATION)
    engine.session.add_entity(sess.id, Entity.TAG, tag.id)
