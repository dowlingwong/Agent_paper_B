# S2-C3b — (g)4 D28 liveness on NEMO2 L40S + prompt-length re-measurement (unit for independent review; ENGINEERING)

**Unit:** S2-C3b (new unit under PLAN row `R1-SWEEP2-SETTINGS` (4)).
**Authority:** `author-decisions-20261116b` @ `025bfc16`: row **R1-SWEEP2-SETTINGS (4)** *"(g)4: 新增单元：pick 在
NEMO2 L40S 上对八个节点做 D28 liveness，并用 pick 的 tokenizer 重测 prompt 长度；S2-C2 wrapper 恢复 sweep 1 的
liveness 与收集门槛（`min_live_nodes` 8、`max_parse_failure_rate` 0.2、`collection_gates`）；不豁免"* (a new unit:
D28 liveness of the pick on NEMO2 L40S over the eight nodes, and re-measure prompt lengths with the pick's
tokenizer; the sweep-2 wrapper restores sweep 1's liveness and collection gates; no exemption), row
**R1-S2C3B-SEEDS** (accepted: `liveness_seed_policy = "sweep1_d28_reuse"`, disclose the 10-of-90 overlap in the
sweep-2 report, no 7001–7010 / 8001–8010 / 9001–9303 seeds) and row **R1-SWEEP2-LAYOUT** (accepted 32k measured
layout: `request_walltime 12,203 s`, `request_disk 42,460,977 kB`, `request_memory 32,000 MB`, replacing the S2-C4
16k layout), plus **R1-SWEEP-HOST-HTC** (HTCondor / NEMO2 L40S only; one GPU model per table) and
**R1-MAIN-PROPOSER (g)4** (D28 liveness before the projection/authorization). **Run plan:** `docs/runbooks-16nov` @
`b3289232` `prompts/SWEEP2_HTCONDOR_RUNBOOK_20261116.md` §3 S2-C3 / §0 (ENGINEERING units may proceed before P1–P7)
with the corrected exam context **32,768** (R1-SWEEP2-SETTINGS (1)).
**Base:** `sweep2-main-20261116` @ **`9a79cfe0`** (accepted round-5.1 + 32k-layout + `_kill(None)`-guard tip; paper
main `9ae6d877`). This unit is rebased onto that tip after independent review round 1 (`S2_C3B_REVIEW_20261116.md`,
NOT ACCEPTED, 4 majors + minors); see "Review round 2 fixes" below.
ENGINEERING_ONLY: no label table, no B.2 audit, no seed 7001–7010, no EVIDENCE; the R1-BX-D8 analysis lock is
unchanged. **Nothing was submitted and no llama-server was started** — this unit is code, tests and a reviewed dry run.

## What the unit does

One HTCondor job = **one owned llama-server** at the exam setting (R1-SWEEP2-SETTINGS: `-c 32768 -ngl 999 -np 1`,
`--jinja`, `{"enable_thinking": false}`, q8_0 K/V, `cache_prompt` false; non-numeric `--no-webui`, `-lv 4` disclosed)
that runs, in order:

1. **D28 liveness, sweep-1 protocol.** `python -m r1.liveness --run --manager langgraph --memory-mode
   append_only_summary --nodes <the eight sweep-1 nodes> --instances 2 --runs 10 --transport-max-attempts 3
   --manager-model llamacpp/gemma4_31b --proposal-schema manager_proposal/v1 --out out --work work` (there is **no
   `--deadline`** in the liveness CLI; the unit tests assert the argv only uses flags the pinned CLI defines).
   The unit then reads `out/liveness.json` and requires **all eight nodes to pass** (`min_live_nodes = 8`, no
   exemption). Any shortfall STOPs: the owned server is killed **first** (None-guarded), then `job_record.json` +
   `out.tar` + `work.tar` + `SHA256SUMS` are written before raising, so the transferred sums verify against the
   closed server log and the evidence can be sealed.
