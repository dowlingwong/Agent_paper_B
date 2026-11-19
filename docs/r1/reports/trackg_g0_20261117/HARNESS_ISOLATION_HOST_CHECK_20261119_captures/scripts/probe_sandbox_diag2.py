"""G0 diagnostic 2: exact mount sequence with correct uid mapping.

Compares (a) the unit's single unshare() of all five namespaces with (b) split unshares (user first, map, then
mount/pid/net/cgroup), then the unit's exact bind sequence up to the /sys read-only remount. Read-only.
"""
import ctypes
import json
import os
import sys
import tempfile

CLONE_NEWNS = 0x00020000
CLONE_NEWCGROUP = 0x02000000
CLONE_NEWPID = 0x20000000
CLONE_NEWNET = 0x40000000
CLONE_NEWUSER = 0x10000000
MS_BIND = 4096
MS_REMOUNT = 32
MS_REC = 0x4000
MS_RDONLY = 1
MS_NOSUID = 2
MS_NODEV = 4
MS_PRIVATE = 1 << 18
PR_SET_DUMPABLE = 4

RO = ["/usr", "/bin", "/sbin", "/lib", "/lib32", "/lib64", "/libx32", "/etc"]
MS = ctypes.CDLL(None, use_errno=True)


def err():
    return os.strerror(ctypes.get_errno())


def mnt(src, tgt, flags, data=None, fstype=None):
    rc = MS.mount(src.encode() if src else None, tgt.encode() if tgt else None,
                  fstype.encode() if fstype else None, ctypes.c_ulong(flags), data.encode() if data else None)
    return rc, ("ok" if rc == 0 else err())


def write(path, text):
    with open(path, "w") as handle:
        handle.write(text)


def run(name, split, rootdir):
    uid, gid = os.getuid(), os.getgid()   # the unit captures these before unshare (inside the new user ns they are unmapped)
    pid = os.fork()
    if pid:
        _, status = os.waitpid(pid, 0)
        print("VARIANT", name, os.waitstatus_to_exitcode(status), flush=True)
        return
    out = {"variant": name, "split": split}
    try:
        MS.prctl(ctypes.c_int(PR_SET_DUMPABLE), ctypes.c_ulong(1), ctypes.c_ulong(0), ctypes.c_ulong(0))
        if split:
            rc = MS.unshare(ctypes.c_int(CLONE_NEWUSER))
            out["unshare_user"] = rc
            if rc != 0:
                raise RuntimeError(err())
            write("/proc/self/setgroups", "deny")
            write("/proc/self/uid_map", f"0 {uid} 1")
            write("/proc/self/gid_map", f"0 {gid} 1")
            out["maps"] = "ok"
            rc = MS.unshare(ctypes.c_int(CLONE_NEWNS | CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWCGROUP))
            out["unshare_rest"] = rc
        else:
            rc = MS.unshare(ctypes.c_int(CLONE_NEWUSER | CLONE_NEWNS | CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWCGROUP))
            out["unshare_all"] = rc
            if rc != 0:
                raise RuntimeError(err())
            write("/proc/self/setgroups", "deny")
            write("/proc/self/uid_map", f"0 {uid} 1")
            write("/proc/self/gid_map", f"0 {gid} 1")
            out["maps"] = "ok"
        out["uid_in_new_userns"] = os.getuid()
        out["m_rprivate"] = mnt(None, "/", MS_REC | MS_PRIVATE)
        root = tempfile.mkdtemp(prefix="sbd2_", dir=rootdir)
        out["root"] = root
        out["m_rootfs"] = mnt("tmpfs", root, MS_NOSUID | MS_NODEV, "mode=0755", "tmpfs")
        os.makedirs(root + "/tmp", exist_ok=True)
        out["m_tmp"] = mnt("tmpfs", root + "/tmp", MS_NOSUID | MS_NODEV, "mode=1777,size=8g", "tmpfs")
        bad = {}
        for path in RO:
            if not os.path.isdir(path):
                continue
            src = os.path.realpath(path)
            full = root + path
            os.makedirs(full, exist_ok=True)
            rc1, e1 = mnt(src, full, MS_BIND | MS_REC)
            rc2, e2 = mnt(None, full, MS_BIND | MS_REMOUNT | MS_NOSUID | MS_RDONLY)
            if rc1 or rc2:
                bad[path] = [e1, e2]
        out["ro_bad"] = bad
        os.makedirs(root + "/sys", exist_ok=True)
        out["sys_bind"] = mnt("/sys", root + "/sys", MS_BIND | MS_REC)
        out["sys_remount_ro_nosuid"] = mnt(None, root + "/sys", MS_BIND | MS_REMOUNT | MS_RDONLY | MS_NOSUID)
        out["sys_remount_ro"] = mnt(None, root + "/sys", MS_BIND | MS_REMOUNT | MS_RDONLY)
        out["sys_remount_bindonly"] = mnt(None, root + "/sys", MS_BIND | MS_REMOUNT)
        # second chance: detach the bind and redo it, as a fresh mount
        os.makedirs(root + "/sys2", exist_ok=True)
        out["sys2_bind"] = mnt("/sys", root + "/sys2", MS_BIND | MS_REC)
        out["sys2_remount"] = mnt(None, root + "/sys2", MS_BIND | MS_REMOUNT | MS_RDONLY | MS_NOSUID)
    except BaseException as error:  # noqa: BLE001
        out["exception"] = repr(error)
    print(json.dumps(out, sort_keys=True), flush=True)
    os._exit(0)


if __name__ == "__main__":
    rootdir = tempfile.mkdtemp(prefix="sbd2_base_")
    run("one_call_all_five", False, rootdir)
    run("split_user_then_rest", True, rootdir)
