import datetime
from dataclasses import dataclass


@dataclass
class AdbDeviceInfo:
    serial: str
    state: str


@dataclass
class FileInfo:
    mode: int
    size: int
    ctime: datetime.datetime
    path: str


class EnumStatusType:
    OKAY = "OKAY"
    FAIL = "FAIL"
    DENT = "DENT"
    DONE = "DONE"
    DATA = "DATA"


class AdbError(Exception):
    """ adb error """


class AdbTimeout(AdbError):
    """ timeout when communicate to adb-server """


class AdbConnectionError(AdbError):
    """ connection error """


class AdbSyncError(AdbError):
    """ sync error """
