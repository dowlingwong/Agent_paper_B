# Independent review — HTCondor image v2 proposal (branch `htc-image-v2-20261115`, pinned commit `4dd563b9`)

**Reviewer role:** fresh, independent, read-only reviewer. Not the author of the unit, not the executing agent.
I ran only read-only checks: `git show`/`diff`, file hash/size checks, byte comparison of the committed freeze
against the TASL-7-validated freeze, grep of the freeze for the recipe assumptions, and reads of the proposal,
workflow, Dockerfile and the Q-TORCH ruling. No cluster access, no image build/push, no git commit.

**Date/time of review:** 15 November 2026, 21:00–21:50 CET (Europe/Berlin).

**Reviewed unit:** branch `htc-image-v2-20261115` at pinned commit **`4dd563b9`** (one commit on
`htc-image-20261114` @ `74820315`), worktree
`/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/htc-image-v2-20261115` (clean). The v1 digests in
use (cpu `sha256:221ca459…`, gpu `sha256:69b06b35…`) are not changed by this unit.

**Basis:** the author's Q-TORCH ruling A (`author-qtorch-20261115` @ `d4ea56c1`: "env3 installed exactly from the
committed R1-ENV-PIN GPU freeze, causal-conv1d compiled for 8.0/8.9/9.0; no Track P training on the cluster until
L40S/H200 smoke + E0 equivalence pass; V100S not used for Track P; current digests unchanged until the author
approves v2; v2 env3 sorted diff empty"), the proposal `docs/r1/reports/HTCONDOR_IMAGE_V2_PROPOSAL_20261115.md`, the
v1 review record `HTCONDOR_CONTAINER_UNIT_REVIEW_20261115.md`/`HTCONDOR_ADAPTER_REVIEW_20261114.md` conventions,
the S3 def review (the def route is stopped; the Docker route is the operative one), the TASL-7 pins doc
`docs/r1/reports/TRACKP_PHASE2_ENV_PINS_TASL7_20261026.md`, and the S5/I3 evidence (torch 2.6.0+cu124 works on
NEMO2 L40S; the S5 nvidia-smi gate artefact prompted the nvidia-smi addition).

---

## 1. Files reviewed and pinned (SHA-256, verified)

| File | SHA-256 |
|---|---|
| `r1/scripts/htcondor/docker/Dockerfile` | `7c4013956b8f46b9dda3928118fc41eee3f0f7f7bbd97d7f488486bec175b45a` |
| `r1/scripts/htcondor/apptainer/pip_freeze_trackp-gpu.txt` | `50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08` (121 lines) |
| `.github/workflows/r1-htc-image.yml` | `4d683ddc7de62560d62ea66bf21272404e1177140d9171bfa11a55e21f004930` |
| `docs/r1/reports/HTCONDOR_IMAGE_V2_PROPOSAL_20261115.md` | `e663224240e2984b58a04f4fd06d6b5f28603f8035492f5d234a0f45d153c514` |
| Committed freeze vs `docs/r1/reports/trackp_phase2_20261026/pip_freeze_trackp-gpu.txt` | **byte-identical** (`50238e5a…`, 121 lines) |
| Q-TORCH ruling | `author-qtorch-20261115` @ `d4ea56c1` (PLAN §10 R1-HTC-QTORCH) |

---

## 2. Checks performed, and results

### (a) Python patch pins — 3.13.4 / 3.12.15 / 3.11.18

`ARG PY313=3.13.4 PY312=3.12.15 PY311=3.11.18`; `uv python install ${PY313} ${PY312} ${PY311}`; env1
`uv sync --frozen --extra dev --python ${PY313}`, env2 `uv venv --python ${PY311}`, env3 `uv venv --python
${PY312}` — **no floating "3.x" install remains** (checked in the Dockerfile). The patches are the validated host
venvs' patches per `TRACKP_PHASE2_ENV_PINS_TASL7_20261026.md` (**3.12.15** for the Track P GPU venv, built from the
recorded freeze; the doc also records the portal's uv 0.13.5 and `uv python install`). This is the right v2
choice: it removes build-time Python drift and, notably, pins env1 to **3.13.4** — exactly the S4/I2 reference
patch, so the `0.922225 x 4` I2 result should now reproduce without the 3.13.18-vs-3.13.4 stack difference that S4
had to record. VERSIONS records the actual `python -VV` for all three envs. **Gate:** confirm `uv python install`
has those exact patches (the build fails visibly if not; the first build log is the evidence).

