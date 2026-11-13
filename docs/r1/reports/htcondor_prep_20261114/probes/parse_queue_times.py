#!/usr/bin/env python3
"""Build queue_times.tsv from HTCondor job event logs + condor_history/condor_q (read-only).
Authority: runbook §4.2 + errata A7-F13. Events: 000 submit, 001 execute, 004 evicted, 005 terminated, 012 held.
Event-log timestamps are the schedd's local time = Europe/Berlin (CET), converted to UTC here.
"""
import csv, glob, os, re, subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

PROBES = "/work/dwong/htcondor_prep_20261114/probes"
OUT = os.path.join(PROBES, "queue_times.tsv")
LOCAL = ZoneInfo("Europe/Berlin")
EV = re.compile(r"^(\d{3}) \((\d+)\.(\d+)\.\d+\) (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")

def events(path):
    out = []
    if not os.path.exists(path):
        return out
    for line in open(path, errors="replace"):
        m = EV.match(line)
        if m:
            t = datetime.strptime(m.group(4), "%Y-%m-%d %H:%M:%S").replace(tzinfo=LOCAL)
            out.append((m.group(1), t, f"{m.group(2)}.{m.group(3)}"))
    return out

def run(*a):
    try:
        return subprocess.run(a, capture_output=True, text=True, timeout=90).stdout.strip()
    except Exception:
        return ""

def history():
    out = run("condor_history", "dwong", "-limit", "500", "-af", "ClusterId", "ProcId",
              "JobStatus", "ExitCode", "LastRemoteHost", "MachineAttrCloudSite0", "RemoteWallClockTime")
    h = {}
    for line in out.splitlines():
        p = line.split()
        if len(p) >= 4:
            h[f"{p[0]}.{p[1]}"] = dict(jobstatus=p[2], exitcode=p[3],
                                       host=p[4] if len(p) > 4 else "", site=p[5] if len(p) > 5 else "",
                                       run_s=p[6] if len(p) > 6 else "")
    return h

def live():
    out = run("condor_q", "dwong", "-af", "ClusterId", "ProcId", "JobStatus", "HoldReason")
    m = {}
    for line in out.splitlines():
        p = line.split(None, 3)
        if len(p) >= 3:
            m[f"{p[0]}.{p[1]}"] = dict(jobstatus=p[2], holdreason=p[3] if len(p) > 3 else "")
    return m

def gpu(outfile):
    if not os.path.exists(outfile):
        return ""
    for line in open(outfile, errors="replace"):
        if re.search(r"(V100S|A100|L40S|H200|TITAN)", line) and not line.startswith("probe="):
            return line.strip()[:70]
    return ""

hist, lq = history(), live()
rows = [("probe","cluster.proc","submit_utc","execute_utc","end_utc","wait_s","run_s","site","host","gpu_name","evictions","holds","exit")]
for path in sorted(glob.glob(os.path.join(PROBES, "P*.log"))):
    probe = os.path.basename(path)[:-4]
    ev = events(path)
    def t(code):
        return next((e[1] for e in ev if e[0] == code), None)
    submit, exe, end = t("000"), t("001"), t("005")
    key = ev[0][2] if ev else ""
    h, l = hist.get(key, {}), lq.get(key, {})
    fmt = lambda x: x.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ") if x else ""
    wait = int((exe - submit).total_seconds()) if (submit and exe) else ""
    run_s = int((end - exe).total_seconds()) if (exe and end) else ""
    status = h.get("jobstatus", "") or l.get("jobstatus", "")
    exitcode = h.get("exitcode", "")
    exit_txt = exitcode if exitcode else ("HOLD:" + l.get("holdreason", "") if l.get("holdreason") else ("IDLE" if status == "1" else ""))
    rows.append((probe, key, fmt(submit), fmt(exe), fmt(end), wait, run_s,
                 h.get("site", ""), h.get("host", ""), gpu(os.path.join(PROBES, probe + ".out")),
                 sum(1 for e in ev if e[0] == "004"), sum(1 for e in ev if e[0] == "012"), exit_txt))
with open(OUT, "w", newline="") as f:
    csv.writer(f, delimiter="\t").writerows(rows)
print("wrote", OUT, "rows", len(rows) - 1)
