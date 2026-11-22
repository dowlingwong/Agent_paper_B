# Sweep-2 audit: the D4 option-B contingency (E5 partial labels), implemented and kept OFF

Prepared by the Mac-desk agent (Claude), AI-assisted, 22 Nov 2026, on `mac-s2-d4b-20261122` over published `main`
`9c2979a2`, for item 1 of the queue of 22 Nov 2026 (01:22). This is desk work: synthetic data only, and no label or
evaluation file of a real audit was opened.

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

## What changed

**`r1/c3/audit_d4b.py` (new).** The module docstring has the full rules.
- `check_contingency` enables the path only after a D4 STOP and with its author row:
  - the stopped audit is a sweep-2 EVIDENCE audit output, not completed, whose `STOP.json` reason is a seed-run STOP
    (`invalid audit result for <node>/<config>`);
  - PLAN §10 on `origin/main` holds exactly one dated author row **`R1-SWEEP2-B2-D4B`**, found with
    `release.author_rows` (fenced and quoted text ignored), naming the sweep-2 run id, "R1-BX-PROPOSED-CONFIRM
    REVISIONS (c)" and the sha256 of that `STOP.json`. No such row exists today.
- `is_divergent` is the operational reading of divergence: no file changed, no finite metric, and the training
  process ran to its end (exit 0 without a finite metric, or `exit code N`). A timeout, a worker exception or a
  changed file stays a STOP.
- `block_label` and `blocks` apply E5 per role block (label seeds 7001–7005 and evaluation seeds 7006–7010, each on its
  own):
  - 3 or more of 5 candidate runs divergent makes the proposal `divergent` in that block: no soft label,
    `delta_label: null`, and the action-target rule `u = -g`;
  - otherwise the label is `audit_partial`, computed from the pairs where neither run diverged, with `k_label` and the
    diverged seeds recorded;
  - fewer than 2 usable pairs is a STOP.
- The Student-t clause is not implemented, because no node is declared heavy-tailed.

**`r1/c3/audit.py`.** The hooks are inert by default:
- `run_config(..., continue_on_divergence=False)`. The seed rule is factored into `_seed_ends_config`, and D4 A's
  rule is unchanged.
- `evidence_run(..., d4b_after_stop=None)` and CLI `--d4b-after-stop`, sweep 2 only:
  - the contingency check runs before anything else, so without the row nothing is written;
  - the environment and completion carry a `d4b_contingency` record (row sha256, STOP sha256, counts by kind);
  - the completion schema is `r1.c3_audit_completion/5`.
- `verify_evidence_completion` re-checks the contingency record against the row and the STOP, then re-derives both
  blocks under E5. The default path is unchanged, in the same order.

**Consumers.** The release integrity check and the label readers accept only `/4`, so a contingency audit cannot be
released or read until a reviewed change to those consumers adds divergent and partial labels. This is tested.

## Tests

`r1/tests/test_c3_sweep2_d4b.py` has 22 tests:
- the divergence reading (8 cases) and the run_config seed rule;
- E5 block labels: complete, one or two divergent seeds giving a partial label, three giving a divergent proposal,
  an incumbent's divergence, and fewer than two usable pairs giving a STOP;
- the row: absent; naming another STOP; given twice; naming another run; only fenced; present;
- the stopped audit: wrong reason, wrong source, completed, wrong path;
- the default path:
  - a NaN seed run still STOPs (`STOP.json`, no blocks, no new keyword for run_config);
  - a complete run gives schema `/4` and no contingency key;
- the contingency:
  - refused without the row, with nothing written;
  - with a test row, one NaN seed gives a partial label (k = 4, δ from the rest), schema `/5`, the record and counts,
    and the release check refuses it;
  - three divergent seeds give a divergent proposal;
  - a non-divergent failure still STOPs;
  - sweep 2 only.

Existing tests pass:
- 131 across `test_c3_sweep2_d4b`, `test_c3_sweep2_audit`, `evidence_split_blocks`, `evidence_authorization`,
  `evidence_guards` and `release`;
- also `test_c3_audit`, `audit_dryrun` and `e2_environment_basis`.

## For the author row, if ever needed

The row would name the run id, REVISIONS (c) and the STOP's sha256. Its text should also confirm or amend the reading
of divergence above (exit 0 with no finite metric, or a non-zero exit code; not a timeout). Before the labels are used,
a reviewed update of the release check and the readers for `divergent` and `audit_partial` labels is needed.
