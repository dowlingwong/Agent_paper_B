# D.3 G1 charged-run snapshot core — independent tier-E review

**Reviewer:** fresh, independent tier-E reviewer; I did not write this unit. Read-only on the reviewed branch
`compute-d3-g1-snapshot-20261127` @ `51cf07f76c261fa34a0fb3f1d8f623fb978a6030` (merge base with `origin/main`
`6684e840`). This review record is on `compute-d3-g1-core-review-20261127`, based on `origin/main`
`5c901d19`; the reviewed branch is not merged into it. No campaign, audit, label, evaluation, GPU or evidence
run was made. I read no test/evaluation partition and no sealed label. The only writes were this record and
synthetic probe files outside the repository tree.

Verdict: CHANGES REQUIRED

The core mechanism is close: charged-run counting, exact-`w` live snapshots, atomic writes, no-overwrite, the
skip path, the charge-time parity STOP, `final.json` at the actual `w`, and the 16 synthetic tests all work. Four
of the gate's explicit requirements are nonetheless not met: the parity check is absent at the E0/E1/E2 hooks
(condition 1); the required no-controller-call assertion is absent and verify snapshots overwrite the E1 state
with the E2 state (condition 3); the controller projection uses an object-id `repr` fallback (condition 4); and
the chunk's revision-6b hardware refusals are defined but not wired into `run_chunk` (and are fail-open on
missing fields). The first two are gate conditions and block merge. There are also layout gaps against design
revision 6b.

## 1. Authority read

- `canon/README.md`, `canon/COMPUTE.md`, `canon/PAPER_B_PLAN.md` §4–§5; PLAN §10 rows `R1-AUTONOMY`,
  `R1-NO-TIMEOUT`, `R1-D3-DECOMP`, `R1-D3-OUTCOMES2`, `R1-D3-ORDER`.
- Coordinator task `tasks/compute/20261127-04-d3-hook-decision.md` (option 1, four conditions), read on
  `origin/coord/coordinator`.
- Accepted design `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_20261126.md` revision 5b (§2.2 snapshot
  contract, §3.3) and its acceptance review `D3_G1_G6_DESIGN_REVIEW_R6_20261126.md`.
- Launcher design revision 6b `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_REV6_LAUNCHERS_20261126.md`
  (on `compute-d3-launcher-design-20261126`, accepted by `D3_G1_G6_LAUNCHER_REV6B_REVIEW_20261127.md`).
- D.3 pre-declaration revision 4 `docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md` §7.5/§8 (Y(w),
  `r1_d3_outcome/v2`) and its unit record `docs/r1/reports/d3_predecl_r4_20261127/D3_PREDECL_R4_20261127.md`.
