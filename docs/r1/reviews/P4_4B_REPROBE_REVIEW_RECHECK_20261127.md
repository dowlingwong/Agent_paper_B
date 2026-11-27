# Tier-E re-check — Ada P.4 4B re-probe (`compute/20261127-24`), tip `a801dc60`

Verdict: ACCEPTED

**Reviewer.** Same fresh, independent tier-E reviewer as the R1 review
`docs/r1/reviews/P4_4B_REPROBE_REVIEW_20261127.md` (sha256
`28c785d3969a5859e0e71e6c9ab16aa8545b1b6a89ca054cdb3b166ee0b09674`, R1 tip
`6a37b9638df01576a2680127048a353452548da4`, R1 verdict `CHANGES REQUIRED`). This re-check supersedes that verdict
for the new tip. Read-only on the deliverable: no job launched, stopped or retried; no label, evaluation, test or
sealed-evidence data read; the deliverable branch was not modified; `main` was not pushed. The only writes are this
re-check file and scratch under `/tmp` and the session temporary directory.

**Target.** `compute-p4-4b-reprobe-20261127` @ `a801dc60b1a84a1bde5bc5cb3872183ba709f708`, one new commit on
`6a37b9638df01576a2680127048a353452548da4`; base of the unit remains `origin/main`
`e92f3c7389e06347a0ff78f5f68971024133c670`. The fix commit is docs-only and changes no code.

**Summary.** All four R1 findings are closed and no measured value changed. The two `p4_run.log` files are now in
`git ls-tree` and the record-level `SHA256SUMS` verifies **20/20 OK (rc 0)** on a clean checkout of `a801dc60`.
`probe_charges.json` is the final live `p4_lib.probe_charges()` snapshot: totals `2.1603 + 0.9307 = 3.091`, T1
`0.0`, `pending: []`, `unrecorded: []`, and both `charge_files` sha256s equal the committed
`charge_files/*.json`. `probe_records.json`, the spec, both stage manifests, both job records, both `out.tar`s,
both receipts and both launcher records are byte-identical to the R1 tip. The report's F3/F4 wording now matches
the evidence. No remaining findings.

## 1. The fix commit changes only the five stated files; no measured artifact changed

```
$ git log --oneline 6a37b963..a801dc60
a801dc60 docs(r1): P.4 re-probe package — commit the p4_run logs and final charges (review F1/F2/F3/F4)
$ git diff --stat 6a37b963..a801dc60
 .../P4_ADA_4B_REPROBE_20261127.md                  | 12 +++--
 .../trackp_p4_probe_ada_20261127b/SHA256SUMS       |  4 +-
 .../probe_charges.json                             | 56 ++++++++++++++++------
 .../kev-4b/attempt-1/p4_run.log                    | 14 ++++++
 .../qwen3.5-4b-base/attempt-1/p4_run.log           | 14 ++++++
 5 files changed, 78 insertions(+), 22 deletions(-)
```

Blob identity against the R1 tip (`git rev-parse <tip>:<path>` compared for each):

| Artifact | At `6a37b963` | At `a801dc60` |
|---|---|---|
| `probe_records.json` | `62a92d71…` | **same** |
| `p4_probe_spec_ada_b.json` | `7181ebc5…` | **same** |
| `stage_kev-4b.json`, `stage_qwen3.5-4b-base.json` | `53feff7b…`, `50a06257…` | **same** |
| `charge_files/*_wallclock.json` | `9a1949a1…`, `fa49096f…` | **same** |
| `trackp-p4-probe-20261127-b/_wallclock.json` | `fa49096f…` | **same** |
| both `job_record.json`, both `out.tar`, both `SEAL_RECEIPT.json`, both `direct_launch.json` | as in R1 | **same** |

So the measurements, seals, charge files and printed lines are exactly the ones verified in R1; only the missing
logs, the standalone charge audit file, the manifest and the report wording changed.

## 2. The two `p4_run.log` files are committed and the record manifest is 20/20 OK

Clean checkout of `a801dc60` (detached worktree, `git status --short` empty):

```
$ git ls-tree -r --name-only a801dc60 -- docs/r1/reports/trackp_p4_probe_ada_20261127b/ | grep p4_run.log
.../trackp-p4-probe-20261127-b/kev-4b/attempt-1/p4_run.log
.../trackp-p4-probe-20261127-b/qwen3.5-4b-base/attempt-1/p4_run.log

$ cd docs/r1/reports/trackp_p4_probe_ada_20261127b && sha256sum -c SHA256SUMS
20 lines: all OK; rc 0
```

