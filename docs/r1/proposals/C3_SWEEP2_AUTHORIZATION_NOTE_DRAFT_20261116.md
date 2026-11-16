# Draft authorization note: C3 sweep 2 (HTCondor, NEMO2 L40S). Update per R1-SWEEP2-LAYOUT-AMEND

**This is a draft, not an authorization.** The Mac agent (Claude, AI-assisted) prepared it as unit S2-M1 of the
sweep-2 work plan (`prompts/SWEEP2_HTCONDOR_RUNBOOK_20261116.md`).
- It updates the accepted 32k-layout draft (`mac-s2-m1-v3-20261116` @ `38fb3620`, accepted at `2939f986`).
- It applies the author row **R1-SWEEP2-LAYOUT-AMEND** (16 Nov (3)):
  - the R1-SWEEP2-LAYOUT numbers are void, so the layout fields are placeholders until the re-measurement: a 2-instance
    32k smoke in which training actually succeeds;
  - two new worker gates;
  - walltime = 1.5 × the re-measured chunk time, and a chunk over its walltime is a STOP;
  - no resume path: a killed or abnormally ended chunk is rerun whole, in a new directory, with the old directory moved
    aside (not deleted), and disclosed;
  - the thinking switch byte-identical to the exam (no disclosure in its place);
  - the S2-C3b liveness pass counts as the pre-launch liveness check, under a sameness condition;
  - the 60 GPU-h / 48 h projection caps unchanged.
- Kept from the accepted draft: the CPU class (`CpuFamily` 6 / `CpuModelNumber` 207), the liveness seed policy
  `sweep1_d28_reuse` with its disclosure, no B.2 audits, and the image digest left to the author (v1 `69b06b35…`
  proposed).

**How the author uses it:**
- Copy the block between the two rules below to `docs/r1/authorizations/c3_sweep2_<date>.md` on `main`.
- Fill every `<…>` placeholder, and add your own prose to the opening paragraph.
- Set `approved: true` yourself. This draft keeps `approved: false`, and the agent never sets it.

The format follows `authorizations/c3_sweep1_20261027.md`: an opening paragraph, "Proposed scope and pins",
"Boundaries and STOPs". A short key block is added because the S2-C2 job wrapper reads three things from the note
(`sweep2/s2_c2_lib.py`, `resolve_label`):
- a line `approved: true`;
- the run id;
- `label: EVIDENCE`.

It refuses the note otherwise, and it also refuses a note whose sha256 differs from the job spec's.

**Authority.**
- Read from `author-decisions-20261116c` @ `65d8d5bb`, which descends from `main` @ `025bfc16` and adds the 16 Nov (3)
  rows. PLAN §10 rows take precedence over this note wherever they differ.
- The rows used are:
  - R1-SWEEP2-LAYOUT-AMEND (16 Nov (3)), which voids the numbers of R1-SWEEP2-LAYOUT;
  - R1-S2C3B-SEEDS, R1-S2C3-DRIVER and R1-E1-OPENML (16 Nov (2));
  - R1-SWEEP2-SETTINGS (1)–(5), as amended by R1-S2C3B-SEEDS and R1-SWEEP2-LAYOUT-AMEND, and R1-SWEEP-HOST-HTC;
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

Each value below cites its source.

---

# Authorization: C3 sweep 2 (HTCondor, NEMO2 L40S)

<Author's opening paragraph: date and time, the instruction, and what was read. Proposed facts to cite:
- `main` at `<launch commit>` carries the S2-M2 integration (`9ae6d877`), the accepted S2-C2 wrapper (round 5 and
  the fix units below) and the S2-C5 switch (this is `paper.evidence_ready`);
- the preconditions below are met: `<reports, reviews>`.
The paper commit is determined at launch.>

```
approved: false
label: EVIDENCE
run_id: <run id, e.g. s2ev-<YYYYMMDD>-a; every job spec and job record carries it>
phase: c3_sweep2
```

## Proposed scope and pins

