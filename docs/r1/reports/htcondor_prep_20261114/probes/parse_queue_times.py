#!/usr/bin/env python3
"""Build queue_times.tsv from HTCondor event logs + condor_history/condor_q (read-only).
Authority: runbook §4.2 + errata A7-F13. Events 000 submit, 001 execute, 004 evicted, 005 terminated, 012 held.
Join is by CLUSTER id (from clusters.tsv), not by log position, so it is robust to old/new event formats.
Event-log times are schedd-local = Europe/Berlin (CET), converted to UTC.
"""
import csv, glob, os, re, subprocess
from datetime import datetime
from zoneinfo import ZoneInfo

PROBES = "/work/dwong/htcondor_prep_20261114/probes"
OUT = os.path.join(PROBES, "queue_times.tsv")
LOCAL = ZoneInfo("Europe/Berlin"); UTC = ZoneInfo("UTC")
EV = re.compile(r"^(\d{3}) \((\d+)\.(\d+)\.\d+\) (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")

def run(*a):
    try: return subprocess.run(a, capture_output=True, text=True, timeout=120).stdout
    except Exception: return ""

def events(path):
    out = []
    if not os.path.exists(path): return out
    for line in open(path, errors="replace"):
        m = EV.match(line)
        if m:
            out.append((m.group(1), m.group(2), datetime.strptime(m.group(4), "%Y-%m-%d %H:%M:%S").replace(tzinfo=LOCAL)))
    return out

def history():
    out = run("condor_history", "dwong", "-limit", "1000", "-af", "ClusterId", "ProcId", "JobStatus",
              "ExitCode", "LastRemoteHost", "MachineAttrCloudSite0", "RemoteWallClockTime")
    h = {}
    for line in out.splitlines():
        p = line.split()
        if len(p) < 2: continue
        h[p[0]] = dict(jobstatus=p[2] if len(p) > 2 else "", exitcode=p[3] if len(p) > 3 else "",
                       host=p[4] if len(p) > 4 else "", site=p[5] if len(p) > 5 else "")
    return h

def live():
    out = run("condor_q", "dwong", "-af", "ClusterId", "JobStatus", "HoldReason")
    m = {}
    for line in out.splitlines():
        p = line.split(None, 2)
        if len(p) >= 2: m[p[0]] = dict(jobstatus=p[1], holdreason=p[2] if len(p) > 2 else "")
    return m

def gpu(outfile):
    if not os.path.exists(outfile): return ""
    for line in open(outfile, errors="replace"):
        if re.search(r"(V100S|A100|L40S|H200|TITAN)", line) and not line.startswith("probe="): return line.strip()[:70]
    return ""

# probe -> cluster from clusters.tsv (waves appended)
clusters = []
if os.path.exists(os.path.join(PROBES, "clusters.tsv")):
    for line in open(os.path.join(PROBES, "clusters.tsv")):
        p = line.rstrip("\n").split("\t")
        if len(p) >= 3 and p[0] != "probe": clusters.append((p[0], p[1], p[2]))

hist, lq = history(), live()
fmt = lambda x: x.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ") if x else ""
rows = [("probe","cluster.proc","submit_utc","execute_utc","end_utc","wait_s","run_s","site","host","gpu_name","evictions","holds","exit")]
for probe, cluster, sub in clusters:
    ev = [e for e in events(os.path.join(PROBES, probe + ".log")) if e[1] == cluster]
    def t(code): return next((e[2] for e in ev if e[0] == code), None)
    submit, exe, end = t("000"), t("001"), t("005")
    h, l = hist.get(cluster, {}), lq.get(cluster, {})
    wait = int((exe - submit).total_seconds()) if (submit and exe) else ""
    run_s = int((end - exe).total_seconds()) if (exe and end) else ""
    status = h.get("jobstatus", "") or l.get("jobstatus", "")
    exitcode = h.get("exitcode", "")
    exit_txt = exitcode if exitcode else ("HOLD:" + l.get("holdreason", "") if l.get("holdreason") not in ("", "undefined") else ("IDLE" if status == "1" else ("REMOVED" if status == "3" else "")))
    rows.append((probe, cluster + ".0", fmt(submit) if submit else sub, fmt(exe), fmt(end), wait, run_s,
                 h.get("site", ""), h.get("host", ""), gpu(os.path.join(PROBES, probe + ".out")),
                 sum(1 for e in ev if e[0] == "004"), sum(1 for e in ev if e[0] == "012"), exit_txt))
with open(OUT, "w", newline="") as f: csv.writer(f, delimiter="\t").writerows(rows)
print("wrote", OUT, "rows", len(rows) - 1)
