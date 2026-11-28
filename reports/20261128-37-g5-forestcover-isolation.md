# compute/20261128-20 — G.5 expansion host check: `gc7rc_forestcover` PASS at its exact G.5 harness pin

**Result: PASS.** TASL-2 host checks 1-7 pass for `gc7rc_forestcover` at
`3f7b09febf401a83f3aa881f00eecdd032024416` on CPUs 4-7 in `torch312`; the record is independently
**ACCEPTED WITH MINORS** (documentation only). This closes the fourth and last of the four expansion addenda
host checks (Titanic, MetaMaze and ETTh1 already PASS).

- Task `compute/20261128-20`; round base `origin/main` `7cd65cfa`; queue `coord/coordinator` `52fb6892`.
- Source Local handoff `reports/20261128-14-g5-forestcover-isolation-handoff.md` (`coord/local` `f9193360`),
  reconciled by `reports/20261128-local-round-forestcover-reconcile.md` (`a3994698`); paper test base
  `57e6d1ed5945ab48684e24e145b69d333b4f77d4`.
- Deliverable branch `compute-g5-expansion-isolation-forestcover-20261128` @
  **`3a334d528d4be799c049d3748b8fec4c8c01f58b`** (first commit `5fc98d52`; the second force-adds exactly the two
  smoke `run.log` files that `.gitignore` line 3 `*.log` had dropped).
- Review branch `compute-g5-expansion-isolation-forestcover-20261128-review` @
  **`eb34c563e36f8f55058d49a0cc1a97edeb7e377a`**: first round **NOT ACCEPTED** on the incomplete capture set;
  re-check at `3a334d52`: **ACCEPTED WITH MINORS**. Review file
  `docs/r1/reviews/G5_EXPANSION_ISOLATION_FORESTCOVER_REVIEW_20261128.md` sha256
  **`42702d3a8414bc6827a886474fff5182a6e4808a785f20bb3baf82d2210545cf`**.
- Record `docs/r1/reports/tasl_chain_20261122/TASL2_ISOLATION_HOST_CHECK_X_gc7rc_forestcover_20261128.md`
  sha256 **`00b84d688d1b167bab1817709919fa7b8c8237ccaff3d60a1245e10a5c27eb12`** (unchanged by the fix).
- Capture set `…_20261128_captures/`: 36 files (35 payloads + `SHA256SUMS`), `SHA256SUMS` sha256
  **`95fb1af5f2d0aef4633a872cffde35dd9a5bea14796e930dadfe71096285e736`**; 35/35 verify in a fresh clone.

## Checks

| Check | Result |
|---|---|
| Gate lines | `host_check_host: TASL-2`, `host_check_harness_commit: 3f7b09fe…`, `host_check_items: 1-7 PASS`, `host_check_verdict: PASS` |
| C1 unprivileged namespaces | PASS (torch312 3.12.16 and `/usr/bin/python3` 3.10.12) |
| C2 Yama ptrace | PASS (`ptrace_scope=1`; unrelated same-uid sibling `EPERM`) |
| C3 delegated cgroup v2 / `cgroup.kill` | PASS (8G / swap 0; create→kill→empty→removed) |
| C4 non-root + interpreter `sys.path` | PASS (uid 1008; both interpreters) |
| C5 sandboxed CPU smoke | PASS (`effective=true`, `waivers={}`, `exceptions=[]`, frozen files unchanged) |
| C6 GPU smoke under lease | PASS (full UUID `GPU-4d623e76-…`, tensor sum 4096.0, matmul 16.0, torch 2.6.0+cu124, CUDA 12.4; lease 17:37:33–17:37:35Z; no foreign compute) |
| C7 end state | PASS (GPU idle, lease free, six leftover buckets empty, 333.8 GiB free, checkout at the pin) |
| Supplementary isolation test | 27 passed, 1 skipped (root-only) |
| Pins | node spec `ff2a585b…`, committed pin `78b48db9…`, edits `0219deb8…`, spec file `edd1a076…`, 16 frozen entries |
| Data | manifest `2b5cfb15…`, 2 files (`X.npy`, `y.npy`) re-hashed and matching |
| Environment | torch312 freeze 77 lines, sha256 `d2e70fe4…`, Python 3.12.16 |
| Harness candidate | one commit above kit `85851664`; only `audit_g5.py` (sha256 `5f384204…`) and `campaign_v2_diff.py` (sha256 `9d4f8e68…`), both matching the accepted harness review `4c721776…` |

No label, test or evaluation value was read; no G.1b/G.5/G.4 chunk ran; no deletion, commit or push on the host.
ENGINEERING_ONLY. The C6 smoke used 2 s of one card; no GPU-hour figure reached.

## Review minors (documentation/evidence coverage only; record bytes kept)

1. "Every C1-C6 step and every step-1-4 capture is `taskset -c 4-7`" is broader than the captures: affinity is
   not exposed by C1-C4 or by the bare sandbox argv, and `commands.txt` shows the phase3 script invoked without
   an outer `taskset` (the inner C2/C3/C4/C5 and pytest commands are pinned).
2. "No CPUs 8-11 were used" and the load-average figure are not in the captures.
3. The skip reason for the one skipped pytest is not captured.
4. `c7_final.json`'s `data.link` field inspects the node directory, not the `data` symlink; the symlink claim is
   supported by `git status` and `datapins.link_present`.
5. The CPU model `i9-14900KF` is not in the captures (confirmed by a live read-only host check).

All substantive checks passed. Attempt 1 (`20261128T173529Z`) was set aside as non-evidence because the copied
script's C2 probe and the supplementary pytest/GPU smoke were not pinned to the node's set; attempt 2
(`20261128T173716Z`) is the evidence session. The record discloses this and keeps attempt 1 in the run root.

## What happens next

1. The coordinator publishes the record and review.
2. Local fills the `gc7rc_forestcover` addendum gate and runs the draft checks; all four addenda host checks are
   then complete.
3. Campaigns still wait on the author's G.5 launch decision. No compute job ID is associated with this check.

Decided alone: to correct the C2/pytest/GPU-smoke CPU pinning and rerun the session before publishing, rather
than publish a check whose pinning did not match the node's set; to keep attempt 1 in the run root; and to
force-add the two ignored `run.log` files after the first review found them missing. No signed value, code,
spec or note was changed.