2. **Prompt-length re-measurement with the pick's tokenizer.** It rebuilds the exact sweep-2 manager prompt texts
   from the **pinned harness** (`_prepare_context`, node specs and parsed node constants) and measures them through
   the owned server's **`/apply-template`** (rendered prompt, `enable_thinking: false`) and **`/tokenize`**
   (`add_special: true`) endpoints. **Three** variants per node: `trial_1` (no memory — exact for every sweep-2
   campaign's first call), `memory_on_declared_12` (a declared 11-record `append_only_summary` history — a *middle*
   class) and **`memory_on_budget_20` (the declared 19-record W = 20 / budget-20 history — the longest sweep-2
   prompt class)**. The rendered prompt must contain the exact user text (a template that mangled/normalised it is a
   STOP); a prompt that does not fit 32,768 tokens is a STOP with the measurement persisted.
3. **Comparison with the sweep-1 prompt-length record** (pinned, SHA-256 checked): per node, the rebuilt trial-1
   prompt text is **byte-identical** to the text the sweep-1 liveness run actually sent (the ledger's
   `extra.manager.context_sha256` is compared), so the pick-vs-sweep-1 token comparison is on identical text; the
   pinned record's per-node memory-on maxima are reported for scale, and the comparison reports the true pinned
   baseline: **1,345 is the 14 Oct rerun-2 prompt set's budget-12 value, not a maximum and not the sweep-2 text**,
   while the **true recorded W = 20 maximum is 1,886** (`tabular_mlp__s112`, budget 20, 7B tokenizer; over the 54
   pinned rerun-2 root ledgers). The 32k fit conclusion is the headroom line (even 1,886 tokens leaves >17x
   headroom). A missing or changed sweep-1 record is a STOP — the unit never invents a baseline. The job also
   cross-checks `/tokenize(add_special=True)` against its **own** liveness-ledger `usage.prompt_tokens` for the same
   trial-1 call (both numbers recorded, BOS question settled in-run).

Outputs inside the job: `job_record.json`, `out.tar`, `work.tar`, `SHA256SUMS`, `llama-server.log` (transferred);
`out/s2_c3b_prompt_lengths.json`, `out/s2_c3b_sweep1_comparison.json`, `out/S2_C3B_PROMPT_REPORT.md` (sealed inside
`out.tar`); the job record carries host/GPU/CPU/image/model/server identity, the liveness verdicts, the prompt token
counts (all three classes), the in-run usage cross-check, the seed plan and the accepted `level_layout`. `seal` reuses the reviewed S2-C2 seal step (S2-C3b record guards + S2-C2 transfer/SHA
verification, `.`/`..`/symlink refusal, no overwrite) and marks the receipt `s2_c3b_seal_receipt/1`.

## Files

| file | role |
|---|---|
| `sweep2/s2_c3b_lib.py` | spec `s2_c3b/v1` validation (reuses `s2_c2_lib.validate_spec` through a C2-shaped view for every image/model/server/requirements/liveness pin, then adds the S2-C3b pins and seed/prompt checks), seed plan + disjointness check, liveness argv/verdict, pinned-harness prompt builder, `/apply-template` + `/tokenize` client, sweep-1 comparison, job record/tars/SHA256SUMS, `seal` (S2-C2 reuse) |
| `sweep2/s2_c3b_job.sh` | container-job entry point (pre-creates the five transferred outputs) |
| `sweep2/render_jdl.py` | extended with `--kind c3b` (stages `s2_c3b_job.sh`, `s2_c3b_lib.py`, `s2_c2_lib.py`, `s2_c3b_spec.json`; fixed requirements/`+RemoteJob`/transfer template; the `c2` default is unchanged and still covered by the S2-C2 tests) |
| `sweep2/spec.c3b.example.json` | reviewed ENGINEERING spec (frozen v1 gpu digest `69b06b35…`, B2 harness `a3fedbb…`, pick GGUF `2959c1b0…`, paper `9ae6d877`, L40S/NEMO2/CPU-class pins, 8-node liveness, 32k exam setting, seeds, prompt record pins) |
| `sweep2/dryrun/c3b/` | staged inputs, rendered JDL and the real `condor_submit -dry-run` ad |
| `sweep2/evidence/s2c3b_seed_check_20261116.json` | the seed-disjointness check actually produced by the reviewed spec |
| `sweep2/evidence/s2c3b_sweep1_records_20261116.md` | read-only record locations/SHA-256 of the sweep-1 liveness + prompt-length sources (repo and deepthought batch tree) |
| `r1/tests/htcondor/test_s2_c3b.py` | 94 synthetic tests (spec negatives incl. extra server kwargs / below-floor layout / superseded 16k layout, seed checks, argv-vs-CLI, 8-node shortfall STOP + evidence persistence, end-to-end synthetic STOP with kill-before-SHA256SUMS and a real `seal`, tokenizer/compare math incl. the W = 20 class and the corrected 1,345/1,886 record, liveness-usage cross-check, prompt builder with a fake pinned harness, seal guards, renderer) |

