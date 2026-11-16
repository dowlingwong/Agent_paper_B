# Draft authorization note: C3 sweep 2 (HTCondor, NEMO2 L40S). Redraft after R1-SWEEP2-SETTINGS

**This is a draft, not an authorization.** The Mac agent (Claude, AI-assisted) prepared it as unit S2-M1 of the
sweep-2 work plan (`prompts/SWEEP2_HTCONDOR_RUNBOOK_20261116.md`, `docs/runbooks-16nov` @ `a2789ea6`).
- It redrafts the accepted first draft (`mac-s2-m1-auth-20261116` @ `56b5b76e`).
- It applies the author's decisions of 16 Nov in R1-SWEEP2-SETTINGS:
  - context 32,768 with the exam's server flags;
  - no B.2 audits in this note;
  - (g)2 without an exception for now;
  - a new (g)4 liveness unit and the restored sweep-1 gates;
  - a projection STOP above 60 GPU-h or 48 h wall.

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
- Read from `author-decisions-20261116` @ `4da73306`, which descends from `main` @ `9ae6d877`; that `main` carries the
  S2-M2 integration. PLAN §10 rows take precedence over this note wherever they differ.
- The rows used are:
  - R1-SWEEP2-SETTINGS (1)–(5) and R1-SWEEP-HOST-HTC;
  - R1-EXAM-X7;
  - R1-MAIN-PROPOSER (b), (c), (e), (g), as amended by R1-SWEEP2-SETTINGS;
  - R1-BX-D8, R1-BX-PROPOSED-CONFIRM and R1-BX-D8-V3-A;
  - R1-CACHEPROMPT-FALSE, R1-EXAM-CACHE-REV and R1-EXAM-B1-HARNESS-PIN;
  - R1-B1-CORPUS-FREEZE;
  - R1-HARNESS-NEXT-PIN, R1-B2-DECOUPLE, R1-B2-REPLAY-GO and R1-E1-AUTH.
- The measured values come from the cluster's S2-C4 results (`sweep2-cluster-20261116` @ `acae9fde`,
  `reports/sweep2_20261116/S2_C4_RESULTS_20261116.md`, `s2c4_run_20261116/`, accepted unit
  `reviews/S2_C4_REVIEW_20261116.md`). They were measured at context **16,384**, before the change to 32,768. They are
  marked where 32,768 can change them.

Each value below cites its source.

---

# Authorization: C3 sweep 2 (HTCondor, NEMO2 L40S)

<Author's opening paragraph: date and time, the instruction, and what was read. Proposed facts to cite:
- `main` at `<launch commit>` carries the S2-M2 integration (`9ae6d877`) and the accepted S2-C2 fix units and S2-C5
  switch (this is `paper.evidence_ready`);
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
    `GPUs_DeviceName == "NVIDIA L40S"`, machine `^g36[0-9]{2}\.nemo\.privat$` and `Cpus >= 16` (S2-C2 class
    constants).
  - CPU model: `INTEL(R) XEON(R) PLATINUM 8562Y+`, as measured on both S2-C4 hosts (`g3605`, `g3608`; job records
    `cpu.model`).
  - The pilot did not require this model (`cpu.required_contains: null`). R1-SWEEP-HOST-HTC says the job requirements
    fix the CPU model, so the S2-C2 fix units must add it to the requirements or to the in-job check:
    `<accepted fix>`.
  - One GPU model and one CPU class for the whole sweep-2 table. A job that lands elsewhere is a STOP.
  - Selection ran on a 4090 (B1/B2 on TASL-7) and deployment runs on the L40S. This is disclosed, and it is why the
    S2-C3 deployment check must pass first.
- **Paper commit.** `main` HEAD at launch. It must contain the S2-M2 integration (`9ae6d877`) and the accepted S2-C2
  fix units and S2-C5 switch (`<launch commit>`). It is recorded in every job record.
- **Harness.** `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` (`cacheprompt-20261031`, the B2 stack): an explicit
  `cache_prompt: false` on every request.
  - `r1/scripts/HARNESS_PIN_C3` on `main` @ `9ae6d877` carries this value.
  - R1-MAIN-PROPOSER (c) requires a check that the harness defaults used by the sweep are unchanged:
    `<check, report, review>`.
- **Image (S2-C1).**
  - GPU image: `<ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296 — proposed v1; used by S2-C4>`.
  - Identity markers, as in the S2-C4 job records: `llama_server_sha256` `f8d35fd33e866808bc76457cf52cf1f8b1baafde9c2c8eebae51abf428843cc0`,
    `versions_sha256` `d31e8b2336c1a1a698163ef8c20f2cdf067bed9539e73bb7b545aeffb117dcc2`.
  - One digest for the table. No switch during the sweep.
- **llama.cpp.** Commit `620d2225cc436ab0b001e3200e590e3b286ef9ab` (in the image). The server reports the build line
  `0.7.0-dev (build 11669, commit 620d2225c)` (S2-C4 job records, `server.build`).
