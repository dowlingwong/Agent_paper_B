Reviewed base: 26519d2890a9b364de6cd4ec405db1da28d7d380

# Track X B2 executable hand-off — independent review record (15 November 2026)

Branch `mac-b2-handoff-exec-20261115`, from `a2cd540c` (the accepted B2 code unit `37282ec3` plus its review record). Unit 5 of the author's 14 Nov message: the filled `exam_b2_v2.json` (`paper_commit` 37282ec3, finalists' analysis sha `07cb62de…`, n = 4), the byte copy of the frozen B1 analysis, the B2 authorization-note draft (`approved` false), the hand-off with the marker-first start order, and a Mac dry check. Not armed. Two rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude); in round 1 the reviewer also ran `runtime.author_gate(cfg,'b2',…)` on a synthetic run HEAD (pasted PLAN rows, note with approved true) and it returned that HEAD, with only the two host-only Stage A table digests stubbed; negative controls each STOPped.
- Round 1 (`d3bd7c09`): changes requested (the marker command pointed `--status` at the run checkout's tracked STATUS.md, which would make the runner STOP after Track S was paused; the host preflight came before the marker although it needs an idle GPU).
- Round 2 (`26519d28`): **accepted**.

Accepted commit (round 2, last): 26519d2890a9b364de6cd4ec405db1da28d7d380

Notes, not blocking: `$LOCAL_STATUS` must exist before the marker step (the tool fails safely before creating the marker otherwise); define the step-3 shell variables in one place; at step 6 use only the checks of the B1 O2 document, not its marker step; READY.txt is `~/Documents/agent_paper_B/Claude outputs/READY.txt` on the Mac.

The round texts are reproduced unchanged below.

---

# Independent review: B2 executable hand-off, round 1

Reviewed commit: d3bd7c09f3ebb5e8ec1890381ec94947b43535e0
Base: a2cd540c (accepted B2 code unit 37282ec3 plus its review record), branch `mac-b2-handoff-exec-20261115`
Reviewer: freshly spawned independent agent (AI-assisted, Claude). I did not write this work. I made no changes to any
worktree and no commit to the repo. The scratch work was done in a `--shared` clone under /tmp/rev_b2exec, which has
since been removed. I had no server or SSH access and did not read any secrets.

Verdict: changes requested

There are two blocking findings, both in the start procedure (§5) of `B2_HANDOFF_EXEC_20261115.md`. The config, the
copied analysis, the note draft and the gate behaviour are all correct. The fixes are doc-only.

## Summary of checks

| # | Check | Result |
|---|---|---|
| 1 | Config values | **Pass.** See below. |
| 2 | Copied `complete_batch_verifier.json` | **Pass.** Byte-identical to fcf52c09's copy (`cmp`, same blob `e70e3163`). sha256 `07cb62de19e0797f197fc658b6043f1ad0fab1aa51e9bb36e054da514f3edffc`. Content: phase b1, rule sha `53018aa7…16ad`, EVIDENCE, `batch_verification` dict, finalists `["gemma4_31b"]`. |
| 3 | Authorization-note draft | **Pass.** Exactly one ```` ```json ```` block. `approved: false`. It binds every key `author_gate` reads for b2 (author, phase, approved, rule sha, nodes, Stage A table, amendment table and acceptance shas, anchor sha, b1_analysis sha, instances_per_node, llm_call_cap, host, gpu_uuid, workers), with values equal to the config. It says "No agent sets `approved: true`"; only the author sets it. Format matches the B1 note at 7912b7ff, plus the two B2 keys. |
| 4 | Gate dry run and synthetic run HEAD | **Pass.** Details below. |
| 5 | Procedure | **Two blocking findings (B1, B2)** and several non-blocking ones. |
| 6 | Test change | **Pass.** Justified, and B1 is not weakened. |
| 7 | Accuracy | Mostly accurate, with no "armed" claims. One unsupported figure ("about 20 h") and some ambiguous wording (non-blocking). |

### 1. Config values (`r1/scripts/configs/exam_b2_v2.json`)

Exactly nine keys changed against a2cd540c: `paper_commit`, `llm_call_cap`, `nodes`, `anchor_duplicate_reference`,
`authorizations` (b2 only), `b1_analysis`, `b2_instances_per_node`, `workers` and `b1_analysis_sha256`. The diff touches
only value lines, and the 2-space formatting and key order are preserved.

Compared with B1's config at 7912b7ff, the filled B2 config differs only in:
- `comment`;
- `paper_commit`;
- `authorizations`;
- the three B2-only keys.

So nodes, llm_call_cap 80, workers 20 and the anchor reference (source, sha, lower, upper) are B1's values exactly.

Where each value comes from:
- **paper_commit** `37282ec3…` is the `Accepted commit:` and the `Reviewed base:` line of `B2_CODE_UNIT_REVIEW_20261114.md`.
- **The protected-path diff** from 37282ec3 to HEAD is empty, and it is an ancestor.
- **b1_analysis and its sha** come from fcf52c09, the STOP 5 report §4 and the review accepted at 7bdce776.
- **n = 4** comes from the power-plan review, accepted at 5a317b14. The PLAN-row drafts are identical at 5a317b14, d1ac6678 and 3533b545.
- **The anchor** file sha is `84200770…85dd`, and lower and upper equal the file's values. `verify_anchor_reference` passes.

`load_config` accepts the file. `exam_runner b2 --check-config` gives `{"valid": true, "unresolved": [".authorizations.b1", ".d22_pick"]}`. Neither of those is in the CLI's b2 `required` list:
- `authorizations.b1` is not read for b2;
- `d22_pick` is read only by `--free-sensitivity`, which is refused in production.

The three values the author must confirm (cap 80, workers 20, anchor) are flagged in hand-off §1.3, in the §3 table and in the note draft.

### 4. Gate dry run and synthetic run HEAD

`dry_check.py` (command as given) exits with rc 0, and its output is byte-for-byte the committed `dry_check.json`. The worktree stayed clean.

**Synthetic run HEAD.** I cloned the repo (`--shared`) at d3bd7c09 and made one scratch commit with two changes:
- I pasted the first (Chinese) paste block of each accepted PLAN-row draft (from d1ac6678) at the end of PLAN §10, with the heading dated `15 November 2026`.
- I wrote `docs/r1/authorizations/trackx_b2_20261115.md` from the draft. I replaced the preamble, changed nothing else, and set `"approved": true`.

I imported `r1.exam.runtime` from the clone and set `runtime.REPO` to the clone (it already pointed there), with cwd at the clone. Then I called `runtime.author_gate(cfg, 'b2', rule_sha)` with the unmodified committed config. It **returned the run HEAD** (`4f967d7e…` = `git rev-parse HEAD`).

**What I stubbed, and nothing else.** I replaced `runtime.digest_file` with a wrapper. For exactly two paths it returns the config's own sha:
- `/home/dowling/exam-x/work/r1_stagea_20261103_t7h8/stage_a_table.json`;
- `/home/dowling/exam-x/work/r1_stagea_20261104_t7j10/stage_a_table.json`.

These are the two host-only Stage A tables. The wrapper recorded that it was called for exactly these two. Every other digest was real:
- rule;
- amendment acceptance `docs/r1/reports/OPS_O1_20261104.md`;
- the committed B1 analysis;
- the anchor.

All git checks also ran for real: the clean checkout, the committed note bytes, the committed PLAN, the committed analysis and the committed anchor.

Further checks on the same scratch clone:
- **The English paste blocks** also return the HEAD.
- **Committed `approved: false`** gives `STOP: evidence authorization does not bind author, phase and frozen rule`.
- **The note without the PLAN rows** gives `STOP: dated §10 B2 power-plan and invalid-trial author rows required`.
- **In-memory config changes** each STOP with the expected message:
  - n = 5 or n = 11: the rows check;
  - cap 81: "LLM-call cap is not author-bound";
  - workers 4: "worker count differs";
  - wrong b1 sha: "not the committed, digest-bound file";
  - wrong anchor sha: "anchor reference digest is not author-bound";
  - tabular_mlp nodes: "does not bind nodes".
- **The CLI preconditions** pass: `require_committed_b1_config(..., rel=B2_CONFIG_REL)` returns the same HEAD on the clean scratch checkout, and `verify_anchor_reference(cfg)` passes.

### 6. Test change

`test_v2_configs_bind_rule_harness_cache_and_repairs` changes in two ways:
- It adds the three B2-only keys to `differ` **only for `exam_b2_v2.json`**.
- It applies the anchor-reference file check (sha, lower and upper equal the file) to B2 as well as B1.

The B1 parametrisation runs exactly the same assertions as before.

Results with `AR_HARNESS_ROOT=AR_HARNESS_B1_ROOT=/tmp/pb/wt/harness-pin`:
- `r1/tests/test_exam_x5_rule_v2.py`, `r1/tests/test_exam_b2_*.py` and `r1/tests/test_exam_core.py`: **269 passed, 1 skipped**. The skip is the Stage A pin negative control, which needs harness 897d83c; with `R1_REQUIRE_B1_HARNESS=1` that test fails for the same reason, an environment issue only.
- `test_exam_cache_d3_guard.py`, which also names the B2 config: 14 passed.

## BLOCKING

**B1. The marker command dirties the run checkout, so B2 cannot start after Track S has been paused (§5 step 2).**

The hand-off says to run:

`python r1/scripts/b1_o2_marker.py create --phase b2 … --status <STATUS.md of the checkout> …`

`create` appends the "Track X B2 running" heading to the `--status` file. `docs/r1/STATUS.md` is tracked in the staged run checkout. Appending to it makes the checkout dirty. Then:
- `exam_runner b2` fails in `require_committed_b1_config` with `STOP: B2 committed config verification failed: checkout is not clean`;
- `author_gate` would fail the same way ("host checkout must be clean").

I reproduced this in the scratch clone:
- marker create with a scratch lock dir;
- `git status` shows ` M docs/r1/STATUS.md`;
- `require_committed_b1_config` raises the STOP above.

The failure is safe, but it comes **after** the marker has already made the watcher stop Track S.

This also departs from the B1 pattern. `B1_TASL7_O2_EXECUTABLE_DRAFT_20261107.md` (at 7912b7ff, ll. 17–30) requires:
- a separate owned local receipt STATUS file, "**not the clean executable checkout's tracked STATUS**";
- `set -C`, `umask 077` and a new `$RUN_DIR`;
- the receipt captured with `> "$RUN_DIR/marker-receipt.json"`;
- the pushed `## <date> — Track X … running` STATUS commit on the feature branch, done from a separate clean status checkout.

Draft §4.6 asks for that feature-branch STATUS (`mac-b1-20261107` or the author's branch, then `B2 done` or `B2 stopped`), and the exec dropped it.

Fix:
- give the marker command in the B1 form: a local receipt STATUS outside the run checkout, the receipt redirected into the B2 handover dir, and `python3 "$CHECKOUT/r1/scripts/b1_o2_marker.py"` from the frozen venv;
- carry over the feature-branch STATUS publication.

**B2. The host preflight needs an idle GPU, but the order puts it before the marker that frees the GPU (§5 step 1).**

§5.1 requires the host preflight to have been run before the marker. That preflight (`B1_FINAL_HOST_PREFLIGHT_INVOCATION_20261108.md` l. 11, l. 77):
- needs "a genuinely idle GPU";
- takes `gpu0.lock`;
- starts an owned anchor server;
- treats "current occupancy" as a STOP.

The marker-first order exists so that the watcher stops Track S (`trks_llm`, which holds the lease) automatically. In exactly that case, with Track S on the GPU, the preflight cannot pass before the marker, and the hand-off cannot be carried out as written.

It only works if Track S happens to be idle already. The hand-off states that as a present-tense snapshot ("at present Track S `digits_mlp` is paused"), not as a checked precondition.

Fix: split §5.1 into two parts:
- **Before the marker:** the gate, the read-only occupancy census, the handover check and the watcher check.
- **After step 3:** the GPU-holding preflight. Run it once the watcher has released the lease, `nvidia-smi` shows no compute app and `flock -n` succeeds, and have it re-reviewed for this run ID before step 4.

The alternative is to state explicitly that B2 starts only when Track S is already off the GPU. That defeats the point of marker-first.

## NON-BLOCKING

- **N1. Check the watcher before the marker.** The auto-pause relies on `trks_watch` running, but no step checks that it is alive. If it is not, step 3 waits forever, because no "priority marker seen" line will appear. The B1 handover (l. 9) also requires, before the marker:
  - an inventory of the manifest parents and existing STOP entries that the watcher will touch;
  - identification of the running collectors and `trks_llm`.

  Add both, and a bounded wait: if no "priority marker seen" line appears within about 2 polls, STOP.

  The description of the watcher itself is correct against 13badb0d §11.4:
  - 60 s poll;
  - STOP files touched beside every `manifest.json` under `r1_tracks/out`;
  - a 30 s wait loop for `--stop-file` collectors;
  - `FORCED` after 3600 s;
  - `tmux kill-session -t trks_llm`, which logs "servers stopped; lease released" only if the session existed.

  Note that after `FORCED` the watcher kills the servers anyway. So "if FORCED appears, STOP" reports a forced stop; it does not prevent one. The pre-marker collector inventory is what avoids it.
- **N2. Record P.3a before the marker.** The B1 handover (l. 11) records whether P.3a is absent, stopped or running, and establishes its safe point, **before** creating the marker. The exec checks P.3a only after the marker. Add the pre-marker record, and keep the post-marker confirmation.
- **N3. State that the `_d` marker is gone.** Say that `~/r1_locks/trackx_evidence.active` must be absent before create. The `_d` marker was retired on 14 Nov at 10:16Z (`B1_D_RUN_20261113.md` §2; `marker-retirement_after_run.json` on fcf52c09). Create uses `O_EXCL`, so it would fail safely anyway.
- **N4. Where the paste blocks are.** Hand-off §1.1 says "pasted as given in the two drafts", but this branch contains neither PLAN-row draft. The power-plan PLAN-row draft file is not named anywhere in the hand-off; §0 cites the rule proposal instead. Name both files with branch and commit: `mac-b2-plan-20261114` @ `d1ac6678` (or `3533b545`), `proposals/PLAN_ROW_R1-EXAM-B2-POWER-PLAN_DRAFT_20261114.md` and `…-INVALID-TRIALS_DRAFT_20261114.md`.
- **N5. Unsupported "about 20 h" (§4).** The B1 `_d` evidence does not support "B1 ran 260 roots in about 20 h":
  - launch was 2026-11-13T13:53:53Z;
  - the server intervals in `batch_state.json` span 14:01Z to 03:37Z on 14 Nov, about 13.6 h (13.5 h summed).

  About 20 h is the time from launch to marker retirement, which includes the post-run work. Correct the figure or give its source.

  "The per-proposal audits use 10 seeds, as B1's used 4" should read "where B1's used 4".
- **N6. "Same lease guardian" (§5.4).** B1 has no separate lease guardian; the runner takes `gpu0.lock` itself (`b1_lease.acquire`, non-blocking), and an external holder would trip "B1 GPU lock is held". Say instead "the same launch wrapper and frozen-venv `$PY` as `_d`, with no other holder of `gpu0.lock`".
- **N7. Analysis command context (§4).** State that the analysis runs from the clean staged run-HEAD checkout with the same `AR_HARNESS_ROOT`. `verify_b2_batch` calls `author_gate(cfg,'b2')`, which needs the clean committed checkout and cwd at its root. B1 `_d` used `$PY -B -m r1.exam.analyze …`.
- **N8. Draft items not carried over** (by reference or omission):
  - **Draft §4.1:** the three-way base check (review `Accepted commit:` = `Reviewed base:` = `Claude outputs/READY.txt`). I verified the first two agree, at 37282ec3.
  - **Draft §4.5:** nothing of B1's runs `_a` to `_d` is moved, overwritten or deleted (R1-EXAM-B1-NO-DELETION-07NOV).
  - **Draft §2:** no Track G node unless the author adds one.
- **N9. Small items in the code and config.**
  - In the test, the `else:` branch after `if name in ('exam_b1_v2.json', 'exam_b2_v2.json')` can no longer run. Optionally, also assert for B2 that `digest_file(REPO/cfg['b1_analysis']) == cfg['b1_analysis_sha256']` and `b2_instances_per_node == 4`.
  - The B2 config `comment` still has B1-oriented wording ("DRAFT: governs nothing…", "the count for TASL-7 is set in the B1 authorization"). Nothing reads it.
- **N10. Snapshot claims.** "TASL-2 is unreachable" and "Track S `digits_mlp` is paused" are snapshots I cannot verify. Phrase them as things to re-check at B2 start.

## Verified as correct (no action)

- **The marker tool command** `--phase b2` matches the code. `PHASE_HEADINGS['b2']` = "Track X B2 running", and `--lock-dir`, `--status`, `--run-id`, `--head` and `retire --receipt` all match.
- **The start command:** `python -m r1.scripts.exam_runner b2 --config r1/scripts/configs/exam_b2_v2.json --out /home/dowling/exam-x/work/b2_<run ID>`. It runs from the checkout root (required by `require_committed_b1_config`); the output is a fresh direct child of `work_dir`; the runner takes the lease.
- **The analysis command** matches the `analyze` CLI (`b2 --batch --config --rule --rule-sha256` goes to `b2_summary_verified`, which uses `verify_b2_batch`).
- **The protected-path rule** matches `ExamRunner.__init__` (ancestor check plus the same five paths).
- **Root counts:**
  - gemma4_31b is switchable and rank 0;
  - its thinking-on grammar was not disabled, since B1 ran its thinking-on roots;
  - the b2 branch uses `cfg['nodes']` for every mode and seeds 9011–9014;
  - so 12 primary and 12 descriptive roots, 24 in total.
- **"B1 thinking-on D28 failed"** is confirmed by `thinking_on_d28.pass = false` in fcf52c09's `b1_manifests.json`.
- **Run HEAD and staging** match the `_d` pattern: a new `ops-b2-<date>` branch, an exact-HEAD review, the real gate, the `b1_paper_final_<HEAD>/paper` staging, harness `a3fedbb` and the frozen venv.
- **Nothing is armed.** The author items (the PLAN rows, the note with `approved` set to true, the three value confirmations, the timing) are stated as the author's. The commit and documents use "not armed" language throughout.

---

# Independent review: B2 executable hand-off, round 2

Reviewed commit: 26519d2890a9b364de6cd4ec405db1da28d7d380
Previous round: d3bd7c09 (round 1, changes requested; `REVIEW_B2EXEC_round1.md`)
Reviewer: the same independent agent as round 1 (AI-assisted, Claude). I made no changes to any worktree, did not
commit or push, had no server or SSH access, and read no secrets.

Verdict: accepted

## Scope

`git diff --name-only d3bd7c09 26519d28` lists only `docs/r1/proposals/B2_HANDOFF_EXEC_20261115.md`. The following are byte-unchanged since round 1, so the round-1 results stand:
- the config;
- the copied analysis (sha `07cb62de…`);
- the note draft;
- the dry check;
- the test change.

Those round-1 results were:
- `author_gate` returned the synthetic run HEAD, with only the two `/home/dowling` Stage A table digests stubbed;
- 269 tests passed and 1 was skipped (harness-pin environment).

The worktree is at 26519d28 and clean.

## Blocking findings from round 1

- **B1, fixed.** §5 step 3 now follows the B1 O2 pattern:
  - a new `RUN_DIR`;
  - `umask 077`, `set -C`, and a check that the checkout is clean;
  - `python3 "$CHECKOUT/r1/scripts/b1_o2_marker.py" create --phase b2 … --status "$LOCAL_STATUS" … > "$RUN_DIR/marker-receipt.json"`.

  It warns explicitly against the tracked `docs/r1/STATUS.md` and quotes the exact runner STOP that I reproduced in round 1. Step 4 restores the feature-branch STATUS publication from a separate clean checkout (draft §4.6), and step 9 adds `B2 done` / `B2 stopped`. The flags match `b1_o2_marker.py` (`--phase b2`, `--lock-dir`, `--status`, `--run-id`, `--head`; `retire --receipt`).
- **B2, fixed.** The host preflight and the handover check moved to step 6:
  - they come after step 5 (watcher observed, `nvidia-smi` shows no compute app, `flock -n gpu0.lock` succeeds, P.3a paused or absent);
  - they come before the start in step 7;
  - they are re-reviewed for this HEAD and run ID;
  - if either fails, the procedure STOPs with the marker preserved and nothing retried.

  This is consistent with the preflight's need for an idle GPU and the lock (`B1_FINAL_HOST_PREFLIGHT_INVOCATION_20261108.md` l. 11, 77).

## Non-blocking findings from round 1

| Item | Status |
|---|---|
| N1 watcher check and inventory | Done (step 2). `trks_watch` must be running; collectors (the exact `pgrep` pattern of runbook §11.4), `trks_llm`, manifest parents and STOP entries are recorded. Do not create the marker if a collector might be FORCED. FORCED, an unexpected path or a lost identity is a STOP (step 5). The watcher description matches 13badb0d §11.4, including "continues anyway" after FORCED. |
| N2 P.3a before the marker | Done (step 2), and confirmed again after the marker (step 5). |
| N3 `_d` marker absent | Done (step 2). |
| N4 PLAN-row drafts named | Done (§0). The rev-2 files are identical at 5a317b14, d1ac6678 and 3533b545 (checked in round 1). `reviews/B2_INVALID_TRIALS_ROW_REVIEW_20261114.md` exists at 3533b545. |
| N5 timing | Done. About 13.6 h is the server span (13.5 h summed). About 20 h is launch (13 Nov 13:53Z) to marker retirement (14 Nov 10:16Z), which is 20.4 h. "Where B1's used 4" is fixed. |
| N6 lease wording | Done. "The runner acquires gpu0.lock itself and passes it to its servers and workers" matches `runtime.py` l. 786, 912 and 956 (`pass_fds`). |
| N7 analysis from the staged checkout | Done. |
| N8 draft carry-overs | The three-way base check including READY.txt is done (step 1). The `Reviewed base:` line and the `Accepted commit:` line agree at 37282ec3, which I verified; READY.txt is Mac-local, so I could not see it. "B1 runs are never moved" is done (step 8). The Track G omission remains; it is trivial. |
| N9 test `else` branch, config comment | Left as they are, by the author's choice. Accepted; neither affects behaviour. |
| N10 snapshot claims | Done (step 2 re-check wording). |

The language is accurate: the hand-off is "not armed", no agent sets `approved: true`, runs the gate or launches anything,
and every author item is left to the author.

## NON-BLOCKING (new, optional)

- **R2-N1.** `b1_o2_marker.create` opens `--status` with `O_APPEND` and without `O_CREAT`, so `$LOCAL_STATUS` must
  already exist as an owned regular file. The B1 draft says "existing B1-owned local receipt STATUS file". If it is missing,
  the tool fails **before** the marker is created, which is safe. Saying so in step 3 avoids a pointless STOP.
- **R2-N2.** Step 3 uses `CHECKOUT`, `RUN_DIR`, `LOCAL_STATUS` and `RUN_ID` without setting them in one place. `RUN_ID` is in §2.
  It would help to list them, with `CHECKOUT` = the staged `b1_paper_final_<FULL_HEAD>/paper`.
- **R2-N3.** Step 6 points to `B1_TASL7_O2_EXECUTABLE_DRAFT_20261107.md` as the handover check, but that document also
  contains marker creation. One clause such as "its checks only; marker and STATUS are steps 3–4 here" would remove the
  ambiguity. The re-review of step 6 for the run ID would catch it either way.
- **R2-N4.** The path of READY.txt is not given in step 1 (`Claude outputs/READY.txt` in the B1 pattern).

Accepted commit: 26519d2890a9b364de6cd4ec405db1da28d7d380
