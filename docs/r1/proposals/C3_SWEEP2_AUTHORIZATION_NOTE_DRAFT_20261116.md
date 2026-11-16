# Draft authorization note: C3 sweep 2 and its B.2 audits (HTCondor, NEMO2 L40S)

**This is a draft, not an authorization.** The Mac agent (Claude, AI-assisted) prepared it as unit S2-M1 of the
sweep-2 work plan (`prompts/SWEEP2_HTCONDOR_RUNBOOK_20261116.md`, `docs/runbooks-16nov` @ `a2789ea6`). The work plan
itself is not a decision.

**How the author uses it:**
- Copy the block between the two rules below to `docs/r1/authorizations/c3_sweep2_<date>.md` on `main`.
- Fill every `<…>` placeholder, and add your own prose to the opening paragraph.
- Set `approved: true` yourself. This draft keeps `approved: false`, and the agent never sets it.

The format follows `authorizations/c3_sweep1_20261027.md`: an opening paragraph, "Proposed scope and pins",
"Boundaries and STOPs". A short key block is added because the accepted S2-C2 job wrapper reads three things from the
note it is given (`sweep2/s2_c2_lib.py`, `resolve_label`):
- a line `approved: true`;
- the run id;
- `label: EVIDENCE`.

It refuses the note otherwise, and it also refuses a note whose sha256 differs from the job spec's.

**Authority read from** `author-sweephost-20261116` @ `fd275c53`. The rows used are:
- R1-SWEEP-HOST-HTC;
- R1-EXAM-X7;
- R1-MAIN-PROPOSER (b), (c), (e), (g);
- R1-SWEEP1-CLASSIFY and R1-B2-DECOUPLE;
- R1-BX-D8 and R1-BX-PROPOSED-CONFIRM;
- R1-CACHEPROMPT-FALSE, R1-EXAM-CACHE-REV and R1-EXAM-B1-HARNESS-PIN;
- R1-B1-CORPUS-FREEZE.

Each value below cites its source.

---

# Authorization: C3 sweep 2 and its fresh-seed audits (HTCondor)

<Author's opening paragraph: date and time, the instruction, and what was read. Proposed facts to cite:
- the accepted S2-M2 integration was pushed to `main` at `<main commit>` (this is `paper.evidence_ready`);
- the S2-C3 L40S deployment check passed (`<report, review>`);
- the S2-C4 timing pilot gave the job layout and the estimate (`<report, review>`);
- the S2-C5 real-submission switch was accepted (`<review>`);
- the S2-C1 image digest is approved.
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
    constants), and `cpu_model_contains = <CPU model string measured by S2-C4>`.
  - One GPU model and one CPU class for the whole sweep-2 table. A job that lands elsewhere is a STOP.
  - Selection ran on a 4090 (B1/B2 on TASL-7) and deployment runs on the L40S. This is disclosed, and it is why the
    S2-C3 deployment check must pass first.
- **Paper commit.** `main` HEAD at launch, which must contain the accepted S2-M2 integration (`<main commit>`). It is
  recorded in every job record.
- **Harness.** `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` (`cacheprompt-20261031`, the B2 stack): an explicit
  `cache_prompt: false` on every request. `r1/scripts/HARNESS_PIN_C3` on that commit carries the same value.
- **Image (S2-C1).**
  - GPU: `<ghcr.io/dowlingwong/r1-htc-gpu@sha256:… — proposed v1: 69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296>`.
  - Identity markers: `build_utc` `<2026-11-14T23:10:24Z>`, `llama_server_sha256` `<f8d35fd33e866808bc76457cf52cf1f8b1baafde9c2c8eebae51abf428843cc0>`.
  - CPU image for the audits: `<proposed v1: ghcr.io/dowlingwong/r1-htc-cpu@sha256:221ca459d62723ec58219c37c71e1664846b135ff919ec59cf37ce57158f75aa>`.
  - One digest per table. No switch during the sweep.
