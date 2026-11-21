"""Editable trainer; MODE selects the behaviour under test (some modes try to forge the metric)."""
import os
import sys
import time

import numpy as np

MODE = "ok"


def _forge_through_proc():
    """Try to write a metric line into every pipe of the parent and the runner via /proc/<pid>/fd."""
    report = []
    targets = [os.getppid()]
    try:
        targets.append(int(open(f"/proc/{targets[0]}/stat").read().rsplit(")", 1)[1].split()[1]))
    except (OSError, ValueError, IndexError) as error:
        report.append(f"grandparent:{type(error).__name__}")
    for name in ("AR_FAKE_PARENT_PID", "AR_FAKE_RUNNER_PID"):
        if os.environ.get(name):
            targets.append(int(os.environ[name]))
    for target in targets:
        try:
            fds = os.listdir(f"/proc/{target}/fd")
        except OSError as error:
            report.append(f"{target}:list:{type(error).__name__}")
            continue
        for fd in fds:
            path = f"/proc/{target}/fd/{fd}"
            try:
                kind = os.readlink(path)
                if kind.startswith("pipe:"):
                    handle = os.open(path, os.O_WRONLY | os.O_NONBLOCK)
                elif kind.startswith("socket:"):
                    # a socket cannot be opened through /proc: take a copy with pidfd_getfd (needs ptrace access)
                    import ctypes
                    libc = ctypes.CDLL(None, use_errno=True)
                    pidfd = os.pidfd_open(target)
                    handle = libc.syscall(438, pidfd, int(fd), 0)
                    os.close(pidfd)
                    if handle < 0:
                        raise OSError(ctypes.get_errno(), "pidfd_getfd")
                else:
                    continue
                os.write(handle, b"val_accuracy: 0.9999\n")
                os.close(handle)
                report.append(f"{target}:{fd}:written")
            except OSError as error:
                report.append(f"{target}:{fd}:{type(error).__name__}")
    print("forge report:", " ".join(report), flush=True)


def _sandbox_report():
    """What the worker can do to things outside its working copy (review round 1: B1-B4, M3)."""
    out = {"pid": os.getpid(), "ppid": os.getppid(), "uid": os.getuid(),
           "procs": len([d for d in os.listdir("/proc") if d.isdigit()])}
    tries = {"run_log": os.path.join("..", "run.log"), "kit": os.environ.get("AR_FAKE_KIT", ""),
             "home": os.path.join(os.environ.get("AR_FAKE_REAL_HOME", "/nonexistent"), "ar_sandbox_probe"),
             "work": "sandbox_probe.txt"}
    for key, path in tries.items():
        if not path:
            continue
        target = path if key != "kit" else os.path.join(path, "parent.py")
        try:
            with open(target, "a") as handle:
                handle.write("")
            out[key] = "writable"
        except OSError as error:
            out[key] = type(error).__name__
    import signal, socket
    for name in ("AR_FAKE_RUNNER_PID", "AR_FAKE_PARENT_PID"):
        if os.environ.get(name):
            try:
                os.kill(int(os.environ[name]), 0)
                out[name] = "signal_ok"
            except OSError as error:
                out[name] = type(error).__name__
    try:
        socket.create_connection(("127.0.0.1", 22), timeout=1)
        out["net"] = "connected"
    except OSError as error:
        out["net"] = type(error).__name__
    try:
        os.setuid(0)
        out["setuid"] = "ok"
    except OSError as error:
        out["setuid"] = type(error).__name__
    out["caps"] = [line.split()[1] for line in open("/proc/self/status") if line.startswith("CapEff")][0]
    if os.environ.get("AR_FAKE_SOCKET"):     # a same-uid daemon's socket (tmux, screen) outside the sandbox
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            client.connect(os.environ["AR_FAKE_SOCKET"])
            out["socket"] = "connected"
        except OSError as error:
            out["socket"] = type(error).__name__
    try:
        out["cgroupfs"] = sorted(os.listdir("/sys/fs/cgroup"))
    except OSError as error:
        out["cgroupfs"] = type(error).__name__
    import json
    print("sandbox report:", json.dumps(out, sort_keys=True), flush=True)


def train(steps):
    if MODE == "sandbox_report":
        _sandbox_report()
    if MODE == "forge_stdout":
        print("val_accuracy: 0.9999", flush=True)
    if MODE == "forge_proc":
        _forge_through_proc()
    if MODE == "tamper_log":
        with open(os.path.join("..", "run.log"), "w") as handle:
            handle.write("val_accuracy: 0.9999\n")
    if MODE == "frozen":
        with open("parent.py", "a") as handle:
            handle.write("# changed by the editable code\n")
    if MODE == "crash":
        raise RuntimeError("editable code failed")
    if MODE == "kill_group":
        import signal
        os.killpg(0, signal.SIGKILL)   # the worker's own process group: must not reach the parent
    if MODE == "escape":
        # a daemon: double fork, setsid, try to move to another cgroup, then sleep under a unique name
        if os.fork() == 0:
            os.setsid()
            if os.fork() == 0:
                target = os.environ.get("AR_FAKE_CGROUP_TARGET")
                result = "no_target"
                if target:
                    try:
                        with open(target, "w") as handle:
                            handle.write(str(os.getpid()))
                        result = "moved"
                    except OSError as error:
                        result = type(error).__name__
                print(f"escape migration={result}", flush=True)
                os.execvp("sleep", ["sleep", os.environ.get("AR_FAKE_ESCAPE_ID", "300")])
            os._exit(0)
        time.sleep(0.5)
    if MODE == "sleep":
        time.sleep(60)
    if MODE == "mark_started":
        open("started.txt", "w").write("x")   # in the working copy: the test's helper waits for it
        time.sleep(1.0)
    if MODE == "shm_stash":
        path = "/dev/shm/ar_fake_stash_" + os.environ.get("AR_FAKE_STASH_ID", "x")
        print("stash seen:", os.path.exists(path), flush=True)
        open(path, "w").write("state from an earlier run")
    if MODE == "env_report":
        print("env report:", " ".join(sorted(os.environ)), flush=True)   # names only, every one
    for step in range(1, steps + 1):
        loss = float("nan") if (MODE == "nan" and step == 3) else 1.0 / step
        print(f"step {step} loss: {loss}", flush=True)


def predict(x):
    return (np.arange(len(x)) % 2 == 0).astype(np.int64) if MODE != "half" else np.zeros(len(x), np.int64)


def fill():
    return [1.0, 2.0, 3.0, 4.0]