Each attempt directory now has six files (`SEAL_RECEIPT.json`, `SHA256SUMS`, `direct_launch.json`,
`job_record.json`, `out.tar`, `p4_run.log`), matching the seal's copy. The two logs' hashes equal the receipts'
`run_log_sha256` and the manifest's lines:

```
b0e8647eb2d135e90d6266b5418b13a2ddef75aeba83b91d043251fed3296671  kev-4b/attempt-1/p4_run.log
d6ff3299a08daad11e69cc6a79ee18e3762477ea414463d3a9edd0b692ea623b  qwen3.5-4b-base/attempt-1/p4_run.log
```

The `kev-4b` log ends `P4 probe venv job end 2026-11-27T12:18:26Z rc=0` and carries the JSON tail with peak
14,135 MiB and 10.0458 s/step; the `qwen3.5-4b-base` log is the same form with 16,959 MiB and 9.9981 s/step. Both
match the R1 records and the live seal.

## 3. `probe_charges.json` is the final live snapshot; `probe_records.json` is untouched

`probe_charges.json` sha256 `833861b19c78c26b58b4ecbe8227a305d2b16e34b071ee6a624db8e80a67b5d6`. I re-derived it
from a read-only `/tmp` copy of the two live sealed runs with `p4_lib.probe_charges(root)` (no `--wallclock` input,
no `--t1-wallclock`; the charge files are applied by default). It is equal to the committed file after dropping
the absolute `path` keys, including every attempt's charge, `charge_basis: "_wallclock.json"`, the `t1` block and
the `charge_files` lists.

```
total                3.091   (2.1603 prior + 0.9307 this run)
trackp-p4-probe-20261125-a total 2.1603, 8 attempts, charge_files [_wallclock.json 9a1949a1…]
trackp-p4-probe-20261127-b total 0.9307, 2 attempts, charge_files [_wallclock.json fa49096f…]
t1_gpu_hours         0.0     (job 760065; source trackp-p4-probe-20261127-b/_wallclock.json)
pending: []   unrecorded: []
```

The two `charge_files` sha256s equal the committed copies
`charge_files/trackp-p4-probe-20261125-a_wallclock.json` = `9a1949a1…` and
`charge_files/trackp-p4-probe-20261127-b_wallclock.json` = `fa49096f…`; the new run's live/copy
`trackp-p4-probe-20261127-b/_wallclock.json` is byte-identical to the latter.

`probe_records.json` is untouched (`62a92d71…`), so its lines still read
`p4_probe_gpu_hours: 3.10` and the two `p4_probe_charge_file:` lines with `9a1949a1…` / `fa49096f…`; its internal
`probe_charges` sub-block remains the first-build snapshot (`charge_files: {}`), as documented by the record's
`binding_note` (the Markdown lines bind, not that sub-block). The standalone `probe_charges.json` now carries the
final charge-file basis. This is the expected write-once split, not a discrepancy.

## 4. The report's F3/F4 wording is accurate

`P4_ADA_4B_REPROBE_20261127.md` sha256 `fe764cda1822213dad46ead7252c74284745c20e0e76673e17061f8997bbc27b`
(was `2c54c9cf…`). The diff is confined to the two wording findings:

- "launch-verified peaks" → **"sampler-measured peaks"**; the peaks come from `out/probe/<arm>.gpu_mem.csv`,
  which is what the report now says.
- "no … sealed read" → **"no label, evaluation or test read; the only sealed file read was the prior
  `kev-0.8b/attempt-4` probe record, the required first-arm gate (not sealed evidence data)"**. The gate
  (`check_first_probe_record`) reads that attempt's `job_record.json`, `SEAL_RECEIPT.json` and `SHA256SUMS`; "the
  probe record" is the sealed attempt, and the disclaimer "not sealed evidence data" is correct. No label,
  evaluation or test file was read.
- "the 4B fit decision is resolved on Ada … so no H200 route is needed" → **"The Ada class fits both 4B arms with
  activation checkpointing at micro-batch 8 on an empty 48 GB card (headroom 0.7124 and 0.6549 of the card). This
  is a measured fit; the class choice for the note remains the coordinator's/author's."** This matches the
  measurement and leaves the route choice where it belongs.

