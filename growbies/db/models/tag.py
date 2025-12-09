from enum import StrEnum
from typing import Optional
from uuid import UUID, uuid4
import textwrap

from prettytable import PrettyTable
from sqlmodel import Field, Relationship

from .common import BaseTable, BaseNamedTableEngine, BuiltinTagName, SortedTable
from .link import SessionTagLink
from .session import Session
from growbies.constants import TABLE_COLUMN_WIDTH
from growbies.service.common import ServiceCmdError
from growbies.utils.report import short_uuid

class Tag(BaseTable, table=True):
    class Key(StrEnum):
        ID = 'id'
        NAME = 'name'
        BUILTIN = 'builtin'
        DESCRIPTION = 'description'
        SESSIONS = 'sessions'

    id: UUID | None = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(unique=True, index=True)
    builtin: bool = Field(default=False, nullable=False)
    description: Optional[str] = None
    sessions: list['Session'] = Relationship(back_populates='tags', link_model=SessionTagLink)

for key_ in Tag.Key:
    assert(hasattr(Tag, key_))

class Tags(SortedTable[Tag]):
    def __str__(self):
        table = PrettyTable(title=self.table_name())
        table.field_names = (Tag.Key.ID, Tag.Key.NAME, Tag.Key.DESCRIPTION)
        for field in table.field_names:
            table.align[field] = 'l'

        for element in self._rows:
            wrapped_desc = textwrap.fill(element.description or '', width=TABLE_COLUMN_WIDTH)
            table.add_row([
                short_uuid(element.id),
                element.name,
                wrapped_desc,
            ])

        return str(table)

class TagEngine(BaseNamedTableEngine):
    model_class = Tag

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._init_builtin_tags()

    def get(self, name_or_id: Optional[str]) -> Optional[Tag]:
        return self._get_one(name_or_id, Tag.sessions)

    def get_exact(self, name: str) -> Optional[Tag]:
        return super()._get_exact(name, Tag.sessions)

    def list(self) -> Tags:
        return Tags(self._get_all(Tag.sessions))

    def remove(self, name_or_id: str):
        existing = self.get(name_or_id)
        if existing.builtin:
            raise ServiceCmdError(f"Cannot remove builtin tag: {name_or_id}")
        super().remove(name_or_id)

    def upsert(self, model: Tag,
               fields: Optional[dict] = None,
               _override_builtin_check: bool = False) -> Tag:
        if model.builtin and not _override_builtin_check:
            raise ServiceCmdError(f"Cannot modify builtin tag: {model.name}")
        return super().upsert(
            model,
            {Tag.Key.NAME: model.name,
             Tag.Key.BUILTIN: model.builtin,
             Tag.Key.DESCRIPTION: model.description}
        )

    def _init_builtin_tags(self):
        for name in BuiltinTagName:
            existing = self.get_exact(name)
            if not existing:
                tag = Tag(name=name, builtin=True, description=name.description)
                self.upsert(tag, _override_builtin_check=True)
