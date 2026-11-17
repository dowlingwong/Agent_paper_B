# Track P attempt-1 artifact backup / TASL-2 copy (17 November 2026, after TASL-7 recovery)

**Status: TASL-7 recovered; local archive + TASL-2 copy in progress/complete; the `/ceph/` leg is not
available from our hosts and is recorded as a STOP/deferral; Unit B on TASL-2 is separately STOPPED on a
code-host constraint (below).** AI-assisted; no GPU evidence; nothing deleted.

## Recovery

TASL-7 answered at `2026-11-17T23:02:25Z` after the multi-hour outage (SSH/Tailscale failure); host is up
(9 min at first check), RTX 4090 driver 580.178.04, GPU idle, 529 G free, checkout `b9ad6f8f`
(`trackp-20261026`). The attempt-1 root `/home/dowling/r1_trackp/runs/p3a_operator_20261027` is intact.

## Artifacts (hashes from TASL-7)

- journal `journal.jsonl` sha **`1e73e80fac2fb5262cffb8d599c8bd861d99d9f4b23b3c20f56543bca501a344`**
  (81 lines); global lease log sha
  **`6950509182f4230dd2c7e2bad4253748415fa969e84ef9bdac21e19242b55077`** (111 lines).
- `EVIDENCE/<base>/final/saved` (5 files each):
  `kev-0.8b` 45,523,843 B; `kev-4b` 135,359,436 B; `qwen3.5-0.8b-base` 43,477,294 B;
  `qwen3.5-4b-base` 130,237,336 B. Each `final/manifest.json` has 4 recorded model files;
  `config_sha256 64073cea…`, `data_manifest_sha256 b963be2d…` for all four.
- TASL-7 local archive (selected artifacts only): `/home/dowling/r1_trackp/backups/
  p3a_attempt1_final_saved_20261117T0015Z.tar.gz`, **sha256
  `fa2437ee52d8873075c0bed6e88fba16d04deb2428e931a365dc602cdf902c87`**, 313 M.

## Ceph leg — unavailable

`/ceph/srv/dwong/paperb` does not exist on TASL-7 or TASL-2 (`/ceph` is not mounted there); the cluster
agent's ceph path is not reachable from our hosts and running on deepthought/HTCondor is out of our scope.
The ceph backup is therefore **deferred to the cluster agent/author**; the TASL-7 local archive and the
TASL-2 copy are the available backups, with the hashes above. No deletion of any source.

## TASL-2 copy

Target: `/home/dowling/r1_trackp/backups/p3a_attempt1_final_saved_20261117T0015Z.tar.gz` and (for Unit B)
an attempt-1 root at `/home/dowling/r1_trackp/runs/p3a_operator_20261027` built from it (journal +
`EVIDENCE/<base>/final/saved` + `final/manifest.json`), with the attempt-1 lease log
`69505091…` placed for provenance. A partial earlier copy of full `final/` trees (which include 1.7 GB
`lora/` checkpoints) was moved aside under `runs/_partial_attempt1_copy_*` (not deleted) after stopping
that transfer; only the saved dirs/manifests are needed for Unit B. The transfer is slow (Tailscale);
its final hash/verification is recorded in the run-in-progress record when complete.

## Unit B on TASL-2 — STOP on code-host constraint

Code D `8662e359` hard-codes the TASL-7 host contract: `verify_probes_only_pins` refuses any hostname
other than `tasl-7`, requires driver `580.178.04` and compares the current boot id with attempt-1's
`2c9bb104…`. TASL-2 is `TASL-2`/driver `535.309.01`/boot `86c613a9…`, so D would STOP before any
root/marker/GPU work. The marker helper is also absent on TASL-2 (installable from the committed script).
Running Unit B on TASL-2 therefore needs a reviewed host-adaptation code unit (C2), a new mechanical pin
child D2, and an authority amendment because `R1-TRACKP-UNITB` names D (`R1-TRACKP-TASL2-HOST` authorizes
the host move but not an unreviewed code change). **No Unit B command was run; no GPU lease/marker taken.**
Decision needed from the author: (a) authorize C2 + D2 + amendment, or (b) keep Unit B on TASL-7 once its
attempt-1/lease/env contract is satisfied (TASL-7 is back), or (c) waive the host checks in an authorized
way. Until then Unit B is BLOCKED.
