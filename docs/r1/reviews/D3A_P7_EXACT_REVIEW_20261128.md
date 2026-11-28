# Independent review — D.3a P7 at the frozen runtime (`-c 32768`, q8_0 K/V)

**Reviewed tip:** `db9fb948c4edd075ef822805cf5fe5071a541dfe` on
`compute-d3a-p7-exact-20261128`.
**Base:** `origin/main` `5200647086afc1e65dd65fd9e369e265af154935` (the D.3a note-fill commit;
`main` has since advanced — see the context note).
**Record:** `docs/r1/reports/d3a_p7_exact_20261128/D3A_P7_EXACT_RUNTIME_20261128.md`.
**Receipt:** run `d3a-p7-exact-20261128-c` / `-d`, 2026-11-28T08:38:47Z–09:05:41Z, TASL-2 RTX 4090
`GPU-4d623e76…0d94`.
**Method:** fresh detached worktree at the tip; no host access and no host workload. The only
execution was the stated local pytest, against a clean local checkout of harness `9bb41680`.

## Summary

The substantive conclusion is right. The exact frozen runtime starts and fits on the 24 GB card
(`-c 32768`, q8_0 K/V, one slot, 21,977 MiB at load), all 14 campaigns complete, and the two-seed
worker gate is **50/276 = 18.1159 % > 12.99 %** — a **STOP** for the P7 item. The record does not
claim a P7 PASS, does not propose changing the signed runtime, and explicitly refuses a rerun as a
fix; the runtime change it defers is correctly marked Level 2.

