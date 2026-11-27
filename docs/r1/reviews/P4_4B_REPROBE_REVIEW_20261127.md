# Tier-E review — Ada P.4 4B re-probe with activation checkpointing (`compute/20261127-24`)

Verdict: CHANGES REQUIRED

**Reviewer.** Fresh, independent tier-E reviewer (delegated subagent). I did not write the record, the spec, the
stage manifests, the sealed attempts, the charge files or the report under review. I read the deliverable and its
base read-only. I opened no label, evaluation or test partition, no sealed evidence data and no credential; the
only SSH was read-only on `deepthought` (`ls`, `cat`, `sha256sum`, and `rsync` of the two sealed probe runs to
`/tmp`). No job was launched, stopped, edited or retried; the deliverable branch was not modified; `main` was not
pushed. The only writes are this review file and scratch under `/tmp` and the session temporary directory.

**Target.** `compute-p4-4b-reprobe-20261127` @ `6a37b9638df01576a2680127048a353452548da4`, one commit on base
`origin/main` `e92f3c7389e06347a0ff78f5f68971024133c670` (the R1-P4-4B-CHECKPOINT merge). Task
`compute/20261127-24` on `origin/coord/coordinator`; PLAN rows R1-P4-4B-CHECKPOINT (author, 27 Nov: "签 P4-4B A"),
R1-P4-TESTPLAN-DECISIONS (P4-PROBE A, P4-PROBECAP A), R1-P4-PROBE-CHARGE. Review branch base
`9cd5863cc1e0855c045fc1090841832cc5b7614c`, the `origin/main` the task names; current `origin/main` has since
advanced to `ab32029e` with the screening re-issue STOP merge, which has no bearing on this record.

**Summary.** The technical result is sound and independently reproduced. Both 4B arms ran the 50-step synthetic
`sft-dev` probe on an empty RTX 6000 Ada card with gradient checkpointing, micro-batch 8 and effective batch 16;
the peaks, s/step, step counts, empty-card observations, GPU UUIDs, freeze, seals and charge all verify, and
`probe_records.json` is reproducible from the sealed tree with the reviewed `p4_lib.probe_records` (every measured
value equal; only absolute paths and the documented write-once charge-file bookkeeping differ between the first
build and a later rebuild). The
charge `3.10` follows from `2.1603 + 0.4474 + 0.4833 = 3.091`, rounded up. The blocking finding is a
record-package defect, not a measurement: the two `p4_run.log` files are absent from the committed attempt
directories although the record's own top-level `SHA256SUMS` lists them, so `sha256sum -c SHA256SUMS` fails
18/20. The fix is to force-add the two logs; no value changes and no re-run is needed.

## 1. The branch is docs-only over the base

```
$ git log --oneline e92f3c73..6a37b963
6a37b963 docs(r1): P.4 Ada 4B re-probe with checkpointing — both arms PASS (compute/20261127-24)
$ git diff --name-status e92f3c73..6a37b963
A  docs/r1/reports/trackp_p4_probe_ada_20261127b/P4_ADA_4B_REPROBE_20261127.md
A  docs/r1/reports/trackp_p4_probe_ada_20261127b/SHA256SUMS
A  docs/r1/reports/trackp_p4_probe_ada_20261127b/charge_files/trackp-p4-probe-20261125-a_wallclock.json
A  docs/r1/reports/trackp_p4_probe_ada_20261127b/charge_files/trackp-p4-probe-20261127-b_wallclock.json
A  docs/r1/reports/trackp_p4_probe_ada_20261127b/p4_probe_spec_ada_b.json
A  docs/r1/reports/trackp_p4_probe_ada_20261127b/probe_charges.json
A  docs/r1/reports/trackp_p4_probe_ada_20261127b/probe_records.json
A  docs/r1/reports/trackp_p4_probe_ada_20261127b/stage_kev-4b.json
A  docs/r1/reports/trackp_p4_probe_ada_20261127b/stage_qwen3.5-4b-base.json
A  docs/r1/reports/trackp_p4_probe_ada_20261127b/trackp-p4-probe-20261127-b/_wallclock.json
A  docs/r1/reports/trackp_p4_probe_ada_20261127b/wallclock_none.json
# plus 10 files: SEAL_RECEIPT.json, SHA256SUMS, direct_launch.json, job_record.json, out.tar
# under trackp-p4-probe-20261127-b/{kev-4b,qwen3.5-4b-base}/attempt-1/
```

