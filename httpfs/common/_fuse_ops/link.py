import os
import logging
import errno
from .common import FuseOp, FuseOpResult


class LinkOp(FuseOp):
    def handle(self, *args, **kwargs):
        result = FuseOpResult()
        target_path = kwargs["target"]
        source_path = kwargs["source"]

        try:
            os.link(source_path, target_path)
        except Exception as e:
            logging.error("Error during link request: {}".format(e))
            result["errno"] = errno.EIO
            result["message"] = str(e)

        return result
