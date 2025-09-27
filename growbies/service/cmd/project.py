from argparse import ArgumentParser
from enum import StrEnum
from typing import Optional
import logging

from ..common import ServiceCmd, ServiceCmdError
from growbies.db.engine import get_db_engine
from growbies.db.models import project

logger = logging.getLogger(__name__)

class PositionalParam(StrEnum):
    GET_NAME = 'get_name'

    @property
    def help(self) -> str:
        if self == self.GET_NAME:
            return 'Get a project by name'
        else:
            return ''

class KwParam(StrEnum):
    SET_NAME = 'set_name'
    DESCRIPTION = 'description'
    REMOVE = 'remove'

    @property
    def help(self) -> str:
        if self == self.SET_NAME:
            return 'Rename a project.'
        elif self == self.DESCRIPTION:
            return 'Set project description.'
        elif self == self.REMOVE:
            return 'Remove a project.'
        else:
            return ''

def make_cli(parser: ArgumentParser):
    parser.add_argument(
        PositionalParam.GET_NAME,
        nargs='?',  # zero or one time
        default=None,  # default if not provided
        help=PositionalParam.GET_NAME.help
    )

    for param in (KwParam.SET_NAME, KwParam.DESCRIPTION):
        parser.add_argument(
            f'--{param}',
            type=str,
            default=None,
            help=param.help
        )

    parser.add_argument(
        f'--{KwParam.REMOVE}',
        action='store_true',
        help=KwParam.REMOVE.help
    )

def execute(cmd: ServiceCmd) -> Optional[project.Projects]:
    engine = get_db_engine()
    get_name = cmd.kw.pop(PositionalParam.GET_NAME)
    description = cmd.kw.pop(KwParam.DESCRIPTION)
    remove = cmd.kw.pop(KwParam.REMOVE)
    set_name = cmd.kw.pop(KwParam.SET_NAME)

    if remove:
        if get_name is None:
            raise ServiceCmdError(f'Must provide {PositionalParam.GET_NAME} to remove a project.')
        if not engine.project.remove(get_name):
            raise ServiceCmdError(f'Failed to remove project "{get_name}"')
        return None

    project_ = engine.project.get(get_name)

    if description is None and set_name is None:
        if project_ is None:
            return engine.project.list()
        else:
            return project.Projects([project_])
    else:
        if project_ is None:
            if set_name is None:
                raise ServiceCmdError(f'Must provide --{KwParam.SET_NAME} to create a new user.')
            project_ = project.Project(name=set_name, description=description)
        else:
            if set_name:
                project_.name = set_name
            if description:
                project_.description = description
        engine.project.upsert(project_)
        return None
