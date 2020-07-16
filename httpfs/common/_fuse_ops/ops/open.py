import os
import logging
import errno
import stat

from .. import FuseOp, FuseOpResult


class OpenOp(FuseOp):
    def handle(self, *args, **kwargs):
        result = FuseOpResult()

        path = kwargs["path"]

        # Hardcode noatime for performance & longer ssd life
        flags = kwargs["flags"] | os.O_NOATIME

        uid = kwargs["uid"]
        gid = kwargs["gid"]

        dir_stats = os.stat(os.path.dirname(path))
        is_dir_owner = dir_stats.st_uid == uid
        is_dir_group = dir_stats.st_gid == gid

        if uid == 0:
            access_ok = True
        elif is_dir_owner:
            access_ok = dir_stats.st_mode & stat.S_IXUSR
        elif is_dir_group:
            access_ok = dir_stats.st_mode & stat.S_IXGRP
        else:
            access_ok = dir_stats.st_mode & stat.S_IXOTH

        if access_ok and os.path.exists(path):
            file_stats = os.stat(path)
            is_owner = file_stats.st_uid == uid
            is_group = file_stats.st_gid == gid

            read_requested = (
                flags & os.O_RDONLY or
                flags & os.O_RDWR or
                flags & os.O_EXCL
            )
            write_requested = (
                flags & os.O_WRONLY or
                flags & os.O_RDWR or
                flags & os.O_APPEND
            )

            if uid == 0:
                access_ok = True
            elif is_owner:
                if read_requested:
                    access_ok = file_stats.st_mode & stat.S_IRUSR
                elif write_requested:
                    access_ok = file_stats.st_mode & stat.S_IWUSR
            elif is_group:
                if read_requested:
                    access_ok = file_stats.st_mode & stat.S_IRGRP
                elif write_requested:
                    access_ok = file_stats.st_mode & stat.S_IWGRP
            else:
                if read_requested:
                    access_ok = file_stats.st_mode & stat.S_IROTH
                elif write_requested:
                    access_ok = file_stats.st_mode & stat.S_IROTH

        try:
            if access_ok:
                fd = os.open(path, flags)
                result["file_descriptor"] = fd
            else:
                result.errno = errno.EACCES
                result.data = "Access denied"
                logging.warning("Error during open request: Access denied")

        except Exception as e:
            logging.error("Error during open request: {}".format(e))
            result.errno = errno.EIO
            result.data = str(e)

        return result
