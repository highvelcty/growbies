from typing import Optional

from sqlmodel import SQLModel, Field, Relationship

from .session import Session, SessionTagLink

class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    builtin: bool = Field(default=False, nullable=False)
    description: Optional[str] = None
    sessions: list[Session] = Relationship(back_populates='tags', link_model=SessionTagLink)