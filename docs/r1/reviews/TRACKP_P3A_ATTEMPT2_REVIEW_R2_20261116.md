# Independent review — Track P P.3a attempt-2 revision 2 (Unit A preparation) and corrected TASL-7 readiness report (16 November 2026)

**Reviewer:** fresh independent reviewer (round 2; no part in drafting revision 2, the readiness corrections or
the code units). **Read-only.**

No run, no process signalled, no git write, no commit/push, nothing deleted. TASL-7 was inspected over
`ssh tasl7` (user `dowling`) between 2026-11-16T10:02:51Z and 10:12Z; the main worktree was not touched.
TASL-2 and Ada were not accessed, so readiness report §7 (TASL-2) and §8 (Ada) are **not independently
verified here** (they are not Track P inputs). *Method note:* one transient scratch file
(`/tmp/_freeze_r2.txt`, plus a stderr capture) was created on TASL-7 to diff `uv pip freeze` and deleted in the
same command; it is the only host write in this review. No experiment/repo/lock path on TASL-7 was written, no
GPU command was run and no `flock` was taken. Attempt-1 artifacts were read only: `journal.jsonl` still ends at
the 2026-10-29 STOP with mtime 2026-10-28 18:25:17 -0700 and the global lease log still ends at
2026-10-29T01:25:16Z.

**Canonical bytes reviewed.**
- Branch `origin/ops-tasl-20261116` @ **`379a633c0ae340461851d3b083ac1b70a627b704`** (merge of the authority at
  `04ce814c`); worktree `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/ops-tasl-20261116`
  (clean apart from the two uncommitted review files).
- Plan: `docs/r1/proposals/TRACKP_P3A_ATTEMPT2_20261116.md`, revision 2, sha256
  `8fcb37cc2066c688144d8eed7b5c7bf909f4eabbe73a414e09d3b4801571a703`, 131 lines.
- Readiness report: `docs/r1/reports/TRACKP_TASL7_READINESS_20261116.md`, sha256
  `edd5f68fece0a4d6a1910ae534b4d10d3f0325b027bd62c357a928c7f5dc9cec`, 146 lines.
- Round-1 review (read first, not accepted): `docs/r1/reviews/TRACKP_P3A_ATTEMPT2_REVIEW_20261116.md`, sha256
  `5f579cdcce96465184ee7678eb184416e78c42df824bbbf1f3de5ff7a20351ec`, uncommitted, 361 lines.
- Authority `author-decisions-20261116` @ `4da73306b8e10455fb124cf13d367e49b37247fe` and the later
  `04ce814c4e0a4fd0366cdf79086faabea24d368c` (T4 row; not Track P). `docs/r1/PLAN.md` sha256
  `b858121280bfbb424242494b41db93ce5dfe276cbc721003e0f0deffec4180b8` at HEAD (was `993cc0a3…` at
  `eb65ac4f`, round 1; the difference is the T4 row, §6 below).
- Authorizations `docs/r1/authorizations/trackp_p3a_20261027.md` (`414e7144…`) and
  `trackp_p3a_amend_20261104.md` (`cd867e95…`); OOM diagnosis
  `docs/r1/reviews/TRACKP_P3A_OOM_DIAGNOSIS_20261031.md` (`a7ef3633…`, **UNCLEAR — STOP**); M13
  `docs/r1/reports/MAC_M13_TEMPLATE_INVENTORY_20261105.md` (`b8f4c8ef…`); spec
  `docs/r1/TRACK_P_POST_TRAINING.md` (`2fa74132…`, §5.6 A3/A6 and the 4 Nov order); Track P runbook
  `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md` (`49dcef69…`) Phase 5; migration review
  `docs/r1/reviews/TRACKP_TASL7_MIGRATION_REVIEW_20261026.md` (`0f715089…`, final **accepted**); marker helper
  `docs/r1/proposals/trackp-evidence.sh` (`f457a04e…`).
- Pin code read at `b9ad6f8fe2e771732100f704accd7f2ce7cf20f0` — the object **is present in the local repo**
  now (`git cat-file -t` = commit; `origin/trackp-20261026` exists), which is material to M13 feasibility.

**Verdict summary.** **Unit A (preparation, no GPU) is accepted as a unit for review/execution now.** Round-1
BLOCKING-1 and MAJOR-1…7 are resolved at the level of Unit A's scope and requirements; **no BLOCKING and no
MAJOR remains in Unit A's scope**. The residual items are MINOR (plan P-M1…P-M10, readiness R-M1…R-M4) and must
be applied to the Unit A record / plan text during Unit A execution and before Unit B. The readiness report's
substantive TASL-7 facts and attempt-1 numbers are independently re-verified and correct, the §1 tmux
correction is verified, and four minor editorial corrections remain. **Unit B is not authorized by this
acceptance** — see §5. Final line at the end.

---

## 1. Evidence verified read-only (16 Nov 2026)

### 1.1 Live TASL-7 facts — readiness §1, §2, §5 re-verified

