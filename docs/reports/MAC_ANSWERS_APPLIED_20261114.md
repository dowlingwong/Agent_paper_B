# Author answers of 14 Nov: what was applied (Mac agent, 14 November 2026)

**AI-assisted (Claude, Mac-local agent). Engineering record, not an author decision.** It lists, for each answer the
author gave on 14 Nov (10:42) to the 13/14 Nov questions, and for the 10:53 container-universe unit, what the Mac agent
did, on which branch, and what is left for the author or the cluster agent. Each unit has its own branch, independent
review record and bundle; READY.txt entries 18–23 on the Mac give the bundles and sha256 sums. This summary itself is not separately reviewed; each unit it lists is. Answers are recorded here
as the author's chat answers. They are not PLAN or DECISIONS rows; nothing here sets `approved: true`.

## 1. Units

| # | Answer | Branch @ tip (accepted commit) | Result |
|---|---|---|---|
| 1 | D8: compare (i) train+dev eligibility and (ii) a D21 σ_node threshold; Q4 d→c; Q3b uv.lock; ROW (a) | `mac-m11-d8-alt-20261114` @ `6cbb6ef5` (`82923797`) | Simulation and report `M11_D8_ELIGIBILITY_ALTERNATIVES_20261114.md`. Recommendation: R1 (train + dev, paired z ≥ 3, provisional); R2 not before r = σ_node / sd(d) is known; P2 = 1/2 : 1/6 : 1/3 with floors T0 ≥ 6, T1 ≥ 4 (×12) or ≥ 2 (×6). New question D8-TEST. `gate.py` unchanged |
| 2 | W2-1 budget line in worker runs; W2-2 `trackp_prompt/v2` | `mac-w2-v3-prompt-20261114` @ `90d17fde` (`f21ab320`) | Line `Budget: trial b; worker runs used k of 20`; no trial total; feature hashes unchanged. The frozen synthetic exam `trackp_e0/v1` (and its E6 probes) keeps the v1 line, so E0 still regenerates (new question W2-4). Full suite: same 40 failures as the base |
| 3 | HTCondor Q1 (a), Q2 (b) | `mac-htcondor-20261114` @ `f2a46da1` (`46bee4c7`) | Walltime holds outside the timeout cap (`infrastructure_failure/htcondor_walltime_hold`); disk hold only by code 34/104 → `infrastructure_failure/htcondor_disk_hold` |
| 3b | Container universe (10:53 unit) | `mac-htcondor-container-20261114` @ `7a6e9612` (`37ef68f3`) | `runtime: "docker"\|"container"`, `container_image`, `container_transfer`; SIF on `/work`/`/ceph` not transferred; remote transfer only with `container_transfer: true` and the `proposed:` cap `max_container_transfer_mb` = 8000; `input_transfer_s` column. See §3 for the reference-JDL gap |
| 4 | IT-2 (A): independent review of the five 9bab3d6f files in `ec6e30a9` | `mac-answers-20261114` @ `2e3cc5c3` (record) | Accepted for the five files (record `IT2_9BAB3D6F_FIVE_FILES_REVIEW_20261114.md`). **The author decides next; until then Track P reads no real table** |
| 5 | IT-1 (a): M3's dry run records `sweep_index.path` | `mac-m3-dryrun-path-20261114` @ `129317d1` (`5ef9db16`) | Dry-run table has `sweep_index: {path, sha256}`; test added |
| 6 | DTQ: no seed in 9001–9210, plus the ledger rule | `mac-m4-dtq-20261114` @ `1da4cd60` (`0396f1bd`) | Required `instance_seed`; any int field named `*seed*` in 9001–9210 is a STOP. The 50 prompts and the projection inputs come from the cluster agent (sweep-1, read-only) |

## 2. Recorded, nothing to build now

- **D8-Q3b:** the environment is the harness `uv.lock` (NumPy 2.4.4, Python 3.13); `.python-version` is not a
  constraint. **D8-ROW:** (a). Both go into the next gate change; D8 is not confirmed.
- **B2:** decided after the B1 report. Recorded for then: extending the invalid-trial rules to B2 needs a PLAN row; at
  B2 start the marker is created first; the power-plan rule is written before it is enabled. The B2 hand-off draft
  (`mac-b2-handoff-20261114`) stays a draft, not armed.

## 3. For the cluster agent

- **W2 rebuild:** rebuild all Track P data with `c3_features/v3` and `trackp_prompt/v2`, and disclose both versions and
  the budget-line change; do not mix v1 and v2 prompts.
- **W2-3:** check from the W2 summary that every ledger has `worker_runs_total == 20`.
- **DTQ:** extract the 50 replay prompts read-only from the sweep-1 ledger; take the projection inputs from sweep-1
  measurements; then run the DTQ tool (it refuses exam-range seeds).
- **Container references:** the unit asked for equivalence with the cluster agent's hand-written, reviewed S2/S4/S5
  JDLs. Only four S2 files (all `docker://`) were on the Mac, without a git link or review record; S4/S5 were absent.
  The test checks equivalence against those four; the SIF and `transfer_container = false` lines have no outside
  reference yet. When reviewed S2/S4/S5 files exist, copy them into `r1/tests/htcondor/data/` and re-run
  `test_htc_container.py`. S5 sets `max_container_transfer_mb` and confirms that `input_transfer_s` covers the image
  transfer.

## 4. New questions for the author

- **D8-TEST.** With 2–6 test instances per node, the per-node "any of 2,000 bootstrap means ≤ 0" STOP drives P(STOP)
  wherever nodes are eligible (0.55 per eligible node at μ = 1, n_test = 6), and it does not fall steadily with more
  test instances (it falls clearly only from about 12). Options: STOP on the point test mean per node and keep the
  bootstrap for the IQM interval; a tier-level or pooled bootstrap; more test instances. The R1 threshold and the T1
  test floor (4 vs 2) depend on this.
- **D8-R1.** Adopt R1 (train + dev, paired z ≥ 3) for eligibility, after D8-TEST?
- **W2-4.** The synthetic exam (E0 `trackp_e0/v1` and the E6 probes) keeps the v1 budget line, `Budget: trial b of W
  (… worker runs left before this trial)`, while Track P prompts now use v2. Keep it so, or move the exam to v2 as a new
  E0 version `trackp_e0/v2` (new file and sha; check the E0 thresholds in `r1/c3/rules/p3_rule_v2.yaml`)?
- **HTC-C1.** Confirm three conservative choices: `/home` not treated as shared for a SIF; transfer refused for local
  jobs; a remote job with a SIF on `/ceph/srv` refused.
