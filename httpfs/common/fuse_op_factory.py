from ._fuse_ops.common import FuseOpType
from ._fuse_ops.ops import *


class FuseOpFactory:
    _HANDLERS = {
        FuseOpType.ACCESS: AccessOp,
        FuseOpType.CREATE: CreateOp,
        FuseOpType.CHMOD: ChmodOp,
        FuseOpType.CHOWN: ChownOp,
        FuseOpType.FLUSH: FlushOp,
        FuseOpType.FSYNC: FsyncOp,
        FuseOpType.GET_ATTR: GetAttrOp,
        FuseOpType.LINK: LinkOp,
        FuseOpType.MKDIR: MkDirOp,
        FuseOpType.MKNOD: MkNodOp,
        FuseOpType.OPEN: OpenOp,
        FuseOpType.READ: ReadOp,
        FuseOpType.READDIR: ReadDirOp,
        FuseOpType.RELEASE: ReleaseOp,
        FuseOpType.RENAME: RenameOp,
        FuseOpType.RM_DIR: RmDirOp
    }

    @staticmethod
    def get_op_handler(op):
        """
        Returns an instance of thee proper handler based on the Op type
        :param op: Type of operation
        :return: Handler for the operation
        """
        handler_cls = FuseOpFactory._HANDLERS[op]
        return handler_cls()