| Claim (readiness report) | Verified value (10:02–10:12Z) |
|---|---|
| Host `TASL-7`, user `dowling` | `hostname`=TASL-7, `whoami`=dowling; 5 users logged in |
| RTX 4090 24,564 MiB, 236 MiB used, 0 %, driver 580.178.04 | `nvidia-smi`: 24564 MiB total, 236 MiB used, 0 %, driver 580.178.04, UUID `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1` |
| no GPU compute app | `nvidia-smi --query-compute-apps` empty |
| Disk 1.9 T, 524 G free, 71 % | `/dev/nvme0n1p2 1.9T 1.3T 524G 71% /` |
| `~/r1_locks/gpu0.lock` FREE | inode 56251186, size 0, mtime 2026-10-26 15:50:48 -0700; **no `/proc/locks` entry** |
| no `*.active` marker | none under `~/r1_locks`; `trackp_evidence.log` absent (helper never run on TASL-7) |
| marker helper installed and matching | `~/r1_locks/bin/trackp-evidence` sha256 `f457a04ef1bbaba1750d9c04aa9211d51df1692ac36139bb720318f2d2533cec`, mode 755, 3,949 B, mtime 2026-11-04 08:55:15 -0800 = committed `docs/r1/proposals/trackp-evidence.sh` |
| Paper `b9ad6f8f` branch `trackp-20261026`, clean | `git rev-parse` = `b9ad6f8fe2e771732100f704accd7f2ce7cf20f0`, branch `trackp-20261026`, status empty |
| Harness `897d83c8…`, clean | `897d83c8efa364ec2fdd37288241cc42e01d7274`, status empty |
| 8 model repos | 8 dirs in `~/r1_trackp/models/` (2 Kev, 2 Qwen3.5, 3 StartLux, 1 Laya) |
| Venv Python 3.12.15, torch 2.6.0+cu124; freeze matches the 121-line pin | Python 3.12.15, torch 2.6.0+cu124; `uv pip freeze` = 121 lines, `diff` vs `docs/r1/reports/tasl7_phase2_20261026/pip_freeze_trackp-gpu_tasl7.txt` **empty**, 3 `@ git+` lines (`kev@2074cc44…`, `laya@a478221b…`, `startlux-decide@a99977d9…`) |
| tmux not empty host-wide; other sessions untouched | default socket `/tmp/tmux-1011/default`: "no server running"; user `tianyu` pid 934891 `tmux new-session -t paper`, 28 d 12 h, panes `pts/0`, `pts/2`, `pts/3` (child shells 934892/1253939/2201249); `dowling` pid 1570627, socket `~/r1_b1_engineering/b1_handover_6835_20261108_a/tmux.sock`, session `b1_6835_20261108_a`, idle bash, socket mtime Nov 7 16:59. No Track P/Track S/experiment process |
| no unplanned reboot since attempt 1 | boot id `2c9bb104-cc3c-4c60-be67-c1c8f0287fe4` = attempt-1 `campaign_start.boot_id`; uptime 45 d 13:55 |
| no attempt-2 root yet | no `~/r1_trackp/runs/p3a_attempt2_*` |
| no GPU lease activity since attempt 1 | `runs/gpu_lease_log.jsonl` 111 lines, last event `end` 2026-10-29T01:25:16Z (`trackp probes qwen3.5-4b-base`), file mtime 2026-10-28 18:25:16 -0700 |

### 1.2 Attempt-1 preserved state — plan §0 and readiness §4 re-verified

`/home/dowling/r1_trackp/runs/p3a_operator_20261027` (12 GB):

| Claim | Verified value |
|---|---|
| journal 81 lines, ends at the STOP | 81 lines; events = 1 `campaign_start`, 40 `unit_start`, 39 `unit_complete`, 1 `STOP`; last line `{"error": "unit failed rc=1: …/EVIDENCE/qwen3.5-4b-base/probes; …", "event": "STOP", "gpu_seconds_total": 130745.3789889291, "unobserved_lease_upper_s": 0.0, "utc": "2026-10-29T01:25:17Z"}` |
| campaign pins | paper `b9ad6f8f` branch `trackp-20261026` clean; harness `897d83c8` clean; "freeze": "matches TASL-7 recorded freeze"; "model_registry": "all files reverified"; `gpu_limit_seconds` 162000 (=45 h) |
| E0 screen/select/final/hard/native completed, four bases | every base has `screen_lr1e-05`, `screen_lr3e-05`, `screen_lr0.0001`, `select`, `final`, `hard`, `native`, each with `report.json`+`manifest.json` |
| short Kev-0.8B DRYRUN completed | `DRYRUN/kev-0.8b/` has the same 7 GPU units + `select` + `probes`; the DRYRUN probes argv is `probes --base kev-0.8b --head-form linear12 --budget --n-probe 32 --load …/DRYRUN/kev-0.8b/final/saved --evidence DRYRUN --run-dir …/DRYRUN/kev-0.8b/probes` |
| probes complete, three bases | report shas `f04df4e113d34fc117b4a881b5bfd34da81f711194b24e87c3e2c060c43d6f27` (kev-0.8b), `fae7c9cbda0c7fbeb55e2993445d096c1a86f0aa487637b80d4e8b96edd5033e` (kev-4b), `73894af6ad537fc9186216c55a790b7eadc86d68609f3e03e9af13f1fc270647` (qwen3.5-0.8b-base) |
| 4b probes absent, OOM | `EVIDENCE/qwen3.5-4b-base/probes/` absent; `probes.stdout.log` ends `torch.OutOfMemoryError: … Tried to allocate 1.49 GiB. … 1.31 GiB is free. … this process has 21.94 GiB memory in use. Of the allocated memory 21.26 GiB is allocated by PyTorch …`; traceback frames `exam_run.py:293 in probes`, `exam_run.py:248 in _a3_rps`, `exam_run.py:45 in predict` |
| `gpu_seconds_total = 130745.3789889291` = 36.318161 h; 8.681839 h left | recomputed from `runs/gpu_lease_log.jsonl`: 35 lease pairs (34 completed GPU units + the failed 4b probes) sum to **130745.378988929093 s = 36.318161 h**; 45 − 36.318161 = **8.681839 h**; 60-h cap includes attempt 1; the failed unit's lease was 112.381628715 s; completed leases sum 130632.997360214 s |
| `final/saved` re-hashes to the manifest | `adapter/README.md d1502e5c…`, `adapter/adapter_config.json 3b31604a…`, `adapter/adapter_model.safetensors 0b39d3fa…`, `heads.safetensors aeea9ec1…` — all equal to `model_files_sha256` in `EVIDENCE/qwen3.5-4b-base/final/manifest.json`; the failed probes unit's argv loaded exactly this `final/saved` |
| probes manifests record no input hash and no template version | `model_files_sha256 = {}` in all three probes manifests; schema `trackp_run_manifest/v1`; evidence `EVIDENCE`; no `prompt_version`/`template` field |
| **no attempt-1 file records the template/prompt version** | searched all 288 `*.json` files under the attempt-1 root: **0** contain `prompt_version`, `trackp_prompt` or `template_version` (round-1's 12 GB search said the same) |
| old descriptive A3 rows are in the preserved reports | `kev-0.8b`: `A3_descriptive = {"pass": null, "ran": [0]}` (2k/8k caught as overflow); `qwen3.5-0.8b-base` actually ran both: `mean_abs_drps {"2000": 6.514800030572588e-06, "8000": 9.603897253782634e-06}` |
| config digest | attempt-1 manifests `config_sha256 = 64073ceaa2660b5b8d783146a406135146a01c2f07e9c0d84f5a17431986f00c`; the pinned `trackp_portal.json` file sha256 is `049bafede821e9a15b38cdfc96b9198f1d1cbdd63153dced25250e045e71c2f7` (`config_digest` is the sha of the sorted-key JSON, not the file) |
| attempt-1 launcher environment | `p3a_operator_20261027.sh` exports `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONUNBUFFERED=1` |

The three probe report shas, the four `final/saved` hashes, the 45-h arithmetic and the exact STOP line all
match both the plan and the readiness report. The plan's numbers are right; round-1's prose "35 completed unit
leases" is slightly inexact — it is **34 completed GPU units + 1 failed probes = 35 lease pairs** (the five
`select` units are CPU-only and take no lease).

