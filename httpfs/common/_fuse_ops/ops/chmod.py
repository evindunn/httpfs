import os
import stat
import logging
import errno
from .. import FuseOp, FuseOpResult


class ChmodOp(FuseOp):
    def handle(self, *args, **kwargs) -> FuseOpResult:
        result = FuseOpResult()
        client = kwargs["client"]
        path = kwargs["path"]
        uid = kwargs["uid"]
        gid = kwargs["gid"]
        mode = kwargs["mode"]

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
                os.chmod(path, mode)
                logging.debug("Successful chmod for {}".format(client))
            else:
                logging.warning("Error during chmod request: Access denied")
                result.errno = errno.EACCES
                result.data = "Access denied"
        except Exception as e:
            logging.error("Error during chmod request: {}".format(e))
            result.errno = errno.EACCES
            result.data = str(e)

        return result
