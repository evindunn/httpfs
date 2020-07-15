import os
import stat
from .common import FuseOp, FuseOpType, FuseOpResult


class AccessOp(FuseOp):
    def handle(self, *args, **kwargs):
        path = kwargs["path"]
        mode = kwargs["mode"]
        uid = kwargs["uid"]
        gid = kwargs["gid"]
        file_stats = os.stat(path)

        is_owner = file_stats.st_uid == uid
        is_group = file_stats.st_gid == gid
        read_requested = bool(mode & os.R_OK)
        write_requested = bool(mode & os.W_OK)
        execute_requested = bool(mode & os.X_OK)
        exists_requested = mode == os.F_OK

        access_ok = True

        # Exists requested
        if exists_requested:
            access_ok = os.path.exists(path)

        # Owner access
        if is_owner:
            owner_readable = bool(file_stats.st_mode & stat.S_IRUSR)
            owner_writeable = bool(file_stats.st_mode & stat.S_IWUSR)
            owner_executable = bool(file_stats.st_mode & stat.S_IXUSR)
            if read_requested:
                access_ok = access_ok and owner_readable
            if write_requested:
                access_ok = access_ok and owner_writeable
            if execute_requested:
                access_ok = access_ok and owner_executable
        # Group access
        elif is_group:
            group_readable = bool(file_stats.st_mode & stat.S_IRGRP)
            group_writeable = bool(file_stats.st_mode & stat.S_IWGRP)
            group_executable = bool(file_stats.st_mode & stat.S_IXGRP)
            if read_requested:
                access_ok = access_ok and group_readable
            if write_requested:
                access_ok = access_ok and group_writeable
            if execute_requested:
                access_ok = access_ok and group_executable
        # World access
        else:
            world_readable = bool(file_stats.st_mode & stat.S_IROTH)
            world_writeable = bool(file_stats.st_mode & stat.S_IWOTH)
            world_executable = bool(file_stats.st_mode & stat.S_IXGRP)
            if read_requested:
                access_ok = access_ok and world_readable
            if write_requested:
                access_ok = access_ok and world_writeable
            if execute_requested:
                access_ok = access_ok and world_executable

        return FuseOpResult({
            "type": FuseOpType.ACCESS,
            "result": access_ok
        })