### 1.3 Pin-code facts that underpin the round-1 findings (read at `b9ad6f8f`)

- `r1/c3/train/exam_run.py`: the budget branch `probes()` is lines 274–286; the **descriptive 2k/8k block is
  exactly `290–295`** (`long = E.a3_probe(tok, n=n, lengths=(0,) + E.A3_DESCRIPTIVE, …)`, `_a3_rps(…, f"descriptive_{L_}")`).
  The OOM traceback's `exam_run.py:293` is that block. Round-1's `274–280` citation was from a different HEAD and
  is now correctly replaced.
- `r1/scripts/trackp.py`: `cmd_probes` returns `"model_files": {}`; `main` calls `R.run_manifest(...)`, whose
  `trackp_run_manifest/v1` fields are `schema, created_utc, subcommand, evidence_label, seed, base,
  model_files_sha256, data_manifest_sha256, config_sha256, git, environment, host, gpu_lease, **(extra)**` — an
  extensible `extra` dict exists but `cmd_probes` sets no template field. `_require_authorization` only globs
  `docs/r1/authorizations/trackp_p3a_*.md`; `R.check_environment` checks torch and the configured code pins only.
  A bare `trackp.py probes` therefore has **no** journal, no 45-h budget guard, no boot-id/driver recheck, no
  e0/rule/config/registry re-verification, no freeze check, no marker and no per-unit input binding — the
  round-1 BLOCKING-1 premise is confirmed, not assumed.
- `r1/scripts/trackp_p3a_guarded.py` (the attempt-1 supervisor at the pin) does have `verify_pins` (paper
  branch/clean, harness commit/clean, `e0_v1` sha, `p3_rule_v2` sha, `uv pip freeze` vs the TASL-7 pin,
  `registry.reverify`), `verify_live_pins`, boot-id check, `GPUBudget` reading the lease log, `journal` and
  `emit`; the revision-2 runner requirement list mirrors these.
- `r1/c3/train/types.py:26` = `PROMPT_VERSION = "trackp_prompt/v1"`; `serialize.py:198–206` puts it in the
  `serialize_view` metadata only. Spec (`TRACK_P_POST_TRAINING.md` §"Order of the serialised parts" and §5.6)
  says "the template carries a version field" and A6 is "(proposed)"; `exam_run.py` has no A6 implementation.
  Verified: the spec's A3 row marks 2k/8k "descriptive only" and the amendment excludes them.
- M13's unblock is **now feasible locally**: the pinned commit object and `origin/trackp-20261026` are present
  in this repo, and the attempt-1 manifests (supplied by the operator per Unit A) record paper `b9ad6f8f` and
  `base.family` (e.g. `qwen_control`), so the order/version determination no longer depends on a missing object.
  M13's own "not available in this local checkout" sentence is out of date; that strengthens, not weakens, the
  revision.

---

## 2. Round-1 findings — explicit status

### BLOCKING-1 — no reviewed probes-only runner/preflight/journal/budget guard — **RESOLVED at plan level**

