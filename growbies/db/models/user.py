from typing import Optional

from sqlmodel import SQLModel, Field, Relationship

from .session import Session, SessionUserLink

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: Optional[str] = None

    sessions: list['Session'] = Relationship(
        back_populates='participants',
        link_model=SessionUserLink
    )
