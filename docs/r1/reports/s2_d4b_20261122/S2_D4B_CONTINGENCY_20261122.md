# Sweep-2 audit: the D4 option-B contingency (E5 partial labels), implemented and kept OFF

Prepared by the Mac-desk agent (Claude), AI-assisted, 22 Nov 2026, on `mac-s2-d4b-20261122` over published `main`
`9c2979a2`, for item 1 of the queue of 22 Nov 2026 (01:22). This is desk work: synthetic data only, and no label or
evaluation file of a real audit was opened. Revision 2 answers review round 1 (findings 1–11, table at the end).

## Authority

R1-SWEEP2-B2-DECISIONS decided D4 A (a non-finite seed run is a STOP, as in the sweep-1 B.2 audit) and adds:

> "Contingency: the Mac agent implements D4 option B (R1-BX-PROPOSED-CONFIRM REVISIONS (c), partial labels) now, as an
> independently reviewed code path that stays unused; it may be used only after a D4 STOP and a further author row."

REVISIONS (c) (E5) reads:
- divergence is "a non-finite loss, or no metric at the fixed budget";
- a divergent proposal enters no belief bin, is counted separately, and has the action target u = −g;
- if only some seeds diverge, μ comes from the rest and the label is marked partial;
- more than half diverging makes the proposal divergent;
- a heavy-tailed node uses a Student-t, declared before labels are built.

The signed sweep-2 preregistration (`docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`) decided PRE-DIV A
for the evaluation seeds and pins the gate-input builder by sha256 (`gate_input_builder_sha256: f67ee5e7…`). That
builder already defines the shapes of partial and divergent label and evaluation rows; the contingency writes those
shapes.

## What changed

**`r1/c3/audit_d4b.py` (new).** The module docstring has the full rules.

- `check_contingency` enables the path only after a D4 A STOP and with its author row:
  - the stopped audit is a sweep-2 EVIDENCE audit output inside the paper root, reached through no symlink, not
    completed, not itself a contingency audit, whose `STOP.json` reason is a seed-run STOP
    (`invalid audit result for <node>/<config>`);
  - PLAN §10 on `origin/main` holds exactly one dated author row **`R1-SWEEP2-B2-D4B`**, found with
    `release.author_rows` (fenced and quoted text ignored), naming the sweep-2 run id, "R1-BX-PROPOSED-CONFIRM
    REVISIONS (c)" and the sha256 of that `STOP.json`. No such row exists today.
- `is_divergent` reads divergence narrowly, so that no infrastructure failure becomes a label. A divergent seed run
  changed no file, ended without a finite metric, and either:
  - exited 0 (it ran to its end; a NaN or inf metric line does not parse), or
  - exited with code 1, with no `FAILURE_CATEGORY` or `runtime_error`, and its recorded log tail names a non-finite
    value (`nan`, `inf`, `infinity`, `non-finite`, `not finite`; whole words).
  Everything else stays a STOP, as under D4 A:
  - exit 2 or `invalid_config`, any other exit code;
  - a signal (a negative code, or 128 and above, such as an OOM kill);
  - a timeout, a worker exception, a changed file;
  - a failed run whose log cannot be read.
- `block_label` and `blocks` apply E5 per role block (label seeds 7001–7005 and evaluation seeds 7006–7010, each on
  its own), in the frozen builder's shapes:
  - 3 or more of the 5 candidate runs divergent makes the proposal divergent in that block:
    - label `label_kind: divergent`, with `delta_label`, `se_label` and `soft_parameters` null;
    - evaluation row with `divergent_seeds`, `k_evaluation` = 5 − their number, and no value (PRE-DIV A: r = −g ×
      execute);
    - the action-target rule `u = -g` is recorded once, in the completion's counts;
  - otherwise (at most 2 divergent) the value is the paired mean over the other seeds:
    - a partial label is `label_kind: audit` with `soft_parameters.k_label` = 3 or 4;
    - a partial evaluation row carries `divergent_seeds` and `k_evaluation`;
    - a complete row is exactly D4 A's row, with no extra key;
  - **an incumbent's divergent run is a STOP**: E5 speaks of the proposal's runs, and the builder has no field for an
    incumbent's divergence (see "For the author row").