- **Manager: the pick `gemma4_31b`, thinking off** (R1-EXAM-X7, R1-MAIN-PROPOSER).
  - GGUF: `bartowski/google_gemma-4-31B-it-GGUF` @ `619aca7589c72be65dd968de8602ad23d68b5c14`, file
    `google_gemma-4-31B-it-Q4_K_M.gguf`, size 19,598,489,952 B, SHA-256
    `2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75`.
  - Registry doc `reports/exam_phase2_20261026/gemma4_31b.json`, SHA-256
    `a04a0346ca887c27998b5f46f4e3d67fa05126ff3af9e0c20fe78d030c1fdc61`.
  - The job checks the GGUF SHA-256 after fetching it.
- **Server: the selection exam's arguments** (R1-SWEEP2-SETTINGS (1)).
  - The arguments are those of the exam launcher (`r1/exam/runtime.py` `EXAM_SERVER_ARGS` and the 32,768 / 999 check;
    `r1/scripts/llama_server_instance.py` `argv` and `thinking_args`). They are `-ngl 999`, `-c 32768`, `-np 1`,
    `--jinja`, `--cache-type-k q8_0`, `--cache-type-v q8_0`, and `--chat-template-kwargs {"enable_thinking":false}`.
  - One owned `llama-server` per job, on `127.0.0.1` with its own port and alias.
  - Temperature 0.2 with the D26 seed (`manager_seed(campaign_id, budget_index, repetition, revision_attempt)`).
  - `cache_prompt: false` on every call; `LLAMACPP_CACHE_PROMPT` and `LLAMACACHE_PROMPT` unset.
  - Non-numeric differences from the exam are disclosed (R1-SWEEP2-SETTINGS (1)). They are the log level (the exam
    used `-lv 4`), `--no-webui` if the wrapper keeps it, and the port, alias and host binding:
    `<list from the accepted S2-C2 fix>`.
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
  `3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310`, as in sweep 1.
  - It is passed to the collector as `--e1-summary` and recorded as `noise_source` in each campaign manifest, as sweep
    1's runner did; `r1/c3/dataset.py` checks it.
  - This needs an S2-C2 fix (precondition 2b).
- **Gates, restored from sweep 1** (R1-SWEEP2-SETTINGS (4)).
  - Before collection: liveness with `min_live_nodes` 8.
  - After collection: `max_parse_failure_rate` 0.2 and `collection_gates`.
  - Not waived. This needs an S2-C2 fix (precondition 2c).
- **Job layout** (S2-C4, measured at context 16,384).
  - One job is one (node, memory mode) chunk of root campaigns: **16 jobs**.
  - `request_gpus 1`, `request_cpus 16`, workers 16; `request_memory 32,000` MB (peak about 10.9 GB);
    `request_disk 42,439,718` kB (peak 30,314,084 kB × 1.4); `+RequestWalltime 10,776` s.
  - `footprint_mib` = model buffer 18,675.55 + KV buffer `<re-measured at 32,768; 680.0 MiB at 16,384>`.
  - The GGUF is fetched once per chunk: 16 × 19.6 GB ≈ 314 GB of HF egress (disclosed; an image-side model cache is a
    later author decision).
  - Resumable only by the collector's A.5 resume and the wrapper's resume pin check. No ad-hoc retries.