No other report sentence changed. The four `p4_estimate_hours` lines, the `p4_probe_gpu_hours: 3.10` line, the two
`p4_probe_charge_file` lines and the projection 20.57 / 23.67 GPU-h / 29.855 slot-h are byte-identical to R1.

## Findings status

| R1 finding | Status | Evidence |
|---|---|---|
| **F1 — MAJOR (blocking):** missing `p4_run.log`, record `SHA256SUMS` failed 18/20 | **closed** | both logs in `git ls-tree`; hashes `b0e8647e…` / `d6ff3299…`; `sha256sum -c SHA256SUMS` = 20/20 OK, rc 0; six files per attempt dir |
| **F2 — MINOR:** `probe_charges.json` was the first-build snapshot | **closed** | final `p4_lib.probe_charges()` snapshot, equal to a fresh derivation after dropping paths; totals `2.1603 + 0.9307 = 3.091`; both charge-file sha256s match |
| **F3 — NIT:** "no … sealed read" imprecise | **closed** | report now names the prior `kev-0.8b/attempt-4` probe record as the only sealed file read and distinguishes it from sealed evidence data |
| **F4 — NIT:** "launch-verified peaks" / route resolution | **closed** | "sampler-measured peaks"; the fit is stated as measured and the class choice is left to the coordinator/author |

No new findings. The only residual note is the expected one in §3: `probe_records.json`'s internal `probe_charges`
sub-block is still the first-build snapshot, by design; the standalone `probe_charges.json` and the record's
top-level `charge_files` carry the final basis, and the printed lines are unchanged.

## Hashes checked at `a801dc60`

| Object | sha256 |
|---|---|
| R1 review file (`P4_4B_REPROBE_REVIEW_20261127.md`) | `28c785d3969a5859e0e71e6c9ab16aa8545b1b6a89ca054cdb3b166ee0b09674` |
| record `SHA256SUMS` (new) | `547be44d419820794686a923949739a4d86f2362023a08ec6b8d4be5bad70dc9` |
| `probe_charges.json` (new) | `833861b19c78c26b58b4ecbe8227a305d2b16e34b071ee6a624db8e80a67b5d6` |
| `P4_ADA_4B_REPROBE_20261127.md` (new) | `fe764cda1822213dad46ead7252c74284745c20e0e76673e17061f8997bbc27b` |
| `probe_records.json` (unchanged) | `62a92d716ce8a000e72c11930f3cd7cbbab976417eaef7fb3f88a5b2d9efcb81` |
| `p4_probe_spec_ada_b.json` (unchanged) | `7181ebc555c4484c477d74824a6109aa96c5a7f87a557cd266e50ebd4733e45f` |
| `stage_kev-4b.json`, `stage_qwen3.5-4b-base.json` (unchanged) | `53feff7b…`, `50a06257…` |
| prior / new charge file (unchanged) | `9a1949a156a23a735a6aae45888c99abc1935b17c069526d7dd6d227b4bf595c` / `fa49096f90319db735d775e0bdb1be3baf6cbd882fa31583c3ae1049c18f0877` |
| `kev-4b` / `qwen3.5-4b-base` `p4_run.log` (new in commit) | `b0e8647eb2d135e90d6266b5418b13a2ddef75aeba83b91d043251fed3296671` / `d6ff3299a08daad11e69cc6a79ee18e3762477ea414463d3a9edd0b692ea623b` |
| `kev-4b` / `qwen3.5-4b-base` job record (unchanged) | `726c5abef04304cec4a17e86f08832536226a71a4df784570785826c26cc9a4c` / `d7ef295e39e64a2c6cbbf5c11834e33829cc37b1b87b2cf02ddb900da5e23756` |
| `kev-4b` / `qwen3.5-4b-base` out.tar (unchanged) | `d92ef63d1e6f2fc943e2be3e56764a0e723b49fdf3998c00e787f3ef5de0276c` / `df06cb2ac03186aa1e38bb2376612c74b1c0513e8e4803a41f90bcb4de57abb5` |

## Reviewer statement

I did not modify the deliverable branch (`compute-p4-4b-reprobe-20261127`) at `a801dc60`, did not force-push, and
did not push `main`. I did not write to `/ceph` or the live sealed trees; the sealed runs were read from a
read-only `/tmp` copy. The only change on `compute-p4-4b-reprobe-review-20261127` in this round is this re-check
file. The unit now accepts at tier E: the record's measured values, seals, charge, projection and phase-1 note
inputs are the ones verified in R1, and the record package verifies on a clean checkout.
