"""R1-T1-HOST-TASL condition 1: the unit's real launcher unshare() flags.

Adapted from the Ada G0 capture ``probe_userns.py`` (19 Nov 2026, ops-tasl-20261116 captures):
  * keeps the exact flags the isolation launcher uses
    (CLONE_NEWUSER|CLONE_NEWNS|CLONE_NEWPID|CLONE_NEWNET|CLONE_NEWCGROUP),
  * maps the caller's uid/gid to 0 in the new user namespace as ``ar_isolated`` does,
  * makes a real tmpfs mount (and a real write) inside the new mount namespace,
  * additionally forks a child after CLONE_NEWPID so the probe proves the child is PID 1 of the new
    PID namespace (the unit's ``worker_sandbox_available`` requires ``pid == 1``),
  * records every namespace inode and compares it with the caller's.

Run with the run interpreter (``trackp-gpu`` venv) and with ``/usr/bin/python3``; both must pass.
Read-only apart from private /tmp dirs, which it removes.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import sys
import time

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


def ns_links() -> dict:
    out = {}
    for kind in ("user", "mnt", "pid", "net", "cgroup", "ipc", "uts", "time"):
        try:
            out[kind] = os.readlink(f"/proc/self/ns/{kind}")
        except OSError as error:
            out[kind] = f"<{type(error).__name__}>"
    return out


def probe(name: str, flags: int, map_ids: bool) -> dict:
    """Parent: fork one child and collect newline-framed JSON messages from the child's pipe."""
    parent_uid, parent_gid, parent_ns = os.getuid(), os.getgid(), ns_links()
    r, w = os.pipe()
    pid = os.fork()
    if pid:
        os.close(w)
        chunks = []
        while True:
            data = os.read(r, 65536)
            if not data:
                break
            chunks.append(data)
        os.close(r)
        _, status = os.waitpid(pid, 0)
        exitcode = os.waitstatus_to_exitcode(status)
        messages = []
        for line in b"".join(chunks).decode("utf-8", "replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                messages.append(json.loads(line))
            except ValueError:
                messages.append({"unparsed": line[:2000]})
        grandchild = next((m for m in messages if "grandchild" in m), None)
        child = next((m for m in reversed(messages) if "unshare_rc" in m or "exception" in m), {})
        if grandchild is not None:
            child["pid_namespace_child"] = grandchild["grandchild"]
        return {"probe": name, "caller_uid": parent_uid, "caller_gid": parent_gid,
                "flags": hex(flags), "child_exitcode": exitcode,
                "caller_ns": parent_ns, "child": child}

    # ---- child ------------------------------------------------------------------------------------
    os.close(r)

    def emit(obj) -> None:
        os.write(w, (json.dumps(obj, sort_keys=True) + "\n").encode())

    out: dict = {"probe": name, "caller_uid": parent_uid, "flags": hex(flags)}
    try:
        MS.prctl(ctypes.c_int(PR_SET_DUMPABLE), ctypes.c_ulong(1), ctypes.c_ulong(0),
                 ctypes.c_ulong(0), ctypes.c_ulong(0))
        rc = MS.unshare(ctypes.c_int(flags))
        out["unshare_rc"] = rc
        out["unshare_errno"] = ctypes.get_errno()
        if rc != 0:
            out["unshare_error"] = os.strerror(ctypes.get_errno())
            emit(out)
            os.close(w)
            os._exit(1)
        if map_ids:
            for path, text in (("/proc/self/setgroups", "deny"),
                               ("/proc/self/uid_map", f"0 {parent_uid} 1"),
                               ("/proc/self/gid_map", f"0 {parent_gid} 1")):
                fd = os.open(path, os.O_WRONLY)
                os.write(fd, text.encode())
                os.close(fd)
            out["mapped_uid_in_new_userns"] = os.getuid()
            out["mapped_gid_in_new_userns"] = os.getgid()
        out["ns_after_unshare"] = ns_links()
        # a real mount in the new mount namespace (as the sandbox does for its private /tmp)
        root = f"/tmp/g0_userns_{os.getpid()}"
        os.makedirs(root, exist_ok=True)
        rc = MS.mount(b"tmpfs", root.encode(), b"tmpfs", ctypes.c_ulong(MS_NOSUID | MS_NODEV),
                      b"mode=0755,size=16m")
        out["tmpfs_mount_rc"] = rc
        out["tmpfs_mount_result"] = "ok" if rc == 0 else os.strerror(ctypes.get_errno())
        if rc == 0:
            out["tmpfs_mounted"] = os.path.ismount(root)
            out["tmpfs_mountinfo"] = [line.strip() for line in open("/proc/self/mountinfo")
                                      if f" {root} " in line][:2]
            try:
                with open(os.path.join(root, "probe.txt"), "w") as handle:
                    handle.write("userns mount ok")
                with open(os.path.join(root, "probe.txt")) as handle:
                    out["tmpfs_writable"] = handle.read()
            except OSError as error:
                out["tmpfs_writable_error"] = repr(error)
            ctypes.CDLL(None).umount(root.encode())
        try:
            os.rmdir(root)          # no leftover /tmp/g0_userns_* even when the mount was refused
        except OSError:
            pass
        # after CLONE_NEWPID the first fork is PID 1 of the new PID namespace
        kid = os.fork()
        if kid == 0:
            info = {"pid": os.getpid(), "ppid": os.getppid(), "uid": os.getuid(),
                    "ns": ns_links(), "new_pid_namespace": os.getpid() == 1}
            emit({"grandchild": info})
            os._exit(0)
        _, status = os.waitpid(kid, 0)
        out["pid_namespace_child_exitcode"] = os.waitstatus_to_exitcode(status)
        emit(out)
        os.close(w)
    except BaseException as error:  # noqa: BLE001
        out["exception"] = repr(error)
        try:
            emit(out)
            os.close(w)
        except OSError:
            pass
        os._exit(1)
    os._exit(0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    probes = {
        "userns_only": probe("userns_only", CLONE_NEWUSER, False),
        "user_mount_pid_net": probe("user_mount_pid_net",
                                    CLONE_NEWUSER | CLONE_NEWNS | CLONE_NEWPID | CLONE_NEWNET, True),
        "launcher_all_five_one_call": probe("launcher_all_five_one_call", ALL, True),
    }
    ok = all(p["child_exitcode"] == 0 for p in probes.values())
    result = {"utc": stamp, "interpreter": sys.executable, "python": sys.version.split()[0],
              "euid": os.geteuid(), "probes": probes, "condition_1_pass": ok}
    if args.out:
        with open(args.out, "w") as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
            handle.write("\n")
    print("RESULT " + json.dumps(result, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
