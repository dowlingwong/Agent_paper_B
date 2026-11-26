# C3 B.2 EVIDENCE audit — sweep 1 fresh-seed audit (authorized second attempt)

**Verdict: PASS.** The complete sweep-1 B.2 EVIDENCE audit ran once on deepthought, on CPU, at the
independently accepted paper-code commit `ab79b4ce0e427d09e5d5b718e98882c8fbcb6e74`, with a byte-identical `docs/` authority
overlay from published `main` `de3de54fd22dcdd86215be0924307e36a64ed08b`. Every eligible proposal has 10 successful, finite,
unchanged-file seed runs for both its candidate and its incumbent; `label_block.jsonl` and
`evaluation_block.jsonl` are written and were recomputed from the raw runs on consumption; the
`evidence_completion.json` record is schema `r1.c3_audit_completion/3` and binds every hash, the addendum,
the e1-replay environment basis and the worker-runtime limitation; the counts equal the plan.

- **Label:** EVIDENCE. This is the B.2 audit authorized by R1-B2-GO and the signed addendum; labels
  count only after an independent review and the author's separate label-table freeze.
- **Authority:** `docs/r1/authorizations/c3_b2_addendum_20261117.md` (sha256
  `e9deba6334014feae805cd468727fbeb44cc9aaf786d34f2ff180ee4c4d69709`), PLAN rows R1-B2-GO / R1-B2-ADDENDUM / R1-B2-ADDENDUM-FIX /
  R1-B2-PIN-FIX2, review `docs/r1/reviews/B2_PACKAGE_ORIGIN_REVIEW_20261118.md` (sha256
  `dd31b3d627a20caeb3cd620a1e32f4b10b45c37b31383090f4c412e81bc75bf3`, `Code-Commit: ab79b4ce0e427d09e5d5b718e98882c8fbcb6e74`, `Verdict: ACCEPTED`).
- **One launch, no retry, no resume.** The 18 Nov 2026 pre-worker STOP directory
  `/ceph/srv/dwong/paperb/b2-435513d2-20261118T012807Z.veDjse` is preserved with unchanged contents:
  every evidence file and the host table keep their 18 Nov mtimes and sizes, `paper/.git/index` was
  not rewritten, and nothing was deleted. The only observable difference is the `paper/.git/`
  directory mtime (00:18Z), a side effect of the operator read-only `git status` inspection.
- **Operator:** single operator session on deepthought, 2026-11-19T00:27:38Z – 2026-11-19T00:50:22Z.

## 0. Result at a glance

| Item | Observed |
|---|---|
| Eligible proposals / unique node configurations / planned seed runs | 1725 / 466 / 4660 |
| Seed runs recorded (all success, finite metric, `changed_files: false`) | 4660 (466 × 10) |
| Duplicates (never audited) / no-ops (rule-labelled, 0 here) | 3274 / 0 |
| Label block / evaluation block rows | 1725 / 1725 |
| Label seeds / evaluation seeds | 7001–7005 / 7006–7010, K = 10 |
| `evidence_completion.json` schema | `r1.c3_audit_completion/3` |
| Consumption re-verification (`verify_evidence_completion`) | **PASS** (blocks recomputed from raw runs) |
| Live gates (provenance, addendum, environment, plan, resources, output path) | all PASS |
| Workers / CPU / operator deadline | 16 / 40 CPUs / 10800 s |
| Co-tenancy immediately before launch | load 1-min 15.39 on 40 CPUs ⇒ ≈24.61 free (floor 10) |
| Wall time | 2026-11-19T00:27:38Z → 2026-11-19T00:50:22Z |
| Exit code | 0 |

## 1. Authorization, pins and checkout

The run follows the addendum procedure exactly: a **fresh** clone, detached checkout at the exact
reviewed commit, then the authority `docs/` bytes overlaid from the then-current published `main`
(`git checkout origin/main -- docs/`), because `main` had moved past the code pin. `PLAN.md` was not
changed on `main` during the audit (`main` tip at launch, at completion check and now:
`de3de54fd22dcdd86215be0924307e36a64ed08b` / `de3de54fd22dcdd86215be0924307e36a64ed08b`). Machine-readable pins: `pins.json`.

