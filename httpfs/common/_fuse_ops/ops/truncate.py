import errno
import logging
import os
from .. import FuseOp, FuseOpResult


class TruncateOp(FuseOp):
    def handle(self, *args, **kwargs):
        result = FuseOpResult()

        path = kwargs["path"]
        length = kwargs["length"]

        try:
            with open(path, 'r+') as f:
                f.truncate(length)
        except Exception as e:
            logging.error("Error during truncate request: {}".format(e))
            result.errno = errno.EIO
            result.data = str(e)

        return result
