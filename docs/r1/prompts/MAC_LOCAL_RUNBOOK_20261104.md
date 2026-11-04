# Paper B (route R1) — Mac-local agent runbook (4 Nov 2026)

**Written 4 Nov 2026 by the chat session (Claude) at the author's request; AI-assisted.** One Claude Code agent on the author's Mac carries out this runbook. It covers every part of the current plan that needs no GPU, no LLM inference and no remote host: integrating the plan documents, code changes and their tests, drafts for the author, analysis of results that the experiment operator copies back, and the manuscript.

A separate agent, the **experiment operator**, runs everything on the servers. Its runbook is `docs/r1/prompts/OPERATOR_RUNBOOK_20261104.md`. The two agents never talk to each other directly. Work passes between them only through **pushed git branches** and the **author**.

**Authority, in order:**
1. `docs/r1/PLAN.md` §10, every dated author row;
2. `docs/r1/RUNBOOK.md`;
3. `docs/r1/STATUS.md`;
4. the specs (`C3_DESIGN.md`, `TRACK_P_POST_TRAINING.md`, `proposals/TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md`);
5. this file.

If they disagree, stop and ask the author. **Only the author decides.** A decision exists only as a dated PLAN §10 row. You draft rows, notes and options; you never adopt them.

Report to the author in **Chinese**, short and concrete. Write documents and commit messages in **English**.

---

## 0. Ground rules

- **Host.** The Mac only: repo `~/Documents/agent_paper_B`, harness `~/Documents/autoresearch_harness`.
  - No SSH to any server.
  - No LLM inference, no model training, no evidence runs.
  - CPU-only tests, fake servers, tiny random-weight models, LaTeX builds and CPU simulations (Track S S0.6) are fine.
- **The main working tree is off-limits.** `~/Documents/agent_paper_B` is checked out on `exam-x-20261026` and has an uncommitted move of `docs/r1/*` to `docs/*` that someone else made. Never edit, stage, stash or switch branches there.
  - Work only in your own worktrees: `git -C ~/Documents/agent_paper_B worktree add .claude-worktrees/<name> -b <branch> <base>`.
  - Use a worktree of `~/Documents/autoresearch_harness` for harness code.
- **Deletions.** If a delete is refused, move the file to `~/Documents/agent_paper_B/_to_delete/` and tell the author.
- **Branches.** Push only your own branches: `mac-int-<date>`, `mac-<task>-<date>` and harness `r1-local-<date>`.
  - Never push `main`, `r1` or `exam-x-*`, and never another agent's branch. Never force-push.
  - Commit author: `Dowling Wong <wangdowling@gmail.com>`. Message bodies say "AI-assisted" and end with the attribution lines the author gives you.
- **Frozen things stay frozen.** Never edit a file after its first evidence use: rule files, frozen prompt sets, configs pinned for a run, authorization notes, label tables, frozen corpora.
  - A change to any of these is a new version with its own sha, review and PLAN row.
  - Never touch seeds 7006–7010 except where a PLAN row allows them (evaluation only).
- **Decisions versus consistency edits.**
  - Consistency edits are yours to make: marking superseded text, fixing stale references, correcting arithmetic, carrying a decided value into the documents.
  - Anything that changes a decision, a threshold, a design choice or a claim is a **proposal**, in `docs/r1/proposals/`, plus a draft PLAN row for the author.
- **Honesty.** Every number traces to a committed file. Estimates are marked as estimates. AI-assisted work is labelled.
- **Review loop at every STOP.**
  1. Spawn a **fresh** reviewer subagent that has not seen your work in progress.
  2. Give it the task goal, this runbook, the relevant PLAN rows, the branch and commit range, and the task's "Done when". Do not give it your conclusions.
  3. It writes `docs/r1/reviews/MAC_<TASK>_REVIEW_<date>.md`.
  4. You fix or answer each finding, and the same reviewer re-checks.
  5. A task is done only when that reviewer writes **accepted**. You never accept your own work.
- **Handing work to the operator.** When a task produces something the operator needs (a code commit, a config, a protocol):
  1. push the branch;
  2. write the exact commit hash into a **handoff entry** in STATUS on your branch;
  3. give the author a paste-ready message for the operator naming the branch, the commit and the step it unlocks.

  The operator deploys only reviewed commits whose hashes the author has passed on.
- **Results from the operator** arrive as pushed `ops-*` branches. Read them with `git fetch` and `git show`, and analyse them in your worktree. Never edit an `ops-*` branch.

