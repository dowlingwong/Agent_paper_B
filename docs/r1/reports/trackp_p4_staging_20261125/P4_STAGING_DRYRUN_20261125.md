# P.4 staging, CPU-only dry run and provisional evidence-phase cost (25 November 2026)

**PROVISIONAL. No GPU job was submitted; no P.4 training was started.** Staging lives on ceph:
`/ceph/srv/dwong/paperb/trackp_p4/staging_20261125/`.

## 1. Staging on ceph (no sealed test split touched)

- **SFT base/adapter weights** from the reviewed `r1/c3/train/registry.yaml` at the pinned revisions, for the four
  phase-1 arms (`kev-0.8b`, `kev-4b`, `qwen3.5-0.8b-base`, `qwen3.5-4b-base`): **53 files, 11,338,046,597 B**.
  Every file was downloaded by the committed `stage_models.py` from
  `https://huggingface.co/<repo>/resolve/<revision>/<file>` and its size+sha256 checked against the registry;
  `MODELS_SHA256SUMS` (sha256 `9926d152b12e34dd74d4394f3b1e58c06be3fb818ec628fd79595c3c7c2531cd`) lists all 53.
  Pinned revisions include `jaredpalmer/kev-0.8b@788ddbdd6571`, `kev-4b@591dcb5bd6d0`,
  `Qwen/Qwen3.5-0.8B-Base@dc7cdfe2ee41`, `Qwen3.5-4B-Base` (registry).
- **Sweep-2 train/dev release** (the SFT source; `sweep2_only` per PRE-SELECT): receipt
  `de95b218486e39369f5143637de904d1f73ae18c13d31a9a1aebaa4072ed2d9c` and
  `label_block.traindev.jsonl` sha256 `7487b627e40edae37022f4467a60867b09bdbd395e61caa20302c090d8e5fe82`
  (1,272 released train+dev rows; `counts.evaluation_rows=0`; `inputs.proposals_sha256=379b17ca…`).
  Copies are under `releases/sweep2/` and the receipt copy is in this branch. **No test/ or evaluation partition was
  copied.**
- **v2.2 GPU image**: pre-pulled to ceph as an Apptainer SIF:
  `images/r1-htc-gpu-v22.sif` (5,460,717,569 B, sha256
  `331e0ca2617b747e13326a026410b7f2033df956103befd54a69249f16e8a1c5`).
  **Node-side pre-pull is not possible right now:** the pool advertises **0 NEMO2 H200 slots** at the sample
  (`condor_status` H200 count = 0), so there is no node cache to populate without submitting a job; HTCondor will
  pull the docker digest when capacity returns. The SIF is a ceph fallback/artifact, not a claim that nodes hold it.
- Staging root sizes: models 11.3 GB, image 5.1 GB.

## 2. CPU-only dry run (no GPU)

On deepthought, current main `5d4f1b09`:
```
pytest -q r1/tests/test_c3_arms_constants.py r1/tests/test_c3_arms_eval.py r1/tests/test_c3_direct_arms.py
→ 33 passed in 89.5 s
```
These are the arms/freeze-adjacent tests present on current main; they do not need a GPU.

P.4 runner tests exist only on the Mac branch `mac-trackp-p4-runner-20261122` @ `7ab79a9d`, not on main `5d4f1b09`.
Run read-only inside the pulled v2.2 image (CPU, `--writable-tmpfs`, harness bound; pytest installed into the throwaway
overlay):
```
pytest -q r1/tests/test_trackp_p4_runner.py
→ 74 passed in 32.1 s
```
They cover the env3-freeze rule (R1-TRACKP-V21-FREEZE), host-config paths/staging checks, synthetic test path,
render/switch and cap logic, all with synthetic fixtures. **They do not need a GPU, but they are not on main**;
they will run on main once the Mac P.4 units land.

Still needing the Mac units (and then a real H200 job):
- the P4 runner module/tests themselves on main;
- a launch-ready `p4_spec.json` (today TODO: paper commit, v2.2 digest/VERSIONS sha, host-config sha, partition/
  receipt/freeze record, probe estimate);
- real cluster checks: env3 freeze in the actual job, host-config local paths, 4B staging/transfer, synthetic test
  path with a real base, and `out.tar` transfer/seal.

## 3. PROVISIONAL evidence-phase cost projection (separate from phase 1 / its 40 GPU-h cap)

Measured inputs (v2.2):
- smoke **759997**: wall 585 s, peak `MemoryUsage=12,208 MB`.
- E0 **760000**: wall 1,393 s, peak `MemoryUsage=9,766 MB`, max_steps=2,000 (`kev-0.8b`).

Proxy step time for 0.8B: lower `(1393−585)/2000 = 0.404 s/step` (subtract smoke startup); upper `1393/2000 =
0.697 s/step` (all wall as steps). 4B scaled ×8 (P4 draft) → **3.23–5.57 s/step**. Startup/staging per job proxy:
**585–1,393 s**.

Fold count: 7 LONO + up to 3 LOSO = **10 folds** (ARMS-A5FOLD A); candidate set per fold = pool × Kev base =
**4 runs/fold** → **40 training runs**, plus **11 A5 test-scoring jobs** (primary + 10 folds). Steps per run from
SFT config (5 epochs, effective batch 16): sweep1 train 593 → ~190 steps; sweep2 train 850 → ~270; pooled 1,443
→ ~455; use **190–455 steps/run**.

| Component | Low | High |
|---|---|---|
| 20 × Kev-0.8B fold runs | 3.7 GPU-h | 9.5 GPU-h |
| 20 × Kev-4B fold runs | 6.7 GPU-h | 21.8 GPU-h |
| 11 test-scoring jobs (overhead proxy) | 1.8 GPU-h | 4.3 GPU-h |
| **Total, 10 folds** | **≈12 GPU-h** | **≈36 GPU-h** |

If only the 7 LONO folds are run (no LOSO), the range is **≈9–26 GPU-h**. Peak-memory observations are only for
0.8B (12.2 GB smoke, 9.8 GB E0); the 4B peak is not measured. **Final figures must come from the SFT probe** and
be reported to the author before the evidence-phase note is signed. This note is separate from phase 1 and its
40 GPU-h cap.

## 4. H200 queue / fair-share at the sample
- `condor_status` advertises **0 NEMO2 H200 slots** now; no node-side pre-pull possible and no immediate capacity
  for the probe/cluster tests.
- `condor_userprio` at the sample did not expose a dwong GPU fair-share entry; recommend checking again when H200
  returns.
- Concurrency recommendation remains **N=2** when capacity returns (one 0.8B + one 4B), until the SFT probe numbers
  justify a larger N.

## 5. Status
All 1–3 prepared; no GPU job submitted; no main push. Awaiting the Mac P.4 units/spec/note and H200 capacity.
