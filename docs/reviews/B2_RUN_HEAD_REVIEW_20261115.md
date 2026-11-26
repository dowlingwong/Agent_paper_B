# Independent review — B2 run HEAD (`8709dce7…`) before the author gate and launch — 15 November 2026

**Reviewer role:** fresh, independent, read-only reviewer, spawned for this exact HEAD. Not the author,
not the B2 executor, not the author of the B2 code/hand-off units. No changes were made to the run
checkout; no commit or push was made; no SSH/server access; no secrets read. The only file written is
this review file (in the shared worktree, untracked; it is **not** part of the run HEAD).

**Review target.** Run HEAD **`8709dce792d45bbb5c05d9f7d239e19454efbb15`**, branch `ops-b2-20261115`
(`origin/ops-b2-20261115` = same), parent `aeeab991e8831b237cbb59107cfb6ddb9913be71`
(`mac-b2-handoff-exec-20261115`). Reviewed against `proposals/B2_HANDOFF_EXEC_20261115.md` §1–§3 and §5.1
and its review `reviews/B2_HANDOFF_EXEC_REVIEW_20261115.md`, the B2 code unit review
`reviews/B2_CODE_UNIT_REVIEW_20261114.md`, the accepted PLAN-row drafts on `mac-b2-plan-20261114` @
`3533b5457399afeb2b1eb050fdf763db4b21e660`, the filled config, and the Mac side (`READY.txt`).

**Note on the shared worktree.** At the start of this review the worktree
`/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/ops-b2-20261115` was clean at `8709dce7`
on `ops-b2-20261115-local`. During the review the B2 executor switched the shared worktree to its own
branch `ops-b2-exec-20261115` @ `2f4970e5` (pushed to `origin/ops-b2-exec-20261115`), which adds only
`docs/r1/reports/b2_exec_20261115/*`. The reviewed files are byte-unchanged by that commit
(`git diff 8709dce7 2f4970e5 -- docs/r1/PLAN.md docs/r1/authorizations/trackx_b2_20261115.md
r1/scripts/configs/exam_b2_v2.json` is empty), and `8709dce7` remains intact as `origin/ops-b2-20261115`
and local `ops-b2-20261115-local`. The static checks below were therefore read from `git show
8709dce7:<path>` / the shared clone at `8709dce7`; the author gate was run in a temporary
`git clone --shared` checked out at `8709dce7` (clean), with only the two host-only Stage A table digests
stubbed, exactly as the hand-off review did.

---

## 1. What was checked and how

