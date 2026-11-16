Reviewed base: c3134bf08629a1f93f2bdc37afe53b70a5a11592

# S2-M1 sweep-2 authorization draft — independent review record (16 November 2026)

Branch `mac-s2-m1-auth-20261116` from `author-sweephost-20261116` @ `fd275c53`. Unit: `proposals/C3_SWEEP2_AUTHORIZATION_NOTE_DRAFT_20261116.md` (draft only, `approved: false`). Sweep-2 work plan unit S2-M1. One freshly spawned independent reviewer agent (AI-assisted, Claude), three rounds.
- Round 1 (`a19127be`): REVISE. 3 MAJOR: "exactly as in the exam" was false, because the exam ran at context 32,768; the noise-source pin is not enforced by the S2-C2 wrapper; the B.2 audits' PLAN preconditions were not listed. 7 MINOR.
- Round 2 (`2777512f`): REVISE. 1 MAJOR: the context was fixed at 16,384 in one place and offered as a placeholder in another. 3 MINOR.
- Round 3 (`c3134bf0`): ACCEPT. One optional nit is left as is: line 217's "build 11669" lacks the "expected" qualifier that line 86 gives it.

Accepted commit (last round): c3134bf08629a1f93f2bdc37afe53b70a5a11592

The round texts are reproduced unchanged below.

---

# Review R1 — S2-M1 draft authorization note for C3 sweep 2 and its B.2 audits

- Reviewer: independent (Claude). I did not write this work. Read-only; scratch only under /tmp/pb/rev_s2m1/.
- Reviewed base: `a19127be8210ee6b45b08c4e1bad9c87ef7014f7` (branch `mac-s2-m1-auth-20261116`, one commit on
  `author-sweephost-20261116` @ `fd275c53`).
- File: `docs/r1/proposals/C3_SWEEP2_AUTHORIZATION_NOTE_DRAFT_20261116.md` (182 lines).
- Sources read:
  - PLAN at `fd275c53`.
  - `c3_sweep1_20261027.md`, from `gh/main`, because it is not on the author branch.
  - The runbook from `gh/docs/runbooks-16nov` @ `a2789ea6`. It is not in the worktree, although the task said it was.
  - The Track X B2 draft and the Track X B2 authorization.
  - `c3_sweep_deepthought.json` on `fd275c53`, `gh/main`, `ccb4712` and `int-main-sweep2-20261116`.
  - `e1b_collect.py`, the registry, `gemma4_31b.json` and `exam_b2_v2.json`.
  - `r1/exam/runtime.py`, `r1/scripts/exam_runner.py` and `r1/scripts/llama_server_instance.py`.
  - The B2 run handback (`gh/ops-b2-exec-20261115`).
  - Cluster ref `gh/sweep2-cluster-20261116` @ `235c9e5f`: `s2_c2_lib.py`, `render_jdl.py`, `spec.example.json`, the dry-run JDL, the S2-C1, S2-C2 and S2-C4 units, and the S2-C2 and S2-C4 reviews.
  - Integration branch `int-main-sweep2-20261116` (`r1/scripts/c3_label_sweep.py`, `r1/c3/analysis_guard.py`, `HARNESS_PIN_C3`).

VERDICT: REVISE

Three MAJOR findings. They are cheap to fix and none needs a decision from the agent. Most values are exact.

## Findings

### 1. MAJOR — "Server flags (exactly as in the exam)" is false for context and for several flags; the conflict is not flagged
**Location:** draft lines 78–82 ("Server flags (exactly as in the exam)… context 16,384, full offload (`-ngl 99`)… `--no-webui`"). Also the cross-proposer list, lines 117–129.

**Evidence:** Track X B2 did not run the pick at 16,384.
- `r1/scripts/configs/exam_b2_v2.json` has `"ctx_size": 32768`.
- `r1/exam/runtime.py:215` refuses any `ctx_size` other than 32768.
- `exam_runner.py:421` starts the server at `16384 if cpu_pool_only else 32768`.
- The B2 EVIDENCE run's `handback/batch_state.json` records `server_intervals` for gemma4_31b, mode `off`, `"context": 32768`.

