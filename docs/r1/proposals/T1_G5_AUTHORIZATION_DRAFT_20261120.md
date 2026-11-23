# G.5 — T1 label runs on the TASL pair (RTX 4090): authorization draft (approved: false)

**Status: DRAFT for the author's signature. `approved: false`. Not runnable.**
- This document authorizes nothing until the author signs a final version and the coordinating chat publishes it
  to `main` as `docs/r1/authorizations/c3_t1_labels_<YYYYMMDD>.md`, with every prerequisite in §7 recorded as PASS
  (under G5-ARPEND A, §2.13, autoresearch's own prerequisites may be PENDING at signature and gate only its jobs).
- The G.5 job code does not exist yet. It will reuse the reviewed G.1b and G.4 code: environment, data pins,
  cgroup, the isolation gate, server and campaign. Its spec, audit runner and switch need their own reviewed unit
  (§9).
- Written by the Mac-desk agent (Claude), AI-assisted.
  - Revisions 1–5 (H200) passed rounds 1–5 of the independent review (`reviews/T1_G5_DRAFT_REVIEW_20261121.md`).
  - Revision 6 re-targeted the draft from NEMO2 H200 to the TASL pair under R1-T1-HOST-TASL (worker on TASL-2,
    proposer `llama-server` on TASL-7 over Tailscale, one GPU model: RTX 4090) and added G5-TASL-GPUH and G5-SLOT. It
    was reviewed with the T1 TASL code unit (`reviews/T1_TASL_REVIEW_20261121.md`).
  - Revision 7 (22 Nov) moved the authority to published `main` `9c2979a2`, after the signed G.4 note
    (`authorizations/g4_t1_tasl_20261122.md`). The changes:
    - The rows published since revision 6 are cited (§1): R1-T1-TASL-ENV, R1-G1B-EDITS, R1-G1B-TIMEOUT,
      R1-G1B-TASL-DECISIONS, R1-G1B-NOTE2-DECISIONS, R1-G4-DECISIONS and R1-SWEEP2-PREREG.
    - G5-SPLIT is now fixed by the frozen analysis preregistration, so it is no longer a decision (§2.7).
    - Two decisions are new: G5-AR, how `autoresearch_fixedtokens` enters G.5 (§2.11), and G5-PIN, the two G.1b
      harness pins (§2.12).
    - The projection and the dates are recomputed as of 22 Nov, with and without autoresearch (§2.8, §2.10, §2.11),
      still pre-pilot.
    - The key values known from R1-T1-TASL-ENV and the signed G.4 note are filled (§5).
    - The launch binding is the TASL binding, not S2-C5 (§9).
    - The prerequisites (§7) and cluster tests (§10) are updated.
    It was reviewed in one round (round 1 of `reviews/T1_G5_DRAFT_TASL_REVIEW_20261122.md`, published with this
    revision's merge: not accepted, M1–M3 and m1–m12; three text-level majors, no blocking finding).
  - **Revision 8 (22 Nov)** moves the authority to published `main` `3c3f822a` and applies R1-G5-DECISIONS and the
    revision-7 review:
    - **R1-G5-DECISIONS** (G5-AR A, G5-PIN B) is applied: eight nodes (§2.11, §5); K = 10 until a published K-check
      row (§1, §5, P4); the cap as projected, 425 GPU-h (§2.6); two G.5 harness commits with byte-identical G.5 code
      and the check that enforces it, `sweep2/t1_tasl/g5_pin_check.py` with tests (§2.12, STOP 13, §9); the dates the
      row accepted (B.7 about 15 Dec, §1, §2.11).
    - From the coordinator's queue (on the basis of review condition C1 and the signed G.4 note's P1, whose acceptance
      covers the pilot only; G.5's labels are EVIDENCE): host-check item 7 (CUDA IPC) as C12 on TASL-2 or an
      acceptance line in the note, with its text (P1, §5).
    - Review M1: PRE-T1 A is quoted verbatim; leave-one-suite-out is a descriptive PRE-SECONDARY analysis (§1, §2.11).
    - Review M2: gate v3.1 (R1-BX-D8-CONFIRM-V31), R1-SWEEP2-RELEASE-DECISIONS (REL-SCOPE, REL-T1-G1B), PRE-STAGE and
      PRE-DELTA, and the preregistration's sha256 are cited (§1, §5); the G.1b summaries reach G.5 through the
      REL-T1-G1B step (§3); the release rows are rewritten (§6).
    - Review M3: the freeze wait (a rule for a late autoresearch, then for every un-STOPped node), with STOP 14 (§2.11, §4).
    - Rows published since revision 7 are cited: R1-G5-DECISIONS, R1-T1-DATA-MANIFEST, R1-G1B-AR-ENV (§1); the TASL
      launch chain of R1-T1-DATA-MANIFEST and the AR host-check STOP are reflected in P2 and §3.
    - The minors m1–m12 are applied; the projection script uses the TASL date wrapper and marks the K = 6 rows (§8).
    - §11 lists exactly what the author still signs.
    - Round 2 of the review (on this revision): a PENDING mechanism for autoresearch's own prerequisites, decision
      G5-ARPEND (§2.13); one statement of G5-TASL-GPUH B against the cap; the freeze wait made a release deadline that
      covers every un-STOPped node; who amends K; the erratum's reviewed sha256; `g5_pin_check.py` compares mode, type
      and object and forces submodule diffs.
    - Round 3: under G5-ARPEND A and the K amendment neither the spec nor the launch commit changes: the spec carries
      PENDING markers for autoresearch's copy, environment and P10 and both seed blocks, and the switch reads the
      completion record and the note's `audit_K` (§2.13, §3, P4, §9, §11); the freeze-wait deadline has a 2-day margin.
- Values marked *(proposed)* are recommendations, not decisions. Two decisions of revision 7 are recorded
  (R1-G5-DECISIONS: G5-AR A, G5-PIN B) and G5-SPLIT is fixed by the preregistration; the others in §2 are open, and
  they interact. §2.8 and §2.11 show them
  together. §11 lists what the signature decides.

## 1. Authority (published `main` `3c3f822a`)

| Row | What it fixes here |
|---|---|
| R1-T1-HOST-TASL (21 Nov; amends the Ada fallback of R1-T1-HOST-H200) | The isolation fails in the HTCondor container on H200 (job 759828) and Ada is occupied, so the T1 table (G.1b, G.4, G.5) runs on the two RTX 4090 hosts: worker (training) on TASL-2 under the harness isolation; the proposer `llama-server` (gemma4_31b, exam settings: context 32,768, `-ngl 999 -np 1 --jinja`, q8_0 KV, `cache_prompt` false, `{"enable_thinking":false}`) on TASL-7 over Tailscale. G.1b may use both hosts' GPUs. One GPU model (RTX 4090) for the whole table. Precondition: the host checks pass on TASL-2 (and on TASL-7 if it runs workers); otherwise STOP. |
| R1-TRACKG-AR-U2-TASL2 (21 Nov) | `autoresearch_fixedtokens`' cond7a smoke and U2 move to TASL-2; the harness-isolation host checks pass on TASL-2 first. |
| R1-TRACKG-G3-EARLY | T1 nodes: `mlab_cifar10`, `mlab_imdb`, `mlab_ogbn_arxiv`, `mlgym_cifar10`, `mlgym_fmnist`, `mlgym_breakout_minatar`. `autoresearch_fixedtokens` and `mlgym_houseprice` "join as soon as their U2 passes". `mlgym_houseprice`'s U2 passed in the U4 census (20 Nov; CPU-only), so seven nodes are certain. `autoresearch_fixedtokens`' U2 passed on TASL-2 (the U4 census, `reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md`, B1 218.951 s on TASL-2's RTX 4090); it joins G.1b under a third note (R1-G1B-NOTE2-DECISIONS). It enters G.5 under G5-AR A (R1-G5-DECISIONS, §2.11). |
| R1-T1-TASL-ENV | Replaces the image row; it is on `main` and was a draft in revision 6. It fixes the following, and each STOPs the job if not met:<br>– **Hosts:** TASL-2 (driver 535.309.01) and TASL-7 (driver 580.178.04), each identified by host name and the full UUID of its RTX 4090; a driver change during the table STOPs.<br>– **Environments:** torch312 and jax312 built with uv from the census freezes (Python 3.12.16), equal to the freeze at every job start.<br>– **Harness:** at the commit the signed note names, clean; the harness-isolation host checks passed on every host that runs workers.<br>– **Jobs:** non-root, Yama `ptrace_scope` ≥ 1, the delegated scope (MemoryMax 8G, MemorySwapMax 0), the host's GPU lease, no other compute process on the card.<br>– **Proposer:** the Track X exam `llama-server` on TASL-7, used in place (executable `b70f4882…7d8b`, build `620d222`, its build directory bound by a manifest), with the pinned GGUF and the exam settings, on TASL-7's Tailscale address.<br>– **Node data:** manifests equal to the census (for `mlgym_fmnist` and `mlgym_cifar10`, the census erratum of R1-T1-DATA-MANIFEST).<br>Its environments do not include autoresearch's `ar-cond7a` (Python 3.12.15); R1-G1B-AR-ENV admits it for autoresearch's G.1b (P9). |
| R1-G1B-EDITS, R1-G1B-TIMEOUT | G.1b measures the four declared edits E1–E4 per T1 node (460 runs per node). The T1 timeout (G.1b, G.4, G.5) is 3 × the slowest of the node's B1, B2 and E1–E4 census records (`census_slowest_x3`; the node's own census host where that is a TASL host, as for autoresearch). In G.5, an edited proposal's timeout is its failure, and a baseline timeout STOPs the campaign. |
| R1-G1B-TASL-DECISIONS, R1-G1B-NOTE2-DECISIONS | **G.1b on the TASL pair.**<br>– The launch binding is LB A (`verify_launch_tasl`): hosts launch from the signed, published commit whose code equals the note's `paper_commit` outside `docs/` and the spec (paper_commit `10fd3343` in the first note).<br>– The signed first note (`authorizations/g1b_t1_tasl_20261121.md`, run_id `g1b-tasl-20261121-b`) ran the TASL-2 nodes from `985dd45d` (or its docs-only child `dbdbd2b6`), the checkout the signed G.4 note names; three are sealed.<br>– The three TASL-7 nodes run under a second note, with the same run_id, once the cross-host check has passed.<br>– `autoresearch_fixedtokens` joins G.1b under a third note with its own spec (run_id `g1b-ar-tasl-20261122-a`, R1-G1B-CAP's 100 GPU-h shared). Harness `2d09f9a9` is reviewed and the spec support is on `main` (`mac-g1b-ar-20261122`, READY 81, merged as `c35c922d`). The TASL-2 host check at that pin STOPped on 22 Nov (Python 3.12.16 against the frozen 3.12.15); its resolution and the third note are pending. |
| R1-T1-DATA-MANIFEST (22 Nov) | The census data manifests of `mlgym_fmnist` and `mlgym_cifar10` become the manifests the frozen environment produces (census erratum, independently reviewed: `reports/trackg_g0_20261117/T1_DATA_MANIFEST_ERRATUM_20261122.md`, reviewed bytes sha256 `9b40944be4df5f214066d689f7f0537590ed95895f9754b55630d8e774077799`, on `ops-t1-data-manifest-20261122` @ `ac298f25`, to be published on `main` byte-identical); the G.1b, cross-check and G.4 specs are re-issued with the corrected values (the TASL launch chain `mac-tasl-chain-20261122`, delivered and accepted (accepted at `cd50e36f`, confirmed at `e740dae7`), not yet on `main`; a G.1b amendment note for `mlgym_fmnist`, note 2 binding the amended spec, a full cross-check rerun as `g1b-tasl-20261121-b-xc2`, G.4). G.5's node data pins are these values (§5). |
| R1-G1B-AR-ENV (22 Nov) | Autoresearch's G.1b runs in `ar-cond7a` in place (`/home/dowling/r1_trackp/venvs/ar-cond7a`, Python 3.12.15, torch 2.6.0+cu124), read-only, for this node only, every job comparing `uv pip freeze` and the Python version with the committed freeze `sweep2/g1b/env/ar-cond7a.freeze.txt` (`11def6ad…`). The row names G.1b; G.5's use of the same environment for autoresearch is part of the G.5 note (P9, §11). |
| R1-G5-DECISIONS (22 Nov) | On revision 7: **G5-AR A** — G.5 covers eight nodes (the seven plus autoresearch); accepted cost as projected, about 305 GPU-h at K = 10 (autoresearch about 138), the cap raised accordingly ("425 GPU-h in revision 7, to be fixed in the G.5 note"), B.7 from about 8 Dec to about 15 Dec 2026; **K = 6** (about 208.5 GPU-h, B.7 about 11 Dec) only after a published K-check author row, until then **K = 10**. **G5-PIN B** — two G.5 harness commits carrying byte-identical G.5 code, one on `c025f89a` (the seven nodes' noise floor), one on `2d09f9a9` (autoresearch's); each node's G.5 runs on the harness commit of its own G.1b noise floor. "The G.5 note itself still needs the author's signature." |
| R1-G4-DECISIONS, signed G.4 note | G4-LB A (the TASL launch binding for G.4); G4-ORDER B (lease order only: the pilot runs whenever both cards are free); G4-NODE3 A (pilot nodes `mlab_cifar10`, `mlgym_fmnist`, `mlgym_breakout_minatar`; **no autoresearch-suite node**). The pilot: 3 instances per node (seeds 4001–4003), W = 20 manager calls, temperature 0.2, memory mode `history`, `max_tokens` 4096; run_id `g4-tasl-20261121-a`; `paper_commit` `02abb367`, launched from a checkout at or after `9c2979a2`; re-issued under R1-T1-DATA-MANIFEST (the corrected `mlgym_fmnist` manifest; launch commit (c) of the TASL launch chain, same run_id). Its sealed attempts feed the R1-BX-D14 recompute with one worker slot (P3). |
| R1-SWEEP2-PREREG (frozen 21 Nov) | `authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`, `frozen: true`. Relevant decisions:<br>– **PRE-SPLIT A:** P3 is the only evidence split. The T1 rule is G5-SPLIT verbatim, and its assignment is in `r1/c3/splits/c3_p3_split_v1.json` (sha256 `b5967dd7…`, eight T1 nodes, autoresearch included).<br>– **PRE-MEM C:** T1 enters with its mode(s) under G5-MEM.<br>– **PRE-DUP A:** the cross-instance repeat rule for the primary test and dev populations is the one G5-AUDIT proposed.<br>– **PRE-DIV A:** divergence on the evaluation seeds.<br>– **PRE-T1 A**, verbatim: "one primary gate read. The T1 node set and its instances are frozen in the arms-frozen record: exactly the T1 nodes whose train/dev labels were released and used to freeze the arms; a node needs ≥ 1 train and ≥ 1 dev instance to be supplied (otherwise reported, not supplied); nodes that STOP at G.5 follow the G.5 rule. No test partition of any tier is released before the arms-frozen record. A later read with more T1 nodes is not allowed."<br>– **PRE-SECONDARY A:** leave-one-suite-out is a descriptive analysis (no verdict), with fold arms retrained without the held-out suite; it STOPs if a suite has no labelled T1 node.<br>– **PRE-STAGE A:** a code lock for both sources: until the test release row exists, readers get the label block of train and dev instances only and no evaluation value of any instance (receipted partitions written by the release step).<br>– **PRE-DELTA A:** T1 σ_node from each node's sealed G.1b summary, its path and sha256 recorded in the T1 train/dev release row before any training (as amended by REL-T1-G1B, below).<br>– Procedure §4 steps 4–5: the **arms-frozen record** (arms, T0 and T1 node sets, split-file, noise-source and G.1b summary sha256s, gate and gate-input builder sha256s), then the test label blocks and every evaluation block.<br>The preregistration's sha256 is `aa1a961ba8eb4ab5c45579ea194260597ea3c2a804c731c92ed4ee778d7d7cc5`. |
| R1-SWEEP2-RELEASE-DECISIONS | REL-SCOPE A (PRE-STAGE A as signed: until a test row exists, readers get train/dev labels only); REL-CODE A (integrity checks in `r1/c3/release_checks.py`); **REL-T1-G1B:** PRE-DELTA's "each node's sealed G.1b summary on H200" reads "on the T1 host of R1-T1-HOST-TASL", each summary copied out of the sealed tree by a reviewed step with its sha256 before the T1 train/dev row (§3, §6). |
| R1-BX-D14 | Target dates: B.7 ≈ 8 Dec 2026, D.3 ≈ 3 Jan 2027, manuscript 10 Jan 2027. They are recomputed from measured throughput after the T1 pilot, and changes are reported to the author before they are applied. R1-G5-DECISIONS accepted B.7 moving to about 15 Dec with autoresearch (pre-pilot; with R1-BX-D14's spans, D.3 about 10 Jan 2027 and the manuscript about 17 Jan 2027). |
| R1-BX-D1, R1-BX-D5 | T1 nodes are label nodes; the nodes' fixed step budgets; one GPU model per table. |
| D1 | The campaign budget is compute (worker runs) plus an LLM-call cap (see G5-W). |
| D15, D26 | Manager temperature 0.2; every manager call carries a seed derived deterministically from (instance, trial index, repetition), recorded in its call event (see G5-TEMP). |
| R1-BX-D3, R1-BX-PROPOSED-CONFIRM (D3; Track G E4) | Audit seeds K = 6 (labels 7001–7003, evaluation 7006–7008) for T1 **only after** the sweep-1 subsampling check passes and a PLAN row records it; until then **K = 10** (repeated by R1-G5-DECISIONS for G.5). If the check fails, K stays 10 and the coordinating agent STOPs for the author. E4 also says "both memory modes; about 12 campaigns per T1 node" (see G5-MEM). |
| R1-BX-PROPOSED-CONFIRM (E5) | Divergence = a non-finite loss, or no metric at the fixed budget. A divergent proposal enters no belief bin, is counted separately, and has action target u = −g. If only some seeds diverge, μ comes from the rest and the label is marked partial; more than half diverging makes the proposal divergent. A heavy-tailed node uses a Student-t, declared before labels are built. |
| R1-MAIN-PROPOSER (e) | Duplicates are grouped by (instance, incumbent hash, edit hash) for folds and deduplication; one instance → train/dev/test assignment; pooled intervals use an instance-cluster bootstrap. |
| R1-BX-D8-V3-A (3) | Split per tier P3 = 1/3 : 1/6 : 1/2 (train : validation : test), written into the analysis preregistration. |
| R1-BX-D8-V3-B (author's addition) | **T1 = 12 instances per node**; per-tier test floor T1 ≥ 3 test instances per node; a node below the floor is excluded from the IQM, kept in the PoI and reported. |
| R1-BX-D8-CONFIRM-V31 (replaces the gate of R1-BX-D8-CONFIRM) | Gate v3.1: `r1/c3/gate.py` @ `31dab9efb94b7f187ec44cab1bc4a4ad63c1085d`, sha256 `a3f7d002b54829c1fa40b7b18a1e2f4c5327749f20ae3ab7e0751b68c009cf23` (it differs from v3 only in accepting a declared T0 node set); T0 and T1 pooled with tier as a stratum; partial T1 at B.7 read on T0 plus the labelled T1 nodes, disclosed; leave-one-suite-out needs at least one labelled T1 node per suite, otherwise it STOPs; the aggregate gate does not STOP on it. The T1 seal is lifted by the T1 release rows under PRE-STAGE A (§6). |
| R1-MAIN-PROPOSER, R1-EXAM-X7, R1-SWEEP2-SETTINGS (1) | Proposer `gemma4_31b`, thinking off, the exam server flags, context 32,768, `cache_prompt` false. |
| R1-EXAM-B1-TRUNCATION-INVALID | Every proposer call carries a completion cap; a truncated reply is an invalid proposal. |
| R1-BX-PROPOSED-CONFIRM (D4) | `manager_proposal/v2-diff`. A pick that fails diff liveness on a T1 node is a STOP; the author decides between a single-parameter fallback and moving the node to T2. |
| R1-TRACKG-G5-DIVERGENCE (4 Nov) | Asked "whether a T1 node should STOP when its audited label proposals' divergence fraction exceeds 20 %, or instead be judged case by case", the author replied "设 20% STOP" (set a 20 % STOP). The recorder's *(proposed)* consequence: a move to T2 needs a separate author row. The 20 % "originated as an agent proposal, not a measured threshold". |
| R1-TRACKG-PORT-DECISIONS (3), (4) | (3) The port-written imdb baseline is frozen and independently reviewed before any label run, and the census funnel and appendix say "baseline written by us". (4) Timeout = 3 × the census baseline run time; a timeout is the proposal's failure, not an infrastructure rerun. |
| R1-HARNESS-ISOLATION | Every T1 label run is effectively isolated: `effective: true`, `waivers {}`, `exceptions []`. Anything else is refused. |
| R1-B2-DECOUPLE, 28 Oct clarification | Labels use the label seeds; the evaluation seeds are never used for C3 or Track P training, tuning or selection. |

**The v2-diff engine as it is** (harness `c025f89a`, the TASL G.1b and G.4 pin; it adds only `--gpu-uuid`, CPU-only
chunks and `stop_on_timeout` to `b5747066`, none of which touches the v2-diff engine; autoresearch's pin `2d09f9a9`
descends from `c025f89a` and changes only autoresearch's node files and config, `node_lib/ar_isolated.py`, a code-unit
report and the port-check tests, not the engine): one manager call per proposal; a
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
  192 at 0.8, §2.8), close to the task's "~150". The engine supports it today, and the signed G.4 pilot runs it
  (W = 20 manager calls), so P3 needs no re-run.
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
  `24935be3`, and the signed G.4 pilot runs at 0.2, so the pilot's shares are measured under the setting G.5 uses. The seed
  rule meets D26's determinism (instance, trial index, repetition 0) but is not T0's derivation function; disclosed.
- **B: temperature 0 (the engine's original default).** Fully deterministic on a deterministic server. At step 1
  every instance of a node sees the same prompt (baseline code, no history), so all 12 instances make the same first
  proposal; instances diverge only through the metrics that later enter the history. More cross-instance
  duplicates, less diversity; a disclosed deviation from D15. The pilot would have to be re-run at 0.

### 2.3 G5-MEM: memory mode (recommendation: A)

E4 says "both memory modes; about 12 campaigns per T1 node"; V3-B says 12 instances per node.

- **A (recommended): the engine's `history` mode only, 12 instances.** 12 campaigns per node, as E4 counts them; 6
  test instances under P3, above the floor of 3. Disclosed as different from both T0 modes. **It amends E4's "both
  memory modes" and needs an author row saying so.** The memory contrast stays on T0, where both modes run. The
  signed G.4 pilot runs `history`. PRE-MEM C takes T1 "with its mode(s) under G5-MEM (one mode under G5-MEM A, the
  same rule as T0 under B)": the parenthesis refers to G5-MEM B, under which T1 has both modes as T0 does.
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
    (`reuse_parent_runs: false`, K = 10, recommended row: at ran share 0.6, 188.3 GPU-h for seven nodes and 349.5
    for eight, within the caps; at 0.8, 235.6 (above 230) and 445.5 (above 425), so re-running every parent at share
    0.8 needs a higher cap).
  - **E5 per seed block.** A proposal's label status (divergent, partial or not) is decided by E5 over the **label
    seeds** only (7001–7005, or 7001–7003 at K = 6). Divergence on the evaluation seeds is part of the evaluation
    value `y_eval` and is handled by PRE-DIV A of the frozen preregistration; it never changes a training label,
    the divergence STOP or a pre-release count (R1-B2-DECOUPLE). Applying E5 over all K seeds would let evaluation-seed outcomes
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
    R1-TRACKP-SFT-DUP for Track P). **The gate side of this rule is now fixed by PRE-DUP A** of the frozen
    preregistration; only the audit-once part stays *(proposed)* here.
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

### 2.6 G5-CAP: the GPU-hour cap (425 GPU-h for eight nodes, as projected; the figure fixed by this note)

Under W A, MEM A, AUDIT A (§2.8; worker-card hours, G5-TASL-GPUH A): with the seven nodes, 119–144 GPU-h at K = 6
and 167–206 GPU-h at K = 10 (ran share 0.6–0.8); with autoresearch as the eighth node, 209–260 GPU-h at K = 6 and
305–386 GPU-h at K = 10. Direct host runs have no scheduler, so there are no requested slot-hours; the binding
quantity is the worker card's wall time (G5-SLOT).

R1-G5-DECISIONS raised the cap "accordingly (425 GPU-h in revision 7, to be fixed in the G.5 note)". This draft fixes
it at **425 GPU-h of the worker card** (option B of revision 7 with autoresearch): it covers K = 10 at ran share ≤ 0.8
with a 10 % margin (386.0 × 1.1 = 424.6) under W A, MEM A, AUDIT A with reused parents, and G5-TASL-GPUH A. Any other
combination of §2.8/§2.11 needs the cap of its row instead, which the signature then fixes (§11): MEM B, W B,
`reuse_parent_runs: false` at share 0.8 (445.5) exceed 425; both cards counted (G5-TASL-GPUH B) stay within 425
only at share 0.6 and only if the server is stopped during the audits (≈ 360), and exceed it otherwise (§2.9). Options A
(150 GPU-h, K = 6 only) and C (a pre-declared audit subset) of revision 7 do not fit eight nodes and are withdrawn.

Under every option: the projection and the consumed worker GPU-hours (a running meter from the job records) within
the cap. The proposer card's hours are reported beside them (G5-TASL-GPUH).

### 2.7 G5-SPLIT: the instance split (fixed by R1-SWEEP2-PREREG; no longer a decision)

Per node, the 12 instances are ordered by `sha256("c3_t1_split/v1:" + <node> + ":" + <instance seed>)`. The first 6
are test, the next 2 validation, the remaining 4 train (P3 = 1/2 : 1/6 : 1/3 of 12). The frozen preregistration
(PRE-SPLIT A) quotes this rule and binds the split file `r1/c3/splits/c3_p3_split_v1.json` (sha256
`b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569`, schema `c3_p3_split/v1`). Its `t1` block names
the salt `c3_t1_split/v1`, the seeds 5101–5112 and eight nodes, `autoresearch_fixedtokens` included. The signed note
cites that file; the G.5 code reads the assignment from it and recomputes it from the rule as a check. The
per-instance diagnostics are read only after the split exists (it does).

### 2.8 The decisions together (pre-pilot, `sweep2/t1_tasl/g5_projection_tasl.py`)

Worker GPU-hours and audited proposals per node, seven nodes (census run times on the RTX 6000 Ada × 1.0, LLM 60 s per
call; the 4090 values replace both after the G.4 pilot). AUDIT A; cross-instance duplicate factor 1.0 (conservative;
the pilot measures it); parents = the 12 baselines (a kept proposal's audit runs serve again when it is a later
parent: same code state, same seeds, on a fixed-seed-deterministic host); MEM "both" is an upper bound (twin campaigns
share labels by key). The eight-node figures with autoresearch are in §2.11.

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
days of the worker card alone (12.7–16.1 days with autoresearch, §2.11).

### 2.9 G5-TASL-GPUH: which card's hours count against the cap (recommendation: A)

On H200 one card carried the server and the worker. On the TASL pair the proposer holds TASL-7's card for the whole
campaign span while the worker uses TASL-2's.

- **A (recommended): the cap counts the worker card (TASL-2).** The proposer card's held hours (campaign spans) are
  metered and reported beside it, not capped. The 230 GPU-h of G5-CAP B were sized on worker plus server work on one
  card, so A is the closer like-for-like.
- **B: both cards count.** What the proposer card adds depends on how long the server is held:
  - held for the campaign waves only (stopped during the audits): + the campaign hours, 167 + 39 ≈ 206 GPU-h at ran
    share 0.6 and 206 + 43 ≈ 249 at 0.8 (K = 10, W A, MEM A) — within cap B at 0.6, above it at 0.8;
  - held for the whole label span (G5-SLOT A, one server start): × 2, ≈ 334 and 412 GPU-h; cap B would need raising.
  - With autoresearch (G5-AR A), K = 10, W A, MEM A: campaign waves only, 305 + 55 ≈ 360 GPU-h at 0.6 (within 425)
    and 386 + 62 ≈ 448 at 0.8 (above 425); the whole span (G5-SLOT A with one server start), ≈ 611 and 772 (above
    425). So under B the 425 cap holds only at share 0.6 with the server stopped during audits.

### 2.10 G5-SLOT: one worker slot, and TASL-7 (recommendation: A)

TASL-7's card serves the proposer for the table's span (it holds TASL-7's GPU lease), so G.5 has **one** worker slot
(TASL-2). TASL-7's G.1b nodes (under the second G.1b note, after the cross-host check) must be sealed before the G.5
server starts, since both use TASL-7's lease. The G.4 pilot is not ordered against G.1b (G4-ORDER B), but it also
needs TASL-7's lease. Autoresearch's G.1b (third note, ≈ 28.2 GPU-h) runs on TASL-2 and so shares the worker card
with G.5.

- **A (recommended): one slot, nodes in sequence on TASL-2.** The dates below are pre-pilot, from `g4_tasl.py dates`
  with `--today 2026-11-22` (G.4 is signed but has not run; nothing from the cross-check or the pilot, and three of
  the seven G.1b nodes, are sealed). They assume the remaining G.1b work takes 1 day before the labels start. These
  are the seven-node dates, kept for comparison; G.5 covers eight nodes (§2.11, R1-G5-DECISIONS).
  - Seven nodes, K = 10, ran share 0.6 and LLM 60 s per call: labels done 5 Dec, B.7 8 Dec, **0 days of slack**
    against R1-BX-D14. The slack was 1 day on 21 Nov; the day lost is the calendar day, not a new measurement.
  - At ran share 0.8, or at 120 s per call: B.7 10 Dec (−2 days).
  - With 2 days of remaining G.1b: B.7 9 Dec (−1), or 11 Dec (−3) at share 0.8 or 120 s per call.
  - With autoresearch: §2.11.

  The 4090's LLM speed for a 31B Q4 model on one card is the main unknown; the G.4 pilot measures it.
- **B: audits on TASL-7 while campaigns pause.** The audit chunks need no proposer, so TASL-7's card could run audits
  between the waves when the server is stopped. This needs TASL-7's host checks (R1-T1-HOST-TASL's precondition) and
  a server restart per wave (identity re-checked each time); about 30–40 % shorter label span. Not built.

### 2.11 G5-AR: how `autoresearch_fixedtokens` enters G.5 (decided: A, R1-G5-DECISIONS)

Autoresearch is the only autoresearch-suite T1 node. The author kept it in G.1b because it is "needed for
leave-one-suite-out" (R1-G1B-TASL-DECISIONS, R1-G1B-NOTE2-DECISIONS). The published rules decide what it is worth:
- Under R1-BX-D8-CONFIRM-V31, leave-one-suite-out STOPs unless each suite has a labelled T1 node; the aggregate gate
  does not STOP. Under PRE-SECONDARY A, leave-one-suite-out is a descriptive analysis (no verdict) with fold arms
  retrained without the held-out suite. What autoresearch adds is a third suite in the T1 stratum and a
  leave-one-suite-out analysis that does not STOP; the aggregate verdict does not depend on it.
- Under PRE-T1 A, there is one primary gate read; the T1 node set is "exactly the T1 nodes whose train/dev labels
  were released and used to freeze the arms" (each with ≥ 1 train and ≥ 1 dev instance), and "a later read with more
  T1 nodes is not allowed". So autoresearch enters any gate read only if its train/dev labels are released before the
  arms-frozen record.

What it costs (pre-pilot, `sweep2/t1_tasl/g5_ar_projection_tasl.py --today 2026-11-22`; W A, MEM A, AUDIT A):
- Its census B1 run takes 218.951 s on TASL-2's 4090 under the option-A isolation path. On the Ada, un-isolated, it took
  67.901 s (U2, 17 Nov): the census records a 3.225× cross-host option-A slowdown (bpb and VRAM not normalised). Most
  of autoresearch's cost here is that slowdown, not the node's intrinsic weight; the other nodes' times are Ada
  times (the slowest, `mlab_imdb`, 64.1 s). Its timeout basis is 767.748 s (3 × E2's 255.916 s, R1-G1B-TIMEOUT).
- Alone it needs 138.4 GPU-h at K = 10 and ran share 0.6 (campaigns 15.7, audits 118.6; 10 jobs, 8 of them audit
  chunks). That is 45 % of the eight-node total. It needs 179.8 GPU-h at share 0.8 and 89.8 at K = 6.
- The G.4 pilot does not measure it (G4-NODE3 A), so its per-call time and shares stay at the fallbacks until G.5's
  own first wave.
- Its census time is already a 4090 time, so the post-pilot 4090/census ratio must not be applied to it (§8, §9).

| W | MEM | Ran share | K = 6 GPU-h (8 nodes) | K = 10 GPU-h (8 nodes) | Audited per node |
|---|---|---|---|---|---|
| A: 20 calls | A: one mode | 0.6 | 208.5 | 305.3 | 144 |
| A: 20 calls | A: one mode | 0.8 | 259.9 | 386.0 | 192 |
| A: 20 calls | B: both | 0.6 | 417.0 | 610.7 | 288 |
| A: 20 calls | B: both | 0.8 | 519.8 | 772.1 | 384 |
| B: 20 runs, cap 80 calls | A: one mode | 0.6 | 334.9 | 489.5 | 240 |
| B: 20 runs, cap 80 calls | A: one mode | 0.8 | 320.9 | 475.5 | 240 |

Dates with autoresearch, one worker slot (G5-SLOT A). The table assumes 2 days of remaining G.1b before the labels,
because autoresearch's G.1b (≈ 28.2 GPU-h) and the TASL-2 G.1b work share TASL-2. With 1 day, each B.7 is one day
earlier. R1-G5-DECISIONS accepted the first row's B.7 (about 15 Dec). The AR host check at `2d09f9a9` STOPped on 22 Nov,
so autoresearch's G.1b may start later than this assumes; the recompute after the pilot (P7) takes the actual state.

| K | Case | GPU-h | Labels done | B.7 | Slack against 8 Dec |
|---|---|---|---|---|---|
| 10 | share 0.6, LLM 60 s | 305.3 | 12 Dec | 15 Dec | −7 |
| 10 | share 0.8 | 386.0 | 16 Dec | 19 Dec | −11 |
| 10 | LLM 120 s | 337.3 | 14 Dec | 17 Dec | −9 |
| 6 (K-check PASS row only) | share 0.6, LLM 60 s | 208.5 | 8 Dec | 11 Dec | −3 |
| 6 (K-check PASS row only) | share 0.8 | 259.9 | 10 Dec | 13 Dec | −5 |

D.3 and the manuscript move with B.7 (the recompute shifts them by R1-BX-D14's spans). At K = 10 and share 0.6 that
gives D.3 10 Jan and the manuscript 17 Jan.

- **A (decided): eight nodes in one G.5 table, the same design for every node.** Autoresearch runs 12 instances
  under the same W, memory mode, temperature, K, audit, divergence and STOP rules.
  - Its own prerequisites gate only its own jobs; the seven nodes may start before them (under G5-ARPEND A, §2.13;
    under G5-ARPEND B the signature waits for them). They are: its G.1b noise floor under the third note (P2, P10);
    its environment for G.5 (P9); the TASL-2 host check at its pin (P1); and its REL-T1-G1B summary copy. The G5-PIN B
    commits (P5) are needed before any G.5 job.
  - Cap: 425 GPU-h (§2.6).
  - The date change goes to the author under R1-BX-D14 with the post-pilot numbers (P7), before it is applied.
  - **The freeze wait** *(proposed rule; review M3, round 2 m4)*. Under PRE-T1 A the arms-frozen record fixes the T1
    node set once. The arms-frozen record therefore **waits for the train/dev release of every T1 node of this table
    that has not STOPped** (autoresearch included; the T1 train/dev release row naming them, §6). The deadline is a
    release date: **18 Dec 2026** *(proposed)*: the projected labels-done date at K = 10 and share 0.8 (16 Dec) plus 2
    days for the REL-T1-G1B copies and the release row (B.7 then about 21 Dec), recomputed with P7 and fixed in the
    signed note. Without that margin STOP 14 would fire by construction in the worst projected case. If a node's release has
    not happened by then (a late node, autoresearch's prerequisites still PENDING, or the wave not finished), or a
    node STOPs at G.5, the coordinating agent STOPs for the author (STOP 14). Only an author row may then freeze the
    arms without that node; under PRE-T1 A it then enters no gate read (for autoresearch, leave-one-suite-out also
    STOPs in the descriptive analysis). No agent freezes the arms without a node on its own. For this table, this
    rule refines R1-BX-D8-CONFIRM-V31's "if only some T1 nodes have labels by B.7, read … on the available labelled T1
    nodes": the available nodes are fixed by the author, not by timing.
  - G5-SLOT B (audits also on TASL-7) would shorten the span by about a third; it is not built.
- **B (not chosen): seven nodes in G.5; autoresearch by a later amendment.** The cap would have stayed 230 GPU-h.
  Like for like (2 days of remaining G.1b in both, autoresearch's G.1b ordered by R1-G1B-NOTE2-DECISIONS either way),
  B.7 would have been 9 Dec against A's 15 Dec, 6 days earlier; with 1 day, 8 against 14 Dec. Autoresearch's labels
  would have come about 6 days after the seven on the one slot. Under PRE-T1 A they would have entered a gate read
  only if the arms-frozen record waited for them (the same days as A plus a second note, a review and an amendment);
  without that wait, autoresearch would have entered **no** gate read unless the preregistration were amended, and
  leave-one-suite-out would have STOPped.
- **C (not chosen): autoresearch with fewer instances or audits** (for example 6 instances, 3 of them test, exactly
  at the floor). About half its cost, but it contradicts V3-B's 12 instances per node and the split file's 12.

### 2.12 G5-PIN: two G.1b harness pins (decided: B, R1-G5-DECISIONS)

The seven nodes' noise floors come from harness `c025f89a`; autoresearch's will come from `2d09f9a9` (third note).
P5 requires the G.5 harness commit to descend from the G.1b pin, with the measurement path byte-identical, so that the
noise floor and the labels share it.

Commit `2d09f9a9` descends from `c025f89a` and changes files inside that path:
- autoresearch's node directory and its config;
- `src/autoresearch/trackg/node_lib/ar_isolated.py`, the master that `isolation.py` loads for its sandbox probe. Its
  diff is a docstring and `torch.cuda.init()` inside the compatibility helper `cuda_open`, which no node uses.

No single G.5 commit is therefore byte-identical over the whole path to both pins.

- **B (decided): two G.5 harness commits with byte-identical G.5 code.**
  - `G5-7` descends from `c025f89a` and carries the seven nodes; `G5-AR` descends from `2d09f9a9` and carries
    autoresearch. Each node's G.5 jobs run on the commit of its own G.1b noise floor.
  - **The check that enforces it** (built in this revision: `sweep2/t1_tasl/g5_pin_check.py`, tests
    `r1/tests/test_t1_tasl_g5_pin_check.py`). For the whole tree, not a list of G.5 files:
    1. `G5-7` descends from `c025f89a`, `G5-AR` from `2d09f9a9`, and `2d09f9a9` from `c025f89a`;
    2. the paths that differ between `G5-7` and `G5-AR` are exactly the paths that differ between the two pins (the
       pin delta: autoresearch's node and config files, `node_lib/ar_isolated.py`, a report, tests);
    3. on each pin-delta path, `G5-7` holds `c025f89a`'s blob and `G5-AR` holds `2d09f9a9`'s.
    So every file outside the pin delta, everything G.5 adds or changes included, is byte-identical between the two
    commits, and G.5 changes no pin-delta file. On the real harness the two pins themselves pass (no G.5 code yet).
    The G.5 switch runs it at every job start, with the two commits from the note (§5), and STOPs on any failure
    (STOP 13).
  - The literal P5 holds within each family (each G.5 commit against its own G.1b pin), checked separately (§7 P5).
  - There are two harness checkouts on TASL-2, as G.1b already has for autoresearch (the third note's second
    checkout). A node launched from the other family's checkout STOPs (§4 item 13).
- **A (not chosen): one G.5 commit descending from `2d09f9a9`, with P5 per node** (the seven nodes checked against
  `c025f89a` except the pin-delta files, bound by sha256); it would have weakened P5's literal byte-identity.

### 2.13 G5-ARPEND: autoresearch's own prerequisites at signature (recommendation: A)

Autoresearch's prerequisites are independent of the seven nodes': the TASL-2 host check at `2d09f9a9` (P1; STOPped on
22 Nov), its G.1b under the third note with its D21 verdict (P2), its environment for G.5 (P9), its Student-t or
Gaussian declaration (P10), and its REL-T1-G1B summary copy (§3, §5 `noise_floor`).

- **A (recommended): PENDING at signature, completed by a record.** The signed note may record these five items for
  autoresearch as PENDING. The G.5 switch refuses autoresearch's jobs until a **completion record** is on `main`:
  `docs/r1/reports/<…>/G5_AR_PREREQUISITES_<YYYYMMDD>.md`, citing, each with path and sha256, the host-check binding
  record at `2d09f9a9` (PASS), the third note and its sealed G.1b summary with the D21 verdict, the REL-T1-G1B copy of
  that summary, the P10 declaration, and the environment (`ar-cond7a` freeze `11def6ad…`, or the one a row resolving
  the host-check STOP names). The coordinating chat commits it after an independent review, **without a further author
  decision**, as for note 2 under R1-G1B-NOTE2-DECISIONS. **Neither the spec nor the signed note changes:** the spec
  carries a PENDING marker in place of autoresearch's summary copy, environment and P10 declaration, and the note's
  `noise_floor` and `ar_prerequisites` lines name the completion record's path pattern; the switch reads the three
  items from the record on `main` and checks every cited sha256 (STOP 15), so the spec sha256 the note binds stays the
  same and no launch commit is re-issued. If the environment differs from `ar-cond7a`, the row that resolves the STOP
  must name its use for G.5 too. The seven nodes start without waiting; the freeze wait (§2.11)
  bounds how late autoresearch may come.
- **B: the signature waits for all of them.** Then the seven nodes do not start before autoresearch's prerequisites
  pass, and the dates of §2.11 move by however long the host-check STOP takes to resolve.

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
assembled, each node is declared Gaussian or Student-t from the G.1b summary (E5; prerequisite P10). The seven nodes'
summary is that of run `g1b-tasl-20261121-b`, assembled from both hosts' sealed node directories: the first note's
three sealed TASL-2 attempts and the attempts under the spec re-issued by R1-T1-DATA-MANIFEST, joined under decision
G1B-JOIN (author row R1-G1B-JOIN pending; the launch chain report). Autoresearch's is that of
`g1b-ar-tasl-20261122-a`, in the `ar-cond7a` environment at harness `2d09f9a9`. Each summary reaches G.5 through the
**REL-T1-G1B step** (R1-SWEEP2-RELEASE-DECISIONS): copied out of the sealed tree by a reviewed step, with its sha256,
before the T1 train/dev release row, which records the path and sha256 (PRE-DELTA A). The G.5 note and spec name the
seven-node copy and its sha256 (§5). Autoresearch's copy is named the same way under G5-ARPEND B; under G5-ARPEND A the
spec carries a PENDING marker for autoresearch's copy, environment and P10 declaration, and the switch takes them from
the completion record on `main`, checked by sha256 (§2.13, STOP 15).

**Checkouts.** The paper-repo checkouts are kept apart, as for G.1b and G.4:
- G.1b's first note ran from `985dd45d` (or its docs-only child `dbdbd2b6`), as the signed G.4 note states; the
  amendment note and note 2 launch from chain commit (a) of the TASL launch chain, the cross-check (`-xc2`) from (b),
  the G.4 pilot from (c) (R1-T1-DATA-MANIFEST; the chain is delivered and accepted, not yet on `main`; it is published
  by merge), and autoresearch's G.1b from the third
  note's commit (a later delivery).
- G.5 launches from its own published checkout, at or after the commit that publishes the G.5 note and spec, whose
  code equals the note's `paper_commit` outside `docs/` and the spec (the TASL launch binding, §9).
- The G.5 job reads the G.1b summaries only as the REL-T1-G1B copies, by path and sha256 (above), never from the
  sealed run directories or through another launch's checkout.

The harness checkouts are per G5-PIN.

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
8. **Timeout.** The basis is R1-G1B-TIMEOUT's `census_slowest_x3` (decided), so the noise floor and the labels share
   it (on the 4090, a G.1b run reaching it is already a STOP). A timeout is the proposal's divergent failure (E5 over
   the label seeds). A **baseline** timeout STOPs the campaign.
9. **Budget.** The projection or the consumed GPU-hours above the cap (G5-CAP; worker card per G5-TASL-GPUH); a job
   past its declared deadline; *(proposed)* an audited count per node after wave 1, extrapolated to 12 instances, outside the band of G5-W (100–200 under A, 150–240 under B; doubled under MEM B). The cross-instance
   duplicate share seen in 4 instances understates the share for 12, so the extrapolation overstates the audited count.
   The author then decides: accept, change W, or cap the audits.
10. **Seeds.** Any use of the evaluation seeds outside the audit's evaluation block, or, when K = 6, of seeds 7004–7005
    (label) or 7009–7010 (evaluation), is a STOP (as the preregistration's §3 and §6). The G.5 validator refuses
    every other reserved block (below).
11. **Reading.** Any read of sealed content before its release step (§6) is a STOP and is reported.
12. **Proposer.** The TASL-7 server unreachable over Tailscale, restarted, or with `/props` (context, slots, build,
    GGUF) different from the server record STOPs the job (infrastructure); the wave is re-run as a new attempt after
    the identity is re-checked, never resumed.
13. **Harness family** (G5-PIN B). A node's job at a harness checkout other than its family's G.5 commit, or any failure
    of `g5_pin_check.py` on the note's two G.5 commits (G.5 code not byte-identical, a pin-delta file changed, an
    ancestry broken), STOPs the job.
14. **The freeze wait** (§2.11). The train/dev release of any un-STOPped T1 node of this table (autoresearch included)
    not done by the date the note fixes (*(proposed)* 18 Dec 2026), or a node STOPped at G.5: the coordinating agent
    STOPs for the author before the arms-frozen record. Only an author row may freeze the arms without that node.
15. **Autoresearch's prerequisites** (G5-ARPEND A). An autoresearch job without the completion record of §2.13 on
    `main`, or with a record whose cited files or sha256s do not match, STOPs.

**After a node STOP**, the node's partial outputs stay sealed and kept. Whether its labelled instances enter the
table is decided by an author row; they count toward B.7 only if that row says so and the node has at least 3 labelled
test instances.

## 5. Key values (the final note carries these lines; the G.5 switch matches every one)

```
approved: false
label: EVIDENCE
run_id: c3_t1_labels_<YYYYMMDD>
hosts: worker TASL-2 (RTX 4090 GPU-4d623e76-7587-ee15-a633-46f60d220d94, driver 535.309.01), proposer TASL-7 (RTX 4090 GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1, driver 580.178.04) over Tailscale http://tasl-7.tail119748.ts.net:8095
host_authority: R1-T1-HOST-TASL; environment row R1-T1-TASL-ENV; for autoresearch, R1-G1B-AR-ENV's ar-cond7a extended to its G.5 jobs by this note (P9)
environments: torch312 d2e70fe4…, jax312 80a455c6… (census freezes, Python 3.12.16); ar-cond7a sweep2/g1b/env/ar-cond7a.freeze.txt 11def6ade60a81eeb43856652048d74a43fd588a7c7c7ccbf98af817cb82fef1 (Python 3.12.15; autoresearch only; subject to the resolution of the 22 Nov AR host-check STOP)
llama_server_sha256: b70f488248ba6c77c1a0750ba666e08d827fc42cfdac918726b6704aaca47d8b; build 0.7.0-dev (build 1, commit 620d222); build-directory manifest a29c667f770b9f62f99e86359867b88d08a2e4781d3a55bd3c2dd58552f1e170 (as in the signed G.4 note)
gguf_sha256: 2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75
harness_commit: G5-7 <the reviewed G.5 commit on c025f89a> (seven nodes); G5-AR <the reviewed G.5 commit on 2d09f9a9> (autoresearch); g5_pin_check.py PASS on the pair (G5-PIN B, R1-G5-DECISIONS); per family, the measurement path byte-identical to its G.1b pin (P5)
g1b_harness_commit: c025f89aeafc2199bf3487b4bcaa16678273c702 (seven nodes); 2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe (autoresearch)
gpu_model: NVIDIA GeForce RTX 4090 (campaigns and audits on TASL-2; server on TASL-7)
nodes: mlab_cifar10,mlab_imdb,mlab_ogbn_arxiv,mlgym_cifar10,mlgym_fmnist,mlgym_breakout_minatar,mlgym_houseprice (CPU-only),autoresearch_fixedtokens (G5-AR A, R1-G5-DECISIONS)
data_manifests: the census node data manifests (R1-T1-TASL-ENV), with the census erratum of R1-T1-DATA-MANIFEST for mlgym_fmnist 24cb34483c5a23b4e7a198ac2840044171f2668d4f8cb3fe8b5e53ac69cadc32 and mlgym_cifar10 54d3a74d342d285fe724538a46872d028639533b4280557b00062e3d3c706100 (record reports/trackg_g0_20261117/T1_DATA_MANIFEST_ERRATUM_20261122.md); autoresearch ab7186d2… (its G.1b spec); each equal to the node's G.1b spec
instances_per_node: 12 (per memory mode under G5-MEM B)
instance_seeds: 5101-5112 (instance k: training = split = manager seed 5100 + k)
instance_split: r1/c3/splits/c3_p3_split_v1.json sha256 b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569 (R1-SWEEP2-PREREG, PRE-SPLIT A; rule of §2.7)
memory_mode: <G5-MEM: history | history and none>
campaign_W: 20 <manager calls | worker runs with an LLM-call cap of 80> (G5-W)
proposer: gemma4_31b (thinking off; exam flags; context 32768; cache_prompt false)
temperature: <G5-TEMP: 0.2 | 0.0>; per-call seed sha256("<manager seed>:<step>")[:8]
completion_cap_tokens: 4096
proposal_schema: manager_proposal/v2-diff
timeout_basis: census_slowest_x3 (R1-G1B-TIMEOUT)
audit_K: 10 (R1-G5-DECISIONS: K = 6 only after a published K-check author row; then the coordinating chat amends this line and the two seed lines by a docs-only amendment of the note citing that row, before the first audit chunk; the spec carries both seed blocks and does not change, and the switch reads audit_K from the note as amended and checks the row is on main; uniform within the table)
audit_seeds_label: 7001-7005 (7001-7003 only under K = 6)
audit_seeds_evaluation: 7006-7010 (7006-7008 only under K = 6)
audit_scope: <G5-AUDIT>; duplicate key (instance, incumbent hash, candidate hash); cross-instance groups audited once; gate repeats per PRE-DUP A
divergence_stop: <G5-DIV>
liveness_floor: 0.25 (proposed)
audited_band: <per G5-W> (proposed)
noise_floor: <g1b-tasl-20261121-b summary (joined under G1B-JOIN): the REL-T1-G1B copy, path and sha256>; <g1b-ar-tasl-20261122-a summary: the REL-T1-G1B copy, path and sha256 (G5-ARPEND B) | as cited by the completion record docs/r1/reports/<…>/G5_AR_PREREQUISITES_<date>.md, read by the switch (G5-ARPEND A)>; joined by node (g1b_tasl_join.py floor-by-node; the split file's eight T1 nodes)
tails: <per node Gaussian or Student-t (P10)>
job_layout: per node on TASL-2 in sequence (G5-SLOT), wave 1 (4 instances) campaigns then audits, wave 2 (8 instances) campaigns then audits; audits in chunks with declared deadlines
launch: the TASL launch binding (LB A of R1-G1B-TASL-DECISIONS, as G4-LB A): a published checkout at or after the commit that publishes this note and the spec, code equal to paper_commit outside docs/ and the spec
gpu_hours: <projection per §8, recomputed from the pilot (P7)>
cap_gpu_hours: 425 (fixed by this note; R1-G5-DECISIONS raised the cap "accordingly", as projected), counted per <G5-TASL-GPUH: the worker card (A) | both cards (B: within 425 only at share 0.6 with the server stopped during audits)>
proposer_card_hours: <metered and reported>
cuda_ipc: <C12 PASS: record path and sha256 | the acceptance line below, signed>
freeze_wait: the arms-frozen record waits for the train/dev release of every un-STOPped T1 node of this table until <date; (proposed) 2026-12-18> (STOP 14)
ar_prerequisites: <PASS, cited | PENDING until the completion record G5_AR_PREREQUISITES_<date>.md (G5-ARPEND A; STOP 15)>
gate: r1/c3/gate.py @ 31dab9efb94b7f187ec44cab1bc4a4ad63c1085d sha256 a3f7d002b54829c1fa40b7b18a1e2f4c5327749f20ae3ab7e0751b68c009cf23 (v3.1, R1-BX-D8-CONFIRM-V31)
preregistration: docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md sha256 aa1a961ba8eb4ab5c45579ea194260597ea3c2a804c731c92ed4ee778d7d7cc5 (frozen)
release_rows: R1-T1-LABELS-UNSEAL (train and validation), R1-T1-LABELS-TEST-RELEASE (test labels and every evaluation block) (§6; PRE-STAGE A, REL-SCOPE A, REL-T1-G1B)
```

**The CUDA-IPC acceptance line** (used only if C12 has not passed before the first G.5 job; the coordinator's queue
asks for the host test on TASL-2 or this line, after review condition C1 and the G.4 note's P1, which accepts the risk
for the pilot only). Text for the author to sign, verbatim in the note:

```
cuda_ipc_acceptance: The author accepts, for the G.5 label runs (EVIDENCE) on TASL-2, the residual risk that harness-isolation host-check item 7 (CUDA IPC across the isolation boundary, reports/HARNESS_ISOLATION_20261117.md §3) is untested on TASL-2: no frozen parent exports a CUDA tensor, harness 2d09f9a9 documents that no node uses cuda_share or cuda_open, and every run record that is not effective with empty waivers and exceptions still STOPs its job (STOP 2). Disclosed in the T1 report.
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

**Release** is staged under PRE-STAGE A (a code lock for both sources) and REL-SCOPE A, with one author row per stage
(the preregistration's §8 ids). The release step writes receipted partitions (the train/dev label block; then the
test label block and every evaluation block), and every T1 label reader (the table assembly, the C3 training
pipeline, the gate run, any Track P loader) opens only receipted partitions of a stage whose row exists; this is a P5
code requirement with a test. Before the test row, readers get the train/dev label block only and no evaluation value
of any instance.
1. **R1-T1-LABELS-UNSEAL** (the T1 train/dev row) cites the preregistration's sha256 (`aa1a961b…`), the gate v3.1
   sha256 (`a3f7d002…`, R1-BX-D8-CONFIRM-V31), the instance-split file's sha256 (`b5967dd7…`), and, per PRE-DELTA A
   as amended by REL-T1-G1B, the path and sha256 of each node's G.1b summary copy (the REL-T1-G1B step, §3), before
   any training. It releases the **train and dev label blocks** of the nodes it names to the C3 training pipeline:
   arms are trained on train and selected on dev. Track P reads them only if the author says so in a row.
2. The **arms-frozen record** (preregistration §4 step 4) is committed: arms, the T0 and T1 node sets (PRE-T1 A;
   autoresearch per §2.11 and STOP 14), and the split-file, noise-source, G.1b summary, gate and gate-input builder
   sha256s.
3. **R1-T1-LABELS-TEST-RELEASE** cites the preregistration's sha256 and the arms-frozen record's sha256. It releases
   the **test label blocks and every evaluation block** (both sources, PRE-STAGE A) to the gate run (§4 step 5).
4. The sealed task test metric is never released.

Partial T1 at B.7 follows R1-BX-D8-CONFIRM-V31: the gate is read on T0 plus the labelled T1 nodes of the arms-frozen
record, with the count disclosed.

**Leave-one-suite-out.** The seven nodes are in two suites (MLAgentBench, MLGym). Under R1-BX-D8-CONFIRM-V31 and
PRE-SECONDARY A, the descriptive leave-one-suite-out analysis STOPs unless `autoresearch_fixedtokens` (the only
third-suite T1 node) has labelled T1 instances; the aggregate gate does not STOP on it. Under PRE-T1 A this is decided
in the arms-frozen record, the only read; G5-AR A (§2.11) and STOP 14 keep autoresearch in it unless an author row
says otherwise.

**Breakout.** `mlgym_breakout_minatar`'s evaluation keys are public constants (port report §6.2). The labels use the
validation return only, inside the isolated worker, and the sealed test return is never read; disclosed in the
appendix.

## 7. Prerequisites (each PASS in the final note)

- **P1** — R1-T1-HOST-TASL: the harness-isolation host checks pass on TASL-2 (and on TASL-7 if G.1b ran workers
  there), recorded with their sha256.
  - Done for TASL-2 at `c025f89a`: `reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_BINDING_20261121.md`, sha256
    `681011b2…`, as cited by the signed G.4 note. Under G5-AR A the check is also needed at `2d09f9a9` (the third
    note's TASL-2 host check).
  - The TASL-2 host check at `2d09f9a9` (third note) STOPped on 22 Nov (Python 3.12.16 against the frozen 3.12.15);
    it must pass, after whatever resolves that STOP, before autoresearch's G.1b and its G.5 jobs (PENDING at
    signature under G5-ARPEND A, §2.13).
  - Host-check item 7 (CUDA IPC; `reports/HARNESS_ISOLATION_20261117.md` §3) is untested on TASL-2 (review condition
    C1). The G.4 note's P1 accepts the residual risk for the pilot only. The risk is that an edit uses CUDA IPC within
    its own worker; no frozen parent exports a CUDA tensor, and `2d09f9a9` documents that no node uses
    `cuda_share`/`cuda_open`. G.5's labels are EVIDENCE, so P1 needs either **C12** (item 7 tested on TASL-2, its
    record and sha256 in the `cuda_ipc` line) or the **acceptance line** of §5, signed in the note.
    *(Recommendation: C12, if it can run on TASL-2 before the G.5 table starts; the acceptance line otherwise.)*
- **P2** — G.1b complete on the TASL pair: D21 verdicts per node, the summary assembled from the sealed node
  directories of both hosts. For the seven nodes: the three sealed TASL-2 nodes of the first note, `mlgym_fmnist`
  under the amendment note, and the three TASL-7 nodes under note 2 after the re-issued cross-host check
  (`g1b-tasl-20261121-b-xc2`) passed, all in run `g1b-tasl-20261121-b`, assembled under decision G1B-JOIN (its author
  row R1-G1B-JOIN is needed; the launch chain report §4). For autoresearch, its G.1b under the third note
  (`g1b-ar-tasl-20261122-a`), required only for autoresearch's jobs (PENDING at signature under G5-ARPEND A). Each
  summary copied out by the REL-T1-G1B step with its sha256 (§3).
- **P3** — G.4 pilot run and read **with the W, memory mode and temperature the author decides here** (otherwise it is
  re-run or amended first): liveness, invalid, refusal and per-proposal divergence shares per node; the
  cross-instance duplicate rate; the R1-BX-D14 dates recomputed (`g4_lib.recompute_dates`, which models this table)
  and reported (`g4_tasl.py dates`, one slot).
  - The signed pilot (`authorizations/g4_t1_tasl_20261122.md`) runs W = 20 manager calls, `history` and 0.2, which
    are the recommended options of G5-W, G5-MEM and G5-TEMP. Under those it needs no re-run.
  - It measures no autoresearch-suite node (G4-NODE3 A). Under G5-AR A, autoresearch enters the recompute from its
    TASL-2 census time, without the 4090/census ratio (§8).
- **P4** — K = 10 (R1-G5-DECISIONS), unless a published K-check PASS author row exists before the first audit chunk,
  in which case the coordinating chat amends the note's `audit_K` and seed lines to K = 6 first (a docs-only
  amendment of the note citing that row; the spec carries both seed blocks and does not change; the switch reads
  `audit_K` from the note; no further author decision, since R1-G5-DECISIONS admits K = 6 on that row); if the
  check fails, K stays 10 and the
  coordinating agent STOPs for the author (R1-BX-D3). K is uniform within the T1 table.
- **P5** — G.5 job code (spec, campaigns in waves, audit runner, diagnostics, release locks, switch) independently
  reviewed at the launch commit. Its harness commit descends from the G.1b pin, and the measurement path is
  byte-identical between the two commits, so the noise floor and the labels share it. There are two G.1b pins,
  `c025f89a` for the seven nodes and `2d09f9a9` for autoresearch; the check runs per family (G5-7 against `c025f89a`,
  G5-AR against `2d09f9a9`), and `g5_pin_check.py` passes on the pair (G5-PIN B). The path is all of
  `src/autoresearch/trackg/` except the v2-diff engine files the labels may change (`manager_v2_diff.py`,
  `campaign_v2_diff.py`, `proposal_v2_diff.py`, `pilot_g4.py`), plus `nodes/`, `third_party/`, `configs/trackg/`,
  `node_lib/`, and every module outside `trackg/` in the import closure of `noise_floor` (the validator computes the
  closure and runs `git diff --quiet <g1b pin> <g5 pin> -- <paths>` over the files present at the G.1b pin). New
  files that G.5 adds — the audit runner and the diagnostics writer, *(proposed)* `trackg/audit_g5.py` and
  `trackg/diagnostics_g5.py` — are allowed if they are outside the import closure of `noise_floor` (the validator
  checks that none of the measurement-path modules imports them). A change such as the R1-TRACKG-AR-COND7
  `ar_isolated.cuda_open` fix therefore fails the check. That fix is in `2d09f9a9`, autoresearch's G.1b pin, and it
  fails the check against `c025f89a`; this is why G5-PIN arose (decided B).
- **P6** — author decisions recorded: the open ones of §11. Already recorded on `main`: G5-AR A and G5-PIN B, with
  the cap raised and K = 10 (R1-G5-DECISIONS); R1-G1B-EDITS and R1-G1B-TIMEOUT; G5-SPLIT through R1-SWEEP2-PREREG
  (PRE-SPLIT A and the split file).
- **P7** — the §8 projection, recomputed from the pilot medians, is within the cap.
- **P8** — the imdb baseline frozen and independently reviewed (R1-TRACKG-PORT-DECISIONS (3)); the review cited.
- **P9** — the host/environment row R1-T1-TASL-ENV (in place of the image row; G.1b, G.4 and G.5 use it), on `main`.
  For autoresearch, R1-G1B-AR-ENV admits `ar-cond7a` for its G.1b; this note extends the same environment, with the
  same freeze check at every job, to autoresearch's G.5 jobs, so that its noise floor and labels share it (§11). If the
  resolution of the 22 Nov AR host-check STOP changes the environment, the G.5 note follows that row. Autoresearch's
  part may be PENDING at signature under G5-ARPEND A.
- **P10** — per node, the Gaussian or Student-t declaration from the G.1b summary, recorded before any label is
  assembled (E5); autoresearch's in the completion record under G5-ARPEND A.
- **P11** — host tests C1–C13 below PASS, in particular C3 (run time on the TASL-2 4090 against the timeout basis)
  and C10 (the proposer link over Tailscale). C12 can be replaced by the author's acceptance (P1); C13 applies only
  under G5-PIN B.

## 8. Projection (pre-pilot; recomputed from the pilot before signature)

One formula serves this note and the G.4 recompute: `g4_lib.g5_node` (`sweep2/t1_tasl/g5_projection_tasl.py` prints
§2.8 with the TASL params; the `sweep2/g4` version uses the H200 params).
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

**Autoresearch** (G5-AR). The eight-node figures in §2.11 come from `sweep2/t1_tasl/g5_ar_projection_tasl.py`. It
uses the same `g4_lib.g5_node` and the TASL date wrapper `g4_tasl.recompute_dates` (one worker slot; no requested
slot-hours), with autoresearch's census B1 time on TASL-2's 4090 (218.951 s); its K = 6 rows are marked
`hypothetical_k_check`. Before the pilot the ratio is 1.0, so the figures are consistent. After the pilot, `recompute_dates`
would multiply every non-pilot node's census time by the measured 4090/census ratio, autoresearch's included, which
is wrong for a node censused on the 4090. The G.5 recompute must exempt such nodes (§9), and until it does, the
eight-node P7 number is computed with autoresearch's time unscaled. Under G5-AR B (not chosen), autoresearch would need its own 4090
noise floor, its own projection and an amendment of this note (not chosen, §2.11).

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
- The measurement-path identity check between the G.1b and G.5 harness pins, per family (G5-7 against `c025f89a`,
  G5-AR against `2d09f9a9`). The identity of the G.5 code between the two families' commits is built in this
  revision (`sweep2/t1_tasl/g5_pin_check.py`, with tests on synthetic repositories and on the real pins); the switch
  calls it at every job start (STOP 13).
- The switch with the key values of §5 and the TASL launch binding (`verify_launch_tasl`, LB A of
  R1-G1B-TASL-DECISIONS, as G4-LB A applied it to G.4). Revision 6 named the S2-C5 binding, which can never pass for a
  note on `main` that names its launch commit (READY 75).
- Autoresearch's spec entry (its harness family; under G5-ARPEND B its environment and G.1b summary copy, under A a
  PENDING marker for both and the P10 declaration, which the switch takes from the completion record, STOP 15); the
  spec's two seed blocks and the switch reading `audit_K` from the note (P4); and the date
  recompute exempting nodes censused on the 4090 from the 4090/census ratio (a params list, with a test). With it,
  `autoresearch_fixedtokens` leaves `pilot_nodes` in `sweep2/t1_tasl/g4_tasl_dates_params.json` (stale against
  G4-NODE3 A: `recompute_dates` would accept an autoresearch "pilot" summary as measured; harmless before the pilot).
- The REL-T1-G1B copy step for the two G.1b summaries (or its use, if the release-step unit provides it), the freeze
  wait (STOP 14), and, under G5-ARPEND A, the switch's check of autoresearch's completion record (STOP 15).

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
- **C11.** TASL-7's lease: the server holds it for the table's span; G.1b on TASL-7 (second note) finished before.
- **C12.** Host-check item 7 (CUDA IPC) on TASL-2, in place of the acceptance line in P1 (§5).
- **C13.** G5-PIN B: the two harness checkouts on TASL-2, each node launched from its own family's checkout,
  `g5_pin_check.py` passing on the two G.5 commits, and a node at the other family's checkout refused (§4 item 13).

## 11. What the author still signs

Recorded already (no further decision): G5-AR A and G5-PIN B, the cap raised to the projection, K = 10 until a
K-check row, B.7 about 15 Dec (R1-G5-DECISIONS); G5-SPLIT (PRE-SPLIT A); the timeout basis (R1-G1B-TIMEOUT).

**Decisions in this draft** (each with options and a recommendation in §2 or §4):
1. **G5-W** — A: 20 manager calls (recommended) | B: 20 worker runs with an 80-call cap.
2. **G5-TEMP** — A: 0.2 with the engine's seed rule (recommended) | B: 0.
3. **G5-MEM** — A: `history` only, 12 instances (recommended), **with the row amending E4's "both memory modes"** | B
   | C.
4. **G5-AUDIT** — A (recommended): the audit-once rule for cross-instance groups, `reuse_parent_runs: true` (subject
   to C2), E5 on the label seeds only | B.
5. **G5-DIV** — A: 20 % on audited proposals from 40, the literal "2 × census" kept (recommended) | B | C.
6. **G5-TASL-GPUH** — A: the worker card counts (recommended; the 425 cap assumes it) | B: both cards (within 425
   only at share 0.6 with the server stopped during audits; above it otherwise).
7. **G5-SLOT** — A: one slot on TASL-2 (recommended) | B: audits on TASL-7 (not built).
8. **G5-ARPEND** — A: autoresearch's own prerequisites PENDING at signature, completed by a reviewed record the
   coordinating chat commits without a further author decision; the spec carries PENDING markers and the switch reads
   the record (no spec or note change) (recommended) | B: the signature waits for them (§2.13).

**Values the signature fixes** (*(proposed)* in the draft):
9. The cap, 425 GPU-h of the worker card (§2.6), or the cap of another row of §2.8/§2.11 if a decision above departs
   from the recommended row.
10. The liveness floor 0.25 (STOP 3), the invalid-share STOP 0.2 (STOP 4), the infrastructure STOP 5 % (STOP 7), and
   the audited band 100–200 per node under W A (150–240 under B; doubled under MEM B) (STOP 9).
11. The freeze wait over every un-STOPped node and its release date, *(proposed)* 18 Dec 2026, recomputed with P7
    (§2.11, STOP 14).
12. The instance seed block 5101–5112 (§5).
13. The seal: procedural (receipts and access log) or the encryption alternative (§6, C6).
14. Autoresearch's G.5 environment: `ar-cond7a` under R1-G1B-AR-ENV, extended to G.5 by this note (P9), or as the
    resolution of the AR host-check STOP decides.
15. CUDA IPC: C12 passed (the `cuda_ipc` line cites it) **or** the acceptance line of §5, signed verbatim.
16. The K amendment: after a published K-check PASS row, the coordinating chat amends the note's `audit_K` and seed
    lines to K = 6 without a further author decision; the spec carries both seed blocks and is not re-issued, and the
    switch reads `audit_K` from the note (P4).

**Rows and records needed before the signature:** R1-G1B-JOIN (decision G1B-JOIN, for the seven-node summary, P2);
the seven-node REL-T1-G1B copy; under G5-ARPEND B also the resolution of the AR host-check STOP, the third note's G.1b
and autoresearch's copy (P1, P2, P9, P10). Optional: a K-check row (P4; K = 6 by amendment, item 16).

**After the signature, while the table runs:** under G5-ARPEND A, the completion record for autoresearch (§2.13), which
the coordinating chat commits after its review (the switch reads it; no amendment); the K amendment if a K-check row
appears; the freeze wait's author row if STOP 14 fires on a node STOP.

**After the table:** the T1 release rows R1-T1-LABELS-UNSEAL (train/dev) and, after the arms-frozen record,
R1-T1-LABELS-TEST-RELEASE (test labels and every evaluation block) (§6); the freeze wait's author row if STOP 14
fires on the release deadline.

**The signature itself:** `approved: true` on the final note at `docs/r1/authorizations/c3_t1_labels_<YYYYMMDD>.md`,
with every `<…>` field of §5 filled from the post-pilot recompute (P7), the reviewed G.5 code unit (P5), the two G.5
harness commits and the seven-node REL-T1-G1B copy, and P1–P11 recorded as PASS (autoresearch's items PENDING under
G5-ARPEND A).
