# Draft authorization note: C3 sweep 2 (HTCondor, any GPU ≥ 24 GB, CC ≥ 7.0). Version 6, per R1-SWEEP2-ANY-GPU

**This is a draft, not an authorization.** The Mac agent (Claude, AI-assisted) prepared it as unit S2-M1 of the
sweep-2 work plan (`prompts/SWEEP2_HTCONDOR_RUNBOOK_20261116.md`).
- It updates version 5 (`mac-s2-m1-v5-20261117`, accepted at `edec3f6d`, final text `3c0c5f75`; not on `main`).
- It applies the author row **R1-SWEEP2-ANY-GPU** (17 Nov (3)): the LLM-backed label runs of sweep 2 (T0) may run
  on **any HTCondor GPU that can run them** — VRAM ≥ 24 GB, compute capability ≥ 7.0, a universe the wrapper
  supports — with no GPU-model or site pin; every campaign records site, node, GPU model and UUID, driver and CPU
  model; the report discloses them and may stratify descriptively by GPU model; the S2-C3 deployment check is one B2
  replay on the **first GPU model actually used**, and the other GPU models are only recorded and disclosed. It
  supersedes R1-SWEEP-HOST-L40S-SITES's GPU-model restriction for sweep 2. T0 worker training runs on CPU; the GPU
  affects proposal generation only. T1 is unaffected.
- It records the cluster's progress since version 5 (`sweep2-main-20261116` @ `d9b31a30`): the any-GPU requirements
  and run-time floor check, the exact thinking bytes, the hold policy, the label-conditional record text, and a
  2-instance 32k re-measurement on an H200 in which, per the recording commit's message, training succeeded (pending
  its report and review). None of these commits has an independent review record yet.
- Kept from version 5: the R1-SWEEP2-LAYOUT-AMEND rules, R1-S2C3B-LAUNCH (S2-C3b rerun at the launch commit),
  R1-SWEEP2-RESOURCES, R1-SWEEP2-STOP-PRECEDENCE, the liveness seed policy `sweep1_d28_reuse` with its disclosure, the
  order of commit and launch, and no B.2 audits (sweep-2 B.2 has its own draft addendum, R1-SWEEP2-B2-DRAFT).
- Placeholders kept: the layout values (proposed from the H200 re-measurement, pending its review), the image digest
  (v1 `69b06b35…` proposed), the `run_id` and the launch commit.

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

The note therefore cannot record S2-C3b's result. That result goes into the launch record (precondition 3). With
the note on `main`, the launch commit is the note's own commit, so the note can cite only its parent, the integration
commit; with the `author-*` option, the note can cite `main` HEAD as the launch commit.

**Authority.**
- Read from `author-decisions-20261117b` @ `45fb94cc`, which descends from `main` @ `26177d82` and adds the 17 Nov
  (3) and (4) rows. PLAN §10 rows take precedence over this note wherever they differ.
- The rows used are:
  - **R1-SWEEP2-ANY-GPU** (17 Nov (3)), which supersedes R1-SWEEP-HOST-L40S-SITES's GPU-model restriction for sweep 2;
    R1-QTORCH-AMEND (17 Nov (4)) where it says sweep 2's image is still decided under S2-C1 / P7; R1-B2-GO and
    R1-SWEEP2-B2-DRAFT (17 Nov (3), (4)) for the status of B.2;
  - R1-SWEEP-HOST-L40S-SITES (site not pinned; per-campaign records), R1-S2C3B-LAUNCH, R1-SWEEP2-RESOURCES,
    R1-SWEEP2-STOP-PRECEDENCE and R1-E1-OPENML-AMEND (17 Nov);
  - R1-SWEEP2-LAYOUT-AMEND (16 Nov (3)), which voids the numbers of R1-SWEEP2-LAYOUT;
  - R1-S2C3B-SEEDS, R1-S2C3-DRIVER and R1-E1-OPENML (16 Nov (2));
  - R1-SWEEP2-SETTINGS (1)–(5), as amended by R1-S2C3B-SEEDS and R1-SWEEP2-LAYOUT-AMEND, and R1-SWEEP-HOST-HTC as
    amended by R1-SWEEP-HOST-L40S-SITES and R1-SWEEP2-ANY-GPU;
  - R1-SWEEP1-CLASSIFY (label from the authorization only);
  - R1-EXAM-X7;
  - R1-MAIN-PROPOSER (b), (c), (e), (g), as amended by R1-SWEEP2-SETTINGS;
  - R1-BX-D8, R1-BX-PROPOSED-CONFIRM, R1-BX-D8-V3-A and R1-BX-D8-V3-B, and **R1-BX-D8-CONFIRM** (signed in
    `14c47777`, on `main` `26177d82`): the gate code `r1/c3/gate.py` @ `6aa9985c`, sha256 `ffb70d7a…`; "sweep-2 label
    tables may be analysed from this row on";
  - R1-CACHEPROMPT-FALSE, R1-EXAM-CACHE-REV and R1-EXAM-B1-HARNESS-PIN;
  - R1-B1-CORPUS-FREEZE;
  - R1-HARNESS-NEXT-PIN, R1-B2-DECOUPLE, R1-B2-REPLAY-GO and R1-E1-AUTH.
