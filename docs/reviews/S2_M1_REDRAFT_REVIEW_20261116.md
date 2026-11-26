Reviewed base: 11db0f652275ac88ac0e5aec414fb2e58c427535

# S2-M1 redraft (sweep-2 authorization draft after R1-SWEEP2-SETTINGS) — independent review record (16 November 2026)

Branch `mac-s2-m1-redraft-20261116` from `author-decisions-20261116` @ `4da73306`. Commit `b068e7a4` copies the accepted first draft (`56b5b76e`) unchanged; `065731ac` is the redraft. Unit: `proposals/C3_SWEEP2_AUTHORIZATION_NOTE_DRAFT_20261116.md`, with `approved: false`. One freshly spawned independent reviewer agent (AI-assisted, Claude), two rounds.
- **Round 1 (`065731ac`): REVISE.** 3 MAJOR and 7 MINOR. The MAJOR findings:
  - the exam argv left out `-lv 4`, and the draft listed differences that are not real differences;
  - the KV footprint and the 32,768 caveat were wrong: there are two KV buffers, and the pilot ran without `-np 1`;
  - **the S2-C4 pilot's visible in-campaign worker runs all ended in ≤ 0.1 s with `success=False`, so the estimate may contain no training time.**
- **Round 2 (`11db0f65`): ACCEPT.** Three optional nits are left as is:
  - "fix A" against precondition "2a";
  - `+RequestWalltime 10,776` is derived from the estimate now marked unusable;
  - note 3 lists "estimate" among the filled values without the qualifier.

The failed pilot worker runs are a finding for the cluster side (S2-C4/S2-C3). The draft makes the estimate "not yet usable" until a re-measurement with successful worker runs.

Accepted commit (round 2, last): 11db0f652275ac88ac0e5aec414fb2e58c427535

The round texts are reproduced unchanged below.

---

Reviewed base: 065731ac3ec19278ce2aee7a96f20de739d2acb0

# Review R1: S2-M1 redraft of the C3 sweep-2 authorization note draft

- Reviewer: independent (Claude). I did not write this work. I worked read-only and kept scratch files under /tmp/pb/rev_s2m1b/.
- Worktree /tmp/pb/wt/s2m1b, branch `mac-s2-m1-redraft-20261116`. Diff `b068e7a4..065731ac`, one file:
  `docs/r1/proposals/C3_SWEEP2_AUTHORIZATION_NOTE_DRAFT_20261116.md`, 256 lines.
- Sources read:
  - PLAN at `4da73306`: R1-SWEEP2-SETTINGS, R1-SWEEP-HOST-HTC, R1-MAIN-PROPOSER (b), (c), (g), (h), R1-BX-D8, R1-BX-D8-V3-A,
    R1-E1-AUTH, R1-B2-DECOUPLE, R1-B2-REPLAY-GO, R1-HARNESS-NEXT-PIN, R1-SWEEP1-CLASSIFY and R1-EXAM-X7.
  - Exam code: `r1/exam/runtime.py` (`EXAM_SERVER_ARGS`, the `load_config` check, `server()`, `template_repair_args`),
    `r1/scripts/llama_server_instance.py` (`argv`, `thinking_args`), `exam_b2_v2.json`, and the registry entry for
    `gemma4_31b`.
  - Cluster ref `gh/sweep2-cluster-20261116` @ `acae9fde`: S2_C4_RESULTS, S2_C4_TIMING.md, timing.json, both job records,
    `s2_c2_lib.py`, `render_jdl.py`, `s2_c4_pilot.py`, `spec.example.json` and the S2-C4 review.
  - `gh/main` @ `9ae6d877`: `HARNESS_PIN_C3`, `c3_sweep_deepthought.json`, `c3_label_sweep.py`, `analysis_guard.py` and the
    c3_sweep1 note.
  - The previous draft review (`mac-s2-m1-auth-20261116`).
  - The X.7(c) unit (`mac-s2-m5-x7c-20261116` @ `31ed1c19`).

VERDICT: REVISE

There are three MAJOR findings and seven MINOR ones.
- What was done well: each requested change is present. Most filled values match the cluster exactly. `approved: false` is kept, the
  key block still works with `resolve_label`, and the D8 lock is stated correctly.
