"""G0 diagnostic: reproduce the sandbox mount sequence (/sys recursive bind then read-only remount) in a new
user+mount(+pid/net/cgroup) namespace, with the flags split, to find why the unit's sandbox probe fails at
'read-only /sys' on this host. Read-only diagnostic; it changes nothing on the host.
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

RO = ["/usr", "/bin", "/sbin", "/lib", "/lib32", "/lib64", "/libx32", "/etc"]
MS = ctypes.CDLL(None, use_errno=True)


def mnt(src, tgt, flags, data=None):
    rc = MS.mount(src.encode() if src else None, tgt.encode() if tgt else None,
                  None, ctypes.c_ulong(flags), data.encode() if data else None)
    err = ctypes.get_errno()
    return rc, (os.strerror(err) if rc != 0 else "ok")


def write(path, text):
    with open(path, "w") as handle:
        handle.write(text)


def variant(name, flags, rootdir):
    pid = os.fork()
    if pid:
        _, status = os.waitpid(pid, 0)
        return name, os.waitstatus_to_exitcode(status)
    out = {"variant": name, "flags": hex(flags)}
    try:
        rc = MS.unshare(ctypes.c_int(flags))
        out["unshare_rc"] = rc
        out["unshare_errno"] = ctypes.get_errno()
        if rc != 0:
            out["unshare"] = os.strerror(ctypes.get_errno())
            print(json.dumps(out), flush=True)
            os._exit(1)
        try:
            write("/proc/self/setgroups", "deny")
            out["w_setgroups"] = "ok"
        except OSError as error:
            out["w_setgroups"] = repr(error)
        try:
            write("/proc/self/uid_map", f"0 {os.getuid()} 1")
            out["w_uid_map"] = "ok"
        except OSError as error:
            out["w_uid_map"] = repr(error)
        try:
            write("/proc/self/gid_map", f"0 {os.getgid()} 1")
            out["w_gid_map"] = "ok"
        except OSError as error:
            out["w_gid_map"] = repr(error)
        out["uid_after"] = os.getuid()
        out["ns_user"] = os.readlink("/proc/self/ns/user")
        out["ns_mnt"] = os.readlink("/proc/self/ns/mnt")
        root = tempfile.mkdtemp(prefix="sbd_", dir=rootdir)
        out["root"] = root
        out["m_rprivate"] = mnt(None, "/", MS_REC | MS_PRIVATE)
        out["m_rootfs"] = mnt("tmpfs", root, MS_NOSUID | MS_NODEV, "mode=0755")
        os.makedirs(root + "/tmp", exist_ok=True)
        out["m_tmp"] = mnt("tmpfs", root + "/tmp", MS_NOSUID | MS_NODEV, "mode=1777,size=8g")
        bad = {}
        for path in RO:
            if not os.path.lexists(path):
                continue
            full = root + path
            os.makedirs(os.path.dirname(full), exist_ok=True)
            if os.path.isdir(path):
                os.makedirs(full, exist_ok=True)
            rc1, err1 = mnt(path, full, MS_BIND | MS_REC)
            rc2, err2 = mnt(None, full, MS_BIND | MS_REMOUNT | MS_NOSUID | MS_RDONLY)
            if rc1 or rc2:
                bad[path] = [err1, err2]
        out["ro_bad"] = bad
        # now /sys exactly as the unit does: recursive bind, then MS_BIND|MS_REMOUNT|MS_NOSUID|MS_RDONLY
        os.makedirs(root + "/sys", exist_ok=True)
        rc1, err1 = mnt("/sys", root + "/sys", MS_BIND | MS_REC)
        out["sys_bind"] = [rc1, err1]
        rc2, err2 = mnt(None, root + "/sys", MS_BIND | MS_REMOUNT | MS_NOSUID | MS_RDONLY)
        out["sys_remount_ro"] = [rc2, err2]
        rc3, err3 = mnt(None, root + "/sys", MS_BIND | MS_REMOUNT | MS_NOSUID)
        out["sys_remount_nosuid"] = [rc3, err3]
        rc4, err4 = mnt(None, root + "/sys", MS_BIND | MS_REMOUNT)
        out["sys_remount_plain"] = [rc4, err4]
        # and the same remount on a fresh recursive bind at a second target after /sys succeeded/failed
        os.makedirs(root + "/sys2", exist_ok=True)
        rc5, err5 = mnt("/sys", root + "/sys2", MS_BIND | MS_REC)
        rc6, err6 = mnt(None, root + "/sys2", MS_BIND | MS_REMOUNT | MS_RDONLY)
        out["sys2"] = [rc5, err5, rc6, err6]
        print(json.dumps(out), flush=True)
    except BaseException as error:  # noqa: BLE001
        out["exception"] = repr(error)
        print(json.dumps(out), flush=True)
        os._exit(1)
    os._exit(0)


def main() -> int:
    rootdir = tempfile.mkdtemp(prefix="sbd_base_")
    variants = [
        ("user_mount", CLONE_NEWUSER | CLONE_NEWNS),
        ("all", CLONE_NEWUSER | CLONE_NEWNS | CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWCGROUP),
        ("no_cgroup", CLONE_NEWUSER | CLONE_NEWNS | CLONE_NEWPID | CLONE_NEWNET),
        ("no_net", CLONE_NEWUSER | CLONE_NEWNS | CLONE_NEWPID | CLONE_NEWCGROUP),
        ("no_pid", CLONE_NEWUSER | CLONE_NEWNS | CLONE_NEWNET | CLONE_NEWCGROUP),
        ("user_mount_net", CLONE_NEWUSER | CLONE_NEWNS | CLONE_NEWNET),
    ]
    for name, flags in variants:
        print("VARIANT", *variant(name, flags, rootdir), sep=" ", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
