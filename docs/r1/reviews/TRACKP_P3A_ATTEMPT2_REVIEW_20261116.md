# Independent review — Track P P.3a attempt 2 (probes-only) plan and TASL-7 readiness report (16 November 2026)

**Reviewer:** independent reviewer (fresh session, no part in drafting the reviewed documents). **Read-only.**
No host write, no run, no process signalled, no git write, nothing deleted. TASL-7 was inspected over
`ssh tasl7` (user `dowling`) between 2026-11-16T09:49Z and 10:00Z; attempt-1 artifacts were read only and
are unmodified (`journal.jsonl` still ends at the 2026-10-29 STOP; last mtime 2026-10-28 18:25).
TASL-2 and Ada were not accessed (no route in this review); the readiness report's §7 and §8 are therefore
**not independently verified here**.

**Canonical bytes reviewed.**
- Branch `origin/ops-tasl-20261116` @ `eb65ac4fb04fa4eff08ee144083a8fce609f342f` (2026-11-16T10:46:30+01:00);
  worktree `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/ops-tasl-20261116` (clean).
- Plan: `docs/r1/proposals/TRACKP_P3A_ATTEMPT2_20261116.md`, sha256
  `f63ab0670c62fb329e667f69574d7415fc8b2adf6e837a5a891ae1b197c42869`.
- Readiness report: `docs/r1/reports/TRACKP_TASL7_READINESS_20261116.md`, sha256
  `8bd16dbc33f7b18db9f4825c93c2277222575d2bacdb66c0207addbe3658e170`.
- Authority `author-decisions-20261116` @ `4da73306b8e10455fb124cf13d367e49b37247fe`; `docs/r1/PLAN.md`
  sha256 `993cc0a3c3407341b367f613225e32535721bfd24002201be30fb22d66742289` (same at `eb65ac4f`).
- Authorizations `docs/r1/authorizations/trackp_p3a_20261027.md` (sha `414e7144…`) and
  `trackp_p3a_amend_20261104.md` (sha `cd867e95…`); runbook Phase 5 in
  `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md`; equivalence record
  `docs/r1/reports/TRACKP_TASL7_EQUIVALENCE_20261026.md` (sha `b0710aa4…`) and its review
  `docs/r1/reviews/TRACKP_TASL7_MIGRATION_REVIEW_20261026.md` (sha `0f715089…`, final **accepted**);
  OOM diagnosis `docs/r1/reviews/TRACKP_P3A_OOM_DIAGNOSIS_20261031.md` (sha `a7ef3633…`).
- Paper pin code read at `b9ad6f8f` (`origin/trackp-20261026`), the attempt-1 launch commit recorded in the
  preserved manifests.

**Verdicts.** Plan: **not accepted** (BLOCKING-1 and MAJOR-1…6; execution also remains blocked on the
open gates in §3). Readiness report: **not accepted as written** (MAJOR-7 plus minor corrections);
its central TASL-7 facts are independently verified and correct. Final line at the end.

---

## 1. What checks out (verified, with values)

### 1.1 Next unit

The next Track P unit is correctly identified as **P.3a attempt 2, probes-only for `qwen3.5-4b-base`**, in a new
root, from the preserved attempt-1 `final/saved`; no P.3b/P.4/P.5/P.6 authorization exists (only
`trackp_p3a_20261027.md` + `trackp_p3a_amend_20261104.md` are in `docs/r1/authorizations/` on `origin/main`, the
review branch and the authority commit). The four-base P.3a pool is real: the 27 Oct note lists eight candidates,
and PLAN `R1-C3-POOL` / `R1-C3-POOL-EXAM` (28 Oct; `STATUS.md:265,267`) restrict P.3a to the four bases that ran
(the plan and readiness do not cite those two rows — finding m4). `R1-P3A-OOM-OPTION3` plus the amendment
authorize "the remaining P.3a evidence runs" with the descriptive 2k/8k A3 rows omitted on any host, attempt 1
preserved, and a new output directory. The amendment's conditions (TASL-7 only, lease, driver, pins/rule/candidates,
DRYRUN first if the code changed, STOPs, marker helper, 60 GPU-h cap incl. attempt 1, 45-h STOP) are stated in the
plan. Runbook Phase 5 and STOP 5 are correctly invoked.

