# Mac overnight 9/10 Nov — questions for the author

**AI-assisted (Claude, Mac-local agent), written 10 Nov 2026.** Each item: context, options, recommendation, and a paste-ready answer line. None of these blocks the B1 restart path; the B1 items at the end are information only.

## Q1 — D8 gate: partial-T1 scope and the layout pins (answer together)

Context: `r1/c3/gate.py` on `mac-m11-d8-20261109` (accepted, SHA-256 `a078cf1f…6acd`). It pins the eight T0 CPU nodes of the sweep-1 authorization (R1-DT-PIN-SWEEP1, with `openml_climate`) and the suites `autoresearch`, `MLAgentBench`, `MLGym` (R1-BX-D2 as amended by R1-1GC-FALLBACK). R1-B7-PARTIAL-T1 ties "≥ 1 labelled T1 node per suite" to leave-one-suite-out; the gate applies it to the whole gate (stricter). 1GC-7RC dataset tasks without a suite currently STOP the gate.

- (a) Keep: whole-gate per-suite STOP; T0 set and suite spellings as pinned; suite-less T1 nodes refused.
- (b) Per-suite rule only for leave-one-suite-out (the confirmation row wording must change).
- (c) Allow suite-less 1GC tasks as T1 (changes both the suite check and the per-suite rule).

Recommendation: (a), unless B.7 risks leaving a suite without a labelled T1 node.
Paste-ready: `D8 Q1+Q2：维持整门按套件的 partial-T1 STOP；T0 八节点（含 openml_climate）与三个套件名按 gate.py 固定；无套件的 1GC 任务不进 T1。`

## Q2 — D8 gate: STOP on a nonpositive resampled denominator

Context: any eligible node whose resampled test denominator is ≤ 0 STOPs the whole gate. Simulated: about 0.52 with 10 eligible nodes at z = 5 test SE, 0.66 with 15; worse with a heavy left tail (report §"Whole-gate STOP probability").

- (a) Keep the STOP. (b) Add an SE-aware dev eligibility rule (e.g. dev denominator ≥ δ_n and dev z ≥ 6). (c) Keep it and report the offending nodes (already done). (d) Exclude such nodes after the fact (not recommended).

Recommendation: (b), implemented and re-reviewed before confirming; otherwise (a)+(c).
Paste-ready: `D8 Q3：采用 (b)，dev 分裂上加 SE 门槛（dev z ≥ 6）作为资格条件，实现并复审后再确认。`

## Q3 — D8 gate: NumPy pin

Context: `NUMPY_VERSION = '2.4.4'` (harness `uv.lock`); any other version STOPs. 2.4.4 and 2.5.3 gave byte-identical gate output in the reviewer's scratch check. The pin must equal the venv that will run the gate.

Recommendation: name that venv and pin its version.
Paste-ready: `D8 Q4：门槛在 <venv 名> 上跑，NumPy 固定为 <版本>。`

## Q4 — D8 gate: minimum test instances per node

(a) None (current). (b) STOP below a predeclared minimum, e.g. 10. Recommendation: (b) if the T1 instance counts allow it.
Paste-ready: `D8 Q5：每节点 test 实例少于 10 时 STOP。`

## Q5 — D8 gate: conventions frozen by confirming

Ratio of means for gap closed, exact-equality ties, fractional-edge IQM (conventions 6–8 of `reports/M11_D8_GATE_20261109.md`). Recommendation: keep.
Paste-ready: `D8 Q6：保留 ratio of means、精确相等记平、分数边界 IQM。`

Any answer to Q1–Q4 that changes `gate.py` changes its SHA: the confirmation draft is then redrafted and the gate re-reviewed before you paste the `R1-BX-D8-CONFIRM` row.

## Q6 — W2: identity on the real sweep-1 ledgers

Context: W2 (`mac-w2-budget-20261109`, accepted) is byte-identical on execute-all campaigns. Whether sweep 1 is truly execute-all was not checked tonight (label seeds). If sweep 1 holds D25 inactive-key skips or precheck rejections, its worker-run count is not b − 1 there and the W2 check STOPs. `r1/scripts/w2_execute_all_identity_check.py` reads only budget index, decision, worker mode and the control record.

- (a) Have the experiment agent run the check read-only on the sweep-1 `root_trials.jsonl*` and report. (b) Skip the check and accept that sweep-1 features may differ on such rows.

Recommendation: (a).
Paste-ready: `W2：由实验 agent 在 sweep 1 的 root_trials 上只读运行 w2_execute_all_identity_check，结果回报；如有差异 STOP 交我决定。`

## Q7 — W2: bump PROMPT_VERSION?

`FEATURIZER_VERSION` is now `c3_features/v3`. `PROMPT_VERSION` stays `trackp_prompt/v1` so execute-all prompts stay byte-identical (the version is in prompt meta); prompts with skips or verify now differ under the same string. Recommendation: keep v1 until the first Track P data with skips is built, then bump.
Paste-ready: `W2：PROMPT_VERSION 暂保持 v1，首次构建含 skip 的 Track P 数据时再升版本。`

## Q8 — M10 port kit: eight design choices

The accepted hand-off `reports/M10_PORTKIT_HANDOFF_20261109.md` §5 lists them with paste-ready lines: non-zero exit counts as divergent (Slurm cgroup OOM as infrastructure, CUDA OOM as divergent); no wall-clock fields; strict determinism by default; docstring-only diffs not inert; unique-context hunk offsets accepted; harness base `a3fedbb`; the same diff on a different incumbent is not a duplicate; cap on repeated timeouts (later). Recommendation: (a) for all.
Paste-ready: `M10 §5 问题 1–8 全部按推荐 (a)。`

## Q9 — M3 design questions

From `reports/MAC_M3_OVERNIGHT_HANDOFF_20261109.md`:
1. PID 1 in the namespace is a trusted sentinel, not the workload (otherwise withdrawn attempts are unobservable on newer kernels). Recommendation: accept.
2. The 16-case preflight runs the data split and the MLP `StandardScaler.fit`, no model fit and no metric. Count it as non-numerical? Recommendation: yes.
3. Whether the four pinned fit paths can read external input: argued from the frozen code by a reviewer (recommended), or you accept the risk.
4. Wire the preflight into `c3_env_replay.run` as a separate reviewed unit after M3 acceptance, only through the e1 authorization path. Recommendation: yes.
5. Harness L8 template test vs the D28 start configs (two subtests fail since `6adf385`): test-only harness fix comparing against D28 values. Recommendation: yes.

Paste-ready: `M3：1 采纳 PID-1 哨兵；2 预检算作非数值；3 由审查者从冻结代码论证；4 预检接入另作审查单元；5 L8 模板测试改为对照 D28 配置（仅测试）。`

## Q10 — M4

Paper commit `d10b05b7` (Track S probe) is needed for the DTQ tool (M4 step 4) and is not in the local clone; the rest of M4 (c3_label_sweep wiring, templates, sweep-2 runbook) waits for M3. Nothing to decide unless you want a different order.

## For information (no answer needed)

- B1 diagnosis classes: the accepted analysis adds a class `REVIEW` (H4 undetermined → you) and accepts two cross-checked null patterns (zero audited proposals; zero evaluated 7B proposals → D7 FAIL as the gate does). The diagnosis report will list them as additions to plan §4.
- The R4 PLAN row prints the 7B interval rounded ([0.4239, 0.5800]); the gate, the diagnosis script and the restart hand-off use the exact bounds. A wording fix would move the reviewed restart base, so it is left for the next reviewed docs commit.
