# Draft authorization note: C3 sweep 2 (HTCondor, NEMO2 L40S). Update for the 32k layout (R1-SWEEP2-LAYOUT)

**This is a draft, not an authorization.** The Mac agent (Claude, AI-assisted) prepared it as unit S2-M1 of the
sweep-2 work plan (`prompts/SWEEP2_HTCONDOR_RUNBOOK_20261116.md`).
- It updates the accepted redraft (`mac-s2-m1-redraft-20261116` @ `e43faa29`, accepted at `11db0f65`), which applied
  R1-SWEEP2-SETTINGS.
- It applies the author rows of 16 Nov (2):
  - **R1-SWEEP2-LAYOUT:** the measured 32k layout (16 chunks, about 9,387 s per chunk, about 41.72 GPU-h;
    walltime 12,203 s, disk 42,460,977 kB, memory 32,000 MB), replacing the S2-C4 16k values;
  - **R1-S2C3B-SEEDS:** liveness seed policy `sweep1_d28_reuse`, with its disclosure;
  - **R1-S2C3-DRIVER** and **R1-E1-OPENML** where they bear on the preconditions.
- It fills the CPU class (`CpuFamily` 6 / `CpuModelNumber` 207, Xeon Platinum 8562Y+) from the cluster's accepted
  round-5 wrapper. It keeps no B.2 audits. The image digest stays a placeholder for the author, with v1
  `69b06b35…` as the proposed value.

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
- Read from `main` @ `025bfc16`, which carries all author rows to date. PLAN §10 rows take precedence over this note
  wherever they differ.
- The rows used are:
  - R1-SWEEP2-LAYOUT, R1-S2C3B-SEEDS, R1-S2C3-DRIVER and R1-E1-OPENML (16 Nov (2));
  - R1-SWEEP2-SETTINGS (1)–(5), as amended by R1-S2C3B-SEEDS, and R1-SWEEP-HOST-HTC;
  - R1-SWEEP1-CLASSIFY (label from the authorization only);
  - R1-EXAM-X7;
  - R1-MAIN-PROPOSER (b), (c), (e), (g), as amended by R1-SWEEP2-SETTINGS;
  - R1-BX-D8, R1-BX-PROPOSED-CONFIRM and R1-BX-D8-V3-A;
  - R1-CACHEPROMPT-FALSE, R1-EXAM-CACHE-REV and R1-EXAM-B1-HARNESS-PIN;
  - R1-B1-CORPUS-FREEZE;
  - R1-HARNESS-NEXT-PIN, R1-B2-DECOUPLE, R1-B2-REPLAY-GO and R1-E1-AUTH.
- The measured values come from the cluster's S2-C2 32k smoke (clusters 759728/759729), as R1-SWEEP2-LAYOUT cites
  it: `sweep2-main-20261116` @ `f172d299`, `reports/sweep2_20261116/SMOKE_RESULTS_20261116.md` and
  `smoke_20261116/` (`S2_C4_TIMING.md`, `timing.json`, both job records); sealed under
  `/ceph/srv/dwong/paperb/sweep2/s2smoke-20261116-a/`. The wrapper that ran it is the cluster's S2-C2 round 5,
  accepted by independent review (`reviews/S2_C2_REVIEW_20261116.md`, round 5 at `8a8ea832`, minors at `d9a17b86`). The
  smoke run itself has no separate review record on that branch.
- One smoke finding bears on the layout and is set out in note 1: every visible in-campaign worker run in both smoke
  job records failed in about 0.1 s.

Each value below cites its source.

---

# Authorization: C3 sweep 2 (HTCondor, NEMO2 L40S)

