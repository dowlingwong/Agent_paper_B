"""R1-T1-HOST-H200 condition C3: unprivileged user namespaces with mount/PID/network (and cgroup) namespaces,
a real pivot_root, and a probe of the sandbox's bind-remount flags.

The shapes mirror the accepted worker sandbox (``ar_isolated.py``): one ``unshare(CLONE_NEWUSER|CLONE_NEWNS|
CLONE_NEWPID|CLONE_NEWNET|CLONE_NEWCGROUP)``, uid/gid mapped to 0, ``/`` made private, a new tmpfs root,
``pivot_root``, a fresh ``/proc`` -- plus a granular per-flag diagnostic and the read-only ``/sys`` bind remount
with both the old fixed flag set (review defect A) and the source mount's locked flags.  No harness run, no waiver.
"""
from __future__ import annotations

import argparse
import ctypes
import errno
import json
import os
import sys
import time
import traceback

import lib_iso

CLONE_NEWNS = 0x00020000
CLONE_NEWCGROUP = 0x02000000
CLONE_NEWPID = 0x20000000
CLONE_NEWNET = 0x40000000
CLONE_NEWUSER = 0x10000000
ALL_NS = CLONE_NEWUSER | CLONE_NEWNS | CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWCGROUP

MS_RDONLY = 1
MS_NOSUID = 2
MS_NODEV = 4
MS_NOEXEC = 8
MS_REMOUNT = 32
MS_BIND = 4096
MS_REC = 16384
MS_PRIVATE = 1 << 18
MNT_DETACH = 2

_libc = ctypes.CDLL(None, use_errno=True)
_libc.unshare.argtypes = [ctypes.c_int]
_libc.unshare.restype = ctypes.c_int
_libc.mount.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_char_p]
_libc.mount.restype = ctypes.c_int
_libc.umount2.argtypes = [ctypes.c_char_p, ctypes.c_int]
_libc.umount2.restype = ctypes.c_int
_libc.pivot_root.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
_libc.pivot_root.restype = ctypes.c_int


def err() -> dict:
    code = ctypes.get_errno()
    return {"errno": code, "name": errno.errorcode.get(code, str(code)), "strerror": os.strerror(code)}


def attempt(fn) -> dict:
    try:
        fn()
        return {"ok": True}
    except OSError as error:
        return {"ok": False, "errno": error.errno,
                "name": errno.errorcode.get(error.errno or 0, str(error.errno)),
                "strerror": error.strerror or str(error)}
    except Exception as error:  # noqa: BLE001
        return {"ok": False, "error": f"{type(error).__name__}: {error}"}


def c_unshare(flags: int) -> None:
    if _libc.unshare(flags) != 0:
        raise OSError(ctypes.get_errno(), os.strerror(ctypes.get_errno()))


def c_mount(source, target, fstype, flags, data=None) -> None:
    enc = lambda value: value.encode() if isinstance(value, str) else value  # noqa: E731
    if _libc.mount(enc(source), enc(target), enc(fstype), flags, enc(data)) != 0:
        raise OSError(ctypes.get_errno(), os.strerror(ctypes.get_errno()))


def c_pivot_root(new_root: str, old_root: str) -> None:
    if _libc.pivot_root(new_root.encode(), old_root.encode()) != 0:
        raise OSError(ctypes.get_errno(), os.strerror(ctypes.get_errno()))


def c_umount2(target: str, flags: int) -> None:
    if _libc.umount2(target.encode(), flags) != 0:
        raise OSError(ctypes.get_errno(), os.strerror(ctypes.get_errno()))


def read_fd_all(fd: int) -> bytes:
    chunks = []
    while True:
        chunk = os.read(fd, 65536)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def run_child(fn) -> dict:
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        try:
            result = fn()
        except BaseException as error:  # noqa: BLE001
            result = {"child_error": f"{type(error).__name__}: {error}", "traceback": traceback.format_exc()}
        try:
            os.write(write_fd, json.dumps(result, default=str).encode())
        finally:
            os._exit(0)
    os.close(write_fd)
    raw = read_fd_all(read_fd)
    os.close(read_fd)
    _, status = os.waitpid(pid, 0)
    try:
        return json.loads(raw.decode() or "{}")
    except json.JSONDecodeError:
        return {"child_error": "unparseable child result", "raw": raw.decode(errors="replace")[:2000],
                "wait_status": status}


def write_proc(field: str, text: str) -> None:
    with open(f"/proc/self/{field}", "w", encoding="utf-8") as handle:
        handle.write(text)


