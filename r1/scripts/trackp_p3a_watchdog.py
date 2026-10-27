"""Independent fail-closed P.3a worker-group watchdog; AI-assisted."""
import os
import json
from pathlib import Path
import signal
import sys
import time


def process_state(pid):
    try:
        # comm may contain spaces or parentheses; fields after its final ')' start with state.
        tail=Path(f"/proc/{pid}/stat").read_text().rsplit(")",1)[1].split()
        return tail[0],tail[19]  # state and field 22 (process start time)
    except (OSError, IndexError):
        return None


def watch(parent, identity, group, log, ready, lease_path, offset, remaining):
    """Kill the group if its supervisor dies or the exclusive GPU lease exhausts budget."""
    def kill(reason):
        try:
            os.killpg(group,signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            with Path(log).open("a") as fh:
                fh.write(json.dumps({"event": "STOP", "reason": reason, "monotonic_s": time.monotonic()}) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
        except OSError:
            pass  # logging must never prevent killing the worker group

    state=process_state(parent)
    if state is None or state[0]=="Z" or state[1]!=identity:
        kill("supervisor lost before watchdog readiness")
        return 2
    os.write(ready,b"1")
    os.close(ready)
    start=end=None
    waiting_since=time.monotonic()
    try:
        with Path(lease_path).open("r") as leases:
            leases.seek(offset)
            while True:
                for line in leases:
                    event=json.loads(line)
                    if event.get("pid") != group:
                        continue
                    if event.get("event") in ("acquired","start"):
                        observed=float(event["monotonic_s"])
                        if start is not None and start!=observed:
                            raise RuntimeError("inconsistent lease start")
                        start=observed
                    elif event.get("event")=="end":
                        if start is None or end is not None:
                            raise RuntimeError("invalid lease end")
                        end=float(event["monotonic_s"])
                if start is None and time.monotonic()-waiting_since >= min(remaining,600.0):
                    kill("GPU lease start not observable before fail-closed deadline")
                    return 4
                if start is not None:
                    duration=(end if end is not None else time.monotonic())-start
                    if duration < 0 or not __import__("math").isfinite(duration):
                        raise RuntimeError("invalid lease duration")
                    if duration >= remaining:
                        kill("GPU lease budget exhausted")
                        return 3
                try:
                    os.killpg(group,0)
                except ProcessLookupError:
                    return 0
                state=process_state(parent)
                if state is None or state[0]=="Z" or state[1]!=identity:
                    kill("supervisor lost")
                    return 2
                time.sleep(.2)
    except Exception:
        kill("watchdog failed")
        return 4


if __name__=="__main__":
    raise SystemExit(watch(int(sys.argv[1]),sys.argv[2],int(sys.argv[3]),sys.argv[4],
                           int(sys.argv[5]),sys.argv[6],int(sys.argv[7]),float(sys.argv[8])))
