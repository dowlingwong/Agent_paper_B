# D.3 single-GPU HTCondor preflight — capacity finding (task `compute/20261127-12`)

**Result: BLOCKED, no match.** Two ENGINEERING_ONLY jobs were submitted with the intended D.3 request shape and
neither could run: the ETP L40S slot is administratively closed (`Start = false`), and the only TOpAS A100 parent
with free GPUs is also `Start = false`; the other A100 parents have no free GPU. No container was started and no
input was read inside a job. This is a capacity finding, not a STOP of evidence and not the D.3 per-arm smoke.

- **Base:** `origin/main` `e153df24ee3435bbe0b2fa994297b15250550c30`
- **Branch:** `compute-preflight-blockers-20261127`
- **Submitted from:** deepthought, `dwong`, 27 Nov 2026 04:07–04:10 UTC
- **Request shape (both jobs):** 1 GPU, 8 CPUs, 131,072 MB, 150,000,000 KB disk, `+RequestWalltime = 3600`,
  `universe = container`, image `ghcr.io/dowlingwong/r1-htc-gpu@sha256:49dd9900e0bbb004fe1f45573583cf0cffeb9fe3d98f0ef6d3aa16fb4fe75949` (v2.2).
  No request value was edited to get a slot.

| Job | Target | Outcome | Submit record |
|---|---|---|---|
| `760148` | ETP `NVIDIA L40S` | Idle, no match: the L40S slot has `Start = false`; removed | `captures/preflight.submit` |
| `760149` | TOpAS `NVIDIA A100-PCIE-40GB` | Idle, no match: no runnable A100; removed | `captures/preflight_a100.submit` |

## Evidence

- **deepthought2 L40S** (`slot1@deepthought2.etp.kit.edu`): `State = Unclaimed`, `Activity = Idle`,
  `GPUs = 1`, `GPUs_DeviceName = "NVIDIA L40S"`, `GPUs_GlobalMemoryMb = 45468`, driver 570.211.01,
  capability 8.9 — but `Start = false` (`captures/l40s_slot_ad.txt`). `condor_config_val -startd START` on
  deepthought2 prints `False` (`captures/startd_START.txt`). Job 760148 therefore had no machine willing to run
  it (`captures/condor_q_better_analyze.txt`, `captures/condor_q_reverse_l40s.txt`).
- **TOpAS A100** (`c03-001-167/175/179`): `167` and `179` advertise A100-PCIE-40GB but have `GPUs = 0` free;
  `175` has 5 free GPUs but `Start = false`/`Requirements = false`
  (`captures/topas_gpu_slots_start.txt`). The other TOpAS GPUs are Tesla V100S-PCIE-32GB, outside the card the
  task names.
- **ETP pool:** 22 visible slots, no H200/H100/A100; the committed H200 request `760065` remains Idle. The two
  TITAN X slots are on deepthought; no L40S or A100 was runnable.
- **Active jobs seen before submitting** (not ours, not touched): `760142`, `760143`, `760145`, `760147`
  (`lucid_torch_job.sh`, running on TOpAS A100 `c03-001-179`/`167`), plus idle `759624`, `759625`, `760065`
  (`captures/condor_q_all.txt`, `captures/condor_q_run.txt`).
- **Inputs:** transferred by HTCondor file transfer (TOpAS has no ETP `/work` or `/ceph`) and hashed on the submit
  side; they were **not** read inside a job because no job started:

| Input | sha256 |
|---|---|
| `trackp_ada_v1.json` | `c249b27e57466181618c57562f956e6c1adfced9fb2534bd747ede0b190695e5` |
| `p4_probe_spec.json` | `45ac32a50b4d1de826c94800907049c45426505ad06c193dd3b632cba9039d9e` |
| `D3_PREDECL_R4_20261127.md` | `68f56dc2cb4768ca1729486510c695870aa8e19a08e0194ef99f3b835c3d5001` |

All inputs are approved non-sealed files. The container digest is pinned; it was not pulled because no job started.

## What remains unverified

Scheduler match, container start, GPU identity inside the container, and in-container input hashes. The next attempt
needs one runnable L40S or A100 slot; the request must not be edited to obtain one. The D.3 per-arm smoke stays
behind its own G1/G6, constants and runner checks.

**Decided alone:** to use the same request shape for both allowed cards; to treat the second (TOpAS) target as the
task's alternative after the L40S slot refused, not as a relaxed request; to remove both idle jobs after capturing
their analysis; to leave the foreign `lucid` jobs and `760065` untouched.

**Needs:** a later retry when a runnable L40S or A100 appears; the coordinator's queue should still treat
`compute/20261127-12` as blocked, not done.
