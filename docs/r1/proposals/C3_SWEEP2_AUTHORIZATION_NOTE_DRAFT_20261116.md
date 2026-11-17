# Draft authorization note: C3 sweep 2 (HTCondor, L40S). Version 5, per the author rows of 17 November

**This is a draft, not an authorization.** The Mac agent (Claude, AI-assisted) prepared it as unit S2-M1 of the
sweep-2 work plan (`prompts/SWEEP2_HTCONDOR_RUNBOOK_20261116.md`).
- It updates version 4 (`mac-s2-m1-v4-20261116`, accepted at `26c83a26`, final text `6eee770c`, on `main` since the
  merge `a17991ba`).
- It applies the author rows of 17 Nov:
  - **R1-SWEEP-HOST-L40S-SITES:** the job requirements pin the GPU model (L40S), not the site; the deepthought2 and
    NEMO2 L40S are both allowed; each campaign records its site, node, GPU name and UUID, driver and CPU model; if the
    two sites' CPU models differ, both are allowed and the report discloses it;
  - **R1-S2C3B-LAUNCH:** the S2-C3b liveness is rerun once at the launch commit, with the launch's image digest,
    harness pin and server settings; no earlier pass replaces it;
  - **R1-SWEEP2-RESOURCES:** `request_disk` and `request_memory` = the re-measured smoke's peak × 1.4, rounded up;
  - **R1-SWEEP2-STOP-PRECEDENCE:** a STOP cause wins over a rerun;
  - **R1-E1-OPENML-AMEND**, where it bears on precondition 7.
- Kept from version 4: the R1-SWEEP2-LAYOUT-AMEND rules (layout void until the re-measurement, worker gates,
  walltime = 1.5 × the re-measured chunk time, whole-chunk rerun, byte-identical thinking switch), the liveness seed
  policy `sweep1_d28_reuse` with its disclosure, and no B.2 audits.
- Placeholders kept: the re-measured layout, the image digest (v1 `69b06b35…` proposed), the `run_id` and the launch
  commit.

**How the author uses it:**
- Copy the block between the two rules below to `docs/r1/authorizations/c3_sweep2_<date>.md` on `main`.
- Fill every `<…>` placeholder, and add your own prose to the opening paragraph.
- Set `approved: true` yourself. This draft keeps `approved: false`, and the agent never sets it.

The format follows `authorizations/c3_sweep1_20261027.md`: an opening paragraph, "Proposed scope and pins",
"Boundaries and STOPs". A key block is added because two cluster programs read fields from the note:
- the S2-C2 job wrapper (`sweep2/s2_c2_lib.py`, `resolve_label`): `approved: true`, the run id and `label: EVIDENCE`;
  it also refuses a note whose sha256 differs from the job spec's;
- the S2-C5 switch (`sweep2/s2_c5_switch.py`, `parse_note`, on `s2c5-switch-20261116` @ `84a0dc30`, not on `main`):
  it requires `approved`, `label`, `run_id`, `image`, `layout_request_walltime_s`, `layout_request_disk_kb`,
  `layout_request_memory_mb`, `layout_chunks`, `layout_gpu_hours`, `b2_audits` and `d8_lock`, and `P1:`–`P7:`, each
  starting with `PASS`. It reads every line of the form `key: value`, so no other line of the copied block may start
  that way.

**Order of commit and launch** (R1-S2C3B-LAUNCH). The S2-C3b liveness runs at the launch commit, `main` HEAD at
launch, and nothing may change that HEAD between S2-C3b and the launch. So:
1. the fix units are integrated into `main`;
2. the note is committed: on `main`, or on an `author-*` branch, which the S2-C5 switch also accepts and which leaves
   `main` HEAD unchanged;
3. S2-C3b runs at that `main` HEAD;
4. the launch follows with no commit to `main` in between.

The note therefore cannot record S2-C3b's result. That result goes into the launch record (precondition 3).

**Authority.**
- Read from `main` @ `16185b0b`, which carries all author rows to date, including those of 17 Nov. PLAN §10 rows take
  precedence over this note wherever they differ.
- The rows used are:
  - R1-SWEEP-HOST-L40S-SITES, R1-S2C3B-LAUNCH, R1-SWEEP2-RESOURCES, R1-SWEEP2-STOP-PRECEDENCE and R1-E1-OPENML-AMEND
    (17 Nov);
  - R1-SWEEP2-LAYOUT-AMEND (16 Nov (3)), which voids the numbers of R1-SWEEP2-LAYOUT;
  - R1-S2C3B-SEEDS, R1-S2C3-DRIVER and R1-E1-OPENML (16 Nov (2));
  - R1-SWEEP2-SETTINGS (1)–(5), as amended by R1-S2C3B-SEEDS and R1-SWEEP2-LAYOUT-AMEND, and R1-SWEEP-HOST-HTC as
    amended by R1-SWEEP-HOST-L40S-SITES;
  - R1-SWEEP1-CLASSIFY (label from the authorization only);
  - R1-EXAM-X7;
  - R1-MAIN-PROPOSER (b), (c), (e), (g), as amended by R1-SWEEP2-SETTINGS;
  - R1-BX-D8, R1-BX-PROPOSED-CONFIRM, R1-BX-D8-V3-A and R1-BX-D8-V3-B;
  - R1-CACHEPROMPT-FALSE, R1-EXAM-CACHE-REV and R1-EXAM-B1-HARNESS-PIN;
  - R1-B1-CORPUS-FREEZE;
  - R1-HARNESS-NEXT-PIN, R1-B2-DECOUPLE, R1-B2-REPLAY-GO and R1-E1-AUTH.
