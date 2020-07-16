import os
import logging
import errno
from .. import FuseOp, FuseOpResult


class MkDirOp(FuseOp):
    def handle(self, *args, **kwargs):
        result = FuseOpResult()
        path = kwargs["path"]
        mode = kwargs["mode"]

        try:
            os.mkdir(path, mode=mode)
        except Exception as e:
            logging.error("Error during mkdir request: {}".format(e))
            result.errno = errno.EIO
            result.data = str(e)

        return result