## Declared seed choice and the disjointness check (read this before the review)

**Sweep-2 instance seeds (the set to stay clear of).** R1-MAIN-PROPOSER (b) fixes sweep 2 to **sweep 1's instance
seeds**, and the pinned paper code derives them (`_instance_seed(node, k) = 100 + 10*k + Σord(node) % 7`, k = 0…17,
18 instances per node). The full list is therefore *derived, not stored as a list*; the sources recorded and checked
are: the paper function (SHA-256 `000126…`), the sweep-1 index
`results/r1/pilot/C3_sweep_index_20261028T033315Z.json` (18 instances/node, 8 nodes, audit seeds 7001–7010;
SHA-256 `812468…`) and the S2-C4 roots `digits_mlp__s104/s114` (k = 0,1). The derived universe has **90 distinct
seeds**, pinned in the spec by SHA-256 `0d7f0e59…` and recomputed by the validator (the job re-checks it against the
sweep-1 liveness manifest campaign seeds).

**Chosen liveness instance seeds — a declared conflict with the literal instruction.** The D28 run must go through
`r1.liveness`, whose CLI has no seed argument: it calls `run_root(node, k)` for k = 0,1, so its instance seeds are
**the first two sweep instance seeds per node** — exactly what sweep 1's D28 liveness used (manifest `s104/s114`, …).
Those 10 seeds (`{100,102,…,115}`) are a subset of the 90-seed sweep universe; **no disjoint liveness instance-seed
set is implementable without changing the pinned harness**, and doing so would break comparability with the sweep-1
D28 record. The unit therefore (i) declares the reuse (`liveness_seed_policy = "sweep1_d28_reuse"`, per-node seed
pairs pinned in the spec), (ii) **refuses a false disjointness claim** — a spec that says `strict_disjoint` is a
STOP with an explanation — and (iii) proves what *can* be proved: no audit seed 7001–7010, no exam seed in the
9001–9303 block (the guard is open-ended: any seed ≥ 9001 STOPs) and no G.1b training seed 8001–8010 is touched, and
the liveness seeds equal the sweep-1 D28 record. This is disclosed
as a residual point for the author: the overlap is the frozen D28 design (liveness checks the *sweep's* instances),
the liveness runs are ENGINEERING_ONLY and never enter a label table, so the overlap is not a label leak.
See `sweep2/evidence/s2c3b_seed_check_20261116.json` for the full check (it includes the 90-seed list and the exact
overlap).

**Chosen prompt-measurement seeds — disjoint.** `6101–6108` (one per node) are disjoint from the 90 sweep instance
seeds, the audit block 7001–7010, the exam block 9001–9303 (open-ended guard ≥ 9001) and the G.1b block 8001–8010;
the check is recomputed by the validator and a collision STOPs. They are *prompt-instance* seeds only: the sweep-1 record shows the trial-1 prompt
text does not depend on the instance seed (both instances of every node recorded the same trial-1 prompt tokens and
the same `context_sha256`), so measuring under a disjoint seed block still measures exactly the sweep-2 prompt.

## Prompt texts and tokenizer method

- The manager stack sends **one user message** (`_prepare_context` `context_text`); there is no separate system
  message, the system/user scaffolding is the GGUF chat template rendered by the server.
- The texts are rebuilt **only** from the pinned harness at `a3fedbb…` (same `_prepare_context` lines as the sweep-1
  harness `6adf385` — checked; the node configs and `nodes/<node>/train.py` are unchanged between the pins), so they
  are the sweep-2 texts, not a copy of a prompt string.
- Server-side measurement: `POST /apply-template` with `messages=[{"role":"user","content":<text>}]`,
  `add_generation_prompt=true`, `chat_template_kwargs={"enable_thinking": false}` → the exact prompt the server
  tokenizes; then `POST /tokenize {content: <rendered prompt>, add_special: true}` → the pick's token count. The raw
  user text is tokenized too (`add_special: false`) and the template prefix is decomposed, so the record has
  manager/user/system components and the authoritative rendered count. A prompt at or over 32,768 tokens is a STOP.
- Exactness proof: for all eight nodes the rebuilt trial-1 prompt SHA-256 equals the sweep-1 liveness ledger's
  `extra.manager.context_sha256` (8/8, checked locally while implementing and re-checked in the job;
  `compare_with_sweep1` STOPs if it ever differs).

## Sweep-1 prompt-length comparison source (located; nothing invented)

The sweep-1 baseline is fully present in the pinned checkout (and byte-identical in the deepthought batch tree
`/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/agent_paper_B/results/...`;
SHA-256 compared read-only, see `sweep2/evidence/s2c3b_sweep1_records_20261116.md`):

1. **Sweep-1 D28 liveness record** `results/r1/engineering/liveness_c3_20261027T152425Z/` — `liveness.json`
   `3f64604e…`, `manifest.json` `154f5f48…`, 16 ledgers (per-node SHA-256 pinned in the module). Per-call
   `usage.prompt_tokens` gives the per-node trial-1 prompt length (514/520/482/481/484/489/497/513) and the per-node
   memory-on maximum (1029–1179).
2. **The 1,345 figure is the 14 Oct rerun-2 budget-12 value, not a maximum and not the sweep-2 text.** It is the
   `proposal.extra.llm_call.prompt_tokens` / `provisional.extra.manager.llm_call.prompt_tokens` value of
   `results/r1/pilot/E1b_rerun2_A_PARTIAL_memory_on_20261014/provenance/snapshots/tabular_mlp__s142/E2_b012/manifest.json`
   (SHA-256 `5e269d4c…`), i.e. the **budget-12** call of the **14 Oct** prompt set. The same pilot's W = 20 calls are
   longer: the 54 pinned rerun-2 **root ledgers**
   (`.../provenance/ledgers/roots/`, `tabular_mlp__s142/root_trials.jsonl.gz` git blob `1da59574…`, .gz SHA-256
   `bd0408a0…`) record
   `tabular_mlp__s142` budget 12 → 1,345 and budget 20 → 1,878, and the maximum over all 54 roots is **1,886**
   (`tabular_mlp__s112`, budget 20). The 54-root (instance, .gz sha256) list is pinned by aggregate SHA-256
   `04d4ccd9…` and re-verified by the unit, which STOPs if any pinned value drifts.
3. **The 14 Oct prompt set is not the 27 Oct liveness/sweep-2 text.** For `openml_breast_w` the trial-1 rerun-2 text
   is `d31c77a3…` / 483 tokens while the 27 Oct liveness text is `61aa9226…` / 482 tokens; both are pinned and the
   unit STOPs if they are identical. The per-node trial-1 byte-identity check is therefore made against the pinned
   **27 Oct liveness ledgers only**, and the 1,345/1,886 figures are used as a **scale reference for the 14 Oct
   rerun-2 record**, never as "the sweep-2 text" or "the maximum".
   There is no separate prompt-length artefact in the batch tree or the repo (`find` for `*prompt*` under the
   sweep-1 batch `results` found none); the record is these per-call ledgers plus the rerun-2 snapshot/root ledgers.
   Nothing is missing from the comparison.

## Execution steps (only after this unit is reviewed and accepted)

1. Stage + render on the submit host:
   `python3 sweep2/render_jdl.py sweep2/spec.c3b.example.json --out <desired>.jdl --stage-dir <fresh-stage> --kind c3b`
2. `condor_submit <jdl>` from the stage dir (after the review; no real submission is authorised by PLAN yet —
   EVIDENCE stays gated and this unit is ENGINEERING).
3. Copy the transferred job output directory and seal:
   `python3 sweep2/s2_c3b_lib.py seal <job-output> --run-id s2c3b-20261116-a --chunk-id liveness-prompt`
   (writes `/ceph/srv/dwong/paperb/sweep2/s2c3b-20261116-a/liveness-prompt/`, verifies `SHA256SUMS`, no overwrite).
4. Read `S2_C3B_PROMPT_REPORT.md` / `s2_c3b_sweep1_comparison.json` in the sealed `out/`; the author decides on any
   liveness shortfall (no node is dropped silently).

## Reviewed dry-run evidence (deepthought, no submission)

**Re-rendered after review round 1** from the current code+spec (`sweep2/render_jdl.py … --kind c3b`), then
`condor_submit -dry-run s2_c3b.dryrun.txt s2_c3b_eng_example.jdl` from the fresh staging dir
`/tmp/s2c3b_dryrun_r2_20261116T1205Z` on deepthought → rc 0, "1 job(s) dry-run to cluster 1". **No job was
queued** (a dry run only renders the ad). The ad (`sweep2/dryrun/c3b/s2_c3b.dryrun.txt`) shows `JobUniverse=5`,
`WantContainer=true`, `ContainerImage=docker://ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35…`, `RequestCpus=16`,
**`RequestDisk=42460977`**, `RequestMemory=32000`, **`RequestWalltime=12203`**, `RequestGPUs=1`, `+RemoteJob=true`,
requirements `CloudSite Nemo2 && GPUs_DeviceName L40S && Arch X86_64 && OpSys LINUX && Cpus>=16 && CpuFamily=6 &&
CpuModelNumber=207`, transfer outputs `out.tar,work.tar,job_record.json,SHA256SUMS,llama-server.log`, **no**
`ProvidesEtpCeph`. This is the accepted R1-SWEEP2-LAYOUT 32k layout (the superseded S2-C4 16k ad is gone).

## STOP conditions (fail-closed; evidence is persisted where it exists)

- Spec drift: wrong schema/kind/label, any pin (image digest `69b06b35…`, llama-server sha, B2 harness `a3fedbb…`,
  pick GGUF `2959c1b0…`, paper `9ae6d877`), exam-setting drift (ctx 32,768, `-ngl 999`, `--jinja`,
  `enable_thinking:false`, q8_0, allowlisted flags), wrong GPU/CPU class or cloud site, a chunk-style EVIDENCE label,
  a `requires_etp_ceph` requirement, wrong liveness dimensions or `min_live_nodes != 8`, `b2_audits != "none"`.
- Layout: any request other than the accepted R1-SWEEP2-LAYOUT 32k values (`12203 / 42460977 / 32000`), a layout
  below the measured floors, or a spec with extra server-level `--chat-template-kwargs` (the accepted wrapper
  requires exactly `{"enable_thinking": false}`).
- Seeds: a `strict_disjoint` liveness policy (not implementable), any declared seed in 7001–7010 / 9001–9303
  (open-ended ≥ 9001) / 8001–8010
  or in the sweep universe (prompt seeds), a changed sweep-2 seed law, a liveness seed set different from the
  frozen D28 seeds or from the sweep-1 liveness manifest.
- Run: `r1.liveness` non-zero exit, malformed / non-ENGINEERING / non-LLM-backed `liveness.json`, a wrong schema or
  unexpected extra node in `liveness.json`, any node failing (`< 8` live), a prompt that cannot be rebuilt from the
  pinned harness, `/apply-template` or `/tokenize` unavailable or malformed, a rendered template that does not
  contain the exact user text, a rendered prompt at/over 32,768 tokens, a missing/changed seed or prompt
  record (including the 1,345 b012 value, the 1,886 W=20 maximum or either `openml_breast_w` prompt text). On each
  post-run STOP the owned server is killed **first** and then the record + `out.tar` + `work.tar` + `SHA256SUMS` are
  written before raising, so the transferred sums verify and the evidence can be sealed; the sandbox output and the
  sealed attempt are kept, never overwritten.
- EVIDENCE/none: this unit never resolves an EVIDENCE label (`label_source.authorization = null`) and the seal
  accepts ENGINEERING_ONLY records only.

## Residual risks (disclosed, not resolved by this unit)

- **Liveness instance-seed overlap** with the sweep-2 instance seeds (10 of 90) is structural (see the seed section).
  It is the sweep-1 D28 design, ENGINEERING-only and not a label path; it is declared rather than hidden.
- **Prompt-length record availability:** the sweep-1 record exists (liveness ledgers + rerun-2 snapshot/root
  ledgers + RUNBOOK note) but the exact *memory-on* prompt texts are not stored, only their token counts and
  `context_sha256`. The unit therefore compares on identical text at trial 1 and uses declared fixtures (11-record
  middle class and 19-record W = 20 longest class) for the memory-on scale check; the true recorded W = 20 maximum
  (1,886, 7B tokenizer) comes from the pinned 54 rerun-2 root ledgers and is a *14 Oct* prompt-set number, not a
  byte-exact replay of the sweep-2 W = 20 text. A byte-exact per-call memory-on replay is not attempted (it would
  require replaying the patched node state).
- **Tokenizer-endpoint differences:** `/apply-template` + `/tokenize` counts are the server's tokenization, not the
  OpenAI `usage.prompt_tokens` field. BOS handling/template-version effects are no longer merely disclosed: the job
  cross-checks `/tokenize(add_special=True)` against its **own** liveness-ledger `usage.prompt_tokens` for the same
  trial-1 text and records both numbers (`liveness_prompt_token_cross_check`, delta and ≤1-token BOS flag) in the
  job record and the prompt report. The comparison is a tokenizer/chat-template comparison on identical text, and
  the pick's GGUF/chat template is pinned by the image and model pins. A different chat template in the pick GGUF
  than in the sweep-1 manager is the intended difference.
- **8-node liveness cost:** sweep 1's D28 run took 1,424 s of campaign wall time on deepthought (CPU-bound); the L40S
  job also pays the 19.6 GB GGUF fetch/load. The layout is now the **accepted R1-SWEEP2-LAYOUT 32k measurement**
  (`request_walltime 12,203 s`, `request_disk 42,460,977 kB`, `request_memory 32,000 MB`), produced by the accepted
  S2-C2 32k smoke (`sweep2-main-20261116` @ `f172d299`, clusters 759728/759729; both modes rc 0, offload 61/61,
  KV 1,360 MiB; 9,387 s per full chunk, 41.72 GPU-h over 16 chunks). The superseded S2-C4 16k layout is gone, and
  the earlier "re-measuring at 32k remains a prerequisite" text was false and has been removed. The C3b job is
  roughly a quarter of a chunk, so the 12,203 s request has large margin.
- **Queueing / cluster availability (not a unit defect):** the last inherited capture showed only 3 fully matching
  L40S slots (`g3608`×2, `g3610`×1); the run may wait in the queue or start on a partially matching slot. Confirm
  the queue and GitHub egress on the submit host at run time; this unit cannot do it without submitting.
- **Liveness failure is not repaired here:** a shortfall STOPs for the author (no node dropped, no retry beyond the
  collector's own A.5/resume semantics). The unit is a deployment check, not a fix.

## Tests

`r1/tests/htcondor/test_s2_c3b.py`: **94** synthetic tests, no GPU/network/server. They cover spec-validation
negatives (incl. extra server `--chat-template-kwargs`, below-floor disk/memory and the superseded S2-C4 16k
layout), the seed check and its negatives (including the impossible-disjointness refusal, the open-ended exam-seed
guard and the real sweep-1 manifest), the liveness argv against the pinned CLI's own flags (no `--deadline`), the
8-node shortfall and evidence persistence, an **end-to-end synthetic STOP** (fake server/liveness) that proves the
owned server is killed *before* `SHA256SUMS` is written and that the real `seal` verification then succeeds, the
tokenizer client/compare math and the prompt-fitting/template-mangling STOPs, the W = 20 prompt class and the
corrected 1,345-b012 / 1,886-W20 record (incl. the `openml_breast_w` 14 Oct-vs-27 Oct difference), the in-run
liveness-usage cross-check, the pinned-record provenance (missing/changed record STOPs), the pinned-harness prompt
builder with a fake harness, the seal guards, and the c3b JDL template. Run with the existing test venv:

```
/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/sweep2-cluster-20261116/.venv-test/bin/python \
  -m pytest r1/tests/htcondor -q        # 129 passed (29 S2-C2 + 6 S2-C4 + 94 S2-C3b)
```

**No run claims:** no HTCondor job was submitted, no llama-server was started, no GPU was used, no B.2 audit ran, no
label (sweep-1 or sweep-2) was read by this unit, and no EVIDENCE claim is made.


## Authority update — R1-S2C3B-SEEDS accepted (16 Nov 2026, `author-decisions-20261116b` @ `025bfc16`)

`liveness_seed_policy = "sweep1_d28_reuse"` is **accepted**: the pick's 8-node D28 liveness reuses sweep 1's
per-node first two instance seeds (r1.liveness has no seed flag), keeping it comparable with sweep 1. The liveness
output never enters a label table, training or selection, and touches no 7001–7010 / 8001–8010 / 9001–9303 seeds
(the collision guard is open-ended: any seed ≥ 9001 STOPs); the
overlap with the sweep-2 instance seeds must be disclosed in the sweep-2 report. This supersedes the earlier
residual concern about "disjoint liveness seeds"; no code change is required.

## Review round 2 fixes — `S2_C3B_REVIEW_20261116.md` (verdict NOT ACCEPTED; 4 majors + minors)

The independent review at branch `s2c3b-live-20261116` @ `066bac28` found no run-safety blocker but 4 majors and 8
minors. All were fixed on branch `s2c3b-fix-20261116`, which was **rebased onto the accepted wrapper tip**
`sweep2-main-20261116` @ `9a79cfe0` (round-5.1 + 32k layout + `_kill(None)` guard) before the fixes; the commit
message chain records the mapping. The unit is re-reviewed as a whole; this section is the point-by-point record.

| id | review finding | fix (what is now true) |
|---|---|---|
| **M1** | superseded S2-C4 16k layout (`walltime 10,776 s`, `disk 42,439,718 kB`) in spec/ad/doc, and the false "re-measuring at 32k remains a prerequisite" risk | spec now carries the accepted **R1-SWEEP2-LAYOUT** values `request_walltime_s 12203`, `request_disk_kb 42460977`, `request_memory_mb 32000` (measured 32k layout from accepted S2-C2 smoke `f172d299`: 16 chunks, 9,387 s/chunk, 41.72 GPU-h); `validate_spec` refuses anything but that exact layout, and a c3b test pins it; `sweep2/dryrun/c3b/` JDL+staged spec re-rendered from current code+spec and the `condor_submit -dry-run` ad re-run (rc 0, `RequestDisk=42460977`, `RequestWalltime=12203`); the renderer test asserts the new values; the false residual-risk text is removed and replaced by the accepted measurement; the job record carries `level_layout {request_walltime_s 12203, request_disk_kb 42460977, request_memory_mb 32000}` (minor m5) |
| **M2** | the prompt re-measurement covered only the 11-record fixture (a *middle* class), and called 1,345 "the recorded maximum"; 1,345 is the 14 Oct prompt set, which is not the sweep-2 text | **third prompt class added — `memory_on_budget_20`, the W = 20 / 19-record longest class** (same declared-fixture builder, budget 20); the true pinned W = 20 maximum is now recorded and re-verified: **1,886** (`tabular_mlp__s112`, budget 20) over the **54** pinned rerun-2 root ledgers (aggregate SHA-256 `04d4ccd9…`; `tabular_mlp__s142` root `bd0408a0…` records budget-12 1,345 → budget-20 1,878); **1,345 is relabelled the b012 value, explicitly not a maximum**; the corrected provenance is machine-checked: `openml_breast_w` trial-1 is `d31c77a3…`/483 tokens in the 14 Oct rerun-2 set vs `61aa9226…`/482 in the 27 Oct liveness/sweep-2 text, and the unit STOPs if they ever agree; tests cover the W = 20 class, the corrected comparison and the record STOPs |
| **M3** | branch 3 commits behind the accepted wrapper, so the C3b gate lacked round-5.1's exact `{"enable_thinking": false}` kwargs check, measured disk/memory floors and the `_kill(None)` guard | branch **rebased/merged onto `origin/sweep2-main-20261116` @ `9a79cfe0`** (clean merge, no conflicts; C3b files preserved). The reused `s2_c2_lib.validate_spec` now enforces exact `{"enable_thinking": false}` and the measured floors; `_kill(None)` is guarded by `e713239f`. c3b-level tests added: extra server-level `chat_template_kwargs` refused, below-floor disk/memory refused, superseded 16k layout refused |
| **M4** | post-run STOP persisted `SHA256SUMS` while the owned llama-server was still running, so `llama-server.log` could change after hashing and `seal` would refuse the sums | `run_liveness_job` now has a `stop()` helper that **kills the owned server (None-guarded) before `_persist`/`_write_sums`** on every post-server-start STOP path (rc≠0, unreadable/malformed verdict, node shortfall, prompt rebuild/measurement STOP, ctx-fit STOP, comparison STOP); the success path is unchanged (persist after the `finally` kill). A new end-to-end synthetic STOP test (fake server/liveness) proves (a) the kill happens before `SHA256SUMS`, (b) the dying server's last log line is inside the hashed log and (c) the **real** C2 `seal` (`sha256sum -c` verification) then succeeds |
| m1 | doc test arithmetic "105 (34 + 6 + 71)" was impossible | actual post-rebase full-suite count is now recorded: **129 passed = 29 S2-C2 + 6 S2-C4 + 94 S2-C3b** (verified in this worktree) |
| m2 | no STOP when the rendered template dropped the user text | `measure_prompts` STOPs when the rendered prompt does not contain the user text verbatim (test added) |
| m3 | tokenizer-vs-`usage.prompt_tokens` (BOS) disclosed but unresolved | in-run cross-check added: `/tokenize(add_special=True)` vs the job's own liveness-ledger `usage.prompt_tokens` for the same trial-1 text; both numbers, delta and ≤1-token BOS flag are recorded in the job record/report (`liveness_prompt_token_cross_check`) |
| m4 | no test of the `run_liveness_job` STOP wiring | covered by the end-to-end synthetic STOP + seal test (M4 above) |
| m5 | no `level_layout` in the job record | added (see M1), visible in the sealed record as well as the JDL/ad |
| m6 | `evaluate_liveness` ignored schema and extra nodes | schema must be exactly `r1.liveness/2` and unexpected extra node keys STOP (tests added) |
| m7 | exam-seed block claimed as "9001+" | classified everywhere as **9001–9303**; the collision guard is open-ended (any seed ≥ 9001 STOPs) and recorded in the seed check (`exam_seed_guard`) |
| m8 | sweep-2-report disclosure vehicle had no C3b line | `S2_ENGINEERING_PILOTS_DISCLOSURE.md` now carries the S2-C3b disclosure line (ENGINEERING-only, 10-of-90 seed reuse accepted by R1-S2C3B-SEEDS, no label path, no 7001–7010) |

**Verification for this fix round:** full synthetic suite in the worktree venv
(`/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/sweep2-cluster-20261116/.venv-test/bin/python -m
pytest r1/tests/htcondor -q`) → **129 passed**; `validate`/`seeds` CLI on the updated spec unchanged in outcome
(seed check reproduces exactly); JDL re-render byte-identical to the committed dry-run JDL; `condor_submit -dry-run`
rc 0 with the accepted layout, no job queued. **No execution:** no HTCondor job was submitted, no llama-server
started, no GPU used, no B.2 audit, no label read; the only remote writes were the `/tmp` staging dir for the
dry-run ad (`/tmp/s2c3b_dryrun_r2_20261116T1205Z`), nothing queued.
