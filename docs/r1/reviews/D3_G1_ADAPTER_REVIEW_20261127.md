# D.3 G1 adapter — independent tier-E review

**Reviewer.** Fresh, independent tier-E reviewer (subagent). I did not write the reviewed unit, the adapter,
its tests, the `campaign_chunk.py` change or the constants artifact. I read the reviewed branch read-only: no
campaign, audit, GPU job, server, label, evaluation, test partition, sweep table or sealed file was read or
run. The only writes are this review file and a scratch worktree under the session's temporary directory.

**Target.** `origin/compute-d3-g1-adapter-20261127` @
`25b0a355281bb1384fc1af2f06e089a2cafd6e47`, one commit on base `origin/main` `98c571d2` (no
force-push). Unit record: `docs/r1/reports/d3_g1_20261127/D3_G1_ADAPTER_20261127.md`. Authority: the D.3
pre-declaration revision 4 §14 (W = 20, `llm_call_cap` = 80, `trial_budget` = 80,
`memory_mode` = `append_only_summary`, `verify_runs` = 2, `verify_seed_base` = 20000,
`verify_split_policy` = `vary`, harness `9bb416805175149eb87b71f28d77530572aa4bce`, the seven `d3_nodes`
and the seven `d3a_arms`), the G2 constants artifact
`docs/r1/reports/d3_g2_20261127/d3_constants.json` (sha256
`4f5f686be8f0210bcb27dfe0968296d68cf54e7266fb72c9038e741163776a93`, verified), the G1/G6 design and
revision 6c for the FIXR3/EGATE unit.

---

Verdict: CHANGES REQUIRED

---

## Summary

The manifest, constants, controller and manager-selection half of the unit is largely right. The manifest's
W, cap, trial-budget, memory-mode, verify, harness, node and arm values are read and a contradicting value
is refused; A1/A2 use the constants file's own vectors; the noise
table supplies `sigma_cmp`; LADDER re-derives `eta = c * sigma_node`; A3/A5/A6 are refused without a frozen
prior; the harness factory and the callable `ended_on` change are sound. I did not find a silent arm or
seed substitution in the harness-arm path.

The FIXR3/EGATE replicate unit, however, **does not run at this tip**. `run_trial` references
`ManagerProposal`, which is imported only in the local scope of `propose`, so every replicate worker run
raises `NameError`; `run_replicate_campaign` catches it as a failed `RunOutcome`, so a FIXR3 campaign burns
its runs as failures instead of executing the fixture worker. EGATE additionally raises `AttributeError` on
the first proposal because `EgateEngine` has no `incumbent_metrics`. The only replicate-arm test asserts an
end state that is identical for the intended six successful 3-run steps and the buggy eighteen failed 1-run
steps, so it passes both before and after the fix, and there is no EGATE test. The replicate validation also
does not enforce the node's active keys, contrary to revision 6c §3.5.

## What I checked

- The full `98c571d2..25b0a355` diff (`adapter.py`, `campaign_chunk.py`, `test_d3_adapter.py`, the unit
  record), the unit record against the diff, and the accepted precedent units.
- **Manifest pins (a).** `load_manifest` refuses a changed `W`, `llm_cap`, `trial_budget`, `memory_mode`,
  `verify_runs`, `verify_seed_base`, `verify_split_policy`, schema, harness commit, node set/order and arm
  set; it also refuses a changed proposer model/schema/temperature/thinking flag and a non-http(s) base
  URL. The four pinned files are hashed (`check_pinned_files`); `check_harness` refuses a dirty or different
  harness checkout. I compared the hard-coded values with §14 and the four file sha256s with the files on
  the reviewed tip.
- **Arms (b).** A0 = `ContinueController`; A0R = `d3_controllers.a0r_controller` with its rule layer on;
  A1/A2 = `TableArmPrior` over the constants file's A1/A2 vectors (`AC.vectors_of`), with `sigma_cmp` from
  `dataset.noise_table` and the A1 fallback; LADDER = `d3_controllers.ladder_controller` with the file's
  `c`; `load_constants` cross-checks each `sigma_node` against the noise table and each `eta` against
  `ladder_eta(c, sigma_node)`. FIXR3/EGATE are refused by the harness factory; A3/A5 are refused without
  an injected `LearnedArm`; A6 is refused even with one. I verified the constants artifact's vectors,
  `sigma_node` and `eta` against the file.
