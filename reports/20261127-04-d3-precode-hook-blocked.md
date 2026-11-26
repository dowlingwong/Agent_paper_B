# Report — D.3 G1/G6 pre-code check: the per-charged-run snapshot hook is not at the pinned harness

**Task:** `cluster/20261126-02` with `compute/20261126-02`.
**Result: BLOCKED before code — one design-level decision needed.** No G1/G6 code was written, because the first
required pre-code check fails at the harness pin the design names. The accepted design itself says the block-charge
case stops for an author decision; no block charge is implemented.

## The check

The accepted design (`docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_20261126.md`, revision 5b, sha256
`4b95798659c13feeef02af02504d68f138e40cdaf056ded0b89a09fbcc4e3a23`, accepted by
`docs/r1/reviews/D3_G1_G6_DESIGN_REVIEW_R6_20261126.md`) requires, at §3.3:

> the hook is a **G1 runner-level charged-run hook implemented in the reviewed G1 code** (action: after each charged
> worker run) and increments `w` by exactly 1 per charged run … Verify has r = 2 pairs, hence **`2r = 4` separate
> charged runs**, each charged singly … a pre-code check verifies the hook/action is present at that pin in the
> cluster checkout **before** code. If a controller or harness can only charge a block, code stops for an author
> decision; no block charge is implemented.

The launcher revision 6b (`docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_REV6_LAUNCHERS_20261126.md`, sha256
`0d696535d94395c85592c7ac9483790483966bbe0bf48961d132c50aa49b922d`, review ACCEPTED FOR CODE) does not change this
requirement.

## What the pin exposes

- Pin: `r1/scripts/HARNESS_PIN_C3` = `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` (file sha256
  `750a10b5f6e5a4dbf7c87fdac341e5e1b3e93d64340ba8c1b41d145c8a1e6e9c`); checkout
  `/Users/wongdowling/Documents/autoresearch_harness` at that commit.
- `src/autoresearch/control_plane/campaign.py` at the pin, sha256
  `9ac5e724c4fa9a0ef0521bd2e751d06916d3dce2d0e4b1360d9ad97df9d172e4`:
  - `_invoke_snapshot_hook` is called at **three** places only: E0 (line 1343), E1 before the trial run (line 1534)
    and E2 after the trial and its verify block (line 1848). There is no per-run callback.
  - `_run_verify` (lines 685–813) runs the candidate and incumbent at each verify seed and calls
    `compute_budget.consume_worker_run()` after **each** of those runs (lines 731 and 743), i.e. 2r = 4 charged runs
    for r = 2, but the next `snapshot_hook` call is E2.
  - The main trial's `consume_worker_run` is at line 1683; the next hook is E2.
- `src/autoresearch/control_plane/budget.py` at the pin, sha256
  `de8eeae790ad866f71f38e6ab0e0b6864ccca1619d19a1607f1a94b3a213cd41`: `consume_worker_run` increments the counter
  by one per run, so the counter is exact; only the callback granularity is missing.

Consequence: with r = 2 verify, one E2 hook sees `w` jump by 5 (1 main + 4 verify runs). A G1 hook driven only by the
harness callback cannot write live `w = 5, 10, 15, 20` snapshots at exact charged-run counts. Writing them from the
E2 state would be a reconstruction, and the design forbids inventing w points.

## Options for the coordinator/author

1. **Confirm a G1 worker-wrapper hook (recommended, no harness change).** G1 wraps the worker passed to
   `run_real_campaign`, counts every `run_trial`/`run_trial_at_seed` call, and writes the snapshot immediately after
   the run at each exact w. The controller state for the snapshot is captured at the E1 hook (no controller call
   occurs between E1 and the main run; the state is unchanged through a verify block). This is a "G1 runner-level
   hook implemented in the reviewed G1 code" and needs only the worker API present at the pin, which it is. It should
   be confirmed in the G1 unit review, because the design's pre-code sentence can also be read as requiring a
   per-run harness callback.
2. **A new reviewed harness pin** with a per-run callback that carries run identity and the controller state.
3. **Amend the snapshot contract** to allow E2-block snapshots and imputed w points. This changes the accepted
   design and the pre-declaration; it is an author item and not recommended.

I did not implement (3), and I did not write a block-charge runner. No G1 or G6 branch exists for this task.

## G6 status

G6 (the Y and Y(w) audit) is not started. It reads the G1 snapshots, so it waits for the snapshot contract to be
settled. Its schema also depends on D.3 pre-declaration revision 4 (`r1_d3_outcome/v2`, `y_raw_w`), which is on the
local worker's branch `mac-d3-predecl-r4-20261127` at `f85b3c88`, not on `main`; the revision-4 record itself says
the G7 outcome-table builder is missing. Nothing in G6 was written or run.

## What happens next

The coordinator decides between options 1–3 (option 1 is a short review confirmation; option 2 is a harness change;
option 3 is an author decision). After that, G1 code and the G6 unit can proceed. The four expansion G.1b jobs,
houseprice and the G.5 note are independent and are reported separately.

**Decided alone:** to stop before code rather than wrap the harness in an unreviewed way, because the design names
this as the pre-code condition and forbids a block charge. No pin, design, spec, note, label or evidence file was
changed. No GPU job or evidence run was made.
