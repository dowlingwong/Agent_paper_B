# D.3c scoping memo: closed loop on T1 code-diff nodes

**Tier D (R1-PROCESS-TIERS: a proposal that is not a draft of a tier-E unit). AI-assisted (Claude, local worker,
27 Nov 2026). approved: n/a (a memo; it decides nothing).** Queue item 4 of `tasks/local/20261126-05-queue.md`
(branch `coord/coordinator`), as asked by R1-D3-ORDER ("a scoping memo … is written first"). Written from published
`main` `47df6f55`, the D.3 pre-declaration draft revision 3 (`docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md`
on `mac-d3-predecl-20261122` @ `a24a55bf`, cited as PD), the G1/G6 design
(`proposals/d3_design_20261126/D3_G1_G6_DESIGN_20261126.md`), the next-phase runbook (row 2C), the G.5 draft revision 13
(§2, §3, §8, §9) and the G.4b result (`reports/tasl_chain_20261122/G4B_TASL_PILOT_RESULT_20261125.md` with its
`captures/dates_g5.json`). No label, test-partition or evaluation file was opened; nothing was run.

## 1. What D.3c is, and what it is not

| | D.3c (R1-D3-ORDER) | Source |
|---|---|---|
| Is | a **descriptive closed loop on T1**: the three G.4b pilot nodes `mlab_cifar10`, `mlgym_fmnist`, `mlgym_breakout_minatar`; **new instances disjoint from G.5's**; arms **A0, A2, A3, A5**; on the TASL pair once the G.5 labels are complete; no verdict | R1-D3-ORDER |
| Proposals | code diffs (`manager_proposal/v2-diff`, D4), not T0's parameter edits (`manager_proposal/v1`) | R1-BX-PROPOSED-CONFIRM (D4); G.5 draft §1 |
| Paperwork | **its own pre-declaration and its own authorization note, both tier E**, before any run; not part of the D.3 pre-declaration that covers D.3a/b | R1-D3-ORDER; R1-PROCESS-TIERS |
| Amends | R1-D3-MIN's "T0 only" and R1-SUBMISSION-CUTS's cut of closed-loop runs on T1 nodes, **for this form only** | R1-D3-ORDER |
| Is not | part of the submission minimum: an optional item that enters if complete and reviewed when parts (1)–(4) of R1-SUBMISSION-MIN are, and never delays them (D.3b included) | R1-STEP-ORDER (2)(c); R1-SUBMISSION-MIN |
| Is not | a test of any arm: outside the Holm families of D.3a/b; not A0R, A1, FIXR3, EGATE, LADDER or A6; not the R1-D3-HPO-REF reference rows (those are T0, W = 20, in the D.3 pre-declaration) | R1-D3-ORDER; R1-D3-DECOMP; R1-D3-HPO-REF |
| Is not | a source of training data: as for D.3, its outputs train, tune or select no arm; it reads no test label and no evaluation value | R1-D3-MIN (by analogy; to be written into its pre-declaration) |

A3 and A5 are deployed "exactly as frozen in the arms-frozen record" (R1-D3B-UNCONDITIONAL), so D.3c cannot run
before that record, which itself follows the G.5 labels and the T1 train/dev release (R1-STEP-ORDER (2)(b)).

## 2. The controller path for code-diff proposals

**What exists.**
- **The v2-diff engine** (harness `trackg/manager_v2_diff.py`, `campaign_v2_diff.py`, `proposal_v2_diff.py`;
  `run_v2_diff_campaign`; G.5 draft §2 and `reports/M10_V2DIFF_WIRING_20261114.md`): one manager call per proposal;
  budget counted in **manager calls**; temperature 0.2 with a per-call seed `sha256("<manager seed>:<step>")[:8]`;
  memory `history` (last 12 steps) or `none`; inert proposals and in-campaign duplicates are **not run**; keep iff
  `ok` and strictly better on validation; repeated-timeout cap and infrastructure reruns. The M10 report says what it
  lacks: "No noise-aware keep rule, controller or observer … Wiring into `run_real_campaign` is not done, because it
  would change base files."
