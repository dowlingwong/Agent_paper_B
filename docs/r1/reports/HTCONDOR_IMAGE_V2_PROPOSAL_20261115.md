# HTCondor image v2 — proposal (15 November 2026, cluster agent; for review and author approval)

**Status: proposal only.** Branch `htc-image-v2-20261115` (from the reviewed `htc-image-20261114` @ `74820315`).
The ghcr digests in use (cpu `sha256:221ca459…`, gpu `sha256:69b06b35…`, SIFs from Actions run 43644472626)
**stay unchanged** until the author approves v2 and the re-run gates below pass. The v1 workflow on
`htc-image-20261114` is untouched; this branch's workflow builds tags `20261115-v2-<sha8>` only.

## Why v2

Author ruling Q-TORCH (A; `author-qtorch-20261115` @ `d4ea56c1`) plus the earlier image-v2 items:
1. env3 (Track P training) must be rebuilt from the committed TASL-7-validated GPU freeze exactly;
   `VERSIONS` must show an empty sorted diff against that freeze;
2. Python patch versions are pinned instead of "latest 3.x" at build time;
3. `libgomp` is installed explicitly (llama.cpp/torch OpenMP runtime; the D1 risk from the first build);
4. the gpu target ships `nvidia-smi` so the S5-style in-container GPU gate can run.

## What changes in `r1/scripts/htcondor/docker/Dockerfile`

- `ARG PY313=3.13.4 PY312=3.12.15 PY311=3.11.18` and `uv python install ${PY313} ${PY312} ${PY311}`.
  The patches are the validated host venvs' patches: exam/B1/B2 venv 3.13.4, Track P GPU venv 3.12.15,
  Track S venv 3.11.18 (TASL-7 read-only `python -VV`). No "3.13/3.12/3.11" floating install remains.
- `libgomp` added to every dnf install list (build, cpu, gpu) and recorded in VERSIONS.
- env3: `uv venv --python 3.12.15`; the new committed freeze `r1/scripts/htcondor/apptainer/pip_freeze_trackp-gpu.txt`
  (121 lines, byte copy of `docs/r1/reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt`) is installed
  **--no-deps**; the three VCS deps (`kev@2074cc4`, `laya@a478221`, `startlux-decide@a99977d`) are installed
  as before; `torch==2.6.0+cu124` comes from `download.pytorch.org/whl/cu124`;
  `causal-conv1d==1.7.0` is built from source with `--no-build-isolation --no-binary` and
  `TORCH_CUDA_ARCH_LIST="8.0;8.9;9.0"` (A100/L40S/H200; the TASL-7 build used 8.9 on the V100S host).
  The build then runs `uv pip freeze | sort` and `diff -u` against the sorted committed freeze;
  **a non-empty diff fails the build** (same check re-asserted in the gpu target before VERSIONS).
- gpu: `COPY --from=build /usr/bin/nvidia-smi /usr/bin/nvidia-smi` from the CUDA devel base and
  `RUN test -x /usr/bin/nvidia-smi`; VERSIONS records `nvidia_smi`, `libgomp`, the env3 freeze SHA-256,
  `env3_sorted_diff=empty`, and `torch_pin=torch==2.6.0+cu124 (Q-TORCH ruling)`.

## Verification plan (each step reviewed before the next; no digest switch before the author approves)

0. **Pre-build checks (done or listed):** the devel/runtime CUDA bases could **not** be probed on the ETP login node (`docker` client present but no daemon socket: `Cannot connect to the Docker daemon at unix:///var/run/docker.sock`); the first v2 build is therefore the nvidia-smi pre-check (the `COPY --from=build /usr/bin/nvidia-smi` fails the build visibly if the devel base lacks it). Fallbacks if it fails: install driver-utils in the gpu target, or gate the GPU with a torch-based check instead (the S5/I3 torch evidence shows the runtime driver injection works on NEMO2), and do not hard-gate any job on `nvidia-smi` until the v2 I2/I3 re-run proves it at runtime; the TASL-7 raw freeze capture and the empty sorted diff are committed under `docs/r1/reports/htcondor_image_20261115/` (`tasl7_trackp_gpu_uv_pip_freeze.txt` SHA-256 `50238e5a…`, 121 lines; `tasl7_vs_committed_freeze.sorted.diff` = 0 lines). The torch install uses `--no-deps` (the freeze pins its closure), and VERSIONS records the causal-conv1d arch list `8.0;8.9;9.0`.
1. **Build** the branch (Actions) → `20261115-v2-<sha8>` tags; record both digests and the VERSIONS files.
   Review: Dockerfile diff, build log, VERSIONS (empty env3 sorted diff, pinned patches, libgomp, nvidia-smi).
2. **I2/I3 re-run on v2** on NEMO2 (container universe) and TOpAS (docker/container) with the new **gpu** digest (I2's tiny-llama probe runs the **cpu** image; I3 the gpu image), through a temporary manifest pinned to the v2 tags (the in-use manifests and digests stay untouched):
   I2 = tiny-llama CUDA probe; I3 = HF fixed-URL download + sha256 + llama-server ready + GPU offload log
   (the v1 evidence: I3 NEMO2 L40S 18 s download/833 s run; TOpAS V100S 19 s/213 s). Compare and review.
3. **`r1/scripts/trackp_gpu_smoke.py` parity** on L40S (NEMO2) and H200 (NEMO2) against the TASL-7 values
   (bf16 matmul rel. error 2.874e-3; fp32 DeltaNet max |Δlogit| 0.02935/tol 0.0403; bf16 0.2361/tol 0.530/99.51 %;
   peak 3,345/2,096 MiB). Review the JSON.
4. **One E0 equivalence job** (the 25-minute E0 run, same config as the TASL-7 equivalence) on the H200 or L40S
   with the v2 **gpu** image; compare with the TASL-7 equivalence record (GPU time and walltime recorded). Review.
5. Only then: author approval → update the job manifests/adapters to the v2 digests, keep the v1 digests in
   the record, and re-run the full I-chain before any Track P training on HTCondor. **Rollback:** the v1
   digests/tags remain valid and published; until the switch, every job manifest keeps using them.
   Track P training is additionally guarded by the adapter (`trackp_gpu_device_names = ["NVIDIA L40S",
   "NVIDIA H200"]`, V100S refused).

**Constraints honoured:** no force push; no change to `main`/`r1/exam-x-*`; nothing deleted (a failed
attempt moves aside to `_to_delete`); no Track P training on HTCondor before gates 3–4 pass; no V100S for
Track P; digests in use unchanged until the author approves.

## Evidence

- freeze: `r1/scripts/htcondor/apptainer/pip_freeze_trackp-gpu.txt` (121 lines; sorted diff empty against the
  TASL-7 venv `uv pip freeze`, verified read-only on TASL-7 on 15 Nov 2026, capture committed as
  `docs/r1/reports/htcondor_image_20261115/tasl7_trackp_gpu_uv_pip_freeze.txt`, SHA-256 `50238e5a…`).
- TASL-7 env values: `docs/r1/reports/TRACKP_PHASE2_ENV_PINS_TASL7_20261026.md`.
- v1 digests/images: Actions run 43644472626, report `reports/HTCONDOR_CHAIN_20261114.md`.