- **llama.cpp.** Commit `620d2225cc436ab0b001e3200e590e3b286ef9ab` (in the image). The expected build line is
  `version: 0.7.0-dev (build 11669, commit 620d2225c)`.
- **Manager: the pick `gemma4_31b`, thinking off** (R1-EXAM-X7, R1-MAIN-PROPOSER).
  - GGUF: `bartowski/google_gemma-4-31B-it-GGUF` @ `619aca7589c72be65dd968de8602ad23d68b5c14`, file
    `google_gemma-4-31B-it-Q4_K_M.gguf`, size 19,598,489,952 B, SHA-256
    `2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75`.
  - Registry doc `reports/exam_phase2_20261026/gemma4_31b.json`, SHA-256
    `a04a0346ca887c27998b5f46f4e3d67fa05126ff3af9e0c20fe78d030c1fdc61`.
  - The job checks the GGUF SHA-256 after fetching it.
- **Server flags (exactly as in the exam).**
  - `--jinja`, `--chat-template-kwargs {"enable_thinking": false}`, `--cache-type-k q8_0`, `--cache-type-v q8_0`;
  - context 16,384, full offload (`-ngl 99`), one owned `llama-server` per job, `--no-webui`;
  - temperature 0.2 with the D26 seed (`manager_seed(campaign_id, budget_index, repetition, revision_attempt)`);
  - `cache_prompt: false` on every call; `LLAMACPP_CACHE_PROMPT` and `LLAMACACHE_PROMPT` unset.
- **Design: the same as sweep 1** (R1-MAIN-PROPOSER (b); config `r1/scripts/configs/c3_sweep_deepthought.json`,
  SHA-256 `2fa891f43bf26e6ed2ac6c794696428a43568a69a850d6029e3bc8233616974b`, for the design values only).
  - The eight nodes: `digits_mlp`, `tabular_mlp`, `openml_breast_w`, `openml_ionosphere`, `openml_wdbc`,
    `openml_credit_approval`, `openml_sonar`, `openml_climate`.
  - Per node: 18 instances × memory modes `{append_only_summary, none}` × W = 20; `vary` split; structure-only
    `manager_proposal/v1`; transport attempts 3. No node changes after launch.
  - Instance seeds are the sweep-1 seeds: `100 + 10k + (Σ ord(node) mod 7)` for k = 0…17
    (`r1.headroom.e1b_collect._instance_seed`). They are also the in-campaign `train_seed` / `split_seed`.
- **Noise source.** `results/r1/noise/D28_REPAIR_20261027/summary.json`, SHA-256
  `3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310`, as in sweep 1.
- **Job layout (S2-C2/S2-C4).**
  - One job = one (node, memory mode) chunk of root campaigns, or `<smaller chunks per S2-C4>`. That is
    `<16 or more>` jobs.
  - `request_gpus 1`, `request_cpus 16`, workers 16, `request_memory <MB, measured>`, `request_disk <kB, measured>`,
    walltime `<s>`.
  - `footprint_mib` = `<L40S model + KV buffers, measured by S2-C4>`.
  - Resumable only by the collector's A.5 resume and the wrapper's resume pin check. No ad-hoc retries.
- **B.2 audits** (R1-SWEEP1-CLASSIFY, R1-B2-DECOUPLE).
  - K = 10: seeds 7001–7005 for labels and 7006–7010 for evaluation. The seed blocks are never mixed, and 7006–7010
    are never used for C3 or Track P training, tuning or selection.
  - Duplicates get no label; no-ops are labelled by rule.
  - The audits run as CPU-only HTCondor jobs on one pinned CPU class, `<class from condor_status>`, in the CPU image
    above.
- **Provisional estimate.** `<from S2-C4: label jobs N × wall h, queue wait, audits h>`. A projected total above
  `<author's threshold>` is a STOP for the author.

## Sealing and the analysis lock (R1-BX-D8)