### 1.2 Attempt-1 preserved state — matches every claim in the plan and readiness report

`/home/dowling/r1_trackp/runs/p3a_operator_20261027` (root 12 GB; attempt 1 was run by the one-shot
supervisor `r1/scripts/trackp_p3a_guarded.py` at `b9ad6f8f`, whose launcher is preserved unmodified). Verified
read-only:

| Claim | Verified value |
|---|---|
| journal 81 lines | 81 lines; last line is the STOP |
| campaign pins | paper `b9ad6f8f` branch `trackp-20261026` clean; harness `897d83c8efa3…` clean; "freeze matches TASL-7 recorded freeze" |
| E0 screen/select/final/hard/native complete, four bases | every unit directory has `report.json`+`manifest.json` for all four bases (3 screen lrs, select, final, hard, native) |
| short Kev-0.8B DRYRUN complete | DRYRUN has all 7 GPU units + select report |
| probes complete, three bases | `kev-0.8b` `report.json` sha `f04df4e113d34fc117b4a881b5bfd34da81f711194b24e87c3e2c060c43d6f27`; `kev-4b` `fae7c9cbda0c7fbeb55e2993445d096c1a86f0aa487637b80d4e8b96edd5033e`; `qwen3.5-0.8b-base` `73894af6ad537fc9186216c55a790b7eadc86d68609f3e03e9af13f1fc270647` |
| `qwen3.5-4b-base` probes STOP, CUDA OOM, 2026-10-29T01:25:17Z, descriptive A3 loop | probes directory absent (no `report.json`); `probes.stdout.log` traceback ends in `exam_run.py:293 _a3_rps` inside the descriptive long-level loop (`long = E.a3_probe(tok, …, lengths=(0,)+E.A3_DESCRIPTIVE)`), then `torch.OutOfMemoryError: tried to allocate 1.49 GiB; 21.94 GiB in use, 1.31 GiB free`; journal STOP `"utc": "2026-10-29T01:25:17Z"` |
| `gpu_seconds_total = 130745.3789889291` = 36.318 GPU-h; 8.682 h of the 45-h STOP left | journal STOP value exactly `130745.3789889291`. Independently recomputed from the global `gpu_lease_log.jsonl`: 35 lease pairs = `130745.378989 s` = **36.318161 h**; 45 − 36.318161 = **8.681839 h**; the sum of the 35 completed unit leases is `130632.997360 s`, exactly the `gpu_seconds_before` of the failed probes unit; that unit's lease was `112.381629 s` |
| prior probe leases 68–148 s (plan §2b) | `kev-0.8b` 67.807 s, `kev-4b` 134.155 s, `qwen3.5-0.8b-base` 148.412 s (exact) |
| no unplanned reboot since attempt 1 | current boot id `2c9bb104-cc3c-4c60-be67-c1c8f0287fe4` = the attempt-1 `campaign_start.boot_id`; uptime 45 d |

The attempt-1 `final/saved` that the plan would load re-hashes to its recorded manifest values: adapter/README
`d1502e5c…`, adapter_config `3b31604a…`, adapter_model `0b39d3fa…`, heads `aeea9ec1…` — **all match**;
`head_form = linear12`, evidence label `EVIDENCE`, `argv` of the failed unit is exactly the command the plan
proposes (`probes --base qwen3.5-4b-base --head-form linear12 --budget --n-probe 100 --load …/final/saved
--evidence EVIDENCE --run-dir …/probes`). The config digest in the attempt-1 manifests is
`64073ceaa2660b5b8d783146a406135146a01c2f07e9c0d84f5a17431986f00c`, equal to the pin's
`r1/scripts/configs/trackp_portal.json`. Distinguishing detail: the failed probes unit had already finished
A3 v2 (the 0/25/50/100 % rows) before the OOM; the whole interrupted unit is re-run by the plan, which the
27 Oct note's "interrupted unit is re-run whole" allows (the plan should say so — finding M4).

### 1.3 Host/gate facts — the readiness §1/§2/§3 GPU, lease, repo, freeze and pin values are verified

