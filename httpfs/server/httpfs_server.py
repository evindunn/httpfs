import os
import socket
import threading
import ssl
import logging
from datetime import datetime

import ujson
from pytcp_message import TcpServer

from ..common import FuseOpFactory, FuseOpType
from ..common.credentials.TextCredStore import TextCredStore


class HttpFsServer(TcpServer):
    """
    Server that implements the HttpFsRequestHandler methods
    """

    def __init__(self, port, fs_root, cred_store_file=None, tls_key=None, tls_cert=None):
        """
        :param port: Port to run the server on
        :param fs_root: The HttpFS filesystem root on the server
        :param tls_key: Optional key file for HTTPS
        :param tls_cert: Optional cert file for HTTPS
        """
        super().__init__(port, address="0.0.0.0")
        self._client_timeout = 300
        self._fs_root = os.path.realpath(fs_root)

        # has_tls_key = tls_key is not None and os.path.exists(tls_key)
        # has_tls_crt = tls_cert is not None and os.path.exists(tls_cert)
        # if has_tls_key and has_tls_crt:
        #     self.socket = ssl.wrap_socket(
        #         self.socket,
        #         keyfile=tls_key,
        #         certfile=tls_cert,
        #         server_side=True
        #     )
        #
        #
        # if cred_store_file is not None:
        #     self._cred_store = TextCredStore(cred_store_file)
        # else:
        #     self._cred_store = None
        #

        # This line fixes TCP keep-alive delay
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        if not os.path.exists(self._fs_root):
            raise RuntimeError(
                "Filesystem root '{}' doesn't exist".format(self._fs_root)
            )

        # Request handlers
        self.add_request_handler(
            lambda req, res: HttpFsServer._add_server(self, req, res)
        )
        self.add_request_handler(HttpFsServer._json_parse)
        self.add_request_handler(HttpFsServer._log_request)
        self.add_request_handler(HttpFsServer._serve_response)
        self.add_request_handler(HttpFsServer._log_response)

    def get_fs_root(self):
        return self._fs_root

    def get_fs_lock(self):
        return self._fs_lock

    def get_cred_store(self):
        # return self._cred_store
        return None

    @staticmethod
    def _add_server(server, req, _):
        req.server = server
        return True

    @staticmethod
    def _json_parse(req, _):
        as_dict = ujson.loads(req.get_content().decode("utf-8"))

        # Resolve path based on FS root
        if "path" in as_dict.keys():
            new_path = os.path.join(
                req.server.get_fs_root(),
                as_dict["path"].lstrip("/")
            )
            as_dict["path"] = new_path

        req.content_json = as_dict
        return True

    @staticmethod
    def _log_request(req, _):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.getLogger().debug(
            "[{}] <-- {}:{} {}".format(
                ts,
                *req.get_client_address(),
                FuseOpType(req.content_json["type"]).name
            )
        )
        return True

    @staticmethod
    def _serve_response(req, res):
        req_content = req.content_json
        handler = FuseOpFactory.get_op_handler(req_content["type"])
        result_json = handler.handle(**req_content).to_json()
        res.set_content(result_json.encode("utf-8"))
        return True

    @staticmethod
    def _log_response(req, _):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.getLogger().debug(
            "[{}] --> {}:{} {}".format(
                ts,
                *req.get_client_address(),
                FuseOpType(req.content_json["type"]).name
            ),
        )
        return True
