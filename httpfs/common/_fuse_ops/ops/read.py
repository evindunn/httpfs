import base64
import os
import logging
import errno
import stat

from .. import FuseOp, FuseOpResult


class ReadOp(FuseOp):
    def handle(self, *args, **kwargs):
        result = FuseOpResult()

        file_descriptor = kwargs["file_descriptor"]
        offset = kwargs["offset"]
        size = kwargs["size"]

        uid = kwargs["uid"]
        gid = kwargs["gid"]

        file_stats = os.stat(file_descriptor)
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

        try:
            if access_ok:
                os.lseek(file_descriptor, offset, os.SEEK_SET)
                bytes_read = os.read(file_descriptor, size)
                result["data"] = base64.standard_b64encode(
                    bytes_read
                ).decode("utf-8")
            else:
                logging.warning("Error during read request: Access denied")
                result.errno = errno.EACCES
                result.data = "Access denied"

        except Exception as e:
            logging.error("Error during read request: {}".format(e))
            result.errno = errno.EIO
            result.data = str(e)

        return result
