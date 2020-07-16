import errno
import logging
import os
import stat

from .. import FuseOp, FuseOpResult


class UnlinkOp(FuseOp):
    def handle(self, *args, **kwargs):
        result = FuseOpResult()

        path = kwargs["path"]
        uid = kwargs["uid"]
        gid = kwargs["gid"]

        try:
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

            if access_ok:
                os.unlink(path)
            else:
                logging.warning("Error during unlink request: Access denied")
                result.errno = errno.EACCES
                result.data = "Access denied"
        except OSError as e:
            logging.error("Error during unlink request: {}".format(e))
            result.errno = e.errno
            result.data = str(e)
        except Exception as e:
            logging.error("Error during unlink request: {}".format(e))
            result.errno = errno.EIO
            result.data = str(e)

        return result