### (b) env3 recipe — freeze filter, --no-deps, cu124 torch, source causal-conv1d, VERSIONS diff

Verified against the Dockerfile and the committed freeze:
- **Freeze content** (121 lines, byte copy of the portal freeze): includes the build deps needed for
  `--no-build-isolation` — `ninja==1.13.2`, `setuptools==84.2.1`, `wheel==0.48.0`, `packaging==26.2`, plus
  `torch==2.6.0+cu124`, `triton`, 13 `nvidia-*` wheels, `transformers==5.19.0`, `causal-conv1d==1.7.0`, and the
  three VCS lines (`kev @ git+…@2074cc44…`, `laya @ git+…@a478221…`, `startlux-decide @ git+…@a99977d…`) — all
  exactly the commits the Dockerfile installs. **No `-e`/`--editable`/`/home`/`file:` lines** (the earlier
  tracks-freeze `/home` problem from the S3 review is absent). The freeze is **not sorted** (it is a raw
  `uv pip freeze` output); the Dockerfile sorts both sides before the diff — correct.
- **Filter:** `grep -viE '^(torch==|causal-conv1d==|kev[[:space:]]|laya[[:space:]]|startlux-decide[[:space:]])'`
  removes exactly the five explicit installs from the pinned set — correct (the freeze's VCS lines are
  `kev @ …`/`laya @ …`/`startlux-decide @ …`, matched by `name[[:space:]]`).
- **Order:** pinned set `--no-deps` → the three VCS deps `--no-deps` at the pinned commits → `torch==2.6.0+cu124`
  from `download.pytorch.org/whl/cu124` → `causal-conv1d==1.7.0` from source with `--no-binary --no-build-isolation`
  and `TORCH_CUDA_ARCH_LIST="8.0;8.9;9.0" MAX_JOBS=$(nproc)`. Correct dependency order (the source build needs
  torch/setuptools/wheel/ninja, all present).
- **VERSIONS / sorted diff:** the build stage computes `uv pip freeze | sort` and `diff -u` against the sorted
  committed freeze and fails the build on any difference; the same check is **re-asserted in the gpu target**
  before VERSIONS, and VERSIONS records `trackp_gpu_freeze_sha256`, `env3_sorted_diff=empty`,
  `torch_pin=torch==2.6.0+cu124 (Q-TORCH ruling)`, `nvidia_smi`, `libgomp`. This is the required proof, and it
  matches the Q-TORCH ruling. Good.
- **Small risk (record/decide, not blocking):** `torch` is installed **without `--no-deps`**, so uv may re-resolve
  the already-installed `nvidia-*`/`triton` deps against the cu124 index; if any version changes, the sorted-diff
  guard fails the build (fail-closed, not silent). Recommend adding `--no-deps` to the torch install (the freeze
  already pins its dependency closure) or confirming from the first build that the diff is empty.
- **Arch list:** `8.0;8.9;9.0` targets A100/L40S/H200 (V100S = sm_70 is deliberately not targeted, consistent with
  "no V100S for Track P"); record the arch list in VERSIONS too (it is currently only in the Dockerfile command).

### (c) nvidia-smi in the gpu target