21 files, all added under `docs/`; `git diff --stat e92f3c73..6a37b963` is 2,346 insertions, no modification and
no deletion. No code, test, assertion, spec template or existing document is touched in the diff (the record's
own copy of the spec is added under `docs/`; the committed template is not edited).

## 2. The filled spec equals the committed template outside the fills and the re-probe run id

I ran the reviewed code at the base commit, not a re-implementation:

```
$ python3 - <<'PY'
import sys; sys.path.insert(0, "r1/scripts/htcondor/trackp_p4")
import p4_lib as lib, p4_render_jdl as rj
spec = lib.load_spec("docs/.../p4_probe_spec_ada_b.json")
tmpl = lib.load_spec("r1/scripts/htcondor/trackp_p4/p4_probe_spec.json")
lib.validate_probe_spec(spec); lib.check_probe_template(spec, tmpl); rj.check_probe_binding(spec)
PY
validate_probe_spec OK: run_id trackp-p4-probe-20261127-b, host_class ada_rtx6000,
                        probe_arms ('kev-4b', 'qwen3.5-4b-base')
check_probe_template: PASS
check_probe_binding: {'paper_commit': 'e92f3c73...', 'origin_main': 'ab32029e...',
                      'host_class': 'ada_rtx6000',
                      'host_config_sha256': 'bb0c7251a5d47e04e82e33c738160be317bfbf59984b82a0d611b0798c4fa908'}
$ python3 r1/scripts/htcondor/trackp_p4/p4_lib.py validate --probe docs/.../p4_probe_spec_ada_b.json
{"ok": true, "strength": "probe", "run_id": "trackp-p4-probe-20261127-b", ...}   # rc 0
```

`diff -u p4_probe_spec.json p4_probe_spec_ada_b.json` differs only in: `paper.commit` `e92f3c73…`;
`image.versions_sha256` `aaa1a304…`; `host_class` `ada_rtx6000`; `hosts.ada_rtx6000.host_config.sha256`
`bb0c7251…`; `run_id` `trackp-p4-probe-20261127-b`; and a pure whitespace reformat of the already-present
`protocol.gradient_checkpointing` object (`{"kev-4b": true, "qwen3.5-4b-base": true}`, parsed-equal). The template's
`ada_4b_reprobe` block already equals the published constant, and the filled spec's block equals it exactly:

```
spec["ada_4b_reprobe"] = {"run_id": "trackp-p4-probe-20261127-b",
                          "prior_run_id": "trackp-p4-probe-20261125-a",
                          "prior_spec_sha256": "540bd979...a2",
                          "prior_paper_commit": "91cfd48a...05"} == p4_lib.ADA_REPROBE
```

The run id is the declared `trackp-p4-probe-20261127-b`, not the prior run and not the P.4 run id. The Ada host
config sha is the sha256 of `r1/scripts/configs/trackp_ada_v1.json` at `e92f3c73` (checked by
`check_probe_binding`); the H200 class's host-config sha stays a placeholder, as probe strength permits.

## 3. Stage manifests, inputs, and the first-arm seal

`sha256sum` of the two committed stage files equals the receipts' `stage_manifest_sha256` and the launcher records'
`stage.manifest_sha256`:

| Stage | file sha256 | receipt / launcher |
|---|---|---|
| `stage_kev-4b.json` | `53feff7bbef242228296a57deb7c18a36bee6a421748f7d21c6920d1f2c6fa3e` | match |
| `stage_qwen3.5-4b-base.json` | `50a06257ec985d1cd010d5b69882a9d2f3ddf4d35bf3900746cfdb2233932ac9` | match |

Both manifests pin the same inputs, and the job records' `table.table_sha256` agree:

```
proposals.jsonl  d0048567a4bedb8618bc174b0103ba07e71194de853c883d16699dab9afcd1d5
configs.json     b585b72758668a17c65b842c204e3c08253ee6c7af92c34c9a8bc8b4a53882df
build.json       7f56619c2cc5ef2145ace44350baac3bc7906433e279a284e9627a2452e1b643
```

