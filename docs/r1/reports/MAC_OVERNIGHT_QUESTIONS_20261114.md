# Mac overnight 13/14 Nov 2026 — questions for the author

AI-assisted (Claude, Mac-local agent). One section per question, with options, a recommendation and, where an answer is needed, a paste-ready line. Sections marked NOTES or observation need no separate answer. Report: `reports/MAC_OVERNIGHT_REPORT_20261114.md`.

## D8-Q4 — minimum test instances per node (Unit 1)
The plans rule out 10 test instances per node: T1 sweep 2 plans about 12 campaigns per T1 node (TRACK_G_RUNBOOK G.5; RUNBOOK l. 235), so at most about 12 instances and likely about 6; T0 has 18. Per the answer, the STOP was not implemented.
Options: (a) no minimum (current); (b) STOP below 10 only after the plans are changed (more T1 instances); (c) a per-tier minimum the plans allow (e.g. T0 ≥ 6, T1 ≥ 2), stated with the split proportions; (d) fix the train/dev/test proportions first, then decide.
Recommendation: (d) then (a) or (c). Note: with 2–6 dev instances the dev-z rule excludes nodes nearly at random (simulation §3), so the split proportions matter for Q2 as well.
Paste-ready: `D8 Q4：计划实例数达不到每节点 10 个 test；先固定 train/dev/test 比例，暂不加 STOP。`

## D8-Q3b — harness Python version
Harness `.python-version` at a3fedbb says 3.11; the answer and the cluster runbook say Python 3.13. The gate checks only NumPy.
Recommendation: record both; no check. Paste-ready: `D8：门槛环境以 uv.lock（NumPy 2.4.4）为准，Python 3.13；.python-version 的 3.11 不作约束。`

## D8-ROW — should the confirmation row name the dev-z rule? (Unit 1)
The row text binds the gate by SHA; it does not mention dev z ≥ 6 or the missing test minimum. Options: (a) keep the row as drafted (the SHA binds the code); (b) add one sentence ("IQM eligibility also requires dev z ≥ 6.") — this needs a parser change and a redraft. Recommendation: (a). Paste-ready: `D8：确认行不另写 dev z 规则，由 SHA 绑定。`

## D8 observation (needed before confirming, no separate answer)
At split sizes the plans allow (2–6 dev instances), dev z ≥ 6 passes or fails nearly at random: about half the nodes are excluded almost regardless of signal; P(STOP) for 10 nodes at 5 test SE falls from about 0.41 to 0.2 mainly through that exclusion; a node with one dev instance is always ineligible, so under block splits the T1 tier could drop out of the IQM; left-skewed differences are not protected. Report M11_D8_GATE_V2_20261114.md §3.

## HTC-Q1 — do HTCondor walltime holds count toward the repeated-timeout cap? (Units 2/3)
The adapter maps a walltime hold to `infrastructure_failure/htcondor_walltime_hold`; the cap counts only the runner's own `timeout`. The adapter refuses Track G manifests whose walltime does not exceed runs_per_job × runner timeout + 600 s, so a walltime hold should only occur if the runner itself hangs or setup overruns the margin.
Options: (a) do not count (current); (b) count walltime holds as timeouts; (c) count a walltime hold as a timeout only for a one-run job whose runner timeout was below the walltime.
Recommendation: (a). Paste-ready: `HTCondor：walltime hold 不计入 timeout_repeated 上限，单独记 infrastructure_failure。`

## HTC-Q2 — disk holds (Unit 2)
An HTCondor disk hold (code 34 subcode 104) is not in the author's list of infrastructure failures (eviction, preemption, memory or walltime hold, image pull). The adapter returns `unclassified` (a human decides).
Options: (a) keep `unclassified`; (b) treat as `infrastructure_failure/htcondor_disk_hold`. Recommendation: (b), consistent with memory holds (both can be caused by the request being too small or by the proposal, e.g. frequent checkpoints; the author already put memory under infrastructure). Paste-ready: `HTCondor：磁盘 hold（34/104）也记 infrastructure_failure。`

## D8-NOTES (Unit 1 round-2, not blocking; not fixed so the reviewed base 80d70832 stays)
- Draft item 4 "P(STOP) about 0.2": true for normal differences with 6 test instances; left-skewed stays 0.52–0.63. Reword when confirming?
- Draft item 15: "no node" → "no T1 node" can reach 10 test instances.
- Report reproduction tables: 4 rows keep the old "spread evenly" label.