Revision 2 §1c item 2 ("Probes-only runner/preflight/journal/budget unit") requires a reviewed script derived
from `trackp_p3a_guarded.py` (not the bare command) with: `verify_live_pins` (paper/harness clean, e0/rule sha,
config, venv freeze, registry, hostname, boot id, driver, disk), lease + empty GPU-compute census + marker
begin/end + no other experiment process, a new root, `journal.jsonl` + `gpu_lease_log.jsonl` + per-unit
manifests (attempt-1 input `model_files_sha256` binding, template version, code pin, config/e0/rule hashes,
host/driver/boot, authorization note + amendment sha, argv), the 45-h budget guard seeded from
`130745.3789889291`, a DRYRUN-first that exercises the changed A3 path, and fail-closed STOPs. The false
"`journal.jsonl` from one bare command" claim is gone; §2 says "no bare `trackp.py probes` command is used".
**This is a code-unit deliverable (item 2 of "Two code units, each separately reviewed before Unit B"), not a
description without a deliverable** — so the Unit A scope is sufficient to produce it, provided the unit is
actually written, tested and reviewed before Unit B. Residuals (MINOR, P-M3/P-M6): the plan does not give the
runner a file path, a test list or a recorded reviewed commit sha (unlike the A3 delta), and it does not say how
the per-unit manifest gets its template-version and input-hash fields (see P-M3). Unit B must not run on the bare
command.

### MAJOR-1 — template order/version — **RESOLVED in substance, with two MINORs**

Revision 2 §1a makes the attempt-1 inventory + M13 determination the first Unit A deliverable: export every
per-run manifest + journal/lease log + the pinned rendering sources at `b9ad6f8f`, and a local reviewer (not the
operator) records (i) commit/model family, (ii) history-first vs proposal-first per family wrapper, (iii) a
concrete template-version recording mechanism for attempt 2 sourced from the pinned `PROMPT_VERSION`/wrapper
order, with results recorded under the attempt-1 version and "never re-labelled", and (iv) the A6 disposition.
This matches M13's unblock in form and is feasible (see §1.3). The plan does **not** falsely claim attempt 1
recorded a version — correct, because none did (0/288 JSON artifacts). Two MINOR gaps: the export list omits the
pinned external Kev encoder (`kev@2074cc44…`) that M13 explicitly requires ("exact Kev encoder version/framing")
(P-M1), and (iii) does not state the negative fact (attempt 1 recorded nothing) nor ask the P.3a report to
retro-tag the attempt-1 results by provenance, labelled as derived (P-M2). The dependency (M13/A6 before the run)
is present ("Unit A is complete only when this record exists; the run cannot start before it", §1a; §1d; §2).

### MAJOR-2 — DRYRUN unspecified and possibly not exercising changed code — **RESOLVED in substance, MINOR on exactness**

Revision 2 now requires a **short Kev-0.8B probes** DRYRUN under the reviewed code path (changed A3) in the new
root before the 4b probes, with cost recorded (§1c.2 bullet; §2 step 2). That exercises the only changed code
(A3 branch skipping `290–295`) rather than merely re-running the unchanged E0 code, and it is cheap (attempt-1
DRYRUN probes lease 33 s; the attempt-1 DRYRUN `final/saved` and `EVIDENCE/kev-0.8b/final/saved` both exist on
host). **Acceptable in substance.** Residual MINORs: the exact argv/model path/n-probe (`--n-probe 32`),
`--evidence DRYRUN` label and `DRYRUN/…` output directory are not pinned (P-M7); the plan should record the
interpretation of the 27 Oct note's "one model (kev-0.8b) end to end as a DRYRUN under the final code" — since
E0 code is unchanged and the attempt-1 end-to-end short DRYRUN is preserved, a changed-path probes DRYRUN
discharges the amendment, but the reading must be stated (or the full ~0.5 h short DRYRUN run); and the budget
projection still omits the DRYRUN and the 26 Oct phase-2/equivalence declaration (P-M7).

### MAJOR-3 — amendment not on the host pin; guard unenforceable — **RESOLVED, MINOR on enforcement**

§1b records the amendment bytes' sha256 (`cd867e95…`) from `main:…trackp_p3a_amend_20261104.md` in a Unit A
record, has the runner take `--authorization-amend-sha256 <sha>` and refuse unless it matches, and journals it;
the host checkout stays clean at `b9ad6f8f`, no merge, no file needed on the host. This is the correct fix for an
absent host dependency. Verified the amendment is absent from the host checkout exactly as stated (the host
`docs/r1/authorizations/` holds only `trackp_p3a_20261027.md`). Residual MINOR: "refuses unless it matches"
needs a pinned expected value (a constant inside the reviewed runner, or the Unit A record's sha read into the
gate), otherwise any argument would pass; and the A3-short flag should be refused without `--budget` (the
round-1 sub-point dropped from §1c.1) so the v1 A3 0/2k/8k path cannot silently run (P-M4).

### MAJOR-4 — must-not list contradicted the authorized re-run — **RESOLVED**

§0 now separates them: "**Completed attempt-1 units are not re-run** (E0/final/hard/native for all four bases;
probes for the other three bases). Only the **interrupted 4b probes unit** is re-run, in a **new root**", and §3
repeats it ("no re-run of completed attempt-1 units (only the interrupted 4b probes unit is re-run, in a new
root)"). This matches the preserved state verified in §1.2 and the amendment's "attempt 1 is preserved … the new
attempt writes to new output directories".

### MAJOR-5 — OOM authority chain incomplete — **RESOLVED**