- **Host.** HTCondor job submission (R1-SWEEP-HOST-HTC).
  - LLM-backed label runs: NEMO2 L40S only. The job requirements pin `CloudSite == "BwForCluster-Nemo2"`,
    `GPUs_DeviceName == "NVIDIA L40S"`, `Arch == "X86_64"`, `OpSys == "LINUX"` and `Cpus >= 16` (S2-C2 class
    constants; `sweep2/render_jdl.py`).
  - **CPU class: `CpuFamily` 6 / `CpuModelNumber` 207, the Intel Xeon Platinum 8562Y+.**
    - It is pinned in the HTCondor requirements (`TARGET.CpuFamily =?= 6`, `TARGET.CpuModelNumber =?= 207`). The job
      also checks it at run time from `/proc/cpuinfo`: family, model number and the model string
      `INTEL(R) XEON(R) PLATINUM 8562Y+` (S2-C2 round 5, `cpu_identity`).
    - Measured on both smoke hosts, `g3608` and `g3610` (job records `cpu`). The cluster's ad snapshot of 16 Nov
      (`sweep2/evidence/condor_status_l40s_20261116.txt`) lists three L40S ads that match the full requirement:
      two on `g3608`, one on `g3610`.
  - One GPU model and one CPU class for the whole sweep-2 table. A job that lands elsewhere is a STOP.
  - Selection ran on a 4090 (B1/B2 on TASL-7) and deployment runs on the L40S. This is disclosed, and it is why the
    S2-C3 deployment check must pass first.
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
    S2-C4 and the 32k smoke. If the worker-run fix (2f) changes the image, the digest changes with it.
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
    separators). The cluster's round-5 spec carries `{"enable_thinking": false}` (with a space), and round 5.1's m12
    checks only the parsed JSON. Both must change, and a disclosure does not replace the fix (precondition 2a′).
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
  - **Pre-launch liveness** (R1-SWEEP2-LAYOUT-AMEND). A pass of the S2-C3b liveness unit counts as the pre-launch
    liveness check, provided its image digest, paper commit, harness pin and server settings are the same as the
    launch's. Otherwise liveness is run again under those launch values before collection.
- **Worker gates** (R1-SWEEP2-LAYOUT-AMEND). Both are STOPs:
  - **(w1)** any campaign with no successful in-campaign worker run;
  - **(w2)** an overall worker failure rate above sweep 1's failure rate + 5 percentage points. Sweep 1's rate is
    computed from its ledger first and recorded: `<sweep-1 worker failure rate, its definition, ledger source and
    the record that holds it>`. How the overall rate is accumulated across chunk jobs: `<fix unit 2f>`.
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
  - **Re-measurement.** A 2-instance 32k smoke, after the worker-run fix (2f), in which training actually succeeds
    (worker gates (w1) and (w2) pass): `<report, review>`. It gives the chunk time
    `<re-measured chunk time, s, and how it is derived from the 2-instance run>`.
  - `+RequestWalltime` = **1.5 × the re-measured chunk time** = `<s>`. The cluster's `sweep2/s2_c4_pilot.py`
    (`layout`) still proposes 1.3 ×, with a 3,600 s floor and a chunk split above 86,400 s; its factor must become 1.5
    before it proposes the spec value (item 2h).
  - `request_disk` `<kB>` and `request_memory` `<MB>`, from the re-measurement's peaks (`s2_c4_pilot.py`, `layout`:
    each is the larger of 1.4 × the peak and its floor, 40,000,000 kB for disk and 32,000 MB for memory).
  - These values go into the job spec, and `render_jdl.py` writes them from it.
  - GPU memory at 32,768 with `-np 1` (32k smoke job records, `server.cuda_lines`; server facts, not affected by the
    worker failure): model buffer 18,675.55 MiB, KV buffers 1,360.00 and 637.50 MiB, compute buffer 396.80 MiB;
    21,069.85 MiB in all.
  - The GGUF is fetched once per chunk: 16 × 19.6 GB ≈ 314 GB of HF egress (disclosed; an image-side model cache is a
    later author decision).
  - **No resume path; whole-chunk rerun** (R1-SWEEP2-LAYOUT-AMEND). There is no resume. A chunk whose job is killed or
    ends abnormally, including a job that HTCondor started more than once (`NumJobStarts` > 1), is rerun whole:
    - in a new directory: `<directory naming for a rerun>`;
    - with the old directory moved aside, not deleted: `<where it is moved>`;
    - disclosed in the sweep-2 report, with the reason and both directories.
  - **Walltime STOP.** A chunk that exceeds its walltime is a STOP, not a rerun.
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
2. **S2-C2 wrapper on `main`**, accepted by independent review, with S2-C5.
   - Round 5 (`sweep2-main-20261116` @ `8a8ea832`, minors at `d9a17b86`) covers redraft items 2b–2d and most of 2a
     and 2e: the 32,768 exam arguments (except the thinking-switch bytes, 2a′), the noise-source binding, the restored
     gates, the CPU class in requirements and at run time, and requests written from the spec. It is not yet on
     `main`: `<integration commit>`.
   - Still open, each to be accepted by review:
     - **a′. Thinking-switch bytes.** The spec and the server argv carry exactly `{"enable_thinking":false}`, and the
       validator checks the bytes, not only the parsed JSON (R1-SWEEP2-LAYOUT-AMEND).
     - **f. Worker runs and worker gates.** In-campaign worker runs fail in both 32k smoke jobs (note 1). This needs a
       diagnosis and a fix, and the job must apply worker gates (w1) and (w2), because no gate checks worker-run success
       today. Sweep 1's `package_environment` check before the collector is a candidate for catching the cause early.
     - **g. Record text.** The chunk record hard-codes `output_use: "ENGINEERING: … disclose in the sweep-2 report as an
       engineering run"` whatever the label. An EVIDENCE chunk record must not carry it. The liveness record's content
       is right, since liveness output never enters a label table, but its `ENGINEERING:` prefix sits under the run's
       label. `<fix>`.
     - **h. Whole-chunk rerun and walltime.** The submission side detects a killed or abnormally ended chunk, including
       `NumJobStarts` > 1, and the rerun follows the rule above (new directory, old one moved aside, disclosure). A job
       over its walltime is reported as a STOP. The collector deadline does not stop running roots, so the HTCondor
       walltime is the limit that applies. The walltime factor in `s2_c4_pilot.py` changes from 1.3 to 1.5.
