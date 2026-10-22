"""Paper A coordination check for Paper B GPU launches on Ada (PLAN §10, R1-COMPUTE, 19 Oct 2026).

Decides, conservatively, whether a Paper A live campaign is waiting for a GPU
card, and prints one JSON object as its last stdout line, the contract of
``r1/scripts/c3_label_sweep.py`` (``paper_a_check.command``):

* ``"paper_a_live_waiting_for_card": false`` only when the evidence shows that
  Paper A either has its card and is computing (``verdict: clear_running``) or
  has finished / stopped (``verdict: clear_finished``);
* ``true`` when the evidence shows it waiting (``verdict: waiting``);
* the key is **omitted** (``verdict: unknown``) whenever anything is missing,
  unreadable, unconfigured or contradictory.  The runner refuses on ``true``
  and on a missing key alike.

Read-only: it reads files, runs ``git symbolic-ref``, ``tmux has-session``,
``nvidia-smi --query-compute-apps`` and ``ps -o args=``; it never signals,
starts or stops anything.  Standard library only.

Signals (all configurable in a JSON file, ``--config``; see
``r1/scripts/configs/paper_a_status_ada.json``):

``expected_host``          short host name the check must run on (e.g. ``ucrtasl``);
``paper_a_checkout``       Paper A repository checkout (absolute path);
``expected_branch``        its checked-out branch (``paper-a-v4-ada``);
``run_dir``                the live run directory (absolute, or relative to the checkout);
``state_file``/``state_key``  a JSON file in the run directory and a dotted key whose
                           value is matched against ``running_values``,
                           ``finished_values`` (finished *or* stopped) and ``waiting_values``;
``state_max_age_seconds``  optional: a running state older than this is not trusted;
``finished_markers``       files in the run directory whose existence means finished/stopped;
``tmux_session``           Paper A's tmux session name (``tmux has-session``; ``tmux_args`` such
                           as ``["-L", "socket"]`` if Paper A uses its own tmux socket);
``process_patterns``       substrings identifying Paper A processes in the command lines
                           of GPU compute processes (``nvidia-smi`` + ``ps``);
``allow_running_without_state``  default false: whether a live session with a Paper A GPU
                           process clears without a ``running`` state value.

Decision (every live signal must be configured and readable for any clear verdict):

1. wrong host, missing checkout/run directory, wrong branch, unreadable state,
   or an unconfigured live signal -> unknown;
2. state in ``waiting_values`` -> waiting;
3. finished evidence (state in ``finished_values`` or a marker) together with a
   running state, a live tmux session or a Paper A GPU process -> unknown
   (contradictory); finished evidence alone -> clear_finished;
4. state in ``running_values`` (fresh, if a maximum age is set) with a live
   session and >= 1 Paper A GPU process -> clear_running; a running state
   without both -> unknown;
5. no state evidence: live session without a Paper A GPU process -> waiting;
   live session with one -> clear_running only if
   ``allow_running_without_state``, else unknown; no session and no process
   -> unknown (stopped, or not started yet: cannot tell).

ENGINEERING_ONLY. AI-assisted (Claude).
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

KEY = "paper_a_live_waiting_for_card"
CONFIG_KEYS = {
    "expected_host", "paper_a_checkout", "expected_branch", "run_dir", "state_file", "state_key",
    "running_values", "finished_values", "waiting_values", "state_max_age_seconds", "finished_markers",
    "tmux_session", "tmux_binary", "tmux_args", "nvidia_smi_binary", "ps_binary", "process_patterns",
    "allow_running_without_state", "timeout_seconds",
}
DOC_KEYS = {"comment", "verify_before_first_use"}
DEFAULTS = {"running_values": [], "finished_values": [], "waiting_values": [], "finished_markers": [],
            "process_patterns": [], "tmux_binary": "tmux", "tmux_args": [], "nvidia_smi_binary": "nvidia-smi", "ps_binary": "ps",
            "allow_running_without_state": False, "timeout_seconds": 30}


class Unknown(Exception):
    """The state cannot be decided; the key is omitted."""


def _run(argv, timeout):
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)


def load_config(path: str | None, overrides: dict) -> dict:
    cfg = dict(DEFAULTS)
    if path:
        user = json.loads(Path(path).read_text())
        unknown = set(user) - CONFIG_KEYS - DOC_KEYS
        if unknown:
            raise Unknown(f"unknown config keys {sorted(unknown)}")
        cfg.update({k: v for k, v in user.items() if k in CONFIG_KEYS})
    cfg.update({k: v for k, v in overrides.items() if v is not None})
    return cfg


def _dotted(obj, key: str):
    for part in key.split("."):
        if not isinstance(obj, dict) or part not in obj:
            raise Unknown(f"state key {key!r} absent")
        obj = obj[part]
    return obj


def tmux_alive(cfg, ev) -> bool:
    name = cfg.get("tmux_session")
    if not name:
        raise Unknown("tmux_session not configured")
    try:
        done = _run([cfg["tmux_binary"], *cfg.get("tmux_args", []), "has-session", "-t", name], cfg["timeout_seconds"])
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Unknown(f"tmux could not run: {exc!r}") from exc
    ev["tmux"] = {"session": name, "returncode": done.returncode, "stderr": done.stderr.strip()[-200:]}
    if done.returncode == 0:
        return True
    # tmux exits 1 both for "no such session" and for "no server running"; both mean no session.
    if done.returncode == 1 and ("can't find session" in done.stderr or "no server running" in done.stderr
                                 or "session not found" in done.stderr or not done.stderr.strip()):
        return False
    raise Unknown(f"tmux has-session gave an unexpected result (rc={done.returncode})")


def gpu_processes(cfg, ev) -> list[dict]:
    patterns = [p for p in cfg.get("process_patterns") or [] if p]
    if not patterns:
        raise Unknown("process_patterns not configured")
    try:
        done = _run([cfg["nvidia_smi_binary"], "--query-compute-apps=pid,gpu_uuid,used_memory",
                     "--format=csv,noheader,nounits"], cfg["timeout_seconds"])
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Unknown(f"nvidia-smi could not run: {exc!r}") from exc
    if done.returncode != 0:
        raise Unknown(f"nvidia-smi failed (rc={done.returncode})")
    found, all_apps = [], []
    for line in done.stdout.splitlines():
        if not line.strip() or "No running processes" in line:
            continue
        parts = [x.strip() for x in line.split(",")]
        if not parts[0].isdigit():
            raise Unknown(f"unparseable nvidia-smi line {line!r}")
        pid = parts[0]
        try:
            ps = _run([cfg["ps_binary"], "-o", "args=", "-p", pid], cfg["timeout_seconds"])
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise Unknown(f"ps could not run: {exc!r}") from exc
        args = ps.stdout.strip()
        if ps.returncode != 0 or not args:
            # process vanished or is invisible (other user): its identity is unknown
            args = None
        app = {"pid": int(pid), "gpu_uuid": parts[1] if len(parts) > 1 else None, "args": args}
        all_apps.append(app)
        if args and any(p in args for p in patterns):
            found.append(app)
    ev["gpu"] = {"patterns": patterns, "compute_apps": len(all_apps),
                 "unidentified_apps": sum(a["args"] is None for a in all_apps), "paper_a_processes": found}
    return found


def decide(cfg: dict, host: str) -> tuple[str, list[str], dict]:
    """(verdict, reasons, evidence); verdict in clear_running, clear_finished, waiting, unknown."""
    ev, reasons = {}, []
    try:
        if cfg.get("expected_host") and host != cfg["expected_host"]:
            raise Unknown(f"host {host!r} is not the expected host {cfg['expected_host']!r}")
        checkout = cfg.get("paper_a_checkout")
        if not checkout or not Path(checkout).is_dir():
            raise Unknown(f"Paper A checkout not configured or missing: {checkout!r}")
        if cfg.get("expected_branch"):
            try:
                done = _run(["git", "-C", checkout, "symbolic-ref", "--short", "HEAD"], cfg["timeout_seconds"])
            except (OSError, subprocess.TimeoutExpired) as exc:
                raise Unknown(f"git could not run: {exc!r}") from exc
            branch = done.stdout.strip()
            ev["branch"] = branch
            if done.returncode != 0 or branch != cfg["expected_branch"]:
                raise Unknown(f"Paper A checkout is on {branch!r}, expected {cfg['expected_branch']!r}")
        run_dir = cfg.get("run_dir")
        if not run_dir:
            raise Unknown("run_dir not configured")
        run = Path(run_dir) if Path(run_dir).is_absolute() else Path(checkout) / run_dir
        ev["run_dir"] = str(run)
        if not run.is_dir():
            raise Unknown(f"run directory missing: {run}")
        # --- file evidence
        state = None
        if cfg.get("state_file") or cfg.get("state_key"):
            if not (cfg.get("state_file") and cfg.get("state_key")):
                raise Unknown("state_file and state_key must be configured together")
            path = run / cfg["state_file"]
            try:
                doc = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError) as exc:
                raise Unknown(f"state file unreadable: {path} ({exc!r})") from exc
            value = _dotted(doc, cfg["state_key"])
            age = time.time() - path.stat().st_mtime
            ev["state"] = {"file": str(path), "key": cfg["state_key"], "value": value, "age_seconds": round(age, 1)}
            sets = {name: value in (cfg.get(f"{name}_values") or []) for name in ("running", "finished", "waiting")}
            if sum(sets.values()) > 1:
                raise Unknown(f"state value {value!r} is listed in more than one value set")
            state = next((n for n, hit in sets.items() if hit), "other")
            ev["state"]["class"] = state
            if state == "running" and cfg.get("state_max_age_seconds") is not None \
                    and age > float(cfg["state_max_age_seconds"]):
                raise Unknown(f"running state is {age:.0f} s old (> {cfg['state_max_age_seconds']} s)")
        markers = [m for m in cfg.get("finished_markers") or [] if (run / m).exists()]
        ev["finished_markers_present"] = markers
        if state is None and not cfg.get("finished_markers"):
            raise Unknown("no file evidence configured (state_file/state_key or finished_markers)")
        # --- live evidence (both signals are required for any verdict)
        alive = tmux_alive(cfg, ev)
        procs = gpu_processes(cfg, ev)
        finished = state == "finished" or bool(markers)
        if state == "waiting":
            reasons.append("state value is a waiting value")
            return "waiting", reasons, ev
        if finished:
            if state == "running" or alive or procs:
                raise Unknown("finished evidence contradicts a running state, a live session or a Paper A GPU process")
            if ev["gpu"]["unidentified_apps"]:
                raise Unknown("a GPU compute process could not be identified (could be Paper A)")
            reasons.append("finished/stopped evidence; no session and no Paper A GPU process")
            return "clear_finished", reasons, ev
        if state == "running":
            if alive and procs:
                reasons.append("running state, live session and a Paper A process on a GPU")
                return "clear_running", reasons, ev
            raise Unknown("running state without both a live session and a Paper A GPU process")
        if alive and not procs:
            reasons.append("live Paper A session without a Paper A GPU process (waiting for a card, or not yet on one)")
            return "waiting", reasons, ev
        if alive and procs:
            if cfg.get("allow_running_without_state"):
                reasons.append("live session and a Paper A GPU process (allow_running_without_state)")
                return "clear_running", reasons, ev
            raise Unknown("live session and GPU process, but no running state value")
        raise Unknown("no session, no GPU process and no finished evidence: stopped or not started; cannot tell")
    except Unknown as exc:
        reasons.append(str(exc))
        return "unknown", reasons, ev


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=None)
    ap.add_argument("--paper-a-checkout", default=None)
    ap.add_argument("--run-dir", default=None)
    ap.add_argument("--host", default=None, help="override the detected short host name (tests)")
    args = ap.parse_args(argv)
    host = args.host or platform.node().split(".")[0]
    report = {"label": "ENGINEERING_ONLY", "ai_assisted": "AI-assisted (Claude)",
              "utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "host": host,
              "config": os.path.abspath(args.config) if args.config else None}
    try:
        cfg = load_config(args.config, {"paper_a_checkout": args.paper_a_checkout, "run_dir": args.run_dir})
        verdict, reasons, evidence = decide(cfg, host)
    except Exception as exc:  # noqa: BLE001 - any failure is an unknown state, never a clearance
        verdict, reasons, evidence = "unknown", [f"check failed: {exc!r}"], {}
    report.update(verdict=verdict, reasons=reasons, evidence=evidence)
    if verdict in ("clear_running", "clear_finished"):
        report[KEY] = False
    elif verdict == "waiting":
        report[KEY] = True
    print(json.dumps(report, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
