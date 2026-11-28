# HTCondor cleanup — stale requests 759624, 759625 removed; 760065 confirmed withdrawn

Task `compute/20261128-04` (author's decision, 28 Nov 2026). ENGINEERING. Submit host deepthought.

## Outcome

| Job | Pre-check (from `condor_q -l`) | Action | Post-check |
|---|---|---|---|
| 759624 | `Owner = "dwong"`, `JobStatus = 1` (Idle), `Cmd = "/work/dwong/htcondor_prep_20261114/probes/probe.sh"`; `RequestGPUs = 1`, `RequestCpus = 2`, `RequestMemory = 4000`, `RequestDisk = 5000000` | `condor_rm 759624` | gone from `condor_q`; `condor_history -l` captured |
| 759625 | same owner/status/command and request as 759624 | `condor_rm 759625` | gone from `condor_q`; `condor_history -l` captured |
| 760065 | not in the queue (`condor_q -l` empty) | none (already gone) | `condor_history -l` shows `JobStatus = 3` (Removed), `RemoveReason = "via condor_rm (by user dwong)"`, `Cmd = "/work/dwong/paperb/work/trackp-p4-cluster-20261125/T1_versions/versions.sh"` |

`condor_rm` output: `All jobs matching constraint (ClusterId == 759624 || ClusterId == 759625) have been marked for removal`.

No other job was touched. The P.4 H200 test 760065 is recorded as withdrawn. Captures in this directory; `SHA256SUMS` binds them.

## Files

`q_759624.txt`, `q_759625.txt`, `q_760065.txt` (empty), `history_759624.txt`, `history_759625.txt`,
`history_760065.txt`, `q_after_759624.txt`, `q_after_759625.txt`, `condor_rm.txt`.

Decided alone: none beyond running the card's checks; the three ids met the named conditions.