<Author's opening paragraph: date and time, the instruction, and what was read. Proposed facts to cite:
- `main` at `<launch commit>` carries the S2-M2 integration (`9ae6d877`), the accepted S2-C2 wrapper (round 5 and
  any later fix units) and the S2-C5 switch (this is `paper.evidence_ready`);
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
    S2-C4 and the 32k smoke.
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
  - One owned `llama-server` per job, bound to `127.0.0.1`, with log level `-lv 4` and alias `gemma4_31b`.
  - Temperature 0.2 with the D26 seed (`manager_seed(campaign_id, budget_index, repetition, revision_attempt)`).
  - **Disclosed non-numeric differences from the exam** (R1-SWEEP2-SETTINGS (1)):
    - the port and the model path;
    - the order of the arguments;
    - `--no-webui`;
    - the JSON spacing of the thinking switch. The exam writes `{"enable_thinking":false}`
      (`llama_server_instance.py`, `json.dumps` with compact separators). The cluster's spec carries
      `{"enable_thinking": false}`, and the wrapper passes it through as written. Round 5.1's m12 checks only that the
      parsed JSON is exactly `{"enable_thinking": false}`, not its bytes.
  - The round-5 job records list only `--no-webui` and `-lv 4` under `non_numeric_differences`. Either the spacing is
    added to that record, or the spec is made byte-identical to the exam: precondition 2a′.
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
- **Job layout: the measured 32k layout** (R1-SWEEP2-LAYOUT; smoke `S2_C4_TIMING.md`, `timing.json`).
  - One job is one (node, memory mode) chunk of root campaigns: **16 jobs**. No chunk split
    (`chunk_split_required: false`).
  - `request_gpus 1`, `request_cpus 16`, workers 16.
  - `+RequestWalltime` **12,203 s**; `request_disk` **42,460,977 kB**; `request_memory` **32,000 MB**
    (`sweep2/s2_c4_pilot.py`, `layout`):
    - walltime = 1.3 × the estimated full-chunk wall, 9,387 s, with a 3,600 s floor. The margin is 30 %.
    - disk = 1.4 × the peak of 30,329,269 kB.
    - memory = the 32,000 MB floor, since 1.4 × the 10,951 MB peak is 15,331 MB.
  - These are the values in the cluster's `sweep2/spec.example.json` at `f172d299`, and `render_jdl.py` writes them
    from the spec. The smoke jobs themselves ran with the earlier 16k requests (10,776 s, 42,439,718 kB); the spec was
    updated after them.
  - GPU memory at 32,768 with `-np 1` (job records, `server.cuda_lines`): model buffer 18,675.55 MiB, KV buffers
    1,360.00 and 637.50 MiB, compute buffer 396.80 MiB; 21,069.85 MiB in all. Against the 16k pilot (run without
    `-np 1`), the first KV buffer doubled (680.00 → 1,360.00 MiB) and the second fell (1,912.50 → 637.50 MiB). Total KV
    went from 2,592.50 to 1,997.50 MiB, and the total from 21,523.85 to 21,069.85 MiB. The smoke results file lists
    only the first KV buffer.
  - The GGUF is fetched once per chunk: 16 × 19.6 GB ≈ 314 GB of HF egress (disclosed; an image-side model cache is a
    later author decision).
  - **Resumption.** `<author>`. The S2-M3 hand-off review found that a resubmitted HTCondor job starts in a fresh
    scratch directory, so the wrapper's resume check never sees the earlier outputs. The proposed rule is that a job
    that does not finish cleanly, or that HTCondor restarts, is a STOP for the author, with no ad-hoc retry.