def map_self(steps: dict, parent_uid: int, parent_gid: int) -> bool:
    """Map uid/gid 0 inside the new namespace to the *parent* euid/egid (captured before unshare)."""
    steps["map_parent_uid"] = parent_uid
    steps["map_setgroups"] = attempt(lambda: write_proc("setgroups", "deny"))
    steps["map_uid_map"] = attempt(lambda: write_proc("uid_map", f"0 {parent_uid} 1"))
    steps["map_gid_map"] = attempt(lambda: write_proc("gid_map", f"0 {parent_gid} 1"))
    steps["euid_after_map"] = os.geteuid()
    return bool(steps["map_uid_map"]["ok"] and steps["map_gid_map"]["ok"])


def mount_flags_of(path: str) -> int:
    best, best_len = 0, -1
    for line in lib_iso.read_text("/proc/self/mountinfo").splitlines():
        fields = line.split(" ")
        if len(fields) < 6:
            continue
        mount_point = fields[4].replace("\\040", " ")
        if path == mount_point or path.startswith(mount_point.rstrip("/") + "/"):
            if len(mount_point) > best_len:
                best_len = len(mount_point)
                best = 0
                options = fields[5].split(",")
                for name, flag in (("nosuid", MS_NOSUID), ("nodev", MS_NODEV), ("noexec", MS_NOEXEC)):
                    if name in options:
                        best |= flag
    return max(best, 0)


def child_combined(base: str) -> dict:
    """The unit's shape: one unshare of all five namespaces, map, / private, PID 1 pivot_root."""
    parent_uid, parent_gid = os.geteuid(), os.getegid()
    steps: dict = {"euid_before": parent_uid}
    steps["unshare_combined"] = attempt(lambda: c_unshare(ALL_NS))
    if not steps["unshare_combined"]["ok"]:
        return steps
    if not map_self(steps, parent_uid, parent_gid):
        return steps
    steps["make_root_private"] = attempt(lambda: c_mount("none", "/", None, MS_REC | MS_PRIVATE, None))

    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        inner: dict = {"pid_inside": os.getpid()}
        try:
            new_root = os.path.join(base, f"root_{os.getpid()}")
            os.makedirs(new_root, exist_ok=True)
            inner["mount_tmpfs_root"] = attempt(
                lambda: c_mount("tmpfs", new_root, "tmpfs", MS_NOSUID | MS_NODEV, "mode=0755,size=32m"))
            # the tmpfs covers the directory, so the mount points must be created after the mount
            inner["mkdir_oldroot"] = attempt(lambda: os.makedirs(os.path.join(new_root, "oldroot"), exist_ok=True))
            inner["mkdir_proc"] = attempt(lambda: os.makedirs(os.path.join(new_root, "proc"), exist_ok=True))
            inner["mkdir_dev"] = attempt(lambda: os.makedirs(os.path.join(new_root, "dev"), exist_ok=True))
            # the sandbox binds the host /proc here first: the kernel lets a user namespace mount a fresh proc
            # only where a fully visible proc mount already exists (ar_isolated._sandbox_preexec)
            inner["bind_host_proc"] = attempt(
                lambda: c_mount("/proc", os.path.join(new_root, "proc"), None, MS_BIND | MS_REC, None))
            inner["pivot_root"] = attempt(lambda: c_pivot_root(new_root, os.path.join(new_root, "oldroot")))
            if inner["pivot_root"]["ok"]:
                os.chdir("/")
                inner["detach_old_root"] = attempt(lambda: c_umount2("/oldroot", MNT_DETACH))
                inner["write_in_new_root"] = attempt(lambda: open("/ar_probe_marker", "w").write("ok\n"))
                inner["mount_proc"] = attempt(lambda: c_mount("proc", "/proc", "proc", 0, None))
                inner["read_proc_self_status"] = attempt(lambda: open("/proc/self/status").read(300))
                inner["mount_dev_tmpfs"] = attempt(lambda: c_mount("tmpfs", "/dev", "tmpfs", 0, "size=8m"))
            inner["ok"] = bool(inner.get("pivot_root", {}).get("ok")) and bool(
                inner.get("write_in_new_root", {}).get("ok")) and bool(inner.get("mount_proc", {}).get("ok"))
        except BaseException as error:  # noqa: BLE001
            inner["child_error"] = f"{type(error).__name__}: {error}"
            inner["traceback"] = traceback.format_exc()
        try:
            os.write(write_fd, json.dumps(inner, default=str).encode())
        finally:
            os._exit(0)
    os.close(write_fd)
    raw = read_fd_all(read_fd)
    os.close(read_fd)
    os.waitpid(pid, 0)
    steps["pid1_child"] = json.loads(raw.decode() or "{}")
    steps["ok"] = bool(steps["pid1_child"].get("ok"))
    return steps