- `counts` counts labels (divergent, partial, complete, rule_noop) and evaluation rows (divergent, partial, complete)
  separately.
- `diagnostics` records the worker's failure category and, for a failed run, the last 4,000 characters of its log
  in the run row. It does so only under the contingency; D4 A rows are unchanged.
- The Student-t clause is not implemented, because no node is declared heavy-tailed.

**`r1/c3/audit.py`.** The hooks are inert by default:
- `run_config(..., continue_on_divergence=False)`:
  - the seed rule is factored into `_seed_ends_config`, and D4 A's rule is unchanged;
  - under the contingency the rows carry the diagnostics, and after a divergent run the remaining seeds of that
    configuration run in a fresh copy of the node; the used copy is kept beside it, renamed `<node>.diverged_seed<N>`.
- `evidence_run(..., d4b_after_stop=None)` and CLI `--d4b-after-stop`, sweep 2 only:
  - the contingency check runs before anything else, so without the row nothing is written;
  - the stopped audit's `STOP.json` is copied into the new audit as `d4b_stopped_STOP.json`;
  - the environment and completion carry a `d4b_contingency` record (row sha256, STOP sha256; the completion adds
    the counts);
  - the completion schema is `r1.c3_audit_completion/5`;
  - a STOP raised while the blocks are built (an incumbent's divergence) writes `STOP.json`.
- `verify_evidence_completion` re-checks the record with `recheck_contingency` and then re-derives both blocks under
  E5. The default path is unchanged and runs in the same order.
  - `recheck_contingency` checks the STOP copy inside the audit, and that the author row on `origin/main` hashes to
    the same row sha256.
  - So the stopped directory can later be archived. The row's text, however, must stay as signed: a later edit of
    the row makes the audit unverifiable, which fails closed.
  - After the run, the recorded `stopped_audit` path is informational; the STOP's sha256, which the row names, is the
    binding.

**Consumers.** None of them reads a contingency audit as it stands:
- `release_checks.sweep2_integrity` accepts only `/4`; this is tested with the real verifier, which itself passes on
  the contingency audit;
- `release.evidence_tier` treats any other schema as T0, so the sweep-2 release refuses it;
- `sft_data.LabelBlockSource` now refuses `/5`, or any completion with `d4b_contingency`, by name (a raw block and a
  receipted partition alike).

The rows already have the frozen builder's shapes, so the only change needed later is a reviewed change to these three
consumers.

## Tests

`r1/tests/test_c3_sweep2_d4b.py` has 62 tests.

**Divergence reading** (19 cases):
- exit 0 with a NaN or missing metric;
- exit 1 with NaN, `non-finite` or `runtime_error`;
- not divergence: exit 1 without a non-finite word, without a tail, or with an empty tail; `banana`; `invalid_config`;
  exit 2, −6, −9 and 137; a timeout; an exception; a changed file; a valid run.

**Recording and the seed rule:**
- `diagnostics`;
- the seed rule;
- `run_config` with a faked worker: diagnostics in the rows; a fresh node copy after a divergent run, with the used one
  kept; a non-divergent failure ends the configuration; D4 A rows unchanged.

**E5 blocks:**
- complete; partial with k = 4 and k = 3; divergent;
- an incumbent's divergence is a STOP, and the old k = 2 case cannot arise.

**Builder compatibility** (6 cases): the frozen `gate_input_builder._label_ok` and `_evaluation` accept the rows
and read them as complete, partial or divergent. The cases check that:
- the builder file's sha256 equals the preregistration's pin;
- label rows carry only the SFT reader's keys;
- complete rows have D4 A's keys.

**The row and the stopped audit:**
- the row: absent, naming another STOP, given twice, naming another run, only fenced, present;
- refusals: wrong reason or source, completed, itself a contingency audit, wrong path, outside the paper root, a
  symlinked directory (relative and absolute).

**Evidence runs:**
- D4 A: a NaN seed still STOPs; a complete run gives `/4`;
- the contingency:
  - refused without the row, with nothing written;
  - a partial label, with the STOP copy and the counts;
  - an exit 1 NaN failure on the evaluation seeds gives a partial evaluation row;
  - an OOM kill, `invalid_config` or an exit 1 without NaN still STOPs;
  - an incumbent's divergence STOPs, with `STOP.json`;
  - a divergent proposal;
  - sweep 2 only.

**Verification:**
- a positive round trip, which still verifies after the stopped directory is archived;
- refusals:
  - the record in the completion only, or in the environment only;
  - the row withdrawn, or its text changed;
  - the STOP copy changed or missing;
  - the recorded path changed, or the recorded STOP sha changed;
  - the run log changed: a divergent run relabelled as exit 137.

**Consumers:**
- the release check with the real verifier;
- the SFT reader (a `/5` schema, or `d4b_contingency` under `/4`);
- the CLI flag.

Existing tests pass: 297 across `test_c3_audit`, `audit_dryrun`, the five `evidence_*` files, `release`,
`sweep2_audit`, `sweep2_d4b`, `trackp_sft` and `trackp_sft_test_eval`.

## For the author row, if ever needed

The row `R1-SWEEP2-B2-D4B` would name the run id, REVISIONS (c) and the STOP's sha256. Its text should also confirm or
amend two readings that E5 and PRE-DIV A leave open:
1. **Divergence**: exit 0 with no finite metric, or exit 1 with a non-finite value named in the log (no other
   failure category). Every other failure stays a STOP.
2. **An incumbent's divergent run is a STOP.** It is not dropped pairwise. The alternative, recording it in
   `divergent_seeds`, would let an incumbent's failure make the proposal partial or divergent.

Before the labels are used, a reviewed update of the release check, `release.evidence_tier` and the SFT reader is
needed.

## Review round 1: dispositions

| # | Finding | Disposition |
|---|---|---|
| 1 | Rows do not match the frozen gate-input builder; k = 2 possible | Rows now use the builder's shapes. Label: `audit` with `k_label`, or `divergent`; no foreign keys. Evaluation: `divergent_seeds` plus `k_evaluation` only when not complete. Incumbent divergence is a STOP, so k ≥ 3. A test runs every case through `_label_ok`/`_evaluation` and checks the builder's pin. |
| 2 | Divergence too broad | Narrowed to exit 0, or exit 1 with a non-finite log signature and no other category. Rows record `failure_category` and `log_tail`. Exit 2 / `invalid_config`, signals, other codes and an unreadable log STOP. Named for the author row. |
| 3 | No test of verify on `/5` | Positive round trip and eight refusals added. The release check is tested with the real verifier. |
| 4 | Incumbent rule not surfaced | Incumbent divergence is now a STOP, listed for the author row. |
| 5 | `sft_data` accepts any completion prefix | `/5` and `d4b_contingency` refused by name in both load paths; tested. |
| 6 | Symlinked stopped audit followed | Every path component is checked for symlinks; absolute paths outside the paper root are refused with a clear message; tested. |
| 7 | Evaluation counts missing | `counts(labels, evaluations)` counts both blocks. |
| 8 | Verification depends on outside state | The STOP bytes are copied into the audit, and verification no longer needs the stopped directory. The dependence on the row's exact text is documented. |
| 9 | A contingency STOP qualifies | A stopped audit whose environment has `d4b_contingency` is refused. |
| 10 | Reused node directory after a crash | A fresh node copy for the remaining seeds after a divergent run; the used copy is kept, renamed. |
| 11 | Test gaps | Failed-run rows in the evidence fixture, the CLI flag, and the absolute and symlink cases are tested. |
