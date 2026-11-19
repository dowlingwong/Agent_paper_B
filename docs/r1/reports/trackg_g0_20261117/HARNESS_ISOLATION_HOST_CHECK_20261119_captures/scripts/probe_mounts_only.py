"""G0 diagnostic 3: the mount sequence only (no unshare); run it inside a namespace prepared by unshare(1) to
compare with the same calls made by a process that called unshare() itself.
"""
import ctypes
import json
import os
import sys
import tempfile

MS_BIND = 4096
MS_REMOUNT = 32
MS_REC = 0x4000
MS_RDONLY = 1
MS_NOSUID = 2
MS_NODEV = 4
MS_PRIVATE = 1 << 18
RO = ["/usr", "/bin", "/sbin", "/lib", "/lib32", "/lib64", "/libx32", "/etc"]
MS = ctypes.CDLL(None, use_errno=True)


def mnt(src, tgt, flags, data=None, fstype=None):
    rc = MS.mount(src.encode() if src else None, tgt.encode() if tgt else None,
                  fstype.encode() if fstype else None, ctypes.c_ulong(flags), data.encode() if data else None)
    return rc, ("ok" if rc == 0 else os.strerror(ctypes.get_errno()))


def main():
    out = {}
    out["uid"] = os.getuid()
    out["ns_user"] = os.readlink("/proc/self/ns/user")
    out["ns_mnt"] = os.readlink("/proc/self/ns/mnt")
    out["m_rprivate"] = mnt(None, "/", MS_REC | MS_PRIVATE)
    root = tempfile.mkdtemp(prefix="sbd3_")
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
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
