# Sweep-2 hand-off for the cluster agent (S2-M3, 16 November 2026)

**AI-assisted (Claude, Mac agent).** This is a hand-off draft in the B2 hand-off style (`B2_HANDOFF_EXEC_20261115.md`).
It is not an author decision and not an authorization.

- **Authority.** `author-decisions-20261116` @ `4da73306` (R1-SWEEP2-SETTINGS, R1-SWEEP-HOST-HTC, R1-BX-D8-V3-A,
  R1-E1-AUTH). It descends from `main` @ `9ae6d877`.
- **Work plan.** `prompts/SWEEP2_HTCONDOR_RUNBOOK_20261116.md` §2 S2-M3 and §3 S2-C5/S2-C6.
- **Measured inputs.** `sweep2-cluster-20261116` @ `acae9fde` (S2-C2 wrapper; S2-C4 results).

**Nothing here may be launched until all of these hold (and nothing here may be pasted as-is: the template needs fixes A–G):**
- the author's authorization note `authorizations/c3_sweep2_<date>.md` exists with `approved: true` (draft: S2-M1
  redraft, `mac-s2-m1-redraft-20261116`);
- every gating item in §0 is accepted;
- the author has given the instruction to launch.

The values below follow the S2-M1 redraft (`mac-s2-m1-redraft-20261116` @ `11db0f65`, review record `e43faa29`).
Where the two differ, the authorization note wins.

## 0. Inputs and gating items

| Item | Status (16 Nov 10:40) | Needed for |
|---|---|---|
| S2-M2 integration on `main` | done, `9ae6d877` | paper commit |
| S2-C1 image v1 `…r1-htc-gpu@sha256:69b06b35…` | proposed; used by S2-C4; author freezes it in the note (P7) | spec `image` |
| S2-C2 wrapper | accepted for ENGINEERING at `70e3a116` / `235c9e5f`. The six S2-C4 hotfixes (`f4a85da1` … `c8d07994`) and the disclosure change `acae9fde` are **not yet reviewed** | everything |
| S2-C4 timing pilot | ran (16 Nov 03:46): 16 chunks, about 8,289 s each, about 36.84 GPU-h, at 16,384. **Provisional, results not yet reviewed:** in both job records every visible in-campaign worker run (`python3 train.py`) ended in ≤ 0.1 s with `success=False metrics={}` | layout, estimate |
| **Fix E, worker environment** | `<accepted fix unit>`. Put the harness env on `PATH` and restore sweep 1's `package_environment` / `evidence_node_commands` checks; a failing or mismatched worker environment is a STOP | wrapper |
| **Fix F, label-dependent record text** | `<accepted fix unit>`. Job records and manifests must stop writing `output_use: ENGINEERING…`, `audit: none (ENGINEERING run …)` and `ctx: 16384` regardless of the label and settings (overlaps S2-M1 precondition 2e). Fix C or F should also write into the record the counts that the redacted projection needs: worker runs ok/failed, LLM calls, parse failures. The projection should be a field allowlist, so no sealed ledger has to be read | wrapper |
| **Fix G, requests** | `<accepted fix unit>`. `render_jdl.py` writes the note's requests, not the fixed 128000 / 50000000 (S2-M1 precondition 2e) | JDL |
| Re-measurement at the sweep-2 settings (S2-C3 or a re-pilot): 32,768, `-np 1`, a full 18-instance chunk, worker runs succeeding | `<report, review>` | layout, requests, estimate |
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

**Fixes E–G** come from this hand-off's review (failed pilot worker runs, ENGINEERING text in records, hard-coded
requests). A resume path does not exist in the wrapper (§6). If the author wants one, it is a further fix (H).

When each is accepted, its commit replaces the placeholder here. The spec template in §2 is written for the behaviour
each fix must have; it should not be used until the fixes exist.

## 1. What the author commits first

1. `docs/r1/authorizations/c3_sweep2_<date>.md` on `main`, from the S2-M1 redraft, with `approved: true`,
   `label: EVIDENCE` and the run id, for example `s2ev-<YYYYMMDD>-a`.