The plan header now cites `reviews/TRACKP_P3A_OOM_DIAGNOSIS_20261031.md` with its verdict "**UNCLEAR — STOP**,
options 1–3", states that option 3 is "a **frozen-execution change**, not the environmental-only rerun", and the
authority list carries `R1-P3A-OOM-OPTION3` + the 4 Nov amendment. The diagnosis's carried preconditions are in
the runner: hash/verify the attempt-1 inputs, empty GPU census under the lease, projected budget (§1c.2), and §1e
"P.3a attempt-1 inputs read-only and hash-verified". This is the right chain: `R1-P3A-OOM` alone (environmental
only) would not authorize the run. The readiness report itself still does not cite the diagnosis (R-M4).

### MAJOR-6 — code-delta citation/base — **RESOLVED, MINOR on delivery**

§1c.1 now cites the delta as "on a new branch with parent **`b9ad6f8f`**, flag/tests-only diff in `r1/`", skipping
"the descriptive 2k/8k levels at `exam_run.py:290–295`", with the test list (flag-on = exactly the four specified
rows; flag-off byte-identical; 2k/8k never attempted with the flag) and the exclusions ("no removal of the pinned
non-finite STOPs, no W2-3/v3/v2/M13/order changes, no other file changes"); the reviewed commit sha is recorded.
Verified at the pin: `290–295` is the descriptive block, `274–280` is the A3 v2 block; `r1/tests/` holds the
Track P tests (e.g. `r1/tests/test_trackp_p3a_guarded.py`), so "flag/tests-only diff in `r1/`" is accurate.
Residual MINOR: delivery to TASL-7 is unstated — the host checkout must move to the **exact reviewed delta
commit** (push/fetch/checkout, clean, branch/HEAD recorded; still no merge of `main`), and the runner preflight's
"paper `b9ad6f8f` (**or** the reviewed A3-short commit on top)" should be tightened to require the delta commit
(not either), otherwise a run without the required code change would pass preflight (P-M5). §1b's "host checkout
stays clean at `b9ad6f8f`" should be scoped to the amendment-delivery step only.

### MAJOR-7 (readiness) — "no tmux server" claim false — **RESOLVED**

Readiness §1 now says "Tmux is not empty host-wide": the operator's default socket has no server, but `tianyu`
pid 934891 (three panes) and the preserved `dowling` `b1_6835_20261108_a` session on its own socket (pid
1570627) exist and "were not touched". Independently verified (§1.1), including the three panes `pts/0,2,3` and
the B1 socket. The plan §1e enumerates the same and says "recorded, never touched". Good.

### Round-1 MINORs

| Round-1 | Status |
|---|---|
| m2 readiness "5 minor findings fixed" | **Not fixed** (readiness line 51 unchanged; the migration review had four MINOR findings plus a new finding 5 in the re-check that blocked until fixed, then accepted) — R-M1 |
| m3 treatment of already-collected descriptive A3 rows | **Not fixed**: the plan does not state that the P.3a report omits `A3_descriptive` for all bases, records the omission under `R1-P3A-OOM-OPTION3`, and does not rewrite the three preserved reports — P-M8 |
| m4 cite `R1-C3-POOL`/`R1-C3-POOL-EXAM` | **Fixed** (plan header, §0) |
| m5 marker procedure details | **Partly**: begin/end required, but not the `p3a` phase string, the no-nested-`flock` rule, or end-on-STOP — P-M6 |
| m6 attempt-1 env vars | **Not fixed**: plan never states/records `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `PYTHONUNBUFFERED=1` — P-M9 |
| m7 new-root enforcement / UTC format | **Partly**: runner requirement "must not exist" + "fail-closed STOPs" imply the check; the UTC format and an explicit `test ! -e` are not given — P-M9 |
| m8 budget projection total / equivalence time | **Not fixed**: no total projection (DRYRUN + probes ≈ <0.1 h against 8.681839 h), no declaration that the 26 Oct phase-2/equivalence GPU time is outside the 45/60-h P.3a accounting — P-M7 |
| m9 "one GPU-producing command" / A1-A2 N/A | **Mostly fixed**: "one GPU-producing session"; "A1/A2 unchanged". The explicit `{"pass": null, "reason": "model does not pack"}` recording for non-packing bases is not stated — P-M8 |
| m10 W2-3 report locations | **Not fixed**: the `W2_3_CHECK` files are on the unmerged `w2-3-check-20261115` branch and the rebuild/repo copy on the unmerged `w2-3-rebuild-unit-20261115` @ `2989f383`, not on the canonical branch; readiness §6 lists them without distinguishing — R-M2 |
| m11 "probes load attempt-1 native outputs" | **Not fixed**: they load `EVIDENCE/<base>/final/saved` (fresh-head `final`), not the `native` unit — R-M3 |
| m12 amendment "present" | **Fixed** by the separate Amendment delivery row; the "Authorization notes … present" row should still distinguish "canonical repo" from "host checkout" — R-M4 |
| m13 TASL-2/Ada unverified | Still a limit; not P.3a inputs (readiness §7/§8) |

---

## 3. Remaining findings

### BLOCKING: none.

### MAJOR: none in Unit A's scope. (The items below are MINOR; they do not change the preparation scope and do
not by themselves prevent Unit A execution, but they must be applied to the plan/Unit A record during Unit A
execution and resolved before Unit B — several are also conditions on the two code units.)

### MINOR — plan (revision 2)

- **P-M1 (plan §1a, lines 31–45) — M13 export incomplete.** The export/inspection list is paper-repo only
  (`types.py`, `serialize.py`, `model.py`, `exam_run.py`, `trackp.py`, `trackp_p3a_guarded.py`). M13's unblock
  explicitly requires the reviewer to inspect the **exact Kev encoder version/framing**; the pinned encoder is the
  external `kev@2074cc4425…` git dependency (`docs/r1/reports/tasl7_phase2_20261026/pip_freeze_trackp-gpu_tasl7.txt:38`).
  Add the pinned Kev encoder source (and optionally `exam_synthetic.py`, which fixes the state/proposal split) to
  the export/inspection list, or record explicitly that it is not locally inspectable and disclose the limitation.
- **P-M2 (plan §1a(iii)) — retro-tag wording.** State the negative fact (attempt 1 recorded **no**
  prompt/template version: 0 of 288 JSON artifacts; the manifests have no field) and require the P.3a report to
  record the attempt-1 results' version **by provenance** (pinned commit + wrapper order), clearly labelled as
  derived, not as a run-time field. "Results are recorded with the attempt-1 version, never re-labelled" should
  not be read as forbidding that provenance tag.
- **P-M3 (plan §1c.2) — implementation route for the new manifest fields.** The per-unit manifest cannot get the
  `model_files_sha256` binding or the template version "for free": `cmd_probes` returns `"model_files": {}`, the
  schema has no template field, and `cmd_probes` sets nothing in `extra`. The A3 delta's "flag/tests-only … no
  other file changes" cannot carry it. Specify the route — post-process the trackp.py manifest and record the new
  hash, a sidecar (e.g. `runner_manifest.json`), or a reviewed one-line `trackp.py`/`extra` change — with a test
  and the reviewed commit sha recorded.
- **P-M4 (plan §1c.1) — flag safety.** Require `--a3-short-rows` to be refused unless `--budget` (otherwise the
  v1 A3 path 0/2k/8k at `exam_run.py:268–273` is reachable and no 2k/8k row may be attempted on any host), and
  add the corresponding test. This was a sub-point of round-1 MAJOR-3 and is no longer stated.
- **P-M5 (plan §1c.1/§1b) — delta delivery.** State how the reviewed delta commit reaches TASL-7 (push branch;
  `git fetch` + checkout the exact commit on TASL-7, clean; no merge of `main`), require the runner preflight to
  accept **only** that exact commit (not "`b9ad6f8f` or …"), record branch/HEAD in the journal, and scope §1b's
  "the host checkout stays clean at `b9ad6f8f`" to the amendment-delivery step.
- **P-M6 (plan §1c.2) — runner as a first-class code unit.** Give the runner the same treatment as the A3 delta:
  file path/name, test list (preflight refuses dirty/wrong pins, the 45-h projection refusal, journal/manifest
  fields present, empty census, marker, no retry), and the reviewed commit sha recorded. Marker specifics: phase
  string `p3a` (the helper `end` requires an exact match); run the job directly (`trackp.py` takes its own `flock`)
  — do **not** wrap it with `trackp-evidence run` (nested `flock` would deadlock/fail) — and end the marker after
  the last job **and on STOP**. The procedure text in
  `proposals/TRACKP_EVIDENCE_MARKER_20261030.md` is still proposed, so the plan must state the procedure it relies
  on (round-1 m5).
- **P-M7 (plan §2, §1c.2) — DRYRUN exactness, budget projection, cost.** Pin the DRYRUN: load
  `…/p3a_operator_20261027/DRYRUN/kev-0.8b/final/saved` (or `EVIDENCE/kev-0.8b/final/saved`), argv
  `probes --base kev-0.8b --head-form linear12 --budget --n-probe 32 --a3-short-rows --load … --evidence DRYRUN
  --run-dir <new-root>/DRYRUN/kev-0.8b/probes`, verify the new probes report has no `A3_descriptive` rows / the
  journal records the flag, and record ≈33 s lease (0.01 GPU-h; full attempt-1-style short DRYRUN ≈0.53 GPU-h).
  State the total projection (DRYRUN + probes ≈ <0.1 h against 8.681839 h left; full short DRYRUN still ≈0.6 h)
  and declare that the 26 Oct phase-2/equivalence GPU time is outside the 45/60-h P.3a accounting (round-1 m8);
  state the reading of the 27 Oct "one model end to end" DRYRUN condition (or run the full short DRYRUN); add the
  completed attempt-1 short DRYRUN to §0's attempt-1 facts.
- **P-M8 (plan §2/§1a) — preserved descriptive rows and A1/A2.** State that the P.3a report omits
  `A3_descriptive` for all bases, records the omission under `R1-P3A-OOM-OPTION3` (the amendment requires this
  sentence), and that the three preserved probe reports are not rewritten; and that A1/A2 are recorded as
  `{"pass": null, "reason": "model does not pack"}` for the non-packing bases (round-1 m3/m9).
- **P-M9 (plan §1c.2/§2) — exact checks and environment.** Give the expected `trackp_portal.json` check value(s)
  (attempt-1 manifests `config_sha256` `64073cea…`; pinned file sha256 `049bafed…`), the new-root UTC format (e.g.
  `20261116T1055Z`) and an explicit `test ! -e <new-root>` preflight, and the exact attempt-1 environment to be
  recorded (`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`,
  `PYTHONUNBUFFERED=1`) — unchanged from attempt 1 unless separately reviewed (round-1 m6/m7). Name the
  attempt-1 subset of the global lease log (111 lines include the 26 Oct phase-2/equivalence jobs; the 35
  attempt-1 leases are the ones within the attempt-1 window).
- **P-M10 (plan header and §1) — Unit A / code-unit boundary.** The header says Unit B "may start only after
  Unit A **and the code units** are accepted", while §1c places the two code units *under* §1 "Unit A". Clarify:
  either (a) Unit A = §1a/1b/1d/1e (this review reads it that way — preparation only) and §1c items are separate
  reviewed code units, or (b) they are part of Unit A execution but still each separately reviewed before Unit B.
  Either way Unit B is blocked; the edit avoids a future operator reading acceptance of Unit A as acceptance of
  the code.

### MINOR — readiness report (corrections still missing)

- **R-M1 (readiness §3, line 51).** Replace "accepted the migration (5 minor findings fixed)" with the accurate
  history: four MINOR findings, then a new finding 5 (a test-block regression) in the re-check that kept the
  migration **not accepted** until fixed; accepted after the fix (round-1 m2).
- **R-M2 (readiness §6, lines 94–100).** The `W2_3_CHECK_20261115.md` / `w2_3_check_20261115/…` artifacts are on
  the unmerged branch `w2-3-check-20261115`, and `W2_3_REBUILD_RUN_20261115.md` / the repo evidence copy on the
  unmerged `w2-3-rebuild-unit-20261115` @ `2989f383`; none is on the canonical branch. Label each as
  branch-only (round-1 m10).
- **R-M3 (readiness §6, lines 102–103).** "probes load attempt-1 native outputs" is imprecise: the probes load
  `EVIDENCE/<base>/final/saved` (the fresh-head `final` unit), not the `native` unit (round-1 m11).
- **R-M4 (readiness §4/§5/§9).** Cite the OOM diagnosis `TRACKP_P3A_OOM_DIAGNOSIS_20261031.md` (**UNCLEAR —
  STOP**) and option 3 as a frozen-execution change in §4/§5 (the plan header does this; the readiness report does
  not); qualify §5's "Authorization notes … 27 Oct note + 4 Nov amendment present" as "present in the canonical
  repo; the 4 Nov amendment is absent from the host checkout — see Amendment delivery"; and update §9's proposed
  unit to the Unit A/Unit B split with the probes-only runner review added to the gate list.

---

## 4. Attempt-1 facts (review question 4) — explicit

- Preserved root `/home/dowling/r1_trackp/runs/p3a_operator_20261027`, 12 GB, journal 81 lines; the last line is
  the STOP at `2026-10-29T01:25:17Z`; journal mtime still 2026-10-28 18:25:17 -0700 (unmodified).
- Three probe reports: `f04df4e1…` (kev-0.8b), `fae7c9cb…` (kev-4b), `73894af6…` (qwen3.5-0.8b-base).
- The 4b probes unit is the interrupted one: directory absent, `probes.stdout.log` ends in the CUDA OOM
  (`1.49 GiB` request, `21.94 GiB` in use, `1.31 GiB` free) at `exam_run.py:293` in the descriptive 2k/8k loop
  (`290–295`); no report/manifest was written, so the failed unit produced a lease (112.381629 s) but no output
  record. The attempt-1 manifests record `model_files_sha256` for the E0 units but `{}` for the probes.
- Budget: `gpu_seconds_total = 130745.3789889291 s` = **36.318161 h** (exact, recomputed: 35 lease pairs =
  34 completed GPU units + failed probes, sum 130745.378988929093 s); **8.681839 h** remain of the 45-h lease
  STOP; the 60-h cap includes attempt 1. No GPU lease event after 2026-10-29T01:25:16Z, and the lease is free
  now.
- Completed vs interrupted: 34 completed GPU units (including the 4-base E0/final/hard/native and the three
  probes) + 5 CPU-only `select` units completed; only the 4b probes unit is interrupted and is the one the plan
  re-runs whole in a new root. The plan states this correctly.
- Four-base pool: `R1-C3-POOL` (Kev candidates, Qwen controls) and `R1-C3-POOL-EXAM` ("P.3a runs on the four
  remaining bases only … DRYRUN-first order (kev-0.8b) holds") — correctly cited.
- A6: unimplemented (`exam_run.py` has no A6 code), only "(proposed)" in spec §5.6; `R1-P3A-OOM-OPTION3` (G2)
  expects it to quantify the difference. The plan's disposition request is correct.
- Template version: no attempt-1 artifact records one (0/288 JSON files); the recording field and the order are
  exactly what Unit A/M13 must establish.

---

## 5. Unit A acceptance — decision and conditions

**Answer: yes.** Unit A (preparation, no GPU) is acceptable as a unit for review now, and its execution may
proceed under the MINOR corrections above. It does not merely describe the round-1 BLOCKING-1 runner: the runner
is a code-unit deliverable (§1c item 2, "each separately reviewed before Unit B") with an explicit requirement
list, and the preparation deliverables (attempt-1 inventory + M13 record, amendment sha record, A6 disposition
request, preflight record) are concrete and feasible — M13's unblock is now checkable because the pin object is
present locally and the attempt-1 manifests record the launch commit. The Unit A conditions that matter are
recorded in the plan (§1a "Unit A is complete only when this record exists; the run cannot start before it", §1b,
§1d "Unit B cannot start until this disposition exists", §2).

**Unit B remains blocked until ALL of the following hold (explicit conditions):**

1. **Unit A accepted and executed**: §1a record exists (attempt-1 order/version per wrapper for the four bases,
   template-version recording mechanism, attempt-1 no-version-recorded fact, Kev encoder or recorded limitation),
   §1b amendment sha record exists, §1d A6 disposition request filed (and answered before Unit B), §1e preflight
   record exists. **Verified at review time:** M13's inputs are now locally checkable.
2. **A3-short code delta reviewed and accepted**: parent `b9ad6f8f`, exact-pin-lines `290–295`, flag/tests-only
   `r1/` diff, flag refused without `--budget`, flag-off byte-identical, flag-on exactly the four specified rows,
   no 2k/8k attempt, no removal of the pinned non-finite STOPs, no W2-3/v3/v2/M13/order change; reviewed commit
   sha recorded and delivered to TASL-7 as the exact clean checkout commit (P-M4/P-M5).
3. **Probes-only runner reviewed and accepted**: all §1c.2 requirements, with its own tests and recorded commit
   sha; per-unit manifest template-version and attempt-1 input-hash mechanism implemented and tested (P-M3/P-M6);
   no bare `trackp.py probes` invocation.
4. **M13 order/version record produced and inspected** (local reviewer, not the operator): attempt-1 order per
   family wrapper, the shared `trackp_prompt/v1` version string, the attempt-1 results retro-tagged by
   provenance (not claimed as recorded at run time), and the attempt-2 recording mechanism.
5. **A6 disposition recorded**: either a separately reviewed A6 unit authorized, or A6 deferred with the
   long-context-row omission and its limitation disclosed in the P.3a report. A P.3a re-run under the 4 Nov order
   is **not** authorized by this plan and would need its own unit (add to P-M2/§1a(iv)).
6. **Marker / lease / preflight at the run**: lease free (verified now: inode 56251186, no `/proc/locks` entry),
   empty GPU-compute census, no `*.active`, foreign tmux sessions enumerated and recorded (verified now), marker
   `begin p3a` before the run and `end p3a` after the last job and on STOP, direct execution (no nested `flock`),
   boot id `2c9bb104…`/driver 580.178.04/disk/pins re-checked and recorded, exact environment recorded, new root
   absent, budget projection (45-h STOP remaining 8.681839 h; 60-h cap incl. attempt 1) computed before each GPU
   unit, DRYRUN-first result recorded.
   Additionally: the amendment sha gate (`cd867e95…`) enforced against a pinned expected value, and attempt 1
   left untouched/read-only throughout.

**This acceptance does not authorize Unit B, any GPU job, any host write, any merge/push, any code-unit
acceptance, or any P.3b/P.4/P.5/P.6 work.** The readiness report is accepted with the four minor corrections above;
the plan's Unit A may proceed subject to the MINOR corrections; Unit B requires the six conditions.

---

## 6. Authority row `04ce814c` — no Track P change

`04ce814c4e0a4fd0366cdf79086faabea24d368c` ("author signs R1-T4-PROOF-CHECK …") changes **only**
`docs/r1/PLAN.md` (+6 lines) and adds the T4 proof-check row: Prop. 8′/10(a′)/10(c) approved with errata, R1(ii),
R4 = 20 proposals, §6 five offline checks, C4 branch test deferred; its stated consequence is the **Track S
appendix** wording (per-decision formulation; no campaign-level conclusion), not Track P. It adds no Track P row
and changes no Track P authority. The plan cites the parent authority `4da73306` (whose own PLAN +10 lines add
R1-SWEEP2-SETTINGS, R1-BX-D8-V3-A, R1-TRACKG-G1B-HOST, R1-TASL2-LOCK, R1-E1-AUTH + the e1 replay authorization —
again no Track P row). The cited Track P rows (`R1-TASL7-TRACKP`, `R1-P3A-*`, `R1-E0-*`, `R1-TRACKP-CHOICES`,
`R1-C3-POOL`, `R1-C3-POOL-EXAM`, `R1-W2-3-STOP`, `R1-B2-REPAIR-SCOPE-ACK`, `R1-BX-D8`) are ancestors and unchanged.
No contradiction; no re-review of Track P is triggered.

---

## 7. Limits

- TASL-2 (§7) and Ada (§8) were not reachable from this review; those sections are unverified and are not P.3a
  inputs (the plan does not depend on them).
- Host facts are point-in-time (16 Nov 10:02–10:12Z); the runner's live preflight is what enforces them at run
  time.
- This review recomputes the lease arithmetic and re-hashes the attempt-1 inputs, but does not recompute E0 slopes,
  RPS or bootstrap bounds (not needed for Unit A); STOP 5 after the P.3a report does that.
- No host write to any experiment/repo/lock path; one transient `/tmp` scratch file was used for the freeze diff
  and deleted in the same command. No git write in the worktree (the two review files remain uncommitted for the
  operator to commit after acceptance).
- Round-1's "35 completed unit leases" is inexact (34 completed GPU units + 1 failed probes = 35 pairs); the plan's
  arithmetic is correct.

---

## 8. Verdict

- **Plan `docs/r1/proposals/TRACKP_P3A_ATTEMPT2_20261116.md` (revision 2), Unit A:** **accepted** as a
  preparation unit for review/execution (no GPU), subject to the MINOR corrections P-M1…P-M10 being applied to
  the plan/Unit A record during Unit A execution and before Unit B. No remaining BLOCKING; no remaining MAJOR in
  Unit A's scope. **Unit B is not authorized by this acceptance** and remains blocked on conditions 1–6 above.
- **Readiness report `docs/r1/reports/TRACKP_TASL7_READINESS_20261116.md`:** its central TASL-7 facts, the tmux
  correction and the attempt-1 numbers are independently verified and correct; accepted subject to the four
  minor corrections R-M1…R-M4. §7/§8 unverified (no access).
- **Authority `04ce814c`:** T4 row only; no Track P change.

**Verdict: accepted**

*(Unit B remains unauthorized. Acceptance covers the Unit A preparation unit only; it authorizes no GPU run, no
host write, no merge/push and no code-unit acceptance.)*