- **Manager (c).** `proposer.model` must be `gemma4_31b`, the schema `manager_proposal/v1`, the
  temperature `0.2` and `thinking` exactly `False`; `LangGraphManager` is built with
  `llamacpp/<alias>`, the manifest temperature and repetition. `apply_proposer_environment` sets
  `LLAMACPP_BASE_URL` from the manifest and refuses most existing values that differ.
- **Replicate unit (d).** Read `make_replicate_factory` against revision 6c §3: the incumbent config is
  restored before each proposal; `validate` applies `features.apply_edit` to the config contents and
  returns `snapshots.config_sha256`; `run_trial` makes one worker call and does not charge the counter or
  the budget; the engine owns the charge. I checked the engine interfaces and the loop's catch of a raising
  `run_trial`.
- **`ended_on` (e).** The `campaign_chunk.py` diff keeps the fixed-string path: a non-callable value must
  be in `ENDED_ON` before the run, a callable is resolved after `run_real_campaign`, and the resolved value
  is checked against `ENDED_ON` before the final record. The existing chunk tests and the A0 whole-chunk
  test cover both paths.
- **No evidence (f).** `adapter.py` reads only the constants, noise summary, pre-declaration and split
  files, by path and sha256; `noise_table` calls `refuse_sealed`; no label, evaluation, test partition,
  server, GPU job or evidence run is started. The tests use a deterministic fixture manager and a fixture
  worker.

## Blocking findings

### B1 — every FIXR3/EGATE worker run raises `NameError` (`r1/c3/d3/adapter.py:643`, import at `:606`)

`propose` does `from autoresearch.manager.base import ManagerProposal, ManagerStatus` locally (`:606`), so
`ManagerProposal` is local to `propose`. `run_trial` (`:643`) uses the name and resolves it in the module
globals, where it does not exist. `run_replicate_campaign` wraps `unit.run_trial(...)` in
`try/except Exception` (`r1/c3/d3/replicate_campaign.py:225-241`) and converts the exception to a failed
`RunOutcome`, so the campaign does not crash: it charges and records failed runs.

Evidence at the reviewed tip: a FIXR3 chunk with the unit's `ToggleManager`/`FakeWorker` records 18
attempts per campaign, **0 successful**, with `cause = "NameError: name 'ManagerProposal' is not defined"`,
`j = {0}` and 18 steps; the campaign ends `no_fundable_candidate` at `w = 18`. After adding the top-level
`ManagerProposal` import in a scratch copy (no other change), the same chunk records 18/18 successful runs,
`j = {0,1,2}` and the intended six 3-run steps. Both replicate arms are non-functional as committed.

Fix: import `ManagerProposal` at module scope (the local import in `propose` can then be reduced to
`ManagerStatus`), and add an assertion that a replicate run actually succeeds.

### B2 — EGATE proposals raise `AttributeError` (`r1/c3/d3/adapter.py:608-609`)

`propose` evaluates `state.engine.incumbent_metrics` on every proposal. `Fixr3Engine` has that attribute
(`None` before the first keep), but `EgateEngine` does not (`r1/c3/d3_replicate.py:180-188`: `gate`,
`instance_seed`, `maximize`, `seeds`, `incumbent`, `steps`). A chunk for arm `EGATE` therefore fails on the
first proposal with

```
AttributeError: 'EgateEngine' object has no attribute 'incumbent_metrics'
```

before any worker call. With a scratch `getattr(state.engine, "incumbent_metrics", None)` and the B1 import,
the EGATE chunk completes 18 campaigns (20 runs each) and ends `worker_runs`; the only EGATE-specific
failure is this attribute.

Fix: use `getattr(..., None)` or an arm-specific `current_best_metric` for EGATE (the engine keeps its
incumbent runs in the `ChargedRunCounter`, which the adapter does not see; `None` is acceptable for the
manager status), and add an EGATE chunk test.

