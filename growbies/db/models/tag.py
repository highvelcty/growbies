from enum import StrEnum
from typing import Iterator, Optional, TYPE_CHECKING
import textwrap

from prettytable import PrettyTable
from sqlmodel import select, SQLModel, Field, Relationship

from .common import BaseTableEngine
from .links import SessionTagLink
if TYPE_CHECKING:
    from .session import Session
from growbies.service.common import ServiceCmdError

class BuiltinName(StrEnum):
    READ_ONLY = 'read-only'
    TEMPLATE = 'template'

    @property
    def description(self) -> str:
        if self == self.READ_ONLY:
            return 'Read-only access. No updating or removal will be permitted with this tag.'
        elif self == self.TEMPLATE:
            return (f'A template from which concrete sessions can be derived. The '
                    f'"{self.READ_ONLY}" tag will automatically be added if it is not already.')
        else:
            return f''

class Tag(SQLModel, table=True):
    class Key(StrEnum):
        ID = 'id'
        NAME = 'name'
        BUILTIN = 'builtin'
        DESCRIPTION = 'description'
        SESSIONS = 'sessions'

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    builtin: bool = Field(default=False, nullable=False)
    description: Optional[str] = None
    sessions: list['Session'] = Relationship(back_populates='tags', link_model=SessionTagLink)

for key in Tag.Key:
    assert(hasattr(Tag, key))

class Tags:
    def __init__(self, tags: list[Tag]):
        self.tags = tags

    def get(self, name) -> Optional[Tag]:
        for tag in self.tags:
            if tag.name == name:
                return tag
        return None

    def append(self, tag: Tag):
        self.tags.append(tag)

    def __getitem__(self, index):
        return self.tags[index]

    def __len__(self):
        return len(self.tags)

    def __iter__(self) -> Iterator[Tag]:
        return iter(self.tags)

    def __str__(self):
        table = PrettyTable()
        table.field_names = ["ID", "Name", "Builtin", "Description"]
        table.align["Description"] = "l"  # left-align description

        for tag in self.tags:
            wrapped_desc = textwrap.fill(tag.description or "", width=60)
            table.add_row([tag.id, tag.name, tag.builtin, wrapped_desc])

        return str(table)

class TagEngine(BaseTableEngine):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._init_builtin_tags()

    def add(self, tag: Tag):
        with self._engine.new_session() as sess:
            # Try to find existing tag
            statement = select(Tag).where(Tag.name == tag.name)
            existing_tag = sess.exec(statement).first()

            if existing_tag:
                # Update fields
                existing_tag.builtin = tag.builtin
                existing_tag.description = tag.description
                sess.add(existing_tag)  # SQLModel needs add() even for updates
            else:
                # Insert new tag
                sess.add(tag)

            sess.commit()

    def remove(self, tag: Tag):
        if tag.builtin:
            raise ServiceCmdError(f"Cannot remove builtin tag: {tag.name}")
        with self._engine.new_session() as sess:
            statement = select(Tag).where(Tag.name == tag.name)
            existing_tag = sess.exec(statement).first()
            if existing_tag:
                sess.delete(existing_tag)
                sess.commit()

    def get(self, name: str) -> Tag:
        with self._engine.new_session() as sess:
            statement = select(Tag).where(Tag.name == name)
            return sess.exec(statement).first()

    def list(self) -> Tags:
        with self._engine.new_session() as sess:
            statement = select(Tag)
            results = sess.exec(statement).all()
            return Tags(results)

    def _init_builtin_tags(self):
        for name in BuiltinName:
            tag = Tag(name=name, builtin=True, description=name.description)
            self.add(tag)
