# Reviews: the D.3 controller units (card local/20261126-05 item 1), 27 Nov 2026

**Reviewers.** Two independent tier-E reviewers (Claude subagents, AI-assisted), neither of whom wrote the units. One reviewed A0R, G8, FIXR3, EGATE and LADDER; the other reviewed G7 and G9. Both worked read-only in fresh worktrees, which were removed afterwards. They opened no credential, label, test-partition or evaluation file.

**Record.** The local worker transcribed this from the reviewers' hand-backs.

**Stack** (on `mac-d3-predecl-r4-20261127` @ `6412b843`):

| Unit | Commit |
|---|---|
| A0R | `f81739c8` |
| G8 | `e775b38c` |
| FIXR3 | `2d4e9cf2` |
| EGATE | `871d4712` |
| LADDER | `222de37a` |
| G7 | `e33abaef` |
| G9 | `98bf9a72` |

**Corrections.** Commits `c56e94f4` (code and tests) and `4ecbbb3d` (reports) sit on top of the top branch `mac-d3-g9-sidecar-20261127`. The lower branches are unchanged, so the top branch carries every fix.

**Tests.**

| Round | Units | Result |
|---|---|---|
| 1 | A0R–LADDER | 216 passed |
| 1 | G7–G9 | 47 passed |
| Re-check | A0R–LADDER | 222 passed |
| Re-check | G7–G9 | 67 passed |

The extra probes confirmed the §5.5 thresholds: 0.0468 commits at 7 pairs and 0.0467 does not; 0.039 commits at 8 pairs and 0.038 does not. All 121 LADDER grid values round-trip.

## A0R (G11): accepted (round 1 accepted with minors; minors resolved)

**What was checked.** §5.1b and R1-D3-DECOMP:
- At E1, a rule no-op or duplicate is skipped with no run charged, no-op first, as A2's `RuleController` does.
- Everything else is executed once, with `default/v1` (keep iff Δ̂ > 0).
- There is no screen, forecast or verify.
- The constants come from `d3_analysis`.
- The rule-layer switch is explicit and refuses a value outside `RULE_LAYER_ARMS` (§13 item 21, as built).

**Tests.** A twin test against `RuleController`; A0's ledger is reproduced up to the first skip.

**Minors** (round 1):
1. `campaign_kwargs` admitted overrides of the split policy, W and cap.
2. The report did not say that featurisation runs, with errors swallowed, when the rule layer is off.
3. The suite commit references were wrong.

All three are resolved: `d3=True` binds 20, 80 and 80 and refuses `verify_split_policy`.

**Note.** Running A0 under `RuleLayerController(rule_layer=False)` is a G1 choice. It is level 0 only if the G1 review confirms the A0 ledger stays the sweep-2 design.

## G8 run accounting: accepted (round 1 accepted with minors; minors resolved)

**What was checked.**
- `campaign_usage` charges each charged replicate and never charges a reused incumbent. It fails closed on malformed or duplicate entries.
- `ChargedRunCounter` is the single W counter: steps are refused before they start, `OverBudget` is a STOP, and there are snapshot hooks.
- Re-issued LLM calls are never counted (R1-NO-TIMEOUT (1)). This is a contract that G1 must emit.
- `table_ended_on` equals `d3_analysis._check_ended_on`, cross-checked.
- `classify_worker_failure` is R1-CARD-SHARE's literal card condition. The §13 item 31 switch is off as built.

**The `ended_on` precedence conflict is real.** The G1/G6 design §3.3 puts `llm_call_cap` above `worker_runs`; the pinned analysis requires `worker_runs` at runs = W. G8 correctly follows the analysis, and the design text must be corrected when G1 is built.

**Minors.**
- Resolved: `MAX_REPLICATE_J` is now imported, and `charge` validates j.
- Not done, and acceptable: optional minor 2, checking each replicate seed. `campaign_usage` does not know the instance seed, so G1 or G7 may add it.

## FIXR3 (G3 decision engine): accepted as the engine only (round 1 accepted with minors; minors resolved)

**What was checked** (§5.4):
- r = 3 on j = 0..2, with the seeds from `replicate_seeds`.
- Each run is charged singly. An unfundable step ends as `no_fundable_candidate`.
- The first valid trial is kept without a test.
- The incumbent is never re-run.
- Any failed replicate gives `failed_invalid`.
- Zero variance on both sides: no keep, and the case is counted.
- The memory line is the replicate mean.
- Welch's test is checked against scipy. Reading "rejects" as p ≤ α is level 0.