I cannot accept the receipt as delivered, however. The committed capture tree is missing **404 of
the 944 paths in its own outer manifest** (44 % of the 916 data entries), **all 28 inner manifests
fail `shasum -c`**, and both gate scripts die on the absent `runs.jsonl`. The record's §9 claim
that "all 28 inner sums verify" is false as committed, and the 50/276 gate cannot be recomputed
from the repository. One per-seed line is also arithmetically wrong. These are correctable (the
files exist on the author's disk and total only ~8.8 MB), but they are not cosmetic.

## What I verified

### Arithmetic and the gate

`worker_gate.json` and `p7_summary.json` are internally consistent and agree with each other.

| Quantity | Record | Verified from the captures |
|---|---|---:|
| Charged trials | 276 (200 harness + 76 replicate) | **276** (row sum; 138 per seed) |
| Successful | 226 | **226** |
| Failures | 50 | **50** (48 `invalid_config` + 2 admitted `runtime_error`) |
| Pooled rate | 18.116 % | **50/276 = 0.1811594** |
| Limit / gate | 12.99 % / FAIL | **0.1299 / FAIL** |
| Harness-only | 50/200 = 25.00 % | **50/200 = 25.00 %** (5 arms; FIXR3/EGATE clean) |
| Seed 6301 | 21/135 = 15.56 % | **22/138 = 15.94 %** |
| Seed 6302 | 29/141 = 20.57 % | **28/138 = 20.29 %** |
| Prechecks / skips / admitted RTE / unadmitted | 2 / 34 / 2 / 0 | **2 / 34 / 2 / 0** |

The 14-row table in §2 matches `worker_gate.json` cell-for-cell — trials, success, worker failures,
prechecks, skips, keeps, wall seconds to 0.1 s, worker seconds to 0.1 s and LLM calls — for all 14
rows. Totals are **1,611.943 s** wall and **316.636 s** worker (record 1,611.9 / 316.6). The
per-seed line is the one exception: the rows sum to 22/138 and 28/138, not 21/135 and 29/141
(finding M1). Both corrected rates remain above 12.99 %, so the STOP is unaffected.

### Runtime evidence

- `captures/server2/server_argv.txt` contains `-c 32768`, `--cache-type-k q8_0`,
  `--cache-type-v q8_0` and `-np 1`, with the signed GGUF path and `llama-server`.
- `captures/server2/props.json`: `default_generation_settings.n_ctx` **32768**, `total_slots`
  **1**, `build_info` **b11669-620d2225c**, model `google_gemma-4-31B-it-Q4_K_M.gguf`.
- `captures/server2/gpu_at_start.txt`: 08:38:34Z, 24,564 MiB total, **353 MiB used / 23,830 MiB
  free**, no compute process (this is the pre-load state, not the 21,977 figure).
- `captures/gpu_samples.csv` first row 08:38:47Z: **21,977 MiB used / 2,206 MiB free**, server PID
  1310012 at 21,618 MiB. Peak over 795 samples: **21,999 / 2,184 MiB**.
- `captures/server2/gpu_at_end.txt`: 21,999 MiB used / 2,184 MiB free, the run's own server at
  21,640 MiB; `compute_after_end.txt` is empty. No foreign compute PID appears in any 2 s sample.
- The 21,977 MiB "at load" figure is in `captures/gpu_samples.csv`, not in `server2/`; the server
  log that would independently show it (and the KV types and 4.8 s load time) is **not delivered**
  (finding B1).

### Captures and hashes

- Report-root `SHA256SUMS` verifies **2/2** (record `418fa984…`, `captures/SHA256SUMS`
  `8fc4906d…`). Every hash quoted in §9 matches the delivered bytes.
- `captures/SHA256SUMS` has 944 entries: 916 data files + 28 inner manifests. Only **540 verify**
  (the 28 inner manifests + 512 data files); **404 paths are absent** and `shasum -c` exits 1.
- All **28** inner `SHA256SUMS` fail; their 1,740 references include **804 absent** paths. There
  are **no digest mismatches**: every present file hashes correctly. The defect is scope, not
  corruption.
- Absent classes: **292 `.log`** (290 trial `art/trial-*/run.log` + `server2/server.log` +
  `attempt-0-partial/run-s6301.log`), **42 `.jsonl`** (14 each `runs.jsonl`, `ledger.jsonl`,
  `events.jsonl`), **56 `.gz`** (OpenML cache / dataset) and **14 `.pyc`**. The trial logs and the
  three `.jsonl` streams are the primary records for the 50 failures and the 2 admitted runtime
  errors.
- `worker_gate.py` and `summarise.py` cannot be rerun from the deliverable: both raise
  `FileNotFoundError` on
  `run-s6301/chunks/A0/campaigns/openml_climate__s6301/runs.jsonl`. The classifier also needs
  `art/trial-*/run.log` to admit the two `ParserError` trials; those logs are absent, so the
  committed `admitted_truncated_mapping_parsererror` labels cannot be checked.

### Peaks, latency and projection

- GPU: 100 % util, 21,999 MiB used, 2,184 MiB free minimum, 392.5 W, 72 °C, 795 samples.
- Host RAM: 14.27 GB used of 67.12 GB, 51.96 GB minimum available; first sample 08:40:20Z, the
  disclosed 93 s after the driver (the sampler used a locale-dependent `free` match before
  `memmon.sh`).
- Scratch: 3.95 MB (6301) / 3.52 MB (6302), cache 0.12 MB, cache-tree hash `01c8e35a…`.
- Latency: 202 calls with a latency, mean 5.1069 s, maximum 11.0384 s, largest campaign mean
  5.764 s, 256 total calls.
- Projection: 18 × max calls × 5.764 s gives 2,178.8 / 2,282.5 / 2,282.5 / 4,980.1 / 311.3 /
  726.3 / 2,075.0 s, sum 14,836.5 s per node = **28.85 GPU-h** for seven nodes; the A0R-at-11.038 s
  sensitivity is **32.91 GPU-h**. The arithmetic is correct. The record correctly does not bind it
  to the note.

### Tests and scope

- With `AR_HARNESS_ROOT` set to a clean checkout of harness `9bb41680`, the stated command gives
  **17 passed in 0.82 s** (record: 17 passed in 0.47 s; timing only). The two files contain 4 + 13
  test functions, so the count is the expected one.
- `git diff --stat 52006470..HEAD` touches only
  `docs/r1/reports/d3a_p7_exact_20261128/` (543 files, 18,974 insertions); no repository code,
  signed file, seed, request or tolerance changed. The manifest's pins still hash-match.

### Discarded start

`captures/attempt-0-partial/` contains `README.txt`, `run.status` (start only, no seed line),
137 GPU samples from 08:33:15Z–08:37:51Z (server PID 1302930) and an affinity probe. There is no
campaign tree from attempt 0 and the gate rows are all from the receipt (`-c`/`-d`). The
"non-receipt" claim is consistent with what is delivered. The README's claim that **both** run logs
are kept is not: only `run-s6301.log` is listed, `run-s6302.log` never existed, and neither is
delivered (finding m3).

## Findings

### BLOCKING

**B1 — The capture set is incomplete; the manifests do not verify and the gate is not
reproducible.** `shasum -a 256 -c captures/SHA256SUMS` returns 540 OK and 404 `FAILED open or read`
(rc 1); all 28 inner manifests fail, with 804 absent references; the record's §9 "all 28 inner sums
verify" is false as committed. The absent files include every trial `run.log`, `server2/server.log`,
and the `runs.jsonl` / `ledger.jsonl` / `events.jsonl` streams of all 14 campaigns. Consequences:
(i) neither `worker_gate.py` nor `summarise.py` runs on the delivered tree; (ii) the 50 failures,
the 2 admitted runtime errors and the 34 skips cannot be checked against their raw records; (iii)
§1's statement that the server log is in `captures/server2/` is false. The root `SHA256SUMS` and
the hashes of the delivered files are sound — this is a delivery-scope defect, not corruption.
Remedy: force-add the 404 ignored files (`git add -f`; the whole capture tree is ~8.8 MB), then
re-run `shasum -c` on the outer and all 28 inner manifests; the existing hashes are those of the
author's files, so no manifest rewrite should be needed unless a file changed. If a manifest is
rewritten, update `captures/SHA256SUMS`, the root `SHA256SUMS` and §9 together. Then re-run both
scripts to show they reproduce the committed JSON. Alternatively regenerate the manifests over the
delivered set and restate §9 — but that loses the raw per-run evidence and does not make the gate
recomputable.

### MAJOR

**M1 — The per-seed split is wrong.** §3 says 6301 **21/135 = 15.56 %** and 6302 **29/141 =
20.57 %**. The 14 rows sum to 6301 **22/138 = 15.94 %** and 6302 **28/138 = 20.29 %** (50/276 in
both cases). The pooled figure and the verdict are unaffected — both corrected rates are also
above 12.99 % — but a per-seed line that does not reconcile to the table should not stand in the
receipt.

### MINOR

- **m1 — "50 (all `invalid_config`)" plus "2 admitted runtime errors" reads as 52.** The two
  `ParserError` trials are inside the 50: 48 raw `invalid_config` + 2 `runtime_error` that
  `worker_gate.py` folds into `invalid_config`. State the 48 + 2 split explicitly.
- **m2 — 21,618 MiB is the at-load value, not the end-of-chunk value.** §4 says the recorded "other
  process" is 21,618 MiB "at the end of each chunk"; `chunk.json` records 21,638 MiB for 6301 A0
  and 21,640 MiB for the other 13. 21,618 is the first `gpu_samples.csv` row. Use the range or the
  representative value.
- **m3 — The attempt-0 disclosure overstates what is kept.** §7 and
  `attempt-0-partial/README.txt` say "the two run logs are kept"; only `run-s6301.log` is listed
  (and it is absent, B1) and no `run-s6302.log` exists because seed 6302 never started. Say "the
  partial `run-s6301.log`", or deliver it.
- **m4 — The causal sentence is stronger than the design.** "The exact runtime therefore changes
  the manager's proposal stream enough to move the gate from PASS to FAIL … a property of the
  measured runtime" rests on one two-seed sample at each runtime. The harness and seeds are the
  same and the manager's per-call seed is deterministic, so the attribution is plausible, but the
  record should say "observed at the exact runtime in this sample"; the STOP does not depend on
  the causal claim.
- **m5 — `affinity_check.txt` contains an unexplained `0-31` worker.** Its fourth line is
  `train.py --config config.yaml pid=1313204 Cpus_allowed_list=0-31`, while `affinity_probe.txt`
  (08:38:52) and 434/435 `affinity_all.txt` lines show `16-31` (one `gone`). The check had no cwd
  filter, unlike the accepted P7's check, so this is most likely a co-tenant; the record should
  say so or re-run the check with the cwd filter. As written, "every worker … ran under
  `taskset -c 16-31`" is not supported by its own capture.
- **m6 — The lease paths in the record are not the paths the captured script locks.**
  `start_server.sh` locks `$B/gpu0.lock` and `$B/cpus-16-31.lock` under the work root, while the
  record names `~/r1_locks/gpu0.lock` and `~/r1_locks/cpus-16-31.lock`; `observed.json` asserts
  the canonical `lease_path` but no canonical-lock capture is delivered. Confirm the canonical
  leases were held by the driver, or reword to the local locks.

## Context note (not a finding against this unit)

`origin/main` has advanced to `53f58881`, which carries the author's **R1-D3-REV5** decision
(28 Nov 2026): the stage worker-failure STOP becomes **18.53 %** on the matching
`append_only_summary` memory mode, and the row explicitly cites this run's 50/276 = 18.12 % as its
motivation. It landed 37 minutes after this tip. Under revision 5, 18.12 % is below 18.53 %, so if
rev 5 is signed and frozen the P7 gate would be re-read; that is precisely the Level 2 decision
the record asked for. This review is against the stated base (rev 4, 12.99 %) and does not fault
the record for not anticipating a later author row, but the coordinator should reconcile rev 5
before merging this record as a current verdict.

## Verdict

**Verdict: CHANGES REQUIRED**
