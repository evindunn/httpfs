import os
import logging
import errno
from .common import FuseOp, FuseOpResult


class GetAttrOp(FuseOp):
    GETATTR_KEYS = [
        'st_atime',
        'st_ctime',
        'st_gid',
        'st_mode',
        'st_mtime',
        'st_nlink',
        'st_size',
        'st_uid'
    ]

    def handle(self, *args, **kwargs):
        result = FuseOpResult()
        path = kwargs["path"]

        try:
            os_attrs = os.lstat(path)
            attrs = dict()

            for k in GetAttrOp.GETATTR_KEYS:
                attrs[k] = getattr(os_attrs, k)

            result["attrs"] = attrs

        except FileNotFoundError:
            logging.warning("{} not found".format(path))
            result["errno"] = errno.ENOENT

        return result
