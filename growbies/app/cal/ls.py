import logging

from growbies.cli.cal.ls import Param
from growbies.db.engine import get_db_engine
from growbies.db.models.session import Sessions
from growbies.db.models.tag import BuiltinTagName
from growbies.service.common import ServiceCmd

logger = logging.getLogger(__name__)

def execute(cmd: ServiceCmd):
    engine = get_db_engine()

    show_inactive = cmd.kw.pop(Param.INACTIVE, False)

    the_list = list()
    for sess in engine.session.ls():
        if BuiltinTagName.CALIBRATION in (tag.name for tag in sess.tags):
            if show_inactive:
                the_list.append(sess)
            elif sess.active:
                the_list.append(sess)

    return Sessions(the_list, show_id=False, show_device_names=True, show_active=show_inactive)