| Pin | Value |
|---|---|
| Paper code commit (detached HEAD) | `ab79b4ce0e427d09e5d5b718e98882c8fbcb6e74` |
| Published `main` at launch / at completion check | `de3de54fd22dcdd86215be0924307e36a64ed08b` / `de3de54fd22dcdd86215be0924307e36a64ed08b` |
| Independent review | `docs/r1/reviews/B2_PACKAGE_ORIGIN_REVIEW_20261118.md`, sha256 `dd31b3d627a20caeb3cd620a1e32f4b10b45c37b31383090f4c412e81bc75bf3` |
| Addendum | `docs/r1/authorizations/c3_b2_addendum_20261117.md`, sha256 `e9deba6334014feae805cd468727fbeb44cc9aaf786d34f2ff180ee4c4d69709` |
| Sweep-1 authorization | `docs/r1/authorizations/c3_sweep1_20261027.md`, sha256 `563374f6b0a8369cadc7739878725362a89ec28e3774bf1b69859cc0076797cd` |
| PLAN.md (published main) | sha256 `9e2093413c454d2bac8573de2f7a8a7562748a6117072b0c9b82f86c69405a86` |
| Sweep index / classification sidecar | `812468e26c0901a6cb5b3241f44a46fd4d1d2e498d172b76d63b1e91f6d835ab` / `bb6d891c499f0fc187726ed7c8c1e1bce107a029b9106ccb95115989c0c0f1dc` |
| Environment basis | R1-B2-GO B6 (a); published e1 replay at `52992b22b50e496935136b50c5b31a79a17d7f20` (review `E1_AMEND_RUN_REVIEW_20261117.md`, ACCEPTED; 16/16 at tolerance 0) |
| Harness | `/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/autoresearch_harness` HEAD `6adf3859de66c4814fcf376eed59880fbd8eeaf7`, tracked-clean, `uv.lock` `dd42d0187d16305913de75031a6fb69dcee00a08476f2f41278a8c307883d090` |
| Interpreter | Python `3.13.15 (main, Aug 14 2026, 15:34:59) [Clang 22.1.3 ]`; prefix `/ceph/dwong/r1_prepare_20261025/venv`; wrapper target `/ceph/dwong/r1_prepare_20261025/venv/bin/python`; package list `c09242ac13970394a660452fb1b92dde39edcf390022c40a19327e67e725315f`; newest dist-info `2026-10-26T22:09:12.359336+00:00` |
| Seeds | K = 10: label 7001–7005, evaluation 7006–7010 |

### 1.1 Host table (rebuilt fresh in the checkout)

`python -B -m r1.c3.dataset build-sweep --index results/r1/pilot/C3_sweep_index_20261028T033315Z.json
--out <attempt>/table --paper-root <checkout> --classification
results/r1/evidence/C3_sweep_classification_20261028.json` in the batch venv (same environment as
e1; `env.sh`/`PYTHONPATH` not sourced). The rebuild gave the frozen dry-run counts and hashes
exactly — 4,999 proposals, 466 node/configuration pairs, 1725 eligible, 3,274
duplicates, 0 no-ops — and passed the full source replay (`_verify_replay` rebuilds the table from
the sweep sources and compares it byte-for-byte):

| Table file | SHA-256 |
|---|---|
| build.json | `c14a68aec5ce8e408923930b63ba057503f14bd82b6e1f077879c3deb03a48ee` |
| configs.json | `b585b72758668a17c65b842c204e3c08253ee6c7af92c34c9a8bc8b4a53882df` |
| proposals.jsonl | `b713c42338c42cea6991ee8ac8e598183fc79c22aeef6a2e8539c7f971dd57c4` |

## 2. What was run

