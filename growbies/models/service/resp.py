from pydantic import BaseModel

__all__ = ['ErrorResp']

class ErrorResp(BaseModel):
    msg: str

    def __str__(self):
        return f'Error: {self.msg}'