- **The recount rule** (R1-G5-DIFF-RECOUNT): hunk-header line counts are recomputed before application
  (`git apply --recount` semantics), at G5-7 `cbf7a003` and G5-AR `ccdb3774`; `proposal.diff` stays the manager's text
  and the audit rebuilds each code state through `recount_hunk_headers` (G.5 draft §9, O1 under (a)). Measured
  liveness `ran_of_valid` 0.6667 / 0.8167 / 0.6167 on the three D.3c nodes (G.4b §4).
- **The audit runner** `trackg/audit_g5.py` (engine contract `g5_tasl_engine_contract/1`): re-materialises a code state
  from the chain of diffs and runs paired fresh-seed audits with joint seeds; cluster test C2 (determinism of audit
  pairs) is still listed (G.5 draft §10).
- **Paper side:** `r1/c3/control.py` `RuleController` (E1 by `rules.execute`, KG verify, keep rule
  `bayes_threshold/v1`, skip display `one_line/v1`), the priors `TableArmPrior` (A2), `LGBMPrior` (A3), `SidecarPrior` +
  `r1/c3/serve.py` (A5); the T1 featurizer `sweep2/t1_tasl/g5_features.py` and A5's T1 input `trackp_prompt_t1/1` with
  the D7-DIFF B diff excerpt (R1-T1-FEAT-DECISIONS, R1-T1-A5-DECISIONS); the T1 noise values (`g5_noise`, σ_node by
  D6-σ B); the G.5 seal/assembly code and the TASL launch binding.

**What is missing for a closed-loop controller to act on code-diff proposals.** Every item is tier E (the deployment
controller, the rule layer, code that writes or parses evaluation records, D.3 analysis scripts).

| # | Missing unit | Why |
|---|---|---|
| C1 | **A controller hook in the v2-diff loop**: an E1 call after parse and apply-check and before execution (execute / skip; a skip costs its call and no run); E2 keep through a keep rule with the E1 forecast instead of the hard-coded "strictly better"; the KG verify action (r = 2 candidate/incumbent replicate pairs on declared seeds, 2r = 4 charged runs) | the engine has none; `RuleController` speaks the T0 harness `Controller.decide`/`ControlView` interface only |
| C2 | **A worker-run budget plus an LLM-call cap** in the engine, with the `ended_on` enum of the G1 design | the engine counts W in calls (G5-W A); D.3 counts 20 worker runs and 80 calls (PD §2, R1-D3-CHOICES (2)); G.5 §9 names this as G5-W B's harness work |
| C3 | **A rule layer on diffs** mapped to `rule_noop` / `rule_duplicate` with the skip display, and a switch that makes A0 *execute* duplicates | the engine's native skipping is A0R's rule layer, not A0 (R1-D3-DECOMP); see Q2 |
| C4 | **An online T1 featurizer**: `g5_features` fields and `trackp_prompt_t1/1` built from the live ledger prefix at E1, with an identity test against the offline table bytes for the same step | A3/A5 were trained on assembled table bytes; at deployment the same features must come from the campaign state |
| C5 | **The D.3c runner** (G1 analogue on the TASL pair): seeds, pins, leases with a free-memory check (R1-CARD-SHARE), per-charged-run snapshot hook, no resume, seal | G1 is HTCondor/T0 only |
| C6 | **The Y audit** (G6 analogue) on `audit_g5.py`: final vs start incumbent on a new K-seed block, cache by (node, code-state sha, seed) | G6 audits T0 configs on deepthought CPUs |
| C7 | **Outcome table, run accounting and a descriptive analysis script** (G7/G8 analogues; paired differences with intervals, no Holm) | no D.3c schema exists |
| C8 | **A5 sidecar placement and image on TASL** (G9 analogue) | PD §13 item 16 is open even for HTCondor |
| C9 | **A seed-namespace check** for the new instance, replicate and audit blocks | disjoint from G.5 5101–5112, G.1b 1001–3030, G.4/G.4b 4001–4099, 7001–7010, 8001–8010, 9001+, 5001–5006 and every D.3 block (G.5 draft §5; PD §4) |

**The one structural choice** (Q1): put the hook into the engine files (C1–C3 inside `campaign_v2_diff.py` and the
allowed additions, a new reviewed harness commit, P5's rule that the change stays out of `noise_floor`'s import closure)
or route v2-diff proposals through `run_real_campaign` (base-file changes the M10 unit refused).