`proposals.jsonl` matches `p4_lib.V3_PROPOSALS_SHA256` and the SFT config's `sweep1_v3` pin; `configs.json`
matches its pin, and `build.json` is recorded, not pinned. The sealed v2 receipt-table hash
(`arms_freeze.SWEEP1_SEALED_PROPOSALS_SHA256` = `b713c423…`, which the phase-1 label job binds under P4-F2 A) is
not the probe's table hash and is not needed here: the probe stages only the table files and reads no label block.

Both stages carry `first_probe_record.first_probe_record_sha256 =
3d9af7d21f89edd86b8fd4efdf25bc8e2bd00e211c20acfccd547dfbc3b9c943`. That is byte-for-byte the prior run's
`trackp-p4-probe-20261125-a/kev-0.8b/attempt-4/job_record.json` on `e92f3c73`
(`sha256sum` = `3d9af7d2…`, `stop: null`, `identity_verified: true` in its receipt); attempt-4 is the first
STOP-free `kev-0.8b` attempt (attempts 1–3 are sealed STOPs). `p4_lib.check_first_probe_record` also verifies the
attempt's `SHA256SUMS` and that the record is the prior run's, sealed and STOP-free; the stage construction passed
that gate.

The stage manifests were made against `origin/main = e92f3c73`; the jobs later cloned at
`origin_main = 9cd5863c` (the job records' `clone.origin_main`), with `paper.commit = e92f3c73` in both. That is
consistent: `e92f3c73` is an ancestor of `9cd5863c`, and the jobs clone the pinned commit.

## 4. Both sealed attempts verify, on the branch and against the live seal

`sha256sum -c SHA256SUMS` in each attempt directory:

```
kev-4b/attempt-1:            out.tar: OK   job_record.json: OK
qwen3.5-4b-base/attempt-1:   out.tar: OK   job_record.json: OK
```

The receipts are consistent with the records and launchers:

| Check | `kev-4b` | `qwen3.5-4b-base` |
|---|---|---|
| `job_record_sha256` = sha256(job_record) | `726c5abe…cc9a4c` ✓ | `d7ef295e…e23756` ✓ |
| `stop` / `stop_class` | `null` / `null` | `null` / `null` |
| `identity_verified` | `true` | `true` |
| `card_shared` | `false` | `false` |
| `other_processes_start/end.count` (receipt) | 0 / 0 | 0 / 0 |
| `card_processes_start/end.count` (record) | 0 / 0 | 0 / 0 |
| GPU UUID | `GPU-9be33fd1-8eeb-497d-772a-87362d6720be` (index 0) | `GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154` (index 2) |
| GPU name / capability / driver | RTX 6000 Ada / 8.9 / 545.23.08 | same |
| launcher `status` / `exit_code` | `finished` / 0 | `finished` / 0 |
| runtime | venv, Python 3.12.10, torch 2.6.0+cu124 | same |
| freeze `status` / pinned sha / sorted sha | identical / `50238e5a…` / `e607c1d8…` | same |
| image executed | `false` (`image: null` in the record) | `false` |
| `charged_gpu_hours` | `0.4474` | `0.4833` |

I independently recomputed the receipt identity and charge path with the reviewed code:

```
lib.direct_launch_matches(launch, spec, arm, "probe", rec)   # PASS both
lib.launch_runtime_verified(launch, rec, spec)               # True both
lib.direct_charge(launch, rec["gpu_hours"], probe_walltime)  # (0.4474, ...) / (0.4833, ...)
```

The charge is `max(launcher_wall_clock_s / 3600, job_record.gpu_hours)`:
`max(1610.582/3600, 0.4472) = 0.4474` and `max(1739.729/3600, 0.4831) = 0.4833`. The launcher's wall clock is the
lease span of one card, which is the direct-attempt charge rule (R1-HOST-FREE (5), P4-PROBECAP A).

I copied both live sealed runs from
`/ceph/srv/dwong/paperb/trackp_p4/trackp-p4-probe-{20261125-a,20261127-b}/` read-only and compared every file:
the branch's `job_record.json`, `out.tar`, `SEAL_RECEIPT.json`, `direct_launch.json` and `SHA256SUMS` are
byte-identical to the live sealed copies for both new attempts. The live copies also contain `p4_run.log`, whose
sha256 equals the receipts' `run_log_sha256` (`b0e8647e…` and `d6ff3299…`); **those two files are not in the
branch** (finding F1).

## 5. The runs themselves

I unpacked each sealed `out.tar` and read `stage_s/sft_report.json`, `wall.json` and the GPU-memory CSV:

| | `kev-4b` | `qwen3.5-4b-base` |
|---|---|---|
| micro-batch / effective batch | 8 / 16 | 8 / 16 |
| `gradient_checkpointing` (protocol and effective run) | `true` / `true` | `true` / `true` |
| `completed` / `early_stopped` | true / false | true / false |
| `stopped_at` / `total_steps` | 50 / 50 | 50 / 50 |
| `protocol_deviation` | `{"max_steps": 50}` | `{"max_steps": 50}` |
| peak device memory (recomputed from CSV) | 14,135 MiB (1,004 samples) | 16,959 MiB (999 samples) |
| headroom (1 − peak/total, total 49,140) | 0.7124 | 0.6549 |
| `wall.json` wall / 50 steps | 502.291 s / 10.0458 | 499.903 s / 9.9981 |
| report/manifest `paper.commit` | `e92f3c73…`, dirty false | same |
| report/manifest harness | `897d83c8…`, branch HEAD, dirty false | same |
| `label_status` in `sft_data.json` | synthetic (seeds 7001–7005; never 7006–7010) | same |

`p4_run.log` (live seal) ends with `rc=0`; the launcher's `exit_code` is 0. Both records' `steps` end with
`probe`, `stop: null`, and `steps` lists `identity, clone, env3_freeze, configs, staging, table, data, probe`.
The 50/50-step, peak and s/step claims in the report are exact.

The two 4B attempts are the first and only attempts in this run; `_submissions.jsonl` on the live run has exactly
two entries (`kev-4b` 11:48:59Z, `qwen3.5-4b-base` 11:49:05Z), each mapping 1:1 by `stage_manifest_sha256` to the
sealed stages. No retry, no re-stage, no change of micro-batch, seed, data or assertion.

## 6. The probe record, the T1 charge, and the projection

`probe_records.json` sha256 `62a92d716ce8a000e72c11930f3cd7cbbab976417eaef7fb3f88a5b2d9efcb81`.

I rebuilt it from a `/tmp` copy of the two live sealed runs with the reviewed code:

```
table = lib.probe_records(probe_spec, sha256(probe_spec), lib.load_spec(p4_spec),
                          [kev-0.8b/attempt-4, qwen3.5-0.8b-base/attempt-2,
                           kev-4b/attempt-1, qwen3.5-4b-base/attempt-1],
                          sealed_root, wallclock={"schema": "trackp_p4_condor_wallclock/1", "runs": {}},
                          t1_wallclock=None)
```

The rebuilt table equals the committed file after removing the absolute `path` keys and the documented
write-once charge-file bookkeeping that differs between the first build and a later rebuild
(`probe_charges.charge_files`, each run's `charge_files`, `charge_basis`, and `t1.source`/`wallclock_source`;
the committed file is the first build, before `probe-record` wrote the two `_wallclock.json` files). **No measured
value differs** — entries, hours, charges, projection, T1 and the printed lines all match.

The record uses the first sealed, verified, STOP-free attempt of each arm in submission order:

| Arm | Attempt used | Run | Peak | s/step | Charge |
|---|---|---|---|---|---|
| `kev-0.8b` | 4 | prior `trackp-p4-probe-20261125-a` | 25,939 MiB | 3.7188 | 0.1231 |
| `kev-4b` | 1 | this `trackp-p4-probe-20261127-b` | 14,135 MiB | 10.0458 | 0.4474 |
| `qwen3.5-0.8b-base` | 2 | prior | 27,271 MiB | 3.7055 | 0.4511 |
| `qwen3.5-4b-base` | 1 | this | 16,959 MiB | 9.9981 | 0.4833 |

The prior `kev-0.8b` attempts 1–3 and the prior 4B attempt-1 are sealed STOPs (the 4B OOM peaks are 48,385 and
48,399 MiB); they are charged but not used. `extra_stop_free_attempts` is `{}` and `card_shared_arms` is `[]`; all
four entries have `card_shared: false`, and `fit_and_timing_reliable: true`. The four `p4_estimate_hours` lines are
`2.52 / 6.79 / 2.51 / 6.75`, which recompute from the measured s/step and the §4.5 step count of 2,430
(3 lr × 3 seeds × 190 steps + 3 × 240 lc steps) with `ceil_hundredth`. The host-class line is
`p4_probe_host_class: ada_rtx6000`.

Charge arithmetic:

```
prior run (every sealed attempt, receipts, T1 null)        2.1603
this run (0.4474 + 0.4833)                                 0.9307
total                                                      3.091
ceil_hundredth(3.091) = p4_probe_gpu_hours                  3.10
T1 (job 760065, condor_history "760065 0 3 0.0")           0.0
```

T1's `condor_history` file (`df41e2df…`) and the T1 `versions.jdl`/`versions.sh`/`versions.submit` hashes match
the committed record's `t1` block; T1 is charged once, in this run's `_wallclock.json` (the prior run's charge
file has `t1: null`). The two charge-file lines and their sha256s are exactly
`trackp-p4-probe-20261125-a _wallclock.json 9a1949a1…` and
`trackp-p4-probe-20261127-b _wallclock.json fa49096f…`; the copies in `charge_files/` hash to the same values, and
the new run's `trackp-p4-probe-20261127-b/_wallclock.json` is byte-identical.

The prior run's `_wallclock.json` was legitimately written by this record: the prior run had none (its committed
report directory on `e92f3c73` has no `_wallclock.json` — only `wallclock_none.json` among the wall-clock inputs —
and the prior record was refused at the 4B OOM); the live file is the base `trackp_p4_probe_charges/1` with
`supplement: 0`, the eight prior attempts, `t1: null`, and host mtime 13:29 alongside this record's build.
`probe-record` writes a run's base charge file once; no supplement was added.

