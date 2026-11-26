# Mac overnight 13/14 Nov 2026 — report

**AI-assisted (Claude, Mac-local agent).** Executed `prompts/MAC_OVERNIGHT_RUNBOOK_20261113.md` (branch
`docs/runbooks-14nov` @ `69b3576b`) after a fresh independent review accepted it with 12 execution-time interpretations
(`/tmp` review file, summarised in §4), with the author's answers to Q1–Q10 in the 13 Nov start message, plus the two
extra requests of 13 Nov 22:46 (M15 standby) and 14 Nov 00:07 (W2 stop rule). No server or SSH access, no host run, no
push (delivery is bundles + `READY.txt`), no label seed, exam seed, secret or real table read, nothing deleted,
`approved: true` set nowhere. Every unit had a freshly spawned independent reviewer; every review record reproduces
the round texts unchanged and carries a `Reviewed base:` line equal to the last round's `Accepted commit:`.

## 1. Units

| Unit | Branch (repo) | Accepted commit | Review record (branch tip) | Result |
|---|---|---|---|---|
| 1 D8 gate v2 (Q1–Q3, Q5) | `mac-m11-d8-v2-20261114` (paper, from `83a12b44`) | `80d70832` (round 2) | `reviews/M11_D8_GATE_V2_REVIEW_20261114.md` @ `e3c0921e` | accepted |
| 2 HTCondor adapter (Q8) | `mac-htcondor-20261114` (paper) + `r1-local-trackg-htc-20261114` (harness) | paper `ee6567a0`, harness `e5830af3` (round 3) | `reviews/HTCONDOR_ADAPTER_REVIEW_20261114.md` @ `68057612` | accepted |
| 3 M10 v2-diff (Q8) | `r1-local-trackg-v2-20261114` (harness) + `mac-trackg-v2-20261114` (paper) | harness `717ad835`, paper `f77dbe32` (round 2) | `reviews/M10_V2DIFF_WIRING_REVIEW_20261114.md` @ `52a40d57` | accepted |
| 4 Track P RL | `mac-trackp-rl-20261114` (paper) | `2f36614a` (round 3) | `reviews/TRACKP_RL_REVIEW_20261114.md` @ `c9d29ba9` | accepted |
| 5 B2 hand-off draft (**not armed**) | `mac-b2-handoff-20261114` (paper, from `mac-b1-20261107` @ `1e5728f9`) | `d19c9072` (round 2) | `reviews/B2_HANDOFF_DRAFT_REVIEW_20261114.md` @ `2120956c` | accepted |
| 6 Appendix disclosure drafts | `mac-appendix-20261114` (paper, from `1e5728f9`) | `3fec3c50` (round 2) | `reviews/B1_APPENDIX_DISCLOSURES_REVIEW_20261114.md` @ `4a5811d1` | accepted |
| 7 Integration trial | `mac-int-trial-20261114` (paper; 9 accepted branches merged `--no-ff`) | `7c9c9cff` (round 3) | `reviews/INTEGRATION_TRIAL_REVIEW_20261114.md` @ `5d8c0274` | accepted (a trial; the author decides the real integration) |
| 8.1 M15 standby (observer 60 → 180 s) | `mac-b1-obs180-20261113` (paper, from `_d` HEAD `7912b7ff`); alias `mac-b1-m15-standby-20261114` | `dd0aa0da` (round 2) | `reviews/B1_OBSERVER_TIMEOUT_REVIEW_20261113.md` @ `8eae3e02` | accepted; **standby**, delivered only if `_d` STOPs on M15 |
| 8.2 M4 step 4, DTQ tool (Q10) | `mac-m4-dtq-20261114` (paper, from `5cd32efc`) | `0aa4bc00` (round 2) | `reviews/M4_DTQ_TOOL_REVIEW_20261114.md` @ `f20e7ccb` | accepted |
| 8.3 L8 test vs D28 configs (Q9.5) | `r1-local-l8-d28-20261114` (harness, from `a3fedbb`) | `a56c3a2` (round 1) | `reviews/HARNESS_L8_D28_TEST_REVIEW_20261114.md` on this branch | accepted |
| W2 stop rule (00:07 request) | `mac-w2-stoprule-20261114` (paper, from `mac-w2-budget-20261109`) | `92c92656` (round 2) | `reviews/W2_STOP_RULE_REVIEW_20261114.md` @ `87f67467` | accepted |

## 2. What came out, in short