- Measured server facts (CPU identity, build line, GPU buffers) come from the cluster's S2-C2 32k smoke (clusters
  759728/759729): `sweep2-main-20261116` @ `f172d299`, `reports/sweep2_20261116/SMOKE_RESULTS_20261116.md` and
  `smoke_20261116/` (both job records). The wrapper that ran it is the cluster's S2-C2 round 5, accepted by independent
  review (`reviews/S2_C2_REVIEW_20261116.md`, round 5 at `8a8ea832`, minors at `d9a17b86`). That smoke's timing is void
  (R1-SWEEP2-LAYOUT-AMEND): every visible in-campaign worker run ended in ≤ 0.1 s with `success=False`.
- The state of the cluster fix units is read from `sweep2-main-20261116` @ `cbb40d28` (not on `main`).

Each value below cites its source.

---

# Authorization: C3 sweep 2 (HTCondor, L40S)

<Author's opening paragraph: date and time, the instruction, and what was read. Proposed facts to cite:
- `main` at `<launch commit>` carries the S2-M2 integration (`9ae6d877`), the accepted S2-C2 wrapper (round 5 and
  the fix units below) and the S2-C5 switch (this is `paper.evidence_ready`);
- preconditions 1, 2 and 4–10 below are met: `<reports, reviews>`; precondition 3 (S2-C3b) runs after this note is
  committed, at the launch commit, and its result goes into the launch record.
The paper commit is determined at launch.>

```
approved: false
label: EVIDENCE
run_id: <run id, e.g. s2ev-<YYYYMMDD>-a; every job spec and job record carries it>
phase: c3_sweep2
image: <author: digest; proposed v1, see "Image" below>
layout_request_walltime_s: <1.5 × the re-measured chunk time, s>
layout_request_disk_kb: <the re-measured disk peak × 1.4, rounded up, kB>
layout_request_memory_mb: <the re-measured memory peak × 1.4, rounded up, MB>
layout_chunks: <16, unless the re-measurement requires a chunk split>
layout_gpu_hours: <chunks × the re-measured chunk time / 3600>
b2_audits: none (this authorization carries no B.2 audits)
d8_lock: true
P1: <PASS — R1-SWEEP-HOST-HTC as amended by R1-SWEEP-HOST-L40S-SITES>
P2: <PASS — main at the launch commit contains the S2-M2 integration and the accepted fix units>
P3: <PASS — this note>
P4: <PASS — S2-C3 deployment check on the L40S used: report, review>
P5: <PASS — re-measurement and layout per R1-SWEEP2-LAYOUT-AMEND and R1-SWEEP2-RESOURCES: report, review>
P6: <PASS — S2-C5 switch enabled for this run id only>
P7: <PASS — image digest frozen above>
```

## Proposed scope and pins

- **Host.** HTCondor job submission (R1-SWEEP-HOST-HTC, as amended by R1-SWEEP-HOST-L40S-SITES).
  - **GPU model pinned, not the site.** LLM-backed label runs run on an L40S at either site, deepthought2 or NEMO2.
    "One table, one host" means one GPU model, the L40S. The job requirements pin `GPUs_DeviceName == "NVIDIA L40S"`,
    `Arch == "X86_64"`, `OpSys == "LINUX"` and `Cpus >= 16`. They no longer pin `CloudSite` or the CPU class (fix
    item 2i; the round-5 `render_jdl.py` pins `CloudSite == "BwForCluster-Nemo2"`, `CpuFamily` 6 and
    `CpuModelNumber` 207).
  - **Recorded for every campaign:** site, node, GPU name and UUID, driver and CPU model (R1-SWEEP-HOST-L40S-SITES).
    The round-5 job record already holds host name and FQDN, GPU name, UUID and driver, and CPU model, family and
    model number, per job; the site and the copy into each campaign's record are fix item 2i.
  - **CPU model: recorded and disclosed, not pinned.** On NEMO2 the two smoke hosts (`g3608`, `g3610`) report
    `INTEL(R) XEON(R) PLATINUM 8562Y+` (family 6 / model 207). The deepthought2 L40S CPU model:
    `<from the cluster's ad snapshot or a job record>`. If the two differ, both are allowed and the sweep-2 report
    discloses which campaigns ran on which (R1-SWEEP-HOST-L40S-SITES). The run-time CPU check becomes a record, not a
    STOP.
  - A job on a GPU other than the L40S is a STOP.
  - Selection ran on a 4090 (B1/B2 on TASL-7) and deployment runs on the L40S. This is disclosed. The S2-C3 deployment
    check is done on the L40S actually used (R1-SWEEP-HOST-L40S-SITES).
- **Paper commit.** `main` HEAD at launch. It must contain the S2-M2 integration (`9ae6d877`), the accepted S2-C2
  wrapper and its fix units, and the S2-C5 switch (`<launch commit>`). It is recorded in every job record.