Projection (S12, from `p4_spec` with the measured hours and `layout.startup_s = 1800`):

```
per arm   kev-0.8b 3.02   kev-4b 7.29   qwen3.5-0.8b-base 3.01   qwen3.5-4b-base 7.25
total_gpu_hours 20.57;  + probe 3.10 = total_with_probe_gpu_hours 23.67;  slot_hours 29.855
within_cap: true against 40 GPU-h / 64 slot-h;  probe_over_2_gpu_h: true (a reporting flag, not a refusal)
```

## 7. The report's factual claims

- **OOM comparison.** The earlier 4B OOM peaks are in the prior run's sealed attempts:
  `kev-4b` 48,385 MiB and `qwen3.5-4b-base` 48,399 MiB, both `oom: true`, `stop_class: arm`, on cards with
  0 other processes. The report's 48,385 / 48,399 is exact.
- **Checkpointing on exactly the two 4B arms.** The spec's `protocol.gradient_checkpointing` is exactly
  `{"kev-4b": true, "qwen3.5-4b-base": true}`; `validate_probe_spec` refuses any other set. The 4B `sft_report`
  and effective run both say `true`; the carried 0.8B records say `"off (SFT path)"`. The report's statement is
  exact.
- **`harness_commit: none`.** The phase-1 note draft (`docs/r1/proposals/TRACKP_P4_PHASE1_NOTE_DRAFT_20261122.md`
  at `e92f3c73`, line 108) says `harness_commit: none (the SFT path does not import the harness)`. Both SFT
  manifests in the sealed `out.tar` record `git.harness.commit = 897d83c8efa364ec2fdd37288241cc42e01d7274`,
  clean, and the probe's synthetic `sft-data` import path needs a harness checkout. The finding stands and is
  correctly escalated to the note; it is not a defect of this probe record.
