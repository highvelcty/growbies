from ..common import BaseServiceCmd, ServiceCmd

class LsServiceCmd(BaseServiceCmd):
    def __init__(self, **kw):
        super().__init__(cmd=ServiceCmd.LS, **kw)
