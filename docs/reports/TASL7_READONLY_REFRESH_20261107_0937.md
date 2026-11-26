# TASL-7 read-only refresh — 7 November 2026, 09:37 CET

AI-assisted (Codex). The author responded to the previous ownership question: “你继续执行，不用管他。只要能跑就去跑” (PLAN §10 `R1-TASL7-AGENT-OCCUPANCY-07NOV`). This permits continuing authorized work without treating the mere presence of other users' agent processes as an automatic STOP. It does not authorize preemption, modifying another person's data, deletion, or bypassing B1's other launch conditions.

At 08:37:16 UTC (09:37:16 CET) a single SSH session performed only the following observations. The local complete capture is retained at `/private/tmp/tasl7-readonly-20261107-0938.txt`, SHA-256 `018fe4fc81bf24495b2834bcfbe8102652b11e29005201e7fa6b8a9c13e87475`. It includes full STATUS files and process arguments; the capture is retained locally rather than reproduced in the Git report because it contains other users' process information. This report is a selected summary, not a claim of an atomic host snapshot.

```bash
set -C
ssh -o BatchMode=yes -o ConnectTimeout=12 tasl7 'bash -s' > /private/tmp/tasl7-readonly-20261107-0938.txt 2>&1 <<'REMOTE'
set -u
date -u
hostname
id
ls -la "$HOME/r1_locks"
for repo in "$HOME/exam-x/work/agent_paper_B" "$HOME/r1_trackp/Agent_paper_B" "$HOME/r1_tracks/work/Agent_paper_B"; do
  printf '\nCHECKOUT %s\n' "$repo"
  if test -f "$repo/docs/r1/STATUS.md" && test -r "$repo/docs/r1/STATUS.md"; then sha256sum "$repo/docs/r1/STATUS.md"; cat "$repo/docs/r1/STATUS.md"; else printf 'STATUS_MISSING_OR_UNREADABLE\n'; fi
done
printf '\nGPU CENSUS\n'
nvidia-smi --query-gpu=index,uuid,memory.used,memory.total,utilization.gpu --format=csv
nvidia-smi --query-compute-apps=pid,process_name,used_gpu_memory --format=csv
printf '\nPROCESS CENSUS\n'
ps -eo user,pid,ppid,etime,comm,args | grep -E '[t]rks-watch|[t]rks_watch|[l]lama|[p]ython|[g]uardian|[c]odex|[c]laude'
printf '\nLOCK USERS\n'
fuser "$HOME/r1_locks/gpu0.lock" 2>&1 || true
printf '\nDISK\n'
df -h "$HOME/exam-x/work"
REMOTE
result=$?
shasum -a 256 /private/tmp/tasl7-readonly-20261107-0938.txt
exit "$result"
```

The three complete STATUS files were readable, with SHA-256 values `65661d28abfc301ac155d9ae7a87f570f196753e1a8b98a1622129915307b1b6` (exam), `dd1c19142ee869568b4a4ba4360ceb878a1d6253bb7ee139da15cac232189317` (Track P), and `97b7217a49d47d857083ee695d96eeb5fd5a9cf1a275b4f4de0d2dc9a7922faf` (Track S). This command prints a marker on a missing STATUS but does not fail the overall session for that marker; none was observed in this capture. The output is historical project STATUS text, not proof of current job ownership or author permission.

GPU index 0 was `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, with 236/24564 MiB used and 0% reported utilization; the compute-app query listed no process. `fuser` printed no lock user, but its status was deliberately swallowed, so that is not proof the flock is obtainable. `trks-watch` remained visible as the author's process; other users' agent processes and an Ollama service were also listed. The approved work path's filesystem showed 585 GiB available. These observations do not establish a held GPU lease, future availability, server/worker safety, watcher loaded-code identity, or a Track P/S handover. No model, GPU workload, marker, lease, server or job was intentionally started or stopped, and no intentional remote mutation was issued; tool side effects and concurrent changes were not independently monitored.

**Remaining STOP:** B1's strict no-deletion/STOP implementation, tests, reviewed final checkout, real author gate, site preflight and reviewed handover are incomplete. The authorized operator must repeat an immediate occupancy and held-lock preflight when those prerequisites are ready, and cannot preempt jobs or affect other work. The time for site qualification depends on actual occupancy and verified capabilities; the local engineering/review effort is still open. Independent review of this report is required.
