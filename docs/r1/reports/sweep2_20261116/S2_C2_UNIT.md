# S2-C2 — sweep-2 HTCondor job wrapper + sealing step (round 2; unit for independent review; ENGINEERING)

**Authority:** `docs/r1/prompts/SWEEP2_HTCONDOR_RUNBOOK_20261116.md` (`docs/runbooks-16nov` @ `a2789ea6`), §3 S2-C2
and §1 P1–P7 (work plan, not a decision). EVIDENCE launch is gated on the PLAN row `R1-SWEEP-HOST-HTC` (absent on
`author-x7-20261116`; verified 0 matches) and P1–P7. Nothing was launched or submitted. This round answers the
independent review `docs/r1/reviews/S2_C2_REVIEW_20261116.md` (B1–B3, M1–M4, minors).

## Architecture (changed: NEMO2 cannot write /ceph)

**B2 finding, captured raw:** NEMO2 slots do **not** advertise `ProvidesEtpCeph` — `condor_status -af CloudSite
ProvidesEtpCeph` gives `BwForCluster-Nemo2 undefined` (57 slots); only `portal`/`mdm`/`schnepf`/`etpsupermachines`
are `true` (`sweep2/evidence/nemo2_provides_etpceph.txt`). A requirement `TARGET.ProvidesEtpCeph` would match no
NEMO2 slot and the job would idle forever. Therefore:

1. the **container job** writes only into its HTCondor sandbox: `out/`, `work/`, `job_record.json`,
   `SHA256SUMS`, `llama-server.log`; the JDL transfers those back to the submit host
   (`transfer_output_files = out,work,job_record.json,SHA256SUMS,llama-server.log`);
2. the reviewed **seal step** (`s2_c2_lib.py seal`) verifies the transferred job record (run/chunk, label, image
   digest, host) and copies the outputs into the sealed
   `/ceph/srv/dwong/paperb/sweep2/<run_id>/<chunk_id>/` path (resolve + `..` refusal + symlink refusal + no
   overwrite + its own SHA256SUMS and `SEAL_RECEIPT.json`). The submit host is on ETP, where /ceph exists.
3. The JDL has **no** `ProvidesEtpCeph` requirement; the GPU/CPU class pins are unchanged.

## Files

| file | role |
|---|---|
| `sweep2/s2_c2_lib.py` | spec validation, authorization-only label resolution, frozen-image identity, host/GPU/CPU/driver identity, streaming GGUF fetch+sha256, owned llama-server (exam flags, tolerant full-offload check), harness collection (`r1.headroom.e1b_collect`, `langgraph`, `llamacpp/<alias>`), job record + SHA256SUMS, resume pin check, `seal` |
| `sweep2/s2_c2_job.sh` | container-job entry point |
| `sweep2/render_jdl.py` | stages the job inputs (+ authorization note when pinned) and renders the fixed JDL |
| `sweep2/spec.example.json` | reviewed ENGINEERING example (frozen v1 gpu digest, B2 harness pin `a3fedbb…`, pick GGUF with registry provenance, L40S/Nemo2/CPU class, transfer outputs) |
| `sweep2/dryrun/` | staged inputs, rendered JDL, real `condor_submit -dry-run` ad |
| `sweep2/evidence/nemo2_provides_etpceph.txt` | raw read-only capture (B2) |
| `r1/tests/htcondor/test_s2_c2_unit.py` | 18 synthetic tests (pass locally) |

## Fixes vs the review

- **B1 sealed path:** the job no longer writes `/ceph`; sealing is the operator-side `seal` step, which resolves
  the target, refuses `.`/`..` parts and any symlink component, and refuses an existing target (no overwrite).
  Tests cover traversal and a symlink escape.
- **B2 NEMO2 ceph:** raw condor_status capture committed; the JDL no longer requires `ProvidesEtpCeph`; outputs
  transfer to the submit host and are sealed there. The validator **refuses** a spec that still sets
  `requires_etp_ceph`.
