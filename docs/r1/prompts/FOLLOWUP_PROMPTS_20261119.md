# Follow-up prompts for the three agents (19 November 2026)

Written by the coordinating chat (Claude, AI-assisted) at the author's request. Paste each block into the agent named. The startup prompts of 18 November (`CLUSTER_AGENT_PROMPT_20261118.md`, `EXPERIMENT_AGENT_PROMPT_20261118.md`) stay in force for rules and working style; PLAN §10 on published `main` wins over both.

## Cluster agent

```
Published main now carries R1-SWEEP2-INTEGRATE (19 Nov, after de3de54f); fetch it. New rows: R1-SWEEP2-INTEGRATE and R1-TRACKG-AR-COND7; the B.2 audit report and review (ops-b2-audit-20261119) are on main, so the B.2 sequencing gate of R1-SWEEP2-SETTINGS (3) is met and the PLAN freeze for B.2 is over.

Keep exactly one cluster session. Base all sweep-2 work on int-sweep2-20261118 @ efc55ed8 (H200-only measured placement, R1-SWEEP2-MEASURED-GPU), not on the older wrapper d9ff7813.

Continue autonomously, in this order:
1. Integration (R1-SWEEP2-INTEGRATE): merge s2c5-switch-20261116 @ ee2c2b5d into int-sweep2-20261118, resolve the conflicts so that the result has both the H200-only placement and the H200 S2-C5 layout (8735 / 42460970 / 32000 / 16 / 25.88), run the full test suite (no new failures against main's baseline) and the scheduler dry runs, get a fresh independent review, push int-sweep2-20261118, and send the author one short Chinese message with the branch tip. The coordinating chat merges it into main.
2. Note: once the integration is on published main, update docs/r1/authorizations/c3_sweep2_20261119.md on sweep2-auth-20261119 (merge main into that branch first): P2 and P6 PASS citing the integration commit and its review, P3 PASS citing R1-SWEEP2-AUTH, render from the integrated code on main, approved: true only within the R1-SWEEP2-AUTH bounds; fresh independent review; push; send the author the branch tip. The coordinating chat publishes it.
3. Launch: with the note on published main, launch commit = main HEAD; rerun S2-C3b liveness at exactly that commit (8/8), launch sweep 2 on H200, monitor all 16 chunks under the declared gates and STOPs, collect, seal, and write the sweep-2 report (counts, gates, GPU models, S2-C3 results incl. the L40S descriptive run if it ran, engineering runs that reused sweep-2 seeds). Labels stay sealed.
4. In parallel: image v2 I2 (CPU determinism), then the Track P H200 smoke and E0 (trackp-h200-20261118), per R1-QTORCH-AMEND and R1-TRACKP-I3-H200.
5. When NEMO2 L40S slots appear: the 2-instance L40S timing smoke (R1-SWEEP2-MEASURED-GPU) and the descriptive L40S S2-C3 (R1-S2C3-ACCEPT).
Report to the author in Chinese at the end, or when everything left is blocked.
```

## Experiment agent

```
Published main now carries R1-SWEEP2-INTEGRATE (19 Nov, after de3de54f); fetch it. New rows: R1-TRACKG-AR-COND7 (autoresearch: option A) and R1-SWEEP2-INTEGRATE; the B.2 audit report is on main. Merge main into ops-tasl-20261116 and continue autonomously:
1. autoresearch condition 7, option A (R1-TRACKG-AR-COND7): one reviewed harness/kit change that removes CUDA IPC from the result path (the worker hands logits or answers to the frozen parent through the existing socket/CPU buffer; the parent alone computes the metric) and adds torch.cuda.init() to ar_isolated.cuda_open; keep effective:true, waivers {}, and drop the shared_dev_shm exception if it is no longer needed. Fresh independent review; update the kit pins and frozen_pin_sha256; push the harness branches; exactly one isolated autoresearch smoke on Ada; then the autoresearch U2 unit, result and review. Record the slowdown of the logits transfer.
2. mlgym_houseprice: the author is placing Kaggle's train.csv at ~/r1_inputs/house-prices/train.csv on Ada. When it appears: record sha256 and md5, then unit → independent review → one smoke → result review, with --from-file (R1-TRACKG-PORT-DECISIONS (2)). Until then it is a per-node block.
3. U4: the census report with per-suite funnels (all nodes that passed, with the blocked ones listed), independently reviewed.
4. Track P: P.3a is complete (Unit B accepted). Do not start P.4 until an author authorization for it is on main. Keep TASL-7 and TASL-2 idle and the attempt-1 archive in both places.
Report to the author in Chinese at the end, or when everything left is blocked.
```

## Mac agent (desk only)

```
You are the Mac agent for Paper B, route R1 (repo dowlingwong/Agent_paper_B). Desk only: code, drafts, simulations, reviews on the Mac; no SSH; deliver git bundles plus an append-only entry in ~/Documents/agent_paper_B/Claude outputs/READY.txt (follow docs/r1/prompts/MAC_LOCAL_RUNBOOK_20261104.md §0). Every unit gets a fresh independent reviewer subagent; files in English; never push main, never force-push, never delete (use _to_delete/); PLAN §10 on published main (fetch it fresh) wins. Work autonomously; fix small problems yourself; stop only at declared STOPs or choices that change declared scientific content (write those up as author decisions with a recommendation).

State: sweep-1 B.2 audit PASS (docs/r1/reports/b2_audit_20261119/, review B2_AUDIT_RUN_REVIEW_20261119.md with 4 non-blocking minors); Track P P.3a complete (Unit B accepted, branch ops-tasl-20261116, TRACKP_UNITB_TASL7_D2_RESULT_20261119.md); SFT pipeline + heldout_excludes_seen on main, ENGINEERING trial passed on TASL-2; harness isolation and isolated Track G kits on main (READY 60/61), six census nodes passed; sweep 2 about to launch on H200.

Units, in order:
1. Sweep-1 label freeze record: freeze the B.2 label and evaluation blocks (hashes, counts, provenance), and carry the review's 4 minors as errata. Draft only for what needs author signature.
2. P.4 SFT authorization draft (Track P, the gate to SFT and later RL): data = sweep-1 B.2 labels now, sweep-2 labels when unsealed under R1-BX-D8-CONFIRM; policy heldout_excludes_seen; a P.4 test evaluator that applies the exclusion list for the primary test number (READY 59 open point) — implement and test it; model/host/budget options (TASL-7/TASL-2 4090 vs NEMO2 H200 with image v2) with a recommendation; STOPs; evidence labels. Deliver the draft plus the evaluator code.
3. Multi-step RL design + code skeleton (after SFT): environment = the governed loop on the isolated runner; reward definition in which the infrastructure-log-pattern class is not neutral (READY 60 open point); worker sees training-split data only (READY 61 open point: labels unreadable by the worker, implement the training-split-only worker layout); budget enforcement against adversarial edits; CPU-only tests with tiny models.
4. Census and T1 drivers enforce the unisolated-run gate (READY 60 "later unit").
5. Sweep-2 analysis preregistration (split P3, gate v3, floors) so analysis can start the day the labels unlock.
6. Manuscript skeleton: methods and theory sections (T4 approved with errata, R1-T4-PROOF-CHECK).
```
