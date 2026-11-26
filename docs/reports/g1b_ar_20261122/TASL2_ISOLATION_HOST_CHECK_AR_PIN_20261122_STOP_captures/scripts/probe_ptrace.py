"""R1-TRACKG-AR-U2-TASL2 condition 2: Yama ``ptrace_scope`` >= 1.

Reads the sysctl and the LSM list, then runs two tiny functional probes with the caller's uid:
  * an unrelated same-uid *sibling* process must NOT be able to PTRACE_ATTACH the target (Yama scope 1),
  * the target's own *parent* still can attach and detach (so the denial above is Yama, not a broken ptrace).
Read-only.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import signal
import sys
import time
from pathlib import Path

PTRACE_ATTACH = 16
PTRACE_DETACH = 17

LIBC = ctypes.CDLL(None, use_errno=True)


def ptrace_attach(pid: int) -> tuple[bool, str]:
    rc = LIBC.ptrace(ctypes.c_int(PTRACE_ATTACH), ctypes.c_int(pid), ctypes.c_void_p(0),
                     ctypes.c_void_p(0))
    err = ctypes.get_errno()
    return rc == 0, (os.strerror(err) if rc != 0 else "ok")


def ptrace_detach(pid: int) -> tuple[bool, str]:
    rc = LIBC.ptrace(ctypes.c_int(PTRACE_DETACH), ctypes.c_int(pid), ctypes.c_void_p(0),
                     ctypes.c_void_p(0))
    err = ctypes.get_errno()
    return rc == 0, (os.strerror(err) if rc != 0 else "ok")


def spawn_sleep(spawned: list[int]) -> int:
    pid = os.fork()
    if pid == 0:
        os.kill(os.getpid(), signal.SIGSTOP)
        time.sleep(60)
        os._exit(0)
    os.waitpid(pid, os.WUNTRACED)   # wait for the SIGSTOP stop
    spawned.append(pid)
    return pid


def reap(pid: int) -> None:
    """SIGKILL and reap a helper; a PTRACE_DETACHed tracee may otherwise stay stopped forever."""
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        os.waitpid(pid, 0)
    except ChildProcessError:
        pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    scope_text = Path("/proc/sys/kernel/yama/ptrace_scope").read_text().strip() \
        if Path("/proc/sys/kernel/yama/ptrace_scope").exists() else "<absent>"
    lsm = Path("/sys/kernel/security/lsm").read_text().strip() \
        if Path("/sys/kernel/security/lsm").exists() else "<absent>"
    scope = int(scope_text) if scope_text.isdigit() else None

    result: dict = {
        "utc": stamp, "euid": os.geteuid(), "ptrace_scope": scope,
        "ptrace_scope_raw": scope_text, "lsm": lsm,
        "yama_in_lsm": "yama" in lsm,
        "checks": {},
    }
    spawned: list[int] = []
    try:
        # target: a stopped child of THIS probe process.  The probe is its parent, so under scope>=1 the
        # parent attach should succeed and detach should restore it.
        target = spawn_sleep(spawned)
        ok, why = ptrace_attach(target)
        result["checks"]["parent_attach_child"] = {"ok": ok, "why": why}
        if ok:
            os.waitpid(target, os.WUNTRACED)
            result["checks"]["parent_detach_child"] = dict(zip(("ok", "why"), ptrace_detach(target)))
        else:
            result["checks"]["parent_detach_child"] = {"ok": None, "why": "not attached"}

        # unrelated sibling: fork two siblings; one tries to attach the other.  Neither is the other's ancestor.
        target2 = spawn_sleep(spawned)
        r, w = os.pipe()
        attacker = os.fork()
        if attacker == 0:
            os.close(r)
            ok2, why2 = ptrace_attach(target2)
            err = ctypes.get_errno()
            os.write(w, (json.dumps({"ok": ok2, "why": why2, "errno": err}) + "\n").encode())
            if ok2:
                ptrace_detach(target2)
            os._exit(0)
        os.close(w)
        raw = os.read(r, 65536).decode()
        os.close(r)
        os.waitpid(attacker, 0)
        result["checks"]["unrelated_sibling_attach"] = json.loads(raw.strip() or "{}")
    finally:
        for pid in spawned:
            reap(pid)

    result["condition_2_pass"] = bool(scope is not None and scope >= 1 and result["yama_in_lsm"])
    result["children_reaped"] = True
    if args.out:
        with open(args.out, "w") as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
            handle.write("\n")
    print("RESULT " + json.dumps(result, sort_keys=True))
    return 0 if result["condition_2_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
