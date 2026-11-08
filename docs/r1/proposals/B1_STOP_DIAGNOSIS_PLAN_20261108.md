# B1 STOP — diagnosis plan, fix routes and restart conditions (proposal, 8 Nov 2026)

**Status.** AI-assisted proposal (Claude, chat session), 8 Nov 2026. It is not evidence and changes no pin, rule, threshold or STOP by itself. The STOP report `reports/B1_STOP_6835_20261108.md` stays authoritative for what happened. Read against `mac-b1-20261107` @ `b06f8a91` (run `6835_20261108_a`, frozen checkout `68357d3d`).


---

## 1. What stopped, in the code

`r1/scripts/exam_runner.py::anchor_gate` runs after the three anchors finish and before any candidate:

1. For `scripted` and `random_valid`, take every audited proposal's `delta_audit` (candidate − incumbent, raw metric, mean over audit seeds 9101–9104).
2. Average per instance (`node__s<seed>`), giving 12 values per anchor (3 nodes × instance seeds 9001–9004).
3. `paired_instance_bootstrap(scripted, random_valid)`: 2000 resamples of the 12 paired differences, seed 20261026, 95 % percentile interval.
4. STOP if `difference_lower ≤ 0`. In DRYRUN the gate is overridden, so **no dry run ever exercised it on real data.**
5. Only after step 4 passes: the 7B duplicate-rate check against the Q2 interval [0.4239, 0.5800]. **This second check has not been evaluated yet.**

The criterion is RUNBOOK X.3 / PORTAL_EXAM_RUNBOOK Phase 5: "random-valid < scripted on audited mean proposal increment … If the exam cannot order the anchors, STOP: it has no discriminating power."

## 2. Hypotheses

| # | Class | Hypothesis | Why it is plausible | What would show it |
|---|---|---|---|---|
| H1 | Design | **Both anchors are random proposers.** `scripted` is `ScriptedRandomManager` (the E1b stand-in): one numeric symbol × a log-uniform factor in [1/3, 3], plus a 30 % categorical switch on OpenML nodes. `random_valid` is uniform over the node's active keys and value grid. Neither is a competent heuristic, and no pilot ever tested that one beats the other. | `r1/headroom/scripted_manager.py` docstring; `r1/exam/campaign.py:226–227` | Point estimate near 0 or negative, consistently across nodes |
| H2 | Metric | **Mean incumbent-relative increment is not monotone in proposer quality.** A proposer that improves faster faces a better incumbent, so its later increments shrink. The mean also depends on how many proposals survive the novelty filter (no-ops and duplicates are excluded). | Per-proposal Δ is relative to the current incumbent; `audited` excludes `active_equals_incumbent` and `active_seen_before` | Increments falling with budget index; different keep counts and audited counts between anchors |
| H3 | Power / scale | **12 instance pairs on a raw metric scale.** Nodes differ in noise and metric scale, so one node can dominate the instance means; the percentile interval on 12 pairs is wide. | `paired_instance_bootstrap` uses raw values; no σ_node standardisation | Point estimate > 0 but interval crossing 0; one node carrying the sign |
| H4 | Engineering | A defect in the B1 path changes anchor results: metric orientation, failed or missing audit seeds, value-grid content, rejected inactive categorical edits counted as trials, the editable-preservation wrapper, the OpenML bootstrap guard, worker-run accounting with W = 20. | Large new B1 code surface since Stage A; the gate never ran on real data | Inconsistent counts, failed audits, sign errors, implausible per-node values |

The classes are not exclusive; the diagnosis reports each separately.

## 3. Diagnosis — read-only steps (½ day)

**Scope and data.** Only the three anchors' existing outputs (36 roots). No candidate has run, so no candidate value can leak. B1 audit seeds are the exam's 9101–9104, not C3's label (7001–7005) or evaluation (7006–7010) seeds, so the C3 seed ban is not touched; confirm this from the run config before reading. **Who does what.** The Mac-local agent (desktop only) does D5 and D6 from the code and writes the read-only diagnosis script for D0–D4, D7 and D8. The experiment agent runs that script on TASL-7 (exit code captured, as in the loader repeat) and sends the capture back; the Mac-local agent turns it into the report. Nothing on the host is modified, signalled, rerun or retired.

| Step | Computation (descriptive only, nothing changes the recorded STOP) | Addresses |
|---|---|---|
| D0 | Inventory: per root, files present, `status`, `execution_label`, audit-cache completeness, `k = 4` on every audited proposal | H4 |
| D1 | Recompute the gate exactly as the code did (point, lower, upper, per-instance differences) and check it reproduces the stop | all |
| D2 | Per node × anchor: trials, worker runs used, invalid, no-ops, duplicates, audited proposals, keeps, final incumbent's in-run metric vs start | H2, H4 |
| D3 | Per node × anchor: mean and median `delta_audit`, share harmful (< 0), and the same divided by the node's σ_node from its D21 noise floor | H1, H3 |
| D4 | `delta_audit` against budget index (first half vs second half of each campaign) | H2 |
| D5 | Metric orientation per node: higher-is-better in the harness metric, sign of `paired()` | H4 |
| D6 | Code diff of the anchor path between Stage A's accepted checkout and `68357d3d` (managers, value grids, worker, wrappers, bootstrap guard), with the value-grid file hash | H4 |
| D7 | The 7B duplicate rate `duplicates / evaluated` against [0.4239, 0.5800] — **the next gate**, computed now so a restart does not stop on it unexpectedly | next STOP |
| D8 | For information only: the same D3 numbers for `qwen25_coder_7b` | §4 options |