- `TASL-7`, user `dowling`; RTX 4090 24,564 MiB, **236 MiB** used, **0 %**; `nvidia-smi` reports no compute
  application; driver **580.178.04**; `/home/dowling` **1.9 T, 524 G free (71 % used)**.
- `~/r1_locks/gpu0.lock` inode `56251186`, size 0; **no `/proc/locks` entry** for it (lease free); no
  `*.active` marker (`trackx_evidence.active`, `trackp_evidence.active`, `trks_drill.active` all absent);
  no `trackp_evidence.log` (the helper has never been used on TASL-7).
- Paper `Agent_paper_B` @ `b9ad6f8fe2e771732100f704accd7f2ce7cf20f0`, branch `trackp-20261026`, **clean**;
  harness `autoresearch_harness` @ `897d83c8efa364ec2fdd37288241cc42e01d7274`, **clean**; 8 model repos in
  `models/`; `runs/` holds attempt 1, the 26 Oct equivalence run, and the global lease log.
- Venv `venvs/trackp-gpu`: Python 3.12.15, torch 2.6.0+cu124; `uv pip freeze` is **byte-identical** to
  `docs/r1/reports/tasl7_phase2_20261026/pip_freeze_trackp-gpu_tasl7.txt` (121 lines, 3 `@ git+` lines;
  `diff` empty — 0 version differences, no extras). The portal freeze file is byte-identical to it (121 lines).
- Marker helper: host sha256 `f457a04ef1bbaba1750d9c04aa9211d51df1692ac36139bb720318f2d2533cec`, mode 755,
  3,949 B, mtime 2026-11-04 08:55:15 -0800 — equal to the committed `docs/r1/proposals/trackp-evidence.sh`
  (sha `f457a04e…`). Note it is **not** in the host paper checkout at `b9ad6f8f` (the pin predates it); the
  "matches the committed script" comparison is against the canonical repo, not the host tree.
- Pins re-verified from committed bytes: `e0_v1.jsonl.gz` `4f4db29b…`, `p3_rule_v2.yaml` `8c0ef908…`,
  `registry.yaml` `e60cdb28…`; equivalence pre-declaration commit `f3567e9` at `2026-10-26T15:47:40-07:00`
  = **22:47:40Z**, before the 22:52Z run, as claimed; Δ width slope −0.0095, Δ mean +0.0077, RPS −2.5 %
  as claimed; migration review final verdict **accepted**.
- Track P Phases 0–4 are accepted as claimed (`TRACKP_0..4_REVIEW_20261026.md` final verdicts accepted;
  `TRACKP_P0_SPIKES_20261026.md` covers all 8 bases; the toy batch, E0-v2 DRYRUN, two-stage DRYRUN and P.3a
  DRYRUN records exist). No P.3a report exists yet (attempt 1 STOPped before writing it) — consistent with
  the plan's "P.3a report after run".
- Readiness §6 W2-3 values verified on unmerged branch `w2-3-rebuild-unit-20261115` @ `2989f383`:
  PASS 288 ledgers × 20 worker runs, 0 differing; artifacts `d0048567…`/`b585b727…`/`7f56619c…`/`661f0fd8…`;
  4,999 proposals / 302 configs / 5,813 replay rows; not merged to `origin/main`. The report is right that
  these are **not** P.3a inputs.

### 1.4 Open gates are correctly identified as open

A3-short code delta (separate review), M13 template-version inventory (attempt-1 manifests; template pin still
unresolved), A6 probe ambiguity (spec §5.6 "(proposed)", unimplemented, and `R1-P3A-OOM-OPTION3` (G2) requires it
to quantify the difference), independent review of the plan, and STOP 5 of the report — all are correctly listed
as open. "Execution waits for its review, the code-delta review, M13/A6 disposition, and the marker/lease checks"
is the right overall gate statement. See §3 for what the plan must add to those gates.

---

## 2. Findings

Severity: **BLOCKING** = the plan cannot be accepted/executed as written; **MAJOR** = material gap or
contradiction that changes what would be executed or recorded; **MINOR** = correction that should be made before
the run.

### BLOCKING-1 — the plan has no reviewed execution harness, preflight, journal or budget guard; the single command drops the attempt-1 safeguards

