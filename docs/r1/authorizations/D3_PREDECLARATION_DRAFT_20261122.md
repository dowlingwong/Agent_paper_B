**AI-assisted (Claude, chat session, 22 Nov 2026; subagent). Revision 4: AI-assisted (Claude, local worker, 27 Nov
2026). DRAFT; not signed; revision 4 not yet reviewed.**

# D.3 closed loop on T0 — pre-declaration of both stages (D.3a rule arms, D.3b learned arms) — DRAFT, revision 4

**Revision 4** (27 Nov 2026; tasks `local/20261126-03`, `local/20261126-16`, card `local/20261126-06` item 3 and
`local/20261126-07` item 3; branch `mac-d3-predecl-r4-20261127`, from revision 3 @ `a24a55bf` with `main` @ `47df6f55`
merged in) applies the PLAN §10 rows of "26 November 2026 (d)" — R1-D3B-UNCONDITIONAL (D.3b always runs; A5 − A3 joins
its family), R1-D3-DECOMP (arm A0R; A0R − A0 and A2 − A0R join the D.3a family), R1-D3-OUTCOMES2 (secondary outcomes
(a)–(f), §7.5), R1-D3-HPO-REF (reference rows RS and SMAC3, §5.8), R1-D3-ORDER (D.3c named, §1) — and of "26 November
2026 (f)/(g)": R1-HOST-FREE (2)(c) (one GPU model per instance across its arms, §2), R1-CARD-SHARE (3) and
R1-NO-TIMEOUT (infrastructure failures, §3.1; no walltime STOP, §10; the 140 GPU-h figure a reporting threshold, §11),
R1-STEP-ORDER (no date decides; §6). It also states the declared readings (§7.4), the two families' multiplicity
(§7.3), the rule layer of FIXR3, EGATE and LADDER (§5), the charging of a repeated attempt (§3.1) and the detectable
difference (§7.3), from the writer's claim-to-table sheet (`PAPER_B_CLAIM_TABLE_SHEET_20261126.md` §5–§6, branch
`writer-20261126-03-claim-table-sheet` @ `a9a9f6bb`). Revision 4's open author items are §13 items 21–31; items 1–20
were settled by R1-D3-CHOICES (2) (item 16 stays open). The text of revisions 2–3 below is kept where no row changes
it.

Drafted by a subagent of the coordinating chat. **Revision 2** answers the independent review
`docs/r1/reviews/D3_PREDECLARATION_REVIEW_20261122.md` (REVISE: 1 MAJOR, 9 MINOR, 10 NOTE); the main change is that
EGATE is now the repository's `PaceStyleGate`. **Revision 3** answers the round-2 review
`docs/r1/reviews/D3_PREDECLARATION_REVIEW_R2_20261122.md` (ACCEPT WITH MINOR: 4 MINOR, 7 NOTE): corrected EGATE
thresholds, smoke node and replicate seeds, the order of the verify-seed check and of script-changing choices, and the
notes. Tier E (R1-PROCESS-TIERS): before signing it needs a committed
independent review re-checked until it writes "accepted". It decides nothing on its own. Every value below carries its
source (a PLAN row, a signed note or a file with its path); a value with no source on `main` is marked **proposed**,
with its reasoning, and is fixed only by the author's signature. Written on branch `mac-d3-predecl-20261122` over
`author-minsub-20261122` @ `d9acb501` (PLAN.md sha256 `75b5ae36afec1a36e233bf85d3b2e114b0d1134fc32e39c6feaf9e5ebec5b47b`).
No label, test-partition or evaluation-value file was opened to write it.

**What it implements.** R1-D3-MIN (one pre-declaration for both stages, committed with its hash before any D.3 run
starts; RUNBOOK §1 "Pre-declaration") as amended by R1-MINSUB-CHOICES (4) (six D.3a arms, the values listed there,
deepthought CPUs as the D.3 audit host), R1-D3-CHOICES (2) (the §13 values), R1-D3B-UNCONDITIONAL, R1-D3-DECOMP,
R1-D3-OUTCOMES2, R1-D3-HPO-REF, R1-D3-ORDER, R1-HOST-FREE (2)(c), R1-CARD-SHARE (3), R1-NO-TIMEOUT and
R1-STEP-ORDER. No PLAN row, preregistration, signed note or code guard is changed. Where a row
cannot be implemented as written, the point is listed in §13, not fixed here.

**How it becomes binding, in this order.** (1) The sweep-2 B.2 audit is registered (R1-SWEEP2-RELEASE-DECISIONS);
(2) the sweep-2 train/dev label blocks are released with their receipt (R1-S2-LABELS-TRAINDEV-RELEASE); (3) the
reviewed constants fitter (§12 G2) writes the A1/A2/LADDER constants file (§5.0) and its sha256 is entered in §14;
the harness's `vary` verify-seed rule is recorded by the G1 implementer and checked for disjointness by a separate
reviewed check outside `r1/c3/d3_analysis.py` (§4.1), whose result is cited in §4.1; (4) the author settles every §13
item that changes `r1/c3/d3_analysis.py` (marked **[sha]**), any resulting change to the script and its tests is made,
and §9/§14 re-pin their sha256s; (5) this document, the script and the tests, complete in every field, are
independently reviewed and accepted; (6) the author settles the remaining §13 items and signs — if anything (text or
script) changes after (5), the reviewer re-checks the diff only and writes "accepted" before the signature;
(7) the coordinating chat sets `frozen: true` and commits. **No field of this document changes after `frozen: true`.**
(8) Its sha256 is written into the D.3a authorization note (`D3A_AUTHORIZATION_DRAFT_20261122.md`) and into every D.3
outcome-table header (§8). No D.3 campaign starts before (8). Signing therefore waits for (1)–(5): R1-D3-MIN pins A1's
constants by sha256 in this document, so no placeholder may be filled after signing.

---

## 1. Scope

| Item | Value | Source |
|---|---|---|
| Stages | **D.3a**: seven rule arms (A0, A0R, A1, A2, FIXR3, EGATE, LADDER), not conditional on the gate. **D.3b**: learned arms A3 and A5 (A6 only if it enters under RUNBOOK P.5), **whether or not the gate passes**, after the arms-frozen record is committed | R1-D3-MIN; R1-MINSUB-CHOICES (4); R1-D3-DECOMP (A0R); R1-D3B-UNCONDITIONAL |
| Reference rows | **HPO-REF**: random search with the rule layer's de-duplication (RS) and SMAC3, each in place of the manager on D.3's instances, W = 20; descriptive, outside the Holm families (§5.8) | R1-D3-HPO-REF |
| Not in this pre-declaration | **D.3c**, the descriptive closed loop on three T1 nodes (A0, A2, A3, A5 on `mlab_cifar10`, `mlgym_fmnist`, `mlgym_breakout_minatar`), is declared by its own later pre-declaration and authorization note after its scoping memo; it is named here only, and nothing of this document binds or is bound by it | R1-D3-ORDER |
| Tier | T0 only; no T1 or T2 node | R1-D3-MIN; R1-SUBMISSION-CUTS |
| Proposer | `gemma4_31b`, thinking off (the Track X pick) | R1-D3-MIN; R1-MAIN-PROPOSER |
| What D.3a may read | the sweep-2 **dev** instances' label block and table fields, through the constants file only (§5.0); the pinned noise source; the node specs; **no test label, no evaluation value, no T1 label** | R1-D3-MIN |
| What D.3 outputs may be used for | nothing that trains, tunes or selects any arm | R1-D3-MIN |
| Repetitions | **one** (rep 0) required; a second is optional. The signed count is `REPETITIONS` in `d3_analysis.py`; a table with more repetitions than declared is analysed on the declared ones, and the mean over all repetitions is reported as a descriptive family with no verdict | R1-D3-MIN; R1-D3-CHOICES (2): 1 |

## 2. Fixed design