One launch only. The launcher is retained verbatim as `command.sh` (and `logs/run_audit.sh` in the
attempt directory); environment: batch `.venv` wrappers first on `PATH`,
`AR_HARNESS_ROOT=<batch>/autoresearch_harness`, `PYTHONDONTWRITEBYTECODE=1`, thread
`OMP/OPENBLAS/MKL_NUM_THREADS=1`, `CUDA_VISIBLE_DEVICES=""`, cwd = detached checkout; the batch
`env.sh` `PYTHONPATH` was deliberately not used (the provenance guard refuses it).

- **Output:** `/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/paper/results/r1/evidence/C3_audit_EVIDENCE_20261119T002306Z` (new, dedicated, under `results/r1/evidence/`).
- **Scratch:** `/tmp/r1_c3_audit_EVIDENCE_20261119T002306Z` (new, dedicated, local `/tmp` on verified local XFS; retained).
- **Workers:** 16 (authorized maximum; below the 40-CPU count); operator deadline
  10800 s (a timeout, not a protocol budget).
- **Scratch floor:** 17179869184 bytes required; 117761064960 bytes free at the
  checked launch. **Ceph:** ≥ 50 GiB floor passed; file-count reserve 2000 against
  478 estimated files and 1500000 − 433784 available.
- **Timing:** launch 2026-11-19T00:27:38Z; first seed journal 2026-11-19T00:29:29Z; last seed
  journal 2026-11-19T00:50:20Z; end 2026-11-19T00:50:22Z; exit code 0.

`evidence-run` creates the output directory only *after* every live gate has passed and the complete
plan with its full source replay has been checked; no partial output from a refused gate exists.

## 3. Live gates (all rerun by the code; none bypassed)

`evidence_run` order: `evidence_paper_provenance` → `b2_addendum` → `evidence_environment` →
`evidence_plan` (includes the published-classification guard and the full table source replay) →
`evidence_resources` → `evidence_output_path`, then the worker pool, then the post-run resource and
OpenML-cache re-checks, worker-record validation, block construction and the completion record.

| Gate | Result | Evidence |
|---|---|---|
| Paper provenance (detached HEAD = reviewed commit, ancestor of live published `main`, clean `r1/`, every loaded `r1` module byte-identical to the reviewed commit, published review accepts it) | **PASS** | `preflight_diagnosis.json`; the 18 Nov namespace-package STOP cause is fixed by the reviewed markers at this commit |
| B.2 addendum (published on live `main`; binds R1-B2-GO, this commit, the harness pin, K = 10) | **PASS** | same |
| Environment (e1-replay basis at `52992b22b50e496935136b50c5b31a79a17d7f20`, its current-environment checks re-run and equal, audit process in the recorded venv, harness tracked-clean at `6adf3859de66c4814fcf376eed59880fbd8eeaf7` with only the e1-recorded untracked OpenML caches + report file, cache tree digests equal to the e1 post-run record, imported harness modules byte-identical to pinned blobs, host = deepthought) | **PASS** | same; harness untracked count 17 |
| Classification + table plan (published index/sidecar/PLAN bytes equal to `main`, full table source replay equal, authorized EVIDENCE classification) | **PASS** | same; 1725 plan rows, counts 1725/3274/0 |
| Resources (workers ≤ 16 and < CPUs, new `/tmp` scratch on local XFS, scratch and Ceph floors, Ceph file-count reserve) | **PASS** | same; live resource samples in `resource_monitor.jsonl` |
| Output path (new dedicated directory, no symlink) | **PASS** | same |

The e1-recorded untracked harness files are the six OpenML data caches (tree digests equal to the e1
post-run record; unchanged before and after this run) plus
`paper/tables/artifact_completeness_report.txt`.

| OpenML cache | tree digest |
|---|---|
| openml_breast_w | `88f68825a3d93e4724b453346c6bc7c360e9e7594658a13b3761589ec359f487` |
| openml_climate | `73c5af1187710d75c717db532b74c287238d97c91d603351c2d865608c6b1f5d` |
| openml_credit_approval | `05cf63a22a3c4e3a391fac7eb78fe6a36ba6c5b9e9071bee1e05760aef97dcb3` |
| openml_ionosphere | `1079cb09c620388b48062855a8849337cd132fcd8cf1c31c4cece6a578cb0c4e` |
| openml_sonar | `ccca8605802002e6df8fef3080a6169c32a91ad8b4c401ad0cf173f16137020c` |
| openml_wdbc | `075915dc1fa10dc7a3f736a5d297765dd057e767becb38ee59b97bace868ebf3` |

