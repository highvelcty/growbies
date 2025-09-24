from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

from .common import BaseTableEngine
from .links import SessionUserLink

if TYPE_CHECKING:
    from .session import Session

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: Optional[str] = None

    sessions: list['Session'] = Relationship(
        back_populates='participants',
        link_model=SessionUserLink
    )

class UserEngine(BaseTableEngine): pass