- **Harness.** `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` (`cacheprompt-20261031`, the B2 stack): an explicit
  `cache_prompt: false` on every request.
  - `r1/scripts/HARNESS_PIN_C3` on `main` carries this value.
  - No PLAN row names `a3fedbb` as the sweep-2 pin. The value comes from the S2-C2 validator and from the author's
    S2-M2 answer of 16 Nov, which put it into `HARNESS_PIN_C3`.
  - R1-MAIN-PROPOSER (c) requires a check that the harness defaults used by the sweep are unchanged:
    `<check, report, review>`.
- **Image (S2-C1). For the author.**
  - GPU image: `<author: digest>`. Proposed: v1,
    `ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296`, which ran
    S2-C4 and the 32k smoke. If a fix unit changes the image, the digest changes with it. The S2-C5 switch hard-codes
    v1 as `FROZEN_IMAGE` (precondition 6).
  - Identity markers, as in the smoke job records: `llama_server_sha256`
    `f8d35fd33e866808bc76457cf52cf1f8b1baafde9c2c8eebae51abf428843cc0`, `versions_sha256`
    `d31e8b2336c1a1a698163ef8c20f2cdf067bed9539e73bb7b545aeffb117dcc2`.
  - One digest for the table. No switch during the sweep.
- **llama.cpp.** Commit `620d2225cc436ab0b001e3200e590e3b286ef9ab` (in the image). The server reports the build line
  `0.7.0-dev (build 11669, commit 620d2225c)` (smoke job records, `server.build`).
- **Manager: the pick `gemma4_31b`, thinking off** (R1-EXAM-X7, R1-MAIN-PROPOSER).
  - GGUF: `bartowski/google_gemma-4-31B-it-GGUF` @ `619aca7589c72be65dd968de8602ad23d68b5c14`, file
    `google_gemma-4-31B-it-Q4_K_M.gguf`, size 19,598,489,952 B, SHA-256
    `2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75`.
  - Registry doc `reports/exam_phase2_20261026/gemma4_31b.json`, SHA-256
    `a04a0346ca887c27998b5f46f4e3d67fa05126ff3af9e0c20fe78d030c1fdc61`.
  - The job checks the GGUF SHA-256 after fetching it.
- **Server: the selection exam's arguments** (R1-SWEEP2-SETTINGS (1)).
  - **The exam's argv.** From `r1/scripts/llama_server_instance.py` `argv` and `thinking_args`, and from
    `r1/exam/runtime.py` `EXAM_SERVER_ARGS` and its 32,768 / 999 check:
    `-m <model> --host 127.0.0.1 --port <p> -ngl 999 -c 32768 --alias <id> -np 1 --jinja --cache-type-k q8_0
    --cache-type-v q8_0 -lv 4 --chat-template-kwargs {"enable_thinking":false}`.
  - **Numeric values for sweep 2:** context 32,768, `-ngl 999`, `-np 1` (one slot), q8_0 K and V cache, `--jinja`,
    thinking off, and `cache_prompt: false` on every call (`LLAMACPP_CACHE_PROMPT` and `LLAMACACHE_PROMPT` unset).
    The smoke ran these values (job records `manager_settings`; 61/61 layers offloaded).
  - **Thinking switch: byte-identical to the exam** (R1-SWEEP2-LAYOUT-AMEND). The argument is exactly
    `{"enable_thinking":false}`, as the exam writes it (`llama_server_instance.py`, `json.dumps` with compact
    separators). At `cbb40d28` the wrapper checks the bytes, but against a constant with a space, and the spec example
    still carries the space; both must change, and a disclosure does not replace the fix (precondition 2a′).
  - One owned `llama-server` per job, bound to `127.0.0.1`, with log level `-lv 4` and alias `gemma4_31b`.
  - Temperature 0.2 with the D26 seed (`manager_seed(campaign_id, budget_index, repetition, revision_attempt)`).
  - **Disclosed non-numeric differences from the exam** (R1-SWEEP2-SETTINGS (1)): the port and the model path; the
    order of the arguments; `--no-webui`. The round-5 job records list `--no-webui` and `-lv 4` under
    `non_numeric_differences`.
- **Design: the same as sweep 1** (R1-MAIN-PROPOSER (b); config `r1/scripts/configs/c3_sweep_deepthought.json` as on
  `main` / `ccb4712`, SHA-256 `2fa891f43bf26e6ed2ac6c794696428a43568a69a850d6029e3bc8233616974b`, for the design
  values only).
  - The eight nodes: `digits_mlp`, `tabular_mlp`, `openml_breast_w`, `openml_ionosphere`, `openml_wdbc`,
    `openml_credit_approval`, `openml_sonar`, `openml_climate`.
  - Per node: 18 instances × memory modes `{append_only_summary, none}` × W = 20; `vary` split; structure-only
    `manager_proposal/v1`; transport attempts 3. No node changes after launch.
  - Instance seeds are the sweep-1 seeds: `100 + 10k + (Σ ord(node) mod 7)` for k = 0…17
    (`r1.headroom.e1b_collect._instance_seed`). They are also the in-campaign `train_seed` / `split_seed`.