### 3.1 Co-tenancy

Recorded in `cotenancy.log` and `pins.json`: 40 CPUs; 1-min load 15.39 immediately
before launch ⇒ ≈24.61 cores free, above the required 10, with the pre-existing
other-user jobs listed. Runtime 1-min load samples during the run: 29.72, 30.45, 32.46, 30.60, 30.60, 30.71, 28.64
(16 audit workers plus the pre-existing load); at completion: load
15.19 / ≈24.81 free. No other audit job was started.

## 4. Population, per-run validation and role blocks

- **Population:** 4999 proposals → 1725 eligible (audited; 466
  node/configuration pairs), 3274 duplicates (never audited), 0
  no-ops (rule-labelled by rule).
- **Raw runs:** 4660 rows in `runs.jsonl` = 466 configurations ×
  10 seeds. Every row: `success: true`, `changed_files: false`, finite metric, exact seed set
  7001–7010; every row carries a `worker_runtime` probe record (separate probe process, worker
  `PATH`/`python3`) equal to the approved venv.
- **Role blocks:** `label_block.jsonl` has 1725 rows
  (1725 audited proposals, 0 rule no-ops);
  `evaluation_block.jsonl` has 1725 rows, each carrying only seeds 7006–7010. Seeds
  7006–7010 appear only in the evaluation block.
- **Durable journals:** 466 per-configuration seed journals (one JSON line per
  seed, fsynced as it completed); manifest SHA-256 `85d9b6b25dec2167e51603e90602a6ecc737dbe3bae648a1a77d2faa7792288e`.

## 5. Completion record and independent recomputation

`evidence_completion.json` is schema `r1.c3_audit_completion/3` and binds: the addendum, the sweep-1
authorization, the index, the classification sidecar, the rebuilt table (`proposals.jsonl`,
`configs.json`, `build.json`), the plan, both role blocks, the raw runs, `environment.json` and
`resources.json`; it carries `environment_basis` (R1-B2-GO B6 (a)) and `worker_runtime_basis`
(R1-B2-GO B4 (a)), including the disclosed limitation that the per-run probe **does not attest the
task process itself**.

A fresh consumption pass, `verify_evidence_completion(table, label_block.jsonl, paper, index,
classification)`, re-ran the whole plan and recomputed both role blocks from `runs.jsonl` with the
unmodified code: **PASS**. Its result is retained in `verification_summary.json`
(attempt directory).

| Artifact | SHA-256 |
|---|---|
| `evidence_completion.json` | `e28bee5e0aaa1a5bd675cc74eb69ffd65559abda0b8019716c6dfca72f8e43b4` |
| `plan.jsonl` | `4fd46e1f6900bfbd9bc7b1def94a0221335526e38ce5a68a900fbcd0e19ddf3c` |
| `runs.jsonl` | `a7610f39be9453985123de49b5a953cfe091dcdc4c98e93ea56557b9d1593fc9` |
| `label_block.jsonl` | `cdae9c3f16d08d7db6309590384db9c390598947a58fea80f5c5c2e250cf9aca` |
| `evaluation_block.jsonl` | `297fed47324839ef6c2a981cd64a38a90df453981231104b7a754dada3347f67` |
| `environment.json` | `497255c7ff34a127f14ec68503a595134e2444bd446b300dd5dc47ab179a665d` |
| `resources.json` | `167587c37a823082d96616ee7feaf7252d427d6a615272adf22b4ed5af9e9c23` |
| `evidence_binding.json` | `9d8b88490d31e26260448b15a1168892eef30283b25b7ded96d6c4524e1b5070` |
| `seed_journals` manifest (466 files) | `85d9b6b25dec2167e51603e90602a6ecc737dbe3bae648a1a77d2faa7792288e` |

