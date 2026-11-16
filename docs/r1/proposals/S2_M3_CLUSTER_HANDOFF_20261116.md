# Sweep-2 hand-off for the cluster agent (S2-M3, 16 November 2026)

**AI-assisted (Claude, Mac agent).** This is a hand-off draft in the B2 hand-off style (`B2_HANDOFF_EXEC_20261115.md`).
It is not an author decision and not an authorization.

- **Authority.** `author-decisions-20261116` @ `4da73306` (R1-SWEEP2-SETTINGS, R1-SWEEP-HOST-HTC, R1-BX-D8-V3-A,
  R1-E1-AUTH). It descends from `main` @ `9ae6d877`.
- **Work plan.** `prompts/SWEEP2_HTCONDOR_RUNBOOK_20261116.md` §2 S2-M3 and §3 S2-C5/S2-C6.
- **Measured inputs.** `sweep2-cluster-20261116` @ `acae9fde` (S2-C2 wrapper; S2-C4 results).

**Nothing here may be launched until all of these hold:**
- the author's authorization note `authorizations/c3_sweep2_<date>.md` exists with `approved: true` (draft: S2-M1
  redraft, `mac-s2-m1-redraft-20261116`);
- every gating item in §0 is accepted;
- the author has given the instruction to launch.

The values below follow the S2-M1 redraft. Where the two differ, the authorization note wins.

## 0. Inputs and gating items

| Item | Status (16 Nov 10:40) | Needed for |
|---|---|---|
| S2-M2 integration on `main` | done, `9ae6d877` | paper commit |
| S2-C1 image v1 `…r1-htc-gpu@sha256:69b06b35…` | proposed; used by S2-C4; author freezes it in the note (P7) | spec `image` |
| S2-C2 wrapper | accepted (ENGINEERING); hotfixes during S2-C4 up to `c8d07994`, plus disclosure fix `acae9fde` | everything |
| S2-C4 timing pilot | done (16 Nov 03:46): 16 chunks, about 8,289 s each, about 36.84 GPU-h, at context 16,384 | layout, estimate |
| **Fix A, server at the exam's settings** (R1-SWEEP2-SETTINGS (1)) | `<accepted fix unit>` | spec `server` |
| **Fix B, noise-source binding** (`--e1-summary`, `noise_source`) | `<accepted fix unit>` | spec `collector` |
| **Fix C, restored sweep-1 gates** (R1-SWEEP2-SETTINGS (4)) | `<accepted fix unit>` | wrapper |
| **Fix D, CPU-model requirement** (R1-SWEEP-HOST-HTC) | `<accepted fix unit>` | spec `requirements` |
| (g)4 liveness unit: pick on 8 nodes on NEMO2 L40S, prompt lengths with the pick's tokenizer | `<report, review>` | precondition |
| S2-C3 L40S deployment check, at 32,768 | `<report, review>` | precondition (P4) |
| S2-C5 real-submission switch: only the authorized run id and digest; the seal compares digest and host with the note | `<review>` | P6 |
| The fix units, the switch and the wrapper integrated to `main` | `<launch commit>` | spec `paper.commit`, `evidence_ready: true` |
| R1-MAIN-PROPOSER (g)2 (R1-SWEEP2-SETTINGS (3)) | sweep-1 B.2 after e1 → e2, or an author exception row | precondition |
| Harness-defaults check (R1-MAIN-PROPOSER (c)) | `<report>` | precondition |

**Fixes A–D are the wrapper changes** that the S2-M1 review found and R1-SWEEP2-SETTINGS decided:
- **Fix A** sets the exam's server arguments (32,768).
- **Fixes B, C and D** are the three wrapper fixes.

When each is accepted, its commit replaces the placeholder here. The spec template in §2 is written for the behaviour
each fix must have; it should not be used until the fixes exist.

## 1. What the author commits first

1. `docs/r1/authorizations/c3_sweep2_<date>.md` on `main`, from the S2-M1 redraft, with `approved: true`,
   `label: EVIDENCE` and the run id, for example `s2ev-<YYYYMMDD>-a`.
2. Its sha256 goes into every chunk spec (`label_source.authorization`). The wrapper refuses a note whose sha256
   differs.
