import os
import logging
import errno
from .. import FuseOp, FuseOpResult


class MkNodOp(FuseOp):
    def handle(self, *args, **kwargs):
        result = FuseOpResult()
        path = kwargs["path"]
        mode = kwargs["mode"]
        device = kwargs["device"]

        try:
            os.mknod(path, mode=mode, device=device)
        except Exception as e:
            logging.error("Error during mknod request: {}".format(e))
            result.errno = errno.EIO
            result.data = str(e)

        return result
