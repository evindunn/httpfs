import os
import logging
import errno
from .. import FuseOp, FuseOpResult


class FsyncOp(FuseOp):
    def handle(self, *args, **kwargs):
        result = FuseOpResult()
        file_desc = kwargs["file_descriptor"]

        try:
            if kwargs["datasync"]:
                os.fdatasync(file_desc)
            else:
                os.fsync(file_desc)
        except Exception as e:
            logging.error("Error during fsync request: {}".format(e))
            result.errno = errno.EIO
            result.data = str(e)

        return result
