# Paper B (route R1) — Mac-local agent runbook (4 Nov 2026, revision 3)

**Written 4 Nov 2026 by the chat session (Claude) at the author's request; AI-assisted. Revision 2 addressed an independent review (not accepted: 2 BLOCKING, 6 MAJOR, 9 MINOR). Revision 3 (4 Nov) applies the author's full adoption of `proposals/PAPER_B_REVIEW_BENCH_EXPANSION_20261104.md` (PLAN §10 R1-BX-D1 … D14, R1-BX-REVISIONS): new tasks M10–M13, and changes to M1, M6–M9. See §4.**

One Claude Code agent on the author's Mac runs this runbook. It covers every part of the current plan that needs no GPU, no LLM inference and no remote host:
- integrating the plan documents;
- code changes and their tests;
- drafts for the author;
- analysis of the results the experiment operator copies back;
- the manuscript.

A separate **experiment operator** runs everything on the servers (`docs/r1/prompts/OPERATOR_RUNBOOK_20261104.md`). The two agents never talk directly. Work passes between them only through **pushed git branches** and **the author**.

**This runbook authorizes nothing.**

**Authority, in this order:**
1. `docs/r1/PLAN.md` §10 (every dated author row);
2. `docs/r1/RUNBOOK.md`;
3. `docs/r1/STATUS.md`;
4. the specs: `C3_DESIGN.md`, `TRACK_P_POST_TRAINING.md`, `proposals/TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md`, `prompts/TRACK_G_RUNBOOK.md` (rewritten 4 Nov);
5. this file.

If two of these disagree, stop and ask the author. **Only the author decides.** A decision exists only as a dated PLAN §10 row. You draft rows, notes and options; you never adopt them. The author commits rows and authorization notes, or tells you in chat to commit a specific one on their behalf. In that case, quote their words in the commit body.

Report to the author in **Chinese**, short and concrete. Write documents and commit messages in **English**.

---

## 0. Ground rules

**Host and compute**
- The Mac only: repo `~/Documents/agent_paper_B`, harness `~/Documents/autoresearch_harness`.
- No SSH to any server.
- No LLM inference, no model training, no evidence runs (R1-COMPUTE).
- Allowed: CPU-only tests, fake servers, tiny random-weight models, LaTeX builds and CPU simulations (Track S S0.6).

**Worktrees**
- Never touch the main working tree. `~/Documents/agent_paper_B` is on `exam-x-20261026` and carries an uncommitted move of `docs/r1/*` to `docs/*` made by someone else. Never edit, stage, stash or switch branches there.
- Work only in your own worktrees: `git -C ~/Documents/agent_paper_B worktree add .claude-worktrees/<name> -b <branch> <base>`. Use the same pattern for the harness.
- If a delete is refused, move the file to `~/Documents/agent_paper_B/_to_delete/` and tell the author.

**Code ownership**
- These rules follow MAC_LOCAL_RUNBOOK §0 of 26 Oct, updated for the 4 Nov handover:
  - `r1/c3/train/` is Track P code. Do not edit it unless the author's handover row assigns it to you.
  - `r1/c3/env.py`, `control.py`, `serve.py` and `prior_model.py` are shared. STOP and ask before editing them.
  - `r1/exam/` and `r1/scripts/exam_*` become yours **only if** the handover row (packet (a)) reassigns them from the Track X agent to you. Then you are their single editor.
  - Never edit code on a branch another agent is still using.

**Branches and commits**
- Push only your own branches: `mac-int-<date>`, `mac-<task>-<date>` and harness `r1-local-<date>`.
- Never push `main` or `r1`. Never force-push.
- Commit author: `Dowling Wong <wangdowling@gmail.com>`. The body says "AI-assisted" and ends with the attribution lines the author gives you.

**Frozen things stay frozen**
- Never edit a file after its first evidence use: rule files, frozen prompt sets, configs pinned for a run, authorization notes, label tables, frozen corpora. A change is a new version with its own sha, review and PLAN row.
- Seeds 7006–7010 are used only where PLAN rows allow: evaluation, and B.2 task-level joint-seed retraining and evaluation (R1-B2-DECOUPLE). Never for C3 or Track P training, tuning or selection.

**Decisions versus consistency edits**
- Yours: consistency edits, such as marking superseded text, fixing stale references, correcting arithmetic, and carrying a decided value into the documents.
- A proposal: any change to a decision, a threshold, a design or a claim. It goes in `docs/r1/proposals/` with a draft PLAN row.

**Honesty**
- Every number must trace to a committed file.
- Mark estimates as estimates.
- Label AI-assisted work.

**Review loop at every STOP**
1. Spawn a **fresh** reviewer subagent. Give it the task goal, this runbook, the relevant PLAN rows, the branch and commit range, and the task's "Done when". Do not give it your conclusions.
2. It writes `docs/r1/reviews/MAC_<TASK>_REVIEW_<date>.md`.
3. Fix or answer each finding. The same reviewer re-checks until it writes **accepted**.
4. You never accept your own work.

**Hand-off to the operator**
- Push the branch.
- Write the exact commit hash into a **handoff entry** in STATUS on your branch.
- Give the author a paste-ready message naming the branch, the commit and the operator step it unlocks.
- The operator deploys only reviewed commits whose hashes the author passed on.

