# Prompts, 20 November 2026 (evening)

Written by the coordinating chat (Claude, AI-assisted). Paste each block into the agent named. Earlier startup prompts stay in force for rules and working style; PLAN §10 on published `main` wins.

## 1. Cluster agent — last two note fixes (paste now)

```
sweep2-auth-20261119 @ b4286a2d is almost ready. The coordinating chat checked the code on main and found two prose statements that are still false; fix them before publication (prose only, key block unchanged):
1. Collection gates (note ~lines 75–78) and the STOP list (~lines 108–110): for EVIDENCE runs the per-chunk, per-(node, memory mode) worker-failure check is deferred (sweep2/s2_c2_lib.py: `worker["failure_rate_gate"] = "deferred to pooled sweep-2 collection"`, ~line 789); the only worker-failure STOP is the overall pooled gate at collection: total worker failures / total trials > pooled sweep-1 failure rate + 5 pp (~lines 1128–1149), as R1-SWEEP2-LAYOUT-AMEND says. The per-(node, mode) rule with the 1 % exact-binomial control applies only to non-EVIDENCE (pilot/engineering) chunks. Rewrite both places to say exactly this, and delete "the current implementation is per-(node, mode)" and the sentence that calls per-cell vs overall an open author decision.
2. Requirements paragraph (~line 46): replace "No site/GPU-model pin beyond that." with: EVIDENCE JDLs additionally pin `GPUs_DeviceName =?= "NVIDIA H200"` (R1-SWEEP2-MEASURED-GPU); no site pin.
Then rerun parse_note and resolve_label on the note, record the new note sha256, have your reviewer confirm these two edits (a short round-3 section in SWEEP2_AUTH_LAUNCH_REVIEW_20261120.md is enough), push, and send the author the new tip. The launch specs are rendered at the launch commit pinning the published note's sha, so the dry-run report may keep its recorded sha with one sentence saying the note was edited afterwards (prose only, key block unchanged). After publication: C3b at that exact main HEAD 8/8, then launch, as you planned.
After the launch, as a separate ENGINEERING job (R1-T1-HOST-H200): run the harness-isolation host checks from docs/r1/reports/HARNESS_ISOLATION_20261117.md §3 inside the v2 image container on one NEMO2 H200 (unprivileged user namespaces, delegated cgroup v2 subtree, non-root, pivot_root, a sandboxed smoke with effective:true, a GPU smoke with the sandbox on). Report PASS/FAIL per condition; if any fails, say exactly why, because then the whole T1 table moves to Ada.
```

## 2. Experiment agent — restart (paste now; it has been idle since 19 Nov 06:31)

```
Fetch published main and merge it into ops-tasl-20261116. New rows: R1-TRACKG-AR-COND7 (option A), R1-T1-HOST-H200, R1-TRACKG-G3-EARLY (once they are on main; if not yet, start anyway — option A was signed on 19 Nov). Work autonomously, highest priority first:
1. autoresearch condition 7, option A: one reviewed harness/kit change that removes CUDA IPC from the result path (logits or answers go from the worker to the frozen parent through the existing socket/CPU buffer; only the parent computes the metric) and adds torch.cuda.init() to ar_isolated.cuda_open; effective:true, waivers {}; drop the shared_dev_shm exception if no longer needed. Fresh independent review; update kit pins and frozen_pin_sha256; push the harness branch; one isolated smoke on Ada; then the autoresearch U2 unit and its result review. Measure and record the slowdown. Target: done within 24 h; this node is the only autoresearch-suite T1 node and B.7's leave-one-suite-out needs it.
2. mlgym_houseprice once ~/r1_inputs/house-prices/train.csv exists on Ada (sha256 + md5, --from-file, unit → review → smoke → result review).
3. U4 census report (all passed nodes, blocked ones listed), independently reviewed; it no longer blocks G.1b/G.4 (R1-TRACKG-G3-EARLY).
Report to the author in Chinese when done or blocked.
```

## 3. Mac agent — T1 job code (paste now)

```
New rows (R1-T1-HOST-H200, R1-TRACKG-G3-EARLY): G.1b noise floors, the G.4 pilot and the G.5 T1 label runs go to NEMO2 H200 via HTCondor, on the six passed census nodes now (mlab_cifar10, mlab_imdb, mlab_ogbn_arxiv, mlgym_cifar10, mlgym_fmnist, mlgym_breakout_minatar), autoresearch and houseprice later. Build, as independently reviewed units, in this order (this now comes before the other desk items):
1. G.1b HTCondor job: D21 protocol, 552 runs per node, on the isolated kits (harness branches mac-trackg-iso-{mlab,mlgym,ar}-20261117 plus the experiment agent's later pins), the v2 image by digest, one chunk per node (or per node × seed block), walltime from the census per-run times × 1.5 plus startup, fixed step budgets (R1-BX-D5), sealed outputs, the unisolated-run gate (refuse any run whose record is not effective:true with empty waivers). Projection: about 32 GPU-h for the six nodes; STOP above the R1-G1B-CAP 100 GPU-h. Reuse sweep2/ patterns (spec, render_jdl, wrapper, S2-C5-style two-key switch) and r1-local-trackg-htc-20261114.
2. G.4 pilot job (3 nodes: mlab_cifar10, mlgym_fmnist, autoresearch or mlgym_breakout_minatar): sweep-2-shaped, main proposer gemma4_31b thinking off, cache_prompt false, manager_proposal/v2-diff, measures throughput, diff liveness, duplicate/inert/divergence rates, prompt lengths; then recompute the R1-BX-D14 dates.
3. G.5 authorization draft for the T1 label runs (K, seeds, W = 20, ~150 audited proposals per node, STOPs incl. divergence > 2 × census, sealing until R1-BX-D8-CONFIRM analysis), approved: false, for the author to sign.
Deliver bundles + READY entries as usual; flag anything that needs the cluster to test (container isolation is being checked by the cluster agent separately).
```