- **Noise source.** `results/r1/noise/D28_REPAIR_20261027/summary.json`, SHA-256
  `3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310`, as in sweep 1. The round-5 wrapper checks the
  file's SHA-256 before the collector starts (a mismatch is a STOP), passes it as `--e1-summary`, and records it as
  `noise_source` in the job record and in the `c3_label_sweep` block of the collector's run manifest
  (`out/manifest.json`, one per chunk job).
- **Gates, restored from sweep 1** (R1-SWEEP2-SETTINGS (4)). Liveness before collection, with `min_live_nodes` 8;
  after collection, `max_parse_failure_rate` 0.2 and `collection_gates`. Not waived. The round-5 wrapper implements
  both: liveness as its own job kind, and the collection gates in each chunk job.
  - **Pre-launch liveness** (R1-S2C3B-LAUNCH). The S2-C3b liveness is rerun once at the launch commit (the paper
    commit = `main` HEAD at launch), with the launch's image digest, harness pin and server settings. No earlier S2-C3b
    pass replaces it.
- **Worker gates** (R1-SWEEP2-LAYOUT-AMEND). Both are STOPs:
  - **(w1)** any campaign with no successful in-campaign worker run;
  - **(w2)** an overall worker failure rate above sweep 1's failure rate + 5 percentage points. Sweep 1's rate is
    computed from its ledger first and recorded: `<sweep-1 worker failure rate, its definition, ledger source and
    the record that holds it>`. How the overall rate is accumulated across chunk jobs: `<fix unit 2f>`.
  - The cluster's implemented gate differs from (w2) as written; see item 2f.
- **Liveness seeds: `liveness_seed_policy = "sweep1_d28_reuse"`** (R1-S2C3B-SEEDS).
  - The pick's D28 liveness on the eight nodes follows sweep 1: per node, the first two sweep instance seeds
    (k = 0, 1 of the formula above). `r1.liveness` has no seed parameter, and the wrapper runs it with 2 instances and
    10 runs in `append_only_summary`, as sweep 1 did.
  - Liveness output never enters a label table, training or selection. It touches no seed in 7001–7010, 8001–8010 or
    9001+.
  - **Disclosure.** The liveness instances share their seeds with the first two sweep-2 instances of each node. The
    sweep-2 report states this overlap. R1-S2C3B-SEEDS records this as amending the requirement, which it attributes to
    R1-SWEEP2-SETTINGS (4), that the seeds be disjoint from the sweep-2 instance seeds. The (4) text on `main` does not
    itself contain that wording.
- **Job layout: from the re-measurement** (R1-SWEEP2-LAYOUT-AMEND). The R1-SWEEP2-LAYOUT numbers are void, because
  the measured runs contained no training time.
  - One job is one (node, memory mode) chunk of root campaigns. By the design that is **16 jobs** (8 nodes × 2 modes),
    unless the re-measurement requires a chunk split: `<chunk split: none | layout>`.
  - `request_gpus 1`, `request_cpus 16`, workers 16.
  - **Re-measurement.** A 2-instance 32k smoke, after the worker-run fix (2f), in which training actually succeeds:
    `<report, review>`. It gives the chunk time `<re-measured chunk time, s, and how it is derived from the 2-instance
    run>`. How "training actually succeeds" is checked on the smoke is not fixed by the row. Proposed by the agent:
    (w1) passes, and the smoke's worker failure rate is within sweep 1's rate + 5 percentage points, which needs
    precondition 10 first.
  - `+RequestWalltime` = **1.5 × the re-measured chunk time** = `<s>`. The cluster's `sweep2/s2_c4_pilot.py`
    (`layout`) still proposes 1.3 ×, with a 3,600 s floor; its factor must become 1.5 before it proposes the spec
    value (item 2h).
  - **Chunk split.** In `s2_c4_pilot.py` a split is flagged when the proposed walltime (factor × chunk time) exceeds
    86,400 s, and the proposed walltime is capped at 86,400 s; the wrapper's validator also requires a walltime of at
    most 86,400 s. With the factor 1.5, a split is needed once the chunk time exceeds 57,600 s.
  - `request_disk` = the re-measured smoke's disk peak × 1.4, rounded up = `<kB>`; `request_memory` = its memory peak
    × 1.4, rounded up = `<MB>` (R1-SWEEP2-RESOURCES). The round-5 `s2_c4_pilot.py` (`layout`) instead takes the
    larger of `round(1.4 × peak)` and a floor (40,000,000 kB for disk, 32,000 MB for memory). The row names no floor
    and rounds up, so the proposal must change (fix item 2j).
  - These values go into the job spec, and `render_jdl.py` writes them from it. The cluster's `sweep2/spec.example.json`
    at `f172d299` still carries the void values (walltime 12,203 s, disk 42,460,977 kB, memory 32,000 MB); they are
    replaced from the re-measurement (item 2h).
  - GPU memory at 32,768 with `-np 1` (32k smoke job records, `server.cuda_lines`; server facts, not affected by the
    worker failure): model buffer 18,675.55 MiB, KV buffers 1,360.00 and 637.50 MiB, compute buffer 396.80 MiB;
    21,069.85 MiB in all.
  - The GGUF is fetched once per chunk: 16 × 19.6 GB ≈ 314 GB of HF egress (disclosed; an image-side model cache is a
    later author decision).
  - **No resume path; STOP before rerun** (R1-SWEEP2-LAYOUT-AMEND, R1-SWEEP2-STOP-PRECEDENCE).
    - A chunk that ends for a reason on the STOP list (for example an OOM kill, a failed gate, a SHA mismatch or a
      settings mismatch) is a STOP: its state is preserved, and the author decides.
    - Only an eviction or an infrastructure interruption with no STOP cause (`NumJobStarts` > 1 and the like) leads to
      a whole-chunk rerun:
      - as a fresh submission, not an HTCondor restart of the same job (item 2h);
      - in a new directory: `<directory naming for a rerun>`;
      - with the old directory moved aside, not deleted: `<where it is moved>`;
      - disclosed in the sweep-2 report, with the reason and both directories.
    - There is no resume. The round-5 wrapper's in-job resume branch was replaced on `sweep2-main-20261116` @
      `61282190` by a STOP when a prior chunk exists in the sandbox (item 2h).
  - **Walltime STOP.** A chunk that exceeds its walltime is a STOP, not a rerun.
  - **What a killed attempt leaves.** The job transfers its outputs only on exit (`when_to_transfer_output = ON_EXIT`
    in `render_jdl.py`), so an evicted or over-walltime attempt returns no outputs. Certain to be kept are the HTCondor
    user log and the job ad (`condor_history`); `out` and `err` only if they are streamed: `<item 2h>`.
