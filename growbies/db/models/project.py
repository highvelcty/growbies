from datetime import datetime
from enum import StrEnum
from typing import Iterator, Optional, TYPE_CHECKING
import textwrap
import uuid

from prettytable import PrettyTable
from sqlalchemy import event
from sqlalchemy.orm import selectinload
from sqlmodel import select, SQLModel, Field, Relationship

from .common import BaseTable, BaseNamedTableEngine
from .link import SessionProjectLink
from growbies.constants import TABLE_COLUMN_WIDTH
from growbies.utils.report import short_uuid
from growbies.utils.timestamp import get_utc_dt
from growbies.utils.types import ProjectID_t

if TYPE_CHECKING:
    from .session import Session

class Project(BaseTable, table=True):
    class Key(StrEnum):
        ID = 'id'
        NAME = 'name'
        DESCRIPTION = 'description'
        CREATED_AT = 'created_at'
        UPDATED_AT = 'updated_at'
        SESSIONS = 'sessions'
    id: Optional[ProjectID_t] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=get_utc_dt, nullable=False)
    updated_at: datetime = Field(default_factory=get_utc_dt, nullable=False)

    sessions: list['Session'] = Relationship(
        back_populates='projects',
        link_model=SessionProjectLink
    )

    @property
    def short_uuid(self) -> str:
        return short_uuid(self.id)

@event.listens_for(Project, "before_update")
def update_timestamp(_mapper, _connection, target):
    target.updated_at = get_utc_dt()

class Projects:
    def __init__(self, projects: list[Project] = None):
        if projects is None:
            self._projects = list()
        else:
            self._projects = projects
        self.sort()

    def append(self, project: Project):
        self._projects.append(project)

    def sort(self, reverse: bool = False):
        """Sort tags in place by name."""
        self._projects.sort(key=lambda tag: tag.name.lower(), reverse=reverse)

    def __getitem__(self, index):
        return self._projects[index]

    def __len__(self):
        return len(self._projects)

    def __iter__(self) -> Iterator[Project]:
        return iter(self._projects)

    def __str__(self):
        table = PrettyTable(title='Projects')
        table.field_names = (Project.Key.ID, Project.Key.NAME, Project.Key.DESCRIPTION,
                             Project.Key.SESSIONS)

        for field in table.field_names:
            table.align[field] = 'l'

        for project in self._projects:
            wrapped_desc = textwrap.fill(project.description or '', width=TABLE_COLUMN_WIDTH)
            session_names = [f'{s.name}' for s in project.sessions]  # Could be id or start_ts
            session_str = ', '.join(session_names)
            wrapped_sessions = textwrap.fill(session_str, width=TABLE_COLUMN_WIDTH)

            table.add_row([
                project.short_uuid,
                project.name,
                wrapped_desc,
                wrapped_sessions
            ])

        return str(table)

class ProjectEngine(BaseNamedTableEngine):
    model_class = Project
    def get(self, name_or_id: Optional[str]) -> Optional[Project]:
        return self._get_one(name_or_id, Project.sessions)

    def list(self) -> Projects:
        return Projects(self._get_all(Project.sessions))

    def upsert(self, model: Project, update_fields: Optional[dict] = None) -> Project:
        return super().upsert(
            model,
            {Project.Key.NAME: model.name, Project.Key.DESCRIPTION: model.description}
        )