3. The launch commit: `main` HEAD carrying §0's integrations. Every spec pins it, with `paper.evidence_ready: true`.

## 2. The chunk spec (template; one per chunk)

The schema is `s2_c2_job/v1` (`sweep2/spec.example.json`). Fields that the fix units change are marked `[fix X]`.

```json
{
 "schema": "s2_c2_job/v1",
 "run_id": "<run id from the note>",
 "chunk_id": "<node>-<memory_mode>",
 "image": {"digest": "ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296",
           "versions_markers": {"image": "r1-htc-gpu", "build_utc": "2026-11-14T23:10:24Z",
                                "llama_server_sha256": "f8d35fd33e866808bc76457cf52cf1f8b1baafde9c2c8eebae51abf428843cc0",
                                "llama_cpp_commit": "620d2225cc436ab0b001e3200e590e3b286ef9ab"},
           "llama_server_sha256": "f8d35fd33e866808bc76457cf52cf1f8b1baafde9c2c8eebae51abf428843cc0"},
 "paper": {"repo": "https://github.com/dowlingwong/Agent_paper_B.git", "commit": "<launch commit>", "evidence_ready": true},
 "harness": {"repo": "https://github.com/dowlingwong/autoresearch_harness.git",
             "commit": "a3fedbbd44309b3fdf99d853ad841b9ec2c299e2", "exception_reason": ""},
 "model": {"url": "https://huggingface.co/bartowski/google_gemma-4-31B-it-GGUF/resolve/619aca7589c72be65dd968de8602ad23d68b5c14/google_gemma-4-31B-it-Q4_K_M.gguf",
           "sha256": "2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75", "size": 19598489952,
           "alias": "gemma4_31b",
           "provenance": {"registry_doc": "docs/r1/reports/exam_phase2_20261026/gemma4_31b.json",
                          "registry_sha256": "a04a0346ca887c27998b5f46f4e3d67fa05126ff3af9e0c20fe78d030c1fdc61",
                          "revision": "619aca7589c72be65dd968de8602ad23d68b5c14",
                          "file": "google_gemma-4-31B-it-Q4_K_M.gguf", "source_label": "bartowski imatrix Q4_K_M"}},
 "server": {"binary": "/opt/r1/llama/bin/llama-server", "ctx": 32768, "n_gpu_layers": 999, "port": 18110,
            "expected_build": "0.7.0-dev (build 11669, commit 620d2225c)",
            "extra_args": ["-np", "1", "--jinja", "--cache-type-k", "q8_0", "--cache-type-v", "q8_0",
                           "--chat-template-kwargs", "{\"enable_thinking\":false}"]},
 "collector": {"node": "<node>", "memory_mode": "<append_only_summary | none>", "instances": 18, "runs": 20,
               "workers": 16, "transport_max_attempts": 3, "proposal_schema": "manager_proposal/v1",
               "verify_split_policy": "vary",
               "e1_summary": "results/r1/noise/D28_REPAIR_20261027/summary.json",
               "e1_summary_sha256": "3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310"},
 "requirements": {"cloud_site": "BwForCluster-Nemo2", "gpu_device_name": "NVIDIA L40S",
                  "machine_regex": "^g36[0-9]{2}\\.nemo\\.privat$", "min_cpus": 16,
                  "cpu_model_contains": "INTEL(R) XEON(R) PLATINUM 8562Y+"},
 "label_source": {"authorization": {"path": "docs/r1/authorizations/c3_sweep2_<date>.md", "sha256": "<note sha256>"}},
 "walltime_s": 10776
}
```

Notes on the template:
- **`server` [fix A].** The accepted validator requires `ctx` 16384, `n_gpu_layers` 99 and `--no-webui`; fix A must
  accept the exam's values. The exam launcher put `-np 1` in the fixed argv and the thinking switch as compact JSON
  (`llama_server_instance.thinking_args`). Fix A decides where `-np 1` goes. Whether `--no-webui` and the log level
  stay is disclosed in the note (R1-SWEEP2-SETTINGS (1)).
- **`collector.e1_summary` [fix B].** These are new fields. The wrapper must pass `--e1-summary` to `e1b_collect` and
  check the sha256. The collector then records `noise_source` in each campaign manifest.