- **Estimate.**
  - GPU-h = the number of chunks × the re-measured chunk time: `<GPU-h>`.
  - Wall: with s matching L40S slots free to this user, about ⌈chunks / s⌉ × the chunk time, plus queue waits:
    `<h; s and the ad snapshot it comes from>`.
  - **STOP for the author** if the projection exceeds **60 GPU-h** or **48 h wall** (R1-SWEEP2-SETTINGS (5); unchanged
    by R1-SWEEP2-LAYOUT-AMEND).
  - The collector's `--deadline` is the walltime minus 600 s, counted from the collector's start. It only stops new
    root campaigns being submitted (`e1b_collect.py`); it never stops roots already running. With 18 instances on 16
    workers, 16 roots start at once, so the deadline can hold back at most the last 2. It gives no protection against
    the walltime: the HTCondor walltime is the only real limit.

## Preconditions before launch

1. **S2-M2 integration on `main`.** Done: `9ae6d877`, an ancestor of `025bfc16`.
2. **S2-C2 wrapper on `main`**, accepted by independent review, with S2-C5. None of the cluster's fix commits below
   is on `main` yet: `<integration commit>`.
   - Round 5 (`sweep2-main-20261116` @ `8a8ea832`, minors at `d9a17b86`) covers redraft items 2b–2d and most of 2a
     and 2e: the 32,768 exam arguments, the noise-source binding, the restored gates and requests written from the
     spec.
   - **a′. Thinking-switch bytes.** The spec and the server argv carry exactly `{"enable_thinking":false}`, and the
     validator checks the bytes (R1-SWEEP2-LAYOUT-AMEND). **Open:** `61282190` on `sweep2-main-20261116` adds a byte
     check, but against `EXAM_THINKING_KWARGS = '{"enable_thinking": false}'`, with a space. The exam's launcher
     writes it without a space (`r1/scripts/llama_server_instance.py`, `json.dumps(..., separators=(',', ':'))`), so
     the constant is not the exam's bytes. No review record for `61282190` was found on the branch.
   - **f. Worker runs and worker gates.** Implemented on `sweep2-main-20261116`: the PATH fix (`77c6394a`) and a
     worker-success gate (`77c6394a`, recalibrated in `e17b0437`, nested-skip fix `ce9210d3`). Independent review
     `reviews/WORKER_FIX_REVIEW_20261116.md` ACCEPTED in round 3, for the tips it names. **Open for the author:** the
     implemented gate is not (w2) as the row writes it.
     - The row: an overall worker failure rate above sweep 1's rate + 5 percentage points is a STOP.
     - The cluster gate: a failure rate above sweep 1's rate **per (node, memory mode)** + 5 pp, and only if it also
       exceeds a 1 % exact-binomial small-n bound; plus a zero-tolerance STOP on any `runtime_error`; skipped worker runs
       (`worker_skipped`) excluded (`S2_C2_UNIT.md`, worker-success section).
     - Whether the per-(node, mode) form with the binomial condition satisfies (w2), or (w2) is added as written:
       `<author>`. (w1) matches the row.
   - **g. Record text.** The chunk record still hard-codes `output_use: "ENGINEERING: … disclose in the sweep-2 report
     as an engineering run"` whatever the label (`s2_c2_lib.py` at `cbb40d28`). An EVIDENCE chunk record must not
     carry it. `<fix>`.
   - **h. Whole-chunk rerun and walltime.**
     - Implemented on `sweep2-main-20261116` @ `61282190`: a prior chunk in the sandbox is a STOP (no resume), a chunk
       walltime check, and walltime = 1.5 × `layout_measured_chunk_s` when the spec carries that field (the check is
       skipped if it is absent). No review record found. Open: the field becomes mandatory for EVIDENCE.
     - How "no STOP cause" is established for an evicted or killed attempt, which returns no outputs:
       `<evidence, e.g. HTCondor hold and eviction reason codes in the user log and job ad; if undecidable, treat as
       STOP>`.
     - The walltime floor of 3,600 s (in `s2_c4_pilot.py` and in `validate_spec`, which requires 3,600–86,400 s) is not
       part of "1.5 × the chunk time"; it binds only if the chunk time is below 2,400 s: `<fix or author>`.
     - Still open: HTCondor must not restart a chunk on its own. `render_jdl.py` at `cbb40d28` still sets no hold
       policy; a job with `NumJobStarts` > 1 is held or removed (for example `periodic_hold = NumJobStarts > 1`) and,
       if it has no STOP cause, rerun as a fresh submission into a new directory, with the old one moved aside and
       disclosed (R1-SWEEP2-STOP-PRECEDENCE).
     - What is preserved from a killed or over-walltime attempt (at least the user log and the job ad; `out` / `err`
       only if streamed), given ON_EXIT transfer.
     - The walltime factor in `s2_c4_pilot.py` (still 1.3 at `cbb40d28`) changes to 1.5, and the spec's layout values
       are replaced from the re-measurement.
   - **i. Host pins and records** (R1-SWEEP-HOST-L40S-SITES).
     - `render_jdl.py` drops the `CloudSite` and CPU-class requirements and keeps the GPU model.
     - `validate_spec` stops requiring `cloud_site == BwForCluster-Nemo2`, `cpu_family` 6, `cpu_model_number` 207 and
       `cpu_model_contains` in the spec, and `spec.example.json` drops them.
     - `cpu_identity()` records instead of STOPping on a CPU mismatch.
     - Each campaign records site, node, GPU name and UUID, driver and CPU model.
   - **j. Requests** (R1-SWEEP2-RESOURCES). `s2_c4_pilot.py` proposes disk and memory as the peak × 1.4 rounded up,
     without its floors (40,000,000 kB, 32,000 MB). `validate_spec` also refuses disk below 30,314,084 kB and memory
     below 10,853 MB, floors taken from the void S2-C4 peaks; they are removed or replaced by the re-measured rule.
