# Paper B — execution runbook for the agent taking over (8 October 2026)

This runbook was written by the coordinating agent (Claude) for the agent that takes over Paper B completely. That covers the engineering, the experiments on the Ada server, the analysis, the manuscript and the release. It is AI-assisted. It was checked against the records named in §1 on 8 October 2026; nothing in it has been run. Revised the same day: the taking-over agent also runs the experiments, and the GitHub repository exists.

Its purpose is to say, in order, what to do from now to the 30 November freeze, where every input is, what you may not touch, and where you must stop for the author (Dow, Dowling Wong).

What stays with the author:
- the decisions in §3;
- the authorization record for every evidence-producing run, which he creates and commits in person;
- the novelty verdict and the hand-reading of the BAVAR preprint;
- the final read and the submission.

Everything else is yours.

This runbook does not change B's science. Science means the estimands, the outcome U, the controllers, the allocator, the comparators, the budgets, the gate sequence and the contract values. Where an item needs something the adopted design does not contain, it says "author decision" and you stop.

---

## 0. The situation in one page

**The paper.** *When should an executor agent spend its one verification?* At two checkpoints the agent can continue, verify now, or keep its single verification for later. This runs under a hard verification budget (q = 0.25) and under replay uncertainty, and the primary outcome is U, the hidden-test accuracy of the final candidate. The framing is budget-constrained dynamic algorithm configuration (DAC) with a learned configurator. That framing is proposed and not yet formally adopted (D-DAC1). The target is ICML 2027.

**What exists, all on CPU and all with scripted or mock agents:**
- paired tree records (`b_branch_v2`);
- the shared two-phase hard-budget allocator;
- the proposed cross-fitted continuation-value rule, with matched comparators (repeated-myopic and a BAVAR-inspired VOI scheduler; constant reserve as an ablation);
- the family-cluster bootstrap and the N1 replay-sensitivity grid;
- the configurator scaffold (serialiser, Kev and CLM slots, projector, heads);
- the executor with a scripted backend (three regimes, chained fork, one-verification guard);
- the governance ledger;
- contract v3 (draft);
- the manuscript, in which every number is marked planned.

Current counts: `tests/control` 207 tests, smoke 11/11. **No model call has ever been made for B, and no real-agent result exists.**

**What blocks the experiment.** Each gate is listed with its source.

| Gate | What | Source |
|---|---|---|
| **B1 task realism** | Attempt 1 of the candidate-consistency task failed R1 and R4 for the "typical" behaviour after its one repair. **One attempt is left** (P-B1). If attempt 2 fails, this task/verifier setup stops and B's ICML 2027 route is dropped. | `docs/paper_split/TASK_REALISM_REPORT.md`; OPEN_ITEMS §B1 |
| **B2 design-ready** | The 28 September fixes for the 27 September review's blockers (C1, M1/M2, N2/N3; plus C2, C3, E2, L1) were never independently re-reviewed. The novelty verdict and the hand-reading of the BAVAR preprint are the author's. | OPEN_ITEMS §B2; `INDEPENDENT_REVIEW_20260927.md` |
| **Live lane** | The Pi-backed executor does not exist; `PiBackend.run_turn` raises. The following also do not exist: B's Pi extension (three tools), B's system prompt, `endpoint_b.json`, `run_screen.py` and `bind_runtime_artifacts.py`. | plan v3.1 §0.2–0.3, IP2, IP5 |
| **P-B2 cutoffs** | Both runtime lanes (`one_step`, `sequential`) must be qualified **by 15 November 2026**. Screen and pilot must be done, the route chosen, the design frozen and the budget authorised **by 30 November 2026**. Missing either retargets B beyond ICML 2027. | OPEN_ITEMS §B5 |

**Honest read.** There is no slack before 15 November (plan v3.1 §4). The date is decided by three things:
1. the single realism attempt, which should have its verdict by about 19 October;
2. the Pi-backed executor, the largest and least certain engineering item;
3. the author's B2 items.

If attempt 2 fails, most of this runbook stops at Stage 2 (§5 says what to do then).

---

## 1. Where everything is

