# D.3 single-GPU HTCondor preflight — capacity finding (task `compute/20261127-12`)

**Result: BLOCKED, no match.** Three ENGINEERING_ONLY submissions (two card targets; one A100 attempt was
superseded) used the intended D.3 request shape and none could run: the ETP L40S slot is administratively closed (`Start = false`); on TOpAS the parent with
the most free A100 GPUs (`175`, five) is `Start = false`, `167` has one free but `Start`/`Requirements` are
`undefined`/`error`, and `179` has none free. No container was started and no
input was read inside a job. This is a capacity finding, not a STOP of evidence and not the D.3 per-arm smoke.

- **Base:** `origin/main` `e153df24ee3435bbe0b2fa994297b15250550c30`
- **Branch:** `compute-preflight-blockers-20261127`
- **Submitted from:** deepthought, `dwong`, 27 Nov 2026 03:07–03:20 UTC
- **Request shape (all jobs):** 1 GPU, 8 CPUs, 131,072 MB requested (the job ad shows 131,100 MB, 28 MB above
  the request), 150,000,000 KB disk, `+RequestWalltime = 3600`, `universe = container`,
  image `ghcr.io/dowlingwong/r1-htc-gpu@sha256:49dd9900e0bbb004fe1f45573583cf0cffeb9fe3d98f0ef6d3aa16fb4fe75949` (v2.2).
  No request value was edited to get a slot. The two JDLs now pass the expected GPU name and capability to the
  same script, so the A100 leg checks A100/8.0 rather than the L40S/8.9 defaults.

| Job | Target | Outcome | Submit record |
|---|---|---|---|
| `760148` | ETP `NVIDIA L40S` | Idle, no match: the L40S slot has `Start = false`; removed | `captures/preflight.submit` |
| `760149` | TOpAS `NVIDIA A100-PCIE-40GB` | Superseded attempt: submitted before the identity arguments were separated (the script default was L40S); no queue capture was kept; removed | `captures/preflight_a100.submit` |
| `760152` | TOpAS `NVIDIA A100-PCIE-40GB` | Idle, no match: no runnable A100; removed | `captures/preflight_a100_fix.submit` |

`760152` is the corrected A100 leg; `760149` is retained as its superseded first attempt and is not evidence of a
valid A100 run.

The corrected A100 job `760152` was submitted at 2026-11-27T03:20:09Z and captured while idle: `JobStatus = 1`,
`RequestMemory = 131100`, no `RemoteHost`/`AssignedGPUs`. The `-better-analyze` output reports 0 of 23 slots
matching, but that query is against the **submit pool** (ETP/deepthought), which does not include the TOpAS
collector; the TOpAS evidence is the separate `condor_status -pool c03-001-140` capture. The two are not the same
slot set (`captures/condor_q_a100_fix.txt`, `captures/condor_q_better_analyze_a100_fix.txt`,
`captures/topas_a100_slots_fix.txt`).

## Evidence

- **deepthought2 L40S** (`slot1@deepthought2.etp.kit.edu`): `State = Unclaimed`, `Activity = Idle`,
  `GPUs = 1`, `GPUs_DeviceName = "NVIDIA L40S"`, `GPUs_GlobalMemoryMb = 45468`, driver 570.211.01,
  capability 8.9 — but `Start = false` (`captures/l40s_slot_ad.txt`). `condor_config_val -startd START` on
  deepthought2 prints `False` (`captures/startd_START.txt`). Job 760148 therefore had no machine willing to run
  it (`captures/condor_q_better_analyze.txt`, `captures/condor_q_reverse_l40s.txt`).
- **TOpAS A100** (`c03-001-167/175/179`): the parent slots advertise A100-PCIE-40GB. `167` shows 1 free parent
  GPU but reports `Start`/`Requirements` as `undefined`/`error`; `179` shows 0 free; `175` shows 5 free but
  `Start = false`/`Requirements = false`. None of the three is a runnable A100 target. Captured at 2026-11-27T03:20:09Z in
  `captures/topas_a100_slots_fix.txt`; the earlier undated capture is `captures/topas_gpu_slots_start.txt`.
  The other TOpAS GPUs are Tesla V100S-PCIE-32GB, outside the card the task names.
- **ETP pool:** 23 visible slots at the 760152 analysis, no H200/H100/A100; the committed H200 request `760065` remains Idle. The two
  TITAN X slots are on deepthought; no L40S or A100 was runnable. The dated ETP refresh is
  `captures/etp_gpu_slots_fix.txt`.
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

The transfer manifest `PREFLIGHT_INPUTS.sha256` is committed beside the script; the three hashes above are the
same values it lists, and the reviewer also checked them against `origin/main`.

All inputs are approved non-sealed files. The container digest is pinned; it was not pulled because no job started.
`preflight_a100_fix.submit` is the `condor_submit` output for `760152`; the earlier `preflight_a100.submit` names
the superseded `760149`.

## What remains unverified

Scheduler match, container start, GPU identity inside the container, and in-container input hashes. The next attempt
needs one runnable L40S or A100 slot; the request must not be edited to obtain one. The D.3 per-arm smoke stays
behind its own G1/G6, constants and runner checks.

**Decided alone:** to use the same request shape for both allowed cards; to treat the TOpAS target as the task's
alternative after the L40S slot refused, not as a relaxed request; to correct the A100 identity arguments and
resubmit once as 760152 rather than editing the request; to remove the idle jobs after capturing their analysis;
to leave the foreign `lucid` jobs and `760065` untouched.

**Needs:** a later retry when a runnable L40S or A100 appears; the coordinator's queue should still treat
`compute/20261127-12` as blocked, not done.