- **Ada estimates for all four arms / 3.10 GPU-h.** Both are in the record and its printed lines, verified above.
  The 0.8B estimate lines are the carried prior values; the 4B lines are new and recompute from this run.
- **Overclaim check.** The measured values are all inside the probe's scope. Two wording points are noted below
  (F4): "launch-verified peaks" (the peaks are sampler-measured) and "the 4B fit decision is resolved … so no H200
  route is needed" (the fit is measured; the route is a recommendation for the note's/author's class choice).

## 8. Reads and evidence status

The probe path is the reviewed synthetic one: `PROBE_TRANSFER_INPUTS` is
`p4_probe.sh, p4_lib.py, p4_probe_spec.json, proposals.jsonl, configs.json, build.json`; `table_inputs` reads only
those three table files; `data_argv` is called with `--labels synthetic`; the resulting `sft_data.json` has
`labels.kind: synthetic`, `label_seeds: [7001..7005]`, and `label_status` "… never the evaluation block
7006–7010". No `label_block.traindev.jsonl`, no receipt, no test/evaluation partition and no sealed evidence data
was read. The only sealed files read are the prior run's `kev-0.8b/attempt-4` probe `job_record.json`,
`SEAL_RECEIPT.json` and `SHA256SUMS` as the required first-arm gate (finding F3 on wording). No SFT evidence run
happened: the jobs are `mode: probe`, `label: ENGINEERING_ONLY`, 50 steps on synthetic labels, `nothing kept as an
arm`; the run's `_submissions.jsonl` has only the two probe stages. The branch is docs-only, so no test suite was
required or run; the record's own `validate --probe` rc 0 was reproduced.

