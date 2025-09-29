from typing import Optional
import logging

from ..common import ServiceCmd, ServiceCmdError
from growbies.cli.tag import KwParam, PositionalParam
from growbies.db.engine import get_db_engine
from growbies.db.models import tag

logger = logging.getLogger(__name__)

def execute(cmd: ServiceCmd) -> Optional[tag.Tags]:
    engine = get_db_engine()
    get_name = cmd.kw.pop(PositionalParam.GET_NAME)
    description = cmd.kw.pop(KwParam.DESCRIPTION)
    remove = cmd.kw.pop(KwParam.REMOVE)
    set_name = cmd.kw.pop(KwParam.SET_NAME)

    if remove:
        if get_name is None:
            raise ServiceCmdError(f'Must provide {PositionalParam.GET_NAME} to remove a tag.')
        if not engine.tag.remove(get_name):
            raise ServiceCmdError(f'Failed to remove tag "{get_name}"')
        return None

    tag_ = engine.tag.get(get_name)

    if description is None and set_name is None:
        if tag_ is None:
            return engine.tag.list()
        else:
            return tag.Tags([tag_])
    else:
        if tag_ is None:
            if set_name is None:
                raise ServiceCmdError(f'Must provide --{KwParam.SET_NAME} to create a new tag.')
            tag_ = tag.Tag(name=set_name, description=description)
        else:
            if set_name:
                tag_.name = set_name
            if description:
                tag_.description = description
        engine.tag.upsert(tag_)
        return None