3. **S2-C3b liveness at the launch commit** (R1-SWEEP2-SETTINGS (4), R1-S2C3B-SEEDS, R1-S2C3B-LAUNCH). D28 liveness of
   the pick on all eight nodes on L40S, seeds per `sweep1_d28_reuse`, with prompt lengths re-measured with the pick's
   tokenizer, run once at the launch commit with the launch's image digest, harness pin and server settings, after
   this note is committed (see "Order of commit and launch"). No earlier S2-C3b pass replaces it. Its result is
   recorded in `<launch record>`, not in this note. D28's criterion "keep after trial 1 ≥ 1" cannot pass if every
   worker run fails, so it also tests item 2f.
4. **S2-C3 L40S deployment check** (R1-S2C3-DRIVER). Run with the declared-input, TASL-independent ENGINEERING replay
   driver, under the pre-declared criteria (`reports/sweep2_20261116/S2_C3_CRITERIA.md`), on the L40S actually used
   (R1-SWEEP-HOST-L40S-SITES). The criteria include criterion 2, parse-failure rate ≤ 0.02 against B2's 0/240, and the
   corrected criterion 3: invalid 20 / duplicates 33 / no-ops 20 of 240, ± 10 %. Passed: `<report, review>`.
5. **Re-measurement** (R1-SWEEP2-LAYOUT-AMEND). The 2-instance 32k smoke with training succeeding, after item 2f (and,
   for the proposed failure-rate check, after precondition 10). It fixes the layout fields above:
   `<report, review>`.
6. **S2-C5 real-submission switch** accepted: `<review>`. At `s2c5-switch-20261116` @ `84a0dc30` it is check and
   submit only. Open:
   - it hard-codes the void R1-SWEEP2-LAYOUT values (`ACCEPTED_LAYOUT` and `REQUIRED_SPEC_LAYOUT`: 12,203 s,
     42,460,977 kB, 32,000 MB, 41.72 GPU-h) and v1 as `FROZEN_IMAGE`; it must take the re-measured layout and the
     authorized digest before it can accept this note;
   - its P1–P7 fields follow the cluster template, whose P5 still names the void R1-SWEEP2-LAYOUT; the key block above
     redefines them for this note, and the switch's wording may need to follow;
   - a seal step comparing the image digest and the GPU model (L40S) with this note, and recording site and CPU, does
     not exist yet: `<fix>`.
7. **R1-MAIN-PROPOSER (g)2** (R1-SWEEP2-SETTINGS (3), R1-E1-OPENML). No exception for now.
   - The order is e1 environment replay, then the author's e2, then sweep-1 B.2 on one pinned HTCondor CPU class. It
     runs in parallel with the sweep-2 preparation.
   - The e1 offline mechanism establishes the identity of the six OpenML datasets with sweep 1's by the evidence of
     R1-E1-OPENML-AMEND, all four together: (i) the OpenML data ids match sweep 1's record; (ii) sweep 1's recorded
     loaded-data fingerprints equal, value by value, the fingerprints recomputed now from the same cache; (iii) each
     cached ARFF's md5 equals OpenML's `md5_checksum` in the cache metadata; (iv) the cache's per-file SHA-256 values
     are unchanged before and after use and equal those in `OFFLINE_MECHANISM_AUDIT.json`. Worker subprocesses run
     without network (unchanged). An independently reviewed offline mechanism on this basis is wired into
     `c3_env_replay.py`, and all 16 e1 cases run under the e1 authorization with the zero-tolerance pass rule. The
     report and the paper disclose that identity rests on this evidence, not on sweep-1 file hashes.
   - An exception is discussed only if (g)2 becomes sweep 2's only blocker. Status at launch:
     `<sweep-1 B.2 complete | exception row>`.
