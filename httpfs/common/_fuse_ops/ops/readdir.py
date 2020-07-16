import os
import logging
import errno
import stat

from .. import FuseOp, FuseOpResult


class ReadDirOp(FuseOp):
    def handle(self, *args, **kwargs):
        result = FuseOpResult()

        path = kwargs["path"]
        uid = kwargs["uid"]
        gid = kwargs["gid"]

        file_stats = os.stat(path)
        is_owner = file_stats.st_uid == uid
        is_group = file_stats.st_gid == gid

        if uid == 0:
            access_ok = True
        elif is_owner:
            access_ok = file_stats.st_mode & stat.S_IRUSR
        elif is_group:
            access_ok = file_stats.st_mode & stat.S_IRGRP
        else:
            access_ok = file_stats.st_mode & stat.S_IROTH

        if access_ok:
            dir_listing = os.listdir(path)
            dir_listing = [".", ".."] + dir_listing
            result.data = dir_listing
        else:
            logging.warning("Error during readdir request: Access denied")
            result.errno = errno.EACCES
            result.data = "Access denied"

        return result