`COPY --from=build /usr/bin/nvidia-smi /usr/bin/nvidia-smi` (from the CUDA **devel** build stage) + `RUN test -x` —
the intent (let the S5-style in-container GPU gate run) is right, and the v1 runtime base indeed lacks the binary
(S5's "nvidia-smi MISSING" artefact). Two conditions: (i) **the devel base actually contains `/usr/bin/nvidia-smi`
is unverified from here** — if it does not, the build fails at the COPY (`test -x` would catch a non-executable
copy; the COPY itself fails if the file is missing), which is safe but wastes a CI run; pre-verify read-only
(the image is public) or keep this as the explicit first-build check, and have a fallback ready (install the
driver-utils package from the CUDA repo, copy from a known image, or fall back to a torch-based S5 gate). (ii) At
runtime the copied `nvidia-smi` needs the host's `libnvidia-ml.so.1`/driver libs injected; the S5/I3 evidence shows
the driver libraries do reach NEMO2 containers (torch CUDA + matmul worked on the L40S), so it should work there, but
do **not** make nvidia-smi a hard gate until the v2 I2/I3 re-run proves it (the S5 artefact was exactly a
gate-on-nvidia-smi problem). Record the binary's version vs the host driver (`615.71.10` on the I3 NEMO2 host) in
the re-run evidence.

### (d) Workflow

The diff changes only: the trigger branch `htc-image-20261114` → **`htc-image-v2-20261115`**, and the tag
`20261114-${GITHUB_SHA::8}` → **`20261115-v2-${GITHUB_SHA::8}`**. The build context, files, targets, platforms,
`push: true`/`provenance: false`, permissions and `timeout-minutes: 300` are unchanged; the v1 branch/workflow and
the digests in use are untouched (the adapter/I3 manifests still pin the v1 digests). The `paths` filter includes
`r1/scripts/htcondor/apptainer/**`, so the new freeze file is a build input ✓. A push may already have started a
v2 build — that only creates new `20261115-v2-…` tags; nothing in use changes. **Record:** the Actions run id, the
two v2 digests, and the VERSIONS files from the build; confirm the v2 tags' visibility (public, like v1) before the
re-runs.

### (e) Proposal verification plan

The staged plan is sound and matches the ruling: build → review (Dockerfile diff, build log, VERSIONS) → **I2/I3
re-run on v2** (NEMO2 container universe; TOpAS docker/container) → **`trackp_gpu_smoke.py` parity** on L40S (NEMO2)
and H200 (NEMO2) against the TASL-7 values (bf16 matmul rel. error 2.874e-3; fp32 DeltaNet max |Δlogit|
0.02935/tol 0.0403; bf16 0.2361/tol 0.530/99.51 %; peak 3,345/2,096 MiB) → **one E0 equivalence job** (25 min,
same config as the TASL-7 equivalence) → author approval → switch the manifests/adapters to the v2 digests, keep
the v1 digests in the record, re-run the full I-chain; no Track P training before gates 3–4; no V100S for Track P;
no force push; nothing deleted. Recommended additions: (i) state exactly which image (cpu or gpu) each re-run uses
— I2 is the cpu-image (S4-style) test, I3/smoke/E0 the gpu image; (ii) the v2 re-run manifests temporarily pin the
v2 digest and must not change the in-use digests; (iii) record the v2 build log/VERSIONS/digests in the proposal
before the re-runs; (iv) enforce "no V100S for Track P" in the adapter's table pins/manifests (the adapter's
`gpu_device_names` list still contains the V100S, so a Track P manifest must pin L40S/H200; the adapter's
`check_table_pin` is the mechanism); (v) record the E0 job's GPU/walltime accounting; (vi) a rollback line (v1
digests remain valid; the v2 tags are additive).

### (f) Adequacy of the TASL-7 freeze evidence for the VERSIONS requirement

