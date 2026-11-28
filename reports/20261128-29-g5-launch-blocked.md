# compute/20261128-18 — G.5 launch stopped at the signed note's own launch binding

**Result: STOP before any job. The note names `paper_commit a70c8872`, but the publication merge `d5d83198`
also carries the D.3 step (8) code, so LB A's "tree equal to the paper commit outside `docs/` and the spec"
cannot hold on any published commit at or after `d5d83198`. A docs-only clean base is ready:
`compute-g5-launch-base-20261128` @ `2178bc6e`. The coordinator merges it; the launch then starts from its tip.**

- Task `compute/20261128-18` (G.5 launch, `compute/20261126-06`); authority R1-G5-SIGNATURE (2), the published
  note, R1-HOST-FREE, R1-NO-TIMEOUT. Round base `origin/main` `d6696f29`; note publication `d5d83198`.
- Note `docs/r1/authorizations/c3_t1_labels_20261128.md` sha256
  `4000c1dbe0ff4930dde80ef1c5e822dc37be5b8dc9692a8784560b40203b4f59` (`approved: true`);
  spec `sweep2/t1_tasl/g5_tasl_spec.json` sha256
  `7dcc581573f84044495006865ff3e6966dab3b0e49ad53afff873b7e41dfaa4e`.
- Clean checkout `d5d83198` on TASL-2 (`/home/dowling/r1_tracks/t1_tasl/paper_g5_20261128`); no job id exists
  because nothing was submitted.

## Checks

| Check (TASL-2, clean `d5d83198`) | Result |
|---|---|
| `g5_tasl.py validate … --launch` | rc 0 |
| `g5_tasl.py check-note …` (strict) | rc 0, `{"ok": true, "K": 10, "mode": "strict"}` |
| launch binding: `git diff --quiet a70c8872 HEAD -- . ':(exclude)docs/' ':(exclude,literal)sweep2/t1_tasl/g5_tasl_spec.json'` | **rc 1** (9 files, 120+/54−) |
| `G5_TASL_ENABLE_REAL=1 g5_tasl.py run … --node mlab_cifar10 --job campaigns-wave1 --enable` | **STOP:** the launch checkout differs from the paper commit outside `docs/` and the spec |

The strict note check passes; the launch binding is a separate, literal condition. The nine files are D.3 code
(`r1/c3/d3/assemble.py`, `d3_hpo_ref.py`, `d3_outcome_table.py`, `r1/scripts/d3_smoke_engineering.py`) and G.5
test fixtures. No G.5 measurement code differs, but the binding does not admit an exception. The STOP occurred
after the earlier switch checks (note, decision rows, host records, CUDA-IPC acceptance, G.4b pilot basis,
REL-T1-G1B copy, noise pre-check, xc3, freeze wait, pin check, family checkout, measurement path), so those
pass; only the launch-tree equality fails.

## Prepared clean base

`compute-g5-launch-base-20261128` @ `2178bc6e1d6ae9e2c58fbe57ca42b955dc09dd8a`:

- base `6466e044` (`Record independent tier-E acceptance of the G.5 render`), an ancestor of `origin/main`;
- the published signed note bytes copied unchanged from `d5d83198`; spec unchanged at `7dcc5815…`;
- `git diff --quiet a70c8872 HEAD -- . ':(exclude)docs/' ':(exclude,literal)sweep2/t1_tasl/g5_tasl_spec.json'`
  returns **0**; `validate --launch` and `check-note` both return rc 0 on this tree;
- documentation only: no code, spec, decision or signed value changes.

Record `docs/r1/reports/g5_launch_base_20261128/G5_LAUNCH_BASE_20261128.md` sha256
`0ea2edc5a6aa58c89637db55cec946d83f85c5046898f48826f9c5584c225e82`; `SHA256SUMS` binds the four captures
(`checkout_state.txt`, `validate_launch.txt`, `check_note_strict.txt`, `launch_attempt.txt`).

**Review/merge:** documentation only; the coordinator's check suffices (R1-AUTONOMY (3)). The note, the spec and
every signed choice are unchanged, so no author re-signature is needed. A different remedy — re-rendering the
note/spec with a new `paper_commit` — changes a signed binding field and would need the author; it is not
proposed here.

## What happens next

1. The coordinator verifies and merges `compute-g5-launch-base-20261128` into `main`.
2. Compute launches from that branch's **tip** `2178bc6e`, not from the merge commit: a merge into current
   `main` keeps the later D.3 code and would fail the same check. At the tip, HEAD is published (an ancestor of
   `origin/main`), tracked-clean, holds the committed spec and the signed note on `main`, and equals `a70c8872`
   outside `docs/` and the spec.
3. Then the launch runs `validate --launch`, starts the TASL-7 proposer (`serve`), and takes the node order in
   the note (`mlab_cifar10` first), reporting job ids per node/wave and GPU-hours against 425.

No GPU was used, no job was submitted, and TASL-2/TASL-7 were idle at the read (TASL-2 353 MiB display,
TASL-7 44 MiB, no Paper B process).

Decided alone: the clean base `6466e044`, copying the published note bytes unchanged, and stopping before any
job. No signed value, code, spec or note content changed.
