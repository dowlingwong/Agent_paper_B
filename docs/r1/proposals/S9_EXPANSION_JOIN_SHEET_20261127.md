# Decision sheet S9: how an expansion node joins G.5 and the T1 gate (local/20261126-04)

AI-assisted (Claude, Mac-desk worker), 27 Nov 2026, over published `main` `47df6f55`. Tier D: a sheet for the author;
it decides nothing.

**Authority.**
- R1-G5-SIGNATURE (1), S9: "not decided here (a separate sheet; the addendum mechanism is not built)".
- R1-G5-EXPANSION-JOIN, read with R1-STEP-ORDER (2)(a): every expansion candidate whose G.1b completes with determinism PASS joins G.5 through an addendum note. The 2 Dec cutoff is withdrawn.
- R1-T1-NODE-EXPANSION.
- R1-SWEEP2-PREREG: PRE-SPLIT A, PRE-T1 A; signed and `frozen: true` since 21 Nov.
- R1-1GC-FALLBACK.

**The candidates** (`sweep2/t1_tasl/g1b_tasl_x_spec.json`): `mlgym_titanic`, `mlgym_metamaze`, `gc7rc_etth1` and `gc7rc_forestcover`. The expansion note is published, and the launch is with compute.

## What is fixed today

- **The split file `r1/c3/splits/c3_p3_split_v1.json`** (sha256 `b5967dd7…`) is cited by:
  - the frozen preregistration;
  - the signed G.5 note's `instance_split` line;
  - `r1/c3/p3_split.py`, which pins `T1_NODES` to the eight nodes.

  The T1 rule is label-free and per node: over the instance seeds 5101–5112, order by `sha256("c3_t1_split/v1:" + node + ":" + seed)`, then 6 test, 2 dev, 4 train. Applied to a new node name, it gives that node's split without touching any other node's.
- **`r1/c3/train/sft_data.py:834-859`** and **`r1/c3/arms_freeze.py:673`** refuse a T1 node outside `p3_split.T1_NODES`. `arms_freeze` also refuses one whose suite is outside `gate.SUITES`.
- **The gate** (`r1/c3/gate.py:63, 156, 365`) requires every T1 node to carry a suite from `SUITES = (autoresearch, MLAgentBench, MLGym)`; otherwise it STOPs.
  - R1-1GC-FALLBACK: "1GC's public datasets may be used as extra tasks but do not count as a suite".
  - So `gc7rc_etth1` and `gc7rc_forestcover` have no admissible suite.
- **PRE-T1 A:** the T1 node set of the one primary read is exactly the T1 nodes whose train/dev labels were released and used to freeze the arms. After R1-STEP-ORDER (2)(b) no node is left out for being late.

## Decision 1: the instance split of a ninth to twelfth node

| Option | What | Cost | Effect |
|---|---|---|---|
| **A** | One generator, one file: `c3_p3_split_v2.json` = v1 plus the joining nodes, by the same T1 rule and salt. The eight nodes' entries and the T0 part are byte-identical to v1, and a test checks this. `p3_split.T1_NODES` grows by the joining nodes. | An author row amending PRE-SPLIT to cite v2's sha256 (the preregistration is frozen). The G.5 addendum cites v2 for the new nodes; the signed note keeps v1 for the eight. A code unit for `p3_split` and its users (tier E). | Every arm, Track P included, uses one assignment, as PRE-SPLIT A intends. No instance of an existing node moves. |
| B | One addendum file per joining node (`c3_p3_split_v1_addendum_<node>.json`), same rule; consumers read v1 plus the addenda. | The same row, plus several files to cite and check; every consumer changes to merge files. | Equivalent assignments, more moving parts. |
| C | No split for the new nodes: they are labelled by G.5 but stay out of the arms and the gate (appendix T2). | An author row departing from R1-STEP-ORDER (2)(a)–(b), which put them in the T1 set. | The primary read keeps eight T1 nodes, and the expansion's labels serve only descriptive tables. |

**Recommendation: A.** It is the smallest change that keeps "one split file for both tiers" true. The split depends on node names and seeds only, so v2 can be generated and reviewed now, before any expansion label exists.

## Decision 2: the gate's node set, and the two 1GC nodes

| Option | What | Effect on the primary read |
|---|---|---|
| **a** | The MLGym candidates (`mlgym_titanic`, `mlgym_metamaze`) enter the arms and the primary gate as T1 nodes of suite MLGym, under PRE-T1 A. The 1GC candidates (`gc7rc_etth1`, `gc7rc_forestcover`) are labelled by G.5 as R1-STEP-ORDER (2)(a) says, but are supplied neither to the arms' training nor to the gate. They are reported per node in the secondary table as "extra tasks", which is what R1-1GC-FALLBACK allows. | T1 grows from 8 to at most 10 nodes, MLGym from 4 to at most 6. The gate code is unchanged (all suites stay valid). |
| b | All four enter the gate, with the 1GC nodes given a fourth suite `1GC`. | Needs a gate code change (`SUITES`), a PRE-WDBC/gate-row amendment and leave-one-suite-out over four suites. It contradicts R1-1GC-FALLBACK, which says they do not count as a suite. |
| c | All four enter the arms' training, but only the MLGym ones are read in the gate. | Training uses labels the gate does not read. That changes PRE-T1 A's definition and needs a preregistration amendment. |

**Recommendation: a.** It follows R1-1GC-FALLBACK's text, needs no gate change, and keeps PRE-T1 A's "nodes used to freeze the arms = nodes read" identity.

## What it does to the primary read

- Under A and a, the gate's T1 stratum holds the eight nodes plus every MLGym candidate that completes G.1b with determinism PASS and is labelled. That is a node set decided by completion (R1-STEP-ORDER (2)(a)), not by results.
- The gate statistic, the thresholds and the T0 set are unchanged.
- With more T1 nodes, the T1 share of the pooled IQM grows. MLGym's weight in leave-one-suite-out grows too: the MLGym fold holds out 6 nodes rather than 4.
- These follow from the node count and are stated before any label is released.
- No test partition is touched by any of this.

## Then: the G.5 addendum mechanism (`local/20261126-12`, after the author's row)

An addendum note `docs/r1/authorizations/c3_t1_labels_<YYYYMMDD>_addendum_<N>.md` per joining node. It cites:
- the signed note;
- the node's G.1b note and result (determinism PASS);
- its REL-T1-G1B copy and P10 declaration;
- its spec entry (the same code, K and rules);
- the split file v2 (decision 1);
- its suite or "extra task" status (decision 2);
- a dates and GPU-hours recompute reported against the 425 threshold (R1-NO-TIMEOUT (3)).

The switch reads the addendum as it reads the note. Under R1-STEP-ORDER there is no join cutoff.

## Draft row

`| R1-G5-S9 (date) | S9 of the G.5 note: (1) split A — c3_p3_split_v2.json, generated by the same rule and salt, the eight T1 nodes and T0 byte-identical to v1, the joining nodes added; PRE-SPLIT is amended to cite v2; (2) gate a — MLGym expansion nodes enter the arms and the primary gate as T1 nodes of suite MLGym; the 1GC nodes (gc7rc_etth1, gc7rc_forestcover) are labelled by G.5 but are not supplied to the arms or the gate, and are reported per node as extra tasks (R1-1GC-FALLBACK); (3) each joining node enters G.5 by an addendum note (local/20261126-12) with the same code, K and rules. |`