Other exam flags also differ from what the draft lists.
- The exam server argv (`llama_server_instance.py:261`, `EXAM_SERVER_ARGS`) is `-ngl 999 -c 32768 -np 1 --jinja --cache-type-k q8_0 --cache-type-v q8_0 -lv 4 --chat-template-kwargs {"enable_thinking":false}`.
- That argv has no `--no-webui`.
- The S2-C2 wrapper uses `-ngl 99 -c 16384`, adds `--no-webui` and omits `-np 1`. The server-slot default of the image build (build 11669) is therefore not the exam's single slot.

The 16,384 value does come from PLAN: R1-MAIN-PROPOSER (c) says "context 8,192 against 16,384", and runbook §0 copies it under "exactly as in the exam". The S2-C2 validator hard-codes 16384 with the message "exam setting". So the upstream texts contradict the exam's actual setting, and the draft repeats the contradiction without flagging it.

Two consequences:
- The author would sign an EVIDENCE note that asserts exam identity when the stack is not identical.
- S2-C3, which replays B2's roots "with B2 settings", may check a different context from the one sweep 2 runs.

**Fix (no decision by the agent):**
- Drop "exactly as in the exam". List the job's actual argv values and cite S2-C2 `spec.example.json` and R1-MAIN-PROPOSER (b)/(c).
- Add a note for the author: B2 ran at 32,768 with `-np 1`, `-ngl 999` and no `--no-webui`. PLAN (c) and the S2-C2 validator say 16,384. The author either confirms 16,384 as a disclosed selection→deployment difference, or amends (c) and S2-C2 to 32,768.
- Ask that S2-C3 run at the sweep-2 context and slot settings. (g)4's prompt-length re-measure is the relevant check.
- Add a short "differences from the selection exam" list: host 4090→L40S; context; `-np`; `-ngl`; `--no-webui`; the llama-server binary (exam "build 1" on TASL-7, image "build 11669", same commit); container; paper commit.

### 2. MAJOR — The noise-source pin is not carried out by the accepted S2-C2 wrapper; the Notes do not say so
**Location:** draft lines 91–92 (noise source "as in sweep 1"); Notes §1 (the list of wrapper gaps); line 140 ("Check all pins … against the job specs").

**Evidence:** Sweep 1 bound the noise source through collection.
- `c3_label_sweep.py` (int-main), `sweep()`, passes `--e1-summary <noise_source.path>`.
- It writes `c3_label_sweep.noise_source` into the extra manifest.
- `r1/c3/dataset.py:395–403` refuses a table whose manifest `noise_source` differs from the index's.

The S2-C2 wrapper does none of this.
- `collector_argv` passes no `--e1-summary`.
- Its `c3_label_sweep` extra manifest has no `noise_source`.
- The spec schema has no `noise_source` field, so the pin cannot be "checked against the job specs".

So `e1b_collect.py:475` falls back to `max(results/r1/pilot/E1_*T*Z/summary.json)`, which is `E1_20261022T214606Z` on main.
- That summary has no `openml_climate`, so climate collection would hit a KeyError in `node_noise` (collector rc≠0, STOP).
- The other nodes would silently get E1 noise instead of the D28_REPAIR composite (`3d12ce05…`, which matches).
- The draft presents the pin as in force and lists only the liveness and parse gates as wrapper gaps.

**Fix:**
- Add a Notes item: S2-C2 must pass `--e1-summary results/r1/noise/D28_REPAIR_20261027/summary.json`, record `noise_source {path, sha256}` in the manifest, and carry it in the spec so it is validated, before EVIDENCE.
- Or state that the pin is unenforced until that change is made.
- Optionally restore sweep 1's wording: "bound through collection, sweep index, table construction and offline evaluation".

### 3. MAJOR — The B.2 audits are in scope, but their PLAN preconditions are not listed
**Location:** "B.2 audits" (lines 100–105), Scope (line 133), Notes §1 and §3.

**Evidence:**
- R1-MAIN-PROPOSER (b) runs sweep-2 audits "under the R1-SWEEP1-CLASSIFY and R1-B2-DECOUPLE rules".
- R1-B2-DECOUPLE says "B.2 … does not start".
- R1-B2-REPLAY-GO says that rule is lifted only by the author's ruling **e2**, after the e1 replay shows zero differences, "together with the B.2 authorization addendum".
- R1-SWEEP1-CLASSIFY requires the audit classification to be fixed from a matching authorization, with tests, and reviewed.

Whether "does not start" also binds sweep-2 audits is unclear, and the PLAN leaves that to the author. The draft neither cites R1-B2-REPLAY-GO nor raises the question. It also authorizes audits that have no wrapper (S2-C7 does not exist; Notes §3), no audit-code commit, no workers, no estimate, and no confirmation of the CPU image.

