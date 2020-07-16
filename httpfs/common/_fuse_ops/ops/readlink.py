import os
import logging
import errno

from .. import FuseOp, FuseOpResult


class ReadLinkOp(FuseOp):
    def handle(self, *args, **kwargs):
        result = FuseOpResult()

        link_path = kwargs["path"]

        try:
            target = os.readlink(link_path)
            if target.startswith("/"):
                target = os.path.relpath(target, self.server.get_fs_root())
            result["data"] = target
        except Exception as e:
            logging.error("Error during readlink request: {}".format(e))
            result.errno = errno.EIO
            result.data = str(e).encode("utf-8")

        return result
