# pylint: disable=unused-argument

"""
Contains a class to be passed to fusepy.FUSE to handle filesystem operations
"""

import base64
import binascii
import errno
import json
import logging
import time
import traceback

import ujson
from fuse import Operations, FuseOSError, fuse_get_context
from pytcp_message import TcpClient

from .fuse_logger import _FuseLogger
from ..common import FuseOpType


class HttpFsClient(_FuseLogger, Operations):
    """
    A FUSE client that talks to an HttpFs server
    """

    _ONE_KILOBYTE = 1024
    _RETRIES = 3

    # Unimplemented filesystem ops
    bmap = None
    getxattr = None
    listxattr = None

    def __init__(self, hostname, port, api_key=None, ca_file=None):
        """
        Constructor
        :param hostname: The server to connect to
        :param port: The server's port
        :param api_key: Key to use for authentication
        :param ca_file: Optional CA cert file if the server uses HTTPS
        """
        self._server_addr = (hostname, port)
        self._tcp_client = TcpClient(self._server_addr)
        self._api_key = api_key
        self._retries = HttpFsClient._RETRIES

    def __del__(self):
        try:
            self._tcp_client.stop()
        except:
            pass

    def _send_request(self, request_type: FuseOpType, **kwargs):
        """
        Sends an HttpFsRequest of the given type with the given kwargs
        :param request_type: The request type to send
        :param kwargs: The arguments for the request
        :return: The HttpFsResponse
        """
        request = {
            "type": request_type,
            "api_key": self._api_key,
            **kwargs
        }

        try:
            try:
                req_as_json = ujson.dumps(request)
                # Don't want to log all the bytes
                if request_type not in [FuseOpType.READ, FuseOpType.WRITE]:
                    logging.debug(req_as_json)
                self._tcp_client.send(req_as_json)

                response = self._tcp_client.receive()
                return ujson.loads(response)

            # TODO: More descriptive errno's based on error received
            except BrokenPipeError as excp:
                if self._retries > 0:
                    self._retries -= 1
                    logging.warning(
                        "Server disconnected: {}, retrying...".format(excp)
                    )
                    self._tcp_client = TcpClient(self._server_addr)
                    return self._send_request(request_type, **kwargs)
                else:
                    logging.error(
                        "Server disconnected. Giving up after {} tries".format(
                            HttpFsClient._RETRIES
                        )
                    )
            except json.JSONDecodeError as excp:
                raise FuseOSError(errno.EINVAL) from excp
            except OSError as excp:
                raise FuseOSError(excp.errno) from excp
            except Exception as excp:
                raise FuseOSError(errno.EIO) from excp

        except FuseOSError as exception:
            if exception.errno != errno.ECONNRESET:
                self._retries = HttpFsClient._RETRIES
            logging.debug(traceback.format_exc())
            raise FuseOSError(exception.errno) from exception

        self._retries = HttpFsClient._RETRIES

    def access(self, path, mode):
        """
        Check file access permissions
        :param path: Path to file to check
        :param mode: Mode to test
        :return:
        """
        uid, gid, _ = fuse_get_context()
        response_obj = self._send_request(
            FuseOpType.ACCESS,
            path=path,
            mode=mode,
            uid=uid,
            gid=gid
        )
        # Access returns a boolean in it's "data" field: whether the user has
        # access
        if response_obj["errno"] != 0 or not response_obj["data"]:
            raise FuseOSError(errno.EACCES)

    def create(self, path, mode, fh=None):
        """
        Create and open a file
        If the file does not exist, first create it with the specified mode,
        and then open it.
        :param path: Path to file
        :param mode: Mode to create the file with
        :param fh: Optional file handle for the file we're creating
        :return: If fh=None, return file handle for the new file; Otherwise
        use fh to create the new file and return zero on success
        """
        uid, gid, _ = fuse_get_context()
        response_obj = self._send_request(
            FuseOpType.CREATE,
            path=path,
            mode=mode,
            uid=uid,
            gid=gid
        )

        if response_obj["errno"] != 0:
            logging.error(response_obj["data"])
            raise FuseOSError(response_obj["errno"])

        return response_obj["data"]

    def chmod(self, path, mode):
        """
        Change permissions on path to mode
        :param path: Path to file/directory
        :param mode: New permissions
        """
        uid, gid, _ = fuse_get_context()
        response_obj = self._send_request(
            FuseOpType.CHMOD,
            path=path,
            mode=mode,
            uid=uid,
            gid=gid
        )

        if response_obj["errno"] != 0:
            logging.error(response_obj["data"])
            raise FuseOSError(response_obj["errno"])

    def chown(self, path, uid, gid):
        """
        Change ownership on path to uid and gid
        :param path: Path to file/directory
        :param uid: New user id
        :param gid: New group id
        """
        caller_uid, caller_gid, _ = fuse_get_context()
        response_obj = self._send_request(
            FuseOpType.CHOWN,
            path=path,
            uid=uid,
            gid=gid,
            caller_uid=caller_uid,
            caller_gid=caller_gid
        )

        if response_obj["errno"] != 0:
            logging.error(response_obj["data"])
            raise FuseOSError(response_obj["errno"])

    def flush(self, path, fh=None):
        """
        Possibly flush cached data.
        Flush is called on each close() of a file descriptor, as opposed
        to release() which is called on the close of the last file descriptor
        for a file
        :param path: Path to file
        :param fh: Optional file handle for the file to flush
        :return:
        """
        response_obj = self._send_request(
            FuseOpType.FLUSH,
            file_descriptor=fh
        )

        if response_obj["errno"] != 0:
            logging.error(response_obj["data"])
            raise FuseOSError(response_obj["errno"])

    def fsync(self, path, datasync=False, fh=None):
        """
        Synchronize file contents
        If the datasync parameter is True, then only the user data should
        be flushed, not the meta data.
        :param path: Path to file file to sync
        :param datasync: Whether to sync data only an skip metadata
        :param fh: Optional file handle for the file to sync
        :return:
        """
        response_obj = self._send_request(
            FuseOpType.FSYNC,
            file_descriptor=fh,
            datasync=datasync
        )

        if response_obj["errno"] != 0:
            logging.error(response_obj["data"])
            raise FuseOSError(response_obj["errno"])

    def getattr(self, path, fh=None):
        """
        Similar to stat(), retrieve file attributes
        :param path: path to the file
        :param fh: None if the current file isn't open
        :return:
        """
        response_obj = self._send_request(FuseOpType.GET_ATTR, path=path)
        if response_obj["errno"] == 0:
            return response_obj["data"]

        raise FuseOSError(response_obj["errno"])

    def link(self, target, source):
        """
        Create a hard link pointing to source named target
        :param target: Original file
        :param source: Link name
        :return:
        """
        response_obj = self._send_request(
            FuseOpType.LINK,
            target=target,
            source=source
        )
        if response_obj["errno"] != 0:
            logging.error(response_obj["data"])
            raise FuseOSError(response_obj["errno"])

    def mkdir(self, path, mode):
        """
        Create a new directory
        :param path: Path to new directory
        :param mode: Permissions for the new directory
        :return:
        """
        response_obj = self._send_request(
            FuseOpType.MKDIR,
            path=path,
            mode=mode
        )
        if response_obj["errno"] != 0:
            logging.error(response_obj["data"])
            raise FuseOSError(response_obj["errno"])

    def mknod(self, path, mode, dev):
        """
        Create a file node
        This is called for creation of all non-directory, non-symlink nodes. If
        the filesystem defines a create() method, then for regular files that
        will be called instead.
        :param path: Path to new node (file)
        :param mode: Permissions for new node
        :param dev: Whether node is a 'special file' (i/o device)
        :return:
        """
        response_obj = self._send_request(
            FuseOpType.MKNOD,
            path=path,
            mode=mode,
            device=dev
        )
        if response_obj["errno"] != 0:
            logging.error(response_obj["data"])
            raise FuseOSError(response_obj["errno"])

    def open(self, path, flags):
        """
        Opens a file
        :param path: Path to file to open
        :param flags: See https://docs.python.org/3/library/functions.html#open
        :return:
        """
        uid, gid, _ = fuse_get_context()
        response_obj = self._send_request(
            FuseOpType.OPEN,
            path=path,
            flags=flags,
            uid=uid,
            gid=gid
        )

        if response_obj["errno"] != 0:
            logging.error(response_obj["data"])
            raise FuseOSError(response_obj["errno"])

        return response_obj["data"]

    def read(self, path, size, offset, fh=None):
        """
        Read at most size bytes from the file at path or fh. Start reading
        at offset
        :param path: Path to file
        :param size: Number of bytes to read
        :param offset: Offset from byte 0 at which to start reading
        :param fh: Optional file handle
        :return:
        """
        uid, gid, _ = fuse_get_context()
        response_obj = self._send_request(
            FuseOpType.READ,
            file_descriptor=fh,
            size=size,
            offset=offset,
            uid=uid,
            gid=gid
        )

        if response_obj["errno"] != 0:
            logging.error(
                "Read failed for %s: '%s'",
                response_obj["data"],
                path
            )
            raise FuseOSError(response_obj["errno"])

        try:
            return base64.standard_b64decode(response_obj["data"])
        except binascii.Error as encoding_error:
            logging.error("Error decoding read data: '%s'", encoding_error)
            raise FuseOSError(errno.EIO)

    def readdir(self, path, fh=None):
        """
        Return the directory listing at path
        :param path: Path to directory to list
        :param fh: Optional file handle for the directory
        :return: List of directory entries
        """
        uid, gid, _ = fuse_get_context()
        response_obj = self._send_request(
            FuseOpType.READDIR,
            path=path,
            uid=uid,
            gid=gid
        )
        if response_obj["errno"] == 0:
            return response_obj["data"]

        raise FuseOSError(response_obj["errno"])

    def readlink(self, link):
        """
        Return a string representing the path to which the symbolic link points.
        :param link: Path to link
        :return: Path to file that link points at
        """
        response_obj = self._send_request(
            FuseOpType.READLINK,
            link_path=link
        )
        if response_obj["errno"] == 0:
            return response_obj["data"]

        raise FuseOSError(response_obj["errno"])

    def release(self, path, fh=None):
        """
        Release path's write lock
        :param path: Path to file
        :param fh: Optional file handle
        :return:
        """
        response_obj = self._send_request(
            FuseOpType.RELEASE,
            file_descriptor=fh
        )
        if response_obj["errno"] != 0:
            logging.error(response_obj["data"])
            raise FuseOSError(response_obj["errno"])

    def rename(self, old, new):
        """
        Move file at path old to path new
        :param old: Path to 'old' file
        :param new: Path to 'new' file
        :return:
        """
        uid, gid, _ = fuse_get_context()
        response_obj = self._send_request(
            FuseOpType.RENAME,
            old_path=old,
            new_path=new,
            uid=uid,
            gid=gid
        )
        if response_obj["errno"] != 0:
            logging.error(response_obj["data"])
            raise FuseOSError(response_obj["errno"])

    def rmdir(self, path, *args, dir_fh=None):
        """
        Removes the directory at path
        :param path: Path to directory to move
        :param args: Optional remove args
        :param dir_fh: Optional file handle for the directory
        :return:
        """
        response_obj = self._send_request(
            FuseOpType.RM_DIR,
            path=path
        )
        if response_obj["errno"] != 0:
            logging.error(response_obj["data"])
            raise FuseOSError(response_obj["errno"])

    def statfs(self, path):
        """
        Get file system statistics for the filesystem at path
        :param path: Path to the filesystem
        :return:
        """
        response_obj = self._send_request(FuseOpType.STAT_FS, path=path)

        if response_obj["errno"] == 0:
            return response_obj["data"]

        raise FuseOSError(response_obj["errno"])

    def symlink(self, target, source):
        """
        Create a symlink that points to target and is named source
        :param target: Real file
        :param source: New symlink
        :return:
        """
        response_obj = self._send_request(
            FuseOpType.SYMLINK,
            target=target,
            source=source
        )
        if response_obj["errno"] != 0:
            logging.error(response_obj["data"])
            raise FuseOSError(response_obj["errno"])

    def truncate(self, path, length, fh=None):
        """
        Resize path to length length
        :param path: Path to file to truncate
        :param length: New length of file
        :param fh: Optional file handle
        :return:
        """
        response_obj = self._send_request(
            FuseOpType.TRUNCATE,
            path=path,
            length=length
        )
        if response_obj["errno"] != 0:
            logging.error(response_obj["data"])
            raise FuseOSError(response_obj["errno"])

    def unlink(self, path, *args, dir_fh=None):
        """
        Remove (delete) the file path.
        :param path: Path to file to delete
        :param args: Optional args
        :param dir_fh: Optional directory file handle
        :return:
        """
        uid, gid, _ = fuse_get_context()
        response_obj = self._send_request(
            FuseOpType.UNLINK,
            path=path,
            uid=uid,
            gid=gid
        )
        if response_obj["errno"] != 0:
            logging.error(response_obj["data"])
            raise FuseOSError(response_obj["errno"])

    def utimens(self, path, times=None):
        """
        Set the access and modified times of the file specified by path.
        If ns is specified, it must be a 2-tuple of the form
            (atime_ns, mtime_ns) where each member is an int expressing
            nanoseconds.
        If times is not None, it must be a 2-tuple of the form (atime, mtime)
            where each member is an int or float expressing seconds.
        If times is None and ns is unspecified, this is equivalent to
            specifying ns=(atime_ns, mtime_ns) where both times are the
            current time.
        :param path: Path to file to update
        :param times: Time tuple
        :return:
        """
        uid, gid, _ = fuse_get_context()
        response_obj = self._send_request(
            FuseOpType.UTIMENS,
            path=path,
            times=times,
            uid=uid,
            gid=gid
        )
        if response_obj["errno"] != 0:
            logging.error(response_obj["data"])
            raise FuseOSError(response_obj["errno"])

    def write(self, path, data, offset, fh=None):
        """
        Write data to path at offset
        :param path: Path to file to write to
        :param data: Data (bytes) to write
        :param offset: Byte at which to start writing
        :param fh: Optional file handle
        :return: The number of bytes actually written
        """
        start_time = time.time()
        uid, gid, _ = fuse_get_context()

        response_obj = self._send_request(
            FuseOpType.WRITE,
            file_descriptor=fh,
            data=base64.standard_b64encode(data).decode("utf-8"),
            offset=offset,
            uid=uid,
            gid=gid
        )

        if response_obj["errno"] != 0:
            logging.error(response_obj["data"])
            return FuseOSError(response_obj["errno"])

        bytes_written = response_obj["data"]
        elapsed_time = time.time() - start_time

        # Print 1/10 of the time
        logging.debug(
            "Took {:.2f}s to write {} bytes ({:.2f} MB/s)".format(
                elapsed_time,
                bytes_written,
                bytes_written / 1024**2 / elapsed_time
            )
        )

        return bytes_written
