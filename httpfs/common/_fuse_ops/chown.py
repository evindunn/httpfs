import os
import stat
import logging
import errno
from .common import FuseOp, FuseOpResult


class ChownOp(FuseOp):
    def handle(self, *args, **kwargs):
        result = FuseOpResult()
        client = kwargs["client"]
        path = kwargs["path"]
        uid = kwargs["uid"]
        gid = kwargs["gid"]
        caller_uid = kwargs["caller_uid"]
        caller_gid = kwargs["caller_gid"]

        file_stats = os.stat(path)
        is_owner = file_stats.st_uid == caller_uid
        is_group = file_stats.st_gid == caller_gid

        if caller_uid == 0:
            access_ok = True
        elif is_owner:
            access_ok = file_stats.st_mode & stat.S_IWUSR
        elif is_group:
            access_ok = file_stats.st_mode & stat.S_IWGRP
        else:
            access_ok = file_stats.st_mode & stat.S_IWOTH

        # TODO: Don't let me if it isn't mine
        try:
            if access_ok:
                os.chown(path, uid, gid)
                logging.debug("Successful chown for {}".format(client))
            else:
                result["errno"] = errno.EACCES
                result["message"] = "Access denied"
                logging.warning("Error during chown request: Access denied")
        except Exception as e:
            logging.error("Error during chown request: {}".format(e))
            result["errno"] = errno.EIO
            result["message"] = str(e)

        return result
