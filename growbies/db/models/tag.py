from enum import StrEnum
from typing import Iterator, Optional, TYPE_CHECKING
import textwrap

from prettytable import PrettyTable
from sqlalchemy.orm import selectinload
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

    def __str__(self):
        lines = []

        # Prepare all field strings using Tag.Key
        fields = {
            str(Tag.Key.ID): str(self.id),
            str(Tag.Key.NAME): self.name,
            str(Tag.Key.BUILTIN): str(self.builtin),
            str(Tag.Key.DESCRIPTION): self.description or "",
            str(Tag.Key.SESSIONS): ', '.join(
                s.name for s in self.sessions) if self.sessions else ""
        }

        # Wrap text and align after the colon
        for key, val in fields.items():
            wrapped = textwrap.fill(val, width=60)
            wrapped_lines = wrapped.splitlines() or ['']
            lines.append(f'{key}: {wrapped_lines[0]}')
            for wline in wrapped_lines[1:]:
                lines.append(' ' * (len(key) + 2) + wline)

        return '\n'.join(lines)

for key_ in Tag.Key:
    assert(hasattr(Tag, key_))

class Tags:
    def __init__(self, tags: list[Tag] = None):
        if tags is None:
            self._tags = list()
        else:
            self._tags = tags
        self.sort()

    def append(self, tag: Tag):
        self._tags.append(tag)

    def sort(self, reverse: bool = False):
        """Sort tags in place by name."""
        self._tags.sort(key=lambda tag: tag.name.lower(), reverse=reverse)

    def __getitem__(self, index):
        return self._tags[index]

    def __len__(self):
        return len(self._tags)

    def __iter__(self) -> Iterator[Tag]:
        return iter(self._tags)

    def __str__(self):
        table = PrettyTable(title='Tags')
        # Use Tag.Key enum values for headers
        table.field_names = [str(x) for x in Tag.Key]

        # Wrap text for description and sessions
        table.align[Tag.Key.NAME] = 'l'
        table.align[Tag.Key.DESCRIPTION.value] = 'l'
        table.align[Tag.Key.SESSIONS.value] = 'l'

        for tag in self._tags:
            wrapped_desc = textwrap.fill(tag.description or '', width=40)

            # Prepare session list string
            session_names = [f'{s.name}' for s in tag.sessions]  # Could be id or start_ts
            session_str = ', '.join(session_names)
            wrapped_sessions = textwrap.fill(session_str, width=40)

            table.add_row([
                tag.id,
                tag.name,
                tag.builtin,
                wrapped_desc,
                wrapped_sessions
            ])

        return str(table)

class TagEngine(BaseTableEngine):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._init_builtin_tags()

    def upsert(self, model: Tag, update_fields: Optional[dict] = None) -> Tag:
        return super().upsert(
            model,
            {Tag.Key.BUILTIN: model.builtin, Tag.Key.DESCRIPTION: model.description}
        )

    def remove(self, tag: Tag):
        if tag.builtin:
            raise ServiceCmdError(f"Cannot remove builtin tag: {tag.name}")
        with self._engine.new_session() as sess:
            statement = select(Tag).where(Tag.name == tag.name)
            existing_tag = sess.exec(statement).first()
            if existing_tag:
                sess.delete(existing_tag)
                sess.commit()

    def get(self, name: Optional[str]) -> Optional[Tag]:
        if name is None:
            return None

        with self._engine.new_session() as sess:
            statement = select(Tag).where(Tag.name == name).options(selectinload(Tag.sessions))
            return sess.exec(statement).first()

    def list(self) -> Tags:
        with self._engine.new_session() as sess:
            tags = sess.exec(
                select(Tag).options(selectinload(Tag.sessions))
            ).all()
        return Tags(tags)

    def _init_builtin_tags(self):
        for name in BuiltinName:
            tag = Tag(name=name, builtin=True, description=name.description)
            self.upsert(tag)