## Findings

### F1 — MAJOR (blocking, record completeness): the two `p4_run.log` files are absent, so the record's `SHA256SUMS` does not verify

The record's top-level `SHA256SUMS` (`ebbe2a5c…b17c78`) lists 20 files, including
`./trackp-p4-probe-20261127-b/kev-4b/attempt-1/p4_run.log` and
`./trackp-p4-probe-20261127-b/qwen3.5-4b-base/attempt-1/p4_run.log`, but neither file is in the branch. Each
committed attempt directory has five files (`SEAL_RECEIPT.json`, `SHA256SUMS`, `direct_launch.json`,
`job_record.json`, `out.tar`), whereas the seal copies six (the `seal` function copies `p4_run.log` when present).

```
$ cd docs/r1/reports/trackp_p4_probe_ada_20261127b && sha256sum -c SHA256SUMS
... 18 lines OK, then:
sha256sum:  ./trackp-p4-probe-20261127-b/kev-4b/attempt-1/p4_run.log: No such file or directory
sha256sum:  ./trackp-p4-probe-20261127-b/qwen3.5-4b-base/attempt-1/p4_run.log: No such file or directory
# rc 1; 18/20 OK
```

The live sealed copies on `deepthought` do contain the logs, and their hashes equal the receipts'
`run_log_sha256` and the manifest's lines:

```
b0e8647eb2d135e90d6266b5418b13a2ddef75aeba83b91d043251fed3296671  kev-4b/attempt-1/p4_run.log
d6ff3299a08daad11e69cc6a79ee18e3762477ea414463d3a9edd0b692ea623b  qwen3.5-4b-base/attempt-1/p4_run.log
```

The cause is the repository `.gitignore` line 3 (`*.log`), which silently excluded the two files from the commit;
the prior probe record tracks its eight `p4_run.log` files in the commit despite the same rule. The per-attempt
`SHA256SUMS` covers only
`out.tar` and `job_record.json`, so it passes; the record-level manifest that the author wrote does not.
This does not change any measured value — the missing logs' content (start/end line, `rc=0`, peak, s/step) is also
evidenced by `job_record.json`, `out.tar` and the launcher's `exit_code: 0` — but a record whose own checksum
manifest fails cannot be accepted as the sealed evidence package for the note.

**Exact fix (no re-run, no value change):** on the deliverable branch, force-add the two files at the paths the
manifest already names, e.g.

```
git add -f docs/r1/reports/trackp_p4_probe_ada_20261127b/trackp-p4-probe-20261127-b/kev-4b/attempt-1/p4_run.log \
           docs/r1/reports/trackp_p4_probe_ada_20261127b/trackp-p4-probe-20261127-b/qwen3.5-4b-base/attempt-1/p4_run.log
```

then `cd docs/r1/reports/trackp_p4_probe_ada_20261127b && sha256sum -c SHA256SUMS` must print 20/20 `OK` and return
rc 0, and each attempt directory must contain six files. (Removing the two lines from `SHA256SUMS` would make the
manifest pass but would leave the seal incomplete; adding the logs is the correct fix and matches the prior
record.) A re-review can be limited to the two files and the manifest check.

