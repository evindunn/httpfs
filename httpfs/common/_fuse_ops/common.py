from enum import auto, IntEnum, unique
from abc import ABC, abstractmethod

import ujson


@unique
class FuseOpType(IntEnum):
    ACCESS = auto()
    CREATE = auto()
    FLUSH = auto()
    FSYNC = auto()
    GET_ATTR = auto()
    LINK = auto()
    MKDIR = auto()
    MKNOD = auto()
    OPEN = auto()
    READ = auto()
    READDIR = auto()
    READLINK = auto()
    RELEASE = auto()
    RENAME = auto()
    RM_DIR = auto()
    STAT_FS = auto()
    SYMLINK = auto()
    TRUNCATE = auto()
    UNLINK = auto()
    UTIMENS = auto()
    WRITE = auto()
    CHOWN = auto()
    CHMOD = auto()


class FuseOpResult:
    ERR_NONE = 0

    def __init__(self, errno=ERR_NONE, data=""):
        self.errno = errno
        self.data = data

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, val):
        if val is not None:
            self._data = val
        else:
            self._data = ""

    def __iter__(self):
        for k in ["errno", "data"]:
            yield k, getattr(self, k)

    def to_json(self):
        return ujson.dumps(dict(self))


class FuseOp(ABC):
    @abstractmethod
    def handle(self, *args, **kwargs) -> FuseOpResult:
        pass

# TODO: Write a check_permissions(uid, gid, mode) helper
