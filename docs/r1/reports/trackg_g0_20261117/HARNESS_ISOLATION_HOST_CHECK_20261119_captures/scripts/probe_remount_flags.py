"""G0 root-cause capture: read-only remount of a recursive bind of /sys, flag by flag.

The unit's sandbox binds /sys recursively and then remounts it with MS_BIND|MS_REMOUNT|MS_NOSUID|MS_RDONLY.
This probe shows that the remount succeeds once the mount's existing locked flags (nodev, noexec) are repeated,
and fails with EPERM when they are dropped -- the exact failure the unit reports on Ada as uid 1030.
"""
import ctypes
import json
import os
import sys
import tempfile

CLONE_NEWUSER = 0x10000000
CLONE_NEWNS = 0x00020000
MS_BIND = 4096
MS_REMOUNT = 32
MS_RDONLY = 1
MS_NOSUID = 2
MS_NODEV = 4
MS_NOEXEC = 8
MS_RELATIME = 0x800000
MS_REC = 0x4000
MS_PRIVATE = 1 << 18
PR_SET_DUMPABLE = 4
MS = ctypes.CDLL(None, use_errno=True)


def mnt(tgt, flags, fstype=None, src=None, data=None):
    rc = MS.mount(src.encode() if src else None, tgt.encode(), fstype.encode() if fstype else None,
                  ctypes.c_ulong(flags), data.encode() if data else None)
    return rc, ("ok" if rc == 0 else os.strerror(ctypes.get_errno()))


def main() -> int:
    uid, gid = os.getuid(), os.getgid()
    pid = os.fork()
    if pid:
        os.waitpid(pid, 0)
        return 0
    out = {}
    try:
        MS.prctl(ctypes.c_int(PR_SET_DUMPABLE), ctypes.c_ulong(1), ctypes.c_ulong(0), ctypes.c_ulong(0))
        out["unshare"] = MS.unshare(ctypes.c_int(CLONE_NEWUSER | CLONE_NEWNS))
        for path, text in (("/proc/self/setgroups", "deny"), ("/proc/self/uid_map", f"0 {uid} 1"),
                           ("/proc/self/gid_map", f"0 {gid} 1")):
            fd = os.open(path, os.O_WRONLY)
            os.write(fd, text.encode())
            os.close(fd)
        out["uid_in_new_userns"] = os.getuid()
        out["m_rprivate"] = mnt("/", MS_REC | MS_PRIVATE)
        root = tempfile.mkdtemp(prefix="g0_remount_")
        out["root"] = root
        out["m_rootfs"] = mnt(root, MS_NOSUID | MS_NODEV, fstype="tmpfs", src="tmpfs", data="mode=0755")
        out["targets"] = {}
        variants = {
            "unit_flags_BIND_REMOUNT_NOSUID_RDONLY": MS_BIND | MS_REMOUNT | MS_NOSUID | MS_RDONLY,
            "plus_NODEV": MS_BIND | MS_REMOUNT | MS_NOSUID | MS_RDONLY | MS_NODEV,
            "plus_NODEV_NOEXEC": MS_BIND | MS_REMOUNT | MS_NOSUID | MS_RDONLY | MS_NODEV | MS_NOEXEC,
            "host_flags_NOSUID_NODEV_NOEXEC_RDONLY_RELATIME":
                MS_BIND | MS_REMOUNT | MS_NOSUID | MS_NODEV | MS_NOEXEC | MS_RDONLY | MS_RELATIME,
        }
        for name, flags in variants.items():
            target = f"{root}/{name}"
            os.makedirs(target, exist_ok=True)
            # bind /sys onto target explicitly
            bind = mnt(target, MS_BIND | MS_REC, src="/sys")
            out["targets"][name] = {"bind_sys_recursive": bind, "remount": mnt(target, flags)}
    except BaseException as error:  # noqa: BLE001
        out["exception"] = repr(error)
    print(json.dumps(out, indent=2, sort_keys=True), flush=True)
    os._exit(0)


if __name__ == "__main__":
    sys.exit(main())