## 6. Environment basis and disclosures (B6 (a), B4 (a))

No environment freeze bound to the sweep-1 launch exists. The audit environment is established by
the published, independently reviewed e1 replay (`docs/r1/reports/e1_replay_20261117/`, 16/16 cases
at tolerance 0 under R1-E1-OPENML-AMEND) and by re-running that replay's current-environment checks
at audit start; the observed interpreter build, prefix, wrapper target, package list and newest
dist-info mtime equal the replay's record. This is a current-state observation, not a launch-bound
freeze; `environment.json` and `evidence_completion.json` say so and carry the replay's three
section-9 disclosures (amended dataset identity basis; batch `.venv` wrappers pointing to the shared
venv; bounded 16-evaluation replay scope, not proof for all 288 roots and silent on LLM seed
replay). The worker-runtime probe limitation (B4 (a)) is disclosed in both records.

## 7. STOP rules

None triggered: no guard failure; the host table equals the dry-run counts and hashes; every seed
run succeeded, was finite and left the files unchanged; the deadline was not reached; no resource
floor was reached; no interruption; no eligible proposal or seed was dropped; 7006–7010 were used
only in the evaluation block. No resume and no retry occurred.

## 8. Retained artifacts

- Ceph attempt directory (checkout at the pin with the `docs/` overlay, host table, preflight,
  logs, `START.json`, this report's assembled files and a full output copy):
  `/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z`.
- Audit output (authoritative, in the checkout): `/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/paper/results/r1/evidence/C3_audit_EVIDENCE_20261119T002306Z`; full output copy in the attempt
  directory under `output/`.
- Local scratch (retained): `/tmp/r1_c3_audit_EVIDENCE_20261119T002306Z`.
- Preserved 18 Nov pre-worker STOP directory (contents unchanged; only its `paper/.git/`
  directory mtime reflects the read-only inspection): `/ceph/srv/dwong/paperb/b2-435513d2-20261118T012807Z.veDjse`.
- Nothing was deleted; the paper repository outside the detached checkout and the `docs/` overlay
  was not edited.

## 9. Independent reviewer checklist

1. Verify `docs/r1/reviews/B2_PACKAGE_ORIGIN_REVIEW_20261118.md` on published `main` contains the
   standalone `Code-Commit: ab79b4ce0e427d09e5d5b718e98882c8fbcb6e74` and `Verdict: ACCEPTED` lines, and that the addendum on
   `main` binds R1-B2-GO, that commit, harness `6adf3859de66c4814fcf376eed59880fbd8eeaf7` and `K = 10`.
2. Verify the code commit is an ancestor of published `main` `de3de54fd22dcdd86215be0924307e36a64ed08b`; the checkout is
   detached at it; `r1/` is clean; the `docs/` overlay is byte-identical to `main`.
3. Rebuild the host table from the frozen index with the same command; confirm 4,999 proposals,
   `proposals.jsonl` `b713c42338c42cea6991ee8ac8e598183fc79c22aeef6a2e8539c7f971dd57c4` and `configs.json` `b585b72758668a17c65b842c204e3c08253ee6c7af92c34c9a8bc8b4a53882df`.
4. Re-run `verify_evidence_completion` at a checkout of `ab79b4ce0e427d09e5d5b718e98882c8fbcb6e74` and confirm `PASS`,
   the `r1.c3_audit_completion/3` completion record and that both role blocks equal its recomputation.
5. Check `runs.jsonl`: 4660 rows, 466 configurations × 10 exact seeds, all
   success/finite/`changed_files: false`, each with a worker-runtime record matching the e1-replayed
   environment; confirm `STOP.json` is absent.
6. Confirm the counts (1725/3274/0; 1725
   labels; 1725 evaluations), the environment basis at `52992b22b50e496935136b50c5b31a79a17d7f20` and the
   worker-runtime limitation disclosure.
7. Confirm the retained artifacts and hashes (`SHA256SUMS`, `OUTPUT_SHA256SUMS`, `pins.json`) and
   that the 18 Nov STOP directory is preserved with unchanged contents.
