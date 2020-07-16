import os
import logging
import errno
import stat

from .. import FuseOp, FuseOpResult


class RenameOp(FuseOp):
    def handle(self, *args, **kwargs):
        result = FuseOpResult()

        old_path = kwargs["old_path"]
        new_path = kwargs["new_path"]

        uid = kwargs["uid"]
        gid = kwargs["gid"]

        file_stats = os.stat(old_path)
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
                os.rename(old_path, new_path)
            else:
                logging.warning("Error during rename request: Access denied")
                result.errno = errno.EACCES
                result.data = "Access denied"
        except Exception as e:
            logging.error("Error during rename request: {}".format(e))
            result.errno = errno.EIO
            result.data = str(e)

        return result
