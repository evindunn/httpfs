import os
import stat
import logging
import errno
from .. import FuseOp, FuseOpResult


class CreateOp(FuseOp):
    def handle(self, *args, **kwargs):
        response = FuseOpResult()
        path = kwargs["path"]
        uid = kwargs["uid"]
        gid = kwargs["gid"]
        mode = kwargs["mode"]

        dir_stats = os.stat(os.path.dirname(path))
        is_dir_owner = dir_stats.st_uid == uid
        is_dir_group = dir_stats.st_gid == gid

        if uid == 0:
            access_ok = True
        elif is_dir_owner:
            access_ok = dir_stats.st_mode & stat.S_IWUSR
        elif is_dir_group:
            access_ok = dir_stats.st_mode & stat.S_IWGRP
        else:
            access_ok = dir_stats.st_mode & stat.S_IWOTH

        try:
            if access_ok:
                fd = os.open(
                    path,
                    flags=os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_ASYNC | os.O_NOATIME,
                    mode=mode
                )
                os.chown(path, uid, gid)
                response.data = fd
            else:
                logging.warning("Error during create request: Access denied")
                response.errno = errno.EACCES
                response.data = "Access denied"

        except Exception as e:
            logging.error("Error during create request: {}".format(e))
            response.errno = errno.EIO
            response.data = str(e)

        return response