- **Liveness and collection gates [fix C].** They are not spec fields. The wrapper must:
  - refuse to start collection unless liveness holds (`min_live_nodes` 8, from the (g)4 unit);
  - apply `max_parse_failure_rate` 0.2 and `collection_gates` after collection, as `c3_label_sweep.py` did for sweep
    1;
  - make a failing gate a STOP that is recorded in the job record.
- **`requirements.cpu_model_contains` [fix D].** The model string measured on both S2-C4 hosts. Fix D must put it
  into the HTCondor requirements, or the author accepts the in-job check (`cpu_identity`) as sufficient.
- **`walltime_s`** is 10,776 s, as S2-C4 proposed.
  - `render_jdl.py` currently writes `request_memory = 128000` and `request_disk = 50000000`. S2-C4 proposed 32,000 MB
    and 42,439,718 kB.
  - The larger fixed values are safe. Whether to lower them is the cluster's call in fix A–D or S2-C5; both values go
    in the report.
  - All S2-C4 values were measured at context 16,384. At 32,768 the KV buffer (680.0 MiB at 16,384) grows, and S2-C3
    or a re-pilot should confirm walltime and memory before launch.

## 3. Job layout (S2-C4)

**16 chunks.** One per (node, memory mode) pair: 8 nodes × 2 modes, 18 instances × W = 20 each.

| # | chunk_id | # | chunk_id |
|---|---|---|---|
| 1 | `digits_mlp-append_only_summary` | 2 | `digits_mlp-none` |
| 3 | `tabular_mlp-append_only_summary` | 4 | `tabular_mlp-none` |
| 5 | `openml_breast_w-append_only_summary` | 6 | `openml_breast_w-none` |
| 7 | `openml_ionosphere-append_only_summary` | 8 | `openml_ionosphere-none` |
| 9 | `openml_wdbc-append_only_summary` | 10 | `openml_wdbc-none` |
| 11 | `openml_credit_approval-append_only_summary` | 12 | `openml_credit_approval-none` |
| 13 | `openml_sonar-append_only_summary` | 14 | `openml_sonar-none` |
| 15 | `openml_climate-append_only_summary` | 16 | `openml_climate-none` |

**Resources per job.** 1 L40S GPU, 16 CPUs and 16 workers, with requests as in §2.

**Estimate** (at 16,384). About 8,289 s per chunk and 36.84 GPU-h in total. If all 16 run at once, the wall is about
one chunk plus queue wait. Re-check this at 32,768.

**Projection STOP for the author.** Above 60 GPU-h or above 48 h wall (R1-SWEEP2-SETTINGS (5)).

## 4. Prechecks on the submit host (before any EVIDENCE submission)

1. **Authority.** PLAN rows R1-SWEEP-HOST-HTC and R1-SWEEP2-SETTINGS are present on the launch commit. The
   authorization note exists there, with `approved: true`, `label: EVIDENCE` and the run id, and its sha256 equals the
   specs'.
2. **Specs.** All 16 specs validate with the accepted wrapper (`validate_spec`):
   - identical except for `chunk_id`, `collector.node` and `collector.memory_mode`;
   - every pin equal to the note: image digest, harness, model, server, noise source, CPU model, run id.
3. **Rendered JDLs.** Render with `render_jdl.py <spec> --out <jdl> --stage-dir <stage> --auth-note <note>`, then
   run `condor_submit -dry-run` for each. Check that the requirements match the L40S / NEMO2 / machine / CPU pins and
   that nothing requires `ProvidesEtpCeph`.
4. **Sealed root.** `/ceph/srv/dwong/paperb/sweep2/<run_id>/` must not exist yet; the seal refuses overwrites.
5. **Real-submission switch** (S2-C5). It must refuse any other run id or digest. Show this with one refused dry
   attempt.
6. **Free space** on the submit host for 16 transferred outputs: at the S2-C4 peak of about 30 GB per chunk, that is
   about 485 GB. Plan the transfer and seal batch by batch if space is short.

## 5. Submission order (proposal, for the author to confirm)