**Fix (no decision by the agent):**
- Add a Notes §1 item: the audits start only after S2-C7 is accepted and the audit path (M3 `r1/c3/audit.py` with the R1-SWEEP1-CLASSIFY audit-classification fix and tests) is on main.
- Add that the author either rules that R1-B2-DECOUPLE's "does not start" or e2 does not apply to sweep-2 audits, or lifts it.
- Offer the author the sweep-1 precedent: keep the audits in this note behind those conditions, or move them to a later addendum with their own pins.
- Add R1-B2-REPLAY-GO to the rows used.

### 4. MINOR — The sweep-1 config SHA is given without a ref, and the author-branch copy differs
**Location:** line 84.

**Evidence:**
- `c3_sweep_deepthought.json` has `2fa891f4…` on `gh/main`, `ccb4712` and `int-main-sweep2-20261116`. That value is correct and matches c3_sweep1.
- On the authority branch `fd275c53` (the worktree) the file is the unfilled DRAFT, `8f1add22…`. It still lists `openml_blood_transfusion`.

**Fix:** write "as on `main` (`60ec768e`) / sweep-1 paper pin `ccb4712`". Note that the copy on the author branch is the pre-fill draft and is not used.

### 5. MINOR — Harness pin: the location claim is wrong and the pin's source is not cited
**Location:** lines 62–63; Notes §1, (g)2.

**Evidence:**
- "`r1/scripts/HARNESS_PIN_C3` on that commit carries the same value" is not true at any authority or main ref. It is `897d83c8` on `fd275c53` and `6adf3859` on `main`. Only the not-yet-accepted `int-main-sweep2-20261116` (`bc164b2e`) has `a3fedbbd`.
- No PLAN row fixes `a3fedbb` exactly as sweep 2's pin:
  - R1-EXAM-B1-HARNESS-PIN covers B1 and B2 only.
  - R1-MAIN-PROPOSER (c) describes "the next pin, which carries … `a3fedbb` … and any R1-HARNESS-NEXT-PIN fixes".
  - The source is the author's 16 Nov answer to the S2-M2 question, recorded in the `bc164b2e` message, together with S2-C2 M1.
- (c) also requires "a check that the harness defaults used by the sweep are unchanged" as part of prerequisite 3. The draft does not mention it.
- The (g)2 conclusion is correct: (g) is the sweep-2 order, and R1-EXAM-B1-HARNESS-PIN's "does not wait for sweep-1 B.2" is scoped to B1 and B2. The phrase "Sweep 2 uses the next pin `a3fedbb`" should still say that `a3fedbb` is used directly, as in B1 and B2, and not merged into `r1`.

**Fix:**
- Write "`HARNESS_PIN_C3` on `<main commit>` (S2-M2) carries the same value".
- Cite the author's 16 Nov S2-M2 answer and S2-C2 M1 for the pin.
- Add the (c) harness-defaults check to the Notes.

### 6. MINOR — Notes (g)4: the gate description is partly wrong and understates what the wrapper lacks
**Location:** lines 165–167.

**Evidence:**
- In `c3_label_sweep.py`, `liveness()` with `min_live_nodes` runs before collection.
- `max_parse_failure_rate` is applied after each sweep's collection, in `collection_gates`. That function also checks:
  - the expected root count;
  - the failure records;
  - that the manager is LLM-backed;
  - that LLM proposals were demonstrated.
- The S2-C2 wrapper applies none of these. It only checks the collector's return code.
- The core claim, that the wrapper calls the collector directly with no liveness or parse gate, is correct.

**Fix:** write "the liveness gate before collection and the collection gates (root count, failures, LLM-backed, parse-failure rate ≤ 0.2) after it". The rest of the item is correct.

### 7. MINOR — The R1-BX-D8 mechanism is misstated, and the seal step's checks are overstated
**Location:** lines 111–115.