- **B3 disk/memory:** `request_disk = 50000000` kB (≈50 GB: 19.6 GB GGUF + ≈11 GB container-universe image cache +
  work), `request_memory = 128000` MB; S2-C4 will measure the real peak and we will pin the measured values.
- **M1 harness stack:** the validator requires the **B2 harness pin** `a3fedbb…` (the spec's `harness.commit`);
  `897d83c8` is refused, so sweep-2 reproduces the B2 stack (`cache_prompt:false` etc.).
- **M2 class constants:** `CLOUD_SITE`, `GPU_MODEL`, `MACHINE_REGEX`, `MIN_CPUS` are module constants; the
  renderer builds the requirements from them and the validator refuses any spec whose `requirements` differ
  (negative tests; a broad regexp cannot be smuggled in).
- **M3 runtime host/identity:** the job verifies the landed hostname/FQDN against the class regexp and
  `os.cpu_count() >= 16`, and the record carries `host`, `gpu` (L40S/UUID/driver), `cpu` (model/cores), image
  identity (digest + VERSIONS markers + llama-server hash), paper/harness commits and the label. Off-class landing
  is a STOP (runbook §4).
- **M4 EVIDENCE note transfer:** `render_jdl.py --auth-note` stages the authorization note and adds it to
  `transfer_input_files`; the staged spec uses the job-relative basename, so `resolve_label` reads it inside the
  job sandbox. ENGINEERING specs have `authorization: null`.
- **Minors:** streaming GGUF hash (no 18.3 GiB read_bytes); driver regex reads only the version; GGUF provenance
  (`registry_doc` + `registry_sha256` + revision/file/source label) required in the spec; resume checks the old
  record's image/model/label/paper/harness pins and STOPs on mismatch; `walltime_s` validated; manager settings
  (temperature 0.2/D26, `cache_prompt` false / `LLAMACACHE_PROMPT` unset, thinking off, q8_0 KV, ctx 16384) are
  recorded in the job record with their source; the offload check tolerates the llama.cpp wording
  (`offloaded N/N layers to GPU`) and STOPs when the log proves nothing (S2-C4 will confirm the exact v1 line and
  we will pin it); EVIDENCE additionally requires `paper.evidence_ready = true` (the S2-M2 integration commit);
  the label-defect test docstring is scoped to this wrapper's path; `c3_label_sweep` extra-manifest carries the
  documented schema fields only.

## Reviewed dry-run evidence (deepthought, no submission)

`condor_submit -dry-run` rc 0: `JobUniverse=5`, `WantContainer=true`, `ContainerImageSource=docker`,
`container_image=docker://ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35…`, `RequestGPUs=1`, `RequestCpus=16`,
`RequestDisk=50000000`, `RequestMemory=128000`, `+RemoteJob=True`, requirements `CloudSite Nemo2 && GPUs_DeviceName
L40S && Arch X86_64 && OpSys LINUX && Cpus>=16 && regexp("^g36[0-9]{2}\.nemo\.privat$")` plus the scheduler's
`HasContainer && HasDockerURL`, **no** ProvidesEtpCeph. Raw: `sweep2/dryrun/s2_c2.dryrun.txt`. No job queued.

## Running an ENGINEERING job (after acceptance; P1–P7 not needed for ENGINEERING)

1. Stage + render (submit host): `python3 sweep2/render_jdl.py <spec> --out <jdl> --stage-dir <stage>`
   (add `--auth-note` only for EVIDENCE).
2. `condor_submit <jdl>` from the stage dir with the reviewed ENGINEERING switch (S2-C5 remains separate; for now
   the reviewed unit's dry-run only does not submit — the engineering submission needs the author's allowance for
   these reviewed ENGINEERING jobs, per the runbook).
3. On completion, copy the transferred job output directory and run
   `python3 -m sweep2.s2_c2_lib seal <job-output> --run-id <id> --chunk-id <id>` to write the sealed `/ceph`
   evidence; verify `SHA256SUMS`/`SEAL_RECEIPT.json`.
4. S2-C4 (timing pilot) uses a small spec (1 node × 2 instances × both modes) and measures wall time, queue wait,
   GPU memory, GGUF fetch time; S2-C3 replays the B2 roots and compares with B2 EVIDENCE values (separate units).

## STOP / no-retry / no-deletion

Any spec/pin/label/identity/GGUF/server/offload/host-class/resume mismatch STOPs before submission or kills the
owned server; the transferred sandbox and the sealed attempt are kept (never deleted, never overwritten); the
collector's own A.5 resume is the only retry mechanism; raw labels are written sealed and never read.

## Round 4 — author decisions 16 Nov (`author-decisions-20261116` @ `4da73306`; rebased onto main `9ae6d877`)

- **Base:** the job code is rebased onto `main` @ `9ae6d877` (S2-M2 integration); unit files were ported onto that
  tree, no sweep-1 changes.
- **R1-SWEEP2-SETTINGS (1):** context is now **32,768**; server argv is the exam setting `-c 32768 -ngl 999 -np 1`
  with `--jinja`, `{"enable_thinking":false}`, q8_0 K/V cache and `cache_prompt` false on every call. The validator
  pins `ctx=32768`, `n_gpu_layers=999` and rejects the old values; `-np 1` is managed by the wrapper. The two
  non-numeric differences from the exam server (`--no-webui`, `-lv 4` log level) are recorded in the job record as
  `non_numeric_differences` and disclosed.
- **R1-SWEEP2-SETTINGS (4):** sweep-1 liveness/collection gates are restored:
  - D28 liveness (all eight sweep-1 nodes, memory on, 2 instances, W=10) is a first-class job mode (`kind:
    liveness`) running `python -m r1.liveness`; `min_live_nodes = 8`, and a shortfall STOPs for the author;
  - every chunk job runs the sweep-1 collection gates after the collector: all expected instance roots present and
    `parse_failure_rate <= max_parse_failure_rate = 0.2`; a breach is a STOP and is recorded in the job record.
- **E1 noise source:** the chunk job passes `--e1-summary <paper>/results/r1/noise/D28_REPAIR_20261027/summary.json`
  to the collector, pins the file's SHA-256 `3d12ce05…` (checked before the collector), records it per manifest
  (`c3_label_sweep.noise_source` and the job record) and STOPs on any path/sha mismatch; a test covers the STOP.
- **CPU class in the HTCondor requirements:** the L40S class measured by S2-C4 is Intel Xeon Platinum 8562Y+
  (`cpu family 6`, `model 207`); the JDL now requires `TARGET.CpuFamily =?= 6 && TARGET.CpuModelNumber =?= 207`
  in addition to `CloudSite=Nemo2`, `GPUs_DeviceName=NVIDIA L40S`, `Arch/OpSys` and `Cpus>=16`, and the wrapper
  verifies the same class from `/proc/cpuinfo` at runtime (model-name contains string included). No `CpuModel`
  string is advertised by the pool, so the family/model numbers carry the class. Current ads matching the full
  requirement: `g3608.nemo.privat` (2 slots, 16 CPUs) and `g3611.nemo.privat` (1 slot, 62 CPUs) on 16 Nov 11:20 CET;
  S2-C4's L40S nodes are the same CPU family/model.
- **Dry-run:** regenerated reviewed JDL + `condor_submit -dry-run` rc 0 (`JobUniverse=5`, `RequestDisk=50000000`,
  `RequestMemory=128000`, `RequestGPUs=1`, container digest `69b06b35…`, requirements Nemo2+L40S+Arch/OpSys+Cpus≥16+
  CpuFamily 6+CpuModelNumber 207, transfer outputs out.tar/work.tar). No submission.
- Tests: **26 synthetic S2-C2 tests + 6 S2-C4 tests pass** (noise-source STOP, CPU-class and settings validators,
  gates, liveness argv/block, non-numeric disclosures, transfer/seal guards).