The committed freeze is a **byte copy** of the portal freeze (verified `50238e5a…`, 121 lines), and
`TRACKP_PHASE2_ENV_PINS_TASL7_20261026.md` records that the TASL-7 venv's `uv pip freeze` is identical to the portal
freeze with a **sorted diff of 0 over 121 lines** (covering torch 2.6.0+cu124, triton 3.2.0, transformers 5.19.0,
peft 0.21.2, fla 0.5.2, causal-conv1d 1.7.0, kev/laya/startlux at the pinned commits). That is **adequate
provenance for the target freeze**, but it is not by itself evidence for the image's env3: the required proof is
the **build-time sorted diff** against the committed freeze, which the Dockerfile performs in the build stage and
re-asserts in the gpu target and records in VERSIONS (`trackp_gpu_freeze_sha256`, `env3_sorted_diff=empty`) — so the
combination is adequate. **Recommend:** commit the TASL-7 raw read-only capture (the exact `uv pip freeze | sort`
command and the diff output, or a pointer to the pins doc's section) so the provenance is not only narrative.

---

## 3. Findings

### BLOCKING / MAJOR

None. The v2 change set is scoped, matches the author's Q-TORCH ruling A, keeps the in-use digests untouched, and
every risky step is fail-visible (the build's `test -x`/sorted diff fail the build; the plan's re-runs are gated
and reviewed one at a time).

### MINOR

1. **m1 — verify `/usr/bin/nvidia-smi` exists in the CUDA devel base before the build** (see (c)); the COPY
   fails the build if absent. Have the fallback recorded (driver-utils install / alternate source / torch-based
   gate).
2. **m2 — add `--no-deps` to the cu124 torch install** (or confirm from the first build that the sorted diff is
   empty): the freeze already pins torch's dependency closure, and a re-resolution is otherwise possible (the diff
   guard makes it fail-closed, not silent).
3. **m3 — record the arch list** (`TORCH_CUDA_ARCH_LIST=8.0;8.9;9.0`) and the `nvidia-smi` version in VERSIONS (the
   freeze sha, libgomp and sorted-diff result are already there); correct the proposal's confusing parenthetical
   "the TASL-7 build used 8.9 on the V100S host" — state instead: 8.0/8.9/9.0 target A100/L40S/H200, V100S (sm_70)
   is deliberately excluded and Track P is not to run on V100S (per the ruling).
4. **m4 — the adapter must enforce "no V100S for Track P"** in the table pins/manifests when the Track P work
   moves to HTCondor (the config's `gpu_device_names` still lists the V100S; that is fine for probes/I-probes, but
   Track P table pins must be L40S/H200). This is outside the v2 build but is a precondition of gate 3–5.
5. **m5 — commit the TASL-7 raw freeze/diff capture** (see (f)); the pins doc prose is good but a raw file is
   stronger for the VERSIONS audit.
6. **m6 — cpu-target VERSIONS lacks the `libgomp` line** (the cpu stage installs libgomp; the gpu VERSIONS records
   it). Add it for symmetry/record.
7. **m7 — the freeze path** `r1/scripts/htcondor/apptainer/pip_freeze_trackp-gpu.txt` is in the Docker build
   context (correct: the workflow context is the apptainer dir); note in the proposal that it is a Docker input
   stored beside the other freeze files, not an apptainer-def input.
8. **m8 — the proposal's v1 I3 TOpAS line ("19 s/213 s")** should cite the source report/commit once the TOpAS
   run is in the record; make every quoted number traceable.

### NIT