## 1. What is already decided or drafted (read first)

| Item | Where | Status |
|---|---|---|
| Main proposer = the Track X pick, run with thinking off; sweep 2 (B.1b); sweep 1 (7B) as the second source | PLAN R1-MAIN-PROPOSER; RUNBOOK B.1b; branch `docs/main-proposer-03nov` | Author decision of 3 Nov. The draft was independently accepted on 4 Nov. **Not yet merged** with the coordinator branch |
| Proposer-exam rule `x5_rule_v2` | `docs/r1/proposals/X5_RULE_V2_DRAFT_20261104.md` | Draft; you implement it (task M2) |
| Track S | Design rev 7.4; operator runbook **rev 3.3 of record** plus the operator's R1-CACHEPROMPT-FALSE procedure | Pins: paper `d10b05b7`, harness `cacheprompt-20261031` @ `a3fedbb`, recorded on `trackS-ops-20261030`. Rev 3.4/3.5 of the operator runbook were overtaken by D6 and are not of record. The S0.1 re-run is pending |
| `cache_prompt: false` for all Paper B LLM calls | PLAN rows of 31 Oct (R1-EXAM-CACHE-REV; R1-CACHEPROMPT-FALSE on `trackS-ops-20261030`) | Decided. The harness fix is not yet merged into harness `r1` |
| B.2 audits of sweep 1 | R1-SWEEP1-CLASSIFY, R1-B2-DECOUPLE, R1-B1-CORPUS-FREEZE | STOP. Still needed: the runner and audit classification fix, the environment-replay driver, and the author's start ruling |
| Track P P.3a | R1-P3A-OOM; `reviews/TRACKP_P3A_OOM_DIAGNOSIS_20261031.md` | STOP, verdict UNCLEAR. Waits on the author's choice among options 1–3 |
| Track X Stage A | Coordinator branch `codex/coordinator-20261031` (STOP 8 at `3a853917`) | Restarted 3 Nov as `t7h8` on TASL-7 |
| deepthought dual-card deployment | Author in chat, 4 Nov: "deepthought我们可以用双卡deploy模型，一部分实验可以放到那上" | Intent stated. A PLAN row is still needed (task M1) |

## 2. Tasks, in priority order

Each task ends with a **STOP**: the review loop, then a STATUS entry, then a report to the author. Tasks M2, M3 and M4 can run in parallel in separate worktrees once M1 is accepted.

### M1 — One authoritative plan (integration branch) and the author's decision packet (½–1 day)

**Why.** Author decisions are now spread over several branches:
- `codex/coordinator-20261031` (latest coordinator, Track X Stage A STOPs 1–8, 31 Oct decisions);
- `docs/main-proposer-03nov` (R1-MAIN-PROPOSER);
- `docs/trackS-decisions-30oct` (R1-TRACKS-* rows, Track S design and operator runbook);
- `trackS-ops-20261030` (R1-CACHEPROMPT-FALSE, the Track S PLAN rows and pins);
- `trackp-*` (Track P);
- this runbook's branch, `docs/runbooks-04nov`.

The operator needs one place to read.

**Steps.**
1. **Create the branch.** `git fetch origin`, then create `mac-int-20261104` from `origin/codex/coordinator-20261031`.
2. **Merge the branches.**
   - Merge `docs/main-proposer-03nov` and `docs/runbooks-04nov`.
   - Take the **docs paths only** (`docs/r1/**`) from `docs/trackS-decisions-30oct` and `trackS-ops-20261030`, path-selectively.
   - Do **not** take their code: code stays on its track branches and is used by pin.
   - PLAN and STATUS conflicts: keep both sides in date order and change no text. If two rows contradict each other, stop and ask.
