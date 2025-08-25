from typing import TypeVar

from pydantic import BaseModel

__all__ = ['ServiceCmdError', 'TBaseServiceResp']

class BaseServiceResp(BaseModel):
    pass
TBaseServiceResp = TypeVar('TBaseServiceResp', bound=BaseServiceResp)

class ServiceCmdError(Exception):
    pass