| Item | Location |
|---|---|
| **B repository (authoritative for B from now on)** | GitHub: `https://github.com/dowlingwong/Agent_paper_B` (private). Mac working copy: `<B_MAC_CHECKOUT>`, branch `main`. Fresh history: import commit `a93e2b7` from S, then two AI-assisted review rounds with their fixes (last commit on 8 Oct: `1554732`). Make sure the remote holds this history (Stage 0, step 1). |
| Where you work | On the Mac working copy, on Ada, or both. Code moves between machines **only through GitHub**: commit, push, then pull on the other machine. Never copy files by hand between checkouts. Stage 0 establishes what you can reach. |
| Source repository (read only for B) | Mac: `<SOURCE_REPO>`. B was copied out at **S = `4154f153`**, and no B file changed there after S (checked on 8 Oct). Paper A lives there. **Never change it for B.** |
| Plan authority (science) | `docs/paper_split/RUNBOOK.md`: the B sections of runbook v2.4, with §12.2 decisions, §12.2a controller design v2, §12.3 gate sequence and §14.2 TKV lessons. Also `B_DECISIONS_20260927.md` and `B_CONTROLLER_DESIGN_20260927.md`. |
| Infrastructure plan | `docs/paper_split/B_INFRA_CONSTRUCTION_PLAN_20261006.md`, **v3.1, draft, not adopted** (D-PLAN in §3). Packages IP0–IP11, the decisions in its §7 and the risks in §5. This runbook orders that plan; it does not repeat its detail. |
| DAC / configurator proposal | `B_DAC_CONFIGURATOR_AMENDMENT_20261004.md` (not adopted; D-DAC1–6) |
| Readiness audit (4 Oct) | `B_READINESS_AUDIT_20261004.md` (gaps G1–G8) |
| Task attempt 1 (keep unchanged) | `experiments/paper_b/task_cc_live/` (`cc_live_generator.py`, `cc_live_realism.py` with frozen `THRESHOLDS` R1–R9) and `results/paper_b/task_realism_20260927/` |
| Contracts and validator | `protocols/paper_b/contract_v{1,2,3}.yaml` (v2 active, v3 draft), `launch_validator.py`, `QUALIFICATION_AND_SCREEN_LAUNCH_SPEC.md`, `design_decisions_20260927{,b}.yaml` |
| Records | `docs/paper_split/`: `STATUS.md` (progress log), `VALIDATION.md` (executed commands only), `OPEN_ITEMS.md` (single checklist), `CLAIMS.yaml`, `MIGRATION.yaml`, `PRIOR_DISCLOSURE.md`, `SCOPE.md`. Also `PROVENANCE.md` at the root. |
| Live-run templates (read only, in the source repository) | Paper A's real-replay panel: `experiments/paper_a/panel_v2/` and `experiments/paper_a/ada/`, at **`3726e7af`** on branch `paper-a-ada-runs`, **not** at S. That commit adds the supervisor, health-probe retries, automatic resumption and stop diagnostics (see §2, lesson L1). |
| Ada host | `ucrtasl`, a shared leased 8-card RTX 6000 Ada server; other tenants use it too. Paper A has its own checkout there, named in the source repository's `protocols/paper_a/ADA_RUNBOOK_20261005.md`; **never enter, change or run anything in it.** B gets its own clone of the GitHub repository (path fixed by D-ADA1). Paper A's E-R2 v2.1 run uses one card and port **18083** from 8 Oct, for about 5 hours plus waiting for a card. The E0 bindings name 18081/18082. |
| Python and TeX | Python 3.13.4 (`.python-version`) in `.venv` from `requirements.lock`. TeX Live with `latexmk`. |
| Pi | Live lane only: `third_party/pi` (needs Node v22.19.0 at `<PINNED_NODE_ROOT>` or `R5_PI_NODE`/`NODE_BIN`, and a built Pi). `make pi-vendor-verify` fails on 3 files, inherited from S; record it and do not "fix" the ledger. |

---

## 2. Ground rules

1. **Scope.**
   - Work only in B's repository: the Mac working copy and B's own clone on Ada.
   - The source repository is read only: `git show`, `git archive`, reading files.
   - Paper A is off limits: its checkouts, branches, results, runs and port 18083.
2. **Science is frozen.** Without a dated author decision recorded in `RUNBOOK.md` (as an amendment section) and in OPEN_ITEMS' decision table, do not change:
   - estimands, U, controllers, allocator, comparators, budgets, caps, gate order, contract values;
   - the SHA-256-pinned fixtures: `smoke_b.py`, `task_cc/witnesses.py`, `design_decisions_20260927.yaml`.

   New scripted-backend entry points go in **new files**.
3. **P-B1 discipline for task attempt 2:**
   - design, mechanisms, thresholds, budget and failure disposition are sealed (SHA-256) **before** the run;
   - one run; attempt 1 stays unchanged;
   - no families added to manufacture now/later/never winners;
   - execution bugs may be fixed transparently, with a record; mechanisms and thresholds are never tuned against a result.
