# Ada P.4 4B re-probe with activation checkpointing (`compute/20261127-24`): both 4B arms PASS

**Result: PASS.** `kev-4b` and `qwen3.5-4b-base` both ran the 50-step synthetic `sft-dev` probe on an empty
RTX 6000 Ada card with micro-batch 8 and gradient checkpointing on (R1-P4-4B-CHECKPOINT), rc 0, no STOP. The
launch-verified peaks are **14,135 MiB** and **16,959 MiB** (the earlier OOM runs reached 48,385 / 48,399 MiB),
and the measured wall times are 10.0458 and 9.9981 s/step. The combined probe record now gives the Ada class
an estimate for all four bases; the probe charge is **3.10 GPU-h** against phase 1's 40 (a reporting
threshold). ENGINEERING_ONLY: no SFT evidence run, no label, evaluation, test or sealed read.

- **Task:** `compute/20261127-24`; PLAN **R1-P4-4B-CHECKPOINT** (author, 27 Nov: "签 P4-4B A"),
  R1-P4-TESTPLAN-DECISIONS (P4-PROBE A, P4-PROBECAP A), R1-P4-PROBE-CHARGE, R1-HOST-FREE, R1-CARD-SHARE,
  R1-NO-TIMEOUT.
- **Base / branch:** `origin/main` `e92f3c7389e06347a0ff78f5f68971024133c670` (the checkpointing merge);
  branch `compute-p4-4b-reprobe-20261127`.
- **Spec:** `p4_probe_spec_ada_b.json` sha256
  `7181ebc555c4484c477d74824a6109aa96c5a7f87a557cd266e50ebd4733e45f`. It is the committed
  `p4_probe_spec.json` template at `e92f3c73` with only its five filled fields (`paper.commit` `e92f3c73`;
  `image.versions_sha256` `aaa1a304…`; `host_class` `ada_rtx6000`; `hosts.ada_rtx6000.host_config.sha256`
  `bb0c7251…`), the re-probe run id `trackp-p4-probe-20261127-b`, and the published `ada_4b_reprobe`
  binding (`prior_run_id` `trackp-p4-probe-20261125-a`, prior spec `540bd979…`, prior commit `91cfd48a…`).
  `validate --probe` rc 0; `check_probe_template` and `check_probe_binding` passed at staging (the latter
  binds the code files and host config to `paper.commit` on published `main`). The prior `kev-0.8b`
  first-arm seal `3d9af7d2…` is bound in both stages.
- **Stages:** `stage_kev-4b.json` sha256 `53feff7b…` (receipt `stage_manifest_sha256` matches),
  `stage_qwen3.5-4b-base.json` sha256 `50a06257…`; inputs `proposals.jsonl` `d0048567…`, `configs.json`
  `b585b727…`, `build.json` `7f56619c…`.
- **Host / runtime:** Ada (`ucrtasl`), account `zli538`, 8 × RTX 6000 Ada 48 GB, driver 545.23.08, one
  empty card per job (kev-4b card 0, qwen3.5-4b-base card 2; `card_shared=false`, other-process count 0 at
  start and end), through the reviewed direct launcher's venv runtime (Python 3.12.10, torch 2.6.0+cu124,
  freeze sha256 `50238e5a…`, 121 lines). No image was executed (`image_executed=false`); the image VERSIONS
  pin is the note's `aaa1a304…`.

## Results

| Arm | Attempt | Result | Peak device memory | Wall s/step | Steps | Charge (GPU-h) | Estimate for full SFT |
|---|---|---|---|---|---|---|---|
| `kev-4b` | 1 | PASS (rc 0) | 14,135 MiB | 10.0458 | 50/50 | 0.4474 | 6.79 h |
| `qwen3.5-4b-base` | 1 | PASS (rc 0) | 16,959 MiB | 9.9981 | 50/50 | 0.4833 | 6.75 h |