**Results from the operator**
- They arrive on pushed `ops-*` branches, or on `trackS-ops-20261030`. Read them with `git fetch` and `git show`, and analyse them in your own worktree.
- Never edit an operator branch.

## 1. Sources and state (read first)

| Branch (GitHub) | Head | What it holds |
|---|---|---|
| `codex/coordinator-20261031` | `3a853917` (3 Nov) | Latest coordinator: PLAN rows to 3 Nov, Track X Stage A STOPs 1–8, the 31 Oct decisions |
| `codex/trackx-stagea-cooperative-20261031` | `19b8f33f` | Track X Stage A code pin |
| **`codex/b2-repair-20261031`** | **`f98e315e`** (31 Oct; contains `codex/r1-operator-drafts` `007a8d1`) | **Not merged into the coordinator.** It holds: <br>• the reviewed environment-replay plan `docs/r1/proposals/C3_ENV_RECONSTRUCTION_REPLAY_DRAFT_20261028.md` and its review; <br>• `reviews/C3_AUDIT_SPLIT_PACKAGE_REVIEW_20261028.md` (B.2 blockers); <br>• the evidence-guard, split-audit and classification code in `r1/c3/audit.py` and `r1/scripts/c3_label_sweep*`, with tests; <br>• 8 PLAN lines. |
| `docs/main-proposer-03nov` | `14dc0fea` | R1-MAIN-PROPOSER, RUNBOOK B.1b and the `x5_rule_v2` draft (independently accepted 4 Nov) |
| `docs/runbooks-04nov` | this branch | This runbook and the operator runbook (both revision 3); the 4 Nov rows **R1-BX-D1 … D14 and R1-BX-REVISIONS** in PLAN §10 (recorded from the author's full adoption of the review document); the matching RUNBOOK, C3_DESIGN, TRACK_P, TECH_ROUTE and README revisions; the rewritten `prompts/TRACK_G_RUNBOOK.md`; `proposals/TRACK_S_GPU_EXTENSION_20261104.md` |
| `docs/trackS-decisions-30oct` | `13badb0` on GitHub (a newer local head `8bfd003` exists in a bundle) | R1-TRACKS-* rows; Track S design rev 7.4; the Track S operator runbook. **Rev 3.3 of record is the file at `13badb0`**, sha `a93fb84b…`. Later heads carry rev 3.4/3.5 with superseded pins and are not of record |
| `trackS-ops-20261030` | `f5d5c6b0` (31 Oct) | Track S operator branch. R1-CACHEPROMPT-FALSE (under its own heading, outside §10), D6 reports, pins paper `d10b05b7` and harness `cacheprompt-20261031` @ `a3fedbb` (`a3fedbb` ⊃ `115df37` ⊃ `6adf385`) |
| `trackp-20261026` | `b9ad6f8f` | Track P code. It adds no PLAN rows |
| `docs/manuscript-28oct` | `9aaa6f69` | The manuscript draft, from `codex/r1-manuscript-28oct` `fb68ff3`. Use `docs/manuscript-28oct` |

**State.**
- **Sweep 1** (B.1) is frozen.
- **B.2** is STOP. The gates of the replay draft's "Separate B.2 gates" section and the AUDIT_SPLIT review are open, and there is no start ruling.
- **Track X Stage A**: attempt `t7h8` is on TASL-7.
- **Track P P.3a** is STOP (OOM, verdict UNCLEAR; options 1–3).
- **Track S** waits for the S0.1 re-run.
- **`cache_prompt: false`** is decided for Track X (R1-EXAM-CACHE-REV) and Track S (R1-CACHEPROMPT-FALSE), and for sweep 2 by R1-MAIN-PROPOSER. Sweep 1 is disclosed as not seed-replayable (R1-SWEEP1-CACHE-DISCLOSURE).
- **Benchmark expansion (4 Nov, R1-BX-*).** The CPU nodes are T0; GPU label nodes (T1) and evaluation nodes (T2) come from autoresearch, 1GC-7RC and MLGym; **Track G is the critical path**; B.7 ≈ 8 Dec on the aggregate criterion; B.6 cut; K = 6 only after the subsampling check. The rows' *(proposed)* and *(open)* items need the author (packet (j)).
- **Deepthought dual-card**: the author said in chat on 4 Nov: "deepthought我们可以用双卡deploy模型，一部分实验可以放到那上". This is intent; there is no PLAN row yet. R1-BX-REVISIONS (f) (4 Nov) now amends R1-MAIN-PROPOSER (f): the main proposer may be served on deepthought across two TITANs if the dual-card qualification (operator O5) passes.

## 2. Tasks, in priority order

Every task ends in a **STOP**: the review loop, a STATUS entry, then a report to the author.

**Order.**
- **M1 first.**
- **M2 and M3** can then run in parallel.
- **M4** comes after M3, because both edit `r1/scripts/c3_label_sweep.py`. M4 rebases on M3's accepted commit.
- **M10** (Track G code) is on the critical path (R1-BX-D14): start it right after M1, in parallel with M2 and M3. Its G.2 diff support must be reviewed and pinned before any GPU sweep.
- **M11** (baselines, gate, TabPFN view) follows M1; its gate guard must exist before any sweep-2 label is analysed.
- **M12** (the K subsampling check) waits for sweep-1 B.2 audits (operator O4).
- **M13** (serialisation order and the E6 probe) waits for packet (a) to name the editor of `r1/c3/train/`.

### M1 — One authoritative plan (integration branch) and the author's decision packet (1 day)

**Step 1: create the branch.** `git fetch origin`. Create `mac-int-20261104` from `origin/codex/coordinator-20261031`.

**Step 2: integrate each source branch** — `docs/main-proposer-03nov`, `docs/runbooks-04nov`, `codex/b2-repair-20261031`, `docs/trackS-decisions-30oct` @ `13badb0` and `trackS-ops-20261030` — like this:
- **List the files** with `git diff --name-status $(git merge-base HEAD <br>) <br>`.
- **New files:** add them.
- **Changed text files** (docs and code): a three-way `git merge-file` against the merge-base. **Never** `git checkout <br> -- <path>`: that overwrites newer rows silently.
- **Code** comes only from `codex/b2-repair-20261031`, `docs/main-proposer-03nov` and `docs/runbooks-04nov`. **Track S code stays on its branch** and is used by pin.
- **PLAN and STATUS:** insert the branch's rows and entries by hand, in date order, without changing their text.
  - R1-CACHEPROMPT-FALSE moves under §10 with its own heading line, unchanged.
  - Do not deduplicate rows by id: ids repeat (for example R1-COMPUTE occurs 12 times).
  - If two rows contradict each other, STOP and ask.

**Step 3: verify the integration.** Write `r1/scripts/plan_row_check.py`:
- it extracts every §10 table row and every STATUS entry from each source branch;
- it checks that each appears byte-identical in the result;
- it lists any row that exists only in the result.

Run it, and commit both the script and its output.

**Step 4: add a pin table** at the top of RUNBOOK §5, "Current code pins (4 Nov)". For each track, record the paper commit, the harness commit, the llama.cpp build, the GGUF sha256, the governing runbook (commit and sha) and the branch. Read every value from the branch that records it:
- **Track S:** `d10b05b7` / `a3fedbb`; runbook rev 3.3 @ `13badb0`, sha `a93fb84b…`.
- **Sweep 1:** `ccb4712` / `6adf385`.
- **Track X:** the coordinator's recorded Stage A pins.
- **Track P:** `trackp-20261026` and its recorded pins.

**Step 5: write the decision packet** `docs/r1/proposals/AUTHOR_DECISIONS_20261104.md`. Each section gives the options, a recommendation and a paste-ready draft PLAN row:

**(a) Handover row.**
- From the date of the row, the operator of `OPERATOR_RUNBOOK_20261104.md` is the only agent acting on the servers.
- The coordinator, the Track X agent, the Track S operator, the Track P agent and the deepthought agent stop at their next safe point.
- `trackS-ops-20261030` is transferred to the operator.
- `r1/exam/` and `r1/scripts/exam_*` are transferred to you as single editor, or stay with Track X: state which.
- `r1/c3/train/` (Track P code) gets a single editor once the Track P agent stops: you, or nobody until the author names one. State which (needed by M13).
- It replaces the scope of R1-OPERATOR-TAKEOVER, and R1-TRACKP-RUNBOOK's assumption of an agent on the host.
- It moves the CPU replay that the replay draft assigns to the deepthought agent over to the operator.
- It names the files that `codex/b2-repair-20261031` changes outside its own scope: Track P's `r1/c3/train/{run,trainer}.py` and the shared `r1/c3/env.py`, `control.py` and `prior_model.py`. M1 merges them only with the author's acknowledgement (or Track P's).
- Standing recovery authorizations held by previous agents are not inherited. The author re-issues the ones the operator needs, in writing and with a scope.

**(b) R1-HOSTS-04NOV (proposed amendment).**
- TASL-7: Track X Stage A until it is accepted. After that, Track P (the PLAN host), with Track S `tabular_mlp` in the gaps. No Track S GPU job runs on TASL-7 before Stage A is accepted.
- TASL-2: Track S `digits_mlp`, with Track X B1/B2 taking priority (their campaign worker is TASL-2-only).
- deepthought: B.2 replay and audits on CPU; the DTQ qualification; the A4 7B row; the main proposer across two TITANs if O5 qualifies it (R1-BX-REVISIONS (f)).
- Ada: overflow, **plus the Track G census and GPU-node noise floors (G.0)**, which R1-BX-D14 starts on Ada while Track X holds TASL-2. Resumable units only.
- **Speed figures for the packet, stated as estimates:**
  - Sweep 1 on one TITAN X made 5,813 proposals in about 11.6 h. That is about 7 s per proposal of *wall throughput*, worker CPU included, at `cache_prompt` default.
  - The recorded per-call latency averages about 112 s because 16 workers queue on one `-np 1` server.
  - Track S's serial latency on a 4090 is 0.68–0.70 s per call.
  - These figures concern the 7B. Sweep 2 uses the Track X pick, whose speed on any host is still unmeasured.

**(c) R1-DT-DUALCARD — mostly settled by R1-BX-REVISIONS (f) (4 Nov).** That row already lets the main proposer run on deepthought across two TITANs if the qualification passes. The packet now only drafts the **DTQ pass criterion** (identity, latency and projection thresholds) and the B.1b difference list. The original draft items, kept for reference:
- Allow one llama-server across two TITAN X cards (`--split-mode layer --tensor-split 1,1`), after the DTQ qualification.
- **Explicitly amend R1-MAIN-PROPOSER (f) and RUNBOOK B.1b** so that sweep 2 may run on deepthought if the pick qualifies. Otherwise it stays on "one RTX 4090 host".
- Add the sm_52 build and the two-card split to B.1b's list of differences from sweep 1.
- Also mention, as a separate option: `deepthought2.etp.kit.edu` (2 × L40S, 48 GB each) is out of scope today. A PLAN row could add it as a sweep-2 host.

**(d′) Harness pin for Track X B1/B2.** R1-EXAM-CACHE-REV requires the Track S operator's independently reviewed `cache_prompt` pin, which is harness `cacheprompt-20261031` @ `a3fedbb` (review `TRACKS_OPS_CACHEPROMPT_REVIEW_20261031.md`). The draft row confirms that the exam may use this unmerged commit directly as its harness pin, so B1 does not wait on sweep-1 B.2. R1-HARNESS-NEXT-PIN concerns merging into harness `r1` and stays as it is.

**(d) R1-EXAM-RULE-X5V2.**
- First the author's ruling on always-thinking models: skip B1, or run them descriptively. This value enters the YAML **before** its sha is computed.
- Then the row carrying the sha, from M2.

**(e) B.2, in two steps.**
- (e1) An authorization for the **environment replay**, an ENGINEERING_ONLY CPU job on deepthought, as the replay draft requires.
- (e2) After the replay passes and the remaining "Separate B.2 gates" are closed: the **B.2 start ruling**, lifting R1-B2-DECOUPLE's "does not start", together with the B.2 authorization addendum.

**(f) P.3a OOM.** Option 1, 2 or 3 of the diagnosis review.

**(g) Track S.**
- The **S0.1 re-run procedure row**: fresh servers; k = 2 serial and then concurrent, at `cache_prompt: false`; the probe output suffix; new output directories. Rev 3.3 has no re-run procedure, and the ruling file cited by R1-CACHEPROMPT-FALSE is not on any branch.
- The k rule's clause (b): if both tiers pass, choose the faster k. Its draft text is in `proposals/TRACKS_NOCACHE_20261030.md` §5–6 at `8bfd003`; quote it in the packet.
- A statement that rev 3.4/3.5 are **not of record**.
- The Track P marker helper (`proposals/TRACKP_EVIDENCE_MARKER_20261030.md`): install it or not.

**(h) R1-MAIN-PROPOSER's "(proposed)" items:**
- deepthought-CPU audits for sweep 2;
- the 4-day projection STOP;
- pooled training versus sweep 2 only, decided on validation;
- Track S keeps the 7B;
- P.3b drawn from sweep 2's training partition.

**(i) Dates.** R1-BX-D14 (4 Nov) supersedes R1-INTERNAL-FREEZES: B.7 ≈ 8 Dec, Track S fallback ≈ 15 Dec, D.3 ≈ 3 Jan, manuscript 10 Jan. They are targets. After the T1 pilot (G.4), recompute them from the measured throughput and give the author the changes **before** they are applied. Never invent numbers.

**(j) The R1-BX rows' *(proposed)* and *(open)* items.** One section per item, each with options, a recommendation and a paste-ready confirmation line:
- R1-BX-D3: the scope (T1 only; T0 stays at K = 10) and the check protocol and thresholds;
- R1-BX-D4: the schema name `manager_proposal/v2-diff`; what happens if the pick fails diff liveness;
- R1-BX-D6: which API proposer, its pin, its host and its cost cap;
- R1-BX-D7: r and α for fixed-r; relabelling A0 as the Karpathy default;
- R1-BX-D8: the numbers of the gate. **This one must be committed before any sweep-2 label is analysed;**
- R1-BX-D10: the Track S manager on GPU nodes;
- R1-BX-D13: the embedding model and the PCA dimension;
- R1-BX-REVISIONS (c): the Student-t rule for heavy-tailed floors;
- (f): the T1 label-run GPU model and the proposer host (also Track G G.3);
- (g): which host the Apptainer check ran on;
- R1-BX-D2: the 1GC-7RC repository's status, once G.0 reports it.

**Step 6: hand the packet to the author.** Give the author the packet and the paste-ready rows. The author commits them on `mac-int-20261104`, or tells you in chat to commit named rows on their behalf, which you then do. After that:
- push the branch;
- give the author a paste-ready message telling the operator to read from `mac-int-20261104` at that commit.

**Done when:**
- `plan_row_check.py` shows every source row and entry present and byte-identical;
- the paper test suite on `mac-int-20261104` (CPU, R1-LOCAL-TEST-SCOPE) has a failure set equal to the coordinator's, apart from new tests;
- the pin table is filled from the recorded sources;
- the packet exists;
- the reviewer has accepted, and the review covers: no row lost, altered or contradicted; code merged only from the three branches; options faithful to the sources; no decision taken.

### M2 — `x5_rule_v2` and its code (1 day; **must finish before Track X B1 starts**; only if packet (a) makes you editor of `r1/exam/`)

**Base.** The latest Track X Stage A code pin recorded by the coordinator, `codex/trackx-stagea-cooperative-20261031` (`19b8f33f` at writing). Rebase if the pin moves.

**Prerequisite.** The author's ruling on always-thinking models (packet (d)).

**Steps.**
0. **Harness binding.** The new B1/B2 configs bind harness `a3fedbb` (packet (d′)). Add a Track X test, using a stand-in server, showing that an exam campaign request carries `cache_prompt: false` and that the value is recorded in the manifest and in `llm_call`.
1. **The rule file.** Create `r1/exam/rules/x5_rule_v2.yaml` from `proposals/X5_RULE_V2_DRAFT_20261104.md`, with every mode quoted (`"off"`) and `always_on_in_b1` set to the author's ruling, plus its `.sha256`. **`x5_rule_v1.yaml` stays unchanged and loadable**, because Stage A's config (`exam_portal.json`) binds v1.
2. **`r1/exam/analyze.py`** (cite functions, not line numbers):
   - `load_rule` accepts both `x5_rule/v1` and `x5_rule/v2`, and the default path stays v1. This is a recorded deviation from the draft, which pointed the default at v2: keeping v1 keeps Stage A unchanged;
   - `b1_summary` and `b2_summary` follow the draft when given v2, and are unchanged under v1;
   - v2 reads `thinking_mode.b1_sensitivity.node`.
3. **`r1/scripts/exam_runner.py`**, in the B1/B2 mode logic (the block that builds `modes` per spec):
   - under v2, always-on models skip B1 if the ruling says so;
   - B2 runs with mode `"off"`;
   - the top-3 rerun is thinking-on and is marked descriptive.
4. **The free schema-sensitivity guard.** The X.7 pick row names the pick as **D22 pick** on the same line, so the guard's PLAN-line check is satisfied. Keep the guard unchanged.
5. **New configs.** Add `r1/scripts/configs/exam_b1_v2.json` and `exam_b2_v2.json`, binding v2's path and sha. Leave the Stage A config unchanged.
6. **Tests:**
   - the YAML mode fields are strings;
   - v2 loads only with its sha;
   - an always-on model is never a finalist;
   - a thinking-on row with a higher Y never wins;
   - ties go to lower GPU-h;
   - B2 refuses a non-off primary manifest;
   - every v1 test still passes against v1.
7. **Hand-off.** The v2 sha, the commit, and the draft row R1-EXAM-RULE-X5V2 carrying the sha.

**Done when:** the tests pass on the Mac CPU, with a failure set equal to the base's apart from the new tests; the reviewer has accepted; the hand-off is written.

### M3 — B.2 prerequisites, continuing `codex/b2-repair-20261031` (1–2 days)

**Base.** `codex/b2-repair-20261031` (`f98e315e`) on `mac-b2-20261104`. **Do not re-implement** what that branch already contains.

**Steps.**
1. **Read the existing work:**
   - `proposals/C3_ENV_RECONSTRUCTION_REPLAY_DRAFT_20261028.md` (its predeclared replay protocol, and "Separate B.2 gates");
   - `reviews/C3_ENV_REPLAY_DRAFT_REVIEW_20261028.md`;
   - `reviews/C3_AUDIT_SPLIT_PACKAGE_REVIEW_20261028.md`;
   - `reviews/C3_B2_REPLAY_LLM_SCOPE_REVIEW_20261031.md`;
   - the evidence-guard code and tests on the branch;
   - R1-SWEEP1-CLASSIFY;
   - the audit procedure in `docs/r1/overnight/C3_OFFLINE_HANDOFF.md`, which DEEPTHOUGHT_SWEEP1_RUNBOOK Phase 8 points to.
2. **Make a gate table** (`docs/r1/reports/MAC_B2_GATES_20261104.md`). List every gate from the replay draft and the reviews, with its state: closed, with commit and test, or open, with what is missing. Typical gates, all from the sources:
   - classification and guard code reviewed and published;
   - a validated original-file mapping;
   - a complete eligible-proposal plan;
   - the package-list hash and the per-run resolved Python and package versions;
   - the non-venv / version-mismatch STOP;
   - the replay driver.
3. **Close the open gates in code,** with tests:
   - the environment-replay driver that implements the predeclared protocol, with `--dry-run` and fixture tests;
   - any classification or guard fix still open.

   The original sweep-1 records are never rewritten.
4. **Dry-run the audit plan** against a copy of the frozen corpus layout:
   - K = 10; seeds 7001–7005 for labels and 7006–7010 for evaluation, never mixed;
   - duplicates get no label;
   - no-ops are labelled by rule;
   - counts reported by kind.
5. **Drafts for the author:**
   - `proposals/AUTH_DRAFT_c3_replay_<date>.md`, packet (e1);
   - `proposals/AUTH_DRAFT_b2_<date>.md`, packet (e2).

   Each names the pins, the host (deepthought CPUs), the worker count, the pass rule and the STOPs.

**Done when:** the gate table shows every gate either closed or explicitly left to the author; the tests pass; the dry runs work; the reviewer has accepted. The operator runs the replay, then B.2 (operator O4), each only after its authorization.

### M4 — Sweep-2 code and deepthought dual-card serving (1–2 days; after M3, rebased on its accepted commit)

**Branches.** `mac-sweep2-20261104` (paper) and `r1-local-20261104` (harness).

**Steps.**
1. **Harness pin candidate.** On `r1-local-20261104`, from `origin/r1`, merge `cacheprompt-20261031` @ `a3fedbb`, which carries the Track S commits since `6adf385`.
   - Run the full harness suite and compare the failure set with `origin/r1`.
   - Add a "defaults unchanged" test against a stand-in server: with the new fields unset, the request body equals the old body byte for byte.
   - **Do not merge into `r1`.** R1-HARNESS-NEXT-PIN applies: only after sweep-1 B.2, or by an author exception.
2. **Sweep runner.** Change `r1/scripts/c3_label_sweep.py` (`start_llamacpp`) and `r1/scripts/llama_server_instance.py` (`LlamaServerInstance`):
   - (a) Pass the pick's registry `thinking_policy` with mode `"off"`, and the exam's server flags (`--jinja`, q8_0 KV), to `LlamaServerInstance`. Do not check the flags against `--help` here: the operator checks them on the host against the pinned build (620d222). You read the build's source tag only to confirm the flags exist.
   - (b) Thread `cache_prompt` through the manager config and the manifest. Refuse a resume that has other values.
   - (c) Record the instance-seed list and check it against the sweep-1 index.
   - (d) Count thinking content: a non-empty `reasoning_content`, a `<think>` tag in `content`, or `reasoning_tokens > 0`.
   - (e) **Two-GPU serving.** Add `gpu_uuids: [u1, u2]` with `tensor_split`. It sets `CUDA_VISIBLE_DEVICES` to both cards and passes `--split-mode layer --tensor-split`. The offload proof must show N/N layers across both cards, and the occupancy census must check both. The single-GPU `gpu_uuid` path stays unchanged.
3. **Configs.**
   - Write `r1/scripts/configs/c3_sweep2_tasl2.json` now, as a template.
   - Write `c3_sweep2_deepthought2gpu.json` once the DTQ pass criterion (packet (c)) is committed; R1-BX-REVISIONS (f) permits deepthought two-card serving if O5 passes.
   - Every placeholder carries a comment naming the source of its value.
4. **DTQ tool.** Write `r1/scripts/dt_dualcard_qualify.py` and reuse the Track S probe at `d10b05b7` (`r1/tracks/probes/determinism.py`: schedule, identity, `--keep-contents`). For a GGUF, it:
   - serves on two named cards, with the B.1b settings (context 16,384, q8_0 KV, `--jinja`, thinking off, `-np 1`, `cache_prompt: false`);
   - proves offload;
   - replays 50 sweep-shaped prompts drawn from sweep-1 contexts, disjoint from the exam's frozen prompt sets, × 3 repeats;
   - reports identity, latency mean and p95, tokens per call, peak memory per card, and the sweep-2 projection.

   The output is labelled ENGINEERING_ONLY. It has a dry-run mode against a fake server.
5. **Tests.** Fake-server tests for (a)–(e) and for the tool. Existing tests must pass unchanged.

6. **Sweep-2 operator runbook (after X.7).** Write `prompts/SWEEP2_RUNBOOK_<date>.md` from `DEEPTHOUGHT_SWEEP1_RUNBOOK.md` Phases 4–9, filled with the pick's pins and the host decision. It covers the 4090 host's lease and watcher, or deepthought's two-card census, and the audit-transfer step. Reviewed before the authorization note.

**Done when:** the tests pass with an unchanged failure set; the reviewer has accepted, and checked in particular that the single-GPU path and the default request body are unchanged; the hand-off gives the operator the commit for O5 and, later, O6.

### M5 — Track X Stage A support (on request)

When the operator stops at a Stage A STOP that needs code, follow the coordinator's established pattern:
1. diagnosis from the preserved evidence the operator copies back;
2. a minimal fix with a test on the Stage A code branch;
3. an independent review;
4. a hand-off.

This applies only if you are the `r1/exam/` editor (packet (a)). Otherwise, prepare the diagnosis for the author.

### M6 — Track S desktop parts (on demand; Track S code pin `d10b05b7`)

These follow rev 3.3 @ `13badb0` and design rev 7.4:
- **S0.5 summary** (`analyze s05-summary`) and **S0.6** (`simulate_controls`, about 1 h of CPU per node). STOP 5.
- **S0.7 selection** (`collect assemble`, `analyze select`).
- **S0.8 pre-declaration draft** (`analyze predecl-template`) and the filled `proposals/AUTH_DRAFT_trackS_20261030.md`. Both are drafts.
- **Phase 9 analysis.**
- **GPU-node design revision (R1-BX-D10, 4 Nov).** From `proposals/TRACK_S_GPU_EXTENSION_20261104.md`, write the Track S design revision for 1–2 GPU nodes (autoresearch short fixed-step; one high-noise RL-type task from the Track G census) against design rev 7.4: the manager (open), seed-replayability, budget, host, and what counts as a campaign-level result for the **≈ 15 Dec fallback**. A draft for review and an author row; it changes no existing Track S pin.

Run them in a worktree at `d10b05b7`. Never change a Track S pin, rule or threshold.

### M7 — Track P desktop parts (on demand)

- **Label table and P.3b.** Once B.2 labels exist:
  - the operator builds the label table on deepthought (O4 step 3) and copies it back; you do not rebuild it. Verify its sha and counts;
  - draw the P.3b exam-set membership: a fixed subset of the training partition, from sweep 2 once it exists (R1-MAIN-PROPOSER, proposed), otherwise from sweep 1, disclosed;
  - record its sha256;
  - write the P.3b authorization draft.
- **Track P marker helper text.** Add it to `TRACK_P_POST_TRAINING.md` and to the RUNBOOK Track P section, after the author's ruling (packet (g)).
- **4 Nov:** R-B (P.6) is an optional ablation and A4 is the self-control arm (R1-BX-D9); Stage D is one round on 1–2 T1 nodes (R1-BX-D11). Keep the label table, the P.3b membership and the Track P drafts consistent with that.

### M8 — Theory and manuscript (background)

- **T4 Proposition 10 proof check.** Write a one-page checklist for the author's proof check of the revision (`proposals/T4_PROP10_REVISION_20261028.md`). Never change the theory files without the author.
- **Manuscript.** On `docs/manuscript-28oct`, in your own branch `mac-ms-20261104`:
  - align setup and methods with R1-MAIN-PROPOSER: main proposer; two sources; cross-proposer analysis; stack differences; selection-effect disclosure;
  - add the formal setup in three layers: DAC is the problem; the decision model is the policy class; one-step training objectives are a surrogate, justified by Prop. 10(a′) and tested by Track S;
  - **4 Nov wording (R1-BX-D9, D12, R1-BX-D1/D4):** R-A is "decision-focused fine-tuning"; only R-B is called RL; A4 is the self-control arm; the screening funnel per suite and the non-qualifying-node appendix; T0 single-parameter nodes as the low-interaction condition against T1 code diffs (the NF contrast); leave-one-suite-out as the primary generalisation test; the Track S fallback statement if it applies on 15 Dec;
  - writing runs in parallel from early December, for the 10 Jan manuscript (R1-BX-D14);
  - results stay `\TBD{}`.

### M10 — Track G code: nodes, fixed budgets and diff support (critical path; starts after M1)

**Governs:** RUNBOOK Track G (G.1, G.2), `prompts/TRACK_G_RUNBOOK.md` §§2–4, R1-BX-D2, D4, D5, R1-BX-REVISIONS (c), (g).

**Branches.** Paper `mac-trackg-20261104`; harness `r1-local-trackg-20261104` from `origin/r1`.

**Steps.**
1. **Diff support in the harness (G.2):**
   - apply a diff in a per-run working copy and refuse any hunk outside `editable_paths` or inside `frozen_paths`, through the existing scope validator;
   - inert detection (empty after normalisation, or an AST equal to the incumbent's);
   - duplicate detection (a normalised diff hash and the resulting code-state hash against every evaluated state of the campaign);
   - provenance fields: diff text, its hash, files touched, code-state hash;
   - the proposal schema `manager_proposal/v2-diff` (name proposed, packet (j));
   - **the T0 path is unchanged:** a test shows that a `manager_proposal/v1` campaign produces byte-identical requests and records.
2. **Node scaffolding (G.1),** written as census rows arrive from the operator: per task, a `NodeSpec` with editable and frozen paths, a fixed step or token budget (never wall-clock), a metric parser that reports divergence as its own outcome, a per-run working copy and resource limits, and validation-only selection for test-scored tasks. Tests on fake runs, including a frozen-path edit being refused.
3. **Divergence class** in the trial record and in `r1/c3/labels`: a divergent run gets no z-value; the label builder reports it separately (R1-BX-REVISIONS (c)).
4. **Apptainer runner option** for a task that ships only as an image: `apptainer exec --nv --containall`, a bound per-run copy, the `.sif` sha256 in provenance. Only if the census finds such a task.
5. **Drafts:** the T1/T2 selection row for the author (G.3), from the census; the T1 pilot plan (G.4); the T1 sweep authorization draft (G.5).

**Done when:** the harness and paper tests pass with an unchanged failure set apart from new tests; the reviewer has accepted and checked in particular that the T0 path is byte-identical; the hand-off gives the operator the commits for G.1 smoke and G.4.

### M11 — Practitioner baselines, the aggregate gate and the TabPFN matched view (after M1)

**Governs:** R1-BX-D7, D8, D13; C3_DESIGN §5–§6; RUNBOOK B.3, B.7.

**Steps.**
1. **Practitioner baselines (D7)** in `r1/c3/arms.py` (or beside it; `arms.py` is not a shared file) and in the controller path: the Karpathy default (check first whether A0 is exactly this rule; if so, label A0 as such rather than duplicating it) and fixed-r replication + t-test with r and α from packet (j), charged for its replicate runs. Offline forms for B.3; online forms through `RuleController`'s interface. `control.py` is shared: STOP and ask before editing it.
2. **Gate statistic (D8)** in `r1/c3/offline_eval` (or a new `r1/c3/gate.py`): gap closed per node against the noisy-oracle ceiling, the IQM across nodes, the probability of improvement, and the node-stratified bootstrap. Tests on synthetic tables with known answers.
3. **The pre-registration guard:** the gate code refuses to read sweep-2 or T1 `y_eval` unless a PLAN line containing `R1-BX-D8` and the numbers' confirmation exists, the same way `runtime.author_gate` reads the PLAN. Test it.
4. **TabPFN information-matched view (D13):** a feature view of hand features plus a PCA-reduced proposal-text embedding (the embedding model from packet (j); PCA fitted on training rows only); TabPFN in regression mode with its predictive distribution binned over the 12 canonical bins; the class cap checked and recorded for the installed version. The Kev side of the matched comparison is Track P code: write a spec only, unless packet (a) makes you its editor.

**Done when:** tests pass; the reviewer has accepted and checked that no evaluation label is read; the hand-off names the commit.

### M12 — The K = 10 → 6 subsampling check (after O4 delivers sweep-1 B.2 audits)

**Governs:** R1-BX-D3 (conditional).

**Steps.**
1. Draft the check protocol from R1-BX-D3's proposed text (packet (j)): 3-subsets of the label seeds; evaluation-seed statistics on training and dev instances only, never the test partition; the pass thresholds. The author commits it before you run it.
2. Run it on the Mac CPU on the label table the operator copied back (verify its sha first).
3. Report `docs/r1/reports/MAC_K_SUBSAMPLE_CHECK_<date>.md`, with an independent review.
4. **If it fails:** K stays 10. STOP and tell the author at once, with the T1 cost and the dates recomputed at K = 10.

**Done when:** the report and its review exist and the author has the verdict. Only an author row puts K = 6 into force.

### M13 — Serialisation order and the E6 probe A6 (only if packet (a) names you editor of `r1/c3/train/`)

**Governs:** R1-BX-REVISIONS (d); TRACK_P §2.2 ("Order of the serialised parts") and §5.6 (probe A6).

**Steps.**
1. Find which order the current template uses (proposal before or after history) and which template version P.3a ran with. Report it.
2. Add a template version with the 4 Nov order (history → proposal → `<decide>`). Keep the old version loadable, so that P.3a records stay reproducible.
3. Add probe A6 (history-first vs proposal-first) to the E6 probe set, with tests on a tiny random-weight model on the CPU.

If you are not the editor, write the same as a spec for the author.

### M9 — Not now

- R1-LAYOUT-FLATTEN waits for the labels freeze.
- Track H H.8 stays deferred.
- ~~Track G adapters are written only if the author keeps Track G.~~ Track G is the critical path since 4 Nov (M10).

## 3. Reporting

- After each STOP, send a few Chinese lines: what was done, commits, the review verdict, what the operator can now do, and the decisions needed.
- Keep the decision packet current, and show it when the author asks "what's pending".

## 4. Review record

**Revision 2.1 → 3** (4 Nov). Applies the author's full adoption of `proposals/PAPER_B_REVIEW_BENCH_EXPANSION_20261104.md` (PLAN §10 R1-BX-*): §1 state and branch row; the order of tasks; packet (a) adds the `r1/c3/train/` editor, (b) adds Ada for the Track G census, (c) is reduced to the DTQ criterion, (i) follows R1-BX-D14, and (j) collects the rows' proposed and open items; M6 adds the Track S GPU-node design; M7 and M8 take the 4 Nov wording; new tasks M10 (Track G code), M11 (baselines, gate, TabPFN view), M12 (K check), M13 (serialisation order); M9 no longer defers Track G. Reviewed with the operator runbook, PLAN and RUNBOOK in one independent review (`reviews/BENCH_EXPANSION_REVISION_REVIEW_20261104.md`).


**Revision 1 → 2** (independent review, not accepted):

| Finding | Fix |
|---|---|
| B1: the unmerged B.2 branch `codex/b2-repair-20261031` (with `codex/r1-operator-drafts`) was missing | Added to §1 and M1; M3 now continues it; M3 runs before M4 on `c3_label_sweep.py` |
| B2: unsafe path-selective merge | Per-file three-way merge, rows inserted by hand, and `plan_row_check.py` checking byte-identical rows (M1 steps 2–3) |
| M-a: deepthought sweep 2 contradicts R1-MAIN-PROPOSER (f) and B.1b | Made a proposed amendment (packet (c)); the deepthought config is written only after the row |
| M-b: the speed figure | Restated as wall throughput per proposal, an estimate, and kept only as background |
| M-c: the Track S runbook file on the docs head is rev 3.5 | Rev 3.3 pinned at `13badb0`, sha `a93fb84b…`; "not of record" moved to a packet row |
| M-d: M2 gaps | Ruling before the sha; functions cited instead of line numbers; new B1/B2 configs with v1 kept; D22 guard; ownership through packet (a); rebase on the latest Stage A pin |
| M-e: missing Stage A support task; ownership rules | M5 added; ownership rules restored (§0) |
| M-f: M3 sources; packet (e) circular | Phase 8 now points to C3_OFFLINE_HANDOFF; (e) split into replay authorization (e1) and B.2 ruling (e2) |
| Minors | Track P branch named; the `--help` check moved to the operator; DTQ reuses the probe at `d10b05b7`; harness ancestry stated; the `cache_prompt` wording corrected; the 7006–7010 scope corrected; Track S code pin in M6; manuscript branch named; who commits the rows (M1 step 6) |

**Revision 2 → 2.1** (4 Nov). The second-round findings of both reviewers were applied without a further review round, on the author's instruction ("stop reviewing"):
- Track X B1's harness pin is named (`a3fedbb`, packet (d′)), with a Track X test;
- M2's editor is now conditional in O2;
- e1 has been added to the dependency line;
- the replay assignment moves to the operator;
- the Stage A STOP window before STOP 0 is covered;
- the b2-repair files outside its scope need the author's acknowledgement, and M1 runs a full test;
- the v1 default is recorded as a deviation from the draft;
- the label table has one owner (O4);
- the sweep-2 operator runbook is assigned to M4 step 6;
- the source of the clause (b) text is given;
- the speed figure is aligned.
