# G.5 — T1 label runs on the TASL pair (RTX 4090): authorization draft (approved: false)

**Status: DRAFT for the author's signature. `approved: false`. Not runnable.**
- This document authorizes nothing until the author signs a final version and the coordinating chat publishes it
  to `main` as `docs/r1/authorizations/c3_t1_labels_<YYYYMMDD>.md`, with every prerequisite in §7 recorded as PASS.
- The G.5 job code does not exist yet. It will reuse the reviewed G.1b and G.4 code: environment, data pins,
  cgroup, the isolation gate, server and campaign. Its spec, audit runner and switch need their own reviewed unit
  (§9).
- Written by the Mac-desk agent (Claude), AI-assisted. Revision 6: re-targeted from NEMO2 H200 to the TASL pair
  under R1-T1-HOST-TASL (worker on TASL-2, proposer `llama-server` on TASL-7 over Tailscale, one GPU model: RTX
  4090). Revisions 1–5 (H200) passed rounds 1–4 of the independent review; revision 6 changes the host, the slot
  count, the node list (`mlgym_houseprice` joins), the projection, and adds G5-TASL-GPUH (§2.9) and G5-SLOT (§2.10).
  The label design (§2–§6) is unchanged apart from those.
- Values marked *(proposed)* are recommendations, not decisions. Nine author decisions are open (§2); they interact,
  and §2.8 shows them together.

## 1. Authority (published `main` `4aac5209`; the 21 Nov rows on branch `author-decisions-20261121` `e5e452a0`, reaching `main`)

