from typing import TypeVar

from sqlmodel import SQLModel

TSQLModel = TypeVar('TSQLModel', bound=SQLModel)
