import base64
import errno
import logging
import os
import stat
import time

from .. import FuseOp, FuseOpResult


class WriteOp(FuseOp):
    _BYTES_IN_MB = 1024**2

    def handle(self, *args, **kwargs):
        result = FuseOpResult()

        file_descriptor = kwargs["file_descriptor"]
        data = base64.standard_b64decode(kwargs["data"])
        offset = kwargs["offset"]

        uid = kwargs["uid"]
        gid = kwargs["gid"]

        file_stats = os.stat(file_descriptor)
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
                write_start_time = time.time()
                os.lseek(file_descriptor, offset, os.SEEK_SET)
                bytes_written = os.write(file_descriptor, data)
                result.data = bytes_written
                write_elapsed = time.time() - write_start_time
                logging.debug(
                    "Took {:.2f}s to write {} bytes ({:.2f} MB/s)".format(
                        write_elapsed,
                        bytes_written,
                        bytes_written / WriteOp._BYTES_IN_MB / write_elapsed
                    )
                )
            else:
                logging.warning("Error during write request: Access denied")
                result.errno = errno.EACCES
                result.data = "Access denied"

        except Exception as e:
            logging.error("Error during write request: {}".format(e))
            result.errno = errno.EIO
            result.data = str(e)

        return result