- What blocks acceptance: three statements the author would sign are wrong or incomplete:
  - the list of non-numeric server differences;
  - the KV footprint and its 32,768 caveat;
  - the provisional estimate, which rests on a pilot whose in-campaign worker runs all seem to have failed.

## Findings

### 1. MAJOR: the exam argv is listed incompletely, and the "non-numeric differences" are partly wrong
**Location:** lines 97–106 (Server); line 196 (exam differences); line 218 (STOP "server arguments … differing from the values
above").

**Evidence.**

The exam's actual argv for the pick is `<bin> -m <gguf> --host 127.0.0.1 --port <p> -ngl 999 -c 32768 --alias gemma4_31b -np 1
--jinja --cache-type-k q8_0 --cache-type-v q8_0 -lv 4 --chat-template-kwargs {"enable_thinking":false}`. It is built from these
pieces:
- `llama_server_instance.py:261-263` (`argv`);
- `runtime.py:117` (`EXAM_SERVER_ARGS` = `--jinja --cache-type-k q8_0 --cache-type-v q8_0 -lv 4`);
- `runtime.py:861-865` (`n_gpu_layers=999`, `alias=spec['id']`);
- `thinking_args` (compact JSON, `separators=(',', ':')`);
- the registry, where `gemma4_31b` has `template_repair: null` and `off_switch: true`.

The S2-C2 wrapper already passes `-lv 4` and binds `127.0.0.1`. In `s2_c2_lib.py:328-329`, `build_server_argv` sets
`--host 127.0.0.1 … -lv 4 --alias <model.alias>`, and `-lv` is a managed flag. `model.alias` is `gemma4_31b`
(`spec.example.json`).

So the draft is wrong in two ways:
- **It lists three "differences" that do not exist.** The draft names the log level ("the exam used `-lv 4`", which implies sweep 2
  does not), the alias and the host binding. All three are the same in both stacks.
- **It leaves out real differences:**
  - `--no-webui`, which the wrapper adds;
  - the spacing of the chat-template-kwargs JSON: S2-C2 has `{"enable_thinking": false}` with a space, the exam has
    `{"enable_thinking":false}`;
  - the port and model path values;
  - the order of the arguments.

The list of "the arguments" on lines 99–100 also leaves out `-lv 4`. Read literally, the STOP on line 218 would then fire on the
wrapper's own `-lv 4`, and also on its JSON spacing, because line 100 uses the exam's compact form.

**Fix.**
- Add `-lv 4` to the exam list on lines 99–100. Optionally add `--host 127.0.0.1` and `--alias gemma4_31b`.
- Rewrite the list of non-numeric differences as: `--no-webui` (if kept), the port and model-path values, the argument order, and the
  spacing of the chat-template-kwargs JSON. Keep the `<list from the accepted S2-C2 fix>` placeholder for anything 2a adds.
- Or say that the 2a fix must make the JSON byte-identical to the exam's.

### 2. MAJOR: the KV footprint undercounts, and the 16,384→32,768 caveat is wrong and incomplete
**Location:** line 129 (`footprint_mib` = model 18,675.55 + KV `<…; 680.0 MiB at 16,384>`); lines 125 and 133 ("measured at
context 16,384"); Notes 1, lines 234–241 ("At 32,768 the KV buffer grows, roughly doubling for q8_0").

**Evidence.**

Both job records (`server.cuda_lines`) show two KV buffers and a compute buffer:
- `llama_kv_cache: CUDA0 KV buffer size = 680.00 MiB`;
- `llama_kv_cache: CUDA0 KV buffer size = 1912.50 MiB`;
- `sched_reserve: CUDA0 compute buffer size = 255.80 MiB`.

The 680.0 in S2_C4_RESULTS and timing.json is a parser artifact. `s2_c4_pilot.py:99,107` uses `KV.search(text)`, which takes only
the first match. The total KV at 16,384 was therefore 2,592.5 MiB, not 680.0. The draft copies the results file faithfully, but
the job records do not support the formula it presents.

The pilot also differed from the exam in more than context:
- **The pilot had no `-np 1`.** The S2-C2 argv has no `-np` (`s2_c2_lib.py:329`, `spec.example.json`). So the pilot ran with the
  build's default slot count. The exam ran `-np 1`, and so did sweep 1, through `LlamaServerInstance`.
- **This is my inference from the measured numbers:** Gemma-4 is an interleaved sliding-window/global model.
  - The 680 MiB buffer fits the global layers at 16,384 cells.
  - The 1,912.5 MiB buffer fits the sliding-window layers at (4 slots × 1,024 + 512) cells.
  - If that is right, only the 680 MiB part scales with context, and the 1,912.5 MiB part scales with the number of slots.
  - At 32,768 with `-np 1`, the total KV would then go *down*, to about 1,360 + 640 MiB. It would not "roughly double".
- **A single slot also serializes the 16 workers' manager calls.** That can raise per-chunk wall time well beyond any effect of
  context length.
- Note 1 mentions only context.

**Fix.**
- Write the footprint as model 18,675.55 + KV 680.00 + 1,912.50 (+ compute 255.80) MiB at 16,384, without `-np 1`, citing the
  `server.cuda_lines` of the job records. Note that the S2-C4 summary records only the first KV line.
- Change the "measured at 16,384" labels to "measured at 16,384, without `-np 1` (S2-C2 pre-2a argv)".
- Replace "roughly doubling" in Note 1 with:
  - the slot count and context both change;
  - single-slot serialization can lengthen the wall time;
  - footprint and wall must be re-measured with the 2a argv before they are written in.

### 3. MAJOR: the provisional estimate rests on a pilot whose in-campaign worker runs seem to have failed; no caveat
**Location:** lines 133–139 (Provisional estimate: 8,289 s per chunk, 36.84 GPU-h, serial 36.8 h); precondition 7 (line 158);
Notes 1.

**Evidence.**
- Both job records' `collector.stderr_tail` show every visible worker run failing at once:
  `running: python3 train.py` / `run_command finished in 0.0s|0.1s; success=False metrics={}`.
  - `none`: 10 such lines, 0 with `success=True`.
  - `append_only_summary`: 9 such lines, 0 with `success=True`.
- The collector took only 121.3 s and 137.1 s per job, against walls of 867 s and 921 s. The ×9 extrapolation (8,289 s) scales a
  wall that apparently contains no real worker training time. So the estimate may not represent sweep 2's cost.
- It may also point to a wrapper or container defect in the worker runs, which the collection gates of precondition 2c would then
  catch at launch.
- I saw only the tails. The full sealed `out/` is on ceph and I could not read it.
- The S2-C4 review does not mention this.

**Fix.**
- Add a caveat beside the estimate and in Notes 1. It should say that the stderr tails of the S2-C4 pilot show worker runs ending
  in ≤ 0.1 s with `success=False`, so 8,289 s and 36.84 GPU-h are not a valid projection basis until that is explained.
- Make precondition 7's projection come from a re-measurement with the 2a argv in which worker runs succeed and the restored gates
  pass.
- Report the observation to the cluster side as an S2-C2/S2-C4 question. That is outside this note.

### 4. MINOR: the job-layout values and the EVIDENCE job record need wrapper changes that no precondition lists
**Location:** lines 125–132; precondition 2.

**Evidence.**
- `render_jdl.py` hard-codes `request_memory = 128000` and `request_disk = 50000000`. Only the walltime comes from the spec. So the
  note's 32,000 MB and 42,439,718 kB need a renderer change. S2_C4_RESULTS says these values "feed P5 (fixed job layout)".
- In `s2_c2_lib.py:496-506`, the job record hard-codes `"ctx": 16384` and `output_use: "ENGINEERING: never enters a label table…"`.
- In `s2_c2_lib.py:444`, the extra manifest says `"audit": "none (ENGINEERING run …)"` whatever the label.
- An EVIDENCE record carrying this text would contradict the note.

**Fix:** add precondition 2e: the job layout (S2-M3/P5) in the renderer, and EVIDENCE-correct record and manifest fields (ctx from
the spec, `output_use`).

### 5. MINOR: the CPU-model item misstates what exists
**Location:** lines 70–72; precondition 2d.

**Evidence:**
- `validate_spec` already refuses EVIDENCE without a non-empty `requirements.cpu_model_contains` (`s2_c2_lib.py:173-175`).
- `cpu_identity` STOPs in the job if the model does not contain that string.
- So the in-job check exists. What is missing:
  - the value in the spec (`INTEL(R) XEON(R) PLATINUM 8562Y+`, or a substring of it);
  - if the author wants the model in the HTCondor `requirements`, as R1-SWEEP-HOST-HTC literally says, a `render_jdl.requirements()`
    change. Today it has no CPU-model term.

**Fix:** reword it as: the spec sets `cpu_model_contains` to `<value>`, and the in-job check exists. The JDL requirement is
`<added | author accepts in-job check>`.

### 6. MINOR: the X.7(c) disclosure item misdescribes its source
**Location:** lines 188–189.

**Evidence.** In `X7C_APPENDIX_20261116.md` §1 and §2, the premises that differ are:
- Q1, the rule-skippable share. It is an upper bound on the duplicate/no-op skip share.
- Q2, the increment sd. Pooled, and node-driven.

The draft gets this wrong in three ways:
- The "B1 μ̂ ordering" is the R1-EXAM-X7 (a) disclosure. It is not a C3 premise.
- Q2 is missing from the item.
- There is no "cross-proposer disclosure paragraph". The report says only that "the cross-proposer tables should say so".

The unit is accepted (review @ `31ed1c19`), but it is on a Mac branch and not in the authority chain. The request also did not ask
for this item.

**Fix:** write "Q1 (A2-skippable share, upper bound) and Q2 (increment sd, node-driven), per the X.7(c) appendix
(`mac-s2-m5-x7c-20261116` @ `31ed1c19`, accepted, not yet on `main`). The B1 μ̂ disclosure is that of R1-EXAM-X7 (a)." Or drop the
item until the author adopts it.

### 7. MINOR: derived figures are presented next to measured S2-C4 values
**Location:** lines 127 and 135–136.

**Evidence:** these figures are not in S2-C4. They are the agent's own arithmetic or assumptions:
- "about one chunk plus queue wait" with 16 concurrent jobs (the pilot ran 2 jobs);
- "serial worst case about 36.8 h";
- "peak about 10.9 GB". The source gives 10,781 / 10,853 MB, or "~11 GB".

The request asked for S2-C4 values only.

**Fix:** mark them as derived, for example "(derived: 16 × 8,289 s)", or remove them.

### 8. MINOR: correct content from the first draft was dropped
**Location:** Authority (lines 30–37); Harness (lines 78–82).

**Evidence:**
- R1-SWEEP1-CLASSIFY has gone from the rows used. `resolve_label` still implements its rule that the label comes from the note,
  never from an index (docstring, `s2_c2_lib.py:181`).
- The first draft's provenance for `a3fedbb` has gone. No PLAN row names the sweep-2 harness pin. The value comes from the S2-C2
  validator and the author's 16 Nov answer to the S2-M2 question. `HARNESS_PIN_C3` on `main` (verified: `a3fedbbd…` @ `9ae6d877`)
  is a file, not a PLAN row.

**Fix:** restore both, each in one line.

### 9. MINOR: the B.2 removal leaves the reserved seeds and the exam seed line unclear
**Location:** line 197; Scope (lines 204–205).

**Evidence:**
- Line 197 compares "instances and audit seeds: exam 9001+/9101+/9201+" with "the sweep-1 instance seeds" only.
- The note does not say that the sweep-2 collector runs `--reps 0 --audit-seeds 0` (`s2_c2_lib.py:451`).
- It does not say that seeds 7001–7010 stay reserved and untouched for the later addendum (R1-MAIN-PROPOSER (b) and (e),
  R1-B2-DECOUPLE).

**Fix:** write "exam instances 9001+ and audit seeds 9101+/9201+ against the sweep-1 instance seeds; sweep 2 runs no audits". Add
under Scope: "audit seeds 7001–7010 stay reserved for the addendum; the collector runs `--audit-seeds 0`".

### 10. MINOR: the seal statement is written as already true
**Location:** line 167, "It compares the image digest and host with this note (precondition 5)."

**Evidence:** the current `seal()` checks only that an image digest and a host FQDN are present (`s2_c2_lib.py`, seal). It does
not compare them with the note. The first draft said "does not yet compare".

**Fix:** write "After S2-C5 it compares…", or "S2-C5 adds the comparison (precondition 5)".

## What I verified (no issue found)

**Requested changes**
- **Context.** 32,768 throughout. Precondition 2a replaces the validator's 16,384 / `-ngl 99`. S2-C3 runs at 32,768, as row (1)
  requires. The sweep-1 difference reads "8,192 against 32,768".
- **Exam flags.** Present in the draft: `-ngl 999`, `-np 1`, `--jinja`, enable_thinking false, q8_0 K and V, and
  `cache_prompt: false` with the env vars unset. They match R1-SWEEP2-SETTINGS (1) and `runtime.py:215`. (`-lv 4`: see finding 1.)
- **B.2 removed.** No audit block, no CPU image, no 7001–7010 and no K = 10 remain. The Scope cites R1-SWEEP2-SETTINGS (2) and
  says that R1-B2-DECOUPLE and R1-B2-REPLAY-GO stand.
- **Projection STOP.** "Exceeds 60 GPU-h or 48 h wall … replacing (h)'s '4 days on one 4090'" matches row (5). It also appears in
  the STOP list and as precondition 7.
- **(g)4 and gates.** The (g)4 unit (eight nodes, NEMO2 L40S, prompt lengths re-measured with the pick's tokenizer) and the
  restored gates (`min_live_nodes` 8, `max_parse_failure_rate` 0.2, `collection_gates`, not waived) match row (4). The values
  match `c3_sweep_deepthought.json` on main.
- **(g)2.** "No exception for now; e1 (R1-E1-AUTH) → author e2 → sweep-1 B.2 on one pinned HTCondor CPU class, in parallel; an
  exception only if it is the only blocker" matches row (3).

**S2-C4 values, exact against S2_C4_RESULTS, timing.json and the job records**
- CPU `INTEL(R) XEON(R) PLATINUM 8562Y+` on g3605 and g3608, with `required_contains: null`.
- 16 jobs, `request_memory` 32,000, `request_disk` 42,439,718 (= 30,314,084 × 1.4), walltime 10,776 (= 8,289 × 1.3).
- Model buffer 18,675.55 MiB.
- Build `0.7.0-dev (build 11669, commit 620d2225c)`, `llama_server_sha256` `f8d35fd3…` and `versions_sha256` `d31e8b23…`.
- Image `69b06b35…`.
- 921 s → 8,289 s, and 36.84 GPU-h.
- Queue wait 16 s.
- 16 × 19.6 GB ≈ 314 GB of egress.

I found no value that exists in S2-C4 and was left unfilled, except the second KV buffer (finding 2).

**Key block and placeholders**
- `approved: false`, `label: EVIDENCE` and the `run_id` placeholder are present. They work with the `resolve_label` regexes
  (`^approved:\s*true\s*$`, a substring match on the run id, and `label:\s*EVIDENCE\b`).
- No `approved: true` appears in the note body.
- The placeholders are limited to the launch commit, the fix units, the reports and reviews, the image approval, the run id and
  the (g)2 status.

**Pins**
- Unchanged pins: GGUF repo, revision, file, size and SHA; registry doc SHA; the sweep-1 config SHA `2fa891f4…`, which is now
  identical on `4da73306`, so dropping the first draft's note about the unfilled draft copy is correct; the eight nodes and the
  seed formula; the noise source `3d12ce05…`.
- `HARNESS_PIN_C3` on `main` @ `9ae6d877` is `a3fedbbd…`. `9ae6d877` is an ancestor of `4da73306`.

**Authority and the D8 lock**
- The authority section names the base and its ancestry, and states that PLAN takes precedence.
- The D8 lock matches R1-BX-D8 (copied back for analysis or read by any analysis code before R1-BX-D8-CONFIRM). R1-BX-D8-V3-A
  keeps the lock.
- `guard_table`, `require_d8_confirmation` and `refuse_sealed` exist on main, and `refuse_sealed` matches `r1_sealed` only.

**Other**
- The selection-exam differences are correct: binary `b70f4882…` "build 1" against `f8d35fd3…` "build 11669"; paper `37282ec3`;
  harness identical.
- The S2-C2 class constants are correct.
- No statement contradicts a PLAN row, apart from the argv inaccuracy in finding 1.

---

Reviewed base: 11db0f652275ac88ac0e5aec414fb2e58c427535

# Review R2: S2-M1 redraft of the C3 sweep-2 authorization note draft

- Reviewer: independent (Claude). I did not write this work. I worked read-only and kept scratch files under /tmp/pb/rev_s2m1b/.
- Diff `065731ac..11db0f65`, one file: `docs/r1/proposals/C3_SWEEP2_AUTHORIZATION_NOTE_DRAFT_20261116.md`, 282 lines.
- I checked each fix against the same sources as in R1. I also checked one new value against `r1/exam/b2_batch.py`.

VERDICT: ACCEPT

All three MAJOR and all seven MINOR findings from R1 are fixed. I found nothing new at BLOCKING or MAJOR level. Three optional
nits are listed at the end.

## Status of the R1 findings

1. **F1 (MAJOR): fixed.**
   - **The exam argv is complete and in the right order.** Lines 101–104 give:
     `-m <model> --host 127.0.0.1 --port <p> -ngl 999 -c 32768 --alias <id> -np 1 --jinja --cache-type-k q8_0 --cache-type-v q8_0 -lv 4 --chat-template-kwargs {"enable_thinking":false}`.
     This matches the order of `llama_server_instance.py:261-263` and `EXAM_SERVER_ARGS` (`runtime.py:117`). `thinking_args` adds
     the compact JSON. The registry has `template_repair: null`, so no `--chat-template-file` is missing.
   - **The shared settings are stated correctly.** `-lv 4`, `127.0.0.1` and the alias `gemma4_31b` are now stated as the same in
     both stacks. That matches `s2_c2_lib.py:328-329`.
   - **The disclosed differences are correct:** port and model path, argument order, JSON spacing, and `--no-webui` if kept.
   - **The STOP exempts only the disclosed non-numeric differences.**
2. **F2 (MAJOR): fixed.**
   - The footprint is now the model buffer plus the KV buffers plus the compute buffer, to be re-measured at 32,768 with `-np 1`.
   - The 680.00 and 1,912.50 MiB KV buffers and the 255.80 MiB compute buffer match `server.cuda_lines` in both job records.
   - The parser artifact is noted correctly.
   - Note 1 now covers the different settings (no `-np 1`) and the serialization through one slot.
   - The wrong claim of "roughly doubling" is gone.
3. **F3 (MAJOR): fixed.**
   - The estimate is marked "not yet usable".
   - Note 1 describes the failed worker runs accurately: ≤ 0.1 s, `success=False metrics={}`, collector 121–137 s of an
     867–921 s wall, tails only. It says the S2-C4 review does not mention them.
   - Precondition 4 and the placeholder on the estimate line both require a re-measurement in which worker runs succeed.
4. **F4: fixed.** Precondition 2e covers the requests in `render_jdl.py` (128000 / 50000000, verified) and the record's `ctx` and
   `output_use`.
5. **F5: fixed.** The CPU wording now matches `s2_c2_lib.py:173-175`. The value in the spec and an optional term in the JDL are
   what is missing.
6. **F6: fixed.** The item now cites Q1 and Q2 only, matching §1 and §2 of the X.7(c) report.
7. **F7: fixed.**
   - Measured and derived figures are now separated.
   - The peaks are 10,781 and 10,853 MB, which matches timing.json.
8. **F8: fixed.** R1-SWEEP1-CLASSIFY and the sentence "No PLAN row names `a3fedbb`" are restored.
9. **F9: fixed.**
   - The new seed values are right. B2 instance seeds start at 9011 (`b2_batch.py:38`, `B2_SEED_BASE`). Audit seeds are 9101+ in
     B1 (`exam_b2_v2.json`) and 9201–9210 in B2 (`b2_batch.py:40`).
   - `--audit-seeds 0` matches `s2_c2_lib.py:451`. Seeds 7001–7010 are stated as reserved.
10. **F10: fixed.** The seal now reads: "With S2-C5 … will also compare; the accepted S2-C2 seal checks only that they are
    recorded."

## Re-checked without change
- The key block is unchanged (`approved: false`, `label: EVIDENCE`, `run_id` placeholder) and still works with `resolve_label`.
- The filled S2-C4 values are still exact.
- The D8 lock, the precedence statement and the R1-SWEEP2-SETTINGS (1)–(5) items are intact.
- No PLAN row is contradicted.

## Optional nits (MINOR, do not block)
- **a.** Line 112, "Final list: `<from the accepted fix A>`": the precondition is called **2a**. Write "fix 2a".
- **b.** `+RequestWalltime 10,776` s is 1.3 × the 8,289 s estimate that is now "not yet usable".
  - The layout line could say that the walltime is re-derived from the re-measurement.
  - Note 1 already says the walltime is re-measured.
- **c.** Note 3 ("What changed") still lists "estimate" among the filled S2-C4 values. "Estimate (marked not yet usable)" would be
  more accurate.
