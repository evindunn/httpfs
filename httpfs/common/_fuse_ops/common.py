import json
from enum import auto, Enum, unique
from abc import ABC, abstractmethod


@unique
class FuseOpType(Enum):
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


class FuseOpResult(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self["errno"] = 0

    def to_json(self):
        return json.dumps(self)


class FuseOp(ABC):
    @abstractmethod
    def handle(self, *args, **kwargs) -> FuseOpResult:
        pass