- Harness `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, in a clean reviewer-side worktree. The checkout normally
  named by `AR_HARNESS_ROOT` was at `897d83c8` (an ancestor), so I created a clean worktree at the pin for the
  tests below; both harness trees were exercised for the 16 new tests.

## 2. The four coordinator conditions — explicit PASS/FAIL

| # | Condition (task `compute/20261127-04`) | Result | Evidence |
|---|---|---|---|
| 1 | Wrapper run count equals `ComputeBudget`'s worker-run counter at every harness hook (E0, E1, E2) and at campaign end; any difference fails closed | **FAIL** | The hook path records but never checks parity. `r1/c3/d3/snapshots.py:297-303` calls `observe_budget(..., where=f"hook {ctx.epoch}")`; `snapshots.py:315-324` calls `check_parity` only when `where == "consume_worker_run"`. `snapshots.py:341-349` is the only check. Only `campaign_chunk.py:191-194` checks at the end of a campaign. A direct probe (`observe_budget` with `worker_runs=7` at `hook E1`, wrapper count 0) raised nothing. |
| 2 | Only budget-charged runs are counted; a rules skip charges no worker run; a repeated attempt is charged as revision 4 says | **PASS** | `CountingWorker.run_trial`/`run_trial_at_seed` count exactly one per harness call (`snapshots.py:448-458`); the harness charges exactly once per such call, including a call that raises (`campaign.py:1669-1683` at the pin) and once per seeded verify run (`campaign.py:726-743`). An E1 skip never reaches the worker. `test_skip_charges_no_worker_run` passes; `test_exact_w_snapshots_include_a_verify_block` shows the seeded runs counted individually. No retry logic exists in the unit, so no lost attempt is charged (revision 4 §3.1). |
| 3 | Snapshot controller state is the last E1-hook state; assert no controller call between that hook and the run; E1 capture before the decision; verify carries the same state with `pending_action=verify` | **FAIL** | `snapshots.py:305-313` builds a fresh `_TrialState` at **every** non-E0 hook, so the E2 hook (`campaign.py:1848-1860` at the pin, after the main run) overwrites the E1 state. `controller_calls_at_e1` is recorded at `snapshots.py:268,312` and is never read (no assertion). `note_decision` sets `pending_action` (`snapshots.py:327-331`) but does not verify the call count. Independent probe with a stateful controller: trial 2's E1 hook was state `n=4`; the `w5` verify snapshot carried the E2 state `n=5` and `pending_action=verify`. Thus verify snapshots do not carry the E1 state, and a revise path can have more than one controller call between the E1 hook and the run with no failure. |
| 4 | The hashed controller projection is documented and deterministic (no object id, time, set iteration or other nondeterminism), and a controller without `snapshot_state()` is handled as the design requires | **FAIL** | The projection is documented (`snapshots.py:118-145`) and is deterministic for the known `RuleController` fields (`_plan_state`, sorted mappings/sets). But `_jsonable` falls back to `{"repr": repr(value)}` at `snapshots.py:95-100`; two logically identical controllers whose `log`/`_pending`/`_plans` contains an unhandled object hash to different values (independent probe: `False`). The docstring admits this is not a serialisation claim. A `repr` with an object address is neither deterministic nor replayable, and the code does not refuse such a controller. |

## 3. Findings

### B1 (BLOCKING) — no parity check at E0/E1/E2; the required invariant is not asserted at the named hooks

`SnapshotRecorder.__call__` (`r1/c3/d3/snapshots.py:297-303`) passes `where=f"hook {ctx.epoch}"` to
`observe_budget`. `observe_budget` (`snapshots.py:315-324`) stores `_last_budget` and the observed `llm_calls`,
then calls `check_parity` **only** if `where == "consume_worker_run"`. The E0/E1/E2 hooks therefore never compare
`self.count` with `ctx.compute_budget.worker_runs`. The end-of-campaign check exists only in
`campaign_chunk.py:191-194` (`if recorder._last_budget is not None and recorder._last_budget.worker_runs !=
w_final`), and only in the chunk shell; a caller that uses `wrap()` directly with `run_real_campaign` (as the
unit's own tests do) has no end check either.

The probe `observe_budget(fake(worker_runs=7), where="hook E1")` returned without an exception while `count=0`.
The two parity tests (`r1/tests/test_d3_g1_snapshots.py:165-179`) exercise the charge path and the direct
`check_parity` call, not the hooks. This is exactly the condition the coordinator said replaces the missing
per-run harness callback. The charge-time check is valuable and catches a block charge at the charge, but the
required hook guard is missing.

### B2 (BLOCKING) — condition 3 is not implemented: no assertion, and verify snapshots carry the E2 state

At every non-E0 hook the recorder replaces `_trial` (`snapshots.py:305-313`), including `controller_state_sha256`
at line 309. The harness order at the pin is E1 hook (`campaign.py:1534-1547`), E1 decision
(`campaign.py:1560`), main run, E2 hook (`campaign.py:1848-1860`), E2 decision (`campaign.py:1868`). A main-run
snapshot is written inside the worker wrapper before the E2 hook and therefore carries the E1 pre-decision state;
a verify snapshot is written after the E2 hook and carries the E2 state. The E1 decision has already mutated a
stateful controller (for `RuleController`, `_plans[b]` is filled in the E1 decision), so these states differ.

The independent probe used a controller whose `snapshot_state()` returns a counter that increments on every
`decide`. The decision sequence at trial 2 was E1 with `n=4`, E2 with `n=5`; the `w5` verify snapshot carried
`n=5`, not the E1 value `n=4`. The unit record (`D3_G1_UNIT_20261127.md:26-27`) says "The E1 state is captured
before the E1 decision, as the design says; verify runs carry the same E1 state with `pending_action=verify`."
The first clause is true for main runs; the second is false for verify runs.

The condition also requires an assertion that no controller call occurred between the captured hook and the run.
`_TrialState.controller_calls_at_e1` is written at `snapshots.py:268` and `312` but has no reader. The harness can
call the controller more than once between the E1 hook and the run on a revise path (E1 decision, optional E1b
rescreen at `campaign.py:1649`), and the code would record the stale state without failing. A correct guard would
compare `_controller_calls` with the captured value plus the known E1 decision, or refuse any unexpected call.

There is also a contract ambiguity to settle explicitly: design revision 5b §2.2 (line 65) says the hash covers
the serialised state **after the run and before its decision**; coordinator option 1 says the state captured at
the last E1 hook (before the E1 decision). The implementation follows the coordinator's wording for main runs
and the design's wording for verify runs, so it satisfies neither reading uniformly. The fix should state which
state is authoritative and make every snapshot (main and verify) use it.

### B3 (MAJOR) — controller projection is not deterministic for an unhandled object

`_jsonable` (`snapshots.py:77-100`) sorts mappings and sets and handles `to_dict()`, but its final fallback is
`{"repr": repr(value)}` (line 100). The projection includes arbitrary controller fields (`_pending`, `log`;
`snapshots.py:137-144`), so an object without a JSON form is hashed through its default `repr`, which contains
the object id. A controller without `snapshot_state()` can therefore produce a different
`controller_state_sha256` for the same logical state in two processes, and the snapshot cannot be replayed against
the same state as design §2.2 requires. The independent probe constructed two `C` objects with identical fields
and `log=[Weird()]`; the hashes differed.

For the actual `RuleController` projection the code is deterministic (fields are numbers, strings, lists and
sorted dicts), so this is not a claim that the D.3 arms necessarily hash object ids today. The generic contract
and the "documented and deterministic" condition are nevertheless not met. Either refuse an unhandled object with
a STOP, or require `snapshot_state()` for controllers that cannot be projected exactly; a `repr` fallback must
not silently enter the hash.

### B4 (MAJOR) — revision-6b hardware refusals are defined but not wired into `run_chunk`, and are fail-open on missing fields

`check_hardware` (`r1/c3/d3/campaign_chunk.py:127-146`) is never called by `run_chunk`
(`campaign_chunk.py:165-230`); `run_chunk` has no observed-hardware parameter. The only run-time check is the
manifest model-source sha (`campaign_chunk.py:173-175`). The unit record line 18 says the chunk shell implements
"the revision-6b hardware/proposer/lease/memory refusals"; the test at `test_d3_g1_chunk.py:146-157` calls
`check_hardware` directly, so the wiring is not tested.

Even the helper is fail-open:
- model and proposer are compared only when both sides are non-empty (`campaign_chunk.py:134-141`), so a missing
  observed value passes;
- the lease is refused only when it is exactly `False` (`:144-146`), so a missing lease passes;
- memory is refused only on `"fail"` (`:142-143`), so a missing check passes;
- there is no instance-model claim across arms and no `campaign_model_source` check inside `check_hardware`
  (revision 6b §3 requires both).

Revision 6b says a detected model mismatch, a missing lease and insufficient memory are placement refusals. A
launcher that trusts `run_chunk` would run on a mismatched card. This must be wired fail-closed before the chunk
is used for a D.3 campaign.

### B5 (MAJOR) — chunk layout is incomplete against design revision 6b

Design revision 6b §2 and §3 require, per campaign, `campaign.json`, `ledger.jsonl`, `runs.jsonl`, the snapshots,
`summary.json` and `SHA256SUMS`, and require `launch.json`/`chunk.json` to carry the hardware record (GPU model,
UUID, driver, memory, memory check, other-process count/memory, proposer expected/observed/check, request/scope,
environment freeze, start/end, status, model check). The unit writes `campaign.json`, the harness ledger, the
snapshots and `SHA256SUMS` (`campaign_chunk.py:196-205`), but no per-campaign `runs.jsonl` and no per-campaign
`summary.json`; the only summary is chunk-level (`campaign_chunk.py:219-228`). The chunk record
(`campaign_chunk.py:208-217`) carries `hardware` and `notes` as free-form mappings and omits the named revision-6b
fields. The unit record calls this the "launcher-neutral chunk shell" and defers the adapter, but the missing
per-campaign files and the absent hardware schema are part of the launcher contract, not the adapter.

The declared ledger root `(<run_root>/<stage>/<arm>/r<rep>/<instance_id>/)` and record name
`<stage>__<arm>__<instance_id>__r<rep>` are also not produced: `run_chunk` uses `<out>/campaigns/<instance_id>`
and `campaign.json` has no `record_name`. The unit record §4.2 acknowledges the separation remains for the
adapter; I treat that specific item as future-unit scope, but the file set and hardware fields above are in this
unit's claimed layout.

### M1 (MINOR) — `final.json` at `w=20` is not a true alias of `w20.json`

`write_final` (`snapshots.py:411-426`) recomputes a payload with `_payload(w=20, final=True, ...)` and adds
`alias_of`/`alias_sha256`. The recomputation uses the `_trial` current at call time, which for a campaign that
reached 20 is the E2 state after the E2 hook, not the E1 state used for `w20.json`. Independent probe: the
`controller_state_sha256` values differ (`w20` `36198c69…`, `final` `d17386ed…`) while the incumbent is equal and
`alias_sha256` equals the `w20` digest. G6 reads the incumbent and start configs, so the primary Y is not
affected, but the record is not the alias the design and the unit record describe. Either copy the `w20` payload
verbatim and add the final fields, or name it a separate record at `w_final=20`.

### M2 (MINOR) — the test does not exercise "w=5 through the four seeded runs"

`test_exact_w_snapshots_include_a_verify_block` places verify at trial 2, so the verify block is `w=3..6` and
`w=5` is the third seeded run (the test comment says this). A verify at trial 1 does produce `w=5` as the fourth
seeded run (independent probe: `count=5`, `w5` `run_kind=verify`, `pending_action=verify`), so the code satisfies
the requirement; the unit record line 19 and the test do not actually demonstrate the four-run case.

### M3 (MINOR) — `note_decision` accepts `llm_calls` and ignores it

`RecordingController.decide` passes `decision.llm_calls` to `note_decision` (`snapshots.py:473-476`), but
`note_decision` (`:327-331`) only increments a counter and stores the action. The module docstring says
`llm_calls` is the last hook value plus the controller's own calls for the decision in flight; in practice the
value comes from `observe_budget` on `consume_llm_call`. This is a documentation/accuracy issue unless a
controller reports calls without consuming the budget.

### M4 (MINOR) — environment note: the default harness checkout is not at the pin

The unit record names `AR_HARNESS_ROOT` at `a3fedbbd…`, but the shared checkout I found was at `897d83c8`
(an ancestor; `a3fedbbd` is its descendant). I ran the 16 tests at both and the full suite at a clean
`a3fedbbd` worktree. The exact command in the unit record should force the pin, not rely on the shared checkout.

## 4. What passes

- **Exact-`w` live snapshots.** `note_run` (`snapshots.py:334-338`) writes at the exact count; no reconstruction,
  no imputation. At `W=20` every `w∈{5,10,15,20}` is written, including a `w5` reached by a seeded verify run.
- **No overwrite / atomic writes.** `_write_snapshot` refuses an existing path or a second write
  (`snapshots.py:402-409`); `_atomic_write_json` writes a sibling temp, flushes/fsyncs and `os.replace`s
  (`snapshots.py:198-207`). `write_final` refuses an existing `final.json` (`:415-417`).
- **`final.json` actual-w semantics.** At `w_final<20` it records the actual `w`; at `w=20` it records `w=20` with
  `alias_of="w20.json"` and the correct `alias_sha256`; the `w=0` path uses the start config
  (`snapshots.py:356-373`, tested at `test_d3_g1_chunk.py:167-173`).
- **Block charge stops at the charge.** `ParityBudget.consume_worker_run` constructs the new budget, calls
  `observe_budget(..., where="consume_worker_run")`, and raises `SnapshotParityStop` before returning when the
  wrapper count differs (`snapshots.py:246-251`, `315-324`, `341-349`). `test_parity_budget_fails_closed_without_a_wrapper_count`
  passes.
- **Rules skip charges no run.** `test_skip_charges_no_worker_run`: W=6 with one skip gives five runs and only
  `w5.json`.
- **No evidence/label/audit read.** The unit reads only node editable paths for the config projection
  (`snapshots.py:187-195`); it never opens an audit, label, evaluation, split or sealed file. No evidence run
  was made.
- **No pinned file changed.** The diff `6684e840..51cf07f7` adds six files and changes none: `r1/c3/d3/__init__.py`,
  `snapshots.py`, `campaign_chunk.py`, two test modules and the unit record. SHA256SUMS in the chunk tree covers
  the files it lists (test at `test_d3_g1_chunk.py:115-118`); inner SHA256SUMS files are excluded from the outer
  tree, which is normal.
- **Test suite.** See §5; 16 new tests pass and the full-suite failing-id list is identical to base.

## 5. Tests run and environment

Command (branch tip `51cf07f7`, clean worktree), with `AR_HARNESS_ROOT` pointing at a clean worktree of the pin
`a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`:

```
V=/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/d3venv
AR_HARNESS_ROOT=<a3fedbbd worktree> \
  "$V/bin/python" -m pytest -q -p no:cacheprovider \
  r1/tests/test_d3_g1_snapshots.py r1/tests/test_d3_g1_chunk.py