For comparison, the carried 0.8B first-arm records (prior run, unchanged) are `kev-0.8b` 25,939 MiB / 3.7188
s/step / 0.1231 GPU-h and `qwen3.5-0.8b-base` 27,271 MiB / 3.7055 s/step / 0.4511 GPU-h. All four arms have
`effective_batch=16`, `micro_batch=8`, 50 steps, synthetic labels and `n_train=593`; checkpointing is `true`
on exactly the two 4B arms and `off (SFT path)` on the 0.8B arms. `fit_and_timing_reliable: true`.

## Probe record and charges

`probe_records.json` sha256 `62a92d716ce8a000e72c11930f3cd7cbbab976417eaef7fb3f88a5b2d9efcb81`. It is the
`trackp_p4_h200_sft_probe/1` record built from the first sealed, verified, STOP-free attempt of each arm in
submission order (the two 0.8B attempts carried from the prior run; the two 4B attempts from this run), with:

```
p4_probe_host_class: ada_rtx6000
p4_estimate_hours: kev-0.8b 2.52
p4_estimate_hours: kev-4b 6.79
p4_estimate_hours: qwen3.5-0.8b-base 2.51
p4_estimate_hours: qwen3.5-4b-base 6.75
p4_probe_gpu_hours: 3.10
p4_probe_charge_file: trackp-p4-probe-20261125-a _wallclock.json 9a1949a1…
p4_probe_charge_file: trackp-p4-probe-20261127-b _wallclock.json fa49096f…
```

- `probe_gpu_hours_charged = 3.091` (every probe attempt, STOPs and repeats included) + T1 `0.0` → rounded up
  to **3.10**. The prior run's charge file was created by this record (it had none; the earlier record was
  refused at the 4B OOM). The new run's charge file holds `kev-4b 0.4474` and `qwen3.5-4b-base 0.4833`;
  both are copies in `charge_files/`.
- Projection: `total_gpu_hours 20.57` (all four arms) with `probe_gpu_hours 3.10`; `total_with_probe_gpu_hours
  23.67`; slot hours 29.855; `within_cap: true` against 40 GPU-h / 64 slot-h. `probe_over_2_gpu_h: true` is a
  reporting flag, not a refusal (P4-PROBECAP A; the probe counts against the 40).
- The record's `harness_commit` finding from the prior review still stands: the synthetic `sft-data` step
  imports the harness and the SFT manifests record `897d83c8…`; the phase-1 note's `harness_commit: none`
  must be settled (note line or a reviewed runner change).

## What the phase-1 note needs

1. `ada_sft_probe:` record `docs/r1/reports/trackp_p4_probe_ada_20261127b/P4_ADA_4B_REPROBE_20261127.md`
   with the four `p4_estimate_hours` lines above; the Ada class now has an estimate for every base.
2. `p4_probe_gpu_hours: 3.10` (the note's `gpu_hours_cap:` line), and the two charge-file hashes.
3. The 4B fit decision is resolved on Ada: activation checkpointing at micro-batch 8 fits both 4B arms on an
   empty 48 GB card with wide margin (headroom 0.7124 and 0.6549 of the card), so no H200 route is needed for
   these two arms.

## Decided alone

To run the two arms concurrently on two different empty cards (one job per card; R1-HOST-FREE, R1-CARD-SHARE)
rather than serialize them, because both cards were empty and each job keeps its own lease; to use cards 0
and 2; and to seal each attempt before building the combined record. No spec, seed, micro-batch, assertion,
reviewed file or label was changed; no retry was needed.

**Task id:** `compute/20261127-24`. **Branch/tip:** `compute-p4-4b-reprobe-20261127` (the tip is named in the
`coord/compute` report). **Tests:** `validate --probe` rc 0; both jobs rc 0; both seals verify (`SHA256SUMS`,
`identity_verified`); `probe-record` rc 0 with `fit_and_timing_reliable: true`. **Next:** fresh tier-E review
of this record and the probe record, then the coordinator merges and the phase-1 note is updated.