Locations: plan §2b ("Probes", "Outputs", "Budget", "Marker"), §5.
The plan replaces the reviewed attempt-1 supervisor with one bare `python r1/scripts/trackp.py probes …`
invocation. Read at the pin, `cmd_probes` does only `check_environment` (torch + three code-pin commits) and the
GPU lease. The attempt-1 supervisor at `b9ad6f8f` additionally did (see its `verify_pins`), and attempt 2 would
lose: paper
branch/clean + harness-commit check, exact `e0_v1`/`p3_rule_v2` sha checks, approved-config-digest check, venv
freeze check, `registry.reverify` of the model files, a `journal.jsonl`, pin re-verification before the unit, a
45-h `GPUBudget` guard seeded from the lease log, the 45-h STOP before starting, and the boot-id/driver
checks around the job. The plan's "Outputs" bullet claims `journal.jsonl` and `gpu_lease_log.jsonl` — a bare
`trackp.py probes` run produces `manifest.json`, `report.json`, its stdout log and a global lease-log append
only; there is no journal writer and no reviewed probes-only runner (`trackp_p3a_guarded.py` is a one-shot full
campaign that refuses an existing root and would re-run every base). The manifest also records
`model_files_sha256: {}` for probes (verified on the completed attempt-1 probes manifest), so the loaded
attempt-1 inputs are not bound by hash in the new record. `R1-P3A-OOM`'s preconditions — "verify and hash
completed native outputs, empty card and projected budget" — appear nowhere as explicit preflight steps.
**Fix:** either (a) add a reviewed minimal probes-only runner/supervisor (journal with `gpu_seconds_total`,
budget guard seeded from `130745.3789889291`, live pin/freeze/config/`e0_v1`/rule/registry checks before the
unit, boot-id/driver guard, hash+record of the four attempt-1 `final/saved` files, record of the authorization
note sha), or (b) enumerate the exact operator preflight commands for each of those checks, define the
post-run accounting (attempt-1 journal total + the new unit's lease start/end from its manifest), and correct
the Outputs bullet (no `journal.jsonl`; per-unit manifest/report only). Do not execute with the bare command as
the plan stands.

### MAJOR-1 — the serialisation template version/order is not pinned, and attempt-2 results would not record it

Locations: plan §1, §2b "Outputs", §3 M13 and A6 rows; amendment condition "Template version"; PLAN
`R1-P3A-OOM-OPTION3` (G2); spec `TRACK_P_POST_TRAINING.md` §2.2/§5.6; M13 inventory/review.
`R1-P3A-OOM-OPTION3` (G2) requires P.3a results to be "kept and tagged with their template version", and spec
§2.2 says "the template carries a version field"; the amendment requires every P.3a result to record it.
Verified: **no attempt-1 file records any template/prompt version** — a read-only search of the whole 12 GB
attempt-1 root finds zero occurrences of `trackp_prompt` or `prompt_version`; probes/e0 manifests and reports
have no version field (the pin sets `PROMPT_VERSION = "trackp_prompt/v1"` only in `serialize_view` metadata, and
the E0 rows do not carry it — exactly M13's point). The plan says only that every result "records its
serialisation/template version", with no mechanism; the current `trackp_run_manifest/v1` schema has no such
field. It also does not state that attempt 2 must use the **attempt-1 order/version** (the 4 Nov order is for
P.3b onward; M13/MAC-local say "keep the old version loadable, so that P.3a records stay reproducible" and "P.3a
is re-run under the new order only if probe A6 shows mean |Δ RPS| > 0.01"). A6's disposition therefore decides
attempt 2's template, but the plan treats A6 only as a separate gate. **Fix:** state (i) attempt 2 runs the
attempt-1 template version/order (as recorded at `b9ad6f8f`; no 4 Nov-order code in the run pin), (ii) the
concrete recording mechanism per result (a new manifest/report field or a sha-verified sidecar added by the code
delta, since the current schema has none), (iii) that the P.3a report retro-tags the attempt-1 results with the
M13-determined version, and (iv) the dependency: A6/M13 dispositions precede execution and their outcome may
change the scope (a P.3a re-run under the new order is a separate, unauthorized unit).

### MAJOR-2 — the required DRYRUN is unspecified and may not exercise the changed code

Locations: plan §2a last sentence, §2b "DRYRUN".
The amendment (unchanged 27 Oct condition) requires "a DRYRUN first, if the code has changed since attempt 1"; the
plan changed the code, so the DRYRUN is mandatory, not optional. The plan gives no model path (`DRYRUN/…` vs
`EVIDENCE/…` attempt-1 saved models), no label (`--evidence DRYRUN`), no arguments, no step/probe count, no
output directory, and no cost. If the DRYRUN is the attempt-1-style short E0 run (`e0` 3×200-step screens + 400-step
final/hard/native), it does **not** exercise the modified `exam_run.probes()` path, which is the only changed
code — that would not satisfy "under the final code". Attempt-1's short DRYRUN cost 1,915.8 lease-seconds
(0.532 GPU-h) plus a 33.1 s n=32 probes unit. **Fix:** specify the exact DRYRUN command(s) (recommended: the
attempt-1 short Kev-0.8B DRYRUN end-to-end, including a `probes --n-probe 32` unit that loads the DRYRUN
`final/saved` **with the new A3-short flag**), label `DRYRUN`, write it to `<new-root>/DRYRUN/…`, and count
≈0.5 GPU-h in the budget projection.

### MAJOR-3 — the amendment authorizing option 3 is not on the host pin, so the flag's "refused unless the amendment is cited" cannot be enforced or verified

Locations: plan §2a ("refused unless the amendment is cited"), §2b "Pins"; readiness §5 "Authorization notes".
Verified: the host paper checkout at `b9ad6f8f` contains only `docs/r1/authorizations/trackp_p3a_20261027.md`;
the 4 Nov amendment (sha `cd867e95…`) is **absent** there. `authorization_note("p3a")` globs
`trackp_p3a_*.md` and takes the last; with only the 27 Oct note present, the EVIDENCE-label check passes, but the
option-3 authority and the flag's own guard have nothing to read. **Fix:** specify how the amendment reaches
TASL-7 (e.g. included in the reviewed code-delta commit, or a sha-verified copy placed for the run) and that its
sha256 is recorded in the attempt-2 record; state how `--a3-short-rows` verifies/refuses it (and that it is
refused without `--budget`, so the v1 A3 path cannot silently run 2k/8k).

### MAJOR-4 — the must-not list contradicts the authorized re-run of the interrupted qwen3.5-4b probes unit

Location: plan §4 "no re-run of attempt-1 screen/select/final/hard/native/probes or another base".
§1 and §2b of the same plan re-run the *interrupted* `qwen3.5-4b-base` probes unit whole — that is the unit being
executed. Read literally, the must-not list forbids the run and the STOP list ("attempts to re-run attempt-1
units") would STOP it. **Fix:** distinguish completed from interrupted: "no re-run of the completed attempt-1
units (three probes, all E0 units) or of another base; the interrupted `qwen3.5-4b-base` probes unit is re-run
whole into the new root (27 Oct note), and its A3 v2 rows are recomputed because the interrupted report was
never written."

### MAJOR-5 — the OOM authority chain is incomplete: the independent diagnosis is UNCLEAR/STOP and is not cited

Location: plan §1.
The plan narrates the STOP and the author's option 3 but omits
`docs/r1/reviews/TRACKP_P3A_OOM_DIAGNOSIS_20261031.md` (sha `a7ef3633…`), whose verdict is "**UNCLEAR — STOP.
No retry authorized under R1-P3A-OOM until an environmental cause is established**", and whose option (3) is "a
frozen execution change … Neither (2) nor (3) is authorized by the environmental-only rerun condition." The
operative authority for attempt 2 is therefore the author's option-3 decision
(`R1-P3A-OOM-OPTION3` + the 4 Nov amendment), **not** `R1-P3A-OOM`'s environmental-only rerun, and this is a
frozen execution change. **Fix:** cite the diagnosis, state the authority chain explicitly, and add its carried
preconditions to the preflight (hash/verify the preserved native outputs — the four `final/saved` files — an
empty card/census, and the projected budget).

### MAJOR-6 — the code-delta citation points at the wrong tree; the delta must be pinned to `b9ad6f8f` with a flag/tests-only diff

Locations: plan §2a ("`r1/c3/train/exam_run.py:274–280`"), §2b "Pins".
At the paper pin `b9ad6f8f` the descriptive 2k/8k block is `exam_run.py:290–295` (the lines 274–280 are the A3 v2
block); lines 274–280 match the review branch's current `HEAD`, not the run pin. The two trees differ materially:
`git diff b9ad6f8f..HEAD` for the run code is exam_run.py 7 hunks/28 lines, run.py 76 lines, model.py 43 lines,
trackp.py 6 lines — and `HEAD` has **removed** the pinned non-finite STOP checks in `exam_run.py`, so a delta
authored on the wrong tree would change far more than the A3 rows. **Fix:** cite `b9ad6f8f:290–295`; require the
delta commit's parent to be `b9ad6f8f`, its `r1/` diff to be only the A3-short flag + tests, the host tree clean
at the delta commit (branch `trackp-20261026`), the delivery mechanism (push/pull, recorded commit) and the
review record; and state that no W2-3/`c3_features/v3`/`trackp_prompt/v2` code or artifacts enter the P.3a pin
(they are not P.3a inputs) and that no M13 4-Nov-order template change is included.

### MAJOR-7 (readiness report) — the "no tmux server / no foreign process" host-occupancy claim is false

Location: readiness report §1.
"no tmux server; no experiment/Track S/Track P process" is **false**. Live tmux servers exist: user `tianyu`,
pid `934891` running 28 d 12 h with three panes (`pts/0,2,3`, all running `claude` agents, one
`--model claude-opus-5-5 --permission-mode auto`), and user `dowling`, pid `1570627`, socket
`~/r1_b1_engineering/b1_handover_6835_20261108_a/tmux.sock`, one idle `bash`. User `jiachenl` also has an
`sshd` session ~23 h old (and there are other users' desktop services: xrdp, code-server). GPU 0 has no
compute application and the lease is free, so the run is not blocked now, but the readiness report must correct
the claim and disclose the foreign interactive sessions; the plan's host preflight should enumerate them and
record that no foreign process holds the GPU (STOP on any foreign GPU job, as the plan already lists). This is
also relevant context for the OOM diagnosis's "does not establish absence of other GPU processes".
**Fix:** correct §1; add the enumeration to the run preflight/record.

### MINOR findings

- **m2 (readiness §3).** "accepted the migration (5 minor findings fixed)" — the review was provisionally
  4 MINOR, then **not accepted** for finding 5 (a test-file bug), then accepted after the fix. Correct the
  wording to "five findings, one of which blocked a prior round".
- **m3 (plan §2b Outputs / amendment).** The treatment of the already-collected descriptive A3 rows is
  unspecified. The three completed probes reports contain `A3_descriptive`: `kev-0.8b`/`kev-4b` have
  `ran: [0]` plus caught `ContextOverflow` for 2k/8k; `qwen3.5-0.8b-base` actually ran them
  (mean |Δ RPS| 6.5148e-6 / 9.6039e-6). The amendment says the rows "are not run, not attempted on any host,
  and not reported as missing results". State that the P.3a report omits `A3_descriptive` for all bases and
  records the omission under `R1-P3A-OOM-OPTION3`, and that the three preserved reports are not rewritten.
- **m4 (plan §1 / readiness §4 authority).** Cite PLAN `R1-C3-POOL` and `R1-C3-POOL-EXAM` for the four-base
  pool (the 27 Oct note alone lists eight candidates).
- **m5 (plan §2b Marker).** Specify phase string `p3a` (the helper's `end` requires exact match); the job takes
  its own `flock -n` inside `trackp.py`, so it must **not** be wrapped with `trackp-evidence run`
  (nested `flock` would deadlock/fail); begin after the lease-free/census check, end after the last job and also
  on STOP. The marker-procedure text in `proposals/TRACKP_EVIDENCE_MARKER_20261030.md` is still proposed
  (only the helper installation is mandated by `R1-TRACKS-S01-RERUN` and the amendment), so the plan must state
  the procedure it relies on.
- **m6 (plan §2b host/env).** The attempt-1 launcher set
  `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`,
  `PYTHONUNBUFFERED=1`. The OOM occurred with `expandable_segments=True`; attempt 2 must state and record the
  exact environment (unchanged from attempt 1 unless separately reviewed).
- **m7 (plan §2b new root).** `trackp.py`'s `_write_json` overwrites an existing `report.json`/`manifest.json`;
  the "must not exist" rule is procedural, not code-enforced. Add an explicit preflight
  (`test ! -e <new-root>` and no unit dir) and a STOP if present; give the `<UTC>` format (e.g. `20261116T1055Z`).
- **m8 (plan §2b Budget).** The projection covers only the probes (<1 h) and omits the DRYRUN (~0.5 h). State
  the total projection (≈1.5 h against 8.682 h left), and state whether the 26 Oct equivalence/Phase-2 GPU time
  (≈0.42 h, not in the attempt-1 journal) is outside the 45/60-h P.3a accounting (defensible, but must be
  declared).
- **m9 (plan §2b wording).** "one GPU-producing command" is two leases (DRYRUN + probes). Also note that A1/A2
  will be recorded as `{"pass": null, "reason": "model does not pack"}` for all four bases; readiness §4 lists
  A3/A4/A5 but not A1/A2 (the amendment says A1/A2 are unchanged — record the N/A).
- **m10 (readiness §6).** `reports/W2_3_CHECK_20261115.md`, `w2_3_check_20261115.json` (actually
  `w2_3_check_20261115/w2_3_check_20261115.json`), `reports/W2_3_REBUILD_RUN_20261115.md` and
  `docs/r1/reports/w2_3_rebuild_20261115/` exist only on the unmerged branch
  `w2-3-rebuild-unit-20261115` @ `2989f383`, not on the canonical branch; label that in the report. The values
  themselves check out.
- **m11 (readiness §6).** "probes load attempt-1 native outputs" is imprecise: the plan and argv load
  `EVIDENCE/qwen3.5-4b-base/final/saved` (the fresh-head `final` unit), not the `native` unit.
- **m12 (readiness §5).** "Authorization notes … present": the 4 Nov amendment is present in the canonical repo
  but not on the host pin — say which, and add the delivery step (MAJOR-3).
- **m13 (limits).** Readiness §7 (TASL-2) and §8 (Ada) could not be verified in this review (no access); the
  plan does not depend on them.

---

## 3. Open gates the plan must carry before execution

1. **A3-short code delta** — open, separate independent code review. Must be authored against `b9ad6f8f`
   (MAJOR-6), include the amendment-citation guard (MAJOR-3), the template-version recording mechanism
   (MAJOR-1), tests (flag→only four A3 rows; no flag→byte-identical; 2k/8k never attempted), and the delta
   commit delivered to TASL-7 and recorded.
2. **M13 template-version inventory** — open. It is now completable from material already available: the
   preserved attempt-1 manifests (read here) record the launch commit `b9ad6f8f`, and `b9ad6f8f` plus its
   `serialize.py`/`types.py` and the pinned Kev encoder (`kev@2074cc44…`) are in the repo, so the order and
   `trackp_prompt/v1` tag can be established and the attempt-1 results retro-tagged. Until then the plan cannot
   claim the amendment's template-version condition.
3. **A6 probe** — open/ambiguous: spec §5.6 marks it "(proposed)", it is unimplemented, and option 3 (G2)
   requires it to quantify the difference. Needs an author decision or a reviewed unit; its outcome decides
   whether P.3a is re-run under the new order, so it gates attempt 2's template.
4. **Independent review of this plan** — this file: not accepted; a corrected plan needs re-review.
5. **STOP 5 review of the P.3a report** — after the run; the reviewer must also recompute the 45-h accounting,
   check the rule hash, and check the template-version tags (attempt-1 retro-tag and attempt-2 field).
6. **Marker/lease preflight** — marker helper installed and sha-verified (done), lease free/census empty
   (true now), marker `begin p3a` / `end` as in m5.

---

## 4. Verdict

- **Plan `docs/r1/proposals/TRACKP_P3A_ATTEMPT2_20261116.md`: not accepted.** The unit identification, attempt-1
  state, budget arithmetic and most host/pin facts are correct and verified, but the plan cannot be executed as
  written: BLOCKING-1 (no reviewed probes-only runner/preflight/journal/budget guard; wrong output claim) and
  MAJOR-1…6 (template version/order, DRYRUN, amendment delivery/enforcement, must-not contradiction, OOM
  authority chain, code-delta base/citation) must be fixed, and the corrected plan independently re-reviewed.
- **Readiness report `docs/r1/reports/TRACKP_TASL7_READINESS_20261116.md`: not accepted as written.** Its
  substantive TASL-7 facts (idle GPU/lease, driver, disk, repos, venv freeze, helper sha, budget) and its
  attempt-1 numbers are independently verified and correct, but §1's "no tmux server" claim is false and
  foreign interactive sessions/agents are undisclosed (MAJOR-7), plus the minor corrections above. §7/§8 are
  unverified here.
- **Execution remains blocked** on acceptance of the corrected plan **and** the A3-short code delta review
  **and** the M13 and A6 dispositions, in addition to the marker/lease preflight; attempt 1 must stay untouched
  and read-only.

**Verdict: not accepted**

---

## Appendix — read-only evidence collected (16 Nov 2026, 09:49–10:00Z unless noted)

- `ssh tasl7`: `hostname`=TASL-7, user `dowling`; `nvidia-smi` 24564 MiB/236 MiB/0 %/580.178.04/UUID
  `GPU-ab72fb4a-…`; `df -h` 1.9T/524G/71 %; boot id `2c9bb104-cc3c-4c60-be67-c1c8f0287fe4` (equals attempt-1
  campaign boot id); `/proc/locks` no entry for inode `56251186`; no `*.active`; no compute app.
- tmux/processes: `tianyu` pid 934891 (28 d 12 h, `new-session -t paper`, panes `pts/0,2,3` running `claude`;
  child PIDs 934951/1595171/1601915/1596620/3122873); `dowling` pid 1570627 (b1 handover socket, idle bash);
  `jiachenl` sshd ~23 h; no experiment/Track S/Track P process; no `trackp_evidence.log`.
- Repos: paper `b9ad6f8fe2e771732100f704accd7f2ce7cf20f0` branch `trackp-20261026` clean; harness
  `897d83c8efa364ec2fdd37288241cc42e01d7274` clean; 8 model repos; `runs/` = attempt-1 root + log + launcher
  (`PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`, `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
  PYTHONUNBUFFERED=1`), `tasl7_equiv_20261026`, `gpu_lease_log.jsonl`.
- Venv: Python 3.12.15, torch 2.6.0+cu124; `uv pip freeze` diff vs committed TASL-7 freeze **empty**
  (121/121 lines).
- Helper: `f457a04ef1bbaba1750d9c04aa9211d51df1692ac36139bb720318f2d2533cec`, 755, 3949 B,
  2026-11-04 08:55:15 -0800; not present in the host paper tree at `b9ad6f8f`.
- Attempt 1: root 12 GB, journal 81 lines; last line
  `{"error": "unit failed rc=1: …/EVIDENCE/qwen3.5-4b-base/probes; see …/probes.stdout.log", "event": "STOP",
  "gpu_seconds_total": 130745.3789889291, "unobserved_lease_upper_s": 0.0, "utc": "2026-10-29T01:25:17Z"}`;
  campaign pins include paper/harness clean + "freeze matches TASL-7 recorded freeze"; probe `report.json`
  shas `f04df4e1…d6f27`, `fae7c9cb…033e`, `73894af6…647`; `qwen3.5-4b-base/probes/` absent; OOM traceback at
  `exam_run.py:293`; `final/saved` files re-hash to their manifest values; probes manifest
  `model_files_sha256 = {}`; no template/prompt version string anywhere in the 12 GB root.
- Config digest `64073ceaa2660b5b8d783146a406135146a01c2f07e9c0d84f5a17431986f00c` (equals the pin); pin
  `e0_v1` `4f4db29b…`; `p3_rule_v2.yaml` `8c0ef908…`; `registry.yaml` `e60cdb28…`.
- Committed cross-checks: `f3567e9` 2026-10-26T15:47:40-07:00 (=22:47:40Z); portal and TASL-7 freeze files
  byte-identical; W2-3 values on branch `2989f383` as in readiness §6; equivalence review final **accepted**;
  `TRACKP_0..4` reviews final accepted; no `trackp_p3b/p4/p5/p6` authorization on `origin/main`, the authority
  commit or the review branch.
