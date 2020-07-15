from enum import Enum, auto, unique

from httpfs.common._fuse_ops import FuseOpType


class HttpFsRequest:
    """
    Class representing a filesystem operation with JSON
    serialization/deserialization methods
    """

    def __init__(self, op_type: FuseOpType, args_dict, api_key=None):
        """
        Class cooresponding to the schema
        https://raw.githubusercontent.com/httpfs/httpfs/master/HttpFsRequest.schema.json
        :param op_type: One of the operation types above
        :param args_dict: Arguments for the operation
        :param api_key: API key for authentication with the server
        """
        self._type = op_type
        self._args = args_dict
        self._api_key = api_key

    def get_type(self):
        return self._type

    def get_args(self):
        return self._args

    @staticmethod
    def from_dict(json_dict):
        try:
            for k in ["type", "args"]:
                if k not in json_dict.keys():
                    raise ValueError("Missing key '{}'".format(k))
            for k, t in [("type", int), ("args", dict)]:
                if not isinstance(json_dict[k], t):
                    raise ValueError("Key '{}' should be a {}".format(k, t))

            return HttpFsRequest(
                json_dict["type"],
                json_dict["args"]
            )
        except Exception as e:
            raise ValueError("Invalid JSON for {}: '{}'".format(__class__, e))

    def as_dict(self):
        # See HttpFsRequest.schema.json
        return {
            "type": self._type,
            "args": self._args
        }