3. **Add a pin table** at the top of RUNBOOK §5, "Current code pins (4 Nov)". For each track, give the paper commit, the harness commit, the llama.cpp build, the GGUF sha256 and the branch where it lives. Track S: `d10b05b7` / `a3fedbb`. Sweep 1: `ccb4712` / `6adf385`. Track X: the coordinator's recorded pins. Track P: its recorded pins. Read each from the branch that records it; never from memory.
4. **Mark superseded text.** In the Track S operator runbook (docs branch), mark rev 3.4/3.5 as "not of record: overtaken by D6 (R1-TRACKS-S01-FOLLOWUP-REV) and R1-CACHEPROMPT-FALSE".
5. **Write the decision packet.** `docs/r1/proposals/AUTHOR_DECISIONS_20261104.md`: one section per open decision, each with its options, a recommendation and a paste-ready draft PLAN row. Cover at least these:
   - **(a) Handover.** The operator of `OPERATOR_RUNBOOK_20261104.md` becomes the only agent acting on the servers. The previous operators stop at their next safe point, once the author has told them so: the coordinator and Track X agent, the Track S operator, and the Track P and deepthought agents.
   - **(b) R1-HOSTS-04NOV, host allocation.**
     - TASL-7: Track X Stage A until it is accepted, then Track P (its PLAN-assigned host); Track S `tabular_mlp` in the gaps.
     - TASL-2: Track X B1/B2 (whose campaign worker is TASL-2-only, R1-EXAM-HOST-TASL7) and Track S `digits_mlp`. Track X evidence has priority there.
     - deepthought: B.2 audits (CPU), the dual-card qualification (DTQ), sweep 2 if the pick qualifies there, and the 7B A4 row.
     - Ada: overflow only.
     - Rationale: on a TITAN X the 7B runs at about 6–7 s per call (from sweep-1 records: 5,813 calls in about 11.7 h with one server) against about 0.65 s on a 4090. So Track S, with about 80k calls per node, stays on the 4090s, while sweep 2, with about 6k calls, can use deepthought.
   - **(c) R1-DT-DUALCARD.** A deepthought model may be served by one llama-server across **two** TITAN X cards (`--split-mode layer --tensor-split 1,1`), only after the DTQ qualification (operator runbook O5) and only for workloads the PLAN assigns. One host type per labelled table still holds.
   - **(d) R1-EXAM-RULE-X5V2.** The sha comes from task M2 after review. Also open: whether always-thinking models skip B1.
   - **(e) B.2 start ruling.** This lifts R1-B2-DECOUPLE's "does not start" once the prerequisites of M3 are met and the environment replay passes.
   - **(f) P.3a OOM.** The author picks option 1, 2 or 3 of the diagnosis review.
   - **(g) Track S.**
     - k rule clause (b): if both tiers pass, choose the faster k;
     - S0.1 re-run acceptance procedure;
     - Track P marker gate before Phase 6 on TASL-7;
     - whether the Track P marker helper (`proposals/TRACKP_EVIDENCE_MARKER_20261030.md`) is installed.
   - **(h) The R1-MAIN-PROPOSER "(proposed)" items:** deepthought-CPU audits for sweep 2; the 4-day projection STOP; pooled training versus sweep 2 only, decided on validation; Track S keeps the 7B; P.3b drawn from sweep 2's training partition.
   - **(i) Internal freezes.** R1-INTERNAL-FREEZES set labels on 3 Nov, B.7 on 26 Nov, D.3 complete on 20 Dec and the manuscript on 10 Jan. Labels have already slipped. Propose new dates from the operator's projections; do not invent numbers.
6. **Report.** Give the author a paste-ready list of rows to commit. Once the author has committed, push `mac-int-20261104`, and give the author a paste-ready message telling the operator to read the runbook and PLAN from that branch at that commit.

**Done when:** `mac-int-20261104` contains every author PLAN row from all the listed branches, in date order and unchanged; the pin table is filled from the recorded sources; the decision packet exists; the reviewer has accepted the integration (no row lost, altered or contradicted) and the packet (options faithful to the sources, no decision taken).

### M2 — `x5_rule_v2` and its code (1 day; **must finish before Track X B1 starts**)

**Base.** The coordinator's Track X code branch (`codex/trackx-stagea-cooperative-20261031` or the branch the coordinator records as the exam code pin; check STATUS).
**Worktree branch.** `mac-x5v2-20261104`.

**Steps.**
1. Create `r1/exam/rules/x5_rule_v2.yaml` exactly as in `proposals/X5_RULE_V2_DRAFT_20261104.md`, with every mode quoted (`"off"`), plus its `.sha256`. `x5_rule_v1.yaml` is not modified.
2. `r1/exam/analyze.py`:
   - `load_rule` accepts `x5_rule/v2`, and its default path points at v2;
   - `b1_summary` takes μ̂ from thinking-off observations only, marks registry `thinking_policy.mode == 'always_on'` as ineligible, reports thinking-on rows separately and reads `thinking_mode.b1_sensitivity.node`;
   - `choose_finalists` ranks only eligible rows;
   - `b2_summary` ranks only primary rows with `mode == "off"` and raises an error on any other mode.