1. **Canary.** Submit chunks 1 and 2 (`digits_mlp`, both modes). Within the first minutes, check each job record:
   - GPU L40S, the pinned CPU model, image identity;
   - GGUF sha256 verified;
   - `server.build` equal to the expected line;
   - offload 61/61;
   - liveness passed (fix C);
   - label EVIDENCE from the note.
2. **The remaining 14** follow only if all canary checks pass. Submit them together, unless walltime or projection
   checks say otherwise.
3. **Projection check.** Recompute the projection from the canary's progress: completed campaigns per hour against
   18 × 20 runs. If it exceeds 60 GPU-h or 48 h wall, STOP before submitting the rest and report to the author.

## 6. Monitoring

- Poll at least every 30 minutes: `condor_q -nobatch`, the hold reasons, `condor_history` for finished jobs, and each
  chunk's transferred `job_record.json` once it is back.
- Never edit a running job. Never resubmit ad hoc.
- **The only retry is a resume.** Resubmit the same spec unchanged. The wrapper's resume pin check and the
  collector's A.5 resume take over from the preserved `out/`.
- Each resume is recorded in the report.
- A held or failed job is preserved; its STOP reason is recorded.

## 7. Copy-back and sealing

- For each finished chunk: `python3 -m sweep2.s2_c2_lib seal <job-output> --run-id <run_id> --chunk-id <chunk_id>`.
- Then verify with `sha256sum -c SHA256SUMS` in the sealed directory, and keep `SEAL_RECEIPT.json`. After S2-C5 the
  seal also compares the digest and host with the note.
- Sealed layout: `/ceph/srv/dwong/paperb/sweep2/<run_id>/<chunk_id>/{out/, work/, job_record.json, llama-server.log,
  SHA256SUMS, SEAL_RECEIPT.json}`.
- Nothing is deleted or overwritten. Failed attempts stay in their own directories.
- **No label is read.** No table is built or copied for analysis before **R1-BX-D8-CONFIRM** (R1-BX-D8; the
  V3-A lock stands). The lock in code is `analysis_guard.guard_table` / `require_d8_confirmation`; the sealed path
  itself is not refused by `refuse_sealed`.
- A sweep index lists, per chunk: run id, chunk id, sealed path, receipt sha256, label and status. It gives counts
  only.

## 8. STOP list (stop, preserve, report; no retry except §6's resume)

- A required PLAN row, precondition (§0) or authorization missing or different; note sha256 ≠ spec.
- A job on a GPU other than L40S, on a machine outside the regex, or on a CPU other than the pinned model.
- GGUF sha256 or size mismatch; image identity mismatch; `server.build` mismatch; offload below 61/61; OOM.
- Server arguments, context or `cache_prompt` differing from the note; `LLAMACPP_CACHE_PROMPT` or
  `LLAMACACHE_PROMPT` set.
- Liveness below 8 live nodes, parse-failure rate above 0.2, or a failing collection gate (fix C).
- Noise source missing or with a different sha256 (fix B).
- Resume pin mismatch; label string not equal to the note's.
- Projection above 60 GPU-h or 48 h wall.
- Any code path reading sweep-2 labels before R1-BX-D8-CONFIRM.
- Any push to `main` without the author's instruction.

## 9. Report template (counts only; no label, metric or score)

```
# Sweep-2 EVIDENCE run <run_id> — run report (counts only)
authorization: docs/r1/authorizations/c3_sweep2_<date>.md  sha256 <…>   launch commit <…>   image <digest>
per chunk: chunk_id | cluster id | host | GPU | CPU model | queue wait s | wall s | GGUF fetch s | offload |
           model/KV buffer MiB | resumes | rc | root campaigns completed (of 18) | liveness pass | collection gates pass |
           sealed path | SEAL_RECEIPT sha256
totals: chunks complete <n>/16 · GPU-h <…> · wall h <…> · resumes <…> · STOPs <list or none>
statement: no label, metric or table was read; sealed outputs untouched since sealing
```

## 10. What to send back

- the report;
- the sweep index;
- every job record and seal receipt, copied into the repo as in `s2c4_run_20261116/`;
- the rendered JDLs and dry-run outputs;
- the canary checks.

All of it goes on a cluster branch, for independent review.