8. **Projection** within 60 GPU-h and 48 h wall, from item 5.
9. **Harness-defaults check** (R1-MAIN-PROPOSER (c)): `<report>`.
10. **Sweep-1 worker failure rate** computed from its ledger and recorded, for worker gate (w2): `<report>`. The
    cluster's commit `77c6394a` states an overall sweep-1 rate of 9.05 %, and its later gate uses per-(node, mode)
    rates from the frozen sweep-1 corpus (item 2f). Not verified here.

## Sealing and the analysis lock (R1-BX-D8)

- Job outputs come back to the submit host by HTCondor transfer (`out.tar`, `work.tar`, `job_record.json`,
  `SHA256SUMS`, `llama-server.log`). The seal step (`sweep2/s2_c2_lib.py seal`) copies them into
  `/ceph/srv/dwong/paperb/sweep2/<run_id>/<chunk_id>/`.
  - It refuses `..`, symlinks and overwrites, and writes `SHA256SUMS` and `SEAL_RECEIPT.json`.
  - With the seal fix of precondition 6 it will also compare the image digest and the GPU model with this note, and
    record site and CPU. The accepted S2-C2 seal checks only that they are recorded.
  - A rerun chunk (above) is sealed into its new directory. The moved-aside directory is kept.
- No sweep-2 label table is copied back for analysis, or read by any analysis code, before the author row
  **R1-BX-D8-CONFIRM** exists. R1-BX-D8-V3-A and R1-BX-D8-V3-B keep this lock.
  - The lock is the PLAN-line guard of the analysis readers (`analysis_guard.guard_table` /
    `require_d8_confirmation`). `refuse_sealed` does not apply to this path layout.
  - Until the row exists, run reports give counts only.

## Disclosed differences

**From sweep 1** (cross-proposer tables, R1-MAIN-PROPOSER (c) as amended by R1-SWEEP-HOST-HTC and
R1-SWEEP2-SETTINGS (1)):
- the manager;
- the host: deepthought TITAN X (sm_52) against L40S (sm_89) at deepthought2 and/or NEMO2, HTCondor container jobs;
- the CPU host of the in-campaign worker runs (sweep 2: the CPU model recorded per campaign; NEMO2 L40S hosts
  Xeon Platinum 8562Y+, family 6 / model 207; deepthought2 L40S `<CPU model>`);
- context 8,192 against 32,768;
- default KV cache against q8_0;
- `--jinja` and the thinking flag;
- `cache_prompt` at the default against an explicit false;
- the harness pin `6adf385` against `a3fedbb`;
- the paper commit;
- the image;
- the C3 premises that differ by proposer, Q1 (duplicate / no-op skip bound) and Q2 (increment dispersion), from the
  X.7(c) appendix (`mac-s2-m5-x7c-20261116`).

The liveness seeds (`sweep1_d28_reuse`) are the same as sweep 1's and do not differ.

**From the selection exam** (B1/B2 on TASL-7):
- GPU 4090 against L40S;
- a direct server against an HTCondor container with the frozen image;
- the llama-server binary: the same llama.cpp commit `620d222`, but the exam binary `b70f4882…` ("build 1") against
  the image's `f8d35fd3…` ("build 11669");
- the non-numeric server arguments listed above (the thinking switch is byte-identical, so it is not among them);
- instance seeds: exam 9001+ (B1) and 9011+ (B2) against the sweep-1 instance seeds; exam audit seeds 9101+ (B1)
  and 9201+ (B2), whereas this note runs no audits;
- paper commit `37282ec3…` against the launch commit;
- harness: identical (`a3fedbb`).

**Within sweep 2:**
- the site and CPU model of each campaign, if both sites are used and their CPU models differ
  (R1-SWEEP-HOST-L40S-SITES);
- the liveness instances reuse the first two instance seeds of each node (R1-S2C3B-SEEDS, above);
- any whole-chunk rerun, with its reason and both directories.

## Boundaries and STOPs

**Scope.** This authorization covers the sweep-2 label collection (B.1b) only. The collector runs with
`--audit-seeds 0`, and seeds 7001–7010 stay reserved for the B.2 addendum. It does not cover:
- B.2 audits: sweep-2 B.2 is authorized later by an addendum (R1-SWEEP2-SETTINGS (2)), and R1-B2-DECOUPLE and
  R1-B2-REPLAY-GO stand;
- sweep-1 B.2;
- T1 sweeps;
- other GPU models;
- a second image digest;
- changing nodes, instances, settings or the layout after launch (a whole-chunk rerun under the rule above is not a
  change).