**What carries over from D.3a/b unchanged:** the decision logic of `RuleController` and `rules`, the three priors and the
frozen artefacts, the G2 fitter's per-node `fit_a2` path (for T1 nodes, from T1 dev labels), the G1 snapshot and
charged-run contract (w += 1 per charged run, `final.json`), G6's cache and no-label rules, G7's row shape with
`ended_on`, and the STOP/recovery split (a killed attempt is repeated in a new directory, R1-CARD-SHARE (3)). **What does
not:** HTCondor chunking, the v1 image, deepthought CPU audits, A0's `e1b_collect` path, `featurize_view`, harness
`a3fedbbd`.

## 3. Instances per node, arms and placement

- **Arms:** A0, A2, A3, A5, paired by instance (same instance seed, start code, replicate and audit seeds across arms).
- **Instances:** the row fixes none. Options 6, 12 or 18 per node (Q3); recommended **12**, the G.5 count and twice
  G.5's test floor, giving 3 × 12 × 4 = **144 campaigns**.
- **R1-HOST-FREE (2)(c):** all four arms of one instance are served by one GPU model, and each campaign keeps its
  proposer on one GPU model from start to end. With the proposer on TASL-7 and the worker on TASL-2 (both RTX 4090) this
  holds for the whole design. (2)(a): the start and final audits of one campaign's Y stay on one hardware class.
  (2)(b): a node's worker or audit runs on a second host use the first host's noise floor only after a cross-host PASS
  (the G.5 draft §2.10, revision 13, reads a PASS on `main` for all three: xc2 for `mlab_cifar10` and
  `mlgym_breakout_minatar`, the short xc3 check for `mlgym_fmnist`; the D.3c note re-checks it).
- **Per-run budget:** T1's R1-G1B-TIMEOUT basis (3 × the slowest census record), deciding only on an attempt that had
  its card to itself (R1-NO-TIMEOUT (2)).

## 4. GPU-hours (a reporting threshold, R1-NO-TIMEOUT (3))

**Basis** (G.4b §4, 3 campaigns of 20 calls per node on the TASL pair): per-call overhead c = (campaign wall − in-run
GPU time)/60 and per-run time r = in-run GPU time / executed runs:

| Node | c (s/call) | r (s/run) | A0 calls for 20 runs (duplicates run) | A0R-rate calls for 20 runs |
|---|---|---|---|---|
| `mlab_cifar10` | 14.23 | 7.10 | 26.7 | 30.0 |
| `mlgym_fmnist` | 10.87 | 13.03 | 20.0 | 24.5 |
| `mlgym_breakout_minatar` | 13.19 | 32.65 | 20.7 | 32.4 |

Campaign hours = calls × c + 20 × r. **Lower case:** A0 as above, A2/A3/A5 at the A0R rate (no E1 skip beyond the rule
layer). **Upper case:** A2/A3/A5 reach the 80-call cap with 20 runs, runs × 1.25 (G.5's allowance). The proposer card
is held through every campaign, so campaign hours count twice (R1-HOST-FREE (5); G.4 convention). **Audits:** Y_final
at K = 10 needs at most 10 start + 4 × 10 final runs per instance (worker card only, × 1.25); the optional Y(w) curve
raises that to 10 + 16 × 10.

| Instances / node | Campaigns, both cards (lower – upper) | Y_final audits | + Y(w) audits | Total |
|---|---|---|---|---|
| 6 | 28 – 50 | 5.5 | 18.7 | 34 – 56 (69 with Y(w)) |
| **12** | **56 – 101** | **11.0** | 37.4 | **67 – 112** (138 with Y(w)) |
| 18 | 85 – 151 | 16.5 | 56.1 | 101 – 167 (207 with Y(w)) |

Not included: the A5 sidecar's compute (unmeasured), job start-up (G.5's model allows 1,500 s per job; ≈ 12 GPU-h for
about 18 jobs on both cards) and repeats after infrastructure failures. **Proposed reporting threshold at 12 instances:
150 GPU-h** (Y_final only) or 175 GPU-h (with Y(w)); usage is reported against it and reaching it is reported at once,
it stops nothing. The binding projection is the smoke's (§5 step 6), as PD §11 does for D.3a. At one worker slot the
span is about the hours of the worker card: roughly 1.5–3 days of campaigns plus half a day of audits at 12 instances.

## 5. What must exist before the D.3c pre-declaration, in step order

