# Coordinator prompt — 31 Oct 2026: resolve the open STOPs, restart the experiments, Track X first

**Written 31 Oct 2026 by the chat session (Claude) at the author's request; AI-assisted.** Addressed to the experiment coordinator agent on the Mac (the one that SSHes into TASL-2 / zhixu portal `portal_zhixu`, TASL-7 `tasl7` and deepthought). It continues your report of 29 Oct 12:29. The author read that report and **adopted the recommendations below (D1–D6) as his decisions (31 Oct)**. Record each as a PLAN §10 row (IDs suggested below) and a STATUS entry, citing this file, before you act on it.

Everything in your existing runbooks still applies unless this file explicitly changes it: `PORTAL_EXAM_RUNBOOK.md`, the Track P runbook, the C3 sweep / B.2 documents, the Track S operator runbook rev 3.3, PLAN §10. If this file and PLAN disagree, PLAN wins: STOP and report the conflict.

## 0. Ground rules (unchanged, restated)

- **Independent review at every STOP.** Spawn a fresh reviewer that has not seen your work. Give it the goal, the runbook, the PLAN rows, the branch/commit range and the "Done when" list, **not your conclusions**. You fix; the reviewer accepts. You never accept your own phase.
- **Git.** Work on your own ops/exam branches. Never push `main` or `r1`, never force-push, never rewrite pushed history. The automatic-approval refusal of a `main` push still stands.
- **Paths.** `docs/r1/...` paths in this file are paths on your branches. Ignore the Mac checkout's working-tree layout.
- **Addressee.** This prompt is for the coordinator. The Track S operator gets only D6, in a separate message.
- **Do not touch the author's Mac checkout `~/Documents/agent_paper_B`.** Its working tree currently holds an **uncommitted** move of `docs/r1/*` to `docs/*` (on branch `exam-x-20261026`; ~200 `D` plus untracked `docs/*`). This is not the flatten batch. Do not commit, stash, reset or check out anything there. Use your own worktrees (e.g. `/private/tmp/paper-b-operator-drafts`). Files to be removed go into a `_to_delete/` folder; never `rm`.
- **GPU.** Wrap every GPU job in `flock ~/r1_locks/gpu0.lock …` on its host. Check that no other compute process is on the card first. Track X evidence keeps priority on TASL-2, and Track P never pre-empts it.
- **Honesty and labels.** A stopped run is reported as stopped. Keep ENGINEERING_ONLY / DRYRUN / PILOT / EVIDENCE labels exactly as the runbooks define them, and invent no numbers. Anything not authorized here (restarts, resumes, frozen-code edits, budget changes) is still forbidden: STOP and ask.
- **Reports to the author** are in Chinese, in the same format as your 29 Oct report.

## 1. Step 0 — fresh census (read-only, all hosts, first)

Your last report is ~1.5 days old. Before anything else, record a census in `OPS_LOG.md`.

**Per host (TASL-2, TASL-7, deepthought):**
- GPU processes
- `~/r1_locks/` contents, including `trackx_evidence.active`
- running supervisors and PIDs
- free disk (deepthought: Ceph file count too)

**Repository state:**
- the branch heads of `origin/main`, `exam-x-*`, `trackp-*`, `ops/c3-sweep1-classify-20261028`, `trackS-ops-20261030`
- every change since 29 Oct 12:29

**Track S:** STOP-1 diagnostic of 30 Oct (`79a38f7`), awaiting the author's ruling.

**Stray write:** the `.claude/.credentials.json` write on TASL-2 that was flagged for the author. Record whether it changed again; do not open the file.

**Missing worktrees.** Check whether your `/private/tmp` worktrees and drafts still exist:
- `/private/tmp/paper-b-operator-drafts`
- `/private/tmp/paper-b-trackx-receipt-review`
- `/private/tmp/paper-b-manuscript-28oct`
- `/private/tmp/paper-b-c3-pool-merge`

On 31 Oct ~01:35 the Track S operator found `/private/tmp/paper-b-operator-drafts` **absent** (it then created an empty directory there as a writability probe). macOS may have cleared `/private/tmp`.

What is known so far:
- **Committed and safe:** `ops/c3-sweep1-classify-20261028` (`007a8d1`, pushed) and `codex/r1-manuscript-28oct` (`fb68ff3`) are in git. So are the three C3 review files cited in your 29 Oct report: `C3_SWEEP1_CLASSIFICATION_REVIEW`, `C3_SWEEP1_ENVIRONMENT_INVESTIGATION`, `C3_AUDIT_SPLIT_PACKAGE_REVIEW`.
- **Never committed:** `EXAM_STOP2_RECEIVING_REVIEW_20261028.md` is not in any git ref.