**Evidence:** the lock rule itself is stated correctly. Two supporting statements are not.
- **The readers.** "Until then the readers refuse sealed paths" does not match the code. `analysis_guard.refuse_sealed` refuses only paths with an `r1_sealed` component. The S2-C2 seal root `/ceph/srv/dwong/paperb/sweep2/` has none, and `_sealed_target` refuses `r1_sealed` explicitly. The PLAN mechanism is that every reader refuses to run without a PLAN line `R1-BX-D8-CONFIRM` (`guard_table` / `require_d8_confirmation`). Runbook §0 says "(`refuse_sealed` paths)", which differs from S2-C2's layout.
- **The seal step.** It "verifies run, chunk, label, image and host". In fact `seal()` checks run and chunk equality, that the label is in {ENGINEERING_ONLY, EVIDENCE}, that the image digest starts with `ghcr.io/`, that a host fqdn is present, and the transferred SHA256SUMS. It does not compare the digest with the authorized one, or the host with the class.

**Fix:**
- Use the row's words for the reader mechanism.
- Mention to the author that the runbook's `refuse_sealed` paths differ from S2-C2's layout.
- Say that the seal step checks presence and form, so the authorized-digest and host-class match comes from the job record checks at pre-launch.

### 8. MINOR — The CPU pin is described as a job requirement, but it is an in-job check
**Location:** lines 54–56.

**Evidence:**
- The JDL requirements (`render_jdl.py`, dry-run JDL) are CloudSite, GPUs_DeviceName, Arch, OpSys, Cpus ≥ 16 and the machine regexp.
- `cpu_model_contains` is enforced inside the job (`cpu_identity`, STOP on mismatch).
- R1-SWEEP-HOST-HTC literally says "job requirements 固定 GPU 型号与 CPU 型号".

**Fix:** say that the CPU model string is checked in the job and that a mismatch is a STOP. Let the author confirm that the machine regexp plus the in-job check satisfies the row.

### 9. MINOR — The projection-threshold note misses a confirmed value
**Location:** lines 169–170.

**Evidence:**
- R1-BX-PROPOSED-CONFIRM, REVISIONS (f) (E1, E2), confirmed "a sweep-2 T0 projection ≤ 4 days" as a pass criterion of the dual-TITAN qualification (DTQ).
- The 4-day figure is in (h), as proposed. (f) has no such figure.

**Fix:** cite (h) and BX-PROPOSED-CONFIRM, and say that both were set for another host. The threshold remains the author's to set.

### 10. MINOR — Provenance wording
**Location:** line 30 and the pins; line 69.

**Evidence:**
- "Each value below cites its source" does not hold for the harness, llama.cpp, GGUF and build-line values.
- The build line `version: 0.7.0-dev (build 11669, commit 620d2225c)` comes from `spec.example.json` and the Track S host facts. It has not yet been shown for the frozen image's binary. The wrapper STOPs on a mismatch.
- The Notes on precedence do not state that PLAN §10 rows override the note if the two conflict, as the runbook header does.

**Fix:**
- Add the sources: S2-C2 `spec.example.json`, S2-C1, and the registry `quant_source`.
- Mark the build line "to be confirmed by S2-C3/S2-C4".
- Add one sentence: PLAN §10 rows take precedence, and a conflict is a STOP.

## What I verified (all match unless a finding above says otherwise)
- **Pick provenance.**
  - Registry `quant_source` and `gemma4_31b.json` entry [2]: repo `bartowski/google_gemma-4-31B-it-GGUF`, revision `619aca75…5c14`, file `google_gemma-4-31B-it-Q4_K_M.gguf`, size 19,598,489,952, SHA-256 `2959c1b0…1b75`.
  - Registry doc SHA-256 `a04a0346…1fc61` (computed).
  - `thinking_policy` off with `off_switch` true.
- **Image.**
  - GPU digest `69b06b35…5cc05296`, `build_utc` 2026-11-14T23:10:24Z, `llama_server_sha256` `f8d35fd3…43cc0`.
  - CPU digest `221ca459…75aa`, as S2-C1 proposes.
  - All are correctly left as `<…>` placeholders pending author approval.
  - llama.cpp commit `620d2225cc436ab0b001e3200e590e3b286ef9ab`, which matches the image markers.
