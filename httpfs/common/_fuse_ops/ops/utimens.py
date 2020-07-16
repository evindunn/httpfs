import errno
import logging
import os
import stat

from .. import FuseOp, FuseOpResult


class UtimeNsOp(FuseOp):
    def handle(self, *args, **kwargs):
        result = FuseOpResult()

        path = kwargs["path"]
        times = kwargs["times"]

        if isinstance(times, list):
            times = tuple(times)

        uid = kwargs["uid"]
        gid = kwargs["gid"]

        file_stats = os.stat(path)
        is_owner = file_stats.st_uid == uid
        is_group = file_stats.st_gid == gid

        if uid == 0:
            access_ok = True
        elif is_owner:
            access_ok = file_stats.st_mode & stat.S_IWUSR
        elif is_group:
            access_ok = file_stats.st_mode & stat.S_IWGRP
        else:
            access_ok = file_stats.st_mode & stat.S_IWOTH

        try:
            if access_ok:
                os.utime(path, times)
            else:
                logging.warning("Error during write request: Access denied")
                result.errno = errno.EACCES
                result.data = "Access denied"

        except Exception as e:
            logging.error("Error during utimens request: {}".format(e))
            result.errno = errno.EIO
            result.data = str(e)

        return result
