#!/usr/bin/env python3
"""HTCondor job event log -> queue-time rows and M10 infrastructure outcomes. AI-assisted draft.

Events read (HTCondor user log, the ``log =`` file): 000 submit, 001 execute, 004 evicted,
005 terminated, 009 aborted, 012 held, 013 released. Each event starts with
``NNN (cluster.proc.subproc) <date> <time> <text>`` and ends with a line ``...``. Dates are either
ISO (``2026-11-14 01:02:03``, HTCondor >= 8.8 default) or ``MM/DD HH:MM:SS`` (older format; the year
must then be given). A time-zone suffix (``Z``, ``+01:00``) is applied when present (and then
``utc_offset_minutes`` must be 0); zone-less times are taken as UTC unless ``utc_offset_minutes`` says
otherwise. The pool's log time zone is a measured fact the cluster report should confirm.

Queue-time row (cluster runbook HTCONDOR_PREP_RUNBOOK_20261114 §4.2):
``probe, cluster.proc, submit_utc, execute_utc, end_utc, wait_s, run_s, site, host, gpu_name,
evictions, holds, exit`` with
* ``wait_s`` = first 001 - 000; ``run_s`` = 005 - last 001 (empty when an event is missing);
* ``site``, ``host``, ``gpu_name`` from an optional ``condor_history`` record (the event log alone does
  not carry them reliably); empty if not supplied;
* ``exit``: ``0``/``N`` (normal termination with return value), ``signal N``, ``aborted``, ``held``,
  ``idle`` (no 001 yet) or ``running``.

Outcome mapping for the M10 classifier (author's answer to Q8, extended by HTC-Q2 (b) on 14 Nov): on HTCondor an
eviction, a preemption, a hold for memory, disk or walltime and a container image pull failure are
``infrastructure_failure``. Each gets its own reason (``htcondor_eviction``, ``htcondor_preemption``,
``htcondor_memory_hold``, ``htcondor_disk_hold``, ``htcondor_walltime_hold``, ``htcondor_image_pull``,
``htcondor_restart_limit``), none of which is the runner's own ``timeout`` reason, so the repeated-timeout cap does
not count them; for walltime holds that is the author's answer HTC-Q1 (a) of 14 Nov (not counted, recorded
separately as infrastructure_failure). Any hold whose reason is not recognised is ``unclassified`` and needs a human:
it is never silently mapped. See
``infrastructure_outcome`` for how this combines with a job that later finished normally.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
from pathlib import Path

HEAD = re.compile(r"^(\d{3}) \((\d+)\.(\d+)\.(\d+)\) (\S+) (\d{2}:\d{2}:\d{2})(?:[.,]\d+)?([+-]\d{2}:?\d{2}|Z)? ?(.*)$")
NORMAL = re.compile(r"\(1\) Normal termination \(return value (-?\d+)\)")
SIGNAL = re.compile(r"\(0\) Abnormal termination \(signal (\d+)\)")
HOLD_CODE = re.compile(r"Code (\d+) Subcode (-?\d+)")
COLUMNS = ("probe", "cluster.proc", "submit_utc", "execute_utc", "end_utc", "wait_s", "run_s", "site", "host",
           "gpu_name", "evictions", "holds", "exit")


class EventLogError(ValueError):
    pass


def _zone_minutes(zone: str) -> int:
    if zone == "Z":
        return 0
    sign = 1 if zone[0] == "+" else -1
    digits = zone[1:].replace(":", "")
    return sign * (int(digits[:2]) * 60 + int(digits[2:]))


def _when(date: str, time: str, year: int | None, offset: int, zone: str | None = None) -> dt.datetime:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        t = dt.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")
    elif re.fullmatch(r"\d{2}/\d{2}", date):
        if year is None:
            raise EventLogError("MM/DD dates need --year")
        t = dt.datetime.strptime(f"{year}/{date} {time}", "%Y/%m/%d %H:%M:%S")
    else:
        raise EventLogError(f"unrecognised event date {date!r}")
    if zone is not None:
        if offset:
            raise EventLogError("the log carries a time-zone suffix; do not also pass utc_offset_minutes")
        offset = _zone_minutes(zone)
    return (t - dt.timedelta(minutes=offset)).replace(tzinfo=dt.timezone.utc)


def parse_events(text: str, *, year: int | None = None, utc_offset_minutes: int = 0) -> list[dict]:
    events, cur = [], None
    for line in text.splitlines():
        m = HEAD.match(line)
        if m and cur is not None:
            raise EventLogError(f"event header inside an open event (missing '...'): {line[:60]!r}")
        if m:
            code, cl, proc, _sub, date, time, zone, rest = m.groups()
            cur = {"code": code, "job": f"{int(cl)}.{int(proc)}",
                   "time": _when(date, time, year, utc_offset_minutes, zone), "text": [rest]}
        elif line.strip() == "...":
            if cur is None:
                raise EventLogError("event terminator without an event")
            events.append(cur)
            cur = None
        elif cur is not None:
            cur["text"].append(line.strip())
        elif line.strip():
            raise EventLogError(f"text outside an event: {line[:60]!r}")
    if cur is not None:
        raise EventLogError("truncated event at end of log")
    return events


HOLD_CODES = {(34, 102): "htcondor_memory_hold",      # JobOutOfResources, memory (HTCondor hold-reason table)
              (34, 104): "htcondor_disk_hold",        # JobOutOfResources, disk (author HTC-Q2 (b), 14 Nov)
              35: "htcondor_image_pull",              # InvalidDockerImage
              46: "htcondor_walltime_hold",           # JobDurationExceeded
              47: "htcondor_walltime_hold"}           # JobExecuteExceeded


def classify_hold(text: str) -> str:
    """Map a hold reason to an infrastructure reason, or 'unclassified'.

    The code and subcode decide first (HOLD_CODES). Text decides only when there is no code, or the code is a policy
    code (3 JobPolicy, 26 SystemPolicy, where a site's walltime or memory policy lands), or code 34 with another
    subcode (older releases write ``code 34,0`` for "Job has gone over memory limit"). Text order: walltime before
    memory (a walltime policy message may also mention memory usage), memory before disk; image pull only on pull or
    manifest wording."""
    t = text.lower()
    m = HOLD_CODE.search(text)
    code, sub = (int(m.group(1)), int(m.group(2))) if m else (None, None)
    if (code, sub) in HOLD_CODES:
        return HOLD_CODES[(code, sub)]
    if code in HOLD_CODES:
        return HOLD_CODES[code]
    if code is not None and code not in (3, 26, 34):
        return "unclassified"
    if "walltime" in t or "wall time" in t or "maxjobretirementtime" in t or "runtime exceeded" in t \
            or ("time limit" in t and "exceed" in t) or "duration exceeded" in t:
        return "htcondor_walltime_hold"
    # "Job has gone over memory limit" / "gone over cgroup memory limit" (HTCondor manual); site policies "exceeded".
    if re.search(r"over (cgroup )?memory limit", t) or ("memory" in t and "exceed" in t):
        return "htcondor_memory_hold"
    # disk: "exceeded its allocated disk", site policies "disk usage exceeded", "over disk limit/quota"
    if re.search(r"\bdisk\b", t) and ("exceed" in t or re.search(r"over (its |the )?(allocated )?disk", t)
                                      or ("disk" in t and ("limit" in t or "quota" in t))):
        return "htcondor_disk_hold"
    if ("pull" in t and ("image" in t or "docker" in t or "singularity" in t or "apptainer" in t)) \
            or "manifest unknown" in t or "pull access denied" in t:
        return "htcondor_image_pull"
    if "started 6 times" in t or "numjobstarts" in t or "too many starts" in t or "job restarts" in t:
        return "htcondor_restart_limit"
    return "unclassified"


def job_summary(events: list[dict], job: str) -> dict:
    ev = [e for e in events if e["job"] == job]
    if not ev:
        raise EventLogError(f"no events for job {job}")
    first = lambda c: next((e for e in ev if e["code"] == c), None)
    submit, execute = first("000"), first("001")
    executes = [e for e in ev if e["code"] == "001"]
    term = next((e for e in reversed(ev) if e["code"] in ("005", "009")), None)
    holds = [e for e in ev if e["code"] == "012"]
    released = [e for e in ev if e["code"] == "013"]
    evictions = [e for e in ev if e["code"] == "004"]
    exit_ = ""
    if term and term["code"] == "005":
        body = "\n".join(term["text"])
        m, s = NORMAL.search(body), SIGNAL.search(body)
        exit_ = m.group(1) if m else (f"signal {s.group(1)}" if s else "terminated")
    elif term:
        exit_ = "aborted"
    elif len(holds) > len(released):
        exit_ = "held"
    else:
        state = [e["code"] for e in ev if e["code"] in ("001", "004")]
        exit_ = "running" if state and state[-1] == "001" else "idle"
    iso = lambda e: e["time"].strftime("%Y-%m-%dT%H:%M:%SZ") if e else ""
    wait = int((execute["time"] - submit["time"]).total_seconds()) if submit and execute else ""
    run = int((term["time"] - executes[-1]["time"]).total_seconds()) if term and executes and term["code"] == "005" else ""
    hold_reasons = [" ".join(e["text"]) for e in holds]
    normal = bool(term and term["code"] == "005" and NORMAL.search("\n".join(term["text"])))
    return {"cluster.proc": job, "normal_termination": normal, "submit_utc": iso(submit), "execute_utc": iso(execute),
            "end_utc": iso(term), "wait_s": wait, "run_s": run, "evictions": len(evictions),
            "holds": len(holds), "exit": exit_, "hold_reasons": hold_reasons,
            "eviction_texts": [" ".join(e["text"]) for e in evictions]}


def infrastructure_outcome(summary: dict) -> dict:
    """HTCondor-level events of one job as M10 outcome input: ``{"final": ..., "attempts": [...]}``.

    ``attempts`` lists every eviction and hold with its reason. ``final`` is None if the job ended with a normal
    termination (005 with a return value): the run's own outcome then comes from the runner and its log, and earlier
    evictions or holds are history for the resume logic, not the outcome. Otherwise ``final`` is the job's
    infrastructure outcome: ``unclassified`` (a human decides) if any hold is unrecognised, listing every hold;
    else the first recognised hold; else the last eviction (``htcondor_preemption`` if its text says "preempt").
    A job still idle or running with no hold or eviction has ``final`` None as well."""
    holds = [{"event": "hold", "reason": classify_hold(r), "detail": r} for r in summary["hold_reasons"]]
    evictions = [{"event": "eviction", "reason": "htcondor_preemption" if "preempt" in x.lower() else "htcondor_eviction",
                  "detail": x} for x in summary["eviction_texts"]]
    attempts = holds + evictions
    final = None
    if not summary.get("normal_termination"):
        if any(h["reason"] == "unclassified" for h in holds):
            final = {"kind": "unclassified", "reason": "unclassified",
                     "detail": [h["detail"] for h in holds]}
        elif holds:
            final = {"kind": "infrastructure_failure", "reason": holds[0]["reason"], "detail": holds[0]["detail"]}
        elif evictions:
            final = {"kind": "infrastructure_failure", "reason": evictions[-1]["reason"],
                     "detail": evictions[-1]["detail"]}
    return {"final": final, "attempts": attempts}


def queue_rows(events: list[dict], probe_by_job: dict[str, str], history: dict[str, dict] | None = None) -> list[dict]:
    history = history or {}
    rows = []
    for job in sorted({e["job"] for e in events}, key=lambda j: tuple(int(x) for x in j.split("."))):
        s = job_summary(events, job)
        h = history.get(job, {})
        rows.append({"probe": probe_by_job.get(job, ""), **{k: s[k] for k in COLUMNS if k in s},
                     "site": h.get("site", ""), "host": h.get("host", ""), "gpu_name": h.get("gpu_name", "")})
    return rows


def write_tsv(rows: list[dict], path) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, delimiter="\t", extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("log", type=Path)
    p.add_argument("--probe", action="append", default=[], help="JOB=NAME, e.g. 123.0=P1")
    p.add_argument("--history", type=Path, default=None,
                   help="JSON {job: {site, host, gpu_name}} built from condor_history (attributes recorded by the caller)")
    p.add_argument("--year", type=int, default=None)
    p.add_argument("--utc-offset-minutes", type=int, default=0)
    p.add_argument("--tsv", type=Path, required=True)
    a = p.parse_args(argv)
    try:
        events = parse_events(a.log.read_text(encoding="utf-8"), year=a.year, utc_offset_minutes=a.utc_offset_minutes)
        probes = {}
        for x in a.probe:
            job, name = x.split("=", 1)
            cl, _, proc = job.partition(".")
            probes[f"{int(cl)}.{int(proc or 0)}"] = name
        history = json.loads(a.history.read_text()) if a.history else None
        write_tsv(queue_rows(events, probes, history), a.tsv)
        return 0
    except (EventLogError, OSError, ValueError) as exc:
        print("STOP: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
