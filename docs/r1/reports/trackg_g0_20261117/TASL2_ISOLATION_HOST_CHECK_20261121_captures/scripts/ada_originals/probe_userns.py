"""G0 host check: the exact unshare() flags the isolation launcher uses (user, mount, PID, network, cgroup),
plus a real mount inside the new mount namespace, mapped to the caller's uid (as the unit's launcher does).

Mirrors ar_isolated.py's launcher rather than the unshare(1) CLI so the result is the unit's own path. Every
child flushes before _exit so the capture file holds the namespace inode ids.
"""
import ctypes
import json
import os
import sys

CLONE_NEWNS = 0x00020000
CLONE_NEWCGROUP = 0x02000000
CLONE_NEWPID = 0x20000000
CLONE_NEWNET = 0x40000000
CLONE_NEWUSER = 0x10000000
MS_NOSUID = 2
MS_NODEV = 4
PR_SET_DUMPABLE = 4

ALL = CLONE_NEWUSER | CLONE_NEWNS | CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWCGROUP
MS = ctypes.CDLL(None, use_errno=True)


def probe(name, flags, map_ids):
    uid, gid = os.getuid(), os.getgid()   # capture before unshare: unmapped inside the new user namespace
    pid = os.fork()
    if pid:
        _, status = os.waitpid(pid, 0)
        return os.waitstatus_to_exitcode(status)
    out = {"probe": name, "caller_uid": uid, "flags": hex(flags)}
    try:
        MS.prctl(ctypes.c_int(PR_SET_DUMPABLE), ctypes.c_ulong(1), ctypes.c_ulong(0), ctypes.c_ulong(0))
        rc = MS.unshare(ctypes.c_int(flags))
        out["unshare_rc"] = rc
        out["unshare_errno"] = ctypes.get_errno()
        if rc != 0:
            out["unshare_error"] = os.strerror(ctypes.get_errno())
            print(json.dumps(out, sort_keys=True), flush=True)
            os._exit(1)
        if map_ids:
            for path, text in (("/proc/self/setgroups", "deny"),
                               ("/proc/self/uid_map", f"0 {uid} 1"),
                               ("/proc/self/gid_map", f"0 {gid} 1")):
                fd = os.open(path, os.O_WRONLY)
                os.write(fd, text.encode())
                os.close(fd)
            out["mapped_uid_in_new_userns"] = os.getuid()
        for kind in ("user", "mnt", "pid", "net", "cgroup"):
            out[kind] = os.readlink(f"/proc/self/ns/{kind}")
        # a real mount in the new mount namespace; a tmpfs at a fresh root directory (as the sandbox does)
        root = f"/tmp/g0_userns_{os.getpid()}"
        os.makedirs(root, exist_ok=True)
        rc = MS.mount(b"tmpfs", root.encode(), b"tmpfs", ctypes.c_ulong(MS_NOSUID | MS_NODEV), b"mode=0755")
        out["tmpfs_mount_rc"] = rc
        out["tmpfs_mount_result"] = "ok" if rc == 0 else os.strerror(ctypes.get_errno())
        if rc == 0:
            out["tmpfs_mounted"] = os.path.ismount(root)
        print(json.dumps(out, sort_keys=True), flush=True)
    except BaseException as error:  # noqa: BLE001
        out["exception"] = repr(error)
        print(json.dumps(out, sort_keys=True), flush=True)
        os._exit(1)
    os._exit(0)


def main():
    results = {
        "userns_only": probe("userns_only", CLONE_NEWUSER, False),
        "user_mount_pid_net": probe("user_mount_pid_net",
                                    CLONE_NEWUSER | CLONE_NEWNS | CLONE_NEWPID | CLONE_NEWNET, True),
        "launcher_all_five_one_call": probe("launcher_all_five_one_call", ALL, True),
    }
    print("RESULT", json.dumps(results, sort_keys=True))
    return 0 if all(code == 0 for code in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