3. `r1/scripts/exam_runner.py:109–117`:
   - always-on models skip B1 if the author keeps `always_on_in_b1: skip`;
   - B2 runs with mode `"off"`;
   - the top-3 rerun becomes thinking-on and is marked descriptive;
   - the B1 and B2 configs bind v2's path and sha.
4. Tests:
   - the rule loads only with its sha, and its mode fields are strings;
   - an always-on model never becomes a finalist;
   - a thinking-on row with a higher Y never wins;
   - ties go to lower GPU-h;
   - B2 refuses a non-off primary manifest;
   - the existing exam tests still pass, except where they test v1-only behaviour, which stays tested against v1.
5. Hand off: the sha of `x5_rule_v2.yaml`, the commit hash, and the draft PLAN row R1-EXAM-RULE-X5V2 carrying the sha (the id must contain `R1-EXAM-RULE` for `runtime.author_gate`).

**Done when:** the tests pass on the Mac CPU, with a failure set identical to the base apart from the new tests; the reviewer has accepted (YAML types, the code paths in `analyze.py` and `exam_runner.py`, nothing in v1 changed); the handoff is written.

### M3 — B.2 prerequisites (1–2 days)

**Base.** The coordinator branch. Find the reviewed 16-case environment-replay plan referenced in `reviews/C3_B2_REPLAY_LLM_SCOPE_REVIEW_20261031.md` and the runner and audit classification defect recorded in R1-SWEEP1-CLASSIFY.

**Steps.**
1. **Classification fix** (R1-SWEEP1-CLASSIFY). The sweep runner and the audit step label EVIDENCE runs correctly from a matching authorization. Add tests. The original sweep-1 records are never rewritten: the classification sidecar stays the binding record.
2. **Environment-replay driver.** Implement the reviewed 16-case plan:
   - rebuild worker configurations from the retained structured edits;
   - re-run them on the audit host's environment;
   - compare the primary worker metrics with zero tolerance;
   - send no manager LLM requests;
   - write a JSON report with every case, both values and the environment fingerprint;
   - include a `--dry-run` mode and fixture tests.
3. **Audit step for sweep 1.** Check that the B.2 audit command of `DEEPTHOUGHT_SWEEP1_RUNBOOK.md` Phase 8 works on the frozen corpus as committed, run as a dry run against a copy:
   - K = 10;
   - seeds 7001–7005 for labels and 7006–7010 for evaluation, kept separate;
   - duplicates get no label, and no-ops are labelled by rule;
   - the counts are reported by kind.
4. **Hand off.** The commit, the dry-run outputs, and a **draft** B.2 authorization addendum for the author (`docs/r1/proposals/AUTH_DRAFT_b2_<date>.md`) naming the pins, the replay requirement and its pass rule, the host (deepthought CPUs), the worker count and the STOPs.

**Done when:** the tests pass; the dry runs work on the frozen corpus layout; the reviewer has accepted. The operator then runs the replay and B.2 (operator runbook O4), only after the author's start ruling.

### M4 — Sweep 2 and deepthought dual-card code (1–2 days; parallel with M2 and M3)

**Base.** The sweep code at the sweep-1 paper pin, plus the harness `cache_prompt` fix.
**Branches.** `mac-sweep2-20261104`; harness `r1-local-20261104`.

**Steps.**
1. **Harness pin candidate.** On `r1-local-20261104` (from `origin/r1`), merge harness branch `cacheprompt-20261031` @ `a3fedbb`, together with the Track S commits it carries from `115df37`.
   - Run the full harness suite and compare the failure set with `origin/r1`.
   - Write a "defaults unchanged" check: with `cache_prompt` and the thinking flag unset, the request body equals the old one byte for byte, as the 30 Oct stand-in-server check did.
   - **Do not merge into `r1`.** R1-HARNESS-NEXT-PIN allows that only after sweep-1 B.2, or by an author exception.
