from enum import Enum, unique
from multipledispatch import dispatch
from json import JSONDecodeError


@unique
class Hpc(Enum):
    CSCS_DAINT = 1
    NSG = 2
    SERVICE_ACCOUNT_DAINT = 3


class HpcSettings:

    @dispatch
    def __init__(self):
        pass

    @dispatch(str)
    def __init__(self, workflow_id):
        pass

    @classmethod
    def from_json(cls, decoded_json):
        s = cls()
        return s

    @dispatch(Hpc)
    def set_hpc(self, int):
        self.hpc = int

    def set_offsize(self, int):
        self.offsize = int

    def set_gennum(self, int):
        self.gennum = int

    def set_corenum(self, int):
        self.corenum = int

    @dispatch(int)
    def set_runtime(self, int):
        self.runtime = int

    @dispatch(float)
    def set_runtime(self, float):
        self.runtime = float

    def get_hpc(self):
        return self.hpc

    def get_offsize(self):
        return self.offsize

    def get_gennum(self):
        return self.gennum

    def get_corenum(self):
        return self.corenum

    def get_runtime(self):
        return self.runtime


class HpcSettingsUtil:

    @staticmethod
    def get_conf()