## B2-NOTES (Unit 5, not armed draft; round-2 notes, not blocking)
- Before arming: pick one order at B2 start (marker first, so Track P / Track S watcher pause on it, vs Track S paused first).
- Confirm intended: at 7912b7ff the b2 job uses seeds 9201–9210 for every per-proposal audit too (2×10 vs B1's 2×4 per proposal; counts in GPU-h tie-break).
- B2 power-plan rule is undeclared; B1 analysis gives only pooled increment_sd per candidate.
- Extend R1-EXAM-B1-TRUNCATION-INVALID / -MODEL-OUTPUT-INVALID to B2? (author row needed)

## W2-1 — trial budget in the prompt (W2 stop-rule report item 2)
The campaign stops after 20 worker runs; the 40-trial cap is a backstop. On rebuilt sweep-1 ledgers the prompt line "trial b of 20" would exceed 20 on the 14 campaigns with precheck rejections.
Options: (a) set `trial_budget = 40` for every sweep-1 campaign (honest; changes every prompt's budget line); (b) keep "of 20". Recommendation: (a), with the PROMPT_VERSION bump (W2-2).
Paste-ready: `W2：sweep-1 的 trial_budget 设为 40（选项 a），与 W2 v3 重建一起。`

## W2-2 — PROMPT_VERSION
Your Q7 answer keeps `trackp_prompt/v1` until the first Track P data with skips. A precheck rejection is not a skip (it is an invalid trial), but its prompt effect is the same and W2-1 (a) changes every prompt. Recommendation: bump to `trackp_prompt/v2` with the v3 rebuild.
Paste-ready: `W2：随 v3 重建把 PROMPT_VERSION 升到 trackp_prompt/v2。`

## W2-3 — precondition (no answer needed, a check)
The recommendation assumes every sweep-1 ledger has `worker_runs_total == 20`; this can be read from the existing W2 check summary (cluster agent), no new data access. If any ledger has fewer (a campaign that hit the 40-trial cap), the report's recommendation needs revisiting.

## TP-1 — Track P leak-guard gap on mac-int (Unit 4 finding; pre-existing)
`EVAL_COLUMNS` in `r1/c3/train/run.py` l. 37 does not match evaluation aliases (`delta_true`, `se_audit`, `delta_audit_all`, `candidate_metrics`, `incumbent_metrics`, nested); 8 TrackPStop guard tests fail on mac-int. The integration trial shows that merging `mac-m3-20261109` makes those 8 tests pass (M3 carries the guard change). Recommendation: integrate M3 (after IT-2) before any Track P run reads real tables.

## IT-1 — integration conflict M3 × mac-int guards (Unit 7)
After merging M3 into mac-int, `test_c3_audit_dryrun.py::test_dryrun_on_the_frozen_corpus_partitions_the_whole_population` fails, and M3's dry-run tool STOPs: mac-int's guard exempts frozen sweep-1 tables only when `build.json` records `sweep_index.path`, and M3's `c3_audit_dryrun.build_table` records only the SHA, so the guard asks for the D8 confirmation. Options: (a) record `sweep_index.path` in `build_table` (no guard change, no author row); (b) leave it failing until R1-BX-D8-CONFIRM is committed. Recommendation: (a), in the real integration.
Paste-ready: `集成：M3 的 c3_audit_dryrun 在 build.json 里记录 sweep_index.path（选项 a）。`

## IT-2 — the five held `9bab3d6f` diffs (Q24, R1-B2-REPAIR-SCOPE-ACK)
Merging M3 as a whole brings in the five held diffs (`r1/c3/train/run.py`, `trainer.py`, `env.py`, `control.py`, `prior_model.py`). The 4 Nov row takes them into M3's scope "and reviewed with it" and keeps them unmerged until then. **No accepted review covers them:** the accepted 9 Nov M3 review does not mention them, the 4 Nov M3 review says it is not acceptance of them, and the 28 Oct review of `9bab3d6f` says BLOCK for B.2 launch. Several base test failures, including the Track P leak-guard tests (TP-1), are fixed only with them. Options: (A) commission an independent review of the five exact diffs at `ec6e30a9`, then decide; (B) split M3 and merge it without them; (C) keep deferring. Recommendation: (A).
Paste-ready: `Q24：先对 ec6e30a9 中 9bab3d6f 的五个文件改动做独立审查，审查后我再决定。`

## DTQ-1 — the replay prompt file and the projection inputs (Unit 8.2; operator)
The DTQ tool takes 50 sweep-shaped prompts (`prompt`, `seed`, `source`, `ledger_sha256`, `trial_id`) drawn from sweep-1 contexts; it checks them against the exam's frozen prompt sets (text and source ledger) but does not build them, and it needs the projection inputs (LLM calls per campaign, worker runs per campaign, CPU seconds per run, workers). Who builds the prompt file on deepthought, and which values are used? Without the CPU-term values the 4-day criterion stays unevaluated.
Paste-ready: `DTQ：50 条重放提示由 cluster agent 从 sweep-1 ledger 只读抽取；投影参数用 sweep-1 实测值。`

## DTQ-2 — "instance" disjointness
The tool treats "disjoint from the exam's instances" as "no replay prompt from a ledger an exam prompt came from" (`ledger_sha256`). If you mean more (e.g. node and seed against the exam namespace 9001–9004), say so. Recommendation: the ledger rule (sweep-1 seeds never overlap the exam namespace).
