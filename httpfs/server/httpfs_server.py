import os
import socket
import threading
import ssl
import logging
import ujson
from pytcp_message import TcpServer

from ._httpfs_request_handler import _HttpFsRequestHandler
from ..common.credentials.TextCredStore import TextCredStore


class HttpFsServer(TcpServer):
    """
    Server that implements the HttpFsRequestHandler methods
    """

    # TCP keepAlive activates after 1 second of idle connection,
    # sends a ping every 3 seconds, and closes after 1 failed ping
    _tcp_keepidle_secs = 1
    _tcp_keep_interval_secs = 3
    _tcp_keep_max_fails = 1

    def __init__(self, port, fs_root, cred_store_file=None, tls_key=None, tls_cert=None):
        """
        :param port: Port to run the server on
        :param fs_root: The HttpFS filesystem root on the server
        :param tls_key: Optional key file for HTTPS
        :param tls_cert: Optional cert file for HTTPS
        """
        super().__init__(port, address="0.0.0.0")

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
        self._fs_root = os.path.realpath(fs_root)
        self._fs_lock = threading.Lock()
        #
        # if cred_store_file is not None:
        #     self._cred_store = TextCredStore(cred_store_file)
        # else:
        #     self._cred_store = None
        #
        # # This line fixes the HTTP/1.1 keep-alive delay
        # self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        #
        # # These options configure TCP keep-alive, which is different
        # self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        # self.socket.setsockopt(
        #     socket.IPPROTO_TCP,
        #     socket.TCP_KEEPIDLE,
        #     HttpFsServer._tcp_keepidle_secs
        # )
        # self.socket.setsockopt(
        #     socket.IPPROTO_TCP,
        #     socket.TCP_KEEPINTVL,
        #     HttpFsServer._tcp_keep_interval_secs
        # )
        # self.socket.setsockopt(
        #     socket.IPPROTO_TCP,
        #     socket.TCP_KEEPCNT,
        #     HttpFsServer._tcp_keep_max_fails
        # )

        if not os.path.exists(self._fs_root):
            raise RuntimeError(
                "Filesystem root '{}' doesn't exist".format(self._fs_root)
            )

        # Request handlers
        self.add_request_handler(
            lambda req, res: HttpFsServer._add_server(self, req, res)
        )
        self.add_request_handler(HttpFsServer._log_request)
        self.add_request_handler(HttpFsServer._json_parse)
        self.add_request_handler(HttpFsServer._delegate_response)

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

    @staticmethod
    def _log_request(req, _):
        logging.getLogger().debug("{}:{}".format(*req.get_client_address()))
        return True

    @staticmethod
    def _json_parse(req, _):
        req.set_content(ujson.loads(req.get_content().decode("utf-8")))
        return True

    @staticmethod
    def _delegate_response(req, res):
        res.set_content("MESSAGE RECEIVED".encode("utf-8"))
        return True