What to do:
1. List what survives and what was lost.
2. Do not reuse the empty probe directory as if it held your old state. Recreate worktrees from the pushed branches.
3. **Never commit anything from `/private/tmp` again without pushing it the same day.**

If anything contradicts this file (e.g. a job is running that should not be), STOP and report before step 2.

## 2. Author decisions of 31 Oct (record in PLAN §10)

### D1 — R1-EXAM-STOP2-ACCEPT: the author accepts Track X STOP 2

The author formally accepts the STOP 2 receiving review (`EXAM_STOP2_RECEIVING_REVIEW_20261028.md`):
- 22 expected files, 343,918,079,904 bytes in total
- per-file size and SHA-256 independently re-checked

**Condition.** STOP 2 per the exam runbook also covers **source pins and fit estimates** ("the reviewer re-checks every sha256, source and fit estimate; report the registry and the fit table").

- If the receiving review already covered the registry source pins (repo @ revision, file name, the Qwen3-Coder "source exception (unsloth)" label) and the `fit.py` table at 32k: record the acceptance.
- If it did not: a fresh reviewer checks exactly the missing part, then record the acceptance.
- Do not re-hash the 344 GB.

**If the review file was lost** with `/private/tmp` (see §1):
- A fresh reviewer re-establishes the receiving record without re-hashing. It compares, for all 22 files:
  - the registry's pinned size and sha256
  - the per-file certificates and receiver journals on the portal (`/home/dowling/exam-x/work/phase2/…`)
  - the file sizes on disk
- It also covers the source/fit part, and the file is then **committed and pushed**.
- If the on-host certificates do not cover all 22 files, STOP and report which ones are missing. The author then decides whether those few files are re-hashed.

### D2 — R1-EXAM-PROMPTSET-FREEZE: freeze the Stage A prompt set as is, disclosed as post-hoc

Freeze the prepared 50-prompt candidate set without changes. It comes from the R1-EXAM-PROMPT-SOURCE material:
- rerun-2 memory-on roots on `openml_breast_w`, `openml_ionosphere`, `tabular_mlp`
- the existing memory-on digits liveness ledgers

Its selection rule was written down after the set was drawn. It is therefore **not preregistered** and must never be called that.

**Before freezing, verify and record:**
1. No candidate or anchor model has generated output on any of these 50 prompts.
2. The selection did not use any exam-model output.

If either fails, STOP.

**Freeze commit** (on your exam branch):
- the prompt set file and its sha256
- the selection rule
- a provenance note with three timestamps: when the set was drawn, when the rule was written, when it was frozen
- a disclosure of the source: ledgers generated with the Ollama `qwen2.5-coder:7b` manager, which is also an exam anchor

After the freeze the set is immutable. Any change means a new version plus an author decision.

**Wording for the manuscript** (put it in the provenance note so the paper can quote it):
> "The 50 Stage A prompts were fixed before any candidate was run. The selection rule was recorded after the set was drawn; the set was then frozen (sha256 …) and not changed. Stage A is not preregistered."

### D3 — R1-EXAM-CACHE: make `cache_prompt` explicit in Track X

**Why.** Track S's STOP-1 diagnostic (30 Oct, `79a38f7`) measured identity under the two settings:
- `cache_prompt: false`: 200/200 identical on both hosts
- `cache_prompt: true` control: 1.000 on digits, 0.990 on tabular

**Do not overstate this.** Review finding S1 says the control did **not** reproduce the original S0.1 failure (0.930 / 0.870), and three things differ from S0.1:
1. one resident server instead of two
2. a cache pre-warmed by the test run instead of a cold one
3. the whole contrast is 2 of 200 tabular prompts

So caching is a plausible cause, not an established one. Treat D3 as removing an uncontrolled variable, not as a fix with a known effect.

Stage A step 4 measures D26 seed reproducibility, so the setting must not be implicit.

**What to do:**
- Check every Stage A request path for `cache_prompt`. `stage_a.py` already sends `false` in the fit probe; also check the template check, the grammar check and the 50-prompt replay.
- **Primary setting for Stage A:** `cache_prompt: false`. Declare it in `exam_portal.json` and record it in every manifest and `llm_call` record.
- **Also record** reproducibility under `true` for the same 50 prompts, as a descriptive column only, with three conditions:
  - run it on a **freshly started (cold) server**, before any `false` call on that server
  - keep one server resident, and record the server count
  - record per-call cache evidence (prompt tokens evaluated vs `usage.prompt_tokens`, first-call hit count)

  This stops the column from inheriting the confounds of S1.
- The B1/B2 setting is decided by the author at STOP 3, from the Stage A table and any Track S follow-up results.
- This is a config and recording change, not a protocol change. It goes through the independent review before Stage A starts.

### D4 — R1-P3A-OOM: Track P P.3a, diagnose first, then probes-only rerun if the cause is environmental

