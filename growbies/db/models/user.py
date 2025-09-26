from enum import StrEnum
from typing import Iterator, Optional, TYPE_CHECKING
import textwrap
import uuid

from prettytable import PrettyTable
from sqlalchemy.orm import selectinload
from sqlmodel import select, SQLModel, Field, Relationship

from .common import BaseTableEngine
from .links import SessionUserLink
from growbies.constants import TABLE_COLUMN_WIDTH
from growbies.utils.types import UserID_t

if TYPE_CHECKING:
    from .session import Session

class User(SQLModel, table=True):
    class Key(StrEnum):
        ID = 'id'
        NAME = 'name'
        EMAIL = 'email'
        SESSIONS = 'sessions'
    id: Optional[UserID_t] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    email: Optional[str] = None

    sessions: list['Session'] = Relationship(
        back_populates='participants',
        link_model=SessionUserLink
    )

class Users:
    def __init__(self, users: list[User] = None):
        if users is None:
            self._users = list()
        else:
            self._users = users
        self.sort()

    def append(self, user: User):
        self._users.append(user)

    def sort(self, reverse: bool = False):
        """Sort tags in place by name."""
        self._users.sort(key=lambda tag: tag.name.lower(), reverse=reverse)

    def __getitem__(self, index):
        return self._users[index]

    def __len__(self):
        return len(self._users)

    def __iter__(self) -> Iterator[User]:
        return iter(self._users)

    def __str__(self):
        table = PrettyTable(title='Users')
        # Use Tag.Key enum values for headers
        table.field_names = [str(x) for x in User.Key]

        # Wrap text for description and sessions
        table.align[User.Key.NAME] = 'l'
        table.align[User.Key.EMAIL] = 'l'

        for user in self._users:
            # Prepare session list string
            session_names = [f'{s.name}' for s in user.sessions]  # Could be id or start_ts
            session_str = ', '.join(session_names)
            wrapped_sessions = textwrap.fill(session_str, width=TABLE_COLUMN_WIDTH)

            table.add_row([
                user.id,
                user.name,
                user.email,
                wrapped_sessions
            ])

        return str(table)

class UserEngine(BaseTableEngine):
    def get(self, name: Optional[str]) -> Optional[User]:
        if name is None:
            return None

        with self._engine.new_session() as sess:
            statement = select(User).where(User.name == name).options(selectinload(User.sessions))
            return sess.exec(statement).first()

    def list(self) -> Users:
        with self._engine.new_session() as sess:
            users = sess.exec(
                select(User).options(selectinload(User.sessions))
            ).all()
        return Users(users)

    def remove(self, name: str) -> bool:
        with self._engine.new_session() as sess:
            statement = select(User).where(User.name == name)
            existing_user = sess.exec(statement).first()
            if existing_user:
                sess.delete(existing_user)
                sess.commit()
                return True
        return False

    def upsert(self, model: User, update_fields: Optional[dict] = None) -> User:
        return super().upsert(
            model,
            {User.Key.NAME: model.name, User.Key.EMAIL: model.email}
        )