2. **Sweep runner** (`r1/scripts/c3_label_sweep.py`, `r1/scripts/llama_server_instance.py`):
   - (a) pass the pick's registry `thinking_policy` with mode `"off"` and the exam's server flags (`--jinja`, q8_0 KV) to `LlamaServerInstance`, and check the flags against the build's `--help`;
   - (b) thread `cache_prompt` through the manager config, record it in the manifest, and refuse a resume with other values;
   - (c) record the instance-seed list and check it against the sweep-1 index;
   - (d) the thinking-content counter: a non-empty `reasoning_content`, a `<think>` tag in `content`, or `reasoning_tokens > 0`;
   - (e) **two-GPU serving:** a config key `gpu_uuids: [uuid1, uuid2]` with `tensor_split`, which sets `CUDA_VISIBLE_DEVICES` to both and passes `--split-mode layer --tensor-split <split>`. The offload proof must show N/N layers across both cards. The occupancy census checks both cards. `gpu_uuid` (one card) keeps working unchanged.
3. **Configs.** Templates `r1/scripts/configs/c3_sweep2_tasl2.json` and `c3_sweep2_deepthought2gpu.json`, with placeholders for the pick and comments saying where each value comes from.
4. **The deepthought dual-card qualification tool (DTQ)** (`r1/scripts/dt_dualcard_qualify.py`). For a given GGUF:
   - start one server on two named cards;
   - prove full offload;
   - replay N sweep-shaped prompts (default 50 × 3 repeats, with `cache_prompt: false`, thinking off and the D26 seeds), reusing the Track S probe's schedule and identity code where possible;
   - report the within-server identity, latency mean and p95, tokens per call, peak memory per card and a projection for sweep 2 (calls × latency).
   - Mark the output ENGINEERING_ONLY. It has a dry-run mode against a fake server.
5. **Tests:** fake-server tests for (a)–(e) and the tool; existing sweep tests unchanged.

**Done when:** the tests pass with an unchanged failure set; the reviewer has accepted, checking especially that the one-GPU path and the default request body are unchanged; the handoff gives the operator the commit for O5 (DTQ) and later O6.

### M5 — Track S desktop parts (on demand, as the operator copies results back)

These follow the Track S operator runbook (rev 3.3 of record) and design rev 7.4:
- **S0.5 summary** (`analyze s05-summary`) and the **S0.6 synthetic calibration** (`simulate_controls`, about 1 h per node of CPU), run when the S0.5 outputs arrive. STOP 5 review.
- **S0.7 selection** (`collect assemble`, `analyze select`) after the tuning outputs arrive.
- **S0.8 pre-declaration draft** (`analyze predecl-template`) and the filled authorization draft `proposals/AUTH_DRAFT_trackS_20261030.md`. Both are drafts; the author commits them.
- **Phase 9 analysis** after S3e.

Each is a STOP with review. Never change a Track S pin, rule or threshold.

### M6 — Track P desktop parts (on demand)

- Once B.2 labels exist:
  - build the label table (`r1.c3.dataset build-sweep`) from the operator's copy-back;
  - draw the P.3b exam-set membership, which is a fixed subset of the training partition. Per R1-MAIN-PROPOSER (proposed), it comes from sweep 2 once that exists; if P.3b must run earlier, it comes from sweep 1, disclosed;
  - compute its sha256 and prepare the P.3b authorization draft.
- Fold the Track P marker helper text into `TRACK_P_POST_TRAINING.md`, and the RUNBOOK Track P section, after the author's decision (M1 (g)).

### M7 — Theory and manuscript (background; whenever M1–M4 are waiting)

- Support the author's proof check of T4 Proposition 10's revision (`proposals/T4_PROP10_REVISION_20261028.md`). Prepare a one-page checklist of what the author must verify. Do not change theory files without the author.
- **Manuscript** (`docs/manuscript-28oct` → your branch). Update the setup and methods sections to R1-MAIN-PROPOSER: the main proposer, two sources, cross-proposer analysis, stack differences and selection-effect disclosure. Add the formal-setup layering:
  - DAC as the problem;
  - the decision model as the policy class;
  - single-step training objectives as a surrogate, justified by Prop. 10(a′) and tested by Track S.

  Results stay `\TBD{}`.

### M8 — Not now

- **R1-LAYOUT-FLATTEN** waits for the labels freeze, which has not happened yet.
- **Track H H.8** stays deferred.
- **Track G** adapters only if the author keeps Track G (MLGym needs a container by 10 Nov).

## 3. Reporting cadence

- After each STOP, send the author a few Chinese lines: done, commits, review verdict, what the operator can now do, and decisions needed.
- Keep `docs/r1/proposals/AUTHOR_DECISIONS_20261104.md` current; show it when the author asks "what's pending".
- Do not wake the author for routine progress.
