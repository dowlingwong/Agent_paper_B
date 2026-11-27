# compute/20261128-04 — remove the stale HTCondor requests 759624, 759625 (and 760065, withdrawn), records kept

Author's decision (28 Nov, in the coordinator session): "759624 / 759625 确认仍是 Idle 的旧探针后，保留记录并移除。`760065` 按已撤处理。"

For each of `759624`, `759625`, `760065`, on the submit host:
1. Capture `condor_q -l <id>` to a file **before** anything else. Remove only if all hold: `Owner == "dwong"`, `JobStatus == 1` (Idle), and for
   `759624`/`759625` the command is the 13 Nov `probe.sh` (P6/P7); for `760065` the P.4 T1 cluster test (H200 request). If any check fails (running,
   held, another owner, another command), do **not** remove it: report the captured attributes.
2. `condor_rm <id>`; then capture `condor_history -l <id>` (or `condor_q` showing it gone).
3. If `760065` is already gone from the queue, capture `condor_history -l 760065` and record it as withdrawn.

Touch no other job. Commit the captures and a short record (`docs/r1/reports/htcondor_cleanup_20261128/`, with SHA256SUMS) on a branch `compute-htcondor-cleanup-20261128`;
documentation only, no review needed beyond the coordinator's check. Report the three outcomes in one table. Do this alongside `compute/20261128-01`
(TASL-7 E0, first) and `compute/20261128-03` (D.3 single-card preflight on A100/L40S), not before them.
