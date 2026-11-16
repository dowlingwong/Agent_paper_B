#!/bin/bash
# gpu_availability.sh — read-only GPU availability snapshot (author supplement 2, 14 Nov 2026).
# Records, per site and GPU model: total slots, idle slots, drained slots, other busy, and the
# container type advertised (HasDocker/HasSingularity). Appends one block to gpu_availability.tsv.
# The author requires a snapshot before every GPU submission and at least 3x per day.
# Usage: bash gpu_availability.sh [OUT_TSV] [NOTE]
set -euo pipefail
OUT="${1:-/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/htcondor-chain-20261114/docs/r1/reports/htcondor_chain_20261114/gpu_availability.tsv}"
NOTE="${2:-}"
TS_CET="$(TZ=Europe/Berlin date +%FT%T%Z)"; TS_UTC="$(date -u +%FT%TZ)"
[ -s "$OUT" ] || echo -e "timestamp_cet\ttimestamp_utc\tsite\tmodel\ttotal_slots\tidle_slots\tdrained_slots\tother_busy\tcontainer\tnote" > "$OUT"
python3 - "$OUT" "$TS_CET" "$TS_UTC" "$NOTE" <<'PY'
import subprocess, sys
out, ts_cet, ts_utc, note = sys.argv[1:5]
SITES = {
    "TOpAS": ["-pool", "c03-001-140.gridka.de"],
    "NEMO2": ["-constraint", 'CloudSite =?= "BwForCluster-Nemo2"'],
    "ETP-local": ["-constraint", "ProvidesETPResources =?= True"],
}
def collect(args):
    # condor_status 25.0.12 on this pool has no -af:j and -format accepts only one %s per call;
    # use plain -af and split from the right (Name has no spaces, the device name does).
    attrs = ["Name", "GPUs_DeviceName", "SlotTypeID", "State", "Activity",
             "HasDocker", "HasSingularity"]
    p = subprocess.run(["condor_status", *args, "-af", *attrs], capture_output=True, text=True)
    rows = []
    for line in p.stdout.splitlines():
        parts = line.split()
        if len(parts) < len(attrs):
            continue
        rec = {
            "Name": parts[0],
            "GPUs_DeviceName": " ".join(parts[1:-5]),
            "SlotTypeID": parts[-5],
            "State": parts[-4],
            "Activity": parts[-3],
            "HasDocker": parts[-2],
            "HasSingularity": parts[-1],
        }
        rows.append(rec)
    return rows
agg = {}
for site, args in SITES.items():
    try:
        rows = collect(args)
    except Exception as exc:  # noqa: BLE001 - a failed site is recorded, not hidden
        rows = []
        print(f"# {site}: condor_status failed: {exc}", file=sys.stderr)
    for r in rows:
        model = r.get("GPUs_DeviceName") or "(none)"
        if model in ("undefined", ""):
            model = "(none)"
        key = (site, model)
        a = agg.setdefault(key, dict(total=0, idle=0, drained=0, busy=0, docker=set(), sing=set()))
        a["total"] += 1
        state = r.get("State") or ""
        if state == "Unclaimed":
            a["idle"] += 1
        elif state == "Drained":
            a["drained"] += 1
        else:
            a["busy"] += 1
        if str(r.get("HasDocker", "")).strip().lower() == "true":
            a["docker"].add("HasDocker=true")
        if str(r.get("HasSingularity", "")).strip().lower() == "true":
            a["sing"].add("HasSingularity=true")
with open(out, "a") as f:
    for (site, model), a in sorted(agg.items()):
        container = ";".join(sorted(a["docker"] | a["sing"])) or "-"
        f.write("\t".join([ts_cet, ts_utc, site, model, str(a["total"]), str(a["idle"]),
                           str(a["drained"]), str(a["busy"]), container, note]) + "\n")
print(f"appended {len(agg)} rows to {out}")
PY