4. **You run the experiments yourself, within these limits.**
   - **CPU work** needs no authorization: the realism run of task attempt 2, dry runs, tests and the Kev measurement on the Mac.
   - **GPU and model work on Ada:**
     - binding, the one-root test and the smoke are engineering runs (ENGINEERING_ONLY). They are allowed once the author has approved the Ada plan (D-ADA1) and the engineering allowance (D-CAP1).
     - Qualification of each lane, the screen, the pilot and any later collection produce evidence. Each needs an **authorization record that the author creates and commits himself, in person**: you prepare the command and the record's statement, he runs it.
     - **Never** run `authorize` yourself, and never write, edit or commit an authorization record.
     - The run tool refuses without the record (Stage 5).
   - **Ada etiquette:**
     - one card at a time, chosen by the co-tenant rule (a card with no foreign compute context, as in Paper A's `select_gpu.py`);
     - never stop, signal or slow another tenant's process;
     - never take ports 18081–18083 unless ownership is confirmed;
     - long runs are detached (`setsid nohup`, under the supervisor) and monitored;
     - every run's caps are enforced by the tool before dispatch, never by you watching.
   - **Network** is limited to:
     - GitHub, for the B repository;
     - installing locked dependencies;
     - IP6 (Kev or CLM weights from the Hugging Face Hub, pinned by commit and hash).

     There is no paid API and no new spend (cap: zero).
5. **Records.**
   - Every finished step gets a STATUS entry.
   - Every check you ran gets a VALIDATION row, with command and numbers, and only commands actually run.
   - Tick an OPEN_ITEMS box only with a commit or record as evidence. "Planned" is not "done".
   - CLAIMS change only when evidence exists.
6. **Independent review.** These need an independent AI-assisted review in a fresh session that has not seen the work:
   - the attempt-2 design before sealing (the contract allows one "independent challenge");
   - the Pi-backed executor before any Ada time;
   - the live tooling before the Ada smoke;
   - the B2 re-review;
   - the frozen design before 30 Nov.

   Also review the analysis code and the manuscript text before the route decision and before any result is written into the paper.

   Either the author starts that session with a prompt you write, or you spawn a reviewer that cannot see your conversation; record which. **Never describe an AI-assisted review as human or external.** Apply findings, then record a disposition for each.
7. **Git.**
   - Stage explicit paths only.
   - Repository-local identity: Dowling Wong <wangdowling@gmail.com>.
   - One commit per coherent step.
   - Commit messages end with your session's `Co-Authored-By:` and session trailers.
   - Push `main` to `origin` (GitHub) after every completed step, and always before you switch machines.
   - Pull with `--ff-only`.
   - Never force-push and never rewrite history. The one exception is Stage 0 step 1, which only the author does.
   - Experiment results are committed from Ada, where the run happened, using the explicit globs of `ADA_RUNBOOK_B.md`. Large per-branch workspaces stay on Ada; their hashes go in the records.
8. **Hygiene.**
   - No secrets, absolute host paths (home directories, macOS temporary directories) or user names in committed files; scan before each push.
   - Restore tracked files that make targets rewrite (see OPEN_ITEMS, "Make targets that rewrite tracked files").
9. **Stop and ask** at every **STOP** below, and whenever:
   - a rule would have to be broken;
   - a check fails for a reason you cannot fix as an execution bug;
   - a record and the code disagree.

   Write the question with options and a recommendation, and wait.

**Lessons already paid for (carry them into B's live tooling):**
- **L1 (Paper A, 7–8 Oct).** On Ada, llama-server shut itself down in an orderly way about 30 minutes after each start. The cause is unknown; no host-level killer was found. Paper A's design allowed one resumption, so its first live run ended STOPPED and the design had to be amended (v2.1). **B's run tooling and contract must assume periodic server loss from the first version:**
  - health-probe retries;
  - a supervisor that restarts the server and resumes;
  - a declared resumption budget and per-root abandonment cap;
  - stop diagnostics (process alive? port listening? server log tail);
  - reporting of the number of resumptions.

  Copy the mechanism from A's `panel_v2` at `3726e7af` (`live.py`, `__main__.py supervise`, `ada/panel_v2_live.sh`), not from S.
- **L2.** A count that the reporting text depends on (resumptions, abandoned roots, roots in the design versus roots started) must be computed and tested for k = 0, 1 and several. Paper A's captions said "resumed once" and "6 of 7 roots" until a review caught it.
- **L3.** Temperature 0 makes repeated leaves uninformative. B needs at least 2 stochastic repetitions with recorded seeds (D-DEC1).

---

## 3. Author decision sheet (prepare in Stage 1; answers gate later stages)

Prepare these as one file, `docs/paper_split/B_DECISION_SHEET_<date>.md`. Give each a one-paragraph context, options and a recommendation. Recommendations come from plan v3.1 §7 unless stated. **STOP** until the author answers the items marked "now"; the others can wait until the stage named.

| ID | Decision | Needed by | Recommendation |
|---|---|---|---|
| D-PLAN | Adopt plan v3.1 as B's infrastructure plan, with the repository `Agent_paper_B` on GitHub (folder `agent_paper_b`; v3.1 says `agent-verification-timing`) | now | adopt |
| D-DAC1 | DAC as B's framing vocabulary, with the two declared deviations and no method claim (amends RUNBOOK §14.2) | now | adopt |
| D-F10 | May model-free live tooling (`run_screen --mode dry`, the binder, `endpoint_b.json` drafting) be built before B1 passes? | now | yes, model-free parts only; otherwise Stage 5 slips about a week |
| D-DEC1 | B's decoding temperature and per-repetition seed rule, and how the seed reaches llama-server | Stage 4 | temperature > 0 with recorded per-repetition seeds; value chosen from the smoke, not from outcomes |
| D-CAP1 | Do the Ada single-root run, the smoke and the qualification runs count toward the 512-leaf cap? | Stage 5 | a small, separately declared engineering allowance |
| D-RES1 (new, from L1) | B's resumption policy: budget and per-root cap | Stage 5 | automatic resumption after infrastructure stops, budget sized from the screen's expected wall time divided by 30 min, ×2 for margin; cap 5 per root; resumptions reported |
| D-ADA1 | Your access to Ada (an SSH alias from the Mac, or sessions started on Ada), B's clone path there, GitHub access from that clone, card policy (one free card, co-tenant rule as in A), port (not 18081–18083 unless ownership is confirmed on the host), and approval of the Ada plan (Stages 6–8) | by 20 Oct | B's own clone of `Agent_paper_B`; port 18084 if free; a pre-flight access check in Stage 4 |
| D-DAC2 | Primary encoder | after IP6 step 1 (Stage 4) | Kev-4B primary, CLM ablation, confirmed by the measurement |
| D-DAC3–6 | One question set and `max_chars` for both models; feature set; projection; Kev size | before the pilot | `telemetry+embedding`; `standardize` for typed questions, PCA k = 8 for raw embeddings; Kev 4B |
| D-REF1 | Descriptive oracle and budget-matched random reference policies | Stage 4 | adopt as descriptive only |
| D-GOV1/2 | Governance depth; visual panel | Stage 5 | schema + ledger + adjudication; no panel (static report only if wanted) |
| D-PT1/2/3 | Post-training scope, order, and a separate posttrain collection | after the screen | extension after the freeze; L2 then L1; size from real costs |
| B2-N | Novelty and overlap verdict (`B_NOVELTY_MEMO.md`, PRIOR_DISCLOSURE §7; `autoresearch_harness` names verify/continue and myopic-VOI policies) | before 15 Nov | the author's own |
| B2-BAVAR | Read the BAVAR / Strategic Verification preprint (preprints.org 202608.2057) by hand; confirm the related-work text and the comparator description | before 15 Nov | the author's own; automated access is blocked |
| D-INFRA-RB | `B_INFRA_RUNBOOK_20261005.md` is cited by `control/executor.py:3` and `cc_live_agent.py:3` but exists in no ref | now | if it exists on another machine (for example `<OTHER_CHECKOUT>`), commit it; else re-point both citations to this runbook |
| D-ATT2 | Approve the sealed attempt-2 design (Stage 2) | Stage 2 | — |
| Authorisations | Evidence-producing runs only: qualification per lane, screen, pilot, final collection. For each, the author runs `authorize` and commits the record on Ada. Engineering runs (binding, one root, smoke) need only D-ADA1 and D-CAP1. | per stage | in person on Ada; you prepare the command and wait |

---

## 4. Stages

Each stage lists its owner, inputs, steps, the done-when condition and the record to write. Owners: **W** = you, on CPU; **X** = you, on Ada; **D** = the author. Stages 2, 3 and 4 run in parallel after Stage 1.

### Stage 0 — Take over (W; ½ day)

1. **Repository.** Check `git -C <B_MAC_CHECKOUT> remote -v` and `git ls-remote origin main`.
   - `origin` must be `https://github.com/dowlingwong/Agent_paper_B.git`.
   - The remote `main` must contain `1554732` (the second review round, committed). If it holds only GitHub's "Initial commit" (`8ae694b`), **STOP** and ask the author to run the one-time push in the coordinator's note. You never force-push.
   - The second review is committed (`docs/paper_split/B_REPO_REVIEW2_20261008.md`).
   - `git status` shows nothing except this runbook (untracked).
2. **Fresh clone.** `git clone https://github.com/dowlingwong/Agent_paper_B.git <scratch>/b0`, then set up `.venv` from `requirements.lock`. Run:
   - `make test`: `tests/control` 207 + release + standalone;
   - `make smoke-b`: 11/11;
   - the two v3 validator refusals (`--for-launch`, both lanes);
   - `make paper-b`.

   Record the numbers.
3. Read, in this order:
   1. this runbook;
   2. OPEN_ITEMS (B and "Standalone repository");
   3. RUNBOOK.md §12.2, §12.2a, §12.3, §14.2, §15;
   4. plan v3.1 in full;
   5. TASK_REALISM_REPORT;
   6. B_READINESS_AUDIT;
   7. the attempt-1 task code;
   8. `control/executor.py` and `control/governance.py`.
4. **Commits.**
   - Commit this runbook as `docs/paper_split/B_EXECUTION_RUNBOOK_20261008.md`.
   - Replace the URL placeholders `<to be decided by the author>` in `README.md` and `PROVENANCE.md` with `https://github.com/dowlingwong/Agent_paper_B`.
   - Add a STATUS entry: "8 Oct: takeover; this runbook is the execution order".
   - Push.
5. **Machines.** Establish what you can reach and record it in STATUS:
   - the Mac working copy;
   - Ada: SSH alias or a session there, B's clone path, `nvidia-smi` readable, GitHub pull and push from the Ada clone;
   - TeX, which the paper build needs: on which machine?

   If Ada is not reachable yet, that is fine until Stage 6. Put it on the decision sheet (D-ADA1).

**Done when** the fresh-clone checks match VALIDATION's last row.

### Stage 1 — Records and the decision sheet (W, then D; 1 day)

1. Plan v3.1 IP0 step 1: add the 5–6 October B entries to STATUS and VALIDATION (executor, ledger, contract v3, configurator scaffold; 207 tests, smoke 11/11). Update OPEN_ITEMS §B6: B-DAC4 is done for the scripted path (H₁/H₂ captured from session entries) and open for the Pi path; B-DAC5 has its draft fields in contract v3.
2. Write the decision sheet (§3).
3. Write the **B2 re-review prompt** (Appendix A) as `docs/paper_split/B2_REREVIEW_PROMPT_<date>.md`.
4. **STOP:** send the author the decision sheet and the re-review prompt. The items marked "now" gate Stages 2–5.

**Done when** the author has answered D-PLAN, D-DAC1, D-F10 and D-INFRA-RB, and the decisions are recorded in OPEN_ITEMS' decision table and as a dated RUNBOOK amendment section.

### Stage 2 — Task attempt 2 (W, D; critical path; verdict by ~19 Oct)

Plan v3.1 IP1b; OPEN_ITEMS §B1; P-B1.

1. **Diagnose attempt 1 from its record only.** For the typical behaviour, no family is now-best (R1), and the verifier never beats ordinary refitting by more than 0.02 U (R4; best −0.04). Write down why, mechanistically:
   - what information the verifier gives that a competent refit does not;
   - what checkpoint 2 reveals that is worth waiting for;
   - why delay costs anything.

   Do not run attempt 1 again to search for parameters.
2. **Write `experiments/paper_b/task_cc_v2/ATTEMPT2_DESIGN.md`** before any code that produces outcomes. It must state:
   - **(a) Diagnostic value.** Where verification has diagnostic value beyond refitting: the mechanism, and why a competent agent cannot get it by refitting.
   - **(b) Waiting tradeoff.** Where waiting trades information against delay: what checkpoint 2 adds, and what verifying late costs.
   - **(c) Families.** Family count and a distinctness rule. Attempt 1's families alternate two sklearn tables and share almost all rows and features. State the near-duplicate metric and threshold that the leakage audit will use.
   - **(d) Partitions.** Three partitions (development / test / posttrain) with disjoint family ids and counts.
   - **(e) Ground truth.** The ground-truth fields recorded per root (for example, whether a shift occurred or the candidate is stale), or a statement that none are used.
   - **(f) Realism harness and thresholds.**
     - Keep attempt 1's runner behaviours (careless / typical / careful) and R1–R9 with their frozen thresholds, or declare and justify any change here.
     - Thresholds may not be loosened to pass: a change must be argued from the realism criterion's purpose, not from attempt 1's numbers.
     - R8 must use B's real caps: 512 leaves, 2M tokens, 10 h.
   - **(g) Failure disposition.** P-B1 verbatim.
   - **(h) Repair budget.** Contract v3 allows one substantive repair pass, and attempt 1 used its own. State before sealing whether attempt 2 has one. The recommendation is execution-bug fixes only, each recorded, because P-B1 forbids tuning mechanisms or thresholds against a result. The author decides this as part of D-ATT2.
   - **(i) Budget.** The cost budget of the realism run (CPU only).
3. **Independent challenge** (the contract's one `independent_challenges`): a fresh-session AI-assisted review of the design (Appendix B). Apply the findings or answer them.
4. **STOP (D-ATT2).** The author approves the design. Then seal it: write `ATTEMPT2_DESIGN.sha256` and commit the design and the hash **before** implementing the outcome-producing code.
5. **Implement in new files** under `experiments/paper_b/task_cc_v2/`: generator, tools, candidate, prompts, realism runner. Reuse attempt 1's interface where possible. Attempt 1 stays byte-identical. Unit tests for:
   - family distinctness (the declared metric);
   - partition disjointness;
   - hidden test not in the workspace (R3);
   - the fit tool returning an executable candidate, with submission as a round-trip (R9).
6. **Run realism once** (CPU, scripted behaviours). Write `results/paper_b/task_realism_v2_<UTC>/` and `docs/paper_split/TASK_REALISM_REPORT_V2.md` in attempt 1's table format.
7. **Verdict:**
   - **PASS** (R1–R9 for every behaviour the design requires): tick B1, record, continue with Stage 5.
   - **FAIL:** **STOP.** Do not tune. Write the failure record. Under P-B1 this task/verifier setup stops and B's ICML 2027 route is dropped. Go to §5.

### Stage 3 — B2 design-ready re-review (separate session; D)

1. The author, or a reviewer you spawn without your context, runs Appendix A against the current code. That code is identical to the source at S, where the 28 Sept fix commits `d6b3bd3e…b9b56265` landed; those commits are read in the source repository.
2. Fix confirmed defects as execution fixes (not science changes), with tests. If a finding needs a science change, **STOP** for an author decision.
3. The author gives the novelty verdict (B2-N) and the BAVAR reading (B2-BAVAR). Update the related-work text and the comparator description as he decides.

**Done when** the re-review's verdict is "design-ready: yes" (or every blocker is fixed and re-checked), and B2-N and B2-BAVAR are recorded. Needed before 15 Nov.

### Stage 4 — CPU engineering that does not need the task (W; 12 Oct – 2 Nov)

Order by the critical path. Detail is in plan v3.1.

1. **IP2: the Pi-backed executor.** This is the largest item.
   1. Write an interface note first: the real Pi session entries, fork semantics, the tool bridge and the launch directory. Read `pi_rpc`, `registered_tools`, `tool_socket`, `pi_extensions/`, and how A's `panel_v2` drives a fork.
   2. Move session handling behind the backend.
   3. Write a Pi-entry → `HistoryEvent` translator, with a recorded real session as a fixture.
   4. Write B's Pi extension (`fit_candidate`, `verify_candidate`, `submit_candidate`) and a `ToolBridge` wrapper, so the one-verification guard is the same code on both backends.
   5. Arm blindness: no regime-revealing paths in the system prompt; the checkpoint-2 notice goes in the turn prompt.
   6. Seed and decoding plumbing (D-DEC1).
   7. Checks:
      - CPU without Node: translator and bridge tests;
      - CPU with the pinned Node, no model: `rpc_handshake` and a fork/verify round on a recorded session.

      A replay-only fake is not evidence for fork semantics.
   8. Port the Pi-stack tests from the source repository (`experiment_scaffold/tests/test_pi_*`, `test_model_client.py`, `test_registered_tools.py`). Decide the six `RUNTIME_GLOBS` files (OPEN_ITEMS).
   9. **Independent review** before any Ada time.
2. **IP3: analysis completions.**
   - B-TKV2: context-conditioned shrinkage baseline, fitted on development families only.
   - B-TKV1: offline-collection versus online-verification budgets in the contract.
   - D-REF1 references (descriptive only).
   - B-DAC6: configurator provenance in `matching_report`; it fails on any feature-map difference.
3. **IP6 steps 1–4: encoder track.**
   1. Measure Kev-4B on Kev's `evals/agents-ood-v1` and on ten scripted B transcripts on the Mac: accuracy/Brier, latency, tokens. This is the input to D-DAC2.
   2. Write the question set for both models.
   3. Bind Kev by commit and checkpoint hash, with backend and dtype in the fingerprint.
   4. One typed-question client, with client-side token counting.
4. **IP4/IP8/IP9: governance and reproduction.**
   - Ledger writing from the run tool.
   - Adjudication records.
   - N1 fault injectors: sealed, block-randomised, with a no-fault control.
   - `export_b_tables.py`.
   - `make reproduce-b`, tested on a scripted dry run.
5. **Manuscript upkeep.** Keep every number marked planned. Update the method text only where an adopted decision changed it. The anonymity check must pass.
6. **Ada access check (X, read only; once D-ADA1 is answered).**
   1. Clone `Agent_paper_B` on Ada at the agreed path and build `.venv` there. `make test` must give the same counts as on the Mac.
   2. Read-only checks:
      - `nvidia-smi` (cards, foreign contexts);
      - the Devstral GGUF and the llama.cpp build named in the E0 bindings (record digests; do not move them);
      - Node v22.19.0;
      - free disk;
      - whether the chosen port is free.
   3. Build the Pi stack (`third_party/pi`) with the pinned Node in B's clone. Run the Node-on-CPU fork check of IP2 step 7 there as well.
   4. Start no GPU process.

   Record everything in VALIDATION.

**Done when** each sub-item's done-when in plan v3.1 holds and is recorded.

### Stage 5 — Live tooling (W; after B1 PASS, or earlier for model-free parts under D-F10)

Plan v3.1 IP5 and IP7 step 1, plus lessons L1–L3.

1. **`protocols/paper_b/endpoint_b.json`**, with the port chosen under D-ADA1.
2. **`experiments/paper_b/run_screen.py`.**
   - Modes `dry` (scripted, CPU), `smoke` and `live`.
   - `--integrity-controls 32`.
   - `--enforce-budget-caps`, checked before every dispatch: 512 terminal leaves, 2M generated tokens, 10 h, 20 accelerator-hours, 10 GiB, zero new spend. The engineering allowance is set under D-CAP1.
   - Writes the ledger.
   - Deferred stop on SIGTERM.
   - From the first version, **supervised resumption after infrastructure stops**, with the D-RES1 budget, a per-root abandonment cap, health-probe retries and stop diagnostics (L1).
   - Counts recomputed from completed roots only, tested at k = 0, 1 and 3 (L2).
   - Refuses without:
     - a qualified, bound contract;
     - an authorization record that binds the code by SHA-256 (as A's `authorize` does);
     - a matching design hash;
     - a free card.
3. **`protocols/paper_b/bind_runtime_artifacts.py`.** Fills contract v3 from the running endpoint and the repository; refuses on mismatch.
4. **Posttrain partition in the split manifest** (IP7 step 1; the validator requires it). Contract v3 configurator fields (B-DAC5).
5. **`protocols/paper_b/ADA_RUNBOOK_B.md`**: the procedure you follow on Ada, modelled on Paper A's `ADA_RUNBOOK_20261005.md` at `3726e7af`.
   - Steps: sync (`git pull --ff-only`), environment check, dry run, binding, one root, smoke, the author authorises (qualification per lane, screen, pilot), live under the supervisor, monitoring, analyse, commit with explicit globs, push.
   - A failure table.
   - The exact `authorize` command and statement for each evidence phase, for the author to run.
6. **Tests.**
   - `--mode dry` completes on CPU with a ledger and a report.
   - `--mode live` refuses on the unbound contract.
   - A simulated server loss is resumed and the run completes.
7. **Independent review** of the tooling and `ADA_RUNBOOK_B.md` (fresh session).

**Done when** all of the above pass and are recorded, and the review findings are dispositioned.

### Stage 6 — Ada: binding, one root, smoke (X; engineering only; ~27 Oct – 2 Nov)

**Precondition:** the author has answered D-ADA1 (Ada plan approved), D-CAP1, D-DEC1 and D-RES1, and the Stage 5 review is dispositioned. These runs are ENGINEERING_ONLY and draw on the engineering allowance, never on the 512 leaves.

1. On Ada, in B's clone at the pushed commit:
   1. Bind Devstral-Small-2-24B with `bind_runtime_artifacts.py`. The GGUF and server build are reused from the E0 binding; decoding per D-DEC1; harness commit; task generator; verifier; endpoint. Record the binding report.
   2. Dry run (`run_screen.py --mode dry`).
   3. **One root, three regimes**, through Pi + Devstral (IP2 step 8). The lineage invariants hold, the ledger validates, and its export equals the tree records.
   4. The **smoke**, through the Pi backend, with its leaves and histories, judged by criteria you declared in `ADA_RUNBOOK_B.md` before running it.
   5. Note how the server behaves over time. If it shuts itself down after about 30 minutes as in Paper A (L1), the supervisor must resume, and you record each event.
2. Commit the ENGINEERING_ONLY records from Ada with explicit globs and push. Pull on the Mac, check them (binding, ledger validation, smoke report) and record them in VALIDATION and STATUS.

**Done when** the smoke is GO under its predeclared criteria. If it is NO-GO: fix execution bugs transparently (new commit, re-run the smoke within the allowance), or **STOP** if the fix would change science.

### Stage 7 — Qualification of both lanes (X + D; 3–12 Nov) → 15 Nov go/no-go

1. Freeze contract v3 for qualification (status, bindings, engineering report). Commit and push.
2. **STOP:** the author authorises qualification for each lane. He runs the command you prepared, on Ada, and commits the record.
3. You run the qualification checks of `QUALIFICATION_AND_SCREEN_LAUNCH_SPEC.md` §2 for `one_step` and `sequential`, on the engineering pool, through the Pi backend. These must pass:
   - `launch_validator.py --contract protocols/paper_b/contract_v3.yaml --phase qualification --lane one_step --for-launch`;
   - the same command with `--lane sequential`.
4. Encoder track qualified on the smoke and scripted transcripts (IP10 step 2).
5. Optional: CLM binding on Ada as the ablation (IP6 steps 5–6), only if a card is free and it does not delay the lanes.
6. Commit the qualification reports from Ada and push. Record them.
7. **STOP, 15 Nov go/no-go (D).** Send the author a one-page go/no-go note: both lanes qualified? B1 closed? B2 closed? Costs per leaf measured against the planning figures?
   - **Go:** continue with Stage 8.
   - **No-go:** record it; B is retargeted beyond ICML 2027 (P-B2); go to §5.

### Stage 8 — Screen, route, pilot, freeze (X + D; 16–30 Nov)

1. **STOP:** the author authorises the screen (record on Ada).
2. You run the screen: 96 leaves plus 32 integrity controls, under the predeclared operability and reachability rules (launch spec §3–4). It runs detached under the supervisor; check it at least every few hours. Then analyse, commit from Ada, and push.
3. Write a screen report: operability, reachability, cost per leaf, infrastructure stops and resumptions. **Independent review** of the screen analysis.
4. **STOP:** the author takes the route decision (COMBINE / CORE_ONLY / narrow report) from the screen report, before any confirmatory outcome.
5. Implement the validator's `pilot` phase (it refuses today), with tests. Review it together with step 8.
6. **STOP:** the author authorises the pilot.
7. You run the pilot: 384 leaves. Fit the configurator heads on development families only. Run the matching report.
8. From the pilot's variance and cost, write the final design and its budget: size, leaves, tokens, accelerator-hours, wall time on a shared host, resumption budget. **Independent review** of the frozen design.
9. **STOP, by 30 Nov:** the author freezes the design and authorises the final budget. Missing this retargets B (P-B2).

### Stage 9 — After the freeze (you own it; write a post-freeze runbook section first)

At the freeze, add a dated "post-freeze" section to this runbook and have it reviewed. It covers:

- **Main collection.** It runs under the authorised budget, with its own authorization record from the author. You run it on Ada under the supervisor and commit the records from Ada.
- **Confirmatory analysis.** Exactly as frozen. Any deviation is a dated amendment that the author approves and the paper reports.
- **Manuscript.** Results replace "planned" only where evidence exists. Every number comes from a generated macro file (Paper A's L2 lesson). Update the claims ledger, the anonymity check and the page limit.
- **Release.** `release-b`, `check-release-b` and `reproduce-b` from the committed records, with no model call.
- **Reviews.** Fresh-session reviews of the results text and of the release candidate.
- **The author's part.** Final read, author list, AI-use statement, submission. The ICML 2027 CFP sets the date; recheck it when it is published (OPEN_ITEMS §B5).
- **Post-training (IP7/IP11).** A separate, separately authorised extension (D-PT1/3).

---

## 5. If a gate fails

- **Attempt 2 fails realism (Stage 2):**
  - Stop Stages 5–8. Finish and record only the work that does not depend on the task:
    - the IP2 executor up to the CPU checks;
    - IP3;
    - the ledger and exporters;
    - the encoder measurement.
  - Write a closing record: what failed, the evidence, what is reusable.
  - Under P-B1, propose to the author (do not decide) a retargeting note: a later venue, and whether a different task/verifier setup should be designed later as a new attempt under a new decision.
- **15 Nov or 30 Nov missed:**
  - Record the miss and continue the validation work at its normal pace.
  - Do not compress validation to keep the venue (OPEN_ITEMS §B5).
  - Ask the author for the new target.
- **An Ada run stops:**
  - Follow `ADA_RUNBOOK_B.md`'s failure table.
  - Infrastructure stops are resumed by the supervisor within the declared budget. Rule and limit stops are not resumed.
  - Never rerun a root by hand, and never start a second run of an authorised phase.
  - Report to the author with the stop record before deciding anything that is not in the failure table.
- **Ada unavailable** (no free card for days, lease ended):
  - Report at once with the dates at risk.
  - Never take a card that has a foreign context.

---

## 6. Calendar (planning targets, not promises)

| Dates | You, on CPU (W) | You, on Ada (X) | Author (D) |
|---|---|---|---|
| 8–11 Oct | Stage 0; Stage 1; start attempt-2 diagnosis; IP2 interface note | — (Paper A's E-R2 v2.1 run is on Ada; keep clear) | decision sheet "now" items; the one-time push |
| 12–18 Oct | attempt-2 design → challenge → seal; implement; **realism run (~16–19 Oct)**; IP2 steps 2–5; Kev measurement | — | D-ATT2; B2-BAVAR reading |
| 19–25 Oct | if PASS: Stage 5 (or the model-free parts earlier under D-F10); IP2 steps 6–9; IP3; IP6 steps 2–4 | Stage 4 item 6: access check, Pi build, no GPU | B2-N; D-DEC1; D-CAP1; D-RES1; D-ADA1; D-DAC2 |
| 26 Oct – 1 Nov | Stage 5 review; IP8/IP9 | Stage 6: binding, one root, smoke | — |
| 2–12 Nov | the B2 re-review closed; analysis of the Ada records | Stage 7: qualification of both lanes | authorise qualification (each lane) |
| **15 Nov** | go/no-go note | — | **decide** |
| 16–30 Nov | screen report; validator pilot phase; matching report; final design | Stage 8: screen, pilot | authorise screen and pilot; route; **freeze and budget by 30 Nov** |

---

## 7. Reporting to the author

After each stage, send a short report:
- what was done, with commits;
- the check results, with numbers;
- the open findings;
- the next **STOP** and what you need from him.

Keep STATUS and OPEN_ITEMS current, so that someone returning after a week can see the state in two files.

---

## Appendix A — B2 re-review prompt (for a fresh session)

```text
You are an independent reviewer (AI-assisted review; never call it human
review) of Paper B's controller and evaluation core in <B_MAC_CHECKOUT>
(read only; work in a fresh clone under a scratch directory). The 27 September
review (docs/paper_split/INDEPENDENT_REVIEW_20260927.md) found B "design-ready:
no": C1 (proposed and repeated-myopic controllers identical on the evaluated
path), C2 (constant-reserve ablation identical to myopic), M1 (the max-bias
correction used an in-sample second-stage decision), M2 (its test could not
detect that), N2 (path allowance fed contrast p-values instead of checkpoint
allowances), N3 (population tax applied 2p, not 2·m·p, and with an empty grid),
E2 (a zero-variance contrast read as equivalence), plus C3 and L1. Fixes were
committed on 28 September in <SOURCE_REPO>
(d6b3bd3e…b9b56265); the code was copied unchanged into agent_paper_b at
S = 4154f153. The review's reproduction scripts (identity.py, maxbias.py,
maxbias2.py, eval_semantics.py, the harness run) were never committed: re-create
each from the review's description in your scratch directory, run it against
the current code, and establish, with numbers:
the evaluated controllers can differ (agreement < 1 on a world with V̂_wait
spread); the corrected continuation target removes the max bias (nested
out-of-fold vs naive, paired CI); the max-bias test fails on the old code and
passes on the new; checkpoint-wise p1, p2 feed the path allowance; the reported
population bound uses 2·m·p_path with m = 3 consistently and no tax when p_path
is 0; an equivalence reading requires distinct policies and a non-degenerate
interval; plus C2, C3, L1. Report BLOCKER/MAJOR/MINOR/NIT with file:line,
evidence and a concrete fix, a verdict "design-ready: yes/no", and what you
checked and found correct. Write docs/paper_split/B2_REREVIEW_<date>.md
(untracked) and return it.
```

## Appendix B — independent challenge of the attempt-2 design (for a fresh session)

```text
You are an independent challenger (AI-assisted; never call it human review) of
the attempt-2 task design for Paper B in <B_MAC_CHECKOUT>:
experiments/paper_b/task_cc_v2/ATTEMPT2_DESIGN.md (not yet sealed). Read
docs/paper_split/TASK_REALISM_REPORT.md (attempt 1 failed R1 and R4 for the
typical behaviour), RUNBOOK.md §12.2–12.3 and OPEN_ITEMS §B1 (P-B1: one attempt,
sealed before running, no tuning against results, no families added to
manufacture winners). Challenge: does the design give verification diagnostic
value that a competent refit cannot get, and a real information-versus-delay
tradeoff for waiting — by mechanism, not by parameter choice? Could it pass
R1–R9 trivially or by construction (manufactured winners, a verifier that leaks
the hidden test, a target that is unsolvable without verification)? Are the
families distinct under the declared metric, the partitions disjoint, the
thresholds unchanged or justified without reference to attempt 1's numbers, R8
computed against the real caps, and the failure disposition P-B1 verbatim? Is
anything left to choose after the seal? Report BLOCKER/MAJOR/MINOR/NIT with
section, problem and fix; write docs/paper_split/ATTEMPT2_CHALLENGE_<date>.md
(untracked) and return it.
```

## Appendix C — kickoff message for the agent taking over

```text
You are taking over Paper B (ICML 2027 target) completely: engineering, the
experiments on the Ada server, analysis, manuscript and release. The repository
is https://github.com/dowlingwong/Agent_paper_B (Mac working copy
<B_MAC_CHECKOUT>). Read docs/paper_split/B_EXECUTION_RUNBOOK_20261008.md
in full (untracked in that folder until you commit it in Stage 0) and follow it
from Stage 0. Its ground rules (§2) bind you: science frozen without a recorded
author decision; P-B1 for task attempt 2; on Ada one card by the co-tenant rule,
engineering runs only within the approved allowance, and every evidence-producing
run only after I have created and committed its authorization record myself —
never run `authorize`; the source repository and Paper A (its checkouts, runs
and port 18083) are off limits; code moves between machines only through
GitHub; never describe an AI-assisted review as human; stop at every STOP and
wait for me. Begin with Stages 0 and 1 and send me the decision sheet.
```