3. **The (g)4 liveness unit (S2-C3b)** (R1-SWEEP2-SETTINGS (4), R1-S2C3B-SEEDS). D28 liveness of the pick on all eight
   nodes on NEMO2 L40S, seeds per `sweep1_d28_reuse`, with prompt lengths re-measured with the pick's tokenizer.
   Passed: `<report, review>`. D28's criterion "keep after trial 1 ≥ 1" cannot pass if every worker run fails, so this
   unit also tests item 2f. Its pass counts as the pre-launch liveness check only if its image digest, paper commit,
   harness pin and server settings are the launch's (R1-SWEEP2-LAYOUT-AMEND). In practice, it runs after items 2 and 6
   are on `main`.
4. **S2-C3 L40S deployment check** (R1-S2C3-DRIVER). Run with the declared-input, TASL-independent ENGINEERING replay
   driver, under the pre-declared criteria (`reports/sweep2_20261116/S2_C3_CRITERIA.md`). They include criterion 2,
   parse-failure rate ≤ 0.02 against B2's 0/240, and the corrected criterion 3: invalid 20 / duplicates 33 / no-ops 20
   of 240, ± 10 %. Passed: `<report, review>`.
5. **Re-measurement** (R1-SWEEP2-LAYOUT-AMEND). The 2-instance 32k smoke with training succeeding, after item 2f. It
   fixes the layout fields above: `<report, review>`.
6. **S2-C5 real-submission switch** accepted. It includes the seal step comparing image digest and host with the
   values authorized here: `<review>`.
7. **R1-MAIN-PROPOSER (g)2** (R1-SWEEP2-SETTINGS (3), R1-E1-OPENML). No exception for now.
   - The order is e1 environment replay, then the author's e2, then sweep-1 B.2 on one pinned HTCondor CPU class. It
     runs in parallel with the sweep-2 preparation.
   - The e1 offline mechanism must first prove that the six OpenML datasets are exactly sweep 1's, by the identity
     sweep 1 recorded, and run worker subprocesses without network. If the identity cannot be proved, it is a STOP
     for the author (R1-E1-OPENML).
   - An exception is discussed only if (g)2 becomes sweep 2's only blocker. Status at launch:
     `<sweep-1 B.2 complete | exception row>`.
8. **Projection** within 60 GPU-h and 48 h wall, from item 5.
9. **Harness-defaults check** (R1-MAIN-PROPOSER (c)): `<report>`.
10. **Sweep-1 worker failure rate** computed from its ledger and recorded, for worker gate (w2): `<report>`.

## Sealing and the analysis lock (R1-BX-D8)

- Job outputs come back to the submit host by HTCondor transfer (`out.tar`, `work.tar`, `job_record.json`,
  `SHA256SUMS`, `llama-server.log`). The seal step (`sweep2/s2_c2_lib.py seal`) copies them into
  `/ceph/srv/dwong/paperb/sweep2/<run_id>/<chunk_id>/`.
  - It refuses `..`, symlinks and overwrites, and writes `SHA256SUMS` and `SEAL_RECEIPT.json`.
  - With S2-C5 (precondition 6) it will also compare the image digest and host with this note. The accepted S2-C2
    seal checks only that they are recorded.
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
- the host: deepthought TITAN X (sm_52) against NEMO2 L40S (sm_89), HTCondor container jobs;
- the CPU host of the in-campaign worker runs (sweep 2: Xeon Platinum 8562Y+, family 6 / model 207);
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
- the liveness instances reuse the first two instance seeds of each node (R1-S2C3B-SEEDS, above);
- any whole-chunk rerun, with its reason and both directories.

