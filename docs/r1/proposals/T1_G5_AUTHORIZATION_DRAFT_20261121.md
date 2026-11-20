# G.5 — T1 label runs on NEMO2 H200: authorization draft (approved: false)

**Status: DRAFT for the author's signature. `approved: false`. Not runnable.** This document authorizes nothing
until the author signs a final version and the coordinating chat publishes it to `main` as
`docs/r1/authorizations/c3_t1_labels_<YYYYMMDD>.md`, with every prerequisite in §6 recorded as PASS. The G.5 job
code does not exist yet. It will reuse the reviewed G.1b and G.4 code: environment, data pin, cgroup, gate, server,
campaign. Its spec and switch need their own reviewed unit after the pilot (§7). Written by the Mac-desk agent
(Claude), AI-assisted. Values marked *(proposed)* are recommendations, not decisions.

## 1. Authority (published `main` `94db94bb`)

| Row | What it fixes |
|---|---|
| R1-T1-HOST-H200 | NEMO2 H200 for the G.5 labels. One GPU model per table: the noise floor (G.1b) and the labels use H200. If the container isolation check fails, the whole T1 table moves to Ada. |
| R1-TRACKG-G3-EARLY | T1 nodes: `mlab_cifar10`, `mlab_imdb`, `mlab_ogbn_arxiv`, `mlgym_cifar10`, `mlgym_fmnist`, `mlgym_breakout_minatar`. `autoresearch_fixedtokens` and `mlgym_houseprice` join after their U2 passes, by an amendment of this note. |
| R1-BX-D1, R1-BX-D5 | T1 nodes are label nodes. Label runs use the nodes' fixed step budgets, and there is one GPU model per table. |
| R1-BX-D3, R1-BX-PROPOSED-CONFIRM (D3) | Audit seeds K = 6 (3 label + 3 evaluation) for T1 **only if** the sweep-1 subsampling check passes and a PLAN row records it. Until then **K = 10** applies. |
| R1-BX-D8-V3-B (author's addition) | **T1 = 12 instances per node.** Per-tier test floor: T1 ≥ 3 test instances per node. |
| R1-MAIN-PROPOSER, R1-EXAM-X7, R1-SWEEP2-SETTINGS (1) | Proposer `gemma4_31b` with thinking off and the exam server flags; context 32,768; `cache_prompt` false. |
| R1-BX-PROPOSED-CONFIRM (D4) | `manager_proposal/v2-diff`. A pick that fails diff liveness on a T1 node is a STOP; the author decides between a single-parameter fallback and moving the node to T2. |
| R1-TRACKG-G5-DIVERGENCE (4 Nov) | **STOP a node when more than 20 % of its T1 label proposals are divergent.** A move to T2 needs a separate author row. |
| R1-TRACKG-PORT-DECISIONS (4) | Timeout = 3 × the census run time; a timeout is the proposal's divergent failure, not an infrastructure rerun. |
| R1-HARNESS-ISOLATION | Every T1 label run must be effectively isolated: `effective: true`, `waivers {}`, `exceptions []`. Anything else is refused. |
| R1-BX-D8, R1-BX-D8-CONFIRM, R1-BX-D8-V3-A/B | The gate (`r1/c3/gate.py` @ `6aa9985c`, sha256 `ffb70d7a…`); T0 and T1 pooled with tier as a stratum; partial T1 at B.7 is disclosed; leave-one-suite-out needs at least one labelled T1 node per suite. The analysis lock stands. |
| R1-B2-DECOUPLE, 28 Oct clarification | Labels use seeds 7001–7005. The evaluation seeds 7006–7010 are never used for C3 or Track P training, tuning or selection. |

## 2. What the label table is

For each T1 node:
- 12 root campaign instances of `run_v2_diff_campaign` (W = 20 manager calls each, so 240 proposals per node);
- the record gate (`noise_floor.check_effective`);
- fresh-seed audits of every proposal that ran with an `ok` outcome, which is about 150 audited proposals per node
  at the pilot's executed share;
- the audit re-runs the proposal's code state and its parent incumbent at the K audit seeds with joint seeds
  (training seed = split seed = s, `"vary"` split), so each seed gives a paired d_s, as in C3_DESIGN §4 and sweep 1
  (B.2).

The node's σ̂ for the soft-label width comes from the G.1b noise floor on the same H200 environment. Its noise
floor is σ_joint; the soft width is s = σ̂_node/√K_label (R1-BX-D3).

## 3. Key values (the final note carries these lines; the job's switch will match them)

```
approved: false
label: EVIDENCE
run_id: c3_t1_labels_<YYYYMMDD>
image: ghcr.io/dowlingwong/r1-htc-gpu@sha256:b1144ecec7ffe07642ff108fb9624aa34775cb873ed17f835ea3e3c87bc024fd
versions_sha256: <as in the G.1b note>
llama_server_sha256: <as in the G.4 note>
harness_commit: <the T1 harness commit of G.1b (one pin for the noise floor and the labels)>
gpu_model: NVIDIA H200
nodes: mlab_cifar10,mlab_imdb,mlab_ogbn_arxiv,mlgym_cifar10,mlgym_fmnist,mlgym_breakout_minatar
instances_per_node: 12
campaign_length_W: 20
instance_seeds: 5001-5012 (instance k: training = split = manager seed 5000 + k)
proposer: gemma4_31b (thinking off; exam flags; cache_prompt false)
proposal_schema: manager_proposal/v2-diff
audit_K: <10, or 6 only after the K-check PASS row>
audit_seeds_label: <7001-7005 for K = 10; 7001-7003 for K = 6>
audit_seeds_evaluation: <7006-7010 for K = 10; 7006-7008 for K = 6>
audit_scope: every proposal with an ok outcome, and its parent incumbent, at every audit seed (joint seeds)
audited_proposals_target: about 150 per node (not a cap; every ok proposal is audited)
noise_floor: <G.1b run id and summary sha256>
gpu_hours: <projection from the G.4 recompute; cap below>
cap_gpu_hours: <proposed 150>
divergence_stop: 20 % of a node's label proposals (R1-TRACKG-G5-DIVERGENCE) — see §4 item 1
sealing: sealed until the R1-BX-D8-CONFIRM analysis (§5)
d8_lock: true
```

*(proposed)* The instance seed block 5001–5012 is disjoint from:
- G.1b: 1001–3030;
- G.4: 4001–4099;
- the audit seeds: 7001–7010;
- the exam seeds: 9001+.

## 4. STOPs

1. **Divergence.**
   - **Signed rule:** STOP a node when more than 20 % of its T1 label proposals are divergent
     (R1-TRACKG-G5-DIVERGENCE).
   - **Additional rule from the 20 Nov task text:** "divergence > 2 × census".
   - **Author decision G5-DIV.** The census measured no LLM proposals: its only divergent run is the deliberately
     broken diff of the stub smoke. So "2 × census" has no measured reference yet. *Recommendation:* keep the signed
     20 % STOP, and add **a STOP at > 2 × the G.4 pilot's divergence rate of the same node, where that node was in
     the pilot**. The pilot is the census of the LLM loop on these nodes. Whichever bound is lower binds. Nodes
     without a pilot measurement use 20 % alone.
2. **Isolation.** Any run record that is not `effective: true` with empty waivers and exceptions STOPs that node's
   job (`stop_unisolated`), with the evidence kept. There is no waiver for label runs.
3. **Diff liveness** (D4). A node whose valid proposals do not run (ran-of-valid = 0, or below the pilot's
   *(proposed)* 0.25) STOPs. The author decides between a single-parameter fallback and T2.
4. **Noise floor.** A node that does not qualify under D21 at G.1b, or failed fixed-seed determinism, is not run in
   G.5. That is a STOP for the node, and the author decides on T2 (R1-BX-D12 discloses it). No node is dropped
   silently.
5. **Integrity, transport, baseline.** A `stop_integrity`, `stop_transport` or `baseline_failed` ledger line STOPs
   that campaign's job. It is resubmitted only as a new attempt after diagnosis, never resumed.
6. **Infrastructure.** Final infrastructure failures (after 2 reruns) above 5 % of a node's proposals STOP the node
   *(proposed)*.
7. **Budget.** A projection above `cap_gpu_hours`, or a job above 86,400 s walltime, is an author STOP.
8. **Timeout.** A timeout is the proposal's divergent failure and counts toward item 1. A **baseline** timeout STOPs
   the campaign (the host or node changed).
9. **Seeds.** Any use of 7006–7010, or 7004–7005 when K = 6, outside the audit evaluation role is a STOP.
10. **Reading.** No label value is read before §5's release (§5).

## 5. Sealing until analysis (R1-BX-D8-CONFIRM)

- Every job's outputs are transferred, SHA256-summed and sealed to `/ceph/srv/dwong/paperb/t1_labels/<run_id>/…` by
  the reviewed seal step. Nothing is overwritten or deleted.
- Before the analysis, operators and agents read **only** the coverage and STOP diagnostics: the decision counts per
  node, the divergence and liveness shares, the gate results, and the seal receipts. They do not read the audit
  values, the Δ estimates or the per-proposal labels.
- The label table is assembled and unsealed only by the R1-BX-D8-CONFIRM analysis run, with the pinned gate code
  (`r1/c3/gate.py` sha256 `ffb70d7a…`), after:
  - the sweep-2 analysis preregistration: split P3 with T1 ≥ 3 test instances per node, gate v3, floors;
  - the T1 instance split (train/validation/test over the 12 instances), fixed before unsealing.
- Partial T1 at B.7 follows R1-BX-D8-CONFIRM: the gate is read on T0 plus the labelled T1 nodes, with the count
  disclosed. Leave-one-suite-out STOPs without a labelled T1 node per suite.
- The test instances are not read for any selection or tuning (R1-TRACKG-ROLE: select on validation only).

## 6. Prerequisites (each must be PASS in the final note)

- P1 — R1-T1-HOST-H200: harness isolation works inside the v2 container on H200 (the cluster's ENGINEERING record).
- P2 — G.1b complete on H200, with D21 verdicts per node and the summary sealed (the noise floor of this table).
- P3 — G.4 pilot run and read: liveness and the shares per node; the R1-BX-D14 dates recomputed and reported.
- P4 — K: either the K-check PASS row (K = 6) or K = 10 recorded.
- P5 — G.5 job code (spec, job, audit runner, switch) independently reviewed at the launch commit; its harness pin
  equals the G.1b pin.
- P6 — author decisions G5-DIV (§4 item 1) and G1B-EDITS (the G.1b edit count) recorded.
- P7 — the projection from the G.4 recompute is within `cap_gpu_hours`.

## 7. Projection (pre-pilot; replaced by the G.4 recompute)

Per node, the estimate is:
- 12 baselines + 240 proposals × (60 s LLM + census run time × 0.6 executed share);
- plus audits: 144 executed proposals and 12 baselines × K × the census run time.

| Node | Census run s | K = 6 GPU-h | K = 10 GPU-h |
|---|---|---|---|
| mlab_cifar10 | 12.297 | 7.7 | 9.9 |
| mlab_imdb | 64.142 | 23.5 | 34.6 |
| mlab_ogbn_arxiv | 5.651 | 5.7 | 6.7 |
| mlgym_cifar10 | 31.731 | 13.6 | 19.1 |
| mlgym_fmnist | 34.376 | 14.4 | 20.4 |
| mlgym_breakout_minatar | 61.248 | 22.6 | 33.2 |
| **Total** | | **87.5** | **123.8** |

*(proposed)* `cap_gpu_hours` = 150. That covers K = 10 with about 20 % margin. Adding autoresearch and houseprice
later needs an amendment with its own projection.

## 8. What remains to build (after G.4, as one reviewed unit)

- The G.5 spec and job: 12 instances per node, one job per node × instance block, built on `g4_lib` / `pilot_g4`
  with the instance seed block.
- The audit runner: fresh-seed paired re-runs of the ok proposals and their parents, through `noise_floor`-style
  chunks with the gate.
- The divergence, liveness and infrastructure STOP counters while the jobs run (from the ledgers, without reading
  labels).
- The seal step, and an assembly that keeps the label values sealed.

The prompt's "approved: false, for the author to sign" applies to this note. The code unit is separate and needs its
own review before P5 can be PASS.