```

- New tests: **16 passed** (10 in `test_d3_g1_snapshots.py`, 6 in `test_d3_g1_chunk.py`). Also 16 passed when
  run against the shared `897d83c8` checkout, so the unit does not depend on a pin-only API in these tests.
- Full `r1/tests`, same venv, clean pin worktree, one run at a time, fresh `TMPDIR` each:

| Tree | Commit | Result |
|---|---|---|
| base | `origin/main` merge base `6684e840` | **100 failed, 4328 passed, 161 skipped, 3 errors** (633.63 s) |
| tip | `51cf07f7` | **100 failed, 4344 passed, 161 skipped, 3 errors** (786.59 s) |

The sorted FAILED/ERROR id lists are identical: 103 ids each, sha256
`e6f2073eb1adeafb5438af19d88bb9e8ad97666a009d029961b6c5ccbad70880`. The only difference is **+16 passed**, the new
tests. **Zero new failing ids; none removed.** The unit record's absolute counts (102 failed / 4342 passed) differ
by two from this run, an environment difference; the zero-new-failure claim is confirmed independently.

Environment: Python 3.12.8, pytest 9.2.0, NumPy 2.5.5, torch 2.15.0; harness pin `a3fedbbd` clean. No GPU, no
campaign, no evidence run, no label/evaluation read.

Independent probes (not committed; outside the repository tree, run against the tip and the pin):
1. Hook parity: `observe_budget(fake(worker_runs=7), where="hook E1")` with wrapper count 0 raised nothing.
2. Verify-state: stateful controller at trial 2; E1 hook `n=4`, E2 hook `n=5`; `w5` snapshot carried `n=5`,
   `pending_action=verify`.
3. `final` alias: `w20` and `final.json` controller states differ while the incumbent is equal.
4. Repr fallback: two equal controllers with `log=[Weird()]` hashed differently.
5. Verify-at-trial-1: `W=5` produced `w5.json` with `run_kind=verify`, `pending_action=verify`, i.e. the fourth
   seeded run.

## 6. Scope and what was not reviewed

**In scope:** the six-file diff; the snapshot contract and counting/parity/projection code; the chunk shell's
layout, refusals and SHA256SUMS; the unit record's claims; the 16 tests; the full-suite comparison; the four
coordinator conditions.

**Explicitly out of scope (not reviewed, not accepted or rejected here):** the full G1 adapter (real node specs,
`gemma4_31b` manager, per-arm factories, `A0/A0R/A1/A2/A3/A5/A6` controllers, real record names and ledger-root
separation); G6 and the Y/Y(w) audit; FIXR3 and EGATE and their design revision 6c; the verify-seed rule and the
P10/P14 seed disjointness check; the A1/A2/LADDER constants file and the signed pre-declaration; the two
launchers (`launch_ssh.py`, `launch_htcondor.py`); `d3_analysis.py` and the `r1_d3_outcome/v2` builder; the
screening measurement; and any evidence, test-label or evaluation read. The "four-way outcome reading" of the
pre-declaration is not used as a code requirement in this unit; only the snapshot/audit fields that G1 emits were
checked.

## 7. Required corrections before merge

1. Check parity inside every E0/E1/E2 hook (not only at `consume_worker_run`) and fail with `SnapshotParityStop`
   on any difference; add a test that injects a mismatch at each hook.
2. Implement the no-controller-call assertion: record the controller-call count at the E1 capture, compare it at
   the run, and fail closed on any unexpected call (including the revise/E1b path). Make verify snapshots carry
   the same chosen E1 state as main snapshots, with `pending_action=verify`, or change the contract explicitly and
   document which state is authoritative.
3. Remove the `repr` fallback from the hashed controller projection, or refuse a controller whose state cannot be
   projected deterministically; add a test with an unhandled object.
4. Wire the revision-6b refusals into `run_chunk` with observed hardware and a fail-closed check for missing model,
   proposer, lease, memory and instance-model claim; test the refusal through `run_chunk`, not only
   `check_hardware`.
5. Complete the per-campaign `runs.jsonl`/`summary.json` and the named revision-6b hardware fields in
   `chunk.json`/`launch.json`, or state explicitly which subset this unit owns and which later unit adds them;
   the current unit record overstates the layout.
6. Make `final.json` a true copy of the `w20` payload at `w=20` (or give it a distinct name), and correct the
   unit record's "four seeded runs" test claim and the `llm_calls` docstring.

## 8. Review-file hash

The final line below is excluded from its own hash. To reproduce:

```
sed '/^Review record sha256:/d' docs/r1/reviews/D3_G1_SNAPSHOT_CORE_REVIEW_20261127.md | sha256sum
```

The committed git blob hash and the report to the coordinator give the file's own identity after commit; the
value below is the hash of the review text with this line removed.

Review record sha256: 624ed610aef7fd5193349952fa9fdd89638e4e5d488f67f472c37b7836f03d0f