### B3 — replicate validation does not enforce the node's active keys (`r1/c3/d3/adapter.py:621-630`)

Revision 6c §3.5 requires "Validate the proposal against the node's active keys exactly as E1 does."
`validate` only checks that `structured_edit` is a dict and that `features.apply_edit` succeeds.
`apply_edit` (`r1/c3/features.py:146-159`) checks that the path is an editable file and that the assignment
exists and is not stale; it does **not** check that the symbol is in `spec_node.editable_symbols` or in the
openml active-key set for the current `model_type`. The pinned manager's `_extract_structured_edit` resolves
against `current_constants`, which the adapter builds from `editable_symbols` (`:604-605`), not from
`resolve_active_keys`; for an openml node an inactive key such as `max_depth` under a logistic
`model_type` is in `editable_symbols`, so a proposal naming it would be applied and run, whereas the
harness E1 would reject it as an inactive key.

Fix: in `validate`, reject an edit whose symbol is not in `spec_node.editable_symbols` or not in
`resolve_active_keys(spec_node, config)` (or reuse the harness's `inactive_key_in_proposal`), and add a
test with an inactive key.

### B4 — the only replicate test cannot detect B1/B2; no EGATE test (`r1/tests/test_d3_adapter.py:230-246`)

`test_replicate_chunk_runs_fixr3_and_uses_table_ended_on` asserts
`summary["ended_on"] == {"no_fundable_candidate": 18}` and `final["w"] == 18`. Those values are the same
for the intended six successful 3-run steps (18 runs) and for the buggy eighteen failed 1-run steps (18
runs): the engine stops at `< 3` left in both cases. The test never asserts a successful attempt, the
`j = 0,1,2` pattern, the six-step count or `FakeWorker.calls`; the comment "3 seeded runs per step: six
complete steps" is therefore not tested, and there is no EGATE case. The unit record's claim that the test
exercises the fixture worker is false at this tip.

Fix: assert every attempt's `success`, `steps == 6`, `j == {0,1,2}` and the expected `FakeWorker.calls`
(e.g., 18 seeds x 6 steps x 3 runs per campaign); add an EGATE chunk test. The accepted
`r1/tests/test_d3_g1_replicate.py:45-49` already shows the right assertions (`len(summary["steps"]) == 6`,
`len(summary["attempts"]) == 18`).

## Non-blocking minors

- **Model file / alias / thinking are not hard-pinned.** `load_manifest` requires a 64-hex
  `proposer.model_sha256` (`:215`) but does not compare it with the pre-declaration's
  `2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75`; `alias` is only non-empty, and
  `thinking=False` is checked but not passed to `LangGraphManager` (the design's
  `{"enable_thinking": false}` is a server chat-template setting). The launcher must verify the served GGUF
  and the `enable_thinking` setting; hard-pinning the sha and the alias here would close the gap.
- **`apply_proposer_environment` URL comparison (`:281`)** uses `str.rstrip("/v1")`, a character set, not a
  suffix. A contrived existing value such as `http://127.0.0.1:80951/v1` compares equal to the manifest's
  `http://127.0.0.1:8095/v1` and is silently replaced; the manifest value is what is used, so no wrong
  server is reached, but the "refuses a contradictory value" claim is not exact. Use `removesuffix("/v1")`
  or parse the URL.
- **Unit-record counts/sha.** The record says the focused set is 285 passed and the tip full suite 4924
  passed; I observe 286 focused (11 new + 275 existing) and a tip full suite of 105 failed / 4928 passed /
  161 skipped / 3 errors. The author's tip log (`adapter_tip_suite.log`, 05:26) predates the commit
  (05:39) and matches a 10-test adapter file; the base log is 05:38. The author's base and tip FAILED/ERROR
  id lists are identical (111 ids), but the record's sha
  `971166036fa365bcb10f01f051c756a7b90c1e94e0b0c1637bedcbd28b7c1f19` does not reproduce from the two logs;
  the sorted, deduplicated `FAILED`/`ERROR` lines hash to
  `826c73490f5ce27d8acf4b3f8b9edcf41b5fec7e8fb457eb95aec2d500411ee1` (identity holds). My tip run has
  the author's 111 ids minus three environment-dependent failures (see Tests below), so the "zero new
  failures" conclusion holds, but the counts and the sha in the record are stale. Correct them and rerun at
  the committed tip.
- **Learned seam (`:381-389`).** `build_controller` checks `arm in learned` but not `entry.arm == arm`, so
  `learned={"A3": LearnedArm("A5", prior)}` would silently use A5's prior for A3; there is no digest check on
  the injected `PriorModel`, and `campaign_kwargs` sets `verify_runs = 2`, overriding `entry.verify_runs`.
  Add `_require(entry.arm == arm, ...)` and carry the digest/verify setting; this is a later-unit seam.
- **Replicate factory scope checks (`:578-584`).** Unlike the harness factory, it does not check
  `spec.stage == manifest.stage` or `node in manifest.nodes`; the arm check and the constants lookup cover
  most of it, but add the two checks for symmetry.
- **Error types.** `load_manifest` and `load_constants` can raise raw `ValueError`/`KeyError` for a
  non-numeric `W`, an off-grid LADDER `c` or a missing field instead of `AdapterStop`; they fail closed, but
  not with the declared error.
- **Unused import.** `D3_RULE_LAYER` (`:59`) is imported and not used.
- **Stage b arm set (`:229`).** A stage-b manifest must contain `A6` because `D3B_ARMS` is
  `ARMS_D3B_WITH_A6`, while §14 makes A6 conditional (`a6_entered`); this unit runs no stage-b arm, but a
  later stage-b launcher will need the conditional set.
- **`ended_on` wording.** The resolver is used by the harness factory only; the `no_fundable_candidate`
  end of FIXR3/EGATE comes from `run_replicate_campaign`'s own `table_ended_on`, not from this resolver.
  The unit record's sentence conflates the two. The resolver also cannot return `stop`/`error`
  (`table_ended_on` raises below W and below the cap); no D.3 controller currently stops, so this is
  acceptable, but a future stopping controller would need a path.

## Tests I ran

Worktree at `25b0a355`, `AR_HARNESS_ROOT=/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/harness9bb`
(`9bb416805175149eb87b71f28d77530572aa4bce`, clean), Python 3.12.8, pytest 9.2.0:

- `r1/tests/test_d3_adapter.py`: **11 passed** in 2.04 s.
- The ten-module focused set in the unit record: **286 passed** in 6.98 s (the record says 285).
- Full `r1/tests` with `--continue-on-collection-errors`: **105 failed, 4928 passed, 161 skipped,
  3 errors**, 71 subtests, 734 s (0:12:14), 108 `FAILED`/`ERROR` ids. The author's base/tip logs are 108
  failed / 4914 or 4924 passed / 161 skipped / 3 errors with identical 111-id lists; my tip log has the
  author's list minus three environment-dependent tests
  (`test_b1_real_worker_determinism.py::test_b1_real_worker_run_is_seed_deterministic`,
  `test_c3_audit.py::test_real_worker_run_is_seed_deterministic`,
  `test_rerun2_batch4c.py::test_dryrun_start_refuses_external_batch_before_log_write`), all of which pass
  here. No adapter test fails and no new failure id appears. The +14 passed over the author's base log is
  the 11 new adapter tests plus the three environment-dependent passes.

The blocking probes: a FIXR3 chunk at the tip records 18/18 failed attempts with the `ManagerProposal`
`NameError`; a scratch top-level import makes 18/18 succeed with six 3-run steps; an EGATE chunk at the tip
raises the `incumbent_metrics` `AttributeError`; a scratch `getattr` plus that import completes 18 EGATE
campaigns.

## Independence

I am a fresh, independent reviewer and did not write the reviewed unit or any of its files. I did not
modify the author's branch or worktree, did not merge or touch `main`, and did not run a campaign, server,
GPU job, or read a label, evaluation, test or sealed file. My only writes are this review file, the new
review branch, and a scratch worktree under the session's temporary directory.
