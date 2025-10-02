from typing import Optional
import logging

from ..common import ServiceCmd, ServiceCmdError
from growbies.cli.project import PositionalParam, KwParam
from growbies.db.engine import get_db_engine
from growbies.db.models import project

logger = logging.getLogger(__name__)

def execute(cmd: ServiceCmd) -> Optional[project.Projects]:
    engine = get_db_engine()
    get_name = cmd.kw.pop(PositionalParam.GET_NAME)
    description = cmd.kw.pop(KwParam.DESCRIPTION)
    remove = cmd.kw.pop(KwParam.REMOVE)
    set_name = cmd.kw.pop(KwParam.SET_NAME)

    if remove:
        if get_name is None:
            raise ServiceCmdError(f'Must provide {PositionalParam.GET_NAME} to remove a project.')
        engine.project.remove(get_name)
        return None

    if description is None and set_name is None:
        if get_name is None:
            return engine.project.list()
        else:
            return engine.project.get(get_name)
    else:
        if get_name is None:
            if set_name is None:
                raise ServiceCmdError(f'Must provide --{KwParam.SET_NAME} to create new.')
            project_ = project.Project(name=set_name, description=description)
        else:
            project_ = engine.project.get(get_name)
            if set_name:
                project_.name = set_name
            if description:
                project_.description = description
        engine.project.upsert(project_)
        return None
