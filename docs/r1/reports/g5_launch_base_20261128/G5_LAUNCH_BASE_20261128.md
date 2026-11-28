# G.5 launch base — the signed note on a clean launch commit

**Task `compute/20261128-18`. Result: the published `main` at `d5d83198` cannot satisfy the signed note's own
launch binding; this branch places the published note bytes on a docs-only descendant of `6466e044`, whose code
already equals the note's `paper_commit` `a70c8872` outside `docs/` and the spec. The coordinator merges this
branch; the launch then starts from its tip.**

- Base `6466e044` (`Record independent tier-E acceptance of the G.5 render`), an ancestor of `origin/main`.
- Note bytes copied unchanged from `d5d83198:docs/r1/authorizations/c3_t1_labels_20261128.md`
  (`sha256 4000c1dbe0ff4930dde80ef1c5e822dc37be5b8dc9692a8784560b40203b4f59`).
- Spec unchanged from `6466e044`: `sweep2/t1_tasl/g5_tasl_spec.json`
  (`sha256 7dcc581573f84044495006865ff3e6966dab3b0e49ad53afff873b7e41dfaa4e`), the digest the note names.
- Code equality: `git diff --quiet a70c8872 HEAD -- . ':(exclude)docs/' ':(exclude,literal)sweep2/t1_tasl/g5_tasl_spec.json'`
  returns 0 on this branch.
- Documentation only; no code, spec, note content, decision or signed value changes.

## What was checked on the published merge

A clean checkout of `d5d83198` in `/home/dowling/r1_tracks/t1_tasl/paper_g5_20261128` (TASL-2):

| Check | Result |
|---|---|
| `g5_tasl.py validate … --launch` | rc 0 |
| `g5_tasl.py check-note … --note …` (strict) | rc 0, `{"ok": true, "K": 10, "mode": "strict"}` |
| `git diff --quiet a70c8872 HEAD -- . ':(exclude)docs/' ':(exclude,literal)sweep2/t1_tasl/g5_tasl_spec.json'` | **rc 1** |
| `G5_TASL_ENABLE_REAL=1 g5_tasl.py run … --node mlab_cifar10 --job campaigns-wave1 --enable` | **STOP**: the launch checkout differs from the paper commit outside `docs/` and the spec |

The strict note check passes because the note, the spec and the PLAN rows are on `main`. The launch binding
(`g1b_tasl.verify_launch_tasl`, LB A) additionally requires the checkout's tree to equal the note's
`paper_commit` (`a70c8872`) outside `docs/` and the spec. Merge `d5d83198` also carries the D.3 step (8)
code from `f3273a50`; the difference is nine files, all D.3 code and G.5 test fixtures:

```
 r1/c3/d3/assemble.py               |  4 +--
 r1/c3/d3_hpo_ref.py                |  2 +-
 r1/c3/d3_outcome_table.py          | 16 +++++----
 r1/scripts/d3_smoke_engineering.py |  4 +--
 r1/tests/g5_spec_fixtures.py       | 47 ++++++++++++++++++++++++
 r1/tests/test_d3_integration.py    |  2 +-
 r1/tests/test_d3_outcome_table.py  | 21 ++++++-----
 r1/tests/test_t1_g5_seal.py        |  5 +--
 r1/tests/test_t1_g5_tasl.py        | 73 ++++++++++++++++++++++----------------
 9 files changed, 120 insertions(+), 54 deletions(-)
```

No G.5 code is affected, but the note's binding is literal. No assertion was relaxed, no request edited, no
job submitted, and no GPU was used.

## Why this branch

`6466e044` is the reviewed G.5 render acceptance, an ancestor of `origin/main`; its tree equals `a70c8872`
outside `docs/` and the spec, and its spec is the published `7dcc5815…`. It carries the unsigned note. Replacing
only that note with the published signed bytes gives a commit that satisfies every term of the note's launch
binding once the coordinator merges it. This preserves the signature: the note bytes, the spec and every
signed choice are unchanged.

## After the merge

Launch from this branch's tip (the second parent of the merge), not from the merge commit: a merge of this
branch into current `main` keeps the later D.3 code and would fail the same check. The tip is published (an
ancestor of `origin/main`), tracked-clean, holds the committed spec and the signed note on `main`, and equals
`a70c8872` outside `docs/` and the spec.

## Captures

`checkout_state.txt`, `validate_launch.txt`, `check_note_strict.txt`, `launch_attempt.txt`; `SHA256SUMS` binds
them and this record.

Decided alone: the clean base `6466e044`, copying the published note bytes unchanged, and stopping the launch
before any job was submitted. No signed value, code, spec or note content changed.