**Output.** `reports/B1_STOP_DIAGNOSIS_20261108.md` with the tables, a class verdict per hypothesis (supported / not supported / undetermined), and the raw per-instance numbers in a JSON file. A freshly spawned independent agent reviews it before anything else happens.

## 4. Fix routes by outcome

| Diagnosis outcome | Fix | Needs the author? | Restart scope |
|---|---|---|---|
| **E — an engineering defect (H4)** | Fix the code, add a regression test, independent review of the fix and of the exact new checkout | No, if the fix leaves the X.3 criterion unchanged | New run ID, fresh output tree; all anchors and candidates from the start. The old run stays preserved |
| **P — power only (H3 without H1/H2)**: point > 0, consistent across nodes, interval crossing 0 | (a) standardise by σ_node, or (b) add anchor-only instance seeds | **Yes**: either one changes the criterion after seeing data | As E |
| **D — design or metric (H1 and/or H2)** | Replace the anchor-ordering STOP; options below | **Yes**: one line choosing an option | As E, unless the runner can verifiably reuse the 36 anchor roots |
| **D7 fails** (7B duplicate rate outside the interval) | Report it separately; do not fold it into the fix above | **Yes** | Decided with the author |

**Options for D** (the author picks one; every option is disclosed in the appendix as a post-hoc amendment made after seeing the anchors, listing the original gate and its numbers, as with the A1 amendment precedent):

- **R4 (recommended if D is confirmed).** Drop the anchor ordering as a STOP. Report the three anchors descriptively next to the candidates, keep the 7B duplicate-rate check, and let the frozen B1 rule (x5_rule_v2) carry the ranking. Reason: any new ordering gate chosen after seeing these anchors would not be a real test, and the gate's purpose (that the exam can separate proposers) is better shown by the spread among the 15 candidates than by two random proposers.
- **R1.** Keep the ordering, on σ_node-standardised increments. Only sensible if D3 shows a clear standardised gap that the raw scale hid; then it is the P route.
- **R2.** Order `random_valid` against `qwen25_coder_7b` instead of `scripted`. This asks a more meaningful question, but D8 will have shown its answer, so it is post-hoc too.
- **R3.** Use a campaign-level criterion (final incumbent audited improvement), matching Paper B's primary outcome. This is the most principled, but B1 does not compute a final Y today (only B2 does), so it needs new code and review.

## 5. Restart conditions

After the fix in §4 is implemented and independently accepted, a new B1 run may start without a further author message, **provided all of the following hold**:

1. The diagnosis report and the fix are each accepted by a freshly spawned independent agent.
2. If the fix changes the scientific criterion (P or D), the author's one-line choice is committed as a dated PLAN §10 row first.
3. Exact new checkout: committed, clean, independently reviewed; the authorization note is re-bound to the new HEAD (`approved: true` candidate per R1-EXAM-B1-NOTE-ORDER-07NOV) and the real author gate passes.
4. Fresh TASL-7 read-only occupancy check, preflight and handover as for run `6835_20261108_a`; no preemption of other users' work (R1-TASL7-AGENT-OCCUPANCY-07NOV).
5. New run ID (`<id>_b`) and a fresh output tree; nothing of run `6835_20261108_a` is moved, overwritten or deleted (R1-EXAM-B1-NO-DELETION-07NOV).
6. Any further STOP in the new run is preserved and reported, not retried.

B2, X.7 and sweep 2 remain separately gated.

## 6. Paste-ready message for the experiment agent

> B1 STOP (run `6835_20261108_a`): see `docs/r1/proposals/B1_STOP_DIAGNOSIS_PLAN_20261108.md` (branch `docs/runbooks-09nov`). (1) When the Mac-local agent's `proposals/B1_DIAGNOSIS_HANDOFF_<date>.md` is pushed, run its read-only diagnosis script on TASL-7 exactly as written, with the exit code captured, and push the capture and its SHA. No rerun, no gate change, no modification or retirement of host files. (2) When `proposals/B1_RESTART_HANDOFF_<date>.md` is pushed and its fix is independently accepted, restart B1 on TASL-7 under the §5 conditions: fresh occupancy check, preflight and handover as on 8 Nov, a new run ID and a fresh output tree, nothing of the old run touched. Any new STOP is preserved and reported, not retried.

## 7. Timing

Diagnosis ½ day. An engineering fix: hours to a day plus review. A D-route decision: one author line. B1 itself took about 30 minutes for the three anchors; the 15 candidates were estimated at 2–4 days. With a restart on 9–10 Nov, B1 ends about 12–14 Nov and B2 about 14–16 Nov, so X.7 lands near the HoreKa submission freeze (20 Nov 12:00). HK4–HK5 before the downtime are unlikely either way; HK1–HK3 do not depend on X.7.