| Row | What it fixes here |
|---|---|
| R1-T1-HOST-TASL (21 Nov; amends the Ada fallback of R1-T1-HOST-H200) | The isolation fails in the HTCondor container on H200 (job 759828) and Ada is occupied, so the T1 table (G.1b, G.4, G.5) runs on the two RTX 4090 hosts: worker (training) on TASL-2 under the harness isolation; the proposer `llama-server` (gemma4_31b, exam settings: context 32,768, `-ngl 999 -np 1 --jinja`, q8_0 KV, `cache_prompt` false, `{"enable_thinking":false}`) on TASL-7 over Tailscale. G.1b may use both hosts' GPUs. One GPU model (RTX 4090) for the whole table. Precondition: the host checks pass on TASL-2 (and on TASL-7 if it runs workers); otherwise STOP. |
| R1-TRACKG-AR-U2-TASL2 (21 Nov) | `autoresearch_fixedtokens`' cond7a smoke and U2 move to TASL-2; the harness-isolation host checks pass on TASL-2 first. |
| R1-TRACKG-G3-EARLY | T1 nodes: `mlab_cifar10`, `mlab_imdb`, `mlab_ogbn_arxiv`, `mlgym_cifar10`, `mlgym_fmnist`, `mlgym_breakout_minatar`. `autoresearch_fixedtokens` and `mlgym_houseprice` "join as soon as their U2 passes". `mlgym_houseprice`'s U2 passed in the U4 census (20 Nov; CPU-only), so this draft carries **seven** nodes; autoresearch joins after its U2 on TASL-2. |
| R1-BX-D1, R1-BX-D5 | T1 nodes are label nodes; the nodes' fixed step budgets; one GPU model per table. |
| D1 | The campaign budget is compute (worker runs) plus an LLM-call cap (see G5-W). |
| D15, D26 | Manager temperature 0.2; every manager call carries a seed derived deterministically from (instance, trial index, repetition), recorded in its call event (see G5-TEMP). |
| R1-BX-D3, R1-BX-PROPOSED-CONFIRM (D3; Track G E4) | Audit seeds K = 6 (labels 7001–7003, evaluation 7006–7008) for T1 **only after** the sweep-1 subsampling check passes and a PLAN row records it; until then **K = 10**. If the check fails, K stays 10 and the coordinating agent STOPs for the author. E4 also says "both memory modes; about 12 campaigns per T1 node" (see G5-MEM). |
| R1-BX-PROPOSED-CONFIRM (E5) | Divergence = a non-finite loss, or no metric at the fixed budget. A divergent proposal enters no belief bin, is counted separately, and has action target u = −g. If only some seeds diverge, μ comes from the rest and the label is marked partial; more than half diverging makes the proposal divergent. A heavy-tailed node uses a Student-t, declared before labels are built. |
| R1-MAIN-PROPOSER (e) | Duplicates are grouped by (instance, incumbent hash, edit hash) for folds and deduplication; one instance → train/dev/test assignment; pooled intervals use an instance-cluster bootstrap. |
| R1-BX-D8-V3-A (3) | Split per tier P3 = 1/3 : 1/6 : 1/2 (train : validation : test), written into the analysis preregistration. |
| R1-BX-D8-V3-B (author's addition) | **T1 = 12 instances per node**; per-tier test floor T1 ≥ 3 test instances per node; a node below the floor is excluded from the IQM, kept in the PoI and reported. |
| R1-BX-D8-CONFIRM (17 Nov) | Gate `r1/c3/gate.py` @ `6aa9985c`, sha256 `ffb70d7a…`; T0 and T1 pooled with tier as a stratum; partial T1 at B.7 read on T0 plus the labelled T1 nodes, disclosed; leave-one-suite-out needs at least one labelled T1 node per suite. "Existing preregistration and analysis gates remain in force. Sweep-2 label tables may be analysed from this row on." It is committed, so the readers' `R1-BX-D8-CONFIRM` lock no longer gates anything; the T1 seal therefore needs its own release rows (§6). |
| R1-MAIN-PROPOSER, R1-EXAM-X7, R1-SWEEP2-SETTINGS (1) | Proposer `gemma4_31b`, thinking off, the exam server flags, context 32,768, `cache_prompt` false. |
| R1-EXAM-B1-TRUNCATION-INVALID | Every proposer call carries a completion cap; a truncated reply is an invalid proposal. |
| R1-BX-PROPOSED-CONFIRM (D4) | `manager_proposal/v2-diff`. A pick that fails diff liveness on a T1 node is a STOP; the author decides between a single-parameter fallback and moving the node to T2. |
| R1-TRACKG-G5-DIVERGENCE (4 Nov) | Asked "whether a T1 node should STOP when its audited label proposals' divergence fraction exceeds 20 %, or instead be judged case by case", the author replied "设 20% STOP" (set a 20 % STOP). The recorder's *(proposed)* consequence: a move to T2 needs a separate author row. The 20 % "originated as an agent proposal, not a measured threshold". |
| R1-TRACKG-PORT-DECISIONS (3), (4) | (3) The port-written imdb baseline is frozen and independently reviewed before any label run, and the census funnel and appendix say "baseline written by us". (4) Timeout = 3 × the census baseline run time; a timeout is the proposal's failure, not an infrastructure rerun. |
| R1-HARNESS-ISOLATION | Every T1 label run is effectively isolated: `effective: true`, `waivers {}`, `exceptions []`. Anything else is refused. |
| R1-B2-DECOUPLE, 28 Oct clarification | Labels use the label seeds; the evaluation seeds are never used for C3 or Track P training, tuning or selection. |
| (draft) R1-T1-TASL-ENV | No container on the TASL pair, so no image row: the host/environment row (drafted with R1-G1B-EDITS and R1-G1B-TIMEOUT) fixes the hosts, the census environments by freeze sha256, the harness checkout, the GPU lease, the delegated scope, and the proposer's `llama-server` binary and build (prerequisite P9). |

**The v2-diff engine as it is** (harness `af480809`, the TASL G.1b and G.4 pin; it adds only `--gpu-uuid` and CPU-only
chunks to `b5747066`): one manager call per proposal; a
temperature parameter (its original default 0.0; the G.4 pilot passes 0.2); a per-call seed
`sha256("<manager seed>:<step>")[:8]`, deterministic in (instance, trial index), repetition 0; a memory parameter
with two modes: `history` (the prompt shows the campaign's own last 12 steps: summary → decision (metric)) and
`none` (no history). Neither mode is T0's `append_only_summary`, which keeps a summary file. Within a campaign, inert
proposals and duplicates of an earlier step are not run.

## 2. Author decisions (each with options and a recommendation)

### 2.1 G5-W: what W = 20 counts (recommendation: A)

The 20 Nov task says "W = 20, ~150 audited proposals/node". The G.4 pilot and the v2-diff engine count W in manager
calls. D1, sweeps 1 and 2 (`--runs 20`) and R1-W2-3-STOP count W in worker runs.

- **A (recommended): 20 manager calls per campaign.** 240 × ran share audited proposals per node (144 at share 0.6,
  192 at 0.8, §2.8), close to the task's "~150". The engine supports it today.
  - The label definition does not depend on W, but the population of labelled proposals does: about 12–16 runs per
    T1 campaign against 20 on T0, so T1 proposals come from earlier, weaker incumbents and lower trial indices.
    With tier as a stratum in the gate this is a disclosed difference between tiers.
  - R1-W2-3-STOP (every Track P source ledger uses exactly 20 worker runs) concerns the sweep data rebuild; a T1
    ledger would fail that check. Any Track P use of T1 ledgers needs its own author row.
- **B: 20 worker runs plus an LLM-call cap of 80 per campaign.** Matches D1 and the sweeps; 240 audited proposals
  per node; 1.6 × the GPU-hours of A at ran share 0.6 and 1.23 × at 0.8 (§2.8). Needs a worker-run budget in the
  v2-diff engine (code unit, §9) and then a re-run of the G.4 pilot with it (P3), which moves the dates.

The audited band of STOP 9 depends on this choice: *(proposed)* 100–200 under A, 150–240 under B (B gives 240 ran
proposals per node, fewer audited after cross-instance duplicates).

### 2.2 G5-TEMP: the proposer temperature (recommendation: A)

- **A (recommended): temperature 0.2 (D15) with the engine's per-call seed rule.** The engine has the parameter since
  `24935be3`, and the G.4 pilot runs at 0.2, so the pilot's shares are measured under the setting G.5 uses. The seed
  rule meets D26's determinism (instance, trial index, repetition 0) but is not T0's derivation function; disclosed.
- **B: temperature 0 (the engine's original default).** Fully deterministic on a deterministic server. At step 1
  every instance of a node sees the same prompt (baseline code, no history), so all 12 instances make the same first
  proposal; instances diverge only through the metrics that later enter the history. More cross-instance
  duplicates, less diversity; a disclosed deviation from D15. The pilot would have to be re-run at 0.

### 2.3 G5-MEM: memory mode (recommendation: A)

E4 says "both memory modes; about 12 campaigns per T1 node"; V3-B says 12 instances per node.

- **A (recommended): the engine's `history` mode only, 12 instances.** 12 campaigns per node, as E4 counts them; 6
  test instances under P3, above the floor of 3. Disclosed as different from both T0 modes. **It amends E4's "both
  memory modes" and needs an author row saying so.** The memory contrast stays on T0, where both modes run.
- **B: both engine modes (`history` and `none`), 12 instances each** (twin campaigns sharing instance seeds; labels
  shared by the (instance, incumbent, edit) key, R1-MAIN-PROPOSER (e)). About 2 × the cost (§2.8, an upper bound).
  `none` exists in the engine since `24935be3`. Neither mode is T0's `append_only_summary`; a T0-matching rendering
  would be new engine work.
- **C: both modes, 6 instances each.** 12 campaigns per node, but only 3 test instances: exactly at the floor, and it
  contradicts V3-B's 12 instances.

### 2.4 G5-AUDIT: which proposals are audited, and duplicates (recommendation: A)

- **A (recommended): as C3_DESIGN §4 and the sweep-1 authorization:** every non-inert, non-duplicate evaluated
  proposal, **including** proposals that diverged or timed out in the campaign, and its parent incumbent, at the K
  audit seeds with joint seeds. No-ops are labelled by rule.
  - *(proposed)* **Parent runs reused.** A kept proposal's audit runs at the audit seeds serve again when it is the
    parent incumbent of later proposals (same code state, same seeds). This relies on fixed-seed determinism of
    **edited** code states on the RTX 4090; G.1b checks it only for each node's baseline and declared edits at the default
    seeds, so cluster test C2 checks it for audit pairs. If C2 fails, or the author prefers, every parent is re-run
    (`reuse_parent_runs: false`: 188.3 GPU-h in the recommended row at ran share 0.6, seven nodes, still within cap B).
  - **E5 per seed block.** A proposal's label status (divergent, partial or not) is decided by E5 over the **label
    seeds** only (7001–7005, or 7001–7003 at K = 6). Divergence on the evaluation seeds is part of the evaluation
    value `y_eval` and is handled in the analysis preregistration; it never changes a training label, the divergence
    STOP or a pre-release count (R1-B2-DECOUPLE). Applying E5 over all K seeds would let evaluation-seed outcomes
    decide labels and remove nodes, and would need an author row amending R1-B2-DECOUPLE; not recommended.
  - **Duplicate key** (R1-MAIN-PROPOSER (e)): (instance, incumbent hash, candidate hash). Within an instance, the
    engine does not run a duplicate, so it gets no label.
  - **Across instances**, the same (node, incumbent hash, candidate hash) can recur (most at step 1, where every
    instance starts from the baseline). Because the audits use common seeds, its label would be the same in every
    instance. *(proposed)* Such a group is audited once and every member carries the label, so coverage does not
    depend on job order. For the gate, the test-side members of a group that also occurs on a train or validation
    instance are left out of the primary test population and kept in a secondary full population, and the
    validation-side members of a group that also occurs on a train instance are left out of the primary
    validation population (where arms are selected) and kept in a secondary one, disclosed (the same rule as
    R1-TRACKP-SFT-DUP for Track P). The sweep-2 analysis preregistration fixes this rule before release.
  - The G.4 pilot reports the cross-instance duplicate rate (P3).
- **B: every proposal with an `ok` campaign outcome.** Cheaper by the in-campaign divergent share, but in-campaign
  divergent proposals never get E5's seed-level test. It also weakens G5-DIV A, whose denominator is the audited
  proposals (§2.5). Not recommended.

### 2.5 G5-DIV: the divergence STOP (recommendation: A)

The 20 Nov task adds "divergence > 2 × census".

- **Literal census reading.** Each census node has one deliberately divergent record (the broken diff, `s002`) among
  8 executed records: 12.5 %, so 2 × census = 25 %. It is looser than 20 % and never binds.
- **A (recommended): the author's 20 % rule, on the denominator the author was asked about.** The task's
  "2 × census" STOP is kept in its literal reading (25 %, on the same denominator); it never binds below 20 %, and
  the note says so.
  - Denominator: the node's **audited** label proposals. It therefore depends on G5-AUDIT: under AUDIT B the
    in-campaign divergent proposals are not in it, and the rule is weaker.
  - Numerator: proposals that are divergent under E5 on the **label seeds** (more than half of them divergent;
    G5-AUDIT, E5 per seed block). The evaluation seeds never enter the STOP.
  - Evaluated at the end of each wave's audits (§3), once the node has at least 40 audited proposals. If wave 1 gives
    fewer than 40, the first evaluation is at the end of wave 2, and wave 1's rate is an early warning only.
  - The noise at a small count: at n = 40, a node whose true E5 rate is 15 % STOPs with probability 0.135, and one at
    18 % with 0.286 (binomial, X ≥ 9); at n = 130 the 15 % figure is 0.047. The alternative of a single evaluation
    at the end of wave 2 lowers the false STOP but lets most of the spend happen first.
  - Early warning (not a STOP): the in-campaign single-seed divergent share per proposal after each wave, reported
    to the author when above 20 %.
- **B: min(20 %, max(2 × the upper 95 % Clopper–Pearson bound of the G.4 pilot's rate, 10 %)) on the same
  denominator**, for the three pilot nodes; the others use 20 %. The pilot runs no audits, so it measures only the
  single-seed divergent share per proposal (`divergent_of_proposals`), a different quantity, on 60 proposals.
- **C: 2 × the G.1b divergent-row rate of the node, capped at 20 %.** Exists for all seven nodes on the 4090, but G.1b
  measures declared edits, not LLM proposals.

### 2.6 G5-CAP: the GPU-hour cap (recommendation: B)

Under W A, MEM A, AUDIT A (§2.8; seven nodes, worker-card hours, G5-TASL-GPUH A): 119–144 GPU-h at K = 6 and
167–206 GPU-h at K = 10 (ran share 0.6–0.8). Direct host runs have no scheduler, so there are no requested slot-hours;
the binding quantity is the worker card's wall time (G5-SLOT).

- **A: 150 GPU-h, with K = 6 only;** K = 10 is an author STOP.
- **B (recommended): 230 GPU-h** of the worker card, which covers K = 10 at ran share ≤ 0.8 under W A / MEM A / AUDIT
  A (24 h, 10 %, margin at 0.8). Any other combination of §2.8 needs the cap of its row instead.
- **C: 150 GPU-h with audits limited to a pre-declared random subset of the auditable proposals** (seeded, fixed
  before any campaign runs). Changes label coverage; not recommended.

Under every option: the projection and the consumed worker GPU-hours (a running meter from the job records) within
the cap. The proposer card's hours are reported beside them (G5-TASL-GPUH).

### 2.7 G5-SPLIT: the instance split, fixed now *(proposed)*

Per node, the 12 instances are ordered by `sha256("c3_t1_split/v1:" + <node> + ":" + <instance seed>)`. The first 6
are test, the next 2 validation, the remaining 4 train (P3 = 1/2 : 1/6 : 1/3 of 12). The signed note records the
resulting assignment and its sha256; the per-instance diagnostics are read only after the split exists.

### 2.8 The decisions together (pre-pilot, `sweep2/t1_tasl/g5_projection_tasl.py`)

Worker GPU-hours and audited proposals per node, seven nodes (census run times on the RTX 6000 Ada × 1.0, LLM 60 s per
call; the 4090 values replace both after the G.4 pilot). AUDIT A; cross-instance duplicate factor 1.0 (conservative;
the pilot measures it); parents = the 12 baselines (a kept proposal's audit runs serve again when it is a later
parent: same code state, same seeds, on a fixed-seed-deterministic host); MEM "both" is an upper bound (twin campaigns
share labels by key).

| W | MEM | Ran share | K = 6 GPU-h | K = 10 GPU-h | Audited per node |
|---|---|---|---|---|---|
| A: 20 calls | A: one mode | 0.6 | 118.7 | 166.9 | 144 |
| A: 20 calls | A: one mode | 0.8 | 143.8 | 206.2 | 192 |
| A: 20 calls | B: both | 0.6 | 237.5 | 333.8 | 288 |
| A: 20 calls | B: both | 0.8 | 287.5 | 412.4 | 384 |
| B: 20 runs, cap 80 calls | A: one mode | 0.6 | 189.6 | 265.5 | 240 |
| B: 20 runs, cap 80 calls | A: one mode | 0.8 | 177.6 | 253.6 | 240 |
| B: 20 runs, cap 80 calls | B: both | 0.6 | 379.2 | 531.0 | 480 |
| B: 20 runs, cap 80 calls | B: both | 0.8 | 355.3 | 507.1 | 480 |

With one worker slot (G5-SLOT) these hours are also the label span in hours: the recommended row at K = 10 is 7.0–8.6
days of the worker card alone.

### 2.9 G5-TASL-GPUH: which card's hours count against the cap (recommendation: A)

On H200 one card carried the server and the worker. On the TASL pair the proposer holds TASL-7's card for the whole
campaign span while the worker uses TASL-2's.

- **A (recommended): the cap counts the worker card (TASL-2).** The proposer card's held hours (campaign spans) are
  metered and reported beside it, not capped. The 230 GPU-h of G5-CAP B were sized on worker plus server work on one
  card, so A is the closer like-for-like.
- **B: both cards count.** The campaign spans count twice. At K = 10, W A, MEM A, ran share 0.6 the total is about
  167 + the campaign hours; cap B would need raising.

### 2.10 G5-SLOT: one worker slot, and TASL-7 (recommendation: A)

TASL-7's card serves the proposer for the table's span (it holds TASL-7's GPU lease), so G.5 has **one** worker slot
(TASL-2). G.1b must be complete before the server starts (both use TASL-7's lease).

- **A (recommended): one slot, nodes in sequence on TASL-2.** Pre-pilot, `g4_tasl.py dates` gives labels done
  4 Dec, B.7 7 Dec (1 day of slack against R1-BX-D14's 8 Dec) at ran share 0.6 and LLM 60 s per call; 9 Dec (−1 day)
  at 0.8 or at 120 s per call. The 4090's LLM speed for a 31B Q4 model on one card is the main unknown; the G.4 pilot
  measures it.
- **B: audits on TASL-7 while campaigns pause.** The audit chunks need no proposer, so TASL-7's card could run audits
  between the waves when the server is stopped. This needs TASL-7's host checks (R1-T1-HOST-TASL's precondition) and
  a server restart per wave (identity re-checked each time); about 30–40 % shorter label span. Not built.

## 3. What the label table is, and the order of work

For each T1 node:
- 12 root campaign instances of `run_v2_diff_campaign`, memory mode per G5-MEM, W per G5-W, temperature per
  G5-TEMP, with the record gate (`noise_floor.check_effective`) and the timeout basis of the table's noise floor
  (§4 item 8).
- **Order:** (1) wave-1 campaigns (instances 1–4); (2) wave-1 audits; (3) the G5-DIV, band, liveness and invalid-share
  checks on the sealed diagnostics; (4) wave-2 campaigns (instances 5–12); (5) wave-2 audits; (6) the checks again.
  A STOP at (3) halts the node before wave 2.
- Audits per G5-AUDIT: paired fresh-seed re-runs of the proposal's code state and its parent incumbent at the K audit
  seeds with joint seeds (training seed = split seed = s, `"vary"` split), so each seed gives a paired d_s, as in
  C3_DESIGN §4 and the sweep-1 B.2 audit. Audits run in chunks, each under the walltime limit.
- Labels and keep decisions use the validation metric. The sealed task test metric is never read for labels or
  selection.

The soft-label width comes from the G.1b noise floor on the same RTX 4090 environment (TASL-2 or TASL-7, the same
census freeze and harness pin; R1-T1-HOST-TASL): σ̂_node is the G.1b `joint`
σ (seeds 3001–3030, `"vary"` split), and the width is s = σ̂_node/√K_label (R1-BX-D3). Before any label is
assembled, each node is declared Gaussian or Student-t from the G.1b summary (E5; prerequisite P10).

## 4. STOPs

Every G.1b STOP (plan §7) and every G.4 STOP (plan §7) applies to the G.5 jobs: spec and authority, host identity,
the GPU lease and foreign compute processes, root uid, GPU UUID and model, Yama `ptrace_scope`, the delegated scope,
the harness checkout at the pin and clean, environment freeze, data manifest, GGUF and `llama-server` sha256 and
build on TASL-7, the server's `/props` before and after each wave, the 4090 timing STOP, the deadline, and the launch
binding. In addition:

1. **Divergence** (G5-DIV). The rule the author chooses, evaluated as stated there. The STOP halts the node; a move
   to T2 needs a separate author row.
2. **Isolation.** Any run record that is not `effective: true` with empty waivers and exceptions STOPs that job
   (`stop_unisolated`), with the evidence kept. No waiver for label runs.
3. **Diff liveness** (D4). *(proposed)* A node whose ran-of-valid share is below 0.25 (absolute; the same for every
   node) after wave 1 STOPs. The author decides between a single-parameter fallback and T2.
4. **Proposer output.** A truncated reply is invalid (completion cap 4,096 tokens). A node whose invalid share
   (parse failures, truncations, refusals) exceeds 0.2 of its manager calls in a wave STOPs (as sweep 2's
   `max_parse_failure_rate`). A prompt longer than 32,768 − 4,096 tokens STOPs the campaign.
5. **Noise floor.** A node that does not qualify under D21 at G.1b, or fails fixed-seed determinism, is not run in
   G.5: a STOP for that node; the author decides on T2 (R1-BX-D12 discloses it). No node is dropped silently.
6. **Integrity, transport, baseline.** A `stop_integrity`, `stop_transport` or `baseline_failed` ledger line STOPs
   that job. A failed job is resubmitted only as a new attempt after diagnosis, never resumed.
7. **Infrastructure.** Final infrastructure failures (after 2 reruns) above 5 % of a node's proposals STOP the node
   *(proposed)*.
8. **Timeout.** The timeout basis is the one the author fixes for the noise floor (R1-G1B-TIMEOUT), so the noise
   floor and the labels share it (on the 4090, a G.1b run reaching it is already a STOP). A timeout is the proposal's divergent failure (E5 over the label seeds).
   A **baseline** timeout STOPs the campaign.
9. **Budget.** The projection or the consumed GPU-hours above the cap (G5-CAP; worker card per G5-TASL-GPUH); a job
   past its declared deadline; *(proposed)* an audited count per node after wave 1, extrapolated to 12 instances, outside the band of G5-W (100–200 under A, 150–240 under B; doubled under MEM B). The cross-instance
   duplicate share seen in 4 instances understates the share for 12, so the extrapolation overstates the audited count.
   The author then decides: accept, change W, or cap the audits.
10. **Seeds.** Any use of the evaluation seeds outside the audit's evaluation block, or of label seeds 7004–7005 when
    K = 6, is a STOP. The G.5 validator refuses every other reserved block (below).
11. **Reading.** Any read of sealed content before its release step (§6) is a STOP and is reported.
12. **Proposer.** The TASL-7 server unreachable over Tailscale, restarted, or with `/props` (context, slots, build,
    GGUF) different from the server record STOPs the job (infrastructure); the wave is re-run as a new attempt after
    the identity is re-checked, never resumed.

**After a node STOP**, the node's partial outputs stay sealed and kept. Whether its labelled instances enter the
table is decided by an author row; they count toward B.7 only if that row says so and the node has at least 3 labelled
test instances.

## 5. Key values (the final note carries these lines; the G.5 switch matches every one)

```
approved: false
label: EVIDENCE
run_id: c3_t1_labels_<YYYYMMDD>
hosts: worker TASL-2 (RTX 4090 <UUID>), proposer TASL-7 (RTX 4090 <UUID>) over Tailscale <server URL>
host_authority: R1-T1-HOST-TASL; environment row <R1-T1-TASL-ENV (P9)>
environments: torch312 d2e70fe4…, jax312 80a455c6… (census freezes)
llama_server_sha256: <as in the G.4 note>; build <as in the G.4 note>
gguf_sha256: 2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75
harness_commit: <the reviewed G.5 harness commit; its measurement path is byte-identical to the G.1b pin (P5)>
g1b_harness_commit: af4808097283f67f99a14ac2c3e1936b957996ab
gpu_model: NVIDIA GeForce RTX 4090 (campaigns and audits on TASL-2; server on TASL-7)
nodes: mlab_cifar10,mlab_imdb,mlab_ogbn_arxiv,mlgym_cifar10,mlgym_fmnist,mlgym_breakout_minatar,mlgym_houseprice (CPU-only)
instances_per_node: 12 (per memory mode under G5-MEM B)
instance_seeds: 5101-5112 (instance k: training = split = manager seed 5100 + k)
instance_split: <G5-SPLIT assignment and its sha256>
memory_mode: <G5-MEM: history | history and none>
campaign_W: 20 <manager calls | worker runs with an LLM-call cap of 80> (G5-W)
proposer: gemma4_31b (thinking off; exam flags; context 32768; cache_prompt false)
temperature: <G5-TEMP: 0.2 | 0.0>; per-call seed sha256("<manager seed>:<step>")[:8]
completion_cap_tokens: 4096
proposal_schema: manager_proposal/v2-diff
timeout_basis: <G1B-TIMEOUT>
audit_K: <10, or 6 only after the K-check PASS row; uniform within the table>
audit_seeds_label: <7001-7005 for K = 10; 7001-7003 for K = 6>
audit_seeds_evaluation: <7006-7010 for K = 10; 7006-7008 for K = 6>
audit_scope: <G5-AUDIT>; duplicate key (instance, incumbent hash, candidate hash); cross-instance groups audited once
divergence_stop: <G5-DIV>
liveness_floor: 0.25 (proposed)
audited_band: <per G5-W> (proposed)
noise_floor: <G.1b run id and summary sha256>
tails: <per node Gaussian or Student-t (P10)>
job_layout: per node on TASL-2 in sequence (G5-SLOT), wave 1 (4 instances) campaigns then audits, wave 2 (8 instances) campaigns then audits; audits in chunks with declared deadlines
gpu_hours: <projection per §8>
cap_gpu_hours: <G5-CAP>, counted per <G5-TASL-GPUH>
proposer_card_hours: <metered and reported>
release_rows: R1-T1-LABELS-UNSEAL (train and validation), R1-T1-LABELS-TEST-RELEASE (test) (§6)
```

*(proposed)* The instance seed block 5101–5112 is disjoint from G.1b (1001–3030), G.4 (4001–4099), the census seeds
(8001–8010), the audit seeds (7001–7010) and the exam seeds (9001+, including 9101+ and 9201+). It avoids
5001–5006, the E1b audit seeds on the CPU nodes.

## 6. Sealing and staged release

**The seal is procedural.** The operator, the cluster agent and the author work under one account (`dowling`) on the TASL
hosts, so file modes restrict nobody. *(proposed alternative, needs a cluster test: encrypt `out.tar` inside
the job to a release public key held by the author.)* What makes the procedural seal checkable:
- **Writing.** The campaign ledgers, the audit records, every per-proposal value **and every log** (`llama-server.log`
  and the job's run log carry prompts, and prompts carry per-step metric values) go only into the job's `out.tar`.
  In clear, the job transfers only `out.tar`, `diagnostics.json`, `job_record.json` and `SHA256SUMS`.
- `diagnostics.json` has a fixed schema: counts and shares only (proposals, valid, invalid, truncated, ran, inert,
  duplicate, divergent in campaign, timed out, kept; audited, E5-divergent on the label seeds (no evaluation-seed
  count before release); cross-instance duplicate groups; prompt
  and completion token percentiles; GPU-seconds; STOP state). `job_record.json` has a fixed schema too. Neither holds
  a metric value, delta, label or keep outcome per proposal.
- The seal step verifies the sums, never overwrites, and records the sha256 of every file in its receipt. An access
  log in the sealed run directory records every opening of `out.tar` (who, when, why); STOP 11 applies to any other.
- What this can and cannot show: the receipt hashes **detect changes** to sealed content; they cannot detect a
  **read**. Reads are governed only by STOP 11 and the access log, which rest on the operators' and agents'
  compliance. The encryption alternative would make an early read impossible rather than forbidden.

**Before release**, operators, agents, reviewers and the author open only `diagnostics.json`, the job records and
the seal receipts. These are enough for every STOP in §4.

**Release** is staged, with one author row per stage. Every T1 label reader (the table assembly, the C3 training
pipeline, the gate run, any Track P loader) refuses to run without the row of its stage; this is a P5 code
requirement with a test.
1. **R1-T1-LABELS-UNSEAL** cites the sha256 of the analysis preregistration (P3 split, gate v3, floors, the
   duplicate rule of G5-AUDIT) and of the instance-split file. It releases the **train and validation** partitions
   to the C3 training pipeline: arms are trained on train and selected on validation. Track P reads them only if the
   author says so in a row.
2. **R1-T1-LABELS-TEST-RELEASE** cites the sha256s of the fixed arms (checkpoints and calibration maps). It releases
   the **test** partition to the gate run only.
3. The sealed task test metric is never released.

Partial T1 at B.7 follows R1-BX-D8-CONFIRM: the gate is read on T0 plus the labelled T1 nodes, with the count
disclosed. **Leave-one-suite-out risk:** the seven current T1 nodes are in two suites (MLAgentBench, MLGym). Under
R1-BX-D8-CONFIRM, leave-one-suite-out STOPs at B.7 unless `autoresearch_fixedtokens` (or another node of the third
suite) has labelled T1 instances by then; the aggregate gate does not STOP on it.

**Breakout.** `mlgym_breakout_minatar`'s evaluation keys are public constants (port report §6.2). The labels use the
validation return only, inside the isolated worker, and the sealed test return is never read; disclosed in the
appendix.

## 7. Prerequisites (each PASS in the final note)

- **P1** — R1-T1-HOST-TASL: the harness-isolation host checks pass on TASL-2 (and on TASL-7 if G.1b ran workers
  there), recorded with their sha256.
- **P2** — G.1b complete on the TASL pair (`sweep2/t1_tasl/g1b_tasl.py`): D21 verdicts per node, the summary
  assembled from the sealed node directories of both hosts.
- **P3** — G.4 pilot run and read **with the W, memory mode and temperature the author decides here** (otherwise it is
  re-run or amended first): liveness, invalid, refusal and per-proposal divergence shares per node; the
  cross-instance duplicate rate; the R1-BX-D14 dates recomputed (`g4_lib.recompute_dates`, which models this table)
  and reported (`g4_tasl.py dates`, one slot).
- **P4** — K: the K-check PASS row (K = 6), or K = 10 recorded; if the check fails, the coordinating agent STOPs for
  the author (R1-BX-D3). K is uniform within the T1 table.
- **P5** — G.5 job code (spec, campaigns in waves, audit runner, diagnostics, release locks, switch) independently
  reviewed at the launch commit. Its harness commit descends from the G.1b pin, and the measurement path is
  byte-identical between the two commits, so the noise floor and the labels share it. The path is all of
  `src/autoresearch/trackg/` except the v2-diff engine files the labels may change (`manager_v2_diff.py`,
  `campaign_v2_diff.py`, `proposal_v2_diff.py`, `pilot_g4.py`), plus `nodes/`, `third_party/`, `configs/trackg/`,
  `node_lib/`, and every module outside `trackg/` in the import closure of `noise_floor` (the validator computes the
  closure and runs `git diff --quiet <g1b pin> <g5 pin> -- <paths>` over the files present at the G.1b pin). New
  files that G.5 adds — the audit runner and the diagnostics writer, *(proposed)* `trackg/audit_g5.py` and
  `trackg/diagnostics_g5.py` — are allowed if they are outside the import closure of `noise_floor` (the validator
  checks that none of the measurement-path modules imports them). A change such as the R1-TRACKG-AR-COND7
  `ar_isolated.cuda_open` fix therefore fails the check and needs a new noise floor or an author row.
- **P6** — author decisions recorded: G5-W, G5-TEMP, G5-MEM (with the row amending E4 under A), G5-AUDIT (with the
  duplicate rule), G5-DIV, G5-CAP, G5-SPLIT, the liveness floor and the audited band, and the G.1b decisions
  R1-G1B-EDITS and R1-G1B-TIMEOUT, and G5-TASL-GPUH and G5-SLOT.
- **P7** — the §8 projection, recomputed from the pilot medians, is within the cap.
- **P8** — the imdb baseline frozen and independently reviewed (R1-TRACKG-PORT-DECISIONS (3)); the review cited.
- **P9** — the host/environment row R1-T1-TASL-ENV (in place of the image row; G.1b, G.4 and G.5 use it).
- **P10** — per node, the Gaussian or Student-t declaration from the G.1b summary, recorded before any label is
  assembled (E5).
- **P11** — host tests C1–C11 below PASS, in particular C3 (run time on the TASL-2 4090 against the timeout basis)
  and C10 (the proposer link over Tailscale).

## 8. Projection (pre-pilot; recomputed from the pilot before signature)

One formula serves this note and the G.4 recompute: `g4_lib.g5_node` (`sweep2/g4/g5_projection.py` prints §2.8).
Per node, with r the census baseline run time and s the ran share (ran proposals per manager call):
- campaigns: manager calls × (60 s LLM + s × r × 1.25 + the instance baseline amortized), with 240 calls under W A;
- audits: (audited + 12 baselines) × K × r × 1.25, with audited = ran × the cross-instance duplicate factor (1.0
  before the pilot; inert proposals and in-campaign duplicates are not run at all); a kept proposal's audit runs
  serve again when it is a later parent (`reuse_parent_runs`; re-running every parent adds 0.2 × ran per node);
- startup: 1,500 s per job (2 campaign waves + the audit chunks; kept from the H200 model as a conservative
  allowance, since the server stays up on TASL-7 between jobs).

The factor 1.25 covers slower edited runs and timeouts; the 4090's speed is unmeasured (C3). After the pilot,
`g4_tasl.py dates` (`g4_lib.recompute_dates` with one slot) uses each pilot node's measured 4090 seconds per call,
run median and shares, the census time × the measured 4090/census ratio elsewhere, the measured cross-instance
duplicate rate, the memory-mode factor of G5-MEM, and the cap of G5-CAP; its label span is the larger of total / slots
and the longest node's serial work. That result is the binding P7 number.

Adding `autoresearch_fixedtokens` later needs its own 4090 noise floor, its own projection and,
*(proposed)*, an amendment of this note.

## 9. What remains to build (one reviewed unit, after G.4)

- The G.5 spec and job: 12 instances per node in two waves with the audits between them, built on `g4_lib` /
  `pilot_g4`, with the instance seed block, the memory mode and temperature, and, under G5-W B, a worker-run budget
  with an LLM-call cap in the v2-diff engine; built on `sweep2/t1_tasl/g4_tasl.py` (worker on TASL-2, the remote
  proposer's identity checked per wave).
- The audit runner: re-materialise each audited proposal's code state and its parent from the ledger; group
  cross-instance duplicates; paired fresh-seed re-runs through `noise_floor`-style chunks with the isolation gate; E5
  per proposal.
- `diagnostics.json` and `job_record.json` with fixed schemas, the logs inside `out.tar`, and the STOP counters on the
  diagnostics, without reading labels.
- The seal step with the receipt hashes and the access log, the assembly, and the two release locks in every reader,
  with tests.
- The measurement-path identity check between the G.1b and G.5 harness pins.
- The switch with the key values of §5 and the S2-C5 launch binding.

## 10. Needs a cluster test

- **C1.** Everything in the TASL plan (`sweep2/t1_tasl/T1_TASL_PLAN.md` §6).
- **C2.** The audit runner on the TASL-2 4090: re-materialisation, isolated joint-seed runs, fixed-seed determinism of audit
  pairs (which the reuse of parent runs relies on), and E5 per seed block (label seeds only for labels and the STOP).
- **C3.** Run time on the TASL-2 4090 against the timeout basis (false divergence).
- **C4.** Diagnostics out per wave and per audit chunk, so the STOPs act early.
- **C5.** The audit-chunk deadlines for the K = 10 imdb and Breakout audits.
- **C6.** The seal: under the shared operator account file modes restrict nobody, so either the procedural seal
  (receipt hashes, access log) is exercised end to end, or the encryption alternative works end to end.
- **C7.** The resident GGUF on TASL-7 (no per-job transfer) and the one worker slot (G5-SLOT).
- **C8.** The cross-instance identical-proposal rate at the chosen temperature, from the G.4 pilot's instances.
- **C9.** The worker GPU-hour meter against the cap under the chosen W, MEM and K, with the proposer card's hours
  beside it.
- **C10.** The proposer link over Tailscale for a multi-day span: reachability, per-call latency, a server restart
  handled as an infrastructure STOP with the identity re-checked.
- **C11.** TASL-7's lease: the server holds it for the table's span; G.1b on TASL-7 finished before.