| Item | Value | Source |
|---|---|---|
| T0 node set | `digits_mlp`, `openml_breast_w`, `openml_climate`, `openml_credit_approval`, `openml_ionosphere`, `openml_sonar`, `tabular_mlp` (seven) | R1-D3-MIN ("the PRE-WDBC primary set unless it says otherwise"); preregistration PRE-WDBC B and R1-S2C3B-WDBC (the seven nodes that passed S2-C3b at the sweep-2 launch commit; `openml_wdbc` failed only D28 `invalid_rate`, `SWEEP2_REPORT_20261121.md`). `openml_wdbc` is not run in D.3 (§13 item 6) |
| Memory mode | `append_only_summary` only | R1-MINSUB-CHOICES (4) |
| Run budget W | 20 worker runs per campaign, every arm; replicate and verify runs count against the same counter (replicate runs need code: §5, §12 G8) | R1-MINSUB-CHOICES (4) ("as in sweep 2"); R1-BX-PROPOSED-CONFIRM (D7) ("replicate runs count against the budget") |
| LLM-call cap | **80 per campaign, every arm** (§3); a call issued again after an infrastructure failure does not count (§3.1) | R1-D3-CHOICES (2); R1-NO-TIMEOUT (1) |
| Trial budget | equal to the LLM-call cap, so it never binds | `r1/c3/control.py` `c3_budgets` (review F6, D1) |
| Instances | 18 per node, the same 18 instance seeds on every node, 126 instances in all (§4) | R1-D3-MIN; R1-MINSUB-CHOICES (4) |
| Split policy (verify) | `vary` | PLAN §10 "Verify split policy"; sweep-2 authorization |
| Proposal schema | structure-only `manager_proposal/v1`, temperature 0.2 with the D26 seed | sweep-2 authorization ("Workers/training") |
| Server | `-c 32768 -ngl 999 -np 1`, `--jinja`, `--chat-template-kwargs` exactly `{"enable_thinking":false}`, q8_0 K/V, `cache_prompt` false on every call | sweep-2 authorization ("Server"); R1-SWEEP2-SETTINGS (1); R1-CACHEPROMPT-FALSE |
| Model file | `google_gemma-4-31B-it-Q4_K_M.gguf`, sha256 `2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75` | sweep-2 authorization ("Pick/model") |
| Image (proposer job) | v1 GPU image `ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296`, one digest for both stages | R1-SWEEP2-IMAGE (sweep 2's digest); keeping it for D.3 is **proposed** so that A0 is the sweep-2 design on fresh instances. The image for D.3b's A5/A6 sidecar is open: §12 G9, §13 item 16 |
| Harness | `9bb416805175149eb87b71f28d77530572aa4bce` (reviewed verify-seed pin). The D.3a note names this pin and §7.2 checks audit equality against it. The sweep-2 record retains its `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` pin | R1-D3-VERIFY-SEED; `D3_VERIFY_SEED_REVIEW_20261127.md` |
| Proposer host | Any host and GPU model that fits the job and passes its environment check, with a measured D.3 chunk time on that model (§11); the compute agent chooses. **Bound (R1-HOST-FREE (2)(c)): every arm of one instance, in both stages and every repetition, is served by one GPU model, and a campaign keeps its proposer on one GPU model from start to end.** With the chunk layout (one job per (stage, node, arm, repetition) holding the node's 18 instances; G1/G6 design §2.1) this means every chunk of a node runs on that node's GPU model; a chunk rerun after an infrastructure failure (§3.1) runs on the same model. Different nodes may use different models. Every row of the outcome table names its `gpu_model` (§8) and the analysis refuses a table in which one instance's arms (D.3a and D.3b together) differ. Every job record names host, GPU model, driver and environment freeze (R1-HOST-FREE (1)); the paper states per table which hardware produced which rows, and no analysis by hardware class is made (R1-HOST-FREE (4)). A card may be shared with other processes (R1-CARD-SHARE (1)) | R1-HOST-FREE (1), (2)(c), (4) (replaces revision 3's "one GPU model for both stages", which the row names); R1-CARD-SHARE; R1-D3-MIN ("Hosts") |
| Worker runs | CPU of the proposer job, as in sweep 2 ("T0 worker training is CPU; the GPU affects proposal generation only") | sweep-2 authorization |
| Skip display | `one_line/v1`: a control-plane skip shows as one line, no metric; recorded in every manifest | R1-SKIP-DISPLAY; `r1/c3/control.py` `SKIP_DISPLAY` |
| Run price g | 0.1 σ_node (no sensitivity value in D.3) | PLAN §10 "g (22 Oct)"; `r1/c3/offline_eval.py` `G_PRIMARY` |
| Noise constants | σ_node, σ_cmp (local / structural), δ_n by `r1.c3.dataset.noise_table` on `results/r1/noise/D28_REPAIR_20261027/summary.json`, sha256 `3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310` | preregistration PRE-DELTA and §1 "Noise source" |

## 3. The LLM-call cap — 80 per campaign (= 4 W), equal for all arms (settled by R1-D3-CHOICES (2))

**Why a cap matters here.** Sweeps 1 and 2 executed every proposal, so no proposal was ever skipped and no cap bound
(R1-MINSUB-CHOICES (4)). The sweep driver passed a trial budget of 2 W = 40 (`r1/headroom/e1b_collect.py`, `_run_root`:
`budget=runs * 2`, `ComputeBudget(max_worker_runs=runs)`); sweep 2 used 5,796 LLM calls for 5,760 trials
(`SWEEP2_REPORT_20261121.md`, `collection_counts.json`), about one call per trial. In D.3 the arms differ in how many
proposals they spend per run: A2 (and A3/A5/A6) skip rule-detected duplicates and no-ops, which costs a call and no run
(RUNBOOK H.4); FIXR3 and EGATE spend several runs per proposal. With a cap that binds, a skipping arm would end before
W and the arms would no longer be matched on runs, which is the comparison C3_DESIGN §6 states ("matched W = 20 runs
and matched LLM-call cap").

**Evidence on how many calls a skipping arm needs for W = 20 runs.**
1. *Sweep 2 (the D.3 proposer, both memory modes pooled).* 2,512 of 5,760 trials were duplicates (B.2 counts:
   2,512 duplicates, 2,500 eligible, 0 no-ops, 5,012 proposals; `reports/s2_audit_20261121/PRECONDITION2_20261122.md`;
   the other 748 trials are the 288 first trials and the 460 worker failures, `SWEEP2_REPORT_20261121.md`). If the
   proposal law did not change under skipping, A2 would execute 1 − 2,512/5,760 = 0.564 of its trials and need
   20 / 0.564 ≈ 35.5 calls. The per-mode split is not on `main`, so the `append_only_summary` value is unknown.
2. *Track X B1/B2 (same proposer, memory on, W = 20).* The pick's replayed-repeat share was 0.054 in B2 and at most
   0.125 in B1 (`reports/X7C_APPENDIX_20261116.md` §2), so with memory on the duplicate share may be much lower than the
   pooled sweep-2 value.
3. *Track S S0.5 (the 7B proposer, duplicates skipped, LLM cap 40, worker budget 40).* Every campaign ended at the
   40-call cap; worker runs used 11–27 (digits) and 14–22 (tabular); E1 executed 318 of 747 and 350 of 749 decisions
   (per instance 0.28–0.68 and 0.35–0.57); 53 and 51 of 800 calls were invalid proposals
   (`reports/TRACKS_S05_SUMMARY_20261115.md` §4). At the worst per-instance execute share (0.28 of E1 decisions, about
   0.26 of calls) a skipping arm needs about 20 / 0.26 ≈ 77 calls for 20 runs.
4. *Precedents for 4 W.* Track X B1 ran with W = 20 and an author-bound LLM-call cap of 80 (R1-EXAM-B1-TRUNCATION-INVALID,
   "budgets (W = 20, LLM-call cap 80)"; `r1/exam/campaign.py` passes it as `ComputeBudget(max_llm_calls=...)`); the
   Track H dry run uses a cap of 4 W (`r1/scripts/c3_control_dryrun.py` `LLM_CAP = 4 * W`).

**Proposal.** Cap = 80 calls per campaign for every arm (every proposal, every D25 revision and every controller call
counts; `r1/c3/accounting.py`), trial budget = 80. Reasoning: with 80, W rather than the cap ends a skipping arm's
campaign unless fewer than about a quarter of its calls lead to a run, which covers both the pooled sweep-2 duplicate
share (≈ 35.5 calls expected) and the worst per-instance share seen under skipping in Track S (≈ 77 calls); a cap of 40
(the sweep trial budget, Track S's cap) would already bind at an execute share below one half. Cost: a campaign that
skips almost everything holds the GPU for up to four times as many calls as an A0 campaign (§11 worst case). The arms
that never skip (A0, A1 unless its constant screen skips, FIXR3, EGATE, LADDER) are unaffected. The analysis reports,
per arm, how many campaigns the cap ended (`ended_on`, §8). The value is `LLM_CALL_CAP` in `r1/c3/d3_analysis.py`, so a
different signed value changes that file's sha256 (§13 item 1). Settled at 80 by R1-D3-CHOICES (2).

### 3.1 Infrastructure failures and repeated attempts (revision 4; R1-CARD-SHARE (3), R1-NO-TIMEOUT (1)–(2))

1. **What is an infrastructure failure.** An attempt lost because of the card or the host: out of memory beside
   another process, a kill, a reset, a lost connection, a job that reaches its scheduler walltime, or an LLM call or
   job that shows no progress and is ended by its operator. It is sealed and recorded (with the card's other compute
   processes and their memory, R1-CARD-SHARE (3)–(4)), and the same work is attempted again. **It is never an
   outcome and never a STOP, and the number of attempts is not limited.**
2. **A single LLM call issued again** after no progress (R1-NO-TIMEOUT (1)) is the same call: the same D26 seed and
   prompt, and it **does not count against the 80-call cap**; only the call that returns is counted (once). No time
   limit on an LLM call decides anything.
3. **Anything else lost to infrastructure inside a chunk** (a worker run killed by the host, the proposer server lost,
   the job killed or over its walltime): the **whole chunk** is attempted again from the start in a new attempt
   directory, the old one moved aside and disclosed (the sweep-2 rule; G1/G6 design §2.1). **No worker run and no
   manager call of a lost attempt counts against W = 20 or the 80-call cap of the new attempt**, and nothing of the
   lost attempt enters any table; the new attempt is a fresh campaign with the same instance id, seeds and D26 seed
   stream, so its decisions are the ones the lost attempt would have made on a deterministic GPU model. It runs on
   the same GPU model (§2). The outcome-table row records `infra_attempts` (≥ 1; descriptive only). This is the
   conservative option (§13 item 27): a partial resume of a campaign is never made (G1/G6 design §1 "No resume,
   ever").
4. **What is not an infrastructure failure.** A worker run that fails for a reason of its proposal
   (`invalid_config`, the two pre-admitted runtime-error classes, §10) or that reaches the T0 per-run budget of 600 s
   while no other compute process was on the job's card is the proposal's failure: it is charged and counted in the
   §10 failure rate (R1-NO-TIMEOUT (2)). Only a run that reaches its budget, or runs out of memory, **while another
   compute process was on the job's card**, recorded as R1-CARD-SHARE (4) requires (the card's other compute processes,
   count and memory, at the start and the end of the job), is an infrastructure failure under item 3; this is the
   row's literal condition. T0 worker runs are CPU runs of the proposer job: a T0 run that reaches its budget while
   only the host's CPUs were shared (no other compute process on the card) is the **proposal's failure**, charged and
   counted. Whether CPU sharing should also count, how it would be recorded and how its repeat would decide, is open
   (§13 item 31).

## 4. Instances and seeds — declared blocks (settled by R1-D3-CHOICES (2)), disjoint from every namespace in the repository

### 4.1 The declared seeds

| Use | Seeds | Rule |
|---|---|---|
| Deployment instances | **6201–6218** on every node | instance id `<node>__s<seed>` (seed in decimal, no padding; the gate's and split file's format, `r1/c3/p3_split.py`). 126 instance ids: `digits_mlp__s6201` … `digits_mlp__s6218`, `openml_breast_w__s6201` … `__s6218`, `openml_climate__s6201` … `__s6218`, `openml_credit_approval__s6201` … `__s6218`, `openml_ionosphere__s6201` … `__s6218`, `openml_sonar__s6201` … `__s6218`, `tabular_mlp__s6201` … `__s6218`. Instance index i = seed − 6201 (0–17) |
| Worker seed of every single in-campaign run (and of replicate j = 0) | train seed = split seed = the instance seed | as sweeps 1 and 2 (`e1b_collect._run_root`: `LocalWorker(..., train_seed=seed, split_seed=seed)`), so candidate and incumbent are compared on one common seed |
| Replicate runs j ≥ 1 (FIXR3, EGATE) | replicate j = 1…9 of instance i runs with **train seed = split seed = 6500 + 10 i + j** (6501–6679) | every configuration of a campaign is replicated on the same seed list, so an incumbent's runs on a seed can be reused; FIXR3 uses j ≤ 2, EGATE j ≤ 7 |
| Proposer seed | D26: `manager_seed(campaign_id, budget_index, repetition, revision_attempt)`, sent as the llama.cpp request seed; the **harness `campaign_id` is the instance id**, the same for every arm and repetition; D26 repetition 0 (1 for rep 1) | `e1b_collect.seed_policy` ("llamacpp_seed"); RUNBOOK A.10. With the same instance id and seed stream, every arm sees the same first prompt and seed, so arms are paired until their first different decision (H200 runs are deterministic, R1-SWEEP2-RTE-DIAG). The arm and the repetition are therefore **not** encoded in the harness `campaign_id` (that would change the D26 seeds); they are encoded in (a) the ledger root, one directory per (stage, arm, repetition): `<run root>/<stage>/<arm>/r<rep>/<instance id>/`, which also holds the harness's `*_pending.json` guard, and (b) the D.3 record name `<stage>__<arm>__<instance id>__r<rep>` (§8) |
| A0R (revision 4) | the instance, audit and D26 seeds of every other arm; A0R runs one run per executed trial, so it uses no replicate seed | R1-D3-DECOMP ("its seeds"): A0R is paired with A0, A1 and A2 on the same instance seeds |
| HPO-REF sampler seeds (revision 4) | RS: a NumPy `PCG64` generator seeded with the instance seed (6201–6218) plus 1,000,000 × repetition; SMAC3: `Scenario(seed=<instance seed>)`, plus the repetition. Worker train and split seeds = the instance seed, audit seeds as every arm | a random-number seed of the sampler, not a training seed, so it is not a worker-seed namespace (as E-SYN, §4.2); proposed (§13 item 26) |
| Engineering smoke (§11) | instance seeds **6301–6302** on node **`openml_climate`**, every arm (revision 4: 14 campaigns with A0R; one GPU model per smoke instance as §2); smoke replicate j = 1…9 of smoke seed s runs with train seed = split seed = **6300 + 10 (s − 6300) + j** (6311–6319, 6321–6329) | ENGINEERING_ONLY. `openml_climate` had the longest `append_only_summary` chunk of sweep 2 (1,150.5 s; `reports/sweep2_20261116/sweep2_report_20261121/chunks_summary.json`). Its outputs may set only walltimes and the compute projection; they never enter an outcome table (the analysis refuses these seeds) and are never audited for Y |
| Audit of Y | audit seed k = 1…10 of instance i: **6700 + 10 i + k** (6701–6880), shared by every arm and repetition on that instance, outside the campaign budget | PLAN §4 "Outcome" (common seeds across arms); per-instance blocks so that one audit error does not recur across instances (the Track S rule, `TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md` "Seed blocks") |
| KG verify of A1/A2/A3/A5/A6, if it fires | `20000 + 10 * budget_index + pair_index` under `vary`, `verify_runs=2`, one-based `budget_index` 1–80 and `pair_index` 0 or 1 | 160 seeds, inclusive range 20010–20801. `python -m r1.c3.d3_verify_namespaces` returned **PASS** against the declared and reserved namespaces. Checker `r1/c3/d3_verify_namespaces.py` at `e44d966f201d15aa627d5399ca2fe7ada0e15958`, SHA-256 `62a13172b028b315c92719da5fed184f0bbaa23739d44971259fcc07d9f9f6d2`. The D.3a note's P10 re-runs it at the launch commit |

### 4.2 Disjointness

`r1.c3.d3_analysis.check_namespaces()` (`python -m r1.c3.d3_analysis namespaces`; tests
`r1/tests/test_d3_analysis.py::NamespaceTest`) refuses any overlap between the five D.3 blocks (instance, smoke,
smoke replicate, replicate, audit) or with the namespaces below. The tests cross-check these intervals against module
constants: `audit.DEFAULT_SEEDS`; `s2_c3b_lib.EXAM_SEED_BLOCK`, `G1B_SEED_BLOCK`, `PROMPT_MEASUREMENT_SEEDS`; parsed
from source because the modules import the harness, `e1_noise_floor.SEED_BASE` (all three 30-seed blocks) and
`e1b_collect.AUDIT_SEED_BASE` (the base only; the count 6 comes from R1-E1B-RERUN2); `r1/e2e.py`'s `train_seed=999`;
`p3_split.T1_SEEDS`; `r1.exam.namespace`. The G.4 seeds, the Track S blocks and the supplementary screening block are checked only as
declared intervals.

| Reserved namespace | Seeds | Source |
|---|---|---|
| Sweep 1 and 2 instance seeds = the P3 T0 split universe | 100 + 10 k + (Σ ord(node) mod 7), k = 0–17: values within 100–276 | `e1b_collect._instance_seed`; `p3_split.t0_instance_seed` (tested copy); preregistration PRE-SPLIT A |
| T1 G.5 instances = the P3 T1 split universe | 5101–5112 | `p3_split.T1_SEEDS`; PRE-SPLIT A |
| B.2 audits (sweeps 1, 2; T1) | 7001–7010 | `r1/c3/audit.py` `DEFAULT_SEEDS`; R1-B2-DECOUPLE |
| Exam (Stage A/B instances 9001–9099, audits 9101–9299; B2 instances 9011–9014, audits 9201–9210) | 9001–9303 | `r1/exam/namespace.py`; `sweep2/s2_c3b_lib.py` `EXAM_SEED_BLOCK`; R1-EXAM-B2-POWER-PLAN |
| G.1b proposed block | 8001–8010 | RUNBOOK G.1b; `sweep2/s2_c3b_lib.py` `G1B_SEED_BLOCK` |
| D21 noise floors (T0 and T1) | 1001–1030, 2001–2030, 3001–3030 | `r1/noise/e1_noise_floor.py` `SEED_BASE`; `r1/scripts/build_d28_noise_summary.py`; `authorizations/g1b_t1_tasl_20261121.md` |
| G.4 pilot | 4001–4003 | `authorizations/g4_t1_tasl_20261122.md` |
| E1b pilot audits | 5001–5006 | `e1b_collect.AUDIT_SEED_BASE`; R1-E1B-RERUN2 |
| S2-C3b prompt measurement | 6101–6108 | `sweep2/s2_c3b_lib.py` `PROMPT_MEASUREMENT_SEEDS` |
| Track S instances; audits | 30000–39999; 100000–799999 | `r1/tracks/collect.py` on branch `trackS-ops-20261030` (not on this branch, so not cross-checked by import) |
| Engineering smoke | 999 | `r1/e2e.py` |
| Supplementary screening measurement (added 23 Nov 2026, R1-SCREEN-MEASURE-CHOICES (6), `author-minsub-20261122` @ `d3f03e2c`) | 3301–3420 | `r1/noise/screen_design.py` on branch `mac-screen-measure-20261123` (not on this branch, so not cross-checked by import) |

In addition, `git grep` over every local and remote ref found no instance id `__s<seed>` with a seed in the instance,
replicate or audit blocks (22 Nov 2026), and a search for 6301–6302 and 6311–6329 found them only as process ids and
numeric values in reports, not as seeds. The S2-C3b liveness reused sweep instance seeds (R1-S2C3B-SEEDS); those lie in
100–276. Paper C's synthetic benchmark E-SYN (`paperC/src/paperc/learner_validation.py`, on `paperc-*` branches) uses simulator root seeds `range(6200, 6328)`, which overlaps the instance and smoke blocks; it is a separate random-number domain of a simulator with no T0 node, so it is not a collision.

## 5. D.3a arms (seven; R1-D3-MIN as amended by R1-MINSUB-CHOICES (4) and R1-D3-DECOMP)

**The rule layer per arm (revision 4; claim sheet §6; §13 item 21).** The rule layer (skip a rule-detected duplicate
or detectable no-op at E1, charged no run; `skip_reason` `rule_duplicate` / `rule_noop`) is **on** for A0R, A2 and
the D.3b arms, and **off** for A0, A1, FIXR3, EGATE and LADDER. For FIXR3, EGATE and LADDER this is the conservative
option: it keeps revision 3's reviewed definitions (FIXR3 "No rule layer"; EGATE and LADDER execute every proposal,
R1-MINSUB-CHOICES (4) "execute every proposal" for LADDER) and the literature rules as published, so that FIXR3 − A0,
EGATE − A0 and LADDER − A0 each compare one keep or replication rule with the default under the same "execute all"
policy. Consequence, stated with the result: LADDER − A2 differs in the rule layer as well as in the keep rule, so it
does not isolate the keep threshold; a FIXR3 or EGATE campaign spends 3 or more runs on a duplicate it executes.

| Arm | Rule layer | E1 screen | E2 keep rule | Verify / replication |
|---|---|---|---|---|
| A0 | off | none | Δ̂ > 0 | none |
| A0R | **on** | none | Δ̂ > 0 | none |
| A1 | off | constant prior | Δ̂ > t* | KG verify r = 2 |
| A2 | on | constant prior | Δ̂ > t* | KG verify r = 2 |
| FIXR3 | off | none | Welch, r = 3 | 3 replicates |
| EGATE | off | none | `PaceStyleGate` | pairs, ≤ 8 |
| LADDER | off | none | Δ̂ > η_node | none |

**Common to all seven.** The design of §2 and the seeds of §4. **Run accounting:** `r1/c3/accounting.py` counts worker
runs (trials whose worker ran, plus 2 r per verify) and LLM calls (every proposal, revision and charged controller
call). It does **not** count the replicate runs of FIXR3 and EGATE: that is gap G8 (§12). Spec: every candidate and
incumbent replicate run is recorded in its trial's record (seed, role, success) and counted by `campaign_usage`, and
every replicate run draws from the **same W counter** as single and verify runs, which refuses a step it cannot fund
before the step starts. Whether the harness `ComputeBudget(max_worker_runs=20)` sees runs issued by a controller is not
visible here; if it does not, G3/G4 route replication through a harness action that charges like verify (a new harness
pin, §2). A trial whose proposal fails the harness precheck costs its call and no run. The first valid trial of a
campaign is kept without comparison in every arm (harness behaviour; `TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md` B5). A
campaign ends when W runs are spent (`ended_on = worker_runs`), when the cap is reached below W (`llm_call_cap`), or,
for FIXR3 and EGATE only, when the runs left cannot fund the next required step (`no_fundable_candidate`).

### 5.0 The constants file (A1, A2, LADDER) — pinned before signing

One reviewed fitter (§12 gap G2) reads two data inputs, plus the split file and the noise constants: (a) **label rows** from the receipted sweep-2 train/dev
partition through `r1.c3.release.traindev_labels(release_root, "sweep2", receipt_sha256=<receipt>)` (the partition
holds only `label_block.traindev.jsonl`; released under R1-S2-LABELS-TRAINDEV-RELEASE); (b) **table fields** (node,
no-op and duplicate flags, features, weights, and LADDER's logged Δ̂) from the sweep-2 proposal table,
`proposals.jsonl` sha256 `379b17ca0783571f87724fc1687d02dfb4084d7ebcec69ab296e855de02197d9` and `configs.json` sha256
`de6d63b5e06e541d97dcb2455f75c27649c6b3698e2a7ab4d7193868f1ab0f4d` (`authorizations/c3_sweep2_b2_addendum_20261122.md`
key block), opened through `r1.c3.analysis_guard.guard_table` (sweep-2 tables may be analysed from R1-BX-D8-CONFIRM-V31
on); its sha256 must equal both the addendum's pin and the train/dev receipt's `inputs.proposals_sha256`
(`r1/c3/release.py`, `RECEIPT.json`), and a mismatch with either is a STOP. The table also holds the rows of train and test instances (in-campaign fields only, no
label): **rows are filtered to the P3 dev instances of the seven nodes before any use**, and dropped rows enter no
computation. The P3 dev instances come from the split file (`r1/c3/splits/c3_p3_split_v1.json`, sha256
`b5967dd7…e569`). The fitter writes one JSON file with, per node: A1's and A2's fitted bin vectors, the LADDER η and its
search table, the σ values used, and the receipt, table and split-file sha256s. The reviewed artifact is
`docs/r1/reports/d3_g2_20261127/d3_constants.json`, sha256
`4f5f686be8f0210bcb27dfe0968296d68cf54e7266fb72c9038e741163776a93`. The independent re-fit was byte-identical,
and `docs/r1/reviews/D3_G2_CONSTANTS_FIT_REVIEW_20261127.md` records acceptance. The same hash is bound in §14.
- **Population (PRE-A2 C):** the full dev population of sweep 2 (both memory modes, all labelled proposals; duplicates
  have no label and do not enter), as `r1/c3/gate_input_builder.py` `fit_a2` fits A2 for the gate. A test shows the
  fitter's per-node A2 vectors equal `fit_a2`'s on the same rows. The comparison is per node, not by `arm_digest`: the
  gate's fit also covers T1 nodes, which changes the pooled vector, and the pooled fallback is never used here. A D.3
  node without a labelled non-inert dev proposal has no constant and is a STOP (as `fit_a2` refuses it). Sweep 1 does
  not enter (PRE-A2 C: "A2 uses sweep 2 only").
- **Labels:** soft labels v2 (R1-SOFT-SIGMA: N(Δ_label, s²), s = σ̂_node/√5) from the label seeds 7001–7005 only.
- The arms-frozen record must carry exactly these per-node A1 and A2 constants for the seven nodes (R1-D3-MIN: "they …
  enter the arms-frozen record unchanged"); a different vector there is a STOP (§10).

### 5.1 A0 — Karpathy default (R1-BX-D7; C3_DESIGN §5 prac-1)

- **Rule:** execute every proposal, one run, keep iff Δ̂ > 0 (harness keep rule `default/v1`, no controller, no
  verify). This is the sweep-2 campaign design (`--new-campaign-versions`, `vary`), so A0 is renamed the Karpathy
  default, not duplicated (R1-BX-PROPOSED-CONFIRM (D7)).
- **Constants:** none. **Reads:** nothing beyond the campaign. **Charged:** one run per executed trial.
- **Implementation:** `e1b_collect.run_root` runs this design but hard-codes the sweep instance-seed law and
  `budget = 2 W` and sets no LLM cap: needs changes (§12 G1).

### 5.1b A0R — the default keep rule with the rule layer (R1-D3-DECOMP; revision 4)

- **Rule:** at E1, a proposal the rule layer marks as a duplicate or a detectable no-op is skipped and charged no run
  (`rule_duplicate` / `rule_noop`, one line in memory, R1-SKIP-DISPLAY), exactly as A2's rule layer (§5.3); every
  other proposal is executed once and kept iff Δ̂ > 0 (keep rule `default/v1`); no screen, no verify.
- **Design role:** with A0, A1 and A2 it forms the 2 × 2 of rule layer × index policy: A0R − A0 identifies the rule
  layer under the default keep rule, A2 − A0R the one-step rule once duplicates are removed. Their interaction
  (A2 − A0R) − (A1 − A0) is **not** a declared contrast and is not reported (claim sheet §4).
- **Constants:** none. **Reads:** nothing beyond the campaign; no label, no offline test read (R1-D3-DECOMP).
  **Charged:** a skip costs its call, no run; one run per executed trial. **Ends:** at W runs or at the cap.
- **Implementation:** missing: a controller with the rule layer and the default keep rule (`RuleController` with
  `rule_layer` on and no screen or verify, or a thin wrapper); a tier-E unit (§12 G11).

### 5.2 A1 — C2 index policy with a constant prior (D23; C3_DESIGN §5; R1-A1-VERIFY)

- **Rule:** at E1, from the node's constant forecast (π, μ, τ): execute iff (1 − π)·V(t*; μ, τ, σ_cmp) ≥ g
  (T4 Proposition 8, `rules.execute`); at E2 keep iff Δ̂ > t* = −μ σ_cmp²/τ² (Proposition 6, keep rule
  `bayes_threshold/v1` served from the same forecast); D23 KG verify with r = 2 (each verify charged 2 r = 4 runs), which
  R1-A1-VERIFY keeps although it is predicted not to fire at g = 0.1 σ_node when σ_cmp ≤ σ_node. No rule layer:
  duplicates are executed.
- **Constants:** A1's per-node bin vector from §5.0 (`arms.ConstantPrior`), moments by `labels.moments` with τ floor
  0.15 σ_node (`arms.TAU_FLOOR_Z`); σ_cmp per edit kind and σ_node from §2's noise constants.
- **A consequence to report, not to repair:** with a constant prior the E1 screen takes the same decision for every
  proposal on a node (R1-MINSUB-CHOICES (4) says this of the Ladder arm). If it skips on a node, A1's campaigns there end
  at the cap with no run and Y = 0. With sweep 2's 0 no-ops (π ≈ 0, since `labels.soft_label` puts no mass on the no-op
  bin for a non-no-op proposal) A1's constant equals A2's, and A1 differs from A2 only in executing duplicates.
- **Reads:** the constants file and the noise constants; no label at run time. **Charged:** runs and verify runs.
- **Implementation:** `r1/c3/control.py` `RuleController` with `prior_model.TableArmPrior(A1)` (`rule_layer` false for
  A1) and `c3_budgets(W, cap)`: usable as is for the decisions (exercised only in the Track H DRYRUN); the D.3 runner is
  missing (§12 G1).

### 5.3 A2 — A1 plus the rule layer (C3_DESIGN §5; D25, D27; PRE-A2 C)

- **Rule:** at E1 skip rule-detected no-ops and duplicates first (`skip_reason` `rule_noop` / `rule_duplicate`; the
  skipped proposal shows as one line, R1-SKIP-DISPLAY); for the rest, A1's screen, keep threshold and KG verify with A2's
  constant (`arms.RulesPrior`).
- **Constants:** A2's per-node bin vector from §5.0. **Reads:** as A1. **Charged:** a skip costs its call, no run.
- **Implementation:** `RuleController` + `TableArmPrior(A2)`: usable as is; runner missing (G1).

### 5.4 FIXR3 — fixed-r replication + test (R1-BX-D7; C3_DESIGN §5 prac-2)

- **Rule:** every executed proposal is run r = 3 times, on replicate seeds j = 0, 1, 2 of its instance (§4.1); keep iff a
  one-sided Welch t-test of mean(candidate) > mean(incumbent) rejects at α = 0.05, the incumbent's three runs being its
  own replicate runs on the same seeds (they exist because it passed all three as a candidate, so FIXR3 never runs an
  incumbent replicate after the first trial). The first valid trial is run three times and kept without a test.
- **Failures and edge cases (§13 item 19; settled by R1-D3-CHOICES (2)):** any failed replicate (first, second or third) makes the candidate
  `failed_invalid`, charged for the runs it used; its remaining replicates are not run. A first trial with a failed
  replicate is `failed_invalid` and the next proposal becomes the first trial. If both sample variances are zero (the
  Welch statistic is undefined), the decision is **no keep**, and such cases are counted and reported.
- **Budget:** a step needs 3 runs, so the campaign ends when fewer than 3 are left (`no_fundable_candidate`). At most six
  proposals can complete all three replicates (3 + 5 × 3 = 18 runs); proposals that fail cost the runs they used, so a
  campaign can execute more proposals than that.
- **Constants:** r = 3, one-sided Welch test at α = 0.05, replicate runs counted against the budget
  (R1-BX-PROPOSED-CONFIRM (D7), confirming R1-BX-D7's proposed values). No rule layer, no screen.
- **Reads:** nothing beyond the campaign. **Charged:** every replicate run (through G8).
- **Memory display (§13 item 15; settled by R1-D3-CHOICES (2)):** the trial's line shows the mean of its successful replicate metrics and the decision.
- **Implementation:** missing (§12 G3).

### 5.5 EGATE — anytime-valid commit gate: the repository's `PaceStyleGate` (PLAN §5 required list; R1-D3-MIN)

- **Gate:** `r1/baselines/responses.py` `PaceStyleGate` ("PACE-style; after arXiv 2606.08106, not a reproduction"),
  with its constants as on `main`: **α = 0.1, clip = 0.05 metric units, max_pairs = 8**; test
  `r1/tests/test_l10_baselines.py::test_pace_gate_controls_false_commits_under_the_null`. A betting e-process
  (Waudby-Smith & Ramdas): paired differences d_j = m(candidate, seed j) − m(incumbent, seed j) are clipped to
  [−c, c] and scaled to [−1, 1]; wealth K_n = Π (1 + λ_j x_j) with a predictable λ_j ∈ [0, ½] (λ_1 = 0, then the
  truncated running mean of earlier x); commit iff K_n ≥ 1/α = 10 within max_pairs.
- **Closed-loop use:** after each pair the wrapper calls `decide` on the differences so far: `commit` → keep;
  `reject` with fewer than max_pairs pairs → run the next pair if the budget can fund it; otherwise → discard. Pair j runs
  the candidate at seed j and, if the incumbent has no run at seed j, the incumbent too; both are charged (G8). The first
  valid trial is kept after one run without a test. No σ is needed; the arm reads nothing beyond the campaign.
- **Assumptions (stated where the claim is made):** Ville's inequality bounds the false-commit probability **of each
  candidate test** by α under optional stopping for the null **E[clip(d_j) | past] ≤ 0**; a campaign can run up to
  two tests that share incumbent runs, so its campaign-level false-commit rate can exceed α. This holds with the d_j taken as independent over replicate
  seeds of one configuration pair. A skewed null with E[d] ≤ 0 can have a positive clipped mean (the class docstring;
  BUILD_REVIEW_20261012 finding 15). The paper claims α control only for the clipped-mean null.
- **What its constants imply at W = 20 (computed, not estimated):** since λ_1 = 0, λ ≤ ½ and |x| ≤ 1, the wealth after
  n pairs is at most 1.5^(n−1), so reaching 10 needs **n ≥ 7** pairs (1.5^5 = 7.59 < 10 ≤ 1.5^6 = 11.39). With a
  constant difference d on every pair and d/c ≥ ½, λ is truncated at ½ and the wealth is (1 + d/(2c))^(n−1), so commit
  by pair 8 needs **d ≥ 0.0390 metric units on every pair**, and by pair 7 **d ≥ 0.0468** (checked against
  `PaceStyleGate().decide([d] * n)`, which rejects at d = 0.038 and commits at d = 0.039 for n = 8, and commits from
  d = 0.0468 for n = 7). A full test costs up to 8 candidate runs plus the incumbent runs it lacks (up to 7 after a
  first trial with one run), so an EGATE campaign completes at most one full test within 20 runs. **After one full test
  (at least 7 pairs, so at least 14 runs with the first trial) the at most 6 runs left cannot reach 7 pairs, so they are
  spent on tests that cannot commit**; this affects usage, not Y, and no futility rule is added (the gate is used as on
  `main`). On the T0 nodes' noise scale
  (σ_node 0.0036–0.046, `noise_table`) a commit is therefore rare and EGATE will often keep only its first valid
  proposal. This is the gate's conservativeness at this budget and is reported as such; no constant is changed to make
  it commit. Reading the code shows no reason it cannot serve as a closed-loop E2 arm: it is anytime, needs no prior or
  σ, and its decision depends only on the pairs seen.
- **Failures and edge cases (§13 item 19; settled by R1-D3-CHOICES (2)):** a failed candidate replicate → `failed_invalid`, charged for the
  runs used; a failed incumbent replicate → the candidate is discarded (`reject`), the failed run is charged, recorded
  and counted in the §10 failure rate, and the campaign continues. Runs are deterministic, so a failed (incumbent, seed) run is recorded and never re-run; a later test that reaches that pair ends there with discard. The stage-wide STOP of revision 2 is dropped as too
  costly; excluding the campaign is not used either, because the analysis needs a complete paired design and a
  campaign excluded on an in-campaign event that only EGATE can have would make EGATE's missingness depend on its own
  history and bias EGATE − A0. A pair the budget cannot fund → discard (`reject`), and the campaign then ends `no_fundable_candidate` if no step can
  be funded.
- **Implementation:** decision logic exists and is tested; the closed-loop wrapper (replication on the declared seeds,
  charging, a declared action version — BUILD_REVIEW_20261012 finding 16 names it `verify:pace`) is missing: §12 G4.
- The normal-mixture construction of revision 1 is **not adopted**; it is kept as an alternative in Appendix A.

### 5.6 LADDER — Ladder margin rule, η per node by direct search on the dev label block (R1-MINSUB-CHOICES (4))

- **Rule:** execute every proposal (no screen: "with a constant prior a screen makes the same decision for every
  proposal"), one run, keep iff Δ̂ > η_node; no verify.
- **Search (§13 item 7, settled by R1-D3-CHOICES (2); result pinned in §5.0's file):** per node, on the same dev rows as A1 (§5.0), maximise
  U_node(η) = Σ_p w_p · Δ_label,p · 1{Δ̂_p > η} over the grid η = c · σ_node, c ∈ {−3.00, −2.95, …, +3.00}
  (121 values), where Δ_label,p is the label-seed mean (7001–7005) of proposal p, Δ̂_p its logged in-campaign
  comparison (from the table) and w_p its `offline_eval` weight (1 here: every eligible sweep-2 proposal was audited).
  The −g·execute term is the same for every η and is dropped. Ties: smallest |c|, then smallest c (c = 0 is A0's rule).
  The objective uses no evaluation value and no test label. Duplicates and first trials have no label and do not enter
  (disclosed).
- **Reads:** η from the constants file. **Charged:** one run per executed trial.
- **Implementation:** missing: the η search in the fitter (G2) and a keep-only controller (G5).

### 5.8 Reference rows HPO-REF: RS and SMAC3 (R1-D3-HPO-REF; revision 4; descriptive)

Classical configuration methods as the proposer, each **in place of the manager** on D.3's 126 instances (§4.1),
with W = 20 charged worker runs, the start configuration of D.3a, worker train seed = split seed = the instance seed,
and the final incumbent audited exactly as Y is (§7.1, same audit seeds, cache and host). No LLM call; the jobs need
no GPU (CPU hosts, any host that passes its environment check, R1-HOST-FREE (1)). **Descriptive, outside both Holm
families; reported whichever way it falls.** Under R1-STEP-ORDER (2)(c) it is optional: it enters the submission
version if complete and reviewed when that version is assembled, and never delays D.3a or D.3b.

- **RS (random search with the rule layer's de-duplication):** each step draws one configuration uniformly from the
  node's configuration space below (log-uniform on the parameters marked log; integers uniform on their range),
  canonicalised to its **active keys** (the node's `active_keys`, so a change only in an inactive key is a detectable
  no-op). A draw whose canonical configuration equals the incumbent or any configuration already executed in the
  campaign is skipped and charged no run (`rule_skips`). Every other draw is executed once and kept iff Δ̂ > 0
  against the incumbent (the default keep rule). At most 80 draws per campaign (`HPO_PROPOSAL_CAP`, proposed equal to
  the LLM-call cap); the campaign ends at W runs (`worker_runs`) or at 80 draws (`proposal_cap`).
- **SMAC3:** the same space as a ConfigSpace with the conditional keys of `active_keys`; facade, initial design and
  version are pinned by the HPO-REF unit before its review (**proposed**: `HyperparameterOptimizationFacade`,
  `deterministic=True`, the default configuration in the initial design, 5 initial configurations, the cost =
  −metric of the node's `metric_direction: maximize`); every ask is evaluated and charged as one worker run on the
  instance seed, so SMAC3 ends only at W runs (its asks never reach the cap of 80, and `proposal_cap` is refused for
  SMAC3);
  the final incumbent is SMAC3's incumbent after 20 evaluations (a failed run is charged and reported to SMAC3 as the
  worst cost). Version: `<TODO: SMAC3 version and its environment, pinned by the HPO-REF unit>`.
- **Seeds:** §4.1 "HPO-REF sampler seeds".
- **Configuration space per node** (from the harness node configs `configs/nodes/<node>.yaml` at the D.3 harness
  pin `a3fedbbd…`, unchanged at harness `HEAD` `897d83c`; these are exactly the keys and bounds the
  `manager_proposal/v1` schema admits, `editable_symbols`, `allowed_values`, `allowed_ranges`). The HPO-REF unit's
  review checks this table against the proposal schema's admitted edits:

| Node(s) (config sha256, first 12) | Keys and bounds | Conditional (active) keys |
|---|---|---|
| `digits_mlp` (`f830be240bd0`), `tabular_mlp` (`971c8bda762c`) | `HIDDEN_UNITS` int [4, 256]; `ALPHA` [1e-6, 1.0] log; `LEARNING_RATE_INIT` [1e-4, 0.1] log; `BATCH_SIZE` int [8, 512]; `MAX_ITER` int [5, 300] | all five always active |
| `openml_breast_w` (`03573e6ef33a`), `openml_climate` (`c2a9a18647cb`), `openml_ionosphere` (`a680286e473f`), `openml_sonar` (`47e9b748b116`), `openml_credit_approval` (`3a7bef047457`) | `model_type` ∈ {logistic_regression, random_forest, gradient_boosting}; `C` [0.001, 100] log; `class_weight` ∈ {null, balanced}; `max_iter` int [100, 3000]; `n_estimators` int [20, 500]; `max_depth` int [2, 30]; `learning_rate` [0.001, 0.5] log; `scaler` ∈ {none, standard, minmax}; `imputer` ∈ {most_frequent, constant} | logistic_regression: C, class_weight, max_iter, scaler, imputer; random_forest: n_estimators, max_depth, class_weight, scaler, imputer; gradient_boosting: n_estimators, max_depth, learning_rate, scaler, imputer. `imputer` is inactive on `openml_breast_w`, `openml_climate`, `openml_ionosphere`, `openml_sonar` (`dataset_excluded`) and active on `openml_credit_approval` |

  The log scales are **proposed** (§13 item 26); the harness gives bounds only.
- **Implementation:** missing: the HPO-REF unit (§12 G10), tier E.

## 6. D.3b arms (always run; R1-D3-MIN as amended by R1-D3B-UNCONDITIONAL)

- **When:** D.3b runs whether or not the gate passes (R1-D3B-UNCONDITIONAL, amending R1-D3-MIN and, for D.3b only,
  the RUNBOOK's "only if B.7 passes"), after the arms-frozen record is committed; its campaigns do not wait for the
  gate read. The gate verdict enters only the declared reading (§7.4).
- **A3, A5:** exactly as frozen in the arms-frozen record (preregistration §4 step 4), through `RuleController` with the
  rule layer, the screen, the keep threshold and KG verify (r = 2) as in A2; A3 = `TableArmPrior(LGBMPrior)`, A5 =
  `SidecarPrior` against `r1/c3/serve.py` with the pinned adapter, head and calibration map; on a sidecar failure the
  fallback prior answers and `prior_unavailable` is logged (`control.py`). The sidecar costs compute only, no LLM call
  (RUNBOOK H.6).
- **A6:** enters only if trained under RUNBOOK P.5 after the gate passes, on the train and dev label blocks only, and
  frozen in its own record before D.3b starts; deployed as P.5 requires ("rule(belief) or the action head, never the
  greedy bin"). A6 stays as R1-D3-MIN states (R1-D3B-UNCONDITIONAL), so it can enter only after a gate that passes.
  Optional: under R1-STEP-ORDER (1), (2)(c) no date decides; A6 enters the submission version only if complete and
  reviewed when that version is assembled. **Whether A6 enters is fixed before D.3b launches** by one
  key line `a6_entered: true|false` in the signed D.3b note; the outcome-table builder writes the same value into the
  D.3b table header (§8), and the analysis reads the note's line and refuses a table that disagrees, so A6 cannot leave
  or join the family after outcomes exist.
- **Paired with D.3a:** the same 126 instances, seeds, repetitions, audit seeds and start configurations; the D.3a rows of
  A0 and A2 are the references (no rerun). Each instance's D.3b arms run on the GPU model of its D.3a arms
  (R1-HOST-FREE (2)(c); checked by the analysis). D.3b runs on byte-identical pins (image, model file, server flags,
  harness, paper code outside the D.3b controller units); any difference is listed in the D.3b note and decided by the
  author before launch (§13 item 13).
- **Needs its own authorization note** (R1-D3-MIN); not drafted here.

## 7. Outcome, audit and contrasts

### 7.1 Outcome Y

Y is "the fresh-seed audited improvement of the final incumbent over the start config, normalised per node" (PLAN §4).
Per campaign: the final incumbent is the configuration of the campaign's last kept trial (the start configuration if
none). y_raw = (1/10) Σ_k [m(final, a_k) − m(start, a_k)] over the instance's audit seeds a_1…a_10 (§4.1), each run with
train seed = split seed = a_k as `r1/c3/audit.py` runs audits, Δ oriented as the C3 audit orients it. If the final
configuration equals the start configuration, y_raw = 0 by rule (no audit). **Y = y_raw / σ_node** (normalisation
settled by R1-D3-CHOICES (2): σ_node is the scale C3 already uses for z = Δ/σ_node; §13 item 10). Identical (node, configuration, seed)
runs are computed once and reused across the arms of an instance (cache; disclosed).

### 7.2 Audit: K = 10, seeds 6701–6880, host deepthought CPUs

K = 10 (R1-MINSUB-CHOICES (4)); no label/evaluation split, because Y trains nothing. Host: deepthought CPUs, which
R1-MINSUB-CHOICES (4) allows for the D.3 audit **under the conditions of R1-SWEEP2-B2-GO**, here applied as:
1. **One host:** every D.3 audit (both stages) on deepthought.
2. **Environment basis:** the e1 replay (R1-B2-GO B6 (a)), with the current-environment checks at audit start that the
   sweep-2 audit used (Python 3.13.15, scikit-learn 1.8.0, NumPy 2.4.4, pandas 3.0.3, SciPy 1.17.1, `uv.lock`
   `dd42d018…`; `authorizations/c3_sweep2_b2_addendum_20261122.md` "Pins"); a difference is a STOP.
3. **Harness-code equality:** the audit harness's node, config, worker and audited-library paths equal those of the D.3
   campaign harness pin (§2), checked at run time.
4. **Host difference disclosed:** campaigns on the HTCondor GPU job's CPUs, audits on deepthought; Python 3.13.18 in the
   v1 image against 3.13.15 in the e1 basis (R1-SWEEP2-B2-DECISIONS D3 A).

Operator protocol as in the sweep-2 audit: 16 workers, at least 10 of 40 cores free, `cotenancy.log`; a non-finite or
failed audit seed run is a STOP (D4 A of R1-SWEEP2-B2-DECISIONS).

### 7.3 Contrasts (every one of both stages)

| Family | Contrast (arm − reference) | Claim |
|---|---|---|
| D.3a | A0R − A0 | the rule layer under the default keep rule (R1-D3-DECOMP) |
| D.3a | A2 − A0R | the one-step rule once duplicates are removed (R1-D3-DECOMP) |
| D.3a | A1 − A0, A2 − A0, FIXR3 − A0, EGATE − A0, LADDER − A0 | each rule arm against the default (R1-D3-MIN; R1-MINSUB-CHOICES (4)) |
| D.3a | LADDER − A2 | a dev-tuned margin against the index policy with rules (R1-MINSUB-CHOICES (4)) |
| D.3b | A3 − A2, A5 − A2, A3 − A0, A5 − A0 | learned arms against the rule floor and the default (R1-D3-MIN) |
| D.3b | A5 − A3 | the two full forecasting arms against each other (R1-D3B-UNCONDITIONAL) |
| D.3b | A6 − A5, only if the D.3b note declares `a6_entered: true` | decision-focused fine-tuning (R1-D3-MIN) |

The order of the table is the order in `d3_analysis.CONTRASTS_D3A` / `CONTRASTS_D3B` (D.3a: A0R − A0, A2 − A0R, A1 − A0,
A2 − A0, FIXR3 − A0, EGATE − A0, LADDER − A0, LADDER − A2; D.3b: A3 − A2, A5 − A2, A3 − A0, A5 − A0, A5 − A3, then
A6 − A5), as in the claim sheet §6. Order does not affect Holm.

**Design and statistic.** Paired by instance: for a contrast a − b, D_{n,s} = Y_{n,s}(a) − Y_{n,s}(b), Y the mean over
the declared repetitions. Estimate: the node-equal-weighted mean D̄ = (1/7) Σ_n mean_s D_{n,s}. Standard error
(1/7)·√(Σ_n s_n²/m_n). Test: **two-sided** Student t with df = Σ_n (m_n − 1) = 119; this pooled df treats the
within-node variances as equal (a Satterthwaite df would be the unequal-variance alternative; not used). **Degenerate
rule:** if the standard error is 0, p = 1 when D̄ = 0 and p = 0 (so Holm rejects) otherwise. Interval: 95 % t interval
(unadjusted) and, beside it, a node-stratified percentile bootstrap interval (instances resampled within node,
10,000 resamples, PCG64 seed 20261122, per node in node order a 10,000 × m_n index array; descriptive). Per node: mean,
sd, n (descriptive). Per arm: mean worker runs, mean LLM calls, `ended_on` counts, mean Y (descriptive).

**Detectable difference at the declared design (a stated design figure, not a claim; claim sheet §5 item 8).** 126
paired instances per contrast (7 nodes × 18; one repetition). No closed-loop paired outcome exists, so sd(D) has no
source and no power is claimed for any effect. sd(D) is the within-node sd of the paired difference in σ_node units,
assumed equal across nodes. The smallest true difference a two-sided test detects with **power 0.8** at Holm's
**first** step (its strictest threshold) is, with the normal approximation (and the t reference, df 119, in
brackets): **D.3a (8 contrasts, α/8): 0.319 · sd(D) (0.323)**; **D.3b (5 contrasts, α/5): 0.304 · sd(D) (0.309)**;
D.3b with A6 (6 contrasts, α/6): 0.310 · sd(D) (0.314); at Holm's **last** step (α = 0.05): 0.250 · sd(D) (0.252).
For illustration only: if sd(D) were 1 σ_node, D.3a's figure would be 0.32 σ_node. The script computes these
(`d3_analysis.detectable_difference`, `python -m r1.c3.d3_analysis design`) and writes them into the report under
`design`; the paper may state the figure as the design's sensitivity, not as a result.

**Multiplicity.** Holm step-down at family-wise α = 0.05 **within each family** (R1-D3-CHOICES (2): "Holm within each
stage, α = 0.05"): **D.3a, eight contrasts**; **D.3b, five contrasts, or six with A6** (R1-D3B-UNCONDITIONAL: the
pre-declaration sets the multiplicity of the enlarged family). Two-sided tests (R1-D3-CHOICES (2)). The two families
stay separate although D.3b no longer depends on the gate: they answer different questions (rule control against the
default; learned forecasts against the rule floor), each is confirmatory for its own claim, and R1-D3-CHOICES (2)
fixed the stage as the family. The family-wise error over both families together is therefore up to 0.10; the
alternative of one Holm family over all 13 (14) contrasts, or α = 0.025 per family, is §13 item 22. Per-node results
are descriptive. The reference rows (§5.8) and the secondary outcomes (§7.5) are outside both families.

**If a stage does not run.** D.3b always runs (R1-D3B-UNCONDITIONAL); it can be missing only if it was stopped
(§10) or has not started when the D.3a analysis is run (§9): its family is then reported as "not run" with the reason
(`stopped` or `not_started`; the script refuses `gate_not_passed`, which is no longer a reason), and its contrasts are
listed as not estimated. A6 not entering: A6 − A5 is listed as not run. D.3a not run or stopped: §10. HPO-REF not
supplied: the reference rows are listed as not run.

### 7.4 Declared readings (revision 4; claim sheet §5 items 1, 2a; task `local/20261126-16` points 2–3)

The headline of the paper is one of the five readings of `GOAL_METRIC_ALIGNMENT_PROPOSAL_20261126.md` §6, adopted by
R1-ALIGN-OUTCOME; this section fixes by rule what its cells mean. The script sets each value
(`d3_analysis.declared_readings`, report key `readings`).

1. **"A2 > A0"** (`rule_gain = gain`) iff A2 − A0 is rejected by Holm in the D.3a family **and** its estimate is
   positive. If it is rejected with a negative estimate (`rule_gain = harm`), the reading is row 5 ("no gain over A0")
   and the paper states that A2 lowered the audited gain against A0. Otherwise `rule_gain = none` (row 5).
2. **"A3 or A5 > A2"** (`learned_gain = gain`) iff A3 − A2 **or** A5 − A2 is rejected by Holm in the D.3b family with
   a positive estimate. A3 − A0, A5 − A0 and A5 − A3 do not enter this cell. If neither is favourable and at least one
   is rejected with a negative estimate (`harm`), the reading is "no gain over A2" and the paper states the harm.
   **Mixed case:** if one of A3 − A2, A5 − A2 is rejected favourably and the other unfavourably, `learned_gain =
   gain` and the unfavourable contrast is reported beside it (a note in the report). If D.3b is not analysed
   (stopped), `learned_gain = not_run` and rows 1–4 are not assigned.
3. **Rule layer alone (claim sheet §5 item 2a).** When "A2 > A0" holds: if A2 − A0R is rejected favourably,
   `gain_source = one_step_rule_adds`; else if A0R − A0 is rejected favourably, `gain_source = rule_layer_alone`;
   else `not_separated`. Under `rule_layer_alone` the gain is **not** credited to the one-step rule, and only the
   rule-control clause of the row changes; its gate-dependent half stays. Row 4's first clause ("noise-aware rule
   control is enough at this task complexity") is replaced by "de-duplication raises the audited gain; the one-step
   rule adds no demonstrated gain", and the rest of row 4 stays; rows 1, 2 and 3 have no rule-control clause, so the
   same sentence is put in front of them. Under `not_separated` the paper says the decomposition does not attribute
   the gain.
4. **Rows by gate verdict.** The script reports the row for each gate verdict (it never reads the gate): rule gain and
   learned gain → row 1 (gate pass) or row 2 (gate fail); rule gain without learned gain → row 3 (pass) or row 4
   (fail); no rule gain → row 5 whatever the other cells; a favourable learned gain over A2 under row 5 is reported
   with its estimate and interval (a note in the report). Row 5's last sentence ("Not an ICML submission in the
   present form") is a planning statement, not paper text (claim sheet §5 item 2), and is not in the script.
5. **Gate STOP** (no eligible node or a nonpositive test denominator; claim sheet §5 item 2b): the gate is reported
   as a STOP with no verdict and the closed-loop reading stands on its own (row 1 with a learned gain, row 5 without
   a rule gain; with a rule gain and no learned gain no row is assigned and the paper states the two closed-loop cells
   only). Proposed, §13 item 24.

"Rejected by Holm, counted in the direction of its estimate" equals a one-sided test at α/2 in that direction within
the same Holm step; the declared tests stay two-sided (R1-D3-CHOICES (2)).

### 7.5 Secondary outcomes (R1-D3-OUTCOMES2; descriptive, no p-value, no verdict)

Declared before any run. The primary Y (at the campaign's actual final charged-run count, G1/G6 design §3.1) and its
contrasts are unchanged. The outcome-table fields are in §8; the script's report key is `secondary`.

| | Outcome | Definition | Fields (§8) / source |
|---|---|---|---|
| (a) | Budget curve Y(w), w = 5, 10, 15, 20 | the incumbent right after the w-th charged worker run (the G1 snapshot, G1/G6 design §2.2), audited as Y is; y_raw(w)/σ_node. A campaign that ended before w has **no** Y(w) (`missing_w`, never imputed); Y(20) equals the primary Y when the campaign reached 20 runs. Reported per arm, node and w as the mean over the campaigns that reached w, with the count | `y_raw_w` |
| (b) | Compute per campaign | worker runs and worker seconds, LLM calls, proposals and tokens (prompt, completion), proposer GPU-seconds, controller inference seconds, wall-clock seconds; per-arm means. Descriptive (R1-CARD-SHARE (2): speed is not a result) | `worker_runs`, `worker_seconds`, `llm_calls`, `proposals`, `llm_tokens_prompt`, `llm_tokens_completion`, `proposer_gpu_seconds`, `controller_seconds`, `wall_seconds` |
| (c) | Runs-to-match | per node, the smallest w ∈ {5, 10, 15, 20} at which an arm's mean Y(w) reaches A0's mean Y(20); none if not reached or if A0 has no Y(20); flagged incomplete if a mean used rests on fewer than 18 campaigns | from (a) |
| (d) | Mechanism counts per campaign | duplicates proposed and executed, rule skips, value skips, keeps, distinct configurations executed, the charged run of the last keep, and **the last charged run that improved the audited incumbent** (`last_improving_run`: the charged-run count at the last keep whose new incumbent's audit, as Y, exceeds the previous incumbent's; null if none) | `duplicates_proposed`, `duplicates_executed`, `rule_skips`, `value_skips`, `keeps`, `distinct_configs_executed`, `last_keep_run`, `last_improving_run` |
| (e) | Offline–online agreement | per node, for A2, A3 and A5 (the arms with an offline per-node utility; claim sheet §5 item 7), the gate's per-node utility beside the arm's closed-loop mean Y, and the rank agreement of the arms per node (Kendall τ-b), with its mean over nodes where defined; from outputs the preregistered analysis already writes | `d3_analysis.offline_online_agreement`; the primary step-6 output's A§4.2 point utilities in `results/r1/evidence/d3_offline_online_utility/gate_utility.json`, key `per_node_utility` |
| (f) | A5 − A3 and A5 − A2 by tier | taken from the per-node and per-tier tables of preregistration §7; a read beyond those tables needs a signed amendment before the arms-frozen record. Not computed by `d3_analysis.py` (D.3 is T0 only) | preregistration §7 tables |

(d)'s `last_improving_run` needs an audit of every kept incumbent of a campaign, not only of the four snapshots and
the final incumbent: a change to the G6 design (§12 G6; §13 item 25).

## 8. Per-campaign outcome table: schema `r1_d3_outcome/v2` (revision 4)

One JSON file (`.json`, at most 64 MiB) per stage (D.3a, D.3b, HPO-REF), written by the outcome-table builder (§12 G7)
from the campaign ledgers and the audit records; the analysis refuses anything else (`d3_analysis.validate_table`),
including a `v1` table. Revision 4 adds the fields marked (r4).

```
{"schema": "r1_d3_outcome/v2",
 "stage": "D.3a" | "D.3b" | "HPO-REF",
 "predeclaration_sha256": <64 hex: the signed file of this pre-declaration>,
 "noise_source_sha256": "3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310",
 "sigma_node": {<each of the seven nodes>: <dataset.noise_table sigma_node>},
 "arms": D.3a ["A0","A0R","A1","A2","FIXR3","EGATE","LADDER"] | D.3b ["A3","A5"] or ["A3","A5","A6"]
         | HPO-REF ["RS","SMAC3"],
 "a6_entered": D.3a and HPO-REF null | D.3b true or false (the D.3b note's value; the arms follow it),
 "repetitions": REPETITIONS .. 2,
 "rows": [ one per campaign:
   {"campaign_id": "<stage>__<arm>__<node>__s<seed>__r<rep>",
    "stage", "arm", "node", "instance_id": "<node>__s<seed>", "instance_seed": 6201..6218, "repetition": 0 | 1,
    "memory_mode": "append_only_summary" (HPO-REF: "not_applicable"), "status": "complete",
    "y_raw": <finite float, metric units, §7.1; the final incumbent at the actual final charged-run count>,
    "worker_runs": 0..20, "llm_calls": 0..80 (HPO-REF: 0),
    "ended_on": "worker_runs" | "llm_call_cap" | "no_fundable_candidate" (HPO-REF: "worker_runs" | "proposal_cap"),
    "audit_seeds": [the ten seeds of §4.1 for this instance],
    "start_config_hash": <64 hex>, "final_config_hash": <64 hex>,
    (r4) "gpu_model": <non-empty string, at most 128 characters; HPO-REF: null>,
    (r4) "infra_attempts": <integer >= 1; §3.1; descriptive>,
    (r4) "y_raw_w": {"5": f|null, "10": f|null, "15": f|null, "20": f|null}   (§7.5 (a); null iff worker_runs < w),
    (r4) "proposals", "llm_tokens_prompt", "llm_tokens_completion": <integers >= 0>,
    (r4) "worker_seconds", "proposer_gpu_seconds", "controller_seconds", "wall_seconds": <finite floats >= 0>,
    (r4) "duplicates_proposed", "duplicates_executed", "rule_skips", "value_skips", "keeps",
         "distinct_configs_executed": <integers >= 0>,
    (r4) "last_keep_run": <null if no keep, else 1..worker_runs>,
    (r4) "last_improving_run": <null, or 1..last_keep_run>} ]}
```

Refused before any statistic, in addition to the v1 rules below (revision 4): an instance whose arms or repetitions
name more than one `gpu_model`, or (D.3b) a model different from its D.3a arms' (R1-HOST-FREE (2)(c)); a null
`gpu_model` outside HPO-REF or a non-null one in HPO-REF; `infra_attempts` < 1; a `y_raw_w` value present for
w > worker_runs or missing for w ≤ worker_runs, or `y_raw_w["20"]` ≠ `y_raw` at worker_runs = 20; `rule_skips` > 0
for an arm without the rule layer (§5 table) or `value_skips` > 0 for an arm without the E1 screen; duplicates
executed above duplicates proposed or worker runs; keeps or distinct configurations above worker runs; proposals above
LLM calls (above 80 in HPO-REF); `last_keep_run` inconsistent with `keeps`; `last_improving_run` after the last keep;
in HPO-REF any LLM call, token or proposer GPU-second, and `proposal_cap` for SMAC3 or below 80 proposals.

Refused before any statistic (v1 rules, kept): any other key at either level; a stage, arm, node, seed, repetition, memory mode or audit
seed list other than declared; a campaign name other than the declared one; a non-complete status; a non-finite y_raw;
runs above W or calls above the cap; `ended_on` inconsistent with the counts (`worker_runs` iff runs = W;
`llm_call_cap` only at calls = cap; below W at the cap only `llm_call_cap`; `no_fundable_candidate` only for
FIXR3/EGATE and below the cap); a design that is not exactly every (arm, node, seed, repetition) once; y_raw ≠ 0 where
the final configuration equals the start; σ_node differing from `noise_table` on the pinned source; a pre-declaration
sha256 differing from the file given; for D.3b, `a6_entered` differing from the D.3b note, or a different
pre-declaration, noise source, σ, repetition count or start configuration than D.3a's (for HPO-REF likewise). Input paths that name a label,
evaluation, split, sweep-table or `r1_sealed` file are refused before opening, and the suffix and size are checked
before reading. Refusal messages name the row index and the rule, never a value or key taken from the table.

## 9. Analysis script

`r1/c3/d3_analysis.py`, sha256 **`c0be039905e682e8b1702542e16607f09daf30a59be3363bbdf5a85c64a484ce`** (this branch, revision 4; revision 3's
sha256 was `48126ffd…8e63`); tests `r1/tests/test_d3_analysis.py` (synthetic tables only), sha256
`c6c56c332d838db0acb2260ad7dc0f1a0ef90cc3bd63849bbe30fd26bf6f01a4` (revision 3: `7d5d8d04…881d`). These pins are of the draft and change again
if the author's choices of §13 items 21–31 marked **[sha]** change the script. Command:
`python -m r1.c3.d3_analysis analyse --d3a <table> (--d3b <table> --d3b-note <signed D.3b note> | --d3b-not-run
stopped|not_started) [--hpo-ref <table>] --predeclaration <this file, signed> --out <new file>`. It reads only the tables,
this file (for its sha256), the D.3b note (at most 1 MiB; exactly one `approved: true` line and one `a6_entered:` line;
its sha256 is recorded in the report and must equal the sha256 pinned in the D.3b launch record) and the pinned noise
summary (sha256-checked); it writes
its output with exclusive create, so an existing output is never overwritten. Its constants (nodes, arms, W, cap,
repetitions, seeds, contrasts, α, bootstrap) are this document's; a change after signing is a STOP. An input refusal is
fixed and the run repeated, both recorded; the analysis is never repeated after its statistics are seen
(preregistration §4, last paragraph, applied here). The D.3a analysis is run **once** (`--d3b-not-run not_started`,
with `--hpo-ref` if that table exists then). If D.3b later runs, the D.3b analysis recomputes the D.3a family from the
same D.3a table; it is a reproduction check, not a repeat: its D.3a family must equal the first run's exactly (the
computation is deterministic), the comparison is recorded, and a difference is a STOP. The same holds for the
reference rows: a later run with `--hpo-ref` recomputes the D.3a family (and D.3b's, if supplied) as a reproduction
check; the reference rows themselves carry no verdict.

## 10. STOP rules

Retain everything; there is no automatic resume. **Before launch (each stage):** any precondition of the stage's note
missing; a pin of §2 or of the note differing; the constants file's sha256 differing from §14; the arms-frozen record's
per-node A1/A2 constants for the seven nodes differing from the constants file (checked when the record is committed,
and before D.3b); `d3_analysis.py`'s sha256 differing from §14 or its tests failing at the launch commit. **During
campaigns:** a pin, image, model file, server-flag, `cache_prompt` or thinking-flag mismatch; thinking content in more
than 1 % of calls (RUNBOOK B.1b); parse failures above 0.2 (the sweep collection gate); a worker `runtime_error` other
than the two proposal-induced classes diagnosed in R1-SWEEP2-RTE-DIAG (a YAML `ParserError` from a truncated mapping
value; `TypeError` from `max_depth: null` at `benchmark.py:164`), which are counted as `invalid_config` failures
(pre-admission, §13 item 14, settled by R1-D3-CHOICES (2)); the pooled worker-failure rate of a stage above 12.99 % (sweep 2's pooled
7.99 % + 5 pp; the form of R1-SWEEP2-LAYOUT-AMEND's rule, which there is relative to sweep 1; settled by R1-D3-CHOICES (2); failed
replicate runs, candidate and incumbent, count as worker runs and failures in this rate, §13 item 14); a campaign over W runs or the cap; any seed outside §4's blocks (other than the harness
verify seeds, once recorded and checked, §13 item 12); an instance whose arms are served by more than one GPU
model (R1-HOST-FREE (2)(c)); more than 1 % of A5/A6
forecasts answered by the fallback prior (settled by R1-D3-CHOICES (2)); any read of a test label, an evaluation value or a T1 label by
D.3 code; any use of a D.3 output to train, tune or select an arm. **Audit:** §7.2's conditions; a failed or non-finite
seed run; co-tenancy breach. **Analysis:** the refusals of §8.

**Not STOPs (revision 4; R1-NO-TIMEOUT (1), R1-CARD-SHARE (3)).** A chunk over its scheduler walltime, a killed or
non-clean chunk, an attempt lost beside another process on a shared card, or an LLM call or job ended for showing no
progress is an **infrastructure failure** (§3.1): it is sealed, recorded and attempted again (the chunk whole, in a
new directory, the old one moved aside and disclosed; a single call issued again without counting against the cap),
with no limit on attempts, and it is never an outcome. Revision 3's STOP "a chunk over its walltime" is withdrawn:
the walltime (1.5 × the measured smoke chunk time, §11) is a scheduler request only. No wall-clock limit and no date
decides any check, STOP or outcome (R1-NO-TIMEOUT, R1-STEP-ORDER). The pre-admitted error classes, the failure-rate
STOP and the per-run budget of 600 s of T0 worker runs are unchanged (R1-NO-TIMEOUT (2); §3.1 item 4).

**Reported on a STOP:** the stage is reported as stopped, with the STOP record, the number of completed campaigns per
arm and node, and no contrast: no outcome table is built from a partial design and no statistic is computed from one.
Any remedy needs an author row and is disclosed. If D.3a stops, R1-SUBMISSION-MIN part (4) is reported as a STOP and C2
has no closed-loop evidence; if D.3b stops, its family is reported as `not_run: stopped`. A STOP of the HPO-REF rows
stops only those rows (they are descriptive) and is reported.

## 11. Compute

**Proposer GPU-hours (HTCondor).** Basis: the measured sweep-2 chunk on H200, 5,823 s for 18 campaigns at W = 20 (about
20 calls per campaign), i.e. 11.32 GPU-h per arm on seven nodes (5,823 × 7 / 3,600; R1-SWEEP2-MEASURED-GPU; sweep-2
authorization "Layout"). Model (approximation): a chunk's time scales with the larger of its campaigns' calls and runs
relative to 20. A2's factor is 35.47/20 = 1.773, so A2 costs 20.08 GPU-h. FIXR3 and EGATE spend at most 20 runs and
fewer calls (factor ≤ 1). This basis is the layout projection of R1-SWEEP2-MEASURED-GPU, from a 2-instance smoke; the
**realised** sweep-2 chunks were much shorter: the eight `append_only_summary` chunks took 1,080 s on average and at most
1,150.5 s, all 16 chunks 4.32 GPU-h in total (`reports/sweep2_20261116/sweep2_report_20261121/chunks_summary.json`,
`wall_s`; 18 campaigns per chunk ran concurrently on 16 workers, so chunk time is not proportional to the number of
campaigns). The table gives both bases; the layout basis is the upper one.

| Stage | Expected | Worst case (cap binds) |
|---|---|---|
| D.3a, layout basis (5,823 s per chunk), revision 4 with A0R | A0, A1, FIXR3, EGATE, LADDER at factor 1: 56.61 GPU-h; A2 and A0R (both skip duplicates) 2 × 20.08 GPU-h; **≈ 96.8 GPU-h** | A0R, A1 and A2 at factor 4: 135.87 GPU-h; the other four 45.29 GPU-h; **≈ 181.2 GPU-h** |
| D.3a, realised basis (1,150.5 s per chunk, the longest realised `append_only_summary` chunk), revision 4 | 2.24 GPU-h per arm at factor 1: **≈ 19.1 GPU-h** | **≈ 35.8 GPU-h** |
| (revision 3, six arms, for comparison) | layout ≈ 76.7; realised ≈ 15.2 | layout ≈ 135.9; realised ≈ 26.8 |
| D.3b, layout basis | A3, A5 like A2: 2 × 20.08 = **40.2 GPU-h**; with A6 3 × 20.08 = **60.2 GPU-h** (60.24); plus unmeasured sidecar compute | **90.6 GPU-h** (135.9 with A6) |
| D.3b, realised basis | **≈ 7.9 GPU-h** (≈ 11.9 with A6), plus sidecar compute | **≈ 17.9 GPU-h** (≈ 26.8 with A6) |

D.3b now always runs (R1-D3B-UNCONDITIONAL; the row's projection: 7.9 GPU-h realised, 40.2 GPU-h layout, plus the
sidecar). GPU-hours count on any card (R1-HOST-FREE (5)); the bases above are H200 times, and a slower or shared card
raises GPU-hours without changing a result (R1-NO-TIMEOUT (3)). For comparison, sweep 2 (288 campaigns) projected
25.88 GPU-h; D.3a has 882 campaigns (7 arms × 126). The expected values rest on the
pooled sweep-2 duplicate share, which may not hold for `append_only_summary` or under skipping. Before the D.3a note is
signed, a 2-instance ENGINEERING smoke per arm (node `openml_climate`, seeds 6301–6302, smoke replicate seeds
6311–6329, §4.1) on **each GPU model that will serve D.3** (R1-HOST-FREE; working worker runs, `gates.worker` PASS)
replaces this model; the scheduler walltime request = 1.5 × the measured chunk time per arm on that model (the
R1-SWEEP2-MEASURED-GPU rule); reaching it is an infrastructure failure, not a STOP (§3.1, §10). **The 140 GPU-h figure
for D.3a's P7 projection is a reporting threshold, not a STOP** (R1-NO-TIMEOUT (3), which names "D.3a's 140
projection"): usage and the projection are reported against it, and reaching it is reported to the author at once;
where reviewed code would stop at it, the coordinator's addendum raises it (R1-NO-TIMEOUT (3)). The revision-4
layout-basis worst case (181.2 GPU-h with A0R) is above 140 and the realised basis (19.1 / 35.8 GPU-h) far below; the
same projection method overstated sweep 2 by about five times.

**Audit CPU-hours (deepthought).** Basis: the sweep-1 B.2 audit ran 4,660 seed runs in 22 min 44 s with 16 workers
(`reports/b2_audit_20261119/REPORT.md`), 4.68 worker-seconds per run. Upper bounds for the primary Y (no reuse across
arms): D.3a (revision 4, seven arms) 126 × (10 start + 7 × 10) = 10,080 runs ≈ **13.1 worker-h, ≈ 49 min at 16
workers**; D.3b 2,520 runs (3,780 with A6) ≈ 3.3 (4.9) worker-h, ≈ 12 (18) min; HPO-REF 2,520 runs ≈ 3.3 worker-h.
The secondary outcomes add the Y(w) audits (up to four snapshots per campaign; the G1/G6 design §3.3 estimates
≈ 3.6–7 × the single-audit work, cache-aware) and the audits of every kept incumbent for `last_improving_run`
(§7.5 (d)); the G6 unit reports its CPU projection before launch. The node mix differs from sweep 1's.
**HPO-REF worker CPU** (no GPU): 126 × 2 × 20 worker runs ≈ 5,040 runs, of the order of the T0 worker times of
sweep 2; the HPO-REF unit projects it from its smoke.

## 12. Implementation gaps (this branch; none is written here)

| Arm or unit | Exists on this branch | Status | Short spec of what is missing |
|---|---|---|---|
| G1 D.3 campaign runner (all arms) | `e1b_collect.run_root` (A0 design); `c3_control_dryrun.py` (DRYRUN wiring of `RuleController`) | **missing** for EVIDENCE | HTCondor job per (node, arm, repetition) chunk as sweep 2; explicit instance seeds 6201–6218, smoke seeds 6301–6302 and smoke replicate seeds 6311–6329 (smoke on `openml_climate`); the separate verify-seed disjointness check of §4.1; harness `campaign_id` = instance id with one ledger root per (stage, arm, repetition) (§4.1); `c3_budgets(20, 80)` for every arm (A0 too); controller per arm; manifests with pins, skip display, seeds; no resume |
| A0 | `e1b_collect._run_root` | **needs changes** | instance seeds and cap from the runner instead of `_instance_seed` and `budget = 2 W` |
| A1, A2 | `control.RuleController`, `prior_model.TableArmPrior`, `arms.ConstantPrior/RulesPrior` | **usable as is** (decision logic) | only G1, G2; pass σ_cmp per edit kind from `noise_table` and verify r = 2 explicitly |
| G2 constants fitter (A1, A2, LADDER η) | `gate_input_builder.fit_a2` (fits A2 from the full gate input, after the test release) | **missing** | reads `release.traindev_labels` (sweep 2) and the pinned sweep-2 table through `guard_table`, filtered to P3 dev instances first (§5.0); test of per-node equality with `fit_a2`; output JSON pinned by sha256 |
| G3 FIXR3 | none | **missing** | §5.4: replicate runs on declared seeds, failure and zero-variance rules, incumbent replicate reuse, charging through G8 (a harness action that charges like verify if controller-issued runs do not reach `ComputeBudget`), memory line |
| G4 EGATE | `r1/baselines/responses.py` `PaceStyleGate` (decision logic) and `r1/tests/test_l10_baselines.py::test_pace_gate_controls_false_commits_under_the_null` | **needs changes** (closed-loop wrapper missing) | §5.5: sequential calls to `decide`, replicate pairs on declared seeds, incumbent runs on demand, charging through G8, failure rules (an incumbent replicate failure discards the candidate), an action version (`verify:pace`, BUILD_REVIEW_20261012 finding 16) |
| G5 LADDER controller | none (`RuleController` cannot keep at a fixed η without a prior) | **missing** | execute always; keep iff Δ̂ > η (e.g. a `KeepPrior` with μ = −η, τ = σ = σ_cmp gives t* = η under `bayes_threshold/v1`); no verify |
| A3 | `RuleController` + `TableArmPrior(LGBMPrior)` | **usable as is**; needs the frozen artefact | arms-frozen record (not yet) |
| A5 | `prior_model.SidecarPrior`, `r1/c3/serve.py` | **needs changes** | HTCondor co-residence of the sidecar with llama-server, an image with its stack (G9), pinned artefact loading; fallback accounting |
| A6 | `RuleController(greedy_bin=True)` | **needs changes** | the greedy-bin path contradicts RUNBOOK P.5 / R1-C3-POST ("never the greedy bin"); a rule(belief) or action-head path is needed |
| G6 Y audit | `r1/c3/audit.py` (B.2 proposal audits, seeds fixed to 7001–7010) | **missing** | final-vs-start audit on per-instance seeds 6701–6880, K = 10, cache across arms, §7.2 conditions, completion record |
| G7 outcome-table builder | none | **missing** | ledgers + audit records → §8 schema; `ended_on` from the completion event; `a6_entered` from the D.3b note |
| G8 usage and run accounting | `r1/branch/matching.py` `matching_report`, `accounting.campaign_usage` | **needs changes** | count FIXR3/EGATE candidate and incumbent replicate runs (§5 "Run accounting"); then `matching_report` as is |
| G9 image for D.3b | v1 (sweep 2), v2.1 (Track P) | **open** | which image serves the A5/A6 sidecar beside the v1 proposer (§13 item 16) |
| G1 additions (revision 4) | G1/G6 design rev. 5 on `main` | **design changes** | (i) placement: one GPU model per instance across its arms and stages (per node with the chunk layout), recorded per row, instead of "one GPU model for both stages" (§2); (ii) infrastructure failures: a lost chunk rerun whole on the same model, nothing of the lost attempt charged, a reissued LLM call not charged, `infra_attempts` recorded; a per-run budget hit counts as infrastructure only with another compute process on the job's card, recorded per R1-CARD-SHARE (4), and a T0 budget hit with only host CPUs shared is the proposal's failure (§3.1 item 4; §13 item 31); walltime a scheduler request only; (iii) A0R in the arm list and the smoke (14 campaigns); (iv) the R1-D3-OUTCOMES2 (b)/(d) counters per campaign (§8) |
| G6 additions (revision 4) | G1/G6 design rev. 5 | **design change** | the Y(w) audits are now declared here (§7.5 (a), §8 `y_raw_w`), which settles the design's §3.2 "MAJOR 3" item; `last_improving_run` (§7.5 (d)) needs an audit of every kept incumbent of a campaign (cache-aware), not only snapshots (§13 item 25) |
| G7 outcome-table builder (revision 4) | none | **missing** | schema `r1_d3_outcome/v2` (§8) for D.3a, D.3b and HPO-REF |
| G10 HPO-REF unit | none | **missing** | RS with de-duplication on active keys and SMAC3 (version, facade pinned), each node's configuration space checked against the proposal schema (§5.8), the runner on CPU hosts, the same audit; tier E |
| G11 A0R controller | `RuleController` (rule layer) | **needs changes** | the rule layer with the default keep rule, no screen, no verify (§5.1b); tier E |

Every unit G1–G8 and the A5/A6 changes are tier E (R1-PROCESS-TIERS: the rule layer, the deployment controller, code
that writes or parses evaluation records, the D.3 analysis scripts): each needs a committed independent review
re-checked until accepted, before the stage's note can cite it.

## 13. Open for the author

Items 1–20 were settled at their recommended values by R1-D3-CHOICES (2) (author, 22 Nov), except item 16, which
stays open; where a later row changes one, revision 4 says so: item 2's families are enlarged (§7.3, item 22),
item 11's 140 GPU-h figure is a reporting threshold under R1-NO-TIMEOUT (3), item 13's "byte-identical" pins no
longer include the GPU model (R1-HOST-FREE (2)(c): the instance's model instead), and item 17 is unchanged by
R1-D3-OUTCOMES2 (its outcomes are D.3 campaign fields, not D.4's per-proposal audits). Items 21–31 are new in
revision 4. Each item gives the recommended value. **[sha]** marks a choice that changes `r1/c3/d3_analysis.py`; it must be written
into the script before signing, and §9/§14 then re-pin its sha256.

1. **LLM-call cap** (§3) **[sha]**: *recommended 80 = 4 W*, equal for all arms. Alternatives: 40 (the sweeps' trial
   budget; Track S), 60.
2. **Sidedness and families** (§7.3) **[sha]**: *recommended two-sided, Holm within each stage at α = 0.05*. Alternative:
   one-sided for the C2 direction (A1, A2 better than A0), as the C3 gate is one-sided.
3. **Repetitions** (§1) **[sha]**: *recommended 1* (`REPETITIONS = 1`). With 2, each instance's outcome is the mean of
   both; a rep 1 run without being declared is analysed only as the descriptive family.
4. **EGATE** (§5.5): *recommended `PaceStyleGate` as on `main` (α = 0.1, clip = 0.05, max_pairs = 8)*: it is the
   repository's reviewed gate and is valid without a known σ (null on the clipped mean); its conservativeness at W = 20
   (at least 7 pairs to commit; at most one full test per campaign) is a property to report. Alternative, not adopted:
   the normal-mixture e-process of Appendix A (can commit after 1–5 pairs, but needs a known σ and loses the α guarantee
   for about half of edits by construction). Changing `PaceStyleGate`'s constants (e.g. a node-scaled clip) would be a
   new arm definition that `main` does not carry; not recommended.
5. **FIXR3 test** (§5.4): *recommended Welch, as R1-BX-PROPOSED-CONFIRM (D7) fixes it*; a paired t-test would use the
   common seeds but is not what the row says.
6. **`openml_wdbc`** **[sha]**: *recommended not run* (R1-D3-MIN's default node set). A sensitivity row would add one node
   per arm (about 1/7 more compute).
7. **LADDER search** (§5.6): *recommended the 121-point grid in σ_node, the objective and the tie rule as written*.
8. **Fit population of A1/A2/LADDER** (§5.0): *recommended both memory modes of sweep 2's dev instances*, as `fit_a2`,
   because that is what the arms-frozen record will carry and R1-D3-MIN requires equality.
9. **Sweep-2 release:** *recommended: no further author row*. R1-S2-LABELS-TRAINDEV-RELEASE already releases both
   sources' train/dev blocks, and R1-SWEEP2-RELEASE-DECISIONS only holds sweep 2 until its audit is registered; once it
   is registered, the release step's receipt (with its sha256 cited in the D.3a note, P2) is the record. The author may
   still prefer a one-line row.
10. **Y normalisation** (§7.1) **[sha]**: *recommended divide by σ_node*; PLAN §4 says "normalised per node" without a
    scale.
11. **Projection reporting threshold** (§11): 140 GPU-h for D.3a, settled by R1-D3-CHOICES (2) as a STOP and made a
    reporting threshold by R1-NO-TIMEOUT (3).
12. **Harness verify seeds:** *recommended: the G1 implementer records the harness's `vary` verify-seed rule before
    step (5), and a separate reviewed check outside the pinned script verifies its disjointness from every declared
    block and reserved namespace; the result is entered in §4.1 before the review, and the D.3a note's P10 re-runs the
    check at the launch commit.* The pinned script does not change for this (no [sha]).
13. **D.3b pins:** *recommended byte-identical to D.3a's*; otherwise the difference is decided before launch.
14. **Runtime errors and failure gate** (§10): *recommended pre-admitting exactly the two classes diagnosed in
    R1-SWEEP2-RTE-DIAG, and a pooled failure-rate STOP at 12.99 %, with failed replicate runs (candidate and incumbent)
    counted in it*, because they are worker runs that failed.
15. **Memory line of a replicated trial** (FIXR3, EGATE): *recommended the mean of its successful replicate metrics with
    the decision*.
16. **Images.** D.3a: *recommended the v1 digest* (§2). D.3b sidecar (G9): no recommendation is possible yet. Missing:
    (a) whether the v1 image carries the stack `r1/c3/serve.py` and the pinned adapter need (not checked on this branch);
    (b) whether image v2.1 has passed its I2/I3 and H200 smoke (R1-TRACKP-IMAGE-V21; no completion record on this
    branch); (c) whether one HTCondor job can run the sidecar container beside the v1 proposer container. Provisional
    preference: the sidecar from v2.1 (the image A5/A6 are trained and calibrated in), if (b) and (c) hold.
17. **D.4 descriptive analyses** (C1 error rates per arm, T4 bound vs realised gain; RUNBOOK D.4): *recommended not in
    this pre-declaration*; they would need per-proposal audits of D.3 campaigns and their own declaration.
18. **Missing implementations:** *recommended* G1–G8 for D.3a and the A5/A6 changes and G9 for D.3b, each as a reviewed
    tier-E unit (§12).
19. **Replicate failure and edge rules** (§5.4, §5.5): *recommended as written*: any failed candidate replicate →
    `failed_invalid`, charged for the runs used; a failed EGATE incumbent replicate → discard the candidate, charge and
    record the run, and continue (not a STOP, and the campaign is not excluded; §5.5 gives the reason); a failed (incumbent, seed) run is never re-run, and a later test that reaches that pair ends with discard; zero variance on both Welch sides → no keep; an unfundable EGATE pair → discard.
20. **Seed blocks and smoke node** (§4.1) **[sha]** for the blocks: *recommended* instances 6201–6218, smoke
    6301–6302 on `openml_climate`, smoke replicates 6311–6329, replicates 6501–6679, audits 6701–6880.

**New in revision 4.**

21. **Rule layer of FIXR3, EGATE, LADDER** (§5) **[sha]**: *recommended off for all three* (built). Alternatives: on
    for all three (each then compares with A0R rather than A0 on the rule layer, and LADDER − A2 isolates the keep
    rule; but it changes three reviewed arm definitions and the claim "rules from the literature as published"); on
    for LADDER only (cleaner LADDER − A2). Changing it changes `RULE_LAYER_ARMS` in the script.
22. **Multiplicity across the two families** (§7.3) **[sha]**: *recommended Holm within each family at α = 0.05, D.3a
    eight contrasts, D.3b five (six with A6)*, as R1-D3-CHOICES (2) fixed per stage (built). Alternatives: one Holm
    family of 13 (14) contrasts at 0.05; or α = 0.025 per family (family-wise 0.05 over both). Cost of the
    alternatives: D.3a's first-step detectable difference rises from 0.319 to 0.332 (one family of 13; 0.335 of 14)
    or 0.338 (α = 0.025, k = 8) sd(D); D.3b's from 0.304 to 0.325 (α = 0.025, k = 5).
23. **Declared readings** (§7.4) **[sha]**: *recommended as written* (the claim sheet's draft: Holm rejection in the
    favourable direction; A3 − A2 or A5 − A2 only for the learned cell; the rule-layer-alone qualifier). Alternative
    for the learned cell: require both A3 − A2 and A5 − A2 (stricter; not the sheet's wording).
24. **Gate STOP reading** (§7.4 item 5): *recommended: the closed-loop reading stands on its own and the gate is
    reported as a STOP with no verdict* (claim sheet §5 item 2b). Alternative: declare a sixth reading row.
25. **`last_improving_run`** (§7.5 (d)): *recommended as the row says: audit every kept incumbent* (cache-aware; more
    audit CPU than the G1/G6 design). Alternative: report `last_keep_run` only and drop "audited" (cheaper; departs
    from the row's wording). The field is nullable; the script does not change between the options except that the
    alternative would drop one key **[sha]**.
26. **HPO-REF details** (§5.8, §4.1): *recommended* the proposal cap of 80 draws or asks, the log scales marked, the
    sampler seeds, SMAC3's `HyperparameterOptimizationFacade` with 5 initial configurations including the default; the
    SMAC3 version is pinned by the HPO-REF unit. The cap is in the script (`HPO_PROPOSAL_CAP`) **[sha]**.
27. **Charging of a repeated attempt** (§3.1): *recommended: a chunk lost to infrastructure is rerun whole; nothing of
    the lost attempt counts against 20/80; a single LLM call issued again does not count* (R1-NO-TIMEOUT (1) states
    the last part). Alternative: re-attempt only the lost run or call inside the campaign (a partial resume; cheaper,
    but against "no resume" and it needs the controller state restored exactly).
28. **GPU model granularity** (§2): *recommended per node in practice* (the chunk layout puts a node's 18 instances
    in one job, so per-instance across arms implies per node). Alternative: per-instance jobs (more jobs, finer
    placement); not recommended.
29. **Offline–online scope** (§7.5 (e)): *recommended A2, A3 and A5 only* (claim sheet §5 item 7); A0 and A1 join only
    if the post-freeze amendment's test rows exist.
30. **Detectable-difference statement** (§7.3): *recommended: state the design figure (0.319 sd(D) for D.3a, 0.304
    sd(D) for D.3b at power 0.8, Holm's first step) in the paper as the design's sensitivity*, not as a result.
31. **CPU sharing and the T0 per-run budget** (§3.1 item 4; review finding B1): *built and recommended: the row's
    literal condition* — a per-run budget hit or out-of-memory is an infrastructure failure only with another compute
    process on the job's card, recorded per R1-CARD-SHARE (4); a T0 CPU-only budget hit is the proposal's failure. The
    alternative counts CPU sharing as well; it needs (a) a recording rule (the other compute processes on the job's
    host or slot, count, CPU and memory, at start and end) and (b) a repeat that decides: the chunk is repeated on a
    host or slot without other compute processes, so that the same seeds cannot reproduce the same budget hit beside
    another process forever. Draft row (if the author chooses the alternative): "R1-D3-R4-CPUSHARE: a T0 worker run
    of D.3 that reaches the 600 s budget while another compute process shared the job's host CPUs is an infrastructure
    failure; the job record names the host's other compute processes (count, CPU, memory) at start and end; the chunk
    is repeated on a host or slot with no other compute process, and a budget hit there is the proposal's failure."

## 14. Key block

```
frozen: false
signed_by: <pending: author signature>
frozen_utc: <pending>
implements: R1-D3-MIN, R1-MINSUB-CHOICES (4), R1-D3-CHOICES (2), R1-D3B-UNCONDITIONAL, R1-D3-DECOMP, R1-D3-OUTCOMES2, R1-D3-HPO-REF, R1-D3-ORDER, R1-HOST-FREE (2)(c), R1-CARD-SHARE (3), R1-NO-TIMEOUT, R1-STEP-ORDER
revision: 4 (27 Nov 2026; over revision 3, which followed reviews/D3_PREDECLARATION_REVIEW_20261122.md, _R2_, _R3_, _R4_DIFF_)
approved: false
d3_nodes: digits_mlp, openml_breast_w, openml_climate, openml_credit_approval, openml_ionosphere, openml_sonar, tabular_mlp
memory_mode: append_only_summary
W: 20
llm_call_cap: 80 (R1-D3-CHOICES (2)); a call issued again after an infrastructure failure is not counted
trial_budget: 80
instances_per_node: 18
instance_seeds: 6201-6218
smoke_seeds: 6301-6302 on openml_climate (ENGINEERING_ONLY)
smoke_replicate_seeds: 6300 + 10 (s - 6300) + j, j = 1..9 (6311-6319, 6321-6329; ENGINEERING_ONLY)
harness_commit: 9bb416805175149eb87b71f28d77530572aa4bce
verify_seed_check: PASS; vary; verify_runs=2; 20000 + 10 * budget_index + pair_index; indexes 1–80 and pair indexes 0–1; 160 seeds in 20010–20801; checker e44d966f201d15aa627d5399ca2fe7ada0e15958 sha256 62a13172b028b315c92719da5fed184f0bbaa23739d44971259fcc07d9f9f6d2
replicate_seeds: 6500 + 10 i + j, j = 1..9 (6501-6679)
audit_seeds: 6700 + 10 i + k, k = 1..10 (6701-6880)
proposer_seed: D26 manager_seed(instance_id, budget_index, repetition, revision_attempt); ledger root per (stage, arm, repetition)
K: 10
repetitions: 1 (R1-D3-CHOICES (2))
d3a_arms: A0, A0R, A1, A2, FIXR3, EGATE, LADDER
rule_layer_on: A0R, A2, A3, A5, A6 (off: A0, A1, FIXR3, EGATE, LADDER; proposed, §13 item 21)
d3a_family: A0R-A0, A2-A0R, A1-A0, A2-A0, FIXR3-A0, EGATE-A0, LADDER-A0, LADDER-A2; Holm, alpha 0.05, two-sided (8)
d3b_family: A3-A2, A5-A2, A3-A0, A5-A0, A5-A3 (+ A6-A5 if a6_entered); Holm, alpha 0.05, two-sided (5 or 6)
readings: Holm rejection in the direction of the estimate; rule_gain = A2-A0; learned_gain = A3-A2 or A5-A2; rule-layer-alone qualifier (§7.4)
secondary_outcomes: R1-D3-OUTCOMES2 (a)-(f), descriptive (§7.5)
reference_rows: RS (de-duplicated), SMAC3; descriptive; W 20; proposal cap 80 (proposed) (§5.8)
outcome_schema: r1_d3_outcome/v2
gpu_model: one per instance across its arms and stages (R1-HOST-FREE (2)(c)); recorded per row
infrastructure_failures: never an outcome, never a STOP, attempts unlimited; lost chunk rerun whole, nothing charged (§3.1)
d3c: own later pre-declaration (R1-D3-ORDER); not declared here
fixr3: r = 3, one-sided Welch, alpha 0.05
egate: r1/baselines/responses.py PaceStyleGate, alpha 0.1, clip 0.05, max_pairs 8 (as on main)
d3b_arms: A3, A5, always run (R1-D3B-UNCONDITIONAL); A6 only under RUNBOOK P.5, declared by a6_entered in the D.3b note
g: 0.1 sigma_node
noise_source: results/r1/noise/D28_REPAIR_20261027/summary.json sha256 3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310
split_file: r1/c3/splits/c3_p3_split_v1.json sha256 b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569
sweep2_table: proposals.jsonl sha256 379b17ca0783571f87724fc1687d02dfb4084d7ebcec69ab296e855de02197d9, configs.json sha256 de6d63b5e06e541d97dcb2455f75c27649c6b3698e2a7ab4d7193868f1ab0f4d
analysis_preregistration: docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md sha256 aa1a961ba8eb4ab5c45579ea194260597ea3c2a804c731c92ed4ee778d7d7cc5
analysis_script: r1/c3/d3_analysis.py sha256 c0be039905e682e8b1702542e16607f09daf30a59be3363bbdf5a85c64a484ce (revision 4 draft); tests r1/tests/test_d3_analysis.py sha256 c6c56c332d838db0acb2260ad7dc0f1a0ef90cc3bd63849bbe30fd26bf6f01a4
constants_file_sha256: 4f5f686be8f0210bcb27dfe0968296d68cf54e7266fb72c9038e741163776a93
audit_host: deepthought CPUs (R1-MINSUB-CHOICES (4), conditions of R1-SWEEP2-B2-GO)
proposer_host: any host and GPU model with a measured D.3 chunk time on that model; one GPU model per instance across its arms and stages (R1-HOST-FREE (2)(c))
```

## Appendix A. Alternative anytime-valid gate, not adopted (revision 1's construction)

For the record only; not part of the declared design. On paired differences d_j with S_n = Σ_{j<n} d_j and
x_n = S_n/σ_cmp, the one-sided normal mixture E_n = 2/√(n+1) · exp(x_n²/(2(n+1))) · Φ(x_n/√(n+1)) (the half-normal
mixture over λ ≥ 0 of exp(λ x_n − λ² n/2)); commit iff E_n ≥ 1/α = 20 for some n ≤ 5; discard as soon as S_n ≤ 0 or at
n = 5. It commits at a mean d of at least 3.26, 2.07, 1.63, 1.40, 1.24 σ_cmp at n = 1…5. It is a test supermartingale
only if the d_j are sub-Gaussian with variance proxy at most σ_cmp²; since σ_cmp is the median over edits of the
per-edit `sd_joint` (`r1/c3/dataset.py:97-104`), that fails for about half of edits by construction, and the α bound then
does not hold for them. Not adopted because it needs a known σ and `PaceStyleGate` does not, and because
`PaceStyleGate` is the reviewed gate already in the repository (review finding 1).