2. Its sha256 goes into every chunk spec as `label_source.authorization_sha256`. The note's bare file name goes in
   as `label_source.authorization`. The wrapper refuses a note whose sha256 differs.
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
 "server": {"binary": "/opt/r1/llama/bin/llama-server", "ctx": 32768, "n_gpu_layers": 999, "port": "<18110 + chunk number, i.e. 18111…18126>",
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
 "label_source": {"authorization": "c3_sweep2_<date>.md", "authorization_sha256": "<note sha256>"},
 "walltime_s": 10776
}
```

Notes on the template:
- **`server` [fix A].** The accepted validator enforces only `ctx == 16384`. `n_gpu_layers` 99 and `--no-webui` come
  from `spec.example.json`, not from the validator. Fix A must accept `ctx` 32,768; the template's other server values
  already pass. The exam launcher put `-np 1` in the fixed argv and the thinking switch as compact JSON
  (`llama_server_instance.thinking_args`). Fix A decides where `-np 1` goes. Whether `--no-webui` and the log level
  stay is disclosed in the note (R1-SWEEP2-SETTINGS (1)).
- **`collector.e1_summary` [fix B].** These are new fields. The wrapper must pass `--e1-summary` to `e1b_collect` and
  check the sha256. The collector then records `noise_source` in each campaign manifest.
- **`label_source`.** The schema is a bare file name plus `authorization_sha256` (`resolve_label`). The repo path goes
  to `render_jdl.py --auth-note docs/r1/authorizations/c3_sweep2_<date>.md`, which stages the note into the job.
- **`server.port`.** It differs per chunk, so that two chunks landing on one multi-GPU node cannot collide, unless the
  cluster shows that containers have separate network namespaces.
- **Liveness and collection gates [fix C].** They are not spec fields. The wrapper must:
  - refuse to start collection unless liveness holds (`min_live_nodes` 8, from the (g)4 unit);
  - apply `max_parse_failure_rate` 0.2 and `collection_gates` after collection, as `c3_label_sweep.py` did for sweep
    1;
  - make a failing gate a STOP that is recorded in the job record.
  - Each job sees one node, so fix C must say how `min_live_nodes` 8 is enforced per chunk: for example, the (g)4
    liveness report pinned by sha256 in the spec, plus this node's pass.
- **`requirements.cpu_model_contains` [fix D].** The model string measured on both S2-C4 hosts. Fix D must put it
  into the HTCondor requirements, or the author accepts the in-job check (`cpu_identity`) as sufficient.
- **Requests and walltime are the authorization note's values** (S2-M1: `request_memory`, `request_disk`,
  `+RequestWalltime`). `render_jdl.py` must write them (fix G); today it writes 128000 / 50000000.
  - The S2-C4 values (32,000 MB, 42,439,718 kB, 10,776 s) were measured with **2 instances**, at 16,384, with failing
    worker runs.
  - The disk peak includes the 19.6 GB GGUF and both `out/`/`work/` and their tars.
  - All three values must be re-derived from the full-chunk re-measurement (§0) before they go into the note.

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

**Estimate.** S2-C4 gives about 8,289 s per chunk and 36.84 GPU-h, but this is **provisional**. The pilot's worker
runs failed, so the timing probably contains little or no training. It must be replaced by the re-measurement (§0).

**Wall projection** = ⌈16 / (L40S slots available at once)⌉ × chunk wall + queue wait. The number of slots comes from
`condor_status` at launch.

**Projection STOP for the author.** Above 60 GPU-h (16 × chunk wall) or above 48 h wall (R1-SWEEP2-SETTINGS (5)).

## 4. Prechecks on the submit host (before any EVIDENCE submission)

1. **Authority.** On the launch commit:
   - the PLAN rows R1-SWEEP-HOST-HTC, R1-SWEEP2-SETTINGS, R1-BX-D8, R1-BX-D8-V3-A, R1-EXAM-X7 and R1-MAIN-PROPOSER are
     present;
   - the authorization note exists with `approved: true`, `label: EVIDENCE` and the run id;
   - its sha256 equals the specs' `label_source.authorization_sha256`.
2. **Provenance**, in the B2 hand-off style.
   - Render from a clean checkout at the launch commit (`git status --porcelain` empty).
   - The sha256 of the staged `s2_c2_job.sh` and `s2_c2_lib.py` must equal those files in the launch commit's
     `sweep2/`. Record the hashes in the report.
   - The launch commit carries the fix units and the switch, with an independent review at that exact HEAD. The
     reviewed base, the `Accepted commit:` line and the READY entry must agree.
3. **Specs.**
   - All 16 specs are identical except for `chunk_id`, `collector.node`, `collector.memory_mode` and `server.port`.
   - Every pin equals the note: image digest, harness, model, server, noise source, CPU model, run id.
   - Validation of an EVIDENCE spec happens inside `render_jdl.py`, which stages the note and changes into the stage
     directory. `s2_c2_lib validate` on its own cannot find the note.
4. **Rendered JDLs.**
   - Render with `render_jdl.py <spec> --out <jdl> --stage-dir <fresh stage> --auth-note <note path>`.
   - Then run `condor_submit -dry-run <dry-run output file> <jdl>` for each.
   - Check that the requirements match the L40S / NEMO2 / machine pins, plus the CPU pin if fix D puts it there; that
     the requests equal the note; and that nothing requires `ProvidesEtpCeph`.
5. **Sealed root.** `/ceph/srv/dwong/paperb/sweep2/<run_id>/` must not exist yet; the seal refuses overwrites.
6. **Real-submission switch** (S2-C5). It must refuse any other run id or digest. Show this with one refused dry
   attempt.
7. **Free space**, from the re-measurement:
   - on the submit host, 16 × (`out.tar` + `work.tar` + the record and logs);
   - on `/ceph`, 16 × the untarred sealed copy.
   The GGUF is not transferred back.

## 5. Submission order (proposal, for the author to confirm)

1. **Canary.** Submit two chunks: `digits_mlp-append_only_summary`, and the `none` chunk of the node the
   re-measurement shows as slowest. The pilot covered `digits_mlp` only, so a projection from it alone would not cover
   slower nodes.
2. **The canary verdict comes from the completed canary jobs.** `job_record.json` is written only when the collector
   finishes and comes back only at job exit (`ON_EXIT`), so nothing is observable mid-job. From each completed canary,
   read only the redacted fields (§7):
   - GPU L40S, the pinned CPU model, image identity;
   - GGUF sha256 verified, `server.build` as expected, offload 61/61;
   - liveness and the collection gates passed (fix C);
   - worker runs: counts succeeded and failed (fix E). A worker-environment failure, zero successful runs, or a failure
     share above the pre-declared bound is a STOP (§8);
   - label EVIDENCE, `NumJobStarts == 1`, rc 0;
   - `DiskUsage` and `MemoryUsage` within the requests.
3. **Projection check.** Recompute from the canaries' measured wall:
   - GPU-h = 16 × the larger canary wall;
   - wall = ⌈16 / concurrent L40S slots⌉ × wall.

   Above 60 GPU-h or 48 h: STOP before submitting the rest, and report to the author.
4. **The remaining 14** follow only if all canary checks pass.

An early identity line or record (for `condor_tail`) would need a further reviewed wrapper change. It is not assumed
here.

## 6. Monitoring, and no retries

- Poll at least every 30 minutes: `condor_q -nobatch` (status, `NumJobStarts`, hold reasons) and `condor_history` for
  finished jobs.
- **The wrapper has no resume path.**
  - The JDL transfers no prior `out/` or tars into a new job.
  - `render_jdl.py` requires a fresh stage.
  - `s2_c2_job.sh` empties `job_record.json` at every start.

  So a resubmission is a fresh full re-run, and a hand-staged resume would crash on the emptied record.
- **Therefore:**
  - any job that does not finish rc 0 with a complete record is a STOP;
  - so is any automatic restart (`NumJobStarts > 1`, for example after eviction under `ON_EXIT`);
  - preserve everything, report it, and the author decides;
  - no `condor_release`, `condor_rm`, resubmission or edit of a job without the author's instruction.
- **The authorization note's line does not create a resume path.** The S2-M1 redraft says the run is "resumable only
  by the collector's A.5 resume and the wrapper's resume pin check". That line authorizes nothing beyond what exists;
  with the current wrapper it means no resume. The author may want to amend it when committing the note.
- **During a STOP,** jobs already running continue and are sealed when they finish. No new job is submitted until the
  author decides.
- If the author wants resumes, a reviewed fix H must come first: staging `out.tar` / `work.tar` / `job_record.json` back
  in; not truncating an existing record; and attempts in the seal path.

## 7. Copy-back and sealing

- For each finished chunk: `python3 -m sweep2.s2_c2_lib seal <job-output> --run-id <run_id> --chunk-id <chunk_id>`.
- Then verify with `sha256sum -c SHA256SUMS` in the sealed directory, and keep `SEAL_RECEIPT.json`. After S2-C5 the
  seal also compares the digest and host with the note.
- Sealed layout: `/ceph/srv/dwong/paperb/sweep2/<run_id>/<chunk_id>/{out/, work/, job_record.json, llama-server.log,
  SHA256SUMS, SEAL_RECEIPT.json}`.
- Nothing is deleted or overwritten.
  - A failed job's transferred outputs stay in its submit directory, unsealed, and are reported.
  - The seal has one path per chunk, so sealing a second attempt of the same chunk would be refused. That case waits
    for the author (§6).
- **No label is read.** No table is built or copied for analysis before **R1-BX-D8-CONFIRM** (R1-BX-D8; the
  V3-A lock stands).
  - The lock in code is `analysis_guard.guard_table` / `require_d8_confirmation`.
  - **This deviates from the work plan §0's "`refuse_sealed` paths":** `refuse_sealed` matches only `r1_sealed`
    components, and this sealed path has none.
- **What leaves sealed storage.** Only a redacted projection of each job record goes into the repo or into reports:
  - identity fields, timings, counts, rc, the gate results, and the worker-run success/failure counts;
  - never `collector.stdout_tail` / `stderr_tail`, which in an EVIDENCE run contain in-campaign metric values;
  - never `llama-server.log`, which at `-lv 4` may contain prompts.

  The full records stay sealed.
- An **operational** index lists, per chunk: run id, chunk id, sealed path, receipt sha256, label and status. It
  gives counts only.
  - It is not the `r1.c3_sweep_index/1` that `r1/c3/dataset.py` reads.
  - Building that table index is a later unit, gated by R1-BX-D8.

## 8. STOP list (stop, preserve, report; no retry)

- A required PLAN row, precondition (§0) or authorization missing or different; note sha256 ≠ spec.
- A job on a GPU other than L40S, on a machine outside the regex, or on a CPU other than the pinned model.
- GGUF sha256 or size mismatch; image identity mismatch; `server.build` mismatch; offload below 61/61; OOM.
- Server arguments, context or `cache_prompt` differing from the note; `LLAMACPP_CACHE_PROMPT` or
  `LLAMACACHE_PROMPT` set.
- Liveness below 8 live nodes, parse-failure rate above 0.2, or a failing collection gate (fix C).
- Noise source missing or with a different sha256 (fix B).
- Label string not equal to the note's.
- Any B.2 audit or use of audit seeds 7001–7010: this note authorizes collection only (R1-SWEEP2-SETTINGS (2)), and the
  collector runs with `--audit-seeds 0`.
- A worker-environment failure or mismatch (fix E), zero successful worker runs in a chunk, or a worker-run failure
  share above a pre-declared bound. Some trials fail legitimately (`invalid_config`; D28 liveness allows an invalid
  rate below 30 %), so the bound is set in fix C or E, before launch.
- `NumJobStarts > 1`; a job not finishing rc 0 with a complete record; any `condor_release`, `condor_rm` or
  resubmission without the author's instruction.
- A request exceeded (disk or memory), or a walltime hit.
- A GGUF fetch error.
- A seal refusal (target exists, or the transferred `SHA256SUMS` do not match).
- The S2-C5 switch failing to refuse another run id or digest.
- Projection above 60 GPU-h or 48 h wall.
- Any code path reading sweep-2 labels before R1-BX-D8-CONFIRM.
- Any push to `main` without the author's instruction.

## 9. Report template (counts only; no label, metric or score)

```
# Sweep-2 EVIDENCE run <run_id> — run report (counts only)
authorization: docs/r1/authorizations/c3_sweep2_<date>.md  sha256 <…>   launch commit <…>   image <digest>
per chunk: chunk_id | cluster id | host | GPU | CPU model | queue wait s | wall s | GGUF fetch s | offload |
           model/KV/compute buffer MiB | NumJobStarts | rc | root campaigns completed (of 18) | worker runs ok / failed |
           LLM calls | parse failures | liveness pass | collection gates pass | DiskUsage / MemoryUsage vs requests |
           sealed path | SEAL_RECEIPT sha256
staged files: s2_c2_job.sh sha256 <…>  s2_c2_lib.py sha256 <…>  (equal to the launch commit's sweep2/)
totals: chunks complete <n>/16 · GPU-h <…> · wall h <…> · STOPs <list or none>
statement: no label, metric or table was read; sealed outputs untouched since sealing
```

## 10. What to send back

- the report;
- the operational index;
- the redacted projection of every job record (§7), and every seal receipt. Not the full records or logs, unlike
  `s2c4_run_20261116/`;
- the rendered JDLs and dry-run outputs;
- the canary checks.

All of it goes on a cluster branch, for independent review.