**Scope.** G3 is not complete until the harness route for controller-issued replicate runs is reviewed. That route is a pre-declaration-level choice. Running the replicates "in the runner around the harness trial" departs from §5 and needs a revision before signature.

## EGATE (G4 decision engine): accepted as the engine only (round 1 accepted with minors; minors resolved)

**What was checked** (§5.5):
- `PaceStyleGate` with (0.1, 0.05, 8) only, action `verify:pace`.
- Pairs at j = 0..7. The candidate runs first, and the incumbent runs only if it has no run at that seed.
- The failure rules, and the §5.5 numbers.

**Minors** (all resolved):
- The incumbent's run is looked up again after the candidate's run, so an identical candidate reuses it (tested).
- Only `PaceStyleGate` itself is accepted.
- The test expectations are exact, and the boundary values are the declared ones.

**Scope.** G4 waits for the same harness-route unit as G3.

## LADDER (G5): accepted (round 1 accepted with minors; minors resolved)

**What was checked** (§5.6):
- Every proposal is executed (rule layer off, by the switch).
- `bayes_threshold/v1` uses a carrier `KeepPrior(mu=-η, tau=1, sigma=1)`, so t* = η exactly over the whole grid. The keep rule is Δ̂ > η, strictly.
- c = 0 reproduces A0.

**Minors** (resolved):
- The constructor now takes `c` (an off-grid η is impossible).
- The override gap is closed.

**Requirement.** G2 writes c, and G1 passes it.

## G7 outcome table (v2): accepted (round 1 accepted with minors; minors resolved)

**What was checked.**
- `ended_on` comes through G8, plus the HPO-REF rules.
- `y_raw_w` is null exactly for unreached w; nothing is imputed.
- The w = 20 snapshot is the same audit as the final one.
- `last_improving_run` comes from the keep audits, with a strict comparison.
- The mechanism counts.
- Any incomplete campaign refuses the whole stage.
- `a6_entered` is read only from the signed note.
- `validate_table` runs on the result, the write uses exclusive create, and a full 882-row synthetic D.3a table runs through `analyse`.

**Minors** (resolved):
- `refuse_input_path` is applied to the inputs and the output.
- A partial file is unlinked on a failed write.
- An executed trial without an E1 rule-flag record is refused.
- The integer checks and `last_keep_run` checks are added.

**Open before signing:** one sentence in §7.5 (d) saying that "keeps" includes the first valid trial.

**Contracts for G1/G6:** they adopt `r1_d3_campaign_summary/v1` and `r1_d3_audit_row/v1`. The HPO-REF runner must log the E1 rule flags, or fill those counts another way.

## G9 A5/A6 sidecar: accepted with minors (round 1 NOT ACCEPTED; re-check accepted with minors)

**Round 1, B1 (blocking).** At a fixed 1 s timeout, a re-issue without limit livelocked whenever the sidecar answered more slowly than the timeout. This was reproduced on the unit's fake sidecar: 25 re-issues and no answer.

**Re-check: B1 fixed.**
- A forecast is one connection with a connect guard only, then no read limit; the request is sent once.
- While waiting, the client writes `sidecar_waiting` progress records.
- Ending a stall is the operator's or G1's job (R1-NO-TIMEOUT (1), (4)).
- The test delays every call beyond the poll interval.

**Round-1 minors 1–6** (resolved):
1. Malformed answers fall back. Only a well-formed answer with the wrong digest is a STOP.
2. The wait fields reach the ledger through `D3SidecarRuleController`.
3. Every `OSError` and `HTTPException` is now `SidecarLost`.
4. The URL must be `http`, loopback, with an explicit port.
5. The `fallback_stop` docstring and caller contract are fixed.
6. The unused constant is removed.

**Residual minors.**
- G1 must persist the `on_progress` records.
- A non-200 reply from a foreign service on the port is classed as a fallback.

**Before signing:**
- The author confirms the failure rule: draft row R1-D3B-SIDECAR-FAILURES, `d3_sidecar_failures/v2`, level 2.
- One sentence each in §6 and §10.
- §13 item 16, the sidecar image, stays open.

Verdict: ACCEPTED (A0R, G8, LADDER, G7). ACCEPTED as engines only (FIXR3, EGATE). ACCEPTED WITH MINORS (G9).
