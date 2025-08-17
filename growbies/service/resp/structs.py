from typing import TypeVar

from pydantic import BaseModel

__all__ = ['ErrorResp', 'TBaseResp']

class BaseResp(BaseModel):
    pass
TBaseResp = TypeVar('TBaseResp', bound=BaseResp)

class ErrorResp(BaseModel):
    msg: str

    def __str__(self):
        return f'Error: {self.msg}'
