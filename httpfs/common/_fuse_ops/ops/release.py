import os
import logging
import errno

from .. import FuseOp, FuseOpResult


class ReleaseOp(FuseOp):
    def handle(self, *args, **kwargs):
        result = FuseOpResult()
        fd = kwargs["file_descriptor"]

        try:
            os.close(fd)
        except Exception as e:
            logging.error("Error during release request: {}".format(e))
            result.errno = errno.EIO
            result.data = str(e)

        return result
