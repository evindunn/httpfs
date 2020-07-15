import os
import logging
import errno
from .common import FuseOp, FuseOpResult


class FlushOp(FuseOp):
    def handle(self, *args, **kwargs):
        result = FuseOpResult()

        try:
            os.fsync(kwargs["file_descriptor"])
        except Exception as e:
            logging.error("Error during flush request: {}".format(e))
            result["errno"] = errno.EIO
            result["message"] = str(e)

        return result