- Job outputs come back to the submit host by HTCondor transfer. The reviewed seal step (`sweep2/s2_c2_lib.py seal`)
  copies them into `/ceph/srv/dwong/paperb/sweep2/<run_id>/<chunk_id>/`. It verifies run, chunk, label, image and
  host, refuses `..`, symlinks and overwrites, and writes `SHA256SUMS` and `SEAL_RECEIPT.json`.
- No sweep-2 label table is copied back for analysis, or read by any analysis code, before the author row
  **R1-BX-D8-CONFIRM** exists. Until then the readers refuse sealed paths, and run reports give counts only.

## Disclosed differences from sweep 1 (cross-proposer tables)

R1-MAIN-PROPOSER (c), with the host updated by R1-SWEEP-HOST-HTC. Every cross-proposer table lists these:
- the manager;
- the host: deepthought TITAN X (sm_52) against NEMO2 L40S (sm_89), and HTCondor container jobs;
- the CPU host of the in-campaign worker runs;
- context 8,192 against 16,384;
- default KV cache against q8_0;
- `--jinja` and the thinking flag;
- `cache_prompt` at the default against an explicit false;
- the harness pin `6adf385` against `a3fedbb`;
- the paper commit;
- the image.

## Boundaries and STOPs

**Scope.** This authorization covers sweep 2 (B.1b) and its B.2 audits only. It does not cover:
- sweep-1 B.2;
- T1 sweeps;
- other GPU models or CPU classes;
- a second image digest;
- changing nodes, instances or settings after launch.

**Checks before launch.** Check all pins and this note's sha256 against the job specs.

**STOP conditions.** These are runbook §4, the S2-C2 STOPs and R1-MAIN-PROPOSER's STOPs:
- a required PLAN row or authorization missing or different;
- a job on a GPU other than L40S, or on a CPU outside the pinned class;
- a GGUF SHA-256 mismatch;
- server flags or `cache_prompt` differing from the values above;
- an image identity mismatch;
- a resume pin mismatch;
- incomplete offload or OOM;
- a label string not matching this note;
- any code path reading sweep-2 labels before R1-BX-D8-CONFIRM;
- pushing `main` without the author's explicit instruction.

Preserve completed outputs and every attempt (never delete, never overwrite), and report any STOP.

---

## Notes for the author (not part of the note)

**1. Preconditions that are not in the runbook's P1–P7 list.** All three come from PLAN rows.
- **R1-MAIN-PROPOSER (g)2:** sweep-1 B.2 complete before the next harness pin (R1-HARNESS-NEXT-PIN), or an explicit
  author exception. The runbook (S2-C7) says sweep-1 B.2 may not have run. Sweep 2 uses the next pin `a3fedbb`, so
  this needs either sweep-1 B.2 first or an exception row.
- **R1-MAIN-PROPOSER (g)4:** D28 liveness of the pick on all eight nodes, which also re-measures prompt lengths with
  the pick's tokenizer. S2-C3 replays only the three B2 exam nodes. Sweep 1's runner applied the liveness and
  parse-failure gates (`min_live_nodes` 8, `max_parse_failure_rate` 0.2) before collection. The S2-C2 wrapper calls
  the collector directly and does not apply them. Either S2-C3 or a separate unit should cover the eight nodes, or
  the author waives this explicitly.
- **R1-MAIN-PROPOSER (f) and (h):** the proposed 4-day STOP on the projection was written for one 4090. Under
  HTCondor the author should set the threshold for the S2-C4 estimate.

**2. Placeholders and the unit that fills each one.**
- S2-C1: image digest.
- S2-C4: CPU class string, job layout, memory and disk, walltime, footprint, estimate.
- S2-C5 and the author: run id.
- S2-M2 push by the author: main commit.
- Author: threshold.

**3. Not decided here.**
- Whether the B.2 audits use the M3 audit code (`r1/c3/audit.py`, EVIDENCE path) inside HTCondor CPU jobs. A job
  wrapper for audits does not exist yet; it is S2-C7.
- Whether sweep-1 B.2 runs on the same CPU class for comparability (runbook S2-C7: the author decides).