### F2 — MINOR (non-blocking, audit-file bookkeeping): `probe_charges.json` is the first-build snapshot

`probe_charges.json` (`c75ecd29…`) has `charge_files: {}`, each run's `charge_files: []`, `t1.source: "input"` and
`charge_basis: "receipt (direct launcher record)"` for every attempt. That is the state at the moment
`probe-record` assembled the record, before it wrote the two `_wallclock.json` files; the totals are correct
(`2.1603`, `0.9307`, `3.091`, T1 `0.0`), and `probe_records.json` plus `charge_files/` carry the authoritative
charge-file listing and hashes. A reader who cites `probe_charges.json` alone as the charge evidence cannot see
which charge files were applied. This is a documentation gap, not a value error; no action is required for the
note if `probe_records.json`'s `p4_probe_charge_file:` lines are cited (as the report does).

### F3 — NIT (wording): "no … sealed read" is imprecise

The report's standing line says "no SFT evidence run, no label, evaluation, test or sealed read." Both stages
read the prior run's sealed `kev-0.8b/attempt-4` probe record (and its `SEAL_RECEIPT.json`/`SHA256SUMS`) as the
required first-arm gate (`check_first_probe_record`). That is a sealed engineering record, not sealed evidence
data, and the stage manifests disclose its hash. Suggest "no label, evaluation or test partition, and no sealed
evidence data; the only sealed files read are the prior probe's seal and record as the required first-arm gate."
No value or verdict change.

### F4 — NIT (wording): two phrases go slightly beyond what the probe measured

"the launch-verified peaks" — the peaks are measured by the launcher's external `nvidia-smi` sampler
(`out/probe/<arm>.gpu_mem.csv`), not verified at launch; "sampler-measured" is precise. "The 4B fit decision is
resolved on Ada … so no H200 route is needed for these two arms" — the fit is measured and the margin is wide, but
the note's host-class choice and any route decision remain the coordinator's/author's; phrase it as a
recommendation ("the probe supports Ada at micro-batch 8 for both 4B arms") rather than a resolution. Neither
changes a number.

## Hashes checked