- **n1** — the freeze is unsorted by design (raw `uv pip freeze`); add one sentence in the proposal ("the
  Dockerfile sorts both sides; the committed file is the raw freeze") so a future reader does not "fix" it.
- **n2** — the Dockerfile header line "the TASL-7 build used 8.9 on the V100S host" (see m3) and the v1/v2 label
  `r1.def_route=…a5a0c9da` are stale; the def is not updated for v2 (the def route is stopped) — record that the
  Dockerfile is now the authoritative recipe and the def remains the v1 record.
- **n3** — the v2 tags (`20261115-v2-<sha8>`) should also be recorded in the chain report once the build lands,
  with the two digests, so the I2/I3 re-run manifests can cite them.

---

## 4. Verdict and conditions

**Accepted as a proposal for build and the gated re-runs, not as a replacement for the images in use.** The v2
change set is the right response to the v1 evidence: env3 is rebuilt exactly from the R1-ENV-PIN committed GPU
freeze with the Q-TORCH-approved recipe (Python 3.12.15, `--no-deps`, cu124 torch, source causal-conv1d for
8.0/8.9/9.0, build-time sorted-diff-empty gate re-asserted in the gpu target and recorded in VERSIONS), Python
patches are pinned to the validated venvs (env1 3.13.4 now matching the I2 reference), libgomp is installed
explicitly (D1), and the gpu target gains nvidia-smi for the S5-style gate. The workflow is scoped to the v2 branch
with additive tags; the v1 digests and manifests are untouched; the verification plan (build → I2/I3 re-run →
L40S/H200 smoke parity → one E0 equivalence → author approval → switch) matches the ruling and is sound.

**Conditions before the v2 images may be switched in:** (1) pre-verify the nvidia-smi source (m1) and record the
build's `test -x` result; (2) the first build's sorted diff must be empty and its VERSIONS/build log reviewed (m2,
m3); (3) record the v2 digests and their public visibility, then run the gated I2/I3/smoke/E0 sequence with
independently reviewed results; (4) enforce the no-V100S-for-Track-P rule in the adapter/manifests (m4); (5) author
approval before any manifest/adapter points at the v2 digests, and the v1 digests stay in the record. The MINOR
items do not block the build/plan.

**Residual risk carried:** the nvidia-smi presence in the devel base and the runtime libnvidia-ml injection are
unverified until the first build/gpu run; the freeze-based env reproducibility is proven by the build-time diff
(not by this review); the causal-conv1d source build adds CI time and depends on the CUDA devel toolchain
(nvcc present) and the pinned build deps; the v2 tags' pullability/visibility is author/Actions-side; Track P
training on HTCondor remains gated on the smoke + E0 evidence and the author's approval.

VERDICT: ACCEPTED

---

## Delta re-check — pre-build conditions (branch @ `3c3a2261` + `c5213bd7`; 15 Nov 2026, 21:40 CET)

**Delta verdict: the pre-build conditions are adequately handled; the proposal stays accepted, with the build and the gated re-runs still the required evidence.**

Verified on the branch (HEAD `c5213bd7`, fix `3c3a2261`): the cu124 torch install is now `uv pip install --no-deps --index-url https://download.pytorch.org/whl/cu124 'torch==2.6.0+cu124'` (the freeze pins its closure); VERSIONS now also records `env3_causal_conv1d_arch=8.0;8.9;9.0` (alongside the freeze sha, `env3_sorted_diff=empty`, `torch_pin`, `nvidia_smi`, `libgomp`); the TASL-7 raw capture is committed under `docs/r1/reports/htcondor_image_20261115/` (`tasl7_trackp_gpu_uv_pip_freeze.txt`, 121 lines, SHA-256 `50238e5a…` — byte-identical to the committed freeze — and `tasl7_vs_committed_freeze.sorted.diff`, 0 bytes, SHA-256 the empty-file digest); the proposal states which image each re-run uses (I2's tiny-llama probe on the **cpu** image, I3/smoke/E0 on the **gpu** image), the temporary v2-pinned manifest that leaves the in-use digests untouched, the rollback line (v1 digests/tags remain valid and published until the switch), and the Track P device guard; and the `c5213bd7` addendum records that the ETP login node has a docker **client** but no daemon socket, so the devel-base nvidia-smi pre-check cannot run there — the first v2 build is the pre-check (the `COPY --from=build /usr/bin/nvidia-smi` fails the build visibly if the file is absent), with documented fallbacks (install driver-utils in the gpu target, or a torch-based GPU gate) and no hard `nvidia-smi` runtime gate until the v2 I2/I3 re-run proves it; this is the correct, fail-visible handling of the environment limitation.

The remaining conditions from the review are therefore either satisfied (torch `--no-deps`, arch recorded, TASL-7 raw capture committed, proposal mappings/rollback/Track P guard) or explicitly converted into the first build's check (nvidia-smi presence) with a fallback plan — no blockers. The build log/digests/VERSIONS review, the gated I2/I3 re-run, the L40S/H200 smoke parity, the E0 equivalence and the author approval remain the required pre-switch evidence; the v1 digests stay in use until then. Minor record nits: the empty sorted-diff file would be stronger with a one-line command/date header, and the proposal's pre-build paragraph should keep the no-daemon statement (as in `c5213bd7`) rather than any earlier "probe pending" wording.

VERDICT: ACCEPTED