- **Harness.** `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, which is the S2-C2 `B2_HARNESS` and R1-CACHEPROMPT-FALSE's commit.
- **Design.**
  - The eight nodes, with climate in place of blood_transfusion: correct.
  - 18 instances, `{append_only_summary, none}`, W = 20, `vary`, `manager_proposal/v1`, transport attempts 3: these match the sweep-1 config, R1-MAIN-PROPOSER (b) and the S2-C2 validator.
- **Instance seeds.** `100 + 10k + (Σ ord(node) mod 7)`, the same on `ccb4712`, main and int-main. Also used as `train_seed` and `split_seed`.
- **Noise SHA.** `3d12ce05…4c34310` (computed on main).
- **D26.** The derivation string matches `e1b_collect.py`. `LLAMACPP_CACHE_PROMPT` and `LLAMACACHE_PROMPT` are unset in the wrapper.
- **Audits.**
  - K = 10, seeds 7001–7005 for labels and 7006–7010 for evaluation, never mixed.
  - The 7006–7010 restriction matches R1-B2-DECOUPLE and R1-SWEEP1-CLASSIFY.
  - T0 stays at K = 10 under R1-BX-PROPOSED-CONFIRM (D3).
  - Duplicates and no-ops are handled as in sweep 1.
- **Host constants.** CloudSite `BwForCluster-Nemo2`, `NVIDIA L40S`, `^g36[0-9]{2}\.nemo\.privat$`, Cpus ≥ 16, `request_gpus` 1, `request_cpus` and workers 16. The sealed path `/ceph/srv/dwong/paperb/sweep2/<run_id>/<chunk_id>/` matches.
- **Cross-proposer list.** It matches R1-MAIN-PROPOSER (c) as amended by R1-SWEEP-HOST-HTC (L40S is sm_89). The selection→deployment disclosure and the requirement that S2-C3 pass first match R1-SWEEP-HOST-HTC.
- **Compatibility with `resolve_label`.**
  - The key block's `approved: false` line will match `^approved:\s*true\s*$` (re.M) once the author changes it.
  - No other line in the block, or in the preamble, can match.
  - `label: EVIDENCE` matches `label:\s*EVIDENCE\b`.
  - The run id is a substring check. `s2ev-YYYYMMDD-a` fits the SAFE pattern.
  - The note's basename is SAFE, as `render_jdl --auth-note` requires.
  - A JSON-style `"approved": true` (the Track X B2 format) would not match, so the plain key block is necessary.
  - The draft keeps `approved: false` and says the agent never sets it.
  - The EVIDENCE preconditions of the S2-C2 validator (`paper.evidence_ready`, a non-empty `cpu_model_contains`) are covered by placeholders.
- **Placeholders.** Present exactly for the S2-C1 approval, the S2-C4 measurements (CPU string, layout, memory, disk, walltime, footprint, estimate), the run id, the main commit and the threshold. No value is invented.
- **Format.** Follows c3_sweep1: opening paragraph, "Proposed scope and pins", "Boundaries and STOPs".
  - Clearly marked as a draft.
  - Target path `docs/r1/authorizations/c3_sweep2_<date>.md` on main.
  - Authority ref stated.
  - Runbook ref `docs/runbooks-16nov` @ `a2789ea6` correct.
  - STOP list covers runbook §4.
- **Notes.** (g)2 and (g)4 are correct readings of R1-MAIN-PROPOSER (g), R1-HARNESS-NEXT-PIN and R1-EXAM-B1-HARNESS-PIN, apart from the qualifications in findings 5 and 6.

---

# Review R2 — S2-M1 draft authorization note (round 2)

- Reviewer: independent (Claude). Read-only; scratch only under /tmp/pb/rev_s2m1/.
- Reviewed head: `2777512fcfaa87a8b68e95a514df5526bcad7fad`.
  - Commits: `4741801c` and `2777512f` on `a19127be`.
  - Only file changed: `docs/r1/proposals/C3_SWEEP2_AUTHORIZATION_NOTE_DRAFT_20261116.md` (+96/−30).
- Sources: as in round 1, and in addition:
  - `r1/exam/runtime.py` (line 215 is inside `load_config`, which starts at line 213);
  - the harness clone (to check where `897d83c` sits relative to `6adf385`).

VERDICT: REVISE

F2–F10 are fixed correctly. The F1 fix is correct in note 2, but the signed body now contradicts itself on the context. One MAJOR finding and three MINOR ones remain.

## Findings

### R2-1. MAJOR — The context is a fixed pin in one place, an author placeholder in another, and the exam's context is offered as a choice
**Location:** body lines 96, 101 and 150; notes 2 and 5.

**Evidence:**
- **Line 96** lists `-c 16384` as a fixed argument of the sweep-2 job.
- **Line 101** says "the selection exam ran at context `<16,384 | 32,768>`".
  - Which context the exam ran at is a fact, not a choice. Note 2 itself says it was 32,768 (`exam_b2_v2.json`, `runtime.load_config`, B2 `batch_state.json`).
  - The decision the author actually has to make (note 2, note 5 "Author: context") is the **sweep-2** context.
- **Line 150** fixes "context 8,192 against 16,384".

What goes wrong in practice:
- If the author fills line 101 with 32,768, meaning it as sweep 2's context, the signed note still pins `-c 16384` on line 96.
- The STOP "server flags … differing from the values above" (line 173) then has no single value to compare against.
- The S2-C2 validator enforces 16384 whatever the note says.

**Fix:**
- Line 96: `-c <16384 | 32768 — author, note 2>`.
- Line 101: "the selection exam ran at 32,768 (note 2); sweep 2 runs at the context above".
- Line 150: "context 8,192 against `<sweep-2 context>` (the exam ran at 32,768)".
- Optionally, in note 2, say that choosing 32,768 also needs the S2-C2 validator change.

### R2-2. MINOR — Note 2 misquotes R1-MAIN-PROPOSER
**Location:** line 197, "R1-MAIN-PROPOSER (b)/(c), the work plan §0 and the S2-C2 validator all say '16,384, as in the exam'".

**Evidence:**
- (b) says "exactly as in the exam" only for the thinking flag, `--jinja` and q8_0. It does not give a context.
- (c) gives "context 8,192 against 16,384" and does not say "as in the exam".
- Only runbook §0 ("server flags exactly as in the exam (… context 16,384)") and the S2-C2 validator ("ctx must be 16384 (exam setting)") pair 16,384 with the exam.

**Fix:** write "(c) gives 16,384; the work plan §0 and the S2-C2 validator call it the exam setting".

### R2-3. MINOR — The rows-used list omits rows the draft now relies on
**Location:** lines 23–30.

**Evidence:** note 3 rests on R1-B2-REPLAY-GO, and note 4 rests on R1-HARNESS-NEXT-PIN. Neither appears in the list of rows used. I asked for R1-B2-REPLAY-GO in round 1 (F3).

**Fix:** add both rows to the list.

### R2-4. MINOR — The list of differences between selection and sweep 2 is incomplete
**Location:** lines 207–212.

**Evidence:**
- The paper commit is missing. `exam_b2_v2.json` has `paper_commit` `37282ec3…`; sweep 2 uses `main` HEAD at launch.
- The llama-server binary is covered only implicitly, by "image: none". The exam binary was SHA-256 `b70f4882…`, build line `version: 0.7.0-dev (build 1, commit 620d222)`. The image binary is `f8d35fd3…`, expected build line "build 11669". The commit is the same.
- The harness is the same in both (`a3fedbb`). That is worth stating, because it is the one stack element that is identical.

**Fix:** add these three lines.

## Round-1 findings: verification
- **F1 (MAJOR):** partly fixed.
  - "Exactly as in the exam" is gone.
  - The actual S2-C2 arguments are listed and match `spec.example.json`.
  - Note 2's evidence is correct: `exam_b2_v2.json` sets `ctx_size` 32768; the `load_config` check is at line 215; B2 `batch_state.json` records `context` 32768; the exam ran `-ngl 999 -np 1 -lv 4` without `--no-webui`.
  - S2-C3 is asked to use sweep 2's context.
  - The body is now inconsistent: see R2-1.
- **F2 (MAJOR): fixed.**
  - There is a new "Noise source binding" pin with an S2-C2 placeholder.
  - Note 1 is correct. The fallback is `E1_20261022T214606Z`, the newest file matching `E1_[0-9]*T*Z`, and it has no `openml_climate`.
  - Note 1 makes this a precondition for EVIDENCE.
- **F3 (MAJOR): fixed.**
  - Note 3 quotes R1-B2-DECOUPLE and R1-B2-REPLAY-GO's e1/e2 sequence exactly, as amended in `2777512f`.
  - It covers the R1-SWEEP1-CLASSIFY fix in S2-M2 and the missing S2-C7 wrapper.
  - The audits are conditional, with the option of a later addendum. Nothing is decided for the author.
- **F4: fixed.** The `main` / `ccb4712` reference is given, and the stale author-branch copy is described correctly.
- **F5: fixed.**
  - The draft now says no PLAN row names a sweep-2 harness pin and gives the source: the S2-C2 validator and the author's 16 Nov answer.
  - The `HARNESS_PIN_C3` values per branch are correct. I checked in the harness clone that `897d83c` is an ancestor of `6adf385`, so "pre-sweep-1" is accurate.
  - There is a placeholder for the (c) harness-defaults check.
- **F6: fixed.** The liveness gate runs before collection and the collection gates after it; the wrapper checks only the return code.
- **F7: fixed.**
  - The lock is now described as the PLAN-line guard (`guard_table` / `require_d8_confirmation`), and the draft says `refuse_sealed` does not apply.
  - The seal check is described accurately, as presence only.
  - An S2-C5 placeholder covers the comparison with authorized values. Whether that check belongs in S2-C5 or S2-C2 is a unit choice, not a defect.
- **F8: fixed.** The CPU model check is in-job; the draft says R1-SWEEP-HOST-HTC wants it in the requirements, and it leaves an author `<choice>`.
- **F9: fixed.** The projection note cites (h) and R1-BX-PROPOSED-CONFIRM's criterion for the dual-TITAN qualification, and leaves the threshold to the author.
- **F10: fixed.** Provenance is given for the identity markers (S2-C1). The build line is marked as not yet shown for the frozen binary, with an S2-C3/S2-C4 placeholder. The sentence that PLAN §10 rows take precedence has been added.

## Checked again for regressions
- The key block is unchanged.
- No new line in the copied block can match `^approved:\s*true\s*$`.
- `label: EVIDENCE` is still present.
- `approved: false` is kept.
- All values verified in round 1 are unchanged: hashes, GGUF, digests, harness, nodes, seed formula, noise SHA, audit seeds and host constants.
- The new placeholders are exactly where values are unknown: noise binding, harness-defaults check, CPU-requirement choice, build line, seal check and context.
- No value is invented.

---

# Review R3 — S2-M1 draft authorization note (round 3)

- Reviewer: independent (Claude). Read-only; scratch only under /tmp/pb/rev_s2m1/.
- Reviewed head: `c3134bf08629a1f93f2bdc37afe53b70a5a11592`, one commit on `2777512f`.
- Only file changed: the draft (+13/−6).

VERDICT: ACCEPT

No BLOCKING or MAJOR finding remains. All round-2 findings are fixed. The note keeps `approved: false`.

## Round-2 findings: verification
- **R2-1 (MAJOR): fixed.** The context is now one author placeholder everywhere.
  - Line 97: `-c <16384 | 32768 — author, note 2>`.
  - Lines 102–103 state the exam's context as a fact (32,768) and point to the placeholder above for sweep 2.
  - The same lines say that choosing 32,768 needs the S2-C2 validator changed. That is correct: `validate_spec` raises a STOP unless ctx is 16384.
  - Line 152: `8,192 against <16,384 | 32,768>`.
  - No line in the signed body still fixes 16,384 (grep). The STOP "server flags … differing from the values above" now has a single referent once the author fills the placeholder.
- **R2-2: fixed.** Note 2 now says (c) lists 16,384 and the work plan §0 and S2-C2 call it the exam setting. That matches PLAN and the sources.
- **R2-3: fixed.** R1-B2-REPLAY-GO and R1-HARNESS-NEXT-PIN are in the list of rows used.
- **R2-4: fixed.** The list of differences now includes:
  - the paper commit `37282ec3…`, which matches `exam_b2_v2.json` `paper_commit`;
  - the exam binary `b70f4882…`, which matches `exam_b2_v2.json` `binary_sha256` and `B2_HANDOFF_EXEC_20261115.md` line 67 on `gh/mac-b2-handoff-exec-20261115`, with build line "build 1";
  - the image binary `f8d35fd3…` with "build 11669";
  - the shared commit `620d222`;
  - the harness, identical at `a3fedbb`.

## NIT (not blocking)
- Line 217 calls the image binary "build 11669". Line 86 marks that build line as expected and not yet shown for the frozen binary, so line 217 could read "expected 'build 11669'" for consistency. The S2-C3/S2-C4 placeholder already covers this.

## Regression check
- The key block is unchanged (`approved: false`, `label: EVIDENCE`, run-id placeholder).
- No line in the copied block can match `^approved:\s*true\s*$`.
- The values verified in rounds 1 and 2 are unchanged.
- No new value is invented.
- Round-1 findings F2–F10 are still fixed.
- The worktree is clean.
