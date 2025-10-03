from enum import StrEnum
from typing import Optional, TYPE_CHECKING
import uuid

from prettytable import PrettyTable
from sqlmodel import Field, Relationship

from .common import BaseTable, BaseNamedTableEngine, SortedTable
from .link import SessionUserLink
from growbies.utils.report import short_uuid
from growbies.utils.types import FuzzyID_t, UserID_t

# if TYPE_CHECKING: # meyere, not sure if this is needed
from .session import Session

class User(BaseTable, table=True):
    class Key(StrEnum):
        ID = 'id'
        NAME = 'name'
        EMAIL = 'email'
        SESSIONS = 'sessions'
    id: Optional[UserID_t] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = ''
    email: Optional[str] = None

    sessions: list[Session] = Relationship(
        back_populates=Session.Key.USERS,
        link_model=SessionUserLink
    )

class Users(SortedTable[User]):
    def __str__(self):
        table = PrettyTable(title=self.table_name())
        table.field_names = (User.Key.ID, User.Key.NAME, User.Key.EMAIL)
        for field in table.field_names:
            table.align[field] = 'l'

        for user in self._rows:
            table.add_row([
                short_uuid(user.id),
                user.name,
                user.email,
            ])

        return str(table)

class UserEngine(BaseNamedTableEngine):
    model_class = User

    def get(self, fuzzy_id: FuzzyID_t) -> User:
        return self._get_one(fuzzy_id, self.model_class.sessions)

    def list(self) -> Users:
        return Users(self._get_all(self.model_class.sessions))

    def upsert(self, model: User, update_fields: Optional[dict] = None) -> User:
        return super().upsert(
            model,
            {User.Key.NAME: model.name, User.Key.EMAIL: model.email}
        )
