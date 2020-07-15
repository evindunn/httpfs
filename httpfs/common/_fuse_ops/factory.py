from .common import FuseOpType
from .access import AccessOp
from .create import CreateOp
from .chmod import ChmodOp
from .chown import ChownOp
from .flush import FlushOp
from .fsync import FsyncOp
from .getattr import GetAttrOp
from .link import LinkOp


class FuseOpFactory:
    _HANDLERS = {
        FuseOpType.ACCESS: AccessOp,
        FuseOpType.CREATE: CreateOp,
        FuseOpType.CHMOD: ChmodOp,
        FuseOpType.CHOWN: ChownOp,
        FuseOpType.FLUSH: FlushOp,
        FuseOpType.FSYNC: FsyncOp,
        FuseOpType.GET_ATTR: GetAttrOp,
        FuseOpType.LINK: LinkOp
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

