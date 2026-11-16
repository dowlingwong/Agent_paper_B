# Proposed unit — Track P P.3a attempt 2 (probes-only completion) on TASL-7 (16 November 2026)

**Status: proposal for independent review; not executed.** Authority: `author-decisions-20261116` @
`4da73306`; PLAN `R1-TASL7-TRACKP`, `R1-P3A-READY`, `R1-P3A-OOM-OPTION3`, `R1-P3A-BUDGET-CLOCK`,
`R1-E0-*`, `R1-TRACKP-CHOICES`; Track P runbook Phase 5; authorizations
`docs/r1/authorizations/trackp_p3a_20261027.md` and `trackp_p3a_amend_20261104.md`. Readiness report:
`reports/TRACKP_TASL7_READINESS_20261116.md`.

## 1. Why this is the next unit

P.3a attempt 1 (EVIDENCE, 27–29 Oct) is preserved at
`/home/dowling/r1_trackp/runs/p3a_operator_20261027` (journal 81 lines). It completed the short
Kev-0.8B DRYRUN, and E0 screen/select/final/hard/native for all four bases; it completed E6 probes for
`kev-0.8b`, `kev-4b` and `qwen3.5-0.8b-base` (report.json shas `f04df4e1…`, `fae7c9cb…`, `73894af6…`)
and **STOPped** on the `qwen3.5-4b-base` probes unit at 2026-10-29T01:25:17Z with a CUDA OOM in the
descriptive A3 2k/8k history-length loop; total `gpu_seconds_total = 130745.3789889291` = **36.318 GPU-h**
of the 45-h lease STOP and the 60-h cap (attempt 1 included).

The author's **option 3** (`R1-P3A-OOM-OPTION3`, amended authorization) preserves attempt 1, omits the
descriptive 2k/8k A3 rows on any host, and authorizes the **remaining P.3a evidence runs**. The only
remaining P.3a evidence is the **`qwen3.5-4b-base` E6 probes** from the retained attempt-1 `final/saved`.
No P.3b/P.4/P.5/P.6 authorization exists.

## 2. Two reviewed parts

### 2a. Code delta (separate code review required before the run)

`r1/c3/train/exam_run.py:274–280` always executes the descriptive long A3 levels when `--budget` is used.
Option 3 needs a switch that, for this run only, executes **only** the A3 specified rows
(0 / 25 / 50 / 100 % of the remaining token budget at the 1,024-token limit) and omits the 2k/8k
descriptive rows. Proposed minimal change: a new explicit CLI/config flag (e.g. `--a3-short-rows`) that
is refused unless the amendment is cited; tests covering (i) the flag produces only the four specified
rows, (ii) without the flag behaviour is byte-identical to the current code, (iii) the 2k/8k rows are
never attempted when the flag is set. The delta, tests and pinned commit are submitted to an independent
code review; the amendment's **DRYRUN first if the code changed** rule then requires a short Kev-0.8B
DRYRUN in the new attempt root before the probes run.

### 2b. Run plan (this unit)

- **Host:** TASL-7 only, user `dowling`; `flock ~/r1_locks/gpu0.lock`; empty compute census; TASL-7
  host-equivalence PASS (`reports/TRACKP_TASL7_EQUIVALENCE_20261026.md`); driver 580.178.04; no marker.
- **Pins:** paper `trackp-20261026` @ `b9ad6f8f` clean (or the reviewed code-delta commit on top of it,
  recorded); harness `897d83c8` clean; venv freeze matches
  `docs/r1/reports/tasl7_phase2_20261026/pip_freeze_trackp-gpu_tasl7.txt`; `e0_v1` sha `4f4db29b…`;
  rule `p3_rule_v2.yaml` sha `8c0ef908…`; attempt-1 inputs read-only.
- **New root:** `~/r1_trackp/runs/p3a_attempt2_<UTC>/` (must not exist). Attempt 1 is read-only; nothing
  in it is overwritten.
- **Marker:** `~/r1_locks/bin/trackp-evidence begin …` before the run; `end` after; the marker helper
  (sha `f457a04e…`) is installed and matches the committed script.
- **DRYRUN:** short Kev-0.8B DRYRUN under the reviewed code delta, in the new root, before the probes.
- **Probes:** one GPU-producing command:
  `python r1/scripts/trackp.py probes --base qwen3.5-4b-base --head-form linear12 --budget --n-probe 100
  --load <attempt-1-root>/EVIDENCE/qwen3.5-4b-base/final/saved --evidence EVIDENCE
  --run-dir <new-root>/EVIDENCE/qwen3.5-4b-base/probes` (with the A3-short flag), plus the DRYRUN in the
  same new root.
- **Budget:** lease accounting includes attempt 1: **36.318 h used, 8.682 h left** of the 45-h STOP; the
  60-h cap includes attempt 1. Projected probes are <1 GPU-h (prior probe leases 68–148 s); if the
  projection would cross 45 h, STOP before starting (R1-P3A-BUDGET-CLOCK).
- **Outputs:** `journal.jsonl`, `gpu_lease_log.jsonl`, per-unit `manifest.json`/`report.json`, the
  attempt-2 probes report; the P.3a report `docs/r1/reports/TRACKP_P3A_<date>.md` + appendix figure data;
  every result records its serialisation/template version (amendment condition).
- **STOPs:** any pin/hash/freeze mismatch; hostname/reboot/driver mismatch; an owner process, marker or
  foreign GPU job; OOM/CPU fallback persists; non-finite metric; budget rule; any change to the protocol,
  rule, e0 set or A3 specification; attempts to run 2k/8k rows; attempts to re-run attempt-1 units or
  another base's probes. STOP = preserve, report, no retry/recovery.

## 3. Gates still open before execution

| Gate | Owner / record | Status |
|---|---|---|
| Host-equivalence | `TRACKP_TASL7_EQUIVALENCE_20261026.md` + review | PASS |
| Env freeze/driver/disk/lease | readiness report §1–2 | PASS at check |
| Authorization notes | 27 Oct + 4 Nov amend | present |
| Code pin clean; harness clean | `b9ad6f8f` / `897d83c8` | PASS |
| **A3-short code delta** | new code unit + independent review | **OPEN** |
| **M13 template-version inventory** | `MAC_M13_TEMPLATE_INVENTORY_20261105.md` | **OPEN** — attempt-1 per-run manifests must be inspected/provided; template pin still `TODO_VERIFY` |
| **A6 probe** | spec `§5.6` / `exam_run.py` | **OPEN/ambiguous** — option 3 says A6 quantifies the difference; A6 is only "(proposed)" and unimplemented; needs a reviewed unit or author decision |
| Independent review of this plan | this document | required before execution |
| STOP 5 review of the P.3a report | after run | required |

## 4. Must not

- No P.3b/P.4/P.5/P.6, no labels/seeds 7006–7010, no real tables, no sweep-2 tables (D8 lock); no change
  to `p3_rule_v2`, `e0_v1`, thresholds, A3 spec or protocol; no re-run of attempt-1 screen/select/final/
  hard/native/probes or another base; no 2k/8k rows; no other host; no Jev/DeepSeek/API; no file deletion
  (move aside only); no claim of acceptance; no merge/push to `main`.

## 5. Review and execution record

An independent reviewer checks these exact bytes, the code delta, the command, the budget accounting and
the STOP list; on acceptance the unit is executed under the operator runbook, the outputs are preserved,
the P.3a report is written, and STOP 5 review follows. No execution before acceptance.
