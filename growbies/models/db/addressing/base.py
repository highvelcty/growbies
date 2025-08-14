from typing import NewType, TypeVar

from sqlmodel import SQLModel

TSQLModel = TypeVar('TSQLModel', bound=SQLModel)
KeyStr = NewType('KeyStr', str)