- Measured server facts (CPU identity, build line, GPU buffers) come from the cluster's S2-C2 32k smoke (clusters
  759728/759729): `sweep2-main-20261116` @ `f172d299`, `reports/sweep2_20261116/SMOKE_RESULTS_20261116.md` and
  `smoke_20261116/` (both job records). The wrapper that ran it is the cluster's S2-C2 round 5, accepted by independent
  review (`reviews/S2_C2_REVIEW_20261116.md`, round 5 at `8a8ea832`, minors at `d9a17b86`). That smoke's timing is void
  (R1-SWEEP2-LAYOUT-AMEND): every visible in-campaign worker run ended in ≤ 0.1 s with `success=False`.
- The state of the cluster fix units is read from `sweep2-main-20261116` @ `d9b31a30` (not on `main`). The H200
  re-measurement is described by that commit's message and its `sweep2/spec.example.json`; its sealed job records
  are on `/ceph` and are not in the repository.

Each value below cites its source.

---

# Authorization: C3 sweep 2 (HTCondor, any GPU ≥ 24 GB, CC ≥ 7.0)

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
layout_request_walltime_s: <1.5 × the re-measured chunk time, s; proposed 8735 (H200), precondition 5>
layout_request_disk_kb: <the re-measured disk peak × 1.4, rounded up, kB; proposed 42460970, precondition 5>
layout_request_memory_mb: <⌈1.4 × the H200 memory peak⌉ MB, from the job records; 32000 is the pilot floor, note 3>
layout_chunks: <16, unless the re-measurement requires a chunk split>
layout_gpu_hours: <chunks × the re-measured chunk time / 3600; proposed 25.88 (16 × 5823 s, H200)>
b2_audits: none (this authorization carries no B.2 audits)
d8_lock: true
P1: <PASS — R1-SWEEP-HOST-HTC as amended by R1-SWEEP-HOST-L40S-SITES and R1-SWEEP2-ANY-GPU>
P2: <PASS — main at the launch commit contains the S2-M2 integration and the accepted fix units>
P3: <PASS — this note>
P4: <PASS — S2-C3 deployment check (one B2 replay) on the first GPU model used: report, review>
P5: <PASS — re-measurement and layout per R1-SWEEP2-LAYOUT-AMEND and R1-SWEEP2-RESOURCES: report, review>
P6: <PASS — S2-C5 switch enabled for this run id only>
P7: <PASS — image digest frozen above>
```

## Proposed scope and pins

- **Host.** HTCondor job submission (R1-SWEEP-HOST-HTC, as amended by R1-SWEEP-HOST-L40S-SITES and
  R1-SWEEP2-ANY-GPU).
  - **Any GPU at or above the floor; no GPU model or site pinned.** The job requirements are `GPUs >= 1`,
    `GPUs_GlobalMemoryMb >= 24576`, `GPUs_Capability >= 7.0`, `Arch == "X86_64"`, `OpSys == "LINUX"` and
    `Cpus >= 16`, in `universe = container` (`sweep2/render_jdl.py` @ `d9b31a30`, from `82c04862`; slots without
    container-universe support are not matched). At run time the wrapper checks the same floor from the device it got
    (VRAM ≥ 24,576 MiB, compute capability ≥ 7.0; `gpu_identity`) and STOPs below it.
  - **"≥ 24 GB" is implemented as 24,576 MiB (24 GiB)**, the cluster's reading of the row. Cards sold as 24 GB report a
    little less (an RTX 4090 about 24,564 MiB; not verified on this pool) and are then excluded by both the requirement
    and the run-time check. Keep 24 GiB, or use a nominal 24 × 10⁹ B (22,888 MiB): `<author>` (note 6).
  - **Recorded for every campaign** (R1-SWEEP2-ANY-GPU): site, node, GPU model and UUID, driver and CPU model. The job
    record holds `host` (host name, FQDN), `site`, `gpu` (name, UUID, driver, VRAM, compute capability, device
    count) and `cpu` (model, family, model number), per chunk job; a chunk job runs all 18 campaigns of its
    (node, memory mode) on one GPU and one CPU, so the job record covers each of its campaigns. Whether each
    campaign's own record must carry a copy: `<fix item 2i>`.
  - **One table, several GPU models.** The sweep-2 table may mix GPU models. The report discloses which campaigns ran
    on which GPU model, site and CPU model, and may stratify descriptively by GPU model (R1-SWEEP2-ANY-GPU). T0 worker
    training runs on CPU, so the GPU affects proposal generation only.
  - **CPU model: recorded and disclosed, not pinned** (R1-SWEEP-HOST-L40S-SITES; unchanged by R1-SWEEP2-ANY-GPU).
    The worker runs of a campaign use the CPU of its GPU node. Known so far: NEMO2 L40S hosts `g3608`, `g3610`,
    `INTEL(R) XEON(R) PLATINUM 8562Y+` (family 6 / model 207, 32k smoke); the H200 re-measurement host:
    `<CPU model from its job record>`.
  - A job on a GPU below the floor (VRAM < 24 GB or compute capability < 7.0) is a STOP.
  - Selection ran on a 4090 (B1/B2 on TASL-7); deployment runs on whatever qualifying GPUs HTCondor assigns. This is
    disclosed. The S2-C3 deployment check is one B2 replay on the first GPU model actually used; other GPU models are
    recorded and disclosed only (R1-SWEEP2-ANY-GPU).
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
  - R1-QTORCH-AMEND approves image v2 (`b1144ece…` gpu) for Track P only; it leaves sweep 2's image to S2-C1 / P7.
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
  - **Re-measurement.** A 2-instance 32k smoke, after the worker-run fix (2f), in which training actually succeeds.
    Run on an **H200** and recorded in `sweep2-main-20261116` @ `d9b31a30` (a data commit: it changes the spec, a test
    and docstrings, not the code the jobs ran; sealed on `/ceph`). The message of `83799722` says the `none` job had
    already shown real training before that port fix, so the two jobs probably ran different wrapper states: `<the
    wrapper commit and spec each job ran, from the job records>`. Per the recording commit's message, 40/40 worker successes with metrics in both memory modes, `runtime_error` 0, gates PASS, and
    a full-chunk time of **5,823 s** (`layout_measured_chunk_s`; `s2_c4_pilot.layout` scales the 2-instance wall time
    to 18 instances linearly). Report and independent review: `<report, review>`. How "training actually succeeds"
    is checked on the smoke is not fixed by the row. Proposed by the agent: (w1) passes, and the smoke's worker
    failure rate is within sweep 1's rate + 5 percentage points, which needs precondition 10 first.
  - `+RequestWalltime` = **1.5 × the re-measured chunk time** = `<s>`; proposed **8,735 s** = ⌈1.5 × 5,823⌉
    (`s2_c4_pilot.layout` now uses 1.5 and rounds up; the validator requires `walltime_s == ⌈1.5 ×
    layout_measured_chunk_s⌉` when that field is present).
  - **Other GPU models** (R1-SWEEP2-ANY-GPU). The chunk time was measured on an H200. A chunk that lands on a slower
    qualifying GPU (for example an L40S, A100 or V100 32 GB) may need longer, and a chunk over its walltime is a STOP.
    The measurement is also one node and one CPU: the pilot derives its specs from `spec.example.json`, node
    `digits_mlp`, and T0 worker training runs on the GPU node's CPU, so a slower node (the OpenML nodes) or a slower
    host CPU can exceed the walltime even on an H200. The GPU-h and wall projections inherit the same limitation.
    The node and host CPU of the re-measurement: `<from its job records>`. How the walltime covers the nodes, CPUs and
    GPU models admitted: `<author: re-measure on the slowest node and GPU model; or one walltime from this measurement
    with the over-walltime STOP accepted as the guard; or a larger factor, which needs an author row since
    R1-SWEEP2-LAYOUT-AMEND fixes 1.5>` (note 2). A per-GPU-model walltime would need a per-job model pin (against the
    row's "no model restriction") and changes to the key block, the S2-C5 switch and the validator.
  - **Chunk split.** In `s2_c4_pilot.py` a split is flagged when the proposed walltime (factor × chunk time) exceeds
    86,400 s, and the proposed walltime is capped at 86,400 s; the wrapper's validator also requires a walltime of at
    most 86,400 s. With the factor 1.5, a split is needed once the chunk time exceeds 57,600 s.
  - `request_disk` = the re-measured smoke's disk peak × 1.4, rounded up = `<kB>`; proposed **42,460,970 kB**.
    `request_memory` = its memory peak × 1.4, rounded up = `<MB>` (R1-SWEEP2-RESOURCES). The spec carries 32,000 MB,
    but that is the floor of `s2_c4_pilot.layout` (which takes the larger of ⌈1.4 × peak⌉ and 40,000,000 kB /
    32,000 MB), and earlier memory peaks were about 11 GB (10.95 GB in the 32k smoke; 10,853 MB in S2-C4), which give
    about 15,300 MB. The job records must show the H200 memory peak; if ⌈1.4 × peak⌉ < 32,000 MB, the floor and not the
    row set the value, and the value changes (or fix 2j removes the floor) (note 3). Precondition 5's report also shows
    the H200 disk peak, since 42,460,970 kB is within 7 kB of the void L40S value.
  - These values go into the job spec, and `render_jdl.py` writes them from it. The cluster's `sweep2/spec.example.json`
    at `d9b31a30` carries 8,735 s, 42,460,970 kB, 32,000 MB and `layout_measured_chunk_s` 5,823.
  - GPU memory at 32,768 with `-np 1` (32k L40S smoke job records, `server.cuda_lines`): model buffer 18,675.55 MiB,
    KV buffers 1,360.00 and 637.50 MiB, compute buffer 396.80 MiB; 21,069.85 MiB in all. This fits the 24 GB floor
    with about 3.4 GiB to spare against 24,576 MiB. If the author admits nominal-24 GB cards (see "Host"), whether the
    full offload holds on them is checked by the existing offload STOP, not measured here.
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
  - GPU-h = the number of chunks × the re-measured chunk time: `<GPU-h>`; on the H200 measurement 16 × 5,823 s =
    **25.88 GPU-h**. Chunks on slower GPU models take longer: `<projection over the GPU models expected>`.
  - Wall: with s qualifying GPU slots free to this user, about ⌈chunks / s⌉ × the chunk time, plus queue waits:
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
   is on `main` yet: `<integration commit>`. No independent review record was found on `sweep2-main-20261116` for
   `61282190`, `2efbb6f6`, `82c04862`, `83799722` or `d9b31a30`: `<reviews>`.
   - Round 5 (`sweep2-main-20261116` @ `8a8ea832`, minors at `d9a17b86`) covers redraft items 2b–2d and most of 2a
     and 2e: the 32,768 exam arguments, the noise-source binding, the restored gates and requests written from the
     spec.
   - **a′. Thinking-switch bytes.** The spec and the server argv carry exactly `{"enable_thinking":false}`, and the
     validator checks the bytes (R1-SWEEP2-LAYOUT-AMEND). **Implemented** in `2efbb6f6`: `EXAM_THINKING_KWARGS =
     '{"enable_thinking":false}'`, the exam's bytes (`r1/scripts/llama_server_instance.py`, `json.dumps(...,
     separators=(',', ':'))`), and `spec.example.json` carries them. Review: `<review>`.
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
   - **g. Record text.** **Implemented** in `2efbb6f6`: the chunk record carries the ENGINEERING `output_use` text
     only when the label is `ENGINEERING_ONLY`. Review: `<review>`. The record's `site_disclosure` text still says
     the requirements pin the L40S GPU model, which is no longer true after `82c04862`: `<fix>`.
   - **h. Whole-chunk rerun and walltime.**
     - Implemented on `sweep2-main-20261116`: a prior chunk in the sandbox is a STOP (no resume; resume functions
       removed in `2efbb6f6`), a chunk walltime check, `periodic_hold = (NumJobStarts > 1)` in the JDL (`2efbb6f6`),
       and walltime = ⌈1.5 × `layout_measured_chunk_s`⌉. Open: the field is optional in `validate_spec` (the check
       is skipped if it is absent); it becomes mandatory for EVIDENCE.
     - How "no STOP cause" is established for an evicted or killed attempt, which returns no outputs:
       `<evidence, e.g. HTCondor hold and eviction reason codes in the user log and job ad; if undecidable, treat as
       STOP>`.
     - The walltime floor of 3,600 s in `validate_spec` (3,600–86,400 s) is not part of "1.5 × the chunk time"; it
       binds only if the chunk time is below 2,400 s, which the H200 measurement (5,823 s) is not.
     - What is preserved from a killed or over-walltime attempt (at least the user log and the job ad; `out` / `err`
       only if streamed), given ON_EXIT transfer and no output streaming in `render_jdl.py` at `d9b31a30`.
   - **i. Host requirements and records** (R1-SWEEP2-ANY-GPU). **Implemented** in `82c04862`: `render_jdl.py`
     requires `GPUs >= 1`, `GPUs_GlobalMemoryMb >= 24576`, `GPUs_Capability >= 7.0` with no model pin;
     `validate_spec` requires `gpu_min_memory_mb` 24,576 and `gpu_min_capability` 7.0 and refuses a GPU model;
     `gpu_identity()` enforces the floor at run time and records model, UUID, driver, VRAM and compute capability.
     From `2efbb6f6` (R1-SWEEP-HOST-L40S-SITES): `validate_spec` refuses any site or CPU pin; `cpu_identity()` records
     the CPU and never STOPs on it; `site_identity()` records the site from the FQDN (`BwForCluster-Nemo2`, `portal`
     or `unknown`). Open: the stale `site_disclosure` text (2g) and the stale L40S and "pinned CPU class" comments and
     STOP messages; whether each campaign record carries a copy of the job's host record (see "Host"); `site` is
     `unknown` on any site other than NEMO2 and the ETP portal; the liveness job record (`run_liveness`) records host,
     GPU and CPU but not `site` (its FQDN stands in). Review: `<review>`.
   - **j. Requests** (R1-SWEEP2-RESOURCES). `s2_c4_pilot.layout` now rounds the peak × 1.4 up but still applies its
     floors (40,000,000 kB, 32,000 MB); `validate_spec` still refuses disk below 30,314,084 kB and memory below
     10,853 MB, floors from the void S2-C4 peaks. The proposed memory value equals the pilot's floor (note 3). The
     floors are removed, or the job records show that they did not set the values.
   - **k. Loopback port.** `83799722` picks a free port per job instead of the fixed 18,110 (two co-located smoke jobs
     collided); the port is recorded in `base_url`. A small race remains (the port is freed before llama-server binds
     it); a collision would end as a server-start STOP. A port is among the disclosed non-numeric differences. Review:
     `<review>`.
3. **S2-C3b liveness at the launch commit** (R1-SWEEP2-SETTINGS (4), R1-S2C3B-SEEDS, R1-S2C3B-LAUNCH). D28 liveness of
   the pick on all eight nodes on a qualifying GPU, seeds per `sweep1_d28_reuse`, with prompt lengths re-measured with the pick's
   tokenizer, run once at the launch commit with the launch's image digest, harness pin and server settings, after
   this note is committed (see "Order of commit and launch"). No earlier S2-C3b pass replaces it. Its result is
   recorded in `<launch record>`, not in this note. D28's criterion "keep after trial 1 ≥ 1" cannot pass if every
   worker run fails, so it also tests item 2f.
4. **S2-C3 deployment check** (R1-S2C3-DRIVER, R1-SWEEP2-ANY-GPU). One B2 replay with the declared-input,
   TASL-independent ENGINEERING replay driver, under the pre-declared criteria
   (`reports/sweep2_20261116/S2_C3_CRITERIA.md`), on the **first GPU model actually used** by sweep 2; the other GPU
   models are recorded and disclosed only. The criteria include criterion 2, parse-failure rate ≤ 0.02 against B2's
   0/240, and the corrected criterion 3: invalid 20 / duplicates 33 / no-ops 20 of 240, ± 10 %. What "the first GPU
   model actually used" means needs your choice (note 6), because P4 must read PASS in the committed note before
   launch, and with no model pin nobody knows beforehand which model the first of 16 chunks submitted together will
   land on:
   - (a) *(the agent's proposal)* the GPU model S2-C3 itself runs on counts as the first one used, since S2-C3 is
     sweep 2's first deployment use; P4 can then read PASS before launch, and every model is recorded and disclosed;
   - (b) the first sweep-2 chunk job's model, with a rule for a mismatch (for example: hold the sweep after the first
     chunk starts until S2-C3 has run on that model); this cannot be a PASS before launch.
   The S2-C3 driver jobs of 16 Nov (759736–759738) carried the L40S requirements; the driver must take the any-GPU
   requirements: `<fix>`. Passed: `<report, review>`.
5. **Re-measurement** (R1-SWEEP2-LAYOUT-AMEND). The 2-instance 32k smoke with training succeeding, after item 2f (and,
   for the proposed failure-rate check, after precondition 10). Run on an H200 and recorded in `d9b31a30` (above); it
   proposes the layout fields above. Its report (with the job records' disk and memory peaks) and its independent review:
   `<report, review>`.
6. **S2-C5 real-submission switch** accepted: `<review>`. At `s2c5-switch-20261116` @ `84a0dc30` it is check and
   submit only. Open:
   - it hard-codes the void R1-SWEEP2-LAYOUT values (`ACCEPTED_LAYOUT` and `REQUIRED_SPEC_LAYOUT`: 12,203 s,
     42,460,977 kB, 32,000 MB, 41.72 GPU-h) and v1 as `FROZEN_IMAGE`; it must take the re-measured layout and the
     authorized digest before it can accept this note;
   - its P1–P7 fields follow the cluster template, whose P5 still names the void R1-SWEEP2-LAYOUT; the key block above
     redefines them for this note, and the switch's wording may need to follow;
   - a seal step comparing the image digest with this note, checking the GPU floor and recording the GPU model, site
     and CPU, does not exist yet: `<fix>`.
7. **R1-MAIN-PROPOSER (g)2** (R1-SWEEP2-SETTINGS (3), R1-E1-OPENML). No exception for now.
   - The order is e1 environment replay, then the author's e2, then sweep-1 B.2. It runs in parallel with the sweep-2
     preparation. Status: e1 passed under R1-E1-OPENML-AMEND and its run review is ACCEPTED
     (`ops-e1-replay-amend-20261117` @ `52992b22`); the author signed R1-B2-GO (17 Nov (3)), which runs sweep-1 B.2 on
     deepthought's CPUs (revising the "fixed HTCondor CPU class" wording of R1-SWEEP2-SETTINGS (3)) once the e2 code
     unit is accepted and on `main` and the author commits the B.2 addendum.
   - The e1 offline mechanism establishes the identity of the six OpenML datasets with sweep 1's by the evidence of
     R1-E1-OPENML-AMEND, all four together: (i) the OpenML data ids match sweep 1's record; (ii) sweep 1's recorded
     loaded-data fingerprints equal, value by value, the fingerprints recomputed now from the same cache; (iii) each
     cached ARFF's md5 equals OpenML's `md5_checksum` in the cache metadata; (iv) the cache's per-file SHA-256 values
     are unchanged before and after use and equal those in `OFFLINE_MECHANISM_AUDIT.json`. Worker subprocesses run
     without network (unchanged). An independently reviewed offline mechanism on this basis must be wired into
     `c3_env_replay.py`, and all 16 e1 cases must then run under the e1 authorization with the zero-tolerance pass rule
     (done: `r1-e1-openml-amend-20261117` @ `bbcfc4a9`, run `ops-e1-replay-amend-20261117` @ `52992b22`). The
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
  - With the seal fix of precondition 6 it will also compare the image digest with this note, check the GPU floor and
    record GPU model, site and CPU. The accepted S2-C2 seal checks only that they are recorded.
  - A rerun chunk (above) is sealed into its new directory. The moved-aside directory is kept.
- **Analysis lock: satisfied.** The author signed **R1-BX-D8-CONFIRM** (`14c47777`, on `main` `26177d82`), which binds
  the gate code `r1/c3/gate.py` @ `6aa9985c` (sha256 `ffb70d7a…`) and says sweep-2 label tables may be analysed from
  that row on. The analysis readers' PLAN-line guard (`analysis_guard.guard_table` / `require_d8_confirmation`) is
  therefore met on `main`. Sweep-2 tables are analysed with the bound gate code only, and the other preregistration
  and analysis gates stay in force, as the row says. `refuse_sealed` does not apply to this path layout.
  - `d8_lock: true` stays in the key block, as the bare value `true`, because the S2-C5 switch's `parse_note` requires
    the field and compares it exactly; it now attests
    that R1-BX-D8-CONFIRM is present and that analysis uses the gate code it binds.

## Disclosed differences

**From sweep 1** (cross-proposer tables, R1-MAIN-PROPOSER (c) as amended by R1-SWEEP-HOST-HTC and
R1-SWEEP2-SETTINGS (1)):
- the manager;
- the host: deepthought TITAN X (sm_52) against the qualifying HTCondor GPUs actually used (models, sites and compute
  capabilities recorded per campaign), HTCondor container jobs;
- the CPU host of the in-campaign worker runs (sweep 2: the CPU model of each campaign's GPU node, recorded per
  campaign);
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
- GPU 4090 against the GPU models actually used;
- a direct server against an HTCondor container with the frozen image;
- the llama-server binary: the same llama.cpp commit `620d222`, but the exam binary `b70f4882…` ("build 1") against
  the image's `f8d35fd3…` ("build 11669");
- the non-numeric server arguments listed above (the thinking switch is byte-identical, so it is not among them);
- instance seeds: exam 9001+ (B1) and 9011+ (B2) against the sweep-1 instance seeds; exam audit seeds 9101+ (B1)
  and 9201+ (B2), whereas this note runs no audits;
- paper commit `37282ec3…` against the launch commit;
- harness: identical (`a3fedbb`).

**Within sweep 2:**
- the GPU model, site and CPU model of each campaign; descriptive strata by GPU model where useful
  (R1-SWEEP2-ANY-GPU);
- the liveness instances reuse the first two instance seeds of each node (R1-S2C3B-SEEDS, above);
- any whole-chunk rerun, with its reason and both directories.

## Boundaries and STOPs

**Scope.** This authorization covers the sweep-2 label collection (B.1b) only. The collector runs with
`--audit-seeds 0`, and seeds 7001–7010 stay reserved for the B.2 addendum. It does not cover:
- B.2 audits: sweep-2 B.2 is authorized later by an addendum (R1-SWEEP2-SETTINGS (2)), and R1-B2-DECOUPLE and
  R1-B2-REPLAY-GO stand;
- sweep-1 B.2;
- T1 sweeps;
- GPUs below the floor (VRAM < 24 GB or compute capability < 7.0);
- a second image digest;
- changing nodes, instances, settings or the layout after launch (a whole-chunk rerun under the rule above is not a
  change).

**Checks before launch.** Check all pins, the layout values and this note's sha256 against the job specs.

**STOP conditions.** These are runbook §4, the S2-C2 STOPs and R1-MAIN-PROPOSER's STOPs:
- a required PLAN row, precondition or authorization missing or different;
- a job on a GPU below the floor (VRAM < 24 GB or compute capability < 7.0);
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
- any analysis of sweep-2 labels that does not use the gate code bound by R1-BX-D8-CONFIRM;
- pushing `main` without the author's explicit instruction.

A chunk that ends for a reason on this list is a STOP, with its state preserved, even if the job was also evicted or
restarted (R1-SWEEP2-STOP-PRECEDENCE). Only an eviction or infrastructure interruption with no STOP cause
(`NumJobStarts` > 1 and the like) leads to a whole-chunk rerun under the rule above.
Preserve completed outputs and every attempt (never delete, never overwrite), and report any
STOP.

---

## Notes for the author (not part of the note)

1. **The implemented worker gate differs from (w2)** (item 2f): per (node, memory mode) rather than overall, and a STOP
   only when the rate also exceeds a 1 % exact-binomial bound. It is reviewed, but the row writes an overall rate
   against sweep 1's rate + 5 pp. Your choice is a placeholder in 2f.
2. **Walltime across nodes, CPUs and GPU models.** The chunk time (5,823 s) and the walltime (8,735 s) come from one
   node (`digits_mlp`, presumably), one H200 and its host CPU. Under R1-SWEEP2-ANY-GPU a chunk may land on a slower
   GPU or CPU, and the OpenML nodes may run longer; a chunk over its walltime is a STOP (R1-SWEEP2-LAYOUT-AMEND). The
   walltime rule needs a choice in "Job layout". The 60 GPU-h / 48 h projection cap is unchanged and inherits the
   same limitation.
3. **Memory request.** The spec's 32,000 MB is the pilot's floor; earlier peaks (about 11 GB) imply about 15,300 MB
   under R1-SWEEP2-RESOURCES (peak × 1.4, rounded up, no floor). The H200 job records decide.
4. **The S2-C5 switch and this note.** The switch's `parse_note` reads every `key: value` line of the note and requires
   the key block's fields, including `P1:`–`P7:` each starting with `PASS`; its accepted layout and frozen image are
   still the void values of 16 Nov (precondition 6). The key block's P lines are redefined for this note, as the
   agent's proposal; S2-C3b is not among them, because it runs after the note is committed.
5. **Commit order** (R1-S2C3B-LAUNCH). Committing the note on an `author-*` branch keeps `main` HEAD, and so the launch
   commit, unchanged after S2-C3b. The S2-C2 wrapper's `resolve_label` does not depend on the branch: it reads the
   staged note and checks its sha256 against the spec. The S2-C5 switch's `check()` needs the file under
   `docs/r1/authorizations/` in the submit-side working tree; nothing checks that this tree is clean.
6. **Placeholders and the unit that fills each one.**
   - The author: the opening paragraph; `run_id`; image digest (proposed v1 `69b06b35…`); launch commit; the P1–P7
     evidence; the (w2) form (2f); the walltime rule (note 2); the reading of "first GPU model used" (precondition 4,
     (a) or (b)); 24 GiB or nominal 24 GB ("Host"); (g)2 status.
   - Cluster fix units 2f, 2g (`site_disclosure`), 2h (mandatory `layout_measured_chunk_s`, "no STOP cause"
     evidence, preserved outputs), 2i (per-campaign copy), 2j, the S2-C3 driver's requirements and the S2-C5 layout
     and seal fixes, their reviews, and their integration into `main` (`<integration commit>`).
   - Re-measurement (precondition 5): its report with the disk and memory peaks, and its review; the H200 host's CPU
     model.
   - Sweep-1 failure rate (precondition 10).
   - S2-C3b at the launch commit, S2-C3, S2-C5, harness-defaults check: their reports.
7. **What changed from version 5** (`3c0c5f75`).
   - Authority: `author-decisions-20261117b` @ `45fb94cc` (over `main` `26177d82`); R1-SWEEP2-ANY-GPU, with
     R1-QTORCH-AMEND, R1-B2-GO and R1-SWEEP2-B2-DRAFT for context.
   - Host: any GPU with VRAM ≥ 24 GB and compute capability ≥ 7.0, no model or site pin; per-campaign GPU, site and
     CPU records; the table may mix GPU models; the STOP is a GPU below the floor.
   - S2-C3: one B2 replay on the first GPU model used; the other models recorded and disclosed.
   - Layout: proposed values from the H200 re-measurement (8,735 s, 42,460,970 kB, 32,000 MB, 25.88 GPU-h); open
     points on slower GPU models and on the memory floor.
   - Preconditions 2 and 6: the cluster's progress to `d9b31a30` (2a′ and 2g implemented, 2h partly, 2i rewritten for
     any GPU, new 2k), with no review records found; precondition 7 updated (e1 passed and reviewed; R1-B2-GO).
   - Removed: version 5's note on the thinking-switch constant (fixed in `2efbb6f6`) and its note on the site question
     (answered by R1-SWEEP2-ANY-GPU).
   - Analysis lock: R1-BX-D8-CONFIRM (signed `14c47777`, on `main` `26177d82`) is now recorded as satisfied, with the
     bound gate code; the "before R1-BX-D8-CONFIRM" STOP is replaced; `d8_lock: true` is explained (review round 1).
   - Review round 1 also: the two readings of "first GPU model used"; 24 GiB versus nominal 24 GB; node and CPU limits
     of the chunk time; the re-measurement's provenance; the memory value as the pilot floor; the 2i attribution split
     between `82c04862` and `2efbb6f6`; `universe = container`; the liveness record's missing `site`.
