import os
import logging
import errno

from .. import FuseOp, FuseOpResult


class RmDirOp(FuseOp):
    def handle(self, *args, **kwargs):
        result = FuseOpResult()

        path = kwargs["path"]
        message = None
        _errno = 0

        try:
            os.rmdir(path)
        except FileNotFoundError as e:
            logging.error("{} not found".format(path))
            _errno = errno.ENOENT
            message = e
        except OSError as e:
            _errno = e.errno
            message = e
        except Exception as e:
            _errno = errno.EIO
            message = e

        if _errno != 0:
            logging.error("Error during rmdir request: {}".format(message))
            result.errno = _errno
            result.data = str(message)

        return result
