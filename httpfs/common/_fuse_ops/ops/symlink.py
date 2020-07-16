import errno
import logging
import os
from .. import FuseOp, FuseOpResult


class SymlinkOp(FuseOp):
    def handle(self, *args, **kwargs):
        result = FuseOpResult()

        source = kwargs["source"]
        target = kwargs["target"]

        try:
            os.symlink(source, target)
        except Exception as e:
            logging.error("Error during symlink request: {}".format(e))
            result.errno = errno.EIO

        return result