## Boundaries and STOPs

**Scope.** This authorization covers the sweep-2 label collection (B.1b) only. The collector runs with
`--audit-seeds 0`, and seeds 7001–7010 stay reserved for the B.2 addendum. It does not cover:
- B.2 audits: sweep-2 B.2 is authorized later by an addendum (R1-SWEEP2-SETTINGS (2)), and R1-B2-DECOUPLE and
  R1-B2-REPLAY-GO stand;
- sweep-1 B.2;
- T1 sweeps;
- other GPU models or CPU classes;
- a second image digest;
- changing nodes, instances, settings or the layout after launch (a whole-chunk rerun under the rule above is not a
  change).

**Checks before launch.** Check all pins, the layout values and this note's sha256 against the job specs.

**STOP conditions.** These are runbook §4, the S2-C2 STOPs and R1-MAIN-PROPOSER's STOPs:
- a required PLAN row, precondition or authorization missing or different;
- a job on a GPU other than L40S, or on a CPU outside family 6 / model 207 / `INTEL(R) XEON(R) PLATINUM 8562Y+`;
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

A chunk killed or ended abnormally for another reason (including `NumJobStarts` > 1) is not a STOP: it is rerun whole
under the rule above. Preserve completed outputs and every attempt (never delete, never overwrite), and report any
STOP.

---

## Notes for the author (not part of the note)

1. **The worker-run failure behind R1-SWEEP2-LAYOUT-AMEND.**
   - Both 32k smoke job records (759728, 759729) keep the last part of the collector's stderr. Every in-campaign
     worker run visible there, 9 per job, ran `python3 train.py` and ended in 0.0–0.1 s with
     `success=False metrics={}`. The S2-C4 16k pilot records showed the same. Only the tails were read.
   - A likely cause, not verified: the wrapper starts the collector with `/opt/r1/envs/harness/bin/python`, but passes
     an environment that sets `PYTHONPATH` and `AR_HARNESS_ROOT` and leaves `PATH` as it is, so `python3 train.py` may
     resolve to a Python without the training dependencies.
2. **Two points the row leaves to the fix units, so they appear as placeholders.**
   - Worker gate (w2): how sweep 1's failure rate is defined (for example, runs with `success=False` over all
     in-campaign worker runs) and how the sweep-2 rate is accumulated across chunk jobs. The two must use the same
     definition.
   - The rerun mechanics: directory naming, where the old directory is moved, and how the submission side detects
     `NumJobStarts` > 1.
3. **Placeholders and the unit that fills each one.**
   - The author: the opening paragraph; the `run_id` in the key block; image digest (proposed v1 `69b06b35…`);
     launch commit; (g)2 status.
   - Cluster S2-C2 fix units 2a′ and 2f–2h, and the integration of round 5 into `main` (`<integration commit>`).
   - Re-measurement (precondition 5): chunk split, chunk time, walltime, disk, memory, GPU-h, wall.
   - Sweep-1 failure rate (precondition 10).
   - S2-C3b ((g)4 liveness), S2-C3 (R1-S2C3-DRIVER), S2-C5, harness-defaults check: their reports.
4. **What changed from the accepted 32k-layout draft** (`38fb3620`).
   - Authority: `author-decisions-20261116c` @ `65d8d5bb`; R1-SWEEP2-LAYOUT-AMEND and R1-BX-D8-V3-B added.
   - Layout: the R1-SWEEP2-LAYOUT values (9,387 s, 41.72 GPU-h, 12,203 s, 42,460,977 kB, 32,000 MB) and the derived
     wave estimate are removed; the fields are placeholders for the re-measurement. Walltime = 1.5 × the re-measured
     chunk time. The GPU memory figures are kept as server facts.
   - Worker gates (w1) and (w2) added to the gates, item 2f and the STOP list; precondition 10 added.
   - Resumption: the `<author>` item and the proposed "non-clean job = STOP" rule are replaced by the whole-chunk rerun
     rule; the walltime STOP stays as a STOP.
   - Thinking switch: from a disclosed difference to a required byte-identical fix (2a′).
   - Pre-launch liveness: the `<author>` placeholder is replaced by the row's condition.
   - Preconditions 5 and 8: no longer agent proposals; the re-measurement is decided.