- **Provisional estimate** (S2-C4, at 16,384).
  - Pilot wall at most 921 s for 2 instances, so a full chunk of 18 instances is estimated at 8,289 s.
  - 16 chunks come to **36.84 GPU-h**. With all 16 jobs running at once the wall is about one chunk plus queue wait
    (16 s in the pilot); serial worst case about 36.8 h.
  - `<re-check at 32,768 in S2-C3>`.
  - **STOP for the author** if a projection of this kind exceeds **60 GPU-h** or **48 h wall** (R1-SWEEP2-SETTINGS (5),
    replacing (h)'s "4 days on one 4090").

## Preconditions before launch

1. **S2-M2 integration on `main`.** Done: `9ae6d877`.
2. **S2-C2 fix units**, each accepted by independent review and integrated to `main` (with S2-C5):
   - a. the exam's server arguments at 32,768 (above), replacing the validator's 16,384 / `-ngl 99`;
   - b. the noise-source binding (`--e1-summary` and `noise_source`);
   - c. the restored liveness and collection gates;
   - d. the CPU-model requirement.
3. **The (g)4 liveness unit** (R1-SWEEP2-SETTINGS (4)). D28 liveness of the pick on all eight nodes on NEMO2 L40S, with
   prompt lengths re-measured with the pick's tokenizer. Passed: `<report, review>`.
4. **S2-C3 L40S deployment check** at the settings above (32,768), passed: `<report, review>`.
5. **S2-C5 real-submission switch** accepted. It includes the seal step comparing image digest and host with the
   values authorized here: `<review>`.
6. **R1-MAIN-PROPOSER (g)2** (R1-SWEEP2-SETTINGS (3)). No exception for now. The order is e1 environment replay
   (R1-E1-AUTH), then the author's e2, then sweep-1 B.2 on one pinned HTCondor CPU class, in parallel with the sweep-2
   preparation. An exception is discussed only if this becomes sweep 2's only blocker. Status at launch:
   `<sweep-1 B.2 complete | exception row>`.
7. **Projection** within 60 GPU-h and 48 h wall (above).
8. **Harness-defaults check** (R1-MAIN-PROPOSER (c)): `<report>`.

## Sealing and the analysis lock (R1-BX-D8)

- Job outputs come back to the submit host by HTCondor transfer (`out.tar`, `work.tar`, `job_record.json`,
  `SHA256SUMS`, `llama-server.log`). The seal step (`sweep2/s2_c2_lib.py seal`) copies them into
  `/ceph/srv/dwong/paperb/sweep2/<run_id>/<chunk_id>/`.
  - It refuses `..`, symlinks and overwrites, and writes `SHA256SUMS` and `SEAL_RECEIPT.json`.
  - It compares the image digest and host with this note (precondition 5).
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
- the CPU host of the in-campaign worker runs;
- context 8,192 against 32,768;
- default KV cache against q8_0;
- `--jinja` and the thinking flag;
- `cache_prompt` at the default against an explicit false;
- the harness pin `6adf385` against `a3fedbb`;
- the paper commit;
- the image;
- the C3 premises that differ by proposer (X.7(c) appendix, `mac-s2-m5-x7c-20261116`): the duplicate / no-op skip
  bound and the B1 μ̂ ordering, as in the cross-proposer disclosure paragraph.

**From the selection exam** (B1/B2 on TASL-7):
- GPU 4090 against L40S;
- a direct server against an HTCondor container with the frozen image;
- the llama-server binary: the same llama.cpp commit `620d222`, but the exam binary `b70f4882…` ("build 1") against
  the image's `f8d35fd3…` ("build 11669");
- the non-numeric server arguments listed above;
- instances and audit seeds: exam 9001+/9101+/9201+ against the sweep-1 instance seeds;
- paper commit `37282ec3…` against the launch commit;
- harness: identical (`a3fedbb`).

## Boundaries and STOPs

**Scope.** This authorization covers the sweep-2 label collection (B.1b) only. It does not cover:
- B.2 audits: sweep-2 B.2 is authorized later by an addendum (R1-SWEEP2-SETTINGS (2)), and R1-B2-DECOUPLE and
  R1-B2-REPLAY-GO stand;
- sweep-1 B.2;
- T1 sweeps;
- other GPU models or CPU classes;
- a second image digest;
- changing nodes, instances or settings after launch.

**Checks before launch.** Check all pins and this note's sha256 against the job specs.

**STOP conditions.** These are runbook §4, the S2-C2 STOPs and R1-MAIN-PROPOSER's STOPs:
- a required PLAN row, precondition or authorization missing or different;
- a job on a GPU other than L40S, or on a CPU other than the pinned model;
- a GGUF SHA-256 mismatch;
- server arguments or `cache_prompt` differing from the values above;
- an image identity mismatch;
- a resume pin mismatch;
- incomplete offload or OOM;
- a liveness or collection gate failing;
- a label string not matching this note;
- a projection above 60 GPU-h or 48 h wall;
- any code path reading sweep-2 labels before R1-BX-D8-CONFIRM;
- pushing `main` without the author's explicit instruction.

Preserve completed outputs and every attempt (never delete, never overwrite), and report any STOP.

---

## Notes for the author (not part of the note)

1. **Values measured at 16,384.** The S2-C4 values were measured at context 16,384:
   - the KV buffer was 680.0 MiB;
   - the wall per chunk was estimated at 8,289 s;
   - the total at 36.84 GPU-h.

   At 32,768 the KV buffer grows, roughly doubling for q8_0. The per-request time may change with longer contexts.
   S2-C3 or a short re-pilot at 32,768 should confirm the footprint and the estimate before they are written into the
   note.
2. **Placeholders and the unit that fills each one.**
   - S2-C1: image digest approval.
   - S2-C2 fix units 2a–2d: non-numeric argument list; CPU requirement.
   - (g)4 unit: liveness report.
   - S2-C3: deployment check and the 32,768 re-measurement.
   - S2-C5: seal check and run id.
   - The author: the launch commit, (g)2 status and the harness-defaults check.
3. **What changed from the first draft.**
   - Context 32,768 with the exam's arguments, replacing 16,384 / `-ngl 99`.
   - The B.2 audits are removed, together with the audit CPU image.
   - The projection STOP is set at 60 GPU-h / 48 h wall.
   - The (g)4 unit and the restored gates are preconditions.
   - (g)2 follows R1-SWEEP2-SETTINGS (3).
   - The S2-C4 values are filled: CPU model, layout, memory, disk, walltime, model buffer, build line, estimate.
   - The harness pin is now on `main`.