No dates (R1-STEP-ORDER); a step starts when the steps it depends on are complete and reviewed. Steps 2 and 3 are desk
work and may run beside G.5, after the D.3 units that R1-D3-ORDER puts first.

1. **Author row** on the open questions of §6 (instances, A0's definition, W semantics, memory mode, sidecar placement,
   Y(w), threshold).
2. **Harness unit** C1–C3 on a new harness commit descending from G5-7 `cbf7a003`, with the P5 measurement-path check
   and the T0 identity test unchanged; independent review until accepted.
3. **Paper-side units** C4–C9, each reviewed until accepted, full `r1/tests` with zero new failures.
4. **G.5 labels complete** for the three nodes (a node that STOPs in G.5 leaves D.3c; D.3c then runs on the rest or
   not at all, an author item).
5. **T1 train/dev release row** (R1-T1-LABELS-UNSEAL, not yet written), then the arms trained, selected and calibrated
   and **the arms-frozen record** with A3, A5 and the T1 nodes' A2 constants; a D.3c node without a labelled non-inert
   dev proposal has no A2 constant and STOPs (as PD §5.0).
6. **Engineering smoke on the TASL pair** after G.5 releases the cards: every arm, two instances on one node from a
   smoke seed block, the frozen artefacts loaded, the sidecar served as Q5 decides, worker runs `ok`; it measures
   c, r, the call factors and the sidecar cost and replaces §4's model (the runbook's "code-diff sidecar smoke").
   Host records: leases, TASL-2 CPU sets without 8–11 with their determinism check (R1-TASL2-CPU), cross-host PASS for
   any TASL-7 audit.
7. **The D.3c pre-declaration** (tier E): nodes, instances and their seeds, arms with pins (arms-frozen sha256,
   harness commit, model and server flags), W and cap, memory mode, K and audit seeds, Y and its secondary outcomes,
   the descriptive analysis script by sha256, STOPs, the threshold; independent review until "accepted"; signature.
8. **The D.3c authorization note** (tier E), reviewed and signed; launch from the commit it names.

## 6. Open questions for the author (options; recommendation in bold)

| # | Question | Options | Recommendation |
|---|---|---|---|
| Q1 | Where the controller hook lives | (a) engine files of a new harness commit; (b) wire v2-diff into `run_real_campaign` | **(a)**: keeps base files and `noise_floor`'s import closure unchanged, as R1-G5-DIFF-RECOUNT did |
| Q2 | What A0 means on T1 | (a) the engine's native loop (skips inert and duplicates; A0R in substance), disclosed; (b) an engine switch so A0 executes duplicates, as T0's A0; (c) (b) plus A0R as a fifth arm (amends R1-D3-ORDER; +25 % campaigns) | **(b)**: the four arms keep their T0 meanings; (a) only if (b) cannot be built without touching `noise_floor`'s closure |
| Q3 | Instances per node | 6 / 12 / 18 | **12** (§3, §4) |
| Q4 | What W counts | (a) 20 worker runs + 80-call cap, as D.3; (b) 20 manager calls, as G.5 | **(a)**: matched worker-run budget is D.3's question; under (b) a skipping arm gains no proposals |
| Q5 | Memory mode | (a) `history`, as G.5 and the A3/A5 T1 inputs (R1-G5-MEM-E4; D7-HIST); (b) a new `append_only_summary` rendering | **(a)**, disclosed as different from T0's mode |
| Q6 | A5 sidecar placement | (a) TASL-2 card beside the worker (free-memory check, R1-CARD-SHARE); (b) TASL-7 beside the proposer; (c) CPU; (d) another card, fixed for all A5 campaigns | **(a)** if the smoke shows the memory fits and the sidecar idles while a run trains; else (d). (b) is unlikely to fit beside the 31B proposer on 24,564 MiB (to verify) |
| Q7 | Secondary outcomes | (a) R1-D3-OUTCOMES2 (b) and (d) only (compute and mechanism counts, free); (b) plus Y(w) (+26 GPU-h at 12 instances) | **(a)** |
| Q8 | Reporting threshold | 150 GPU-h (Y_final) / 175 GPU-h (with Y(w)) / the smoke's projection × 1.1 | **150 GPU-h**, replaced by the smoke projection if higher, reported before signature |
