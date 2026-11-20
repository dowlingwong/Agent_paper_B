# G.5 — T1 label runs on NEMO2 H200: authorization draft (approved: false)

**Status: DRAFT for the author's signature. `approved: false`. Not runnable.**
- This document authorizes nothing until the author signs a final version and the coordinating chat publishes it
  to `main` as `docs/r1/authorizations/c3_t1_labels_<YYYYMMDD>.md`, with every prerequisite in §7 recorded as PASS.
- The G.5 job code does not exist yet. It will reuse the reviewed G.1b and G.4 code: environment, data pins,
  cgroup, the isolation gate, server and campaign. Its spec, audit runner and switch need their own reviewed unit
  (§9).
- Written by the Mac-desk agent (Claude), AI-assisted. Revision 2, after round 1 of the independent review.
- Values marked *(proposed)* are recommendations, not decisions. Six author decisions are open (§2).

## 1. Authority (published `main` `94db94bb`)

| Row | What it fixes here |
|---|---|
| R1-T1-HOST-H200 | NEMO2 H200 for G.1b, G.4 and G.5. One GPU model per table; the noise floor and the labels of the table use H200. If the container isolation check fails, the whole T1 table moves to Ada. |
| R1-TRACKG-G3-EARLY | T1 nodes: `mlab_cifar10`, `mlab_imdb`, `mlab_ogbn_arxiv`, `mlgym_cifar10`, `mlgym_fmnist`, `mlgym_breakout_minatar`. `autoresearch_fixedtokens` and `mlgym_houseprice` "join as soon as their U2 passes". |
| R1-BX-D1, R1-BX-D5 | T1 nodes are label nodes; the nodes' fixed step budgets; one GPU model per table. |
| D1 | The campaign budget is compute (worker runs) plus an LLM-call cap (see G5-W). |
| R1-BX-D3, R1-BX-PROPOSED-CONFIRM (D3; Track G E4) | Audit seeds K = 6 (labels 7001–7003, evaluation 7006–7008) for T1 **only after** the sweep-1 subsampling check passes and a PLAN row records it; until then **K = 10**. If the check fails, K stays 10 and the coordinating agent STOPs for the author. E4 also says "both memory modes; about 12 campaigns per T1 node" (see G5-MEM). |
| R1-BX-PROPOSED-CONFIRM (E5) | Divergence = a non-finite loss, or no metric at the fixed budget. A divergent proposal enters no belief bin, is counted separately, and has action target u = −g. If only some seeds diverge, μ comes from the rest and the label is marked partial; more than half diverging makes the proposal divergent. A heavy-tailed node uses a Student-t, declared before labels are built. |
| R1-BX-D8-V3-A (3) | Split per tier P3 = 1/3 : 1/6 : 1/2 (train : validation : test), written into the analysis preregistration. |
| R1-BX-D8-V3-B (author's addition) | **T1 = 12 instances per node**; per-tier test floor T1 ≥ 3 test instances per node; a node below the floor is excluded from the IQM, kept in the PoI and reported. |
| R1-BX-D8-CONFIRM (17 Nov) | Gate `r1/c3/gate.py` @ `6aa9985c`, sha256 `ffb70d7a…`; T0 and T1 pooled with tier as a stratum; partial T1 at B.7 read on T0 plus the labelled T1 nodes, disclosed; leave-one-suite-out needs at least one labelled T1 node per suite. "Existing preregistration and analysis gates remain in force. Sweep-2 label tables may be analysed from this row on." It is committed, so the readers' `R1-BX-D8-CONFIRM` lock no longer gates anything; the T1 seal therefore needs its own release row (§6). |
| R1-MAIN-PROPOSER, R1-EXAM-X7, R1-SWEEP2-SETTINGS (1), D15, D26 | Proposer `gemma4_31b`, thinking off, the exam server flags, context 32,768, `cache_prompt` false; temperature 0.2; every manager call carries a seed derived from (instance, trial index, repetition), recorded in its `llm_call` event. |
| R1-EXAM-B1-TRUNCATION-INVALID | Every proposer call carries a completion cap; a truncated reply is an invalid proposal. |
| R1-BX-PROPOSED-CONFIRM (D4) | `manager_proposal/v2-diff`. A pick that fails diff liveness on a T1 node is a STOP; the author decides between a single-parameter fallback and moving the node to T2. |
| R1-TRACKG-G5-DIVERGENCE (4 Nov) | Asked "whether a T1 node should STOP when its audited label proposals' divergence fraction exceeds 20 %, or instead be judged case by case", the author replied "设 20% STOP" (set a 20 % STOP). The recorder's *(proposed)* consequence: a move to T2 needs a separate author row. The 20 % "originated as an agent proposal, not a measured threshold". |
| R1-TRACKG-PORT-DECISIONS (3), (4) | (3) The port-written imdb baseline is frozen and independently reviewed before any label run, and the census funnel and appendix say "baseline written by us". (4) Timeout = 3 × the census baseline run time; a timeout is the proposal's failure, not an infrastructure rerun. |
| R1-HARNESS-ISOLATION | Every T1 label run is effectively isolated: `effective: true`, `waivers {}`, `exceptions []`. Anything else is refused. |
| R1-B2-DECOUPLE, 28 Oct clarification | Labels use the label seeds; the evaluation seeds are never used for C3 or Track P training, tuning or selection. |
| R1-QTORCH-AMEND, R1-SWEEP2-IMAGE | Image v2 is approved for Track P; "image v2 只用于 Track P" (v2 is for Track P only), and sweep 2 uses v1. **No row yet authorizes v2 for the T1 table** (prerequisite P9). |

## 2. Author decisions (each with options and a recommendation)

### G5-W: what W = 20 counts (recommendation: A)

The 20 Nov task says "W = 20, ~150 audited proposals/node". The G.4 pilot and the v2-diff campaign engine count W
in manager calls. D1, sweeps 1 and 2 (`--runs 20`) and R1-W2-3-STOP count W in worker runs.

- **A (recommended): 20 manager calls per campaign.** About 240 × executed share × 0.9 audited proposals per node
  (130 at share 0.6, 173 at 0.8), which matches the task's "~150". The engine supports it today.
  - Cost: the T1 campaign budget differs from the T0 sweeps' run budget; disclosed. The per-proposal labels and the
    gate's per-proposal utility (scaled to a 20-run campaign, R1-BX-D8) do not depend on it.
  - R1-W2-3-STOP (every Track P source ledger uses exactly 20 worker runs) concerns the sweep data rebuild; a T1
    ledger would fail that check. Any Track P use of T1 ledgers needs its own author row.
- **B: 20 worker runs plus an LLM-call cap (proposed 80 per campaign).** Matches D1 and the sweeps; about 216
  audited proposals per node; about 1.6 × the cost (§8). Needs a worker-run budget in the v2-diff engine (code unit,
  §9).

### G5-MEM: memory mode (recommendation: A)

E4 says "both memory modes; about 12 campaigns per T1 node"; V3-B says 12 instances per node.

- **A (recommended): `append_only_summary` only, 12 instances.** 12 campaigns per node, as E4 counts them; 6 test
  instances under P3, above the floor of 3. The memory contrast stays on T0, where both modes run. Disclosed.
- **B: both modes, 12 instances each** (twin campaigns sharing instance seeds and labels by key, R1-MAIN-PROPOSER
  (e)). 24 campaigns per node, about 2 × the campaign cost; duplicates across modes need no second audit.
- **C: both modes, 6 instances each.** 12 campaigns per node, but only 6 instances, so 3 test instances: exactly at
  the floor, and it contradicts V3-B's 12 instances.

### G5-AUDIT: which proposals are audited (recommendation: A)

- **A (recommended): as C3_DESIGN §4 and the sweep-1 authorization:** every non-inert, non-duplicate evaluated
  proposal, **including** proposals that diverged or timed out in the campaign, and its parent incumbent, at the K
  audit seeds with joint seeds. No-ops are labelled by rule; duplicates (same node, incumbent, candidate) get no
  label and no audit. E5 then decides divergence over the audit seeds for every audited proposal.
- **B: every proposal with an `ok` campaign outcome.** Cheaper by the in-campaign divergent share, but in-campaign
  divergent proposals never get E5's seed-level test, and inert or duplicate `ok` proposals would need special
  handling. Not recommended.

### G5-DIV: the divergence STOP (recommendation: A)

The 20 Nov task adds "divergence > 2 × census".

- **Literal census reading.** Each census node has one deliberately divergent record (the broken diff, `s002`) among
  8 executed records: 12.5 %, so 2 × census = 25 %. It is looser than 20 % and never binds.
- **A (recommended): the author's 20 % rule, on the denominator the author was asked about.** The task's
  "2 × census" STOP is kept in its literal reading (25 %, on the same denominator); it never binds below 20 %, and
  the note says so.
  - Denominator: the node's **audited** label proposals (G5-AUDIT).
  - Numerator: proposals that are divergent under E5 (more than half of their audit seeds divergent).
  - Evaluated after each audit chunk, from at least 40 audited proposals of the node; the STOP then halts that
    node's remaining audits and campaigns.
  - Early warning (not a STOP): the in-campaign single-seed divergent share of ran proposals after each wave (§3),
    reported to the author when above 20 %.
- **B: min(20 %, max(2 × the upper 95 % Clopper–Pearson bound of the G.4 pilot's rate, 10 %)) on the same
  denominator**, for the three pilot nodes; the others use 20 %. This makes "2 × census" refer to the measured LLM
  loop, but the pilot measures single-seed divergence of ran proposals, a different quantity, on about 36 proposals.
- **C: 2 × the G.1b divergent-row rate of the node, capped at 20 %.** Exists for all six nodes on H200, but G.1b
  measures declared edits, not LLM proposals.

### G5-CAP: the GPU-hour cap (recommendation: B)

The projection (§8) under G5-W A is 118–145 GPU-h at K = 6 and 169–212 GPU-h at K = 10 (executed share 0.6–0.8).

- **A: 150 GPU-h, with K = 6 only;** K = 10 would be an author STOP.
- **B (recommended): 220 GPU-h,** which covers K = 10 at share ≤ 0.8 with the declared overheads. K is not decided
  yet (the K check), and a cap that only fits K = 6 would force a second authorization.
- **C: 150 GPU-h with audits limited to a pre-declared random subset of the auditable proposals** (seeded, fixed
  before any campaign runs). Changes label coverage; not recommended.

Under every option the cap bounds the projection, the requested slot-hours and the consumed GPU-hours (a running
meter from the job records).

### G5-SPLIT: the instance split, fixed now *(proposed)*

Per node, the 12 instances are ordered by `sha256("c3_t1_split/v1:" + <node> + ":" + <instance seed>)`. The first 6
are test, the next 2 validation, the remaining 4 train (P3 = 1/2 : 1/6 : 1/3 of 12). The signed note records the
resulting assignment and its sha256; the per-instance diagnostics are read only after the split exists.

## 3. What the label table is

For each T1 node:
- 12 root campaign instances of `run_v2_diff_campaign`, memory mode per G5-MEM, W per G5-W, with the record gate
  (`noise_floor.check_effective`) and the timeout basis of the table's noise floor (§4 item 8).
- The campaigns run in two waves: instances 1–4, then 5–12. Each wave's diagnostics are sealed and read (§6)
  before the next wave is submitted, so the STOPs act before most of the spend.
- Audits per G5-AUDIT: paired fresh-seed re-runs of the proposal's code state and its parent incumbent at the K audit
  seeds with joint seeds (training seed = split seed = s, `"vary"` split), so each seed gives a paired d_s, as in
  C3_DESIGN §4 and the sweep-1 B.2 audit. Audits run in chunks, each under the walltime limit.
- Labels and keep decisions use the validation metric. The sealed task test metric is never read for labels or
  selection.

The soft-label width comes from the G.1b noise floor on the same H200 environment: σ̂_node is the G.1b `joint`
σ (seeds 3001–3030, `"vary"` split), and the width is s = σ̂_node/√K_label (R1-BX-D3). Before any label is
assembled, each node is declared Gaussian or Student-t from the G.1b summary (E5; prerequisite P10).

## 4. STOPs

Every G.1b STOP (plan §7) and every G.4 STOP (plan §7) applies to the G.5 jobs: spec and authority, image and
VERSIONS, root uid, GPU count and model (including a device-name variant), code pins, staged files, environment
freeze, data manifest, cgroup, GGUF sha256 and size, `llama-server` build and offload, the deadline, and the launch
binding. In addition:

1. **Divergence** (G5-DIV). The rule the author chooses, evaluated as stated there. The STOP halts the node; a move
   to T2 needs a separate author row.
2. **Isolation.** Any run record that is not `effective: true` with empty waivers and exceptions STOPs that job
   (`stop_unisolated`), with the evidence kept. No waiver for label runs.
3. **Diff liveness** (D4). A node whose ran-of-valid share is below 0.25 (absolute; the same for every node) after
   wave 1 STOPs. The author decides between a single-parameter fallback and T2.
4. **Proposer output.** A truncated reply is invalid (completion cap 4,096 tokens). A node whose invalid share
   (parse failures, truncations, refusals) exceeds 0.2 of its manager calls in a wave STOPs (as sweep 2's
   `max_parse_failure_rate`). A prompt longer than 32,768 − 4,096 tokens STOPs the campaign.
5. **Noise floor.** A node that does not qualify under D21 at G.1b, or fails fixed-seed determinism, is not run in
   G.5: a STOP for that node; the author decides on T2 (R1-BX-D12 discloses it). No node is dropped silently.
6. **Integrity, transport, baseline.** A `stop_integrity`, `stop_transport` or `baseline_failed` ledger line STOPs
   that job. A failed job is resubmitted only as a new attempt after diagnosis, never resumed.
7. **Infrastructure.** Final infrastructure failures (after 2 reruns) above 5 % of a node's proposals STOP the node
   *(proposed)*.
8. **Timeout.** The timeout basis is the one the author fixes for the noise floor (G1B-TIMEOUT, G.1b plan §2a), so
   the noise floor and the labels share it. A timeout is the proposal's divergent failure (E5 over the audit seeds).
   A **baseline** timeout STOPs the campaign.
9. **Budget.** The projection, the requested slot-hours or the consumed GPU-hours above the cap (G5-CAP); a job above
   86,400 s walltime; a projected audited count outside 100–200 per node after wave 1 (the author then decides:
   accept, change W, or cap the audits).
10. **Seeds.** Any use of the evaluation seeds outside the audit's evaluation block, or of label seeds 7004–7005 when
    K = 6, is a STOP. The G.5 validator refuses every other reserved block (below).
11. **Reading.** Any read of sealed content before its release step (§6) is a STOP and is reported.

**After a node STOP**, the node's partial outputs stay sealed and kept. Whether its labelled instances enter the
table is decided by an author row; they count toward B.7 only if that row says so and the node has at least 3 labelled
test instances.

## 5. Key values (the final note carries these lines; the G.5 switch matches every one)

```
approved: false
label: EVIDENCE
run_id: c3_t1_labels_<YYYYMMDD>
image: ghcr.io/dowlingwong/r1-htc-gpu@sha256:b1144ecec7ffe07642ff108fb9624aa34775cb873ed17f835ea3e3c87bc024fd
image_authority: <the PLAN row of P9>
versions_sha256: <as in the G.1b note>
llama_server_sha256: <as in the G.4 note>
gguf_sha256: 2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75
harness_commit: c11ef75f461a7e429abb85c40c34167de034e4d7 (branch mac-trackg-t1-20261120; the G.1b and G.4 pin, or its pushed successor)
gpu_model: NVIDIA H200 (campaigns, server and audits)
nodes: mlab_cifar10,mlab_imdb,mlab_ogbn_arxiv,mlgym_cifar10,mlgym_fmnist,mlgym_breakout_minatar
instances_per_node: 12
instance_seeds: 5101-5112 (instance k: training = split = manager seed 5100 + k)
instance_split: <G5-SPLIT assignment and its sha256>
memory_mode: <G5-MEM>
campaign_W: 20 <manager calls | worker runs with an LLM-call cap of 80> (G5-W)
proposer: gemma4_31b (thinking off; exam flags; context 32768; cache_prompt false; temperature 0.2; D26 per-call seed)
completion_cap_tokens: 4096
proposal_schema: manager_proposal/v2-diff
timeout_basis: <G1B-TIMEOUT: 3 x the census baseline time | 3 x the slowest census record>
audit_K: <10, or 6 only after the K-check PASS row; uniform within the table>
audit_seeds_label: <7001-7005 for K = 10; 7001-7003 for K = 6>
audit_seeds_evaluation: <7006-7010 for K = 10; 7006-7008 for K = 6>
audit_scope: <G5-AUDIT>
divergence_stop: <G5-DIV>
noise_floor: <G.1b run id and summary sha256>
tails: <per node Gaussian or Student-t (P10)>
job_layout: campaigns one job per node x wave (2 waves); audits in chunks under 86,400 s
gpu_hours: <projection per §8>
cap_gpu_hours: <G5-CAP>
release_row: R1-T1-LABELS-UNSEAL (§6)
```

*(proposed)* The instance seed block 5101–5112 is disjoint from G.1b (1001–3030), G.4 (4001–4099), the census seeds
(8001–8010), the audit seeds (7001–7010) and the exam seeds (9001+, including 9101+ and 9201+). It avoids
5001–5006, the E1b audit seeds on the CPU nodes.

## 6. Sealing and staged release

**Writing.**
- The campaign ledgers, the audit records and every per-proposal value go only into the job's sealed `out.tar`.
- Each job also writes one `diagnostics.json` with a fixed schema: counts and shares only (proposals, valid,
  invalid, truncated, ran, inert, duplicate, divergent in campaign, timed out, kept; audited, E5-divergent; prompt
  and completion token percentiles; GPU-seconds; STOP state). It holds no metric value, delta, label or keep
  outcome per proposal.
- The sealed directory on `/ceph/srv/dwong/paperb/t1_labels/<run_id>/` is created with mode 0700 for the operator
  account (cluster test C6 checks the effective read restriction). The seal step verifies the sums and never
  overwrites.

**Before release**, operators, agents, reviewers and the author open only `diagnostics.json`, the job records and
the seal receipts. These are enough for every STOP in §4.

**Release** needs a separate author row **R1-T1-LABELS-UNSEAL**, which cites the sha256 of the analysis
preregistration (P3 split, gate v3, floors) and of the instance-split file. Every T1 label reader (the table
assembly, the C3 training pipeline, the gate run, any Track P loader) refuses to run without that row; this is a P5
code requirement with a test. Release is staged:
1. **Train and validation partitions** to the C3 training pipeline: arms are trained on train and selected on
   validation. Track P reads them only if the author says so in a row.
2. **Test partition** only to the gate run, after the arms are fixed.
3. The sealed task test metric is never released.

Partial T1 at B.7 follows R1-BX-D8-CONFIRM: the gate is read on T0 plus the labelled T1 nodes, with the count
disclosed. **Leave-one-suite-out risk:** the six current T1 nodes are in two suites (MLAgentBench, MLGym). Under
R1-BX-D8-CONFIRM, leave-one-suite-out STOPs at B.7 unless `autoresearch_fixedtokens` (or another node of the third
suite) has labelled T1 instances by then; the aggregate gate does not STOP on it.

**Breakout.** `mlgym_breakout_minatar`'s evaluation keys are public constants (port report §6.2). The labels use the
validation return only, inside the isolated worker, and the sealed test return is never read; disclosed in the
appendix.

## 7. Prerequisites (each PASS in the final note)

- **P1** — R1-T1-HOST-H200: harness isolation works inside the v2 container on H200 (the cluster's ENGINEERING
  record).
- **P2** — G.1b complete on H200: D21 verdicts per node, the summary assembled and sealed.
- **P3** — G.4 pilot run and read: liveness, invalid and divergence shares per node; the R1-BX-D14 dates recomputed
  and reported; the executed share that §8 uses.
- **P4** — K: the K-check PASS row (K = 6), or K = 10 recorded; if the check fails, the coordinating agent STOPs for
  the author (R1-BX-D3). K is uniform within the T1 table.
- **P5** — G.5 job code (spec, campaigns in waves, audit runner, diagnostics, release lock, switch) independently
  reviewed at the launch commit; its harness pin equals the G.1b pin.
- **P6** — author decisions recorded: G5-W, G5-MEM, G5-AUDIT, G5-DIV, G5-CAP, G5-SPLIT, and the G.1b decisions
  G1B-EDITS and G1B-TIMEOUT.
- **P7** — the §8 projection, recomputed from the pilot medians, is within the cap.
- **P8** — the imdb baseline frozen and independently reviewed (R1-TRACKG-PORT-DECISIONS (3)); the review cited.
- **P9** — an author row authorizing image v2 for the T1 table (G.1b, G.4 and G.5 use it; R1-SWEEP2-IMAGE reserves
  v2 for Track P).
- **P10** — per node, the Gaussian or Student-t declaration from the G.1b summary, recorded before any label is
  assembled (E5).
- **P11** — cluster tests C1–C7 below PASS, in particular C3 (run time on H200 next to a resident `llama-server`,
  against the timeout basis).

## 8. Projection (pre-pilot; recomputed from the pilot before signature)

Per node, with r the census baseline run time, share s the executed share, and the declared overheads:
- campaigns: 12 baselines × r + manager calls × 60 s + ran proposals × r × 1.25;
- audits: (audited + 12 baselines + keeps) × K × r × 1.25, with audited = 0.9 × ran (inert and duplicates excluded)
  and keeps = 0.2 × ran (each keep creates a new parent incumbent);
- startup: 1,500 s per job (2 campaign waves + the audit chunks, each chunk under 86,400 s with the × 1.5 walltime
  rule).

The factor 1.25 covers slower edited runs and timeouts; H200 speed next to the server is unmeasured (C3). The
formula is `sweep2/g4/g5_projection.py`.

| W (G5-W) | Share | K = 6 GPU-h | K = 10 GPU-h | Audited per node |
|---|---|---|---|---|
| A: 20 manager calls | 0.6 | 117.9 | 169.1 | 130 |
| A: 20 manager calls | 0.8 | 144.8 | 211.8 | 173 |
| B: 20 worker runs, cap 80 calls | 0.6 | 188.6 | 270.5 | 216 |
| B: 20 worker runs, cap 80 calls | 0.8 | 178.6 | 260.5 | 216 |

`g4_lib.recompute_dates` models a different shape (⌈150/share⌉ proposals, 150 audits, no baselines or parents) and
gives 86.1 / 121.0 GPU-h; it sizes the dates, not this table. P7 uses the formula above with the pilot's medians.

Adding `autoresearch_fixedtokens` or `mlgym_houseprice` later needs its own H200 noise floor, its own projection and,
*(proposed)*, an amendment of this note.

## 9. What remains to build (one reviewed unit, after G.4)

- The G.5 spec and job: 12 instances per node in two waves, built on `g4_lib` / `pilot_g4`, with the instance seed
  block, the memory mode and, under G5-W B, a worker-run budget with an LLM-call cap in the v2-diff engine.
- The audit runner: re-materialise each audited proposal's code state and its parent from the ledger; paired
  fresh-seed re-runs through `noise_floor`-style chunks with the isolation gate; E5 per proposal.
- `diagnostics.json` per job and the STOP counters on it, without reading labels.
- The seal step with the restricted target, the assembly, and the R1-T1-LABELS-UNSEAL lock in every reader, with
  tests.
- The switch with the key values of §5 and the S2-C5 launch binding.

## 10. Needs a cluster test

- **C1.** Everything in G.1b plan §6 (items 1–12) and G.4 plan §6 (items 1–3).
- **C2.** The audit runner on H200: re-materialisation, isolated joint-seed runs, fixed-seed determinism of audit
  pairs.
- **C3.** Run time on H200 with a resident `llama-server`, against the timeout basis (false divergence).
- **C4.** Diagnostics out per wave and per audit chunk, so the STOPs act early.
- **C5.** The audit-chunk split that keeps the K = 10 imdb and Breakout audits under 86,400 s.
- **C6.** Read restriction on the `/ceph` seal target.
- **C7.** GGUF transfer per job (19.6 GB) or a cache, and the number of concurrent H200 slots actually available.