**Checks before launch.** Check all pins, the layout values and this note's sha256 against the job specs.

**STOP conditions.** These are runbook §4, the S2-C2 STOPs and R1-MAIN-PROPOSER's STOPs:
- a required PLAN row, precondition or authorization missing or different;
- a job on a GPU other than the L40S;
- a GGUF SHA-256 mismatch;
- a noise-source SHA-256 mismatch;
- server arguments or `cache_prompt` differing from the values above, other than the disclosed non-numeric
  differences, including a thinking switch that is not byte-identical to `{"enable_thinking":false}`;
- an image identity mismatch;
- incomplete offload or OOM;
- a liveness or collection gate failing;
- worker gate (w1): a campaign with no successful worker run;
- worker gate (w2): an overall worker failure rate above sweep 1's rate + 5 percentage points;
- a chunk exceeding its walltime;
- a label string not matching this note;
- a projection above 60 GPU-h or 48 h wall;
- any code path reading sweep-2 labels before R1-BX-D8-CONFIRM;
- pushing `main` without the author's explicit instruction.

A chunk that ends for a reason on this list is a STOP, with its state preserved, even if the job was also evicted or
restarted (R1-SWEEP2-STOP-PRECEDENCE). Only an eviction or infrastructure interruption with no STOP cause
(`NumJobStarts` > 1 and the like) leads to a whole-chunk rerun under the rule above.
Preserve completed outputs and every attempt (never delete, never overwrite), and report any
STOP.

---

## Notes for the author (not part of the note)

1. **The thinking-switch constant on the cluster branch is not the exam's bytes** (item 2a′). `61282190` checks the
   argument against `{"enable_thinking": false}` (with a space) and calls it byte-identical to the exam. The exam's
   launcher writes `{"enable_thinking":false}`. As implemented, the check would enforce the space that
   R1-SWEEP2-LAYOUT-AMEND asked to remove.
2. **The implemented worker gate differs from (w2)** (item 2f): per (node, memory mode) rather than overall, and a STOP
   only when the rate also exceeds a 1 % exact-binomial bound. It is reviewed, but the row writes an overall rate
   against sweep 1's rate + 5 pp. Your choice is a placeholder in 2f.
3. **Site no longer pinned.** With `CloudSite` dropped, the requirement admits an L40S at any site in the HTCondor pool,
   not only deepthought2 and NEMO2. R1-SWEEP-HOST-L40S-SITES names those two. If the pool has (or gains) other L40S
   sites, they would be accepted and recorded. Whether to restrict to the two sites: `<author>`.
4. **The S2-C5 switch and this note.** The switch's `parse_note` reads every `key: value` line of the note and requires
   the key block's fields, including `P1:`–`P7:` each starting with `PASS`; its accepted layout and frozen image are
   the void values (precondition 6). The key block's P lines are redefined for this note; S2-C3b is not among them,
   because it runs after the note is committed.
5. **Commit order** (R1-S2C3B-LAUNCH). Committing the note on an `author-*` branch keeps `main` HEAD, and so the launch
   commit, unchanged after S2-C3b. Whether the S2-C2 wrapper's `resolve_label` accepts a note there was not checked:
   `<fix unit>`.
6. **Placeholders and the unit that fills each one.**
   - The author: the opening paragraph; `run_id`; image digest (proposed v1 `69b06b35…`); launch commit; the P1–P7
     evidence; the (w2) form (2f); the site restriction (note 3); (g)2 status.
   - Cluster fix units 2a′, 2f–2j and the S2-C5 layout fix, and their integration into `main`
     (`<integration commit>`).
   - Re-measurement (precondition 5): chunk split, chunk time, walltime, disk, memory, GPU-h, wall.
   - The deepthought2 L40S CPU model.
   - Sweep-1 failure rate (precondition 10).
   - S2-C3b at the launch commit, S2-C3, S2-C5, harness-defaults check: their reports.
7. **What changed from version 4** (`6eee770c`, on `main`).
   - Authority: `main` @ `16185b0b`; the five 17 Nov rows added.
   - Host: the GPU model pinned instead of the site; the CPU class no longer pinned or checked as a STOP, but recorded
     per campaign and disclosed; the deepthought2 L40S allowed; S2-C3 on the L40S actually used.
   - Liveness: the S2-C3b rerun at the launch commit replaces the "S2-C3b counts if …" condition and its `<author>`
     choice.
   - Resources: disk and memory = peak × 1.4, rounded up, replacing the `<author: confirm>` on the pilot's rule with
     floors.
   - STOP precedence: the agent's reading is replaced by the row.
   - Precondition 7: the R1-E1-OPENML-AMEND identity evidence.
   - Preconditions 2 and 6: the cluster's progress on `sweep2-main-20261116` @ `cbb40d28` and the open points it
     leaves (2a′ constant, 2f gate form, 2g, 2h hold policy, new 2i and 2j, S2-C5's hard-coded layout).
   - Key block: the S2-C5 switch's required fields added, with placeholders, including P1–P7.
   - The order of commit and launch, so that S2-C3b runs at the launch commit and its result goes into the launch
     record.
   - Removed with version 4's notes: the worker-failure narrative (now fixed on the cluster branch, item 2f) and the
     list of earlier removals.