| # | Check | Method | Result |
|---|---|---|---|
| 1 | (a) three-way reviewed base | `head` / `grep` of `docs/r1/reviews/B2_CODE_UNIT_REVIEW_20261114.md`; Mac `~/Documents/agent_paper_B/Claude outputs/READY.txt` | **PASS.** First line `Reviewed base: 37282ec37a715feaaea48dd621ae08678424accc`; the only/last `Accepted commit:` line is the same SHA; config `paper_commit` is the same SHA; READY.txt (item 26, B2 code unit) has `Reviewed base: 37282ec3…` and item 27 repeats `paper_commit: 37282ec3…`. See MINOR-3 on READY.txt being Mac-local. |
| 2 | (b) PLAN §10 rows vs the accepted drafts | `git show origin/mac-b2-plan-20261114:docs/r1/proposals/PLAN_ROW_*`; byte comparison with the committed §10 blocks | **PASS.** Both committed blocks (heading + table header + separator + row) are byte-identical to the **first (Chinese) paste block** of the accepted drafts with only `14 November 2026` → `15 November 2026`. Headings are `### 15 November 2026 — B2 instance count (author)` and `### 15 November 2026 — B2 invalid trials (author)` (full month + `author`). |
| 3 | (b) row structure and counts | `runtime._b2_author_rows`, `_x5_author_row`, `_dated_author_decisions` on the committed PLAN; regex checks | **PASS.** Exactly one dated author row per ID, no second row in §10 and no B2 row outside §10 (`grep R1-EXAM-B2 docs/r1/PLAN.md` returns only the two rows, lines 1153/1159, inside §10 which runs to line 1160). `_b2_author_rows(plan, 4)` = True, `_b2_author_rows(plan, 5)` = False; `_x5_author_row` = True. The POWER row contains `b2_instances_per_node = 4` exactly once and no other assignment of that name. The INVALID-TRIALS row names both `R1-EXAM-B1-TRUNCATION-INVALID` and `R1-EXAM-B1-MODEL-OUTPUT-INVALID`. |
| 4 | (b) the drafts are the accepted rev-2 artifacts | blob ids at `5a317b14`, `d1ac6678`, `3533b545` | **PASS for the paste target.** POWER draft is the same blob (`6d173a93…`) at all three; INVALID draft is `a700f880…` at `d1ac6678`/`3533b545` (accepted at `d1ac6678`) and the committed row matches that block. (See MINOR-5 about the hand-off review's "identical at 5a317b14" claim: the INVALID draft blob there is `4e73f579…`.) |
| 5 | (c) authorization note `approved: true` and bindings | JSON block parsed; compared to the config and the filled values; committed bytes checked by the gate | **PASS.** Exactly one JSON block; `author: "Dowling Wong"`, `phase: "b2"`, `approved: true`; every field equals the config / the expected value: rule `53018aa7…16ad`, nodes `digits_mlp, openml_credit_approval, openml_ionosphere`, Stage A table `00ab143d…975c`, amendment table `71525124…2103`, acceptance `0cda82fa…053e`, anchor `84200770…85dd`, `b1_analysis` `07cb62de…dffc`, `instances_per_node: 4`, `llm_call_cap: 80`, host `TASL-7`, `gpu_uuid GPU-ab72fb4a-…babb1`, `workers: 20`. The note draft (committed `approved: false`) has the same JSON except `approved`. The committed note bytes equal the working file at `HEAD`. |
| 6 | (d) config | `load_config`, `placeholders`, sha256 checks, comparison to the B1 config at `7912b7ff` | **PASS.** B2-required keys have no placeholders (only `.authorizations.b1` and `.d22_pick` remain, both not B2-required and not read for b2); `paper_commit` = `37282ec3…`; `authorizations.b2` = `docs/r1/authorizations/trackx_b2_20261115.md` (exists, matches the note); `b2_instances_per_node` = 4; `b1_analysis` path exists, sha256 = `07cb62de…dffc`, and its bytes are exactly the `fcf52c09` copy; anchor sha256 = `84200770…85dd` and the file's `lower`/`upper` equal the config; rule file sha256 = `53018aa7…16ad`; acceptance file sha256 = `0cda82fa…053e`; **all 31 unchanged pins/keys compared to the B1 `_d` config at `7912b7ff` are identical** (host, GPU, ctx/KV/offload, temperature, schema, rule, harness `a3fedbb`, prompts, server binary/build, Stage A paths/shas, anchor, cache_prompt, repairs, W, llm cap, workers, watchdog, timeout, sensitivity node). `exam_runner b2 --check-config` → `{"valid": true, "unresolved": [".authorizations.b1", ".d22_pick"]}` (expected). `verify_anchor_reference(cfg)` → PASS. B1 analysis content: phase `b1`, rule sha matches, `execution_label` `EVIDENCE`, `finalists ["gemma4_31b"]`, `batch_verification` dict. |
| 7 | (e) protected paths and ancestry | `git diff --name-only 37282ec3 8709dce7 -- r1/exam r1/scripts/exam_runner.py r1/scripts/llama_server_instance.py r1/scripts/llamacpp_probe.py r1/headroom/e1b_collect.py`; `merge-base --is-ancestor` | **PASS.** Empty; `37282ec3` is an ancestor of `8709dce7`. |
| 8 | (f) author commit contents | `git diff --name-only aeeab991 8709dce7` | **PASS.** Exactly `docs/r1/PLAN.md` and `docs/r1/authorizations/trackx_b2_20261115.md`; the PLAN diff is purely additive (12 added lines: the two headings + two 3-line tables; no deletions). |
| 9 | (g) push / branch state | `git rev-parse origin/ops-b2-20261115`, parent chain, `git status` | **PASS.** `origin/ops-b2-20261115` = `8709dce7`; commit parent is `aeeab991` (fast-forward, no force-push implication); the worktree was clean at the review start. (See MINOR-6 on the shared worktree switch during the review.) |
| 10 | Real author gate on the exact HEAD | `runtime.author_gate(cfg, 'b2', rule_sha)` in a clean `clone --shared` at `8709dce7`, with `digest_file` stubbed **only** for the two `/home/dowling/exam-x/work/r1_stagea_*` host tables (the rest ran for real: rule, acceptance, committed note, committed PLAN, committed B1 analysis, committed anchor, clean checkout) | **PASS.** Returned `8709dce792d45bbb5c05d9f7d239e19454efbb15`; only the two expected host paths were stubbed. `require_committed_b1_config(path, cfg, rel=B2_CONFIG_REL)` also returned `8709dce7`. Negative controls (in-memory config): n=5 and n=11 → `STOP: dated §10 B2 power-plan and invalid-trial author rows required`; cap 81 → `STOP: LLM-call cap is not author-bound`; workers 4 → `STOP: worker count differs from authorization`. On TASL-7 the two Stage A table digests must match the config (the gate will STOP otherwise); that host-only part is still to be observed at launch (see residual risk). |
| 11 | (h) Mac dry check (adapted) | `docs/r1/reports/b2_handoff_exec_20261115/dry_check.py` with only the drafts path adapted to `git -C … show origin/mac-b2-plan-20261114:…`; run at `8709dce7`; and a pre-author replay on `aeeab991`'s PLAN (paste the same first blocks) | See §2. Pre-author replay reproduces the committed `dry_check.json` **exactly**; on the run HEAD exactly two entries differ, both expected because the author rows are now committed (below). The committed script has **12 result entries (11 booleans + one empty list)**, not 13 (MINOR-4). |
| 12 | Content STOP check | whole-PLAN grep, note/config bindings, commit metadata | No contradictory count, no row in a wrong section, no unbound sha, no dirty/untracked run-HEAD file, no base disagreement. The only process items are the MINORs below. |

---

## 2. Mac dry check — the exact booleans

**Committed `dry_check.json`** (generated at `d3bd7c09`, unchanged from `aeeab991` to `8709dce7`, i.e. the
**pre-author** state): all 12 entries are true/empty.

**Run at `8709dce7` (author rows now committed), adapted only in the drafts path:**

| Entry | Run HEAD | Committed (pre-author) | Comment |
|---|---|---|---|
| `x5_row_present` | true | true | unchanged |
| `b2_rows_absent_before_author` | **false** | true | expected: the author's rows are now in PLAN §10 |
| `b2_rows_after_paste` | **false** | true | expected: pasting again duplicates the rows; `_b2_author_rows` refuses duplicates (only one row per ID) |
| `b2_rows_wrong_n_refused` | true | true | n = 5 is refused |
| `unresolved_b2_settings` | `[]` | `[]` | unchanged |
| `b2_authorization_path_resolved` | true | true | unchanged |
| `note_binds_config` | true | true | unchanged |
| `b1_analysis_sha_matches_file` | true | true | unchanged |
| `anchor_sha_matches_file` | true | true | unchanged |
| `count_within_author_cap` | true | true | n = 4 ≤ cap 10 |
| `protected_diff_empty` | true | true | unchanged |
| `paper_commit_is_ancestor` | true | true | unchanged |

The 10 unchanged entries match the committed JSON; the two differences are the correct post-author
behaviour (rows present and single). The pre-author replay (PLAN at `aeeab991` + the two first paste
blocks) reproduces the committed JSON exactly: `replay == committed dry_check.json: True`. The correct
post-author checks are covered directly: `_b2_author_rows(plan, 4)` = True, `n = 5` refused, and the
author gate returns the HEAD.

---

## 3. Findings

**No BLOCKING or MAJOR finding.** The run HEAD content, the three author items and the author gate are
all correct. The items below are process/record/accuracy issues; none changes the reviewed HEAD or
prevents the gate (conditions are stated).

| ID | Sev | Finding and evidence | Exact fix |
|---|---|---|---|
| MINOR-1 | MINOR | **The author-signing commit is authored by Claude, not the author.** `git show -s 8709dce7` gives `author/committer Claude <noreply@anthropic.com>`; every earlier author authorization/PLAN commit is authored by `Dowling Wong <wangdowling@gmail.com>` (e.g. B1 run HEAD `7912b7ff`, B1 note `8325b460`, Track P authorizations). The commit body does record the process: "The author signed in the coordinating chat on 15 Nov 2026 and asked for this commit on their behalf … Co-Authored-By: Claude …". The author gate checks the committed note bytes and `approved: true`, not the commit author, and its docstring makes the process boundary "independent review and the author's instruction". | Record the author's sign-off (the coordinating-chat message/date already quoted in the commit body) in the launch receipt/READY and in the run report, so the gate/launch record carries the author's instruction rather than only the agent's commit. If the standing rule "author commits are authored by Dowling Wong" is enforced, the alternative is to re-commit as the author — but that changes the run HEAD and would require repeating this exact-HEAD review. Nothing is armed; either path is safe. |
| MINOR-2 | MINOR | **Order: the execution plan claims the author gate is already done before this review.** `docs/r1/reports/b2_exec_20261115/PLAN.md` (2f4970e5, separate exec branch) step 1 says "author gate … (done: `GATE_PASS 8709dce7… 53018aa7… phase b2`, capture `b2_final_gate_preflight_…/gate.log`)" while the hand-off's order (§5.1) and the author's request are HEAD review → author gate → launch. The gate on the unchanged HEAD is deterministic and my independent run returns the HEAD, so no content harm; but the launch record should not claim a gate that ran before the review. | After this review is accepted, re-run the author gate on `8709dce7` (clean staged checkout; capture a fresh `gate.log`), or explicitly record the earlier run as a pre-review dry run and the post-review run as the gate. Update the plan line accordingly. |
| MINOR-3 | MINOR | **READY.txt is not in git.** The hand-off §5.1 three-way base check uses `Claude outputs/READY.txt`. It is a Mac-local file (`~/Documents/agent_paper_B/Claude outputs/READY.txt`, 15 Nov 10:30) and is not tracked in the repository. On this Mac, item 26 (B2 code unit) has `Reviewed base: 37282ec37a715feaaea48dd621ae08678424accc` and item 27 repeats `paper_commit: 37282ec3…`, so the Mac side of the three-way check passes. TASL-7 cannot read the Mac file; the exec plan itself has a dangling "OPEN QUESTION about READY.txt". | Record the Mac-side READY check (item 26 = 37282ec3) in the launch receipt (or in the author's relayed message) so the host-side three-way check is complete; do not rely on the host finding `READY.txt`. |
| MINOR-4 | MINOR | **The committed dry-check output is the pre-author state, and the "13 booleans" count is not what the script emits.** `dry_check.py`/`dry_check.json` are from `d3bd7c09` (unchanged to `8709dce7`); they are valid for the pre-author branch. At the run HEAD, `b2_rows_absent_before_author` and `b2_rows_after_paste` are necessarily false (see §2); the pre-author replay reproduces the committed JSON exactly. The committed script returns 12 entries (11 booleans + the empty `unresolved_b2_settings` list), not 13. | Either add a post-author check to `dry_check.py`/`dry_check.json` (rows present with n = 4; duplicate paste refused) or document the pre/post distinction in the review/plan, and fix the "13 booleans" description in the brief. No action on the run HEAD. |
| MINOR-5 | MINOR | **The hand-off review's "drafts identical at 5a317b14" claim is stale for the INVALID-TRIALS draft.** `B2_HANDOFF_EXEC_REVIEW_20261115.md` says "The PLAN-row drafts are identical at `5a317b14`, `d1ac6678` and `3533b545`"; the INVALID-TRIALS draft blob is `4e73f579…` at `5a317b14` and `a700f880…` at `d1ac6678`/`3533b545`. The accepted version is `d1ac6678`, and the committed row matches the `3533b545`/`d1ac6678` block, so the paste target is correct. | Correct the stale sentence in the hand-off review (docs-only; no run-HEAD change). |
| MINOR-6 | MINOR | **Shared-worktree switch / execution-branch separation.** During the review the shared worktree moved to `ops-b2-exec-20261115` @ `2f4970e5` (pushed), which adds only `docs/r1/reports/b2_exec_20261115/*`; the reviewed files are unchanged and the reviewed HEAD remains `8709dce7`. The execution plan and scripts pin `HEAD=8709dce7` and verify it at launch, but if the run checkout were created from the exec branch the gate would return `2f4970e5` instead of the reviewed HEAD. | Keep the run checkout a clean checkout at exactly `8709dce7`; keep the exec scripts on their own branch/checkout outside the run checkout; record the run HEAD in the launch receipts (the exec plan already says `staged checkout … exact HEAD 8709dce7`, so this is a confirmation, not a change). |
| NIT-1 | NIT | Config `comment` still says "DRAFT: governs nothing until the author commits R1-EXAM-RULE-X5V2 …" (stale; accepted as N9 in the hand-off review; nothing reads it). | Optionally update the comment in a later docs commit; no run-HEAD change needed. |
| NIT-2 | NIT | `authorizations.b1` and `d22_pick` remain `TODO_…`; the B2 CLI `required` list excludes them and the gate for b2 does not read them; `--check-config` reports them as unresolved. | Leave as-is for B2 (accepted by the hand-off review); they become required for B1/free-sensitivity only. |
| NIT-3 | NIT | The exec PLAN's "see OPEN QUESTION about READY.txt" reference is dangling (the 33-line plan has no such section). | Resolve with MINOR-3 (record the Mac READY check); remove or complete the reference. |

---

## 4. What was verified as correct (no action)

- **Three-way base:** code-unit review `Reviewed base:` and last `Accepted commit:` = `37282ec3…`; READY
  item 26 = `37282ec3…`; config `paper_commit` = `37282ec3…`; `37282ec3` is an ancestor of the run HEAD
  and the protected-path diff from it is empty.
- **PLAN §10:** one dated full-month `(author)` heading per row, one row per ID, byte-identical to the
  accepted first paste blocks with only the date changed, `b2_instances_per_node = 4` once, both B1 rows
  named, no B2 row outside §10; `_x5_author_row` and `_b2_author_rows` pass on the committed PLAN
  (n = 4 accepted, n = 5 refused).
- **Authorization note:** `approved: true`, one JSON block, all 16 bindings equal to the config; the
  draft differs only in `approved`; the committed bytes are the ones the gate reads.
- **Config:** no B2-required placeholders; `paper_commit`/`authorizations.b2`/`b2_instances_per_node`
  correct; B1 analysis byte-copied from `fcf52c09` and sha-bound; anchor file/sha and lower/upper bound
  and `verify_anchor_reference` PASS; rule file sha matches; all 31 other pins identical to the B1 `_d`
  config; `exam_runner b2 --check-config` valid.
- **Gate behaviour:** `author_gate(cfg, 'b2', rule_sha)` on the exact clean HEAD (two host Stage A
  digests stubbed only) returns `8709dce7…`; `require_committed_b1_config(rel=B2_CONFIG_REL)` returns the
  HEAD; negative controls (n = 5/11, cap 81, workers 4) STOP with the expected messages.
- **Git state:** `origin/ops-b2-20261115` = `8709dce7`; fast-forward from `aeeab991`; author commit
  touches only the PLAN and the authorization note; run-HEAD views were clean.
- **No STOP-worthy content inconsistency:** no contradictory count, no misplaced row, no unbound sha, no
  dirty/untracked file in the run HEAD, no base disagreement.

---

## 5. Residual risk and conditions

1. **Host-only Stage A digests.** My gate test stubbed the two `/home/dowling/exam-x/work/r1_stagea_*`
   table digests because they are on TASL-7. The real gate on the host must find `stage_a_table` and the
   amendment table with the configured shas; if either differs, the gate STOPs (as designed) and the
   launch must not proceed.
2. **READY.txt is Mac-local.** The Mac item 26 check was performed and passes; the host-side receipt must
   record it (or the author's relayed message) — see MINOR-3.
3. **Gate order.** If the exec plan's "gate done" line reflects an actual pre-review run, re-run the gate
   after this review acceptance and record that receipt (MINOR-2); the HEAD is unchanged.
4. **Author-signature attribution.** The commit body records the author's on-behalf sign-off (15 Nov); it
   should be copied into the launch receipt/READY (MINOR-1). The gate itself binds the committed
   `approved: true` note and the dated §10 rows, which are correct.
5. **Do not put this review file, or any later docs commit, into the run HEAD.** The run checkout must be
   a clean checkout at exactly `8709dce7`; adding a docs commit (including this review) before launch
   changes the HEAD and would require repeating the exact-HEAD review. Deliver this review on a separate
   docs branch/outside the run checkout.
6. Minor documentation items: MINOR-4/5/6, NIT-1/2/3 — no effect on the run HEAD.

---

## 6. Verdict

The run HEAD `8709dce792d45bbb5c05d9f7d239e19454efbb15` is accepted for the author gate. The exact HEAD,
its three author items (dated PLAN §10 rows, `approved: true` authorization note, the confirmed B1 values),
the config bindings, the protected-path rule and the three-way base all check out; the author gate run
independently (with only the two host-only Stage A digests stubbed) returns this HEAD, and the negative
controls STOP as designed.

**The author gate may be run on `8709dce7`.** Record the Mac READY item-26 check and the author's
on-behalf sign-off (from the commit body) in the launch receipt, re-run the gate after this review if a
pre-review gate run exists, and stage the run checkout at exactly `8709dce7` (not the exec branch). No
STOP-worthy inconsistency remains.

VERDICT: ACCEPTED