- **Estimate** (R1-SWEEP2-LAYOUT).
  - Measured: pilot wall at most 1,043 s for 2 instances on `digits_mlp`. The wrapper scales this to 9,387 s for a full
    chunk of 18 instances, and **41.72 GPU-h** for the 16 chunks. That is below R1-SWEEP2-SETTINGS (5)'s 60 GPU-h.
  - The scaling multiplies the whole wall by 9, fixed per-job costs included (`timing.json`, `assumptions`: "a
    conservative upper bound"). Only one node was measured.
  - Derived here (wall): the ad snapshot (09:53Z on 16 Nov, before the smoke) shows three matching L40S ads. It does
    not show claimed state or other users. If all three are free to this user, sixteen jobs run in six waves, so about
    6 × 9,387 s ≈ 15.6 h plus queue waits (23 s in the smoke). If all 16 ran at once, the wall would be about
    one chunk; one job at a time would take about 41.7 h. All three are within 48 h.
  - **Caveat (note 1).** The smoke's worker runs all failed, so these numbers may contain no training time. A full
    chunk with successful worker runs may take longer than 9,387 s.
  - **STOP for the author** if a projection of this kind exceeds **60 GPU-h** or **48 h wall** (R1-SWEEP2-SETTINGS (5)).
  - **Proposed by the agent, not decided** (`<author: adopt | strike>`): a further STOP when a re-measured chunk wall
    (precondition 5) exceeds the signed 12,203 s walltime. An over-walltime job is killed and cannot be resumed, so
    R1-SWEEP2-LAYOUT would need revising first.
  - The collector's `--deadline` is the walltime minus 600 s, counted from the collector's start. It only stops new
    root campaigns being submitted (`e1b_collect.py`); it never stops roots already running. With 18 instances on 16
    workers, 16 roots start at once, so the deadline can hold back at most the last 2. It gives no protection against
    the walltime: the HTCondor walltime is the only real limit (item 2h).

## Preconditions before launch

1. **S2-M2 integration on `main`.** Done: `9ae6d877`, an ancestor of `025bfc16`.
2. **S2-C2 wrapper on `main`**, accepted by independent review, with S2-C5.
   - Round 5 (`sweep2-main-20261116` @ `8a8ea832`, minors at `d9a17b86`) covers redraft items 2b–2d and most of 2a
     and 2e: the 32,768 exam arguments (except the thinking-switch bytes, 2a′), the noise-source binding, the restored
     gates, the CPU class in requirements and at run
     time, and requests written from the spec. It is not yet on `main`: `<integration commit>`.
   - Still open, each to be accepted by review:
     - **a′. Thinking-switch bytes.** Make the spec byte-identical to the exam's `{"enable_thinking":false}`, or record
       the spacing under `non_numeric_differences` (above).
     - **f. Worker runs.** In-campaign worker runs fail in both 32k smoke jobs (note 1). This needs a diagnosis, a fix,
       and a fail-closed check in the job, because no gate checks worker-run success today. Proposed: sweep 1's
       `package_environment` check before the collector, and a worker-success gate with a threshold the author sets
       (`<threshold>`). Then a re-run showing successful runs.
     - **g. Record text.** The chunk record hard-codes `output_use: "ENGINEERING: … disclose in the sweep-2 report as an
       engineering run"` whatever the label. An EVIDENCE chunk record must not carry it. The liveness record's content
       is right, since liveness output never enters a label table, but its `ENGINEERING:` prefix sits under the run's
       label. `<fix>`.
     - **h. Resumption and walltime**, per the author's choice above. The collector deadline does not stop running
       roots, so protection against the walltime needs either a per-job time budget enforced inside the job, or
       reliance on the walltime STOP: `<fix or author choice>`.
3. **The (g)4 liveness unit (S2-C3b)** (R1-SWEEP2-SETTINGS (4), R1-S2C3B-SEEDS). D28 liveness of the pick on all eight
   nodes on NEMO2 L40S, seeds per `sweep1_d28_reuse`, with prompt lengths re-measured with the pick's tokenizer.
   Passed: `<report, review>`. D28's criterion "keep after trial 1 ≥ 1" cannot pass if every worker run fails, so this
   unit also tests item 2f. Whether this unit's pass meets the pre-collection liveness gate, or a liveness job is
   re-run under the EVIDENCE `run_id` at launch: `<author>`.
4. **S2-C3 L40S deployment check** (R1-S2C3-DRIVER). Run with the declared-input, TASL-independent ENGINEERING replay
   driver, under the pre-declared criteria (`reports/sweep2_20261116/S2_C3_CRITERIA.md`). They include criterion 2,
   parse-failure rate ≤ 0.02 against B2's 0/240, and the corrected criterion 3: invalid 20 / duplicates 33 / no-ops 20
   of 240, ± 10 %. Passed: `<report, review>`.
5. **Re-measurement with successful worker runs.** *Proposed by the agent, not decided* (`<author: adopt | strike>`).
   R1-SWEEP2-LAYOUT bases the note on the smoke measurement as it stands. At least the smoke layout (one node × 2
   instances × both modes), preferably a full chunk. It must show worker runs succeeding and the gates passing. It
   yields the chunk wall to
   check against the signed 12,203 s and the projection: `<report, review>`.
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
8. **Projection** within 60 GPU-h and 48 h wall: the R1-SWEEP2-LAYOUT figure (41.72 GPU-h), or the item-5 figure if
   the author adopts item 5.
9. **Harness-defaults check** (R1-MAIN-PROPOSER (c)): `<report>`.

## Sealing and the analysis lock (R1-BX-D8)

- Job outputs come back to the submit host by HTCondor transfer (`out.tar`, `work.tar`, `job_record.json`,
  `SHA256SUMS`, `llama-server.log`). The seal step (`sweep2/s2_c2_lib.py seal`) copies them into
  `/ceph/srv/dwong/paperb/sweep2/<run_id>/<chunk_id>/`.
  - It refuses `..`, symlinks and overwrites, and writes `SHA256SUMS` and `SEAL_RECEIPT.json`.
  - With S2-C5 (precondition 6) it will also compare the image digest and host with this note. The accepted S2-C2
    seal checks only that they are recorded.
- No sweep-2 label table is copied back for analysis, or read by any analysis code, before the author row
  **R1-BX-D8-CONFIRM** exists. R1-BX-D8-V3-A keeps this lock.
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
- the non-numeric server arguments listed above;
- instance seeds: exam 9001+ (B1) and 9011+ (B2) against the sweep-1 instance seeds; exam audit seeds 9101+ (B1)
  and 9201+ (B2), whereas this note runs no audits;
- paper commit `37282ec3…` against the launch commit;
- harness: identical (`a3fedbb`).

**Within sweep 2:** the liveness instances reuse the first two instance seeds of each node (R1-S2C3B-SEEDS, above).

## Boundaries and STOPs

**Scope.** This authorization covers the sweep-2 label collection (B.1b) only. The collector runs with
`--audit-seeds 0`, and seeds 7001–7010 stay reserved for the B.2 addendum. It does not cover:
- B.2 audits: sweep-2 B.2 is authorized later by an addendum (R1-SWEEP2-SETTINGS (2)), and R1-B2-DECOUPLE and
  R1-B2-REPLAY-GO stand;
- sweep-1 B.2;
- T1 sweeps;
- other GPU models or CPU classes;
- a second image digest;
- changing nodes, instances, settings or the layout after launch.

**Checks before launch.** Check all pins, the layout values and this note's sha256 against the job specs.

**STOP conditions.** These are runbook §4, the S2-C2 STOPs and R1-MAIN-PROPOSER's STOPs:
- a required PLAN row, precondition or authorization missing or different;
- a job on a GPU other than L40S, or on a CPU outside family 6 / model 207 / `INTEL(R) XEON(R) PLATINUM 8562Y+`;
- a GGUF SHA-256 mismatch;
- a noise-source SHA-256 mismatch;
- server arguments or `cache_prompt` differing from the values above, other than the disclosed non-numeric
  differences;
- an image identity mismatch;
- incomplete offload or OOM;
- a liveness or collection gate failing;
- the worker-success gate of item 2f failing (threshold `<author>`);
- per the author's resumption choice (proposed rule): a job that does not finish cleanly, exceeds its walltime, or is
  restarted by HTCondor (`NumJobStarts` > 1) (see "Resumption");
- a label string not matching this note;
- a projection above 60 GPU-h or 48 h wall;
- if the author adopts it, a re-measured chunk wall above 12,203 s;
- any code path reading sweep-2 labels before R1-BX-D8-CONFIRM;
- pushing `main` without the author's explicit instruction.

Preserve completed outputs and every attempt (never delete, never overwrite), and report any STOP.

---

## Notes for the author (not part of the note)

1. **The 32k smoke's worker runs failed, as the 16k pilot's did.**
   - **What the records show.** Both smoke job records (759728, 759729) keep the last part of the collector's stderr.
     Every in-campaign worker run visible there, 9 per job, ran `python3 train.py` and ended in 0.0–0.1 s with
     `success=False metrics={}`. The S2-C4 16k pilot records showed the same.
   - **The gates passed anyway.** They count roots, LLM calls and parse failures, not worker-run success.
   - **Only the tails were read.** The sealed outputs and the full logs were not.
   - **A likely cause, not verified.** The wrapper starts the collector with `/opt/r1/envs/harness/bin/python`, but
     passes an environment that sets `PYTHONPATH` and `AR_HARNESS_ROOT` and leaves `PATH` as it is. The worker then
     runs `python3 train.py`, which may resolve to a Python without the training dependencies. Sweep 1 had
     `package_environment` / `evidence_node_commands` checks for this.
   - **What it means for R1-SWEEP2-LAYOUT.**
     - The collector took 210.4 s and 184.9 s of the 1,043 s and 868 s walls. So 9,387 s per chunk and 41.72 GPU-h may
       contain no training time.
     - The scaling is conservative on fixed costs, so the signed values may still hold. But this cannot be known until
       a run with successful worker runs is measured (precondition 5).
     - If a re-measured chunk exceeded 12,203 s (walltime margin 30 %), the walltime and the GPU-h figure in
       R1-SWEEP2-LAYOUT would need revising before launch. Precondition 5 is the agent's proposal for checking this.
   - **What catches it before EVIDENCE.** The (g)4 liveness and S2-C3 would both fail on failing worker runs. The
     cluster side has not reported the failures, and neither the S2-C4 review nor the smoke results mention them.
2. **Placeholders and the unit that fills each one.**
   - The author: the opening paragraph; the `run_id` in the key block; image digest (proposed v1 `69b06b35…`);
     resumption rule; whether to adopt precondition 5 and its walltime STOP; the worker-success threshold (2f); how the
     liveness gate is met (precondition 3); launch commit; (g)2 status.
   - Cluster S2-C2 fix units 2a′ and 2f–2h, and the integration of round 5 into `main` (`<integration commit>`).
   - S2-C3b ((g)4 liveness): liveness report.
   - S2-C3 (R1-S2C3-DRIVER): deployment check report.
   - Re-measurement (precondition 5): chunk wall and projection.
   - S2-C5: seal check.
   - Harness-defaults check.
3. **What changed from the accepted redraft.**
   - Authority: `main` @ `025bfc16`.
   - Layout: the R1-SWEEP2-LAYOUT values (12,203 s, 42,460,977 kB, 32,000 MB; 9,387 s per chunk; 41.72 GPU-h),
     replacing S2-C4's 16k values. The GPU memory figures are now from the 32k smoke.
   - CPU class: family 6 / model 207 in the requirements and at run time, replacing the "value missing" item.
   - Liveness seed policy `sweep1_d28_reuse` and its disclosure.
   - Preconditions: round 5 covers redraft items 2b–2d, most of 2a (all but the thinking-switch bytes, now 2a′) and most
     of 2e. New items: 2a′, 2f worker runs, 2g record text, 2h resumption and walltime, and 5 (the re-measurement,
     proposed). S2-C3 cites R1-S2C3-DRIVER, and (g)2 cites R1-E1-OPENML.
   - The redraft's "resumable only by the collector's A.5 resume" line is replaced by the resumption item.
   - Derived wall for three matching slots.
   - Image: still the author's, with v1 proposed. No B.2 audits.