`qwen3.5-4b-base` failed in probes (E6) at 02:25:17 on 29 Oct. CUDA asked for 1.49 GiB with 1.31 GiB free on a 24 GB card, about two minutes after native ended at 02:23:21.

**Read-only diagnosis on TASL-7:**
1. `probes.stdout.log`
2. the journal `/home/dowling/r1_trackp/runs/p3a_operator_20261027/journal.jsonl`
3. any nvidia-smi / memory samples around 02:23–02:26
4. whether the native-stage process or model was still resident when probes started
5. whether any other process was on the card
6. whether the probes stage loads the model a second time
7. the peak memory of the probes stage for the other three candidates (especially `kev-4b`, the same size)

Classify the cause as one of:
- **(a) environmental:** residual allocation from the previous stage, or another process
- **(b) intrinsic:** E6 at the frozen settings needs more than the card has

**If (a):**
- Re-run the **probes stage only** for `qwen3.5-4b-base`, from the retained native outputs.
- Unchanged frozen code and config.
- A fresh process with the card verified empty first.
- Recorded as attempt 2, with attempt 1's outputs and logs kept.
- First verify that native's outputs are complete and hash them.
- Do not re-run screening, select, final, hard or native.
- Do not start removed candidates (Laya, StartLux).

**Budget.** 36.32 of 45 GPU-hours are used (R1-P3A-BUDGET-CLOCK, measured lease time). If the projected probes time (from the other candidates' probes durations) would cross the 45 h STOP, STOP before starting.

**If (b), or the cause is unclear:** STOP. Report the options (e.g. a smaller probe batch, which is a frozen-config change), each with its expected numerical effect. The author decides.

**Note.** `qwen3.5-4b-base` is the **control**, not a selection candidate (C3 candidates are Kev-0.8B and Kev-4B). Say in the report whether its missing probes would affect selection at all. It must not be classed as an E4 hard-limit failure: E4 is training memory, and this is an outputs-only probe.

### D5 — R1-B2-DECOUPLE: B.2 is decoupled from the 3 Nov labels freeze

- **The labels freeze** proceeds on B.1 only, once the already-decided classification is complete:
  - sidecar plus `git mv`
  - native records unchanged
  - every condition in `C3_SWEEP1_CLASSIFICATION_REVIEW_20261028.md` independently verified
- If the B.1 classification is not verified by 3 Nov, the freeze slips. Report it; never freeze unverified labels.
- **B.2 does not start.** It continues closing its blockers on its own schedule:
  - dirfd test coverage
  - Linux production guard
  - `procfd`
  - dataset preflight
  - evidence of the actual task interpreter
  - replay evidence
  - environment conditions
- B.2 results do not enter the frozen label tables.
- The seed rules are unchanged:
  - labels: 7001–7005
  - evaluation: 7006–7010, only for B.2 task-level joint-seed retraining and evaluation, never for C3 or Track P training, tuning or selection

### D6 — R1-TRACKS-S01-FOLLOWUP: run both Track S cache follow-ups

The author answered the Track S operator's STOP-1 question (diagnostic `79a38f7`, review S1): **run both follow-ups** before any code change or full S0.1 re-run.

**Who runs what:**
- The **Track S operator agent** executes.
- You (coordinator) schedule the GPU windows and relay the results.

**What is authorized:**
- **F1, cold control:** a control-only run (`cache_prompt: true`) on a **freshly started** server, with no prior call on that server. One server per host. Same pinned S0.1 probe, prompts, seeds, body and serial schedule as the 30 Oct diagnostic. About 7 min per host.
- **F2, single-server plain repeat:** a repeat of the plain S0.1 serial probe with **no** `cache_prompt` field, one server resident, otherwise exactly S0.1. This isolates the server count.

Run both on both hosts: digits_mlp on TASL-2, tabular_mlp on TASL-7.

**Rules:**
- **Diagnostic, not a phase.** `k` stays unset, Phase 3 is not started, no pinned code changes. Reuse the committed diagnostic code. If F2 needs a new launch script, commit it first and get it reviewed before use.
- Keep the raw responses. For every call, record:
  - prompt tokens evaluated vs `usage.prompt_tokens`
  - first-call cache hits
  - the resident server count
- **Scheduling.** Under `flock ~/r1_locks/gpu0.lock`:
  - **On TASL-2:** only between two Stage A models, never inside one, and never while `trackx_evidence.active` exists.
  - **On TASL-7:** after the D4 diagnosis and any probes-only rerun, or in a gap where no Track P job holds the lease.
- **Review.** An independent review recomputes the results from the raw JSON.

**STOP for the author.** Report:
- identity per host for F1 and F2, next to S0.1 (0.930 / 0.870) and the 30 Oct diagnostic
- which of the three S1 differences (server count, cache warmth, contrast size) the data now isolates
- the operator's recommendation on the code change and the full S0.1 re-run

The author decides those. **Do not change code or re-run S0.1 before that.**

**Already dispatched.** The Track S operator has been told separately (`TRACKS_D6_FOLLOWUP_PROMPT_20261031.md`) to run F1/F2 **immediately**, while both hosts are idle.
- If it holds `gpu0.lock` when you are ready for Stage A or D4, wait for it to release. That is roughly 15–30 min per host; do not pre-empt.
- Once Stage A has started, the "between Stage A models" rule above applies.

**Feeds D3.** Whatever F1/F2 show, the author's B1/B2 `cache_prompt` decision at Track X STOP 3 uses it. Put the F1/F2 results into the STOP 3 report.

**Unchanged:** the layout flatten. Earliest 4 Nov. The gate stays: the label freeze is verified, all four agents are at STOP, and no EVIDENCE job is running. The author still has to name the new top-level Python package. When you reach that gate, STOP and ask. Do not pre-execute anything.

## 3. Work order and hosts

Track X has priority. Run the TASL-7 and deepthought work in parallel where it does not need your attention at the same moment.

| # | Host | Work | Ends at |
|---|---|---|---|
| 1 | all | §1 census | report if anything contradicts |
| 2 | Mac (git) | Record D1–D6 in PLAN §10 and STATUS | — |
| 3 | TASL-2 | **Track X:** D1 closure → fill every `TODO_VERIFY_ON_HOST` value (10 on `exam-x-20261026`) in `exam_portal.json` from the host → complete the receiving records → D3 config → D2 freeze → independent review of 3–5 → **Stage A** (exam runbook Phase 3, ENGINEERING_ONLY) for every admissible candidate and anchor | **STOP 3**: Stage A table, independently reviewed |
| 4 | TASL-7 | **Track P:** D4 diagnosis → (a) probes-only rerun, or (b) STOP → P.3a report | P.3a STOP (review loop) |
| 5 | deepthought (CPU) | B.1 classification migration and verification; labels-freeze readiness for 3 Nov | freeze verified, or slip reported |
| 6 | deepthought | B.2 blocker closure, engineering only | no B.2 start |
| 4b | TASL-2 / TASL-7 | **Track S D6 follow-ups (F1, F2)**, run by the Track S operator in lease gaps: on TASL-2 between Stage A models, on TASL-7 after D4. No other Track S work. | STOP for the author (D6) |

### Stage A specifics (exam runbook Phase 3)

Run these per model:
1. **Fit probe at 32k** with the one-slot reserve. If a model only fits at 16k: re-probe at 16k and flag it "CPU-pool rows only".
2. **Template byte-equality** on 5 prompts.
3. **Grammar after thinking.**
4. **50 frozen prompts:**
   - parse rate, free and with schema
   - active-key validity
   - D26 reproducibility under D3
   - latency p50/p95
   - prompt, completion and reasoning token counts

Keep the failure classes separate: offload, template, parse, grammar, timeout. One template repair per model is allowed, declared before Phase 5.

Execution rules:
- One `llama-server` per model, one model at a time, resumable.
- If Stage A is interrupted, report it at a model boundary. Do not skip models to save time.
- Do **not** start B1. It needs the Phase 4 author gate:
  - the `x5_rule_v1.yaml` sha256 in a PLAN row
  - the authorization note `docs/r1/authorizations/exam_b1_<date>.md`

  At STOP 3, list which of these are still missing.

## 4. Done when (for this prompt)

- [ ] Census in `OPS_LOG.md`; no contradictions, or a STOP raised.
- [ ] D1–D6 recorded in PLAN §10 and STATUS.
- [ ] Track X STOP 2 acceptance recorded (with the source/fit coverage confirmed); host config has no placeholders; prompt set frozen with sha256 and post-hoc disclosure; `cache_prompt` explicit everywhere in Stage A. All independently reviewed.
- [ ] Stage A complete for all admissible models, table independently reviewed. **STOP 3** raised with the exclusions the author must confirm and the B1 gate items still missing.
- [ ] P.3a: diagnosis written; probes rerun completed and reviewed, or STOP with options.
- [ ] B.1 classification verified and the labels freeze done on 3 Nov, or the slip reported with its cause.
- [ ] B.2: blocker status updated; not started.
- [ ] Track S D6: F1 and F2 done on both hosts, independently reviewed, STOP raised. No other Track S work; no code change; S0.1 not re-run.
- [ ] The TASL-2 credentials-file observation reported.

**Report to the author at each STOP, and at the end:**
- what was done
- commits
- checks and their results
- review verdicts
- what is not done
- the decisions he must make (numbered, each with your recommendation)