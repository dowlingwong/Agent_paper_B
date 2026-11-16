# Proposed units — Track P P.3a attempt 2 on TASL-7 (16 November 2026, revision 2)

**Status: proposal for independent review; nothing executed.** This revision answers the round-1 review
(`reviews/TRACKP_P3A_ATTEMPT2_REVIEW_20261116.md`, sha `5f579cdc…`, verdict NOT ACCEPTED) and splits the
work into a **preparation unit (Unit A, no GPU)** — proposed here as the first unit for review — and a
**run unit (Unit B)** that may start only after Unit A and the code units are accepted and the M13/A6
dispositions exist. Authority: `author-decisions-20261116` @ `4da73306`; PLAN `R1-TASL7-TRACKP`,
`R1-P3A-READY`, `R1-P3A-OOM-OPTION3`, `R1-P3A-BUDGET-CLOCK`, `R1-E0-*`, `R1-TRACKP-CHOICES`,
`R1-C3-POOL`, `R1-C3-POOL-EXAM` (four-base pool), `R1-W2-3-STOP`, `R1-B2-REPAIR-SCOPE-ACK`, `R1-BX-D8`;
authorizations `trackp_p3a_20261027.md` + `trackp_p3a_amend_20261104.md`; Track P runbook Phase 5;
attempt-1 OOM diagnosis `reviews/TRACKP_P3A_OOM_DIAGNOSIS_20261031.md` (**UNCLEAR — STOP**, options 1–3;
option 3 is a **frozen-execution change**, not the environmental-only rerun); M13 inventory
`reports/MAC_M13_TEMPLATE_INVENTORY_20261105.md`.

## 0. Attempt-1 facts (read-only; independently re-verified)

- Root `/home/dowling/r1_trackp/runs/p3a_operator_20261027`; journal 81 lines; E0
  screen/select/final/hard/native completed for all four bases (the four-base pool is `R1-C3-POOL` /
  `R1-C3-POOL-EXAM`); E6 probes completed for `kev-0.8b` (`report.json` `f04df4e1…`), `kev-4b`
  (`fae7c9cb…`), `qwen3.5-0.8b-base` (`73894af6…`).
- The `qwen3.5-4b-base` **probes unit is the interrupted unit**: CUDA OOM in the descriptive A3 2k/8k
  loop (`exam_run.py:290–295` at the pin; 1.49 GiB request, 21.94 GiB in use), STOP at
  2026-10-29T01:25:17Z; `gpu_seconds_total = 130745.3789889291` = **36.318161 h**; **8.681839 h** remain
  of the 45-h lease STOP, and the 60-h cap includes attempt 1. Attempt 1 is preserved and is not
  overwritten or reused.
- **Completed attempt-1 units are not re-run** (E0/final/hard/native for all four bases; probes for the
  other three bases). Only the **interrupted 4b probes unit** is re-run, in a **new root**.

## 1. Unit A (first for review; no GPU) — preparation, M13/order, amendment delivery, code units

### 1a. Attempt-1 inventory + M13 template/order determination (read-only local artifact export)

Export to a repo evidence directory (hashes in a `SHA256SUMS`; read-only on TASL-7): every attempt-1
per-run `manifest.json` (all bases/units, including the three probes manifests and the final/native/hard
manifests), the attempt-1 journal/lease log, and the pinned source files that define the rendering:
`b9ad6f8f:r1/c3/train/{types.py,serialize.py,model.py,exam_run.py}`, `r1/scripts/trackp.py`,
`r1/scripts/trackp_p3a_guarded.py`. A **local reviewer** (not the operator) inspects them and records:
(i) the exact attempt-1 paper commit and model family; (ii) whether attempt 1 was history-first or
proposal-first per family wrapper (M13's actual question); (iii) a concrete **template-version recording
mechanism** for attempt 2 (a manifest field with the version string, sourced from the pinned
`PROMPT_VERSION`/wrapper order, plus the attempt-1 order; results are recorded with the attempt-1
version, never re-labelled); (iv) the A6 question (A6 is only "(proposed)" in the spec and is **not
implemented** in `exam_run.py`; option 3 says A6 quantifies the difference — the author/coordinator must
either authorize A6 as a separate reviewed unit or record that it is deferred and the limitation
disclosed). Unit A is complete only when this record exists; the run cannot start before it.

### 1b. Amendment delivery/record (no host checkout change)

The host checkout at `b9ad6f8f` has only the 27 Oct note; the 4 Nov amendment is on `main` at
`4da73306`. The run gate must not depend on a file that is absent. Unit A records the amendment bytes'
sha256 (from `main:docs/r1/authorizations/trackp_p3a_amend_20261104.md`) and specifies that the runner
takes `--authorization-amend-sha256 <sha>` and refuses unless it matches; the journal records it. The host
checkout stays clean at `b9ad6f8f`; no merge of `main`, no code change for this.

### 1c. Two code units (each separately reviewed before Unit B)

1. **A3-short execution delta** on a new branch with parent **`b9ad6f8f`**, flag/tests-only diff in `r1/`:
   a flag that makes the budget branch of `exam_run.probes()` run only A3's specified rows (0/25/50/100 %
   of the remaining budget at 1,024 tokens) and **not** the descriptive 2k/8k levels at
   `exam_run.py:290–295`; tests: flag-on produces exactly the four specified rows; flag-off is
   byte-identical to the current code; no 2k/8k attempt with the flag. **No other change** (no removal of
   the pinned non-finite STOPs, no W2-3/v3/v2/M13/order changes, no other file changes). The delta's
   reviewed commit sha is recorded.
