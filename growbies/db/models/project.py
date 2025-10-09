from datetime import datetime
from enum import StrEnum
from typing import Optional, TYPE_CHECKING
import textwrap
import uuid

from prettytable import PrettyTable
from sqlalchemy import event
from sqlmodel import Field, Relationship

from .common import BaseTable, BaseNamedTableEngine, SortedTable
from .link import SessionProjectLink
from growbies.constants import TABLE_COLUMN_WIDTH
from growbies.utils.report import short_uuid
from growbies.utils.timestamp import get_utc_dt
from growbies.utils.types import ProjectID

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

    id: Optional[ProjectID] = Field(default_factory=uuid.uuid4, primary_key=True)
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

class Projects(SortedTable[Project]):

    def __str__(self):
        table = PrettyTable(title=self.table_name())
        table.field_names = (Project.Key.ID, Project.Key.NAME, Project.Key.DESCRIPTION,
                             Project.Key.SESSIONS)

        for field in table.field_names:
            table.align[field] = 'l'

        for project in self._rows:
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

    def get(self, name_or_id: Optional[str]) -> Project:
        return self._get_one(name_or_id, Project.sessions)

    def list(self) -> Projects:
        return Projects(self._get_all(Project.sessions))

    def upsert(self, model: Project, update_fields: Optional[dict] = None) -> Project:
        return super().upsert(
            model,
            {Project.Key.NAME: model.name, Project.Key.DESCRIPTION: model.description}
        )
