# Ada P.4 host-config fill — `trackp_ada_v1.json` filled from the host

**Status:** DELIVERED for independent tier-E review, 27 Nov 2026. ENGINEERING_ONLY; no probe, no SFT, no evidence
training, no label read. Task `compute/20261127-18` (with `compute/20261127-13`).

- **Branch:** `compute-p4-ada-hostconfig-20261127`
- **Base:** `origin/main` `66cc33f2` (the merged Ada venv launcher)
- **Config:** `r1/scripts/configs/trackp_ada_v1.json` sha256
  `bb0c7251a5d47e04e82e33c738160be317bfbf59984b82a0d611b0798c4fa908`
- **Fill input:** `docs/r1/reports/trackp_p4_20261127/ADA_HOST_FILL_20261127/host_fill.json` sha256
  `ec42f76d0e01bb15ab450e74a820e7587894090df34399c86dd25332345a1ca9`
- **Host check:** `.../host_check.txt` sha256 `516fea06…`; **check-config:** `.../check_config.json` sha256
  `34748ceb…`
- **Review:** `compute-p4-ada-hostconfig-review-20261127` @ `f173ede7` — **`Verdict: ACCEPTED`** (two non-blocking
  prose minors: the old `experiment_zhixu` name in the config comment and the legacy `venv.path`/3.12.15 line; the
  runtime uses `direct.venv` 3.12.10).

## Host facts (Ada, `ssh ada_server`, 27 Nov 2026 05:22 UTC)

| Fact | Value |
|---|---|
| Account | `zli538` (uid 1008); the author's approved Ada account |
| Hostname | `ucrtasl` |
| Interpreter | `/data1/zli538/paperb_p4_20261127/venv/bin/python`, Python 3.12.10 |
| `uv` | `/home/zli538/.local/bin/uv`, version 0.7.8 (the venv's tool path; not on `PATH`) |
| Torch / CUDA | `2.6.0+cu124`, CUDA 12.4, `cuda.is_available() == true` |
| `causal_conv1d` | 1.7.0, built from the pinned sdist for sm_89, wheel sha256 `8f676dbd…` |
| Driver | 545.23.08 |
| GPUs | 8 × RTX 6000 Ada 48 GB; cards 0, 2, 6, 7 empty (5 MiB used), cards 1, 3, 4, 5 shared by another user (~33.7 GB each) at this sample |
| Disk | `/data1` 2.1 TB free (69 % used) |
| New directories | `/data1/zli538/paperb_p4_20261127/jobs` (0700); `/data1/zli538/r1_locks` (0700) |

The venv, freeze and smoke are the record `docs/r1/reports/trackp_p4_20261127/ADA_P4_VENV_20261127.md` (review
`ADA_P4_VENV_REVIEW_R2_20261127.md`, ACCEPTED). This fill does not rebuild or change the venv.

## Fill

Command (from the branch base, dry run then write):

```
python3 r1/scripts/htcondor/trackp_p4/p4_fill_host_config.py \
  docs/r1/reports/trackp_p4_20261127/ADA_HOST_FILL_20261127/host_fill.json \
  --host-class ada_rtx6000 --config r1/scripts/configs/trackp_ada_v1.json
```

The fill replaced exactly the 26 `TODO_VERIFY_ON_HOST` values and reported `placeholders_left: []`; then
`python -B r1/scripts/trackp.py --config r1/scripts/configs/trackp_ada_v1.json --check-config` returned
`placeholders: []` and config digest `098123e3…` (the digest `--check-config` prints is **not** the file sha256; the
file sha used by the spec/note is `bb0c7251…`).

| Value | Filled |
|---|---|
| `work_dir` | `.` (job-relative) |
| `models_dir`, `hf_home`, `runs_dir` | `models`, `hf`, `out` (forced, job-relative) |
| `gpu.name`, `gpu.compute_capability` | `NVIDIA RTX 6000 Ada Generation`, `8.9` |
| `gpu.lock_path` | `gpu0.lock` (job-relative) |
| `bases.*.local_path` | `models/<registry key>`; the four unused bases use their suggested paths |
| `venv.path` | `/opt/r1/envs/trackp` (forced env3 path; the Ada venv route uses `direct.venv.python`) |
| `venv.causal_conv1d` | `1.7.0 … wheel sha256 8f676dbd…, R1-TRACKP-IMAGE-V22-B; imports on the Ada venv` |
| `direct.container_runtime` | `venv` |
| `direct.ssh_alias` | `ada_server` (the working route; the fill accepts this Ada alias) |
| `direct.hostname` | `ucrtasl` |
| `direct.work_root` | `/data1/zli538/paperb_p4_20261127/jobs` |
| `direct.lock_dir` | `/data1/zli538/r1_locks` |
| `direct.shm_size` | `16g` (docker-only; recorded) |
| `direct.min_free_mib` | `46000` (one empty 48 GB card before the probe, R1-CARD-SHARE (1)) |

## Tests

The fill makes the committed config a filled file; the P.4 tests that need a template now restore the 26 placeholders
in a copy (`_ada_template()`), and the shipped-config placeholder assertion checks that copy plus the filled file:

- `r1/tests/test_trackp_p4_direct.py`: **45 passed** (includes the fill hook's 26-value form, refusals, the Ada venv
  path and the direct descriptor).
- `r1/tests/test_trackp_p4_runner.py`: **159 passed**.
- `r1/tests/test_trackp_sft.py` + `r1/tests/test_trackp_cli.py`: **35 passed, 9 skipped**.
- No test assertion was relaxed; the fill tests still require the 26 values and every refusal.
- Full `r1/tests` with `--continue-on-collection-errors`, harness `9bb41680`, Python 3.12.8, pytest 9.2.0:
  base `98c571d2` **108 failed / 4914 passed / 161 skipped / 3 errors**; tip `77e364e7` **108 / 4918 / 161 / 3**;
  the 111 sorted FAILED/ERROR ids are identical (sha256
  `971166036fa365bcb10f01f051c756a7b90c1e94e0b0c1637bedcbd28b7c1f19`); **+4 passed (the venv merge's tests), zero
  new failures**. The branch base `66cc33f2` adds the reviewed Ada venv launcher on top of that baseline.

## What this does not do

- No synthetic-label probe, no SFT and no evidence training. The probe waits for this fill's merge (the task says
  "after that merges").
- No `sudo`, no system package, no other user's file or process touched; the two new directories are under our account.
- No change to the venv, the image, the package lock or the fill script.

## Decided alone

- To use `direct.ssh_alias = ada_server`, the route that actually reaches Ada as `zli538` (the fill script permits it
  for the Ada class; `experiment_zhixu` resolves to another user and is not our route).
- To place `work_root` and `lock_dir` under `/data1/zli538/paperb_p4_20261127` and `/data1/zli538/r1_locks`, both
  created 0700; `/data1` has 2.1 TB free.
- `direct.min_free_mib = 46000`: one empty 48 GB card before the probe; after the probe the peak memory plus headroom
  replaces it, as the fill template says.

## What happens next

1. Independent tier-E review of the fill and its host check.
2. Coordinator merge of `compute-p4-ada-hostconfig-20261127`.
3. `compute/20261127-18` probe: one empty RTX 6000 Ada card (0, 2, 6 or 7 at this sample), the synthetic-label probe
   under R1-P4-TESTPLAN-DECISIONS, recording each base's peak GPU memory, timing and the probe charge; then the
   phase-1 note can cite the actual runtime.