2. **Probes-only runner/preflight/journal/budget unit** (the round-1 BLOCKING-1): a reviewed script
   derived from the attempt-1 guarded supervisor (`trackp_p3a_guarded.py`), not the bare
   `trackp.py probes` command, with at least:
   - `verify_live_pins`: paper `b9ad6f8f` (or the reviewed A3-short commit on top), clean; harness
     `897d83c8`, clean; `e0_v1` sha `4f4db29b…`, `p3_rule_v2.yaml` sha `8c0ef908…`, `trackp_portal.json`
     unchanged from the approved config; run venv freeze vs the TASL-7 pin; model registry reverified;
     hostname TASL-7; boot id; driver 580.178.04; disk; boot/uptime snapshot;
   - lease acquire (`flock ~/r1_locks/gpu0.lock`) and an **empty GPU-compute census**; the Track P
     evidence marker (`~/r1_locks/bin/trackp-evidence`, sha `f457a04e…`) begin/end; no other experiment
     process;
   - a **new root** `~/r1_trackp/runs/p3a_attempt2_<UTC>/` (must not exist), per-unit directories,
     `journal.jsonl` + `gpu_lease_log.jsonl` + per-unit `manifest.json` (with the attempt-1 input
     `model_files_sha256` binding for the loaded `final/saved`, template version, code pin, config/e0/rule
     hashes, host/driver/boot, authorization note + amendment sha, argv);
   - the **budget guard**: reads attempt 1's 130745.3789889291 s and the 45-h lease STOP, computes the
     projection before each GPU unit, refuses if the projection crosses 45 h, and accounts the total
     toward the 60-h cap;
   - a **DRYRUN-first** (short Kev-0.8B) that exercises the **changed** `probes()` A3 path (not merely
     e0), with its cost recorded, before the 4b probes;
   - fail-closed STOPs for every mismatch; no retry; preserve outputs.
   The runner's preflight is also used by the run; no bare `trackp.py probes` command is used.

### 1d. A6 disposition — RESOLVED (author, 16 Nov 2026, `R1-TRACKP-A6-DEFER`)

The author signed `R1-TRACKP-A6-DEFER` (branch `author-decisions-20261116c` @ `65d8d5bb`, merged into this
branch): **A6 is deferred for P.3a attempt 2 and disclosed in the report; a separate independently reviewed
A6 unit comes before any P.3b serialisation-order change.** Basis: A6 is spec "(proposed)", descriptive,
not a gate; attempt 1's two wrapper families are both history-first (M13 record
`reviews/TRACKP_P3A_M13_ORDER_RECORD_20261116.md`). This clears the A6 prerequisite for Unit B; the P.3a
report must state the deferral and that the 2k/8k descriptive rows are omitted under
`R1-P3A-OOM-OPTION3` (no A6 quantification).

### 1e. Preflight checklist recorded (no run)

TASL-7: hostname/user; GPU idle (236 MiB/0 %, no compute app); driver 580.178.04; disk 524 G; lease free
(no `/proc/locks` entry); no `*.active` marker; operator default tmux socket has no server, **but other
users' tmux servers/sessions exist** (`tianyu` pid 934891 with three panes; the preserved `dowling`
`b1_6835_20261108_a` session on its own socket, pid 1570627) — recorded, never touched; P.3a attempt-1
inputs read-only and hash-verified. No GPU job in Unit A.

## 2. Unit B (run unit; starts only after Unit A accepted + both code units accepted + M13/A6 dispositions + preflight)

One GPU-producing session, TASL-7 only:
1. New root `~/r1_trackp/runs/p3a_attempt2_<UTC>/`; marker begin; journal/lease log start.
2. DRYRUN: short Kev-0.8B probes under the reviewed code path (changed A3) in the new root; verify it
   exercises the A3 path and record cost.
3. EVIDENCE: `qwen3.5-4b-base` probes only, from attempt-1 `final/saved`; A3 specified rows under the
   A3-short flag; A4; A5 descriptive; A1/A2 unchanged; template version recorded; no 2k/8k rows.
4. Budget: attempt 1 (36.318 h) + this run; refuse if projected >45 h; 60-h cap includes attempt 1.
5. Outputs: per-unit manifests/reports, attempts' journal/lease log; the P.3a report
   `docs/r1/reports/TRACKP_P3A_<date>.md` + appendix data; STOP 5 review (reviewer recomputes slopes/
   rule hash).
6. STOPs: pin/freeze/config/e0/rule/registry mismatch; hostname/boot/driver mismatch; owner process,
   marker or foreign GPU job; OOM/CPU fallback; non-finite metric; budget rule; any protocol/A3/order
   change; attempted 2k/8k rows; attempted re-run of completed units. STOP = preserve, report, no retry.

## 3. Must not

- No P.3b/P.4/P.5/P.6; no labels/seeds 7006–7010; no real or sweep-2 tables (D8 lock); no change to
  `p3_rule_v2`, `e0_v1`, thresholds or the A3 spec; no W2-3/v3/v2/M13/order changes on the Track P code
  pin; no removal of the pinned non-finite STOPs; no merge of `main` into the host checkout; no other
  host; no Jev/DeepSeek/API; no deletion (move aside only); no claim of acceptance; no push to `main`;
  **no re-run of completed attempt-1 units** (only the interrupted 4b probes unit is re-run, in a new
  root).

## 4. What the reviewer should decide now

Unit A: is the preparation scope complete and sufficient (inventory/M13, amendment record, code-unit
requirements, A6 request, preflight)? Unit B is not for acceptance yet; it is included to show the
intended run and its gates. Execution of either unit waits for the independent review; Unit B additionally
waits for the two code reviews and the M13/A6 dispositions.
