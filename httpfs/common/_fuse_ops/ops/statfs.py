import os
from .. import FuseOp, FuseOpResult


class StatFsOp(FuseOp):
    _STAT_FS_KEYS = [
        'f_bavail',
        'f_bfree',
        'f_blocks',
        'f_bsize',
        'f_favail',
        'f_ffree',
        'f_files',
        'f_flag',
        'f_frsize',
        'f_namemax'
    ]

    def handle(self, *args, **kwargs):
        result = FuseOpResult()

        fs_path = kwargs["path"]
        statfs_os_result = os.statvfs(fs_path)
        statfs_result = dict()

        for k in StatFsOp._STAT_FS_KEYS:
            statfs_result[k] = getattr(statfs_os_result, k)

        result.data = statfs_result

        return result