def child_incremental() -> dict:
    """Per-flag diagnostic: which namespace kind the host refuses, and with what error."""
    parent_uid, parent_gid = os.geteuid(), os.getegid()
    steps: dict = {"euid_before": parent_uid}
    steps["newuser"] = attempt(lambda: c_unshare(CLONE_NEWUSER))
    if not steps["newuser"]["ok"]:
        return steps
    if not map_self(steps, parent_uid, parent_gid):
        return steps
    for name, flag in (("newmount", CLONE_NEWNS), ("newnet", CLONE_NEWNET),
                       ("newcgroup", CLONE_NEWCGROUP), ("newpid", CLONE_NEWPID)):
        steps[name] = attempt(lambda flag=flag: c_unshare(flag))
    steps["ok"] = all(item.get("ok") for key, item in steps.items()
                      if key in ("newmount", "newnet", "newcgroup", "newpid"))
    return steps


def child_remount(base: str) -> dict:
    parent_uid, parent_gid = os.geteuid(), os.getegid()
    out: dict = {}
    out["unshare_user_mount"] = attempt(lambda: c_unshare(CLONE_NEWUSER | CLONE_NEWNS))
    if not out["unshare_user_mount"]["ok"]:
        return out
    if not map_self(out, parent_uid, parent_gid):
        return out
    out["make_root_private"] = attempt(lambda: c_mount("none", "/", None, MS_REC | MS_PRIVATE, None))
    sys_flags = mount_flags_of("/sys")
    out["sys_source_flags"] = {"mask": sys_flags, "nosuid": bool(sys_flags & MS_NOSUID),
                               "nodev": bool(sys_flags & MS_NODEV), "noexec": bool(sys_flags & MS_NOEXEC)}
    bind = os.path.join(base, f"sysbind_{os.getpid()}")
    os.makedirs(bind, exist_ok=True)
    out["bind_sys"] = attempt(lambda: c_mount("/sys", bind, None, MS_BIND | MS_REC, None))
    variants = {
        "old_unit_flags_RDONLY_NOSUID": MS_BIND | MS_REMOUNT | MS_RDONLY | MS_NOSUID,
        "RDONLY_NOSUID_NODEV": MS_BIND | MS_REMOUNT | MS_RDONLY | MS_NOSUID | MS_NODEV,
        "RDONLY_NOSUID_NODEV_NOEXEC": MS_BIND | MS_REMOUNT | MS_RDONLY | MS_NOSUID | MS_NODEV | MS_NOEXEC,
        "source_locked_flags_RDONLY": MS_BIND | MS_REMOUNT | MS_RDONLY | sys_flags | MS_NOSUID,
    }
    out["remounts"] = {name: attempt(lambda flags=flags: c_mount(None, bind, None, flags, None))
                       for name, flags in variants.items()}
    out["ok"] = True
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    base = os.path.join(args.base, "userns_probe")
    os.makedirs(base, exist_ok=True)
    result: dict = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "euid": os.geteuid(), "uid": os.getuid(),
        "sysctls": {name: lib_iso.read_sysctl(name) for name in (
            "user.max_user_namespaces", "kernel.unprivileged_userns_clone",
            "kernel.apparmor_restrict_unprivileged_userns", "kernel.yama.ptrace_scope")},
    }
    for key, fn in (("combined", lambda: child_combined(base)),
                    ("incremental", lambda: child_incremental()),
                    ("remount_flags", lambda: child_remount(base))):
        try:
            result[key] = run_child(fn)
        except Exception:  # noqa: BLE001
            result[key] = {"error": traceback.format_exc()}
    combined = result["combined"]
    result["condition_C3_pass"] = bool(combined.get("ok"))
    result["userns_steps"] = {k: v for k, v in combined.items() if k != "pid1_child"}
    lib_iso.write_json(args.out, result)
    print(json.dumps({"C3_userns_pass": result["condition_C3_pass"],
                      "combined_unshare": combined.get("unshare_combined"),
                      "stopped_after": combined.get("stopped_after"),
                      "pivot_root": (combined.get("pid1_child") or {}).get("pivot_root"),
                      "remount_variants": (result.get("remount_flags") or {}).get("remounts")}, default=str))
    return 0 if result["condition_C3_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
