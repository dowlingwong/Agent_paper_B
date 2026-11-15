# Track X Stage B2 hand-off — executable version (15 November 2026)

**Status.** AI-assisted (Claude, Mac-local agent). This replaces `proposals/B2_HANDOFF_DRAFT_20261114.md`
(`mac-b2-handoff-20261114` @ `2120956c`; the draft stays as history). It applies the author's instruction of 14 Nov to
advance B2 and fills every value the draft left open from accepted work. It is **not armed** until the author has
committed the three author items of §1 on the run HEAD. No agent sets `approved: true`, runs the author gate or
launches anything.

## 0. Accepted inputs (all independently reviewed)

| Item | Value | Record |
|---|---|---|
| B1 run, HEAD | `7912_20261113_d`, `7912b7fffb4c1adeb39688bdb3852a919bdc71c8`; normal completion, 260 roots | `reports/B1_D_RUN_20261113.md` (`mac-b1-20261107` @ `fcf52c09`) |
| STOP 5 finalists (x5_rule_v2, rule sha `53018aa7…16ad`) | **`[gemma4_31b]`**: the only eligible candidate with D28 pass. With one finalist, gemma4_31b is the pick whatever its B2 score; there is no second proposer | `reports/B1_STOP5_FINALISTS_20261114.md`; review `reviews/B1_STOP5_FINALISTS_REVIEW_20261114.md`, accepted at `7bdce776` (`mac-b2-plan-20261114`) |
| `b1_analysis`, `b1_analysis_sha256` | `docs/r1/reports/b1_d_20261113_evidence/complete_batch_verifier.json`, `07cb62de19e0797f197fc658b6043f1ad0fab1aa51e9bb36e054da514f3edffc` (the run's verified complete-batch analysis; byte-copied onto this branch from `fcf52c09`) | as above |
| `b2_instances_per_node` | **4** (seeds 9011–9014), by the pre-declared precision rule; n_j = 4 / 3 / 3; under the author's cap of 10 | `proposals/B2_POWER_PLAN_RULE_20261114.md`; review `reviews/B2_POWER_PLAN_REVIEW_20261114.md`, accepted at `5a317b14` |
| Invalid-trial rules for B2 | R1-EXAM-B1-TRUNCATION-INVALID and -MODEL-OUTPUT-INVALID extended unchanged | `proposals/PLAN_ROW_R1-EXAM-B2-INVALID-TRIALS_DRAFT_20261114.md`; review accepted at `d1ac6678` |
| B2 code (reviewed base) | `37282ec37a715feaaea48dd621ae08678424accc` | `reviews/B2_CODE_UNIT_REVIEW_20261114.md` (`mac-b2-code-20261114`), `Accepted commit: 37282ec37a715feaaea48dd621ae08678424accc`; report `reports/B2_CODE_UNIT_20261114.md` |

## 1. What the author commits on the run HEAD (three items)

1. **PLAN §10, two rows**, pasted as given in the two drafts (one paste block per row: either the Chinese or the
   English one). Use a dated `### … (author)` heading with the commit date, written as a full month name or ISO date.
   The B2 author gate reads them: `R1-EXAM-B2-POWER-PLAN` must contain `b2_instances_per_node = 4` exactly once;
   `R1-EXAM-B2-INVALID-TRIALS` must name both B1 rows. Only one row per ID may exist in §10.
2. **The B2 authorization note** `docs/r1/authorizations/trackx_b2_20261115.md`. The draft
   `proposals/TRACKX_B2_AUTHORIZATION_NOTE_DRAFT_20261115.md` carries the JSON with every binding filled. The author
   copies it to that path and sets `"approved": true`. If the path changes, `authorizations.b2` in the config changes
   with it.
3. **Confirm or change three values** taken over from B1 and bound by the note: `llm_call_cap` 80, `workers` 20,
   anchor reference `docs/r1/reports/B1_ANCHOR_DUPLICATE_REFERENCE_20261107.json` (`84200770…85dd`). Changing any of
   them changes both the config and the note.

## 2. The branch and the run HEAD

- **Branch `mac-b2-handoff-exec-20261115`**, from `a2cd540c` = the reviewed code base `37282ec37a715feaaea48dd621ae08678424accc` plus its review record (later commits on the code branch may only add review records). Commits:
  - the byte copy of `complete_batch_verifier.json` at the `b1_analysis` path;
  - the filled `r1/scripts/configs/exam_b2_v2.json` (§3);
  - the authorization-note draft and this hand-off.
- **Protected-path diff.** `paper_commit` = `37282ec37a715feaaea48dd621ae08678424accc`. `git diff --name-only 37282ec37a715feaaea48dd621ae08678424accc <run HEAD> -- r1/exam r1/scripts/exam_runner.py r1/scripts/llama_server_instance.py r1/scripts/llamacpp_probe.py r1/headroom/e1b_collect.py` must be empty; this branch touches only docs and the config.
- **Run HEAD.** The author's commit(s) of §1 on top of this branch, on a new branch `ops-b2-<YYYYMMDD>`, pushed without force. Exact-HEAD independent review of that HEAD, then the real author gate on it (`runtime.author_gate(cfg, 'b2', rule_sha)` must return that HEAD). The run ID is `<first four hex of run HEAD>_<UTC date>_b2`; the output tree is `/home/dowling/exam-x/work/b2_<run ID>`, a fresh direct child of `work_dir`.
- **Staging on TASL-7** as for B1:
  - the clean checkout `b1_paper_final_<FULL_HEAD>/paper` (B2 name);
  - the harness at `b1_harness_offline_stage_20261107_a/harness` (`a3fedbb`);
  - the frozen venv of hand-off `_d` §0.3. If the venv changed, STOP.

## 3. The filled configuration (`r1/scripts/configs/exam_b2_v2.json`)

| Key | Draft value | Filled |
|---|---|---|
| `paper_commit` | `TODO_REVIEWED_M2_COMMIT` | `37282ec37a715feaaea48dd621ae08678424accc` |
| `nodes` | `TODO_VERIFY_D28_DIGITS_OR_TABULAR`, credit, ionosphere | `digits_mlp`, `openml_credit_approval`, `openml_ionosphere` (B1's nodes) |
| `llm_call_cap` | `TODO_AUTHOR_LLM_CALL_CAP` | 80 (as B1; author confirms, §1.3) |
| `workers` | 4 | 20 (as B1; author confirms) |
| `anchor_duplicate_reference` | `TODO_VERIFY_ON_HOST` | B1's: source, sha `84200770…85dd`, lower 0.4239, upper 0.5800 |
| `b1_analysis`, `b1_analysis_sha256` | `TODO_VERIFY_ON_HOST` | §0 |
| `b2_instances_per_node` | `TODO_AUTHOR_B2_POWER_PLAN` | 4 |
| `authorizations.b2` | `TODO_AUTHOR_B2_V2_AUTHORIZATION_NOTE` | `docs/r1/authorizations/trackx_b2_20261115.md` |
| `d22_pick` | `TODO_AUTHOR_D22_PICK` | unchanged; read only by the schema-free sensitivity, which the B2 code refuses in production (separately gated after X.7 (a)) |

Unchanged and bound by sha:
- host TASL-7 and GPU `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`;
- harness `a3fedbb`, `cache_prompt: false`;
- context 32,768, q8_0 KV, temperature 0.2, `manager_proposal/v1`, W = 20, `vary`;
- the Stage A tables and acceptance record;
- llama.cpp `620d222` (binary sha `b70f4882…7d8b`);
- the rule sha `53018aa7…16ad`.

The B2 seeds come from the code, not the config: instances 9011–9014, final-Y and per-proposal audits 9201–9210. The config's `instance_seeds`/`audit_seeds` are B1's and are not read for b2.

### 3.1 Dry check on the Mac

`reports/b2_handoff_exec_20261115/dry_check.py` (output `dry_check.json`, all true or empty) checks the package
without the host:
- the X5 row is present;
- the B2 rows are absent now, and present after pasting the first paste block of each accepted draft (heading dated 15 November 2026), with n = 4 accepted and n = 5 refused;
- no B2 setting is unresolved;
- the note draft, with `approved` set to true as the author would, binds exactly the filled config;
- the B1 analysis and anchor files match their shas;
- n is within the author's cap;
- `paper_commit` is an ancestor, and the protected-path diff is empty.

Host-only checks (the Stage A files on TASL-7, the clean committed run HEAD, the harness checkout) and the real author gate are run on the host, not here. `r1/tests/test_exam_x5_rule_v2.py::test_v2_configs_bind_rule_harness_cache_and_repairs` is updated for the filled B2 config: the B2-only keys may differ from the portal config, and the anchor reference is checked against its file as for B1.

## 4. What B2 runs

- **Primary.** gemma4_31b, thinking off, on 3 nodes × 4 instances = **12 roots**, W = 20, LLM cap 80. At the end of each root the incumbent's editable files are audited on 9201–9210, and `final_y` is the mean of the ten metrics.
- **Descriptive top-3 rerun.** gemma4_31b is switchable and ranked first, so the runner also reruns it thinking-on, descriptive only, on the same grid: another **12 roots**. It never changes the pick. gemma4_31b's B1 thinking-on D28 failed; the rerun is still run by the code as reviewed.
- **Total: 24 roots.** For scale, B1 ran 260 roots in about 20 h. The per-proposal audits use 10 seeds, as B1's used 4 (code unit report §6).
- **Analysis after the run.** `python -m r1.exam.analyze b2 --batch <batch> --config r1/scripts/configs/exam_b2_v2.json --rule r1/exam/rules/x5_rule_v2.yaml --rule-sha256 53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad`. It ranks only after the grid verifier passes. With one finalist the "rule top" is gemma4_31b; the B2 report gives its per-node final audited Y and the descriptive rerun.

## 5. Start order — the marker first

The author asked that B2 create its marker first, so that the Track S watcher pauses automatically. The watcher (`trks-watch`, runbook §11.4) polls every 60 s for `~/r1_locks/trackx_evidence.active`. When it sees the marker it does three things:
- touches `STOP` in every Track S phase directory;
- waits for the LLM collectors to stop (up to 1 h, then logs `FORCED`);
- kills `trks_llm` ("servers stopped; lease released").

1. **Before the marker:**
   - the run HEAD has been reviewed and the author gate passed on it;
   - the read-only TASL-7 occupancy check, the host preflight (B1 pattern, new absent `--out` and capture directory) and the handover check have been re-reviewed for this HEAD and run ID;
   - no B1, B2 or Track P job is running, and the Track P marker is absent;
   - no other user's job would be preempted (R1-TASL7-AGENT-OCCUPANCY-07NOV).
2. **Create the marker** with the reviewed tool:
   `python r1/scripts/b1_o2_marker.py create --phase b2 --lock-dir ~/r1_locks --status <STATUS.md of the checkout> --run-id <run ID> --head <run HEAD>`.
   Keep its receipt in the B2 handover directory. It writes the STATUS heading "Track X B2 running".
3. **Wait for the watcher**, as recorded in `~/r1_tracks/logs/watch.log`:
   - `priority marker seen (…/trackx_evidence.active): pausing`;
   - then either `servers stopped; lease released`, or no Track S collector or server running at all (at present Track S `digits_mlp` is paused and TASL-2 is unreachable);
   - if `FORCED` appears, STOP and report.

   Then confirm on the host: `nvidia-smi` lists no compute app, `flock -n ~/r1_locks/gpu0.lock true` succeeds, and P.3a is at its safe pause.
4. **Start B2** from the staged checkout root:
   `python -m r1.scripts.exam_runner b2 --config r1/scripts/configs/exam_b2_v2.json --out /home/dowling/exam-x/work/b2_<run ID>`, under the same lease guardian and environment as B1 `_d` (`AR_HARNESS_ROOT` = the staged harness; `LLAMACPP_CACHE_PROMPT` unset). The runner acquires `~/r1_locks/gpu0.lock` itself.
5. **During B2**, Track S and Track P stay paused. Any STOP is preserved and reported, never retried. The invalid-trial classes do not stop the run; everything else in hand-off draft §6 does. An existing production root is never resumed.
6. **After the last B2 job**, or when B2 is stopped for good, retire the B2 marker with `b1_o2_marker.py retire` and its receipt, under its own reviewed post-run unit. Track S resumes by hand ("marker gone: resume by hand …"). If a marker does not match its receipt, STOP.

## 6. What to send back

- the run ID and the run HEAD;
- the HEAD review;
- the author-gate receipt;
- the preflight and handover receipts;
- the marker receipt and the watcher log lines;
- the first monitor capture;
- at the end: `b2_manifests.json`, `batch_state.json`, the verified analysis output, and per candidate, mode and check the invalid-trial counts (`proposal_journal.rejected_by_check`).

B2's result goes to a report with the review loop (STOP 6: the reviewer recomputes every table from the manifests). The author then decides X.7. Sweep 2 remains separately gated.