- **D8 v2.** Partial-T1 is a leave-one-suite-out rule only; the whole-gate per-suite STOP is gone; eligibility adds
  paired dev z ≥ 6 (ddof 1, n_dev ≥ 2) with ineligible nodes reported; environment pinned to the harness uv.lock
  (NumPy 2.4.4). Q4 was **not implemented**: the plans give T1 nodes about 12 instances, so no T1 node can reach 10
  test instances (question D8-Q4). The plan-bounded simulation shows that at 2–6 dev instances the dev-z rule excludes
  nodes nearly at random, which is most of why P(STOP) drops (D8 observation). Confirmation draft
  `proposals/R1_BX_D8_CONFIRM_DRAFT_20261114.md` binds gate commit `da264a40`.
- **HTCondor / v2-diff.** Adapter, hold-code mapping and outcome records per your Q8 answers; v2-diff wired behind a
  flag with the item-8 repeated-timeout cap, baseline reruns and STOP. Two questions (HTC-Q1 walltime holds, HTC-Q2
  disk holds).
- **Track P RL.** GRPO per §6.4 (leave-one-out, PPO clip 0.2 × 2 epochs, k3 KL β ∈ {0, 0.02}), DAgger aggregation,
  R-B warm-up loader, R-A1 detached head (with LayerNorm) and the §6.4 rollback rule; all synthetic, CPU, no run.
  Found a **pre-existing Track P leak-guard gap** on mac-int (`EVAL_COLUMNS`; question TP-1) — M3 fixes it.
- **B2 draft.** Not armed. At the `_d` HEAD the B2 code path STOPs on purpose in several places, so a reviewed B2 code
  unit and an author row extending the B1 invalid-trial rules to B2 are preconditions (B2-NOTES).
- **Appendix.** One section per post-hoc B1 change (R4-H2, truncation + 16,384 cap, model-output invalid trials +
  journal), with `_d` placeholders and a combined paragraph carrying the PLAN-required disclosures.
- **Integration trial.** M3 conflicts with mac-int in 6 files (guards vs refactor; resolved by keeping both, for
  review); afterwards one M3 dry-run test and the tool behind it hit mac-int's D8 authority guard because the dry-run
  table does not record `sweep_index.path` (IT-1). Merging M3 whole also brings in the five held `9bab3d6f` diffs that
  need an independent review and then your acknowledgement (IT-2, Q24). M3 fixes 16 base failures (with those diffs); all later merges are
  clean. Report `reports/INTEGRATION_TRIAL_20261114.md` on the trial branch.
- **DTQ.** Tool ready for O5 with fake-server tests; the 50-prompt file and the projection inputs are operator work.
- **W2.** The campaign stops on worker runs (20); the 40-trial count is a backstop. Recommendation: v3 rebuild plus
  disclosure; questions W2-1 to W2-3.

## 3. Q-answers that needed no code

- **Q6** is delegated to the cluster agent (cluster runbook §5, which runs only if its W2 line was pasted there).
- **Q7**: `PROMPT_VERSION` stays `trackp_prompt/v1`; the W2 finding argues for bumping with the v3 rebuild (W2-2).
- **Q9.1–Q9.4**: no code tonight (the PID-1 sentinel is adopted; preflight counts as non-numeric; item 3 is for the
  reviewer from frozen code; preflight wiring is a separate review unit). Q9.5 is Unit 8.3.

## 4. Runbook interpretations used

As accepted in the runbook review: Q2 eligibility = δ_n AND dev z ≥ 6; the analysis-guard regex, tests and draft path
changed together, old draft marked superseded; Q4 by plan documents only (not implemented, asked); a `/tmp` venv for
Unit 4; Unit 2's harness part on its own branch; the v2 cap on, walltime holds outside it (HTC-Q1); Q9.1–4 no code;
Unit 8.2 probe copied byte-identically from `d10b05b7`; Units 5–6 read from `ops-b1-restart-d-20261113` @ `7912b7ff`;
08:00 freeze, Unit 7 accepted-only; Unit 8.1 continues on `mac-b1-obs180-20261113`. One more: the runbook's
`origin/mac-b1-20261107` was taken as its newest known tip `1e5728f9` (the older local `origin/` ref `3b7d5704` is
its ancestor; both reviewers found this acceptable).

## 5. Not done / caveats

- No host action of any kind; DTQ, B2 and Track P runs are for the operators after your decisions.
- Test environments are local `/tmp` venvs, not the pinned host images; each review record names its environment.
- Non-blocking review notes are listed in each review record; the ones that need a decision are in the question list.

Questions: `reports/MAC_OVERNIGHT_QUESTIONS_20261114.md`. Bundles and `READY.txt`: `Claude outputs/`.