| Object | sha256 |
|---|---|
| Deliverable tip `6a37b963…` base `e92f3c73…` | one commit, 21 docs files, 2,346 insertions; no non-docs change |
| `p4_probe_spec_ada_b.json` | `7181ebc555c4484c477d74824a6109aa96c5a7f87a557cd266e50ebd4733e45f` |
| committed template `p4_probe_spec.json` @ `e92f3c73` | `21a2ad9c34104c9a35b33891cd4ef030966aa9702301f096161f86e839e77022` |
| `stage_kev-4b.json` | `53feff7bbef242228296a57deb7c18a36bee6a421748f7d21c6920d1f2c6fa3e` |
| `stage_qwen3.5-4b-base.json` | `50a06257ec985d1cd010d5b69882a9d2f3ddf4d35bf3900746cfdb2233932ac9` |
| prior `kev-0.8b` first-arm seal (attempt-4 job record) | `3d9af7d21f89edd86b8fd4efdf25bc8e2bd00e211c20acfccd547dfbc3b9c943` |
| `P4_ADA_4B_REPROBE_20261127.md` | `2c54c9cfb45974d596c4c856b409fc8f9c727c0c55936a495a1ff5510d2fc196` |
| record `SHA256SUMS` | `ebbe2a5c3d7cf04ed1b52dcf8b964c054b29581a9d9fe69b07789c2dd3b17c78` |
| `probe_records.json` | `62a92d716ce8a000e72c11930f3cd7cbbab976417eaef7fb3f88a5b2d9efcb81` |
| `probe_charges.json` | `c75ecd29f4464c5608331ff4092ba6209837a66faa2d44bfefd539e7a8bc4f13` |
| prior charge file `_wallclock.json` | `9a1949a156a23a735a6aae45888c99abc1935b17c069526d7dd6d227b4bf595c` |
| new charge file `_wallclock.json` (and branch copy) | `fa49096f90319db735d775e0bdb1be3baf6cbd882fa31583c3ae1049c18f0877` |
| `kev-4b` job record | `726c5abef04304cec4a17e86f08832536226a71a4df784570785826c26cc9a4c` |
| `kev-4b` out.tar | `d92ef63d1e6f2fc943e2be3e56764a0e723b49fdf3998c00e787f3ef5de0276c` |
| `kev-4b` `SEAL_RECEIPT.json` | `f017602a5c3298a4d571c67f11b124f4feebddf2f98f082e41d67fed85e4569a` |
| `kev-4b` `direct_launch.json` | `3b1d8442b483f71602d43277ed77576839c54c83d2dfc686dd4b9b0b1d067a0e` |
| `qwen3.5-4b-base` job record | `d7ef295e39e64a2c6cbbf5c11834e33829cc37b1b87b2cf02ddb900da5e23756` |
| `qwen3.5-4b-base` out.tar | `df06cb2ac03186aa1e38bb2376612c74b1c0513e8e4803a41f90bcb4de57abb5` |
| `qwen3.5-4b-base` `SEAL_RECEIPT.json` | `a4bfef5948814900a1a8f001dc74f0306d86c9b6529931ffbe7373b47914ed7d` |
| `qwen3.5-4b-base` `direct_launch.json` | `7993e66579e41dff8d5b573932446d09b7381f837b50e7e9525159fb41332248` |
| `kev-4b` `p4_run.log` (live seal; absent from branch) | `b0e8647eb2d135e90d6266b5418b13a2ddef75aeba83b91d043251fed3296671` |
| `qwen3.5-4b-base` `p4_run.log` (live seal; absent from branch) | `d6ff3299a08daad11e69cc6a79ee18e3762477ea414463d3a9edd0b692ea623b` |
| prior spec | `540bd9798017260ca391612351706189712221c269482a7d47385695160a50a2` |
| prior `paper.commit` | `91cfd48a67f8d62d4e20826976cbdbdbcfcaf505` |
| T1 `condor_history.txt` | `df41e2df4d598cfcb561b6f4b718c2faba3701a8a58fac15ff6957e1cbf2a3a9` |
| Ada host config `trackp_ada_v1.json` @ `e92f3c73` | `bb0c7251a5d47e04e82e33c738160be317bfbf59984b82a0d611b0798c4fa908` |
| image VERSIONS pin | `aaa1a304c2230466f603e63c96d7259d631f0668fa2d8b6486772fef22f0117a` |
| `p4_lib.py` @ `e92f3c73` | `0e1b9770556553266a2df77a95eb2ffea49adca9702970e1195bf8a3660c31d7` |
| `p4_probe.sh` @ `e92f3c73` | `96b591887c7b2e75f749e62dffe284c4dead77ad62836f9695f727b4375a86a4` |
| `p4_direct.py` @ `e92f3c73` | `f997e7bc02ab8939ab461a4c8b2ef80dd4c81bdd7508f50d63870f4271ba371d` |

## What I did not verify

- I did not re-run the training or launch any job; the probes are read-only reviewed at their sealed outputs. A
  fresh run would be a new attempt, not a review action.
- I did not ssh Ada (`ucrtasl`); the live sealed copies on `deepthought`/`ceph` and the branch copies were
  compared, and the launcher/record GPU facts were checked against the sealed captures.
- I did not re-read the model weights or the table contents beyond the pinned hashes; the staged bytes and hashes
  are the record's evidence.
- I did not run the full `r1/tests` suite: the branch is docs-only and changes no code. The record's
  `validate --probe` rc 0 was reproduced with the base code.
- I did not verify the phase-1 note signature or the note's other fields; this review covers the probe record
  and the claims it contributes to the note.

## Reviewer statement

I did not modify the deliverable branch (`compute-p4-4b-reprobe-20261127`), did not push `main`, and did not
launch, stop or retry any job. I did not write to `/ceph` or the live sealed trees; the two sealed runs were
copied read-only to `/tmp` for the rebuild. The only change on
`compute-p4-4b-reprobe-review-20261127` is this review file. The blocking item is F1; when the two logs are
force-added and `sha256sum -c SHA256SUMS` passes 20/20, the record's measured values and the phase-1 note inputs
are the ones verified above.
