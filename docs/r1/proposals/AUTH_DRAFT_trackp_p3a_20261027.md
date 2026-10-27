# Authorization: Track P P.3a (label-free decision-model exam) — 27 October 2026

**Author:** Dowling Wong. **DRAFT.** Drafted by the coordinating session (Claude) at the author's request. It authorizes nothing while it sits in `docs/r1/proposals/`; it becomes valid only when the author commits it (or explicitly instructs a commit on their behalf) as `docs/r1/authorizations/trackp_p3a_<date>.md`.

## What is authorized

Evidence runs of **P.3a** as defined in `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md` Phase 5 and `docs/r1/TRACK_P_POST_TRAINING.md` §5.5–§5.6, with the evidence label `EVIDENCE`:

- **E0 aleatoric pass-through** on the committed synthetic set `r1/c3/train/data/e0_v1.jsonl.gz` (sha256 `4f4db29b6a4c0ca0181825e5c2c0fb031521e034a006990b93686cd5fffc8290`), soft labels, with the hard-label contrast, under R1-E0-PROTOCOL (v2: slopes against the label's own std; validation cells held out of the training grid), R1-E0-BUDGET (lr screen on {1e-5, 3e-5, 1e-4} at ≤ 2,000 steps by val RPS, then one run at the selected lr, cap 6,000 steps, evaluation every 100, patience 10; E0 metrics from that run), R1-E0-HEADFIT (head fit descriptive only, L-BFGS on cached frozen features; LoRA starts from the fresh head) and R1-TRACKP-CHOICES (selected lr reused for the hard-label and native runs).
- **E6 architecture probes** A1–A5 under R1-A3-BUDGET and R1-CONTROL-READOUT (A5 descriptive only).
- **Candidates:** every base that passed P.0 per `r1/c3/train/registry.yaml`: `kev-0.8b`, `kev-4b`, `qwen3.5-0.8b-base`, `qwen3.5-4b-base` (control, carried regardless of E0), `laya`, `startlux-0.8b`, `startlux-2b`, `startlux-4b` (R1-STARTLUX-TRAINABLE).
- **Pass rule:** R1-E0-THRESHOLDS as frozen in `r1/c3/rules/p3_rule_v2.yaml` (sha256 `8c0ef9089589eafcea04aea9c5936c7ab57625d19f2a7ab736de204d09840242`): width slope vs label std ≥ 0.6 with bootstrap 95 % lower bound > 0, mean slope ≥ 0.8; A4 monotone on ≥ 95 % of prompts. Models failing E0 are disqualified from P.3b except the Qwen control, which is carried as the ablation arm.

## Conditions

- **Host:** TASL-7 only (R1-TASL7-TRACKP). No reboot is required (the author has no root); every job records `uptime`, `/proc/driver/nvidia/version` and the `nvidia-smi` driver version in its manifest; a driver/library version mismatch, an `nvidia-smi` failure, or an unplanned reboot is a STOP (completed units are kept; an interrupted unit is re-run whole). Use the GPU lease (`flock ~/r1_locks/gpu0.lock`). No portal, no Ada, no API calls.
- **Host check (27 Oct 2026):** loaded NVIDIA module, `nvidia-utils-580` and `libnvidia-compute-580` are 580.178.04; `nvidia-smi` reports 580.178.04 and works. `Automatic-Reboot` has no active setting in the checked apt configuration or `apt-config dump` (the `false` example is commented); `20auto-upgrades` enables periodic package-list updates and unattended upgrades. Pending Linux images do not alone block P.3a under the author's correction.
- **Pins:** the run venv whose freeze equals the recorded portal freeze (torch 2.6.0+cu124); model revisions and file hashes as in the committed registry; harness `897d83c`; code at the head of `trackp-20261026` at launch, recorded in every manifest with host and GPU UUID. A pin mismatch is a STOP.
- **Order:** first one model (`kev-0.8b`) end to end as a DRYRUN under the final code, then all candidates as EVIDENCE. The protocol, thresholds and rule file are not changed after the first evidence result.
- **Budget:** at most **60 GPU-hours** in total for P.3a. Reaching 45 GPU-hours with candidates outstanding is a STOP with a report.
- **STOP conditions:** OOM or CPU fallback that persists after the runbook's engineering attempts; any non-finite metric; a pin mismatch; budget as above; anything that would change the protocol.
- **Review:** the independent review loop of the runbook (the reviewer recomputes slopes, bootstrap bounds and pass/fail from the run outputs and checks the rule hash).

## Not authorized by this note

P.3b and any use of audited labels; P.4 and later stages; Jev or DeepSeek API calls; any change to `p3_rule_v2.yaml`, the E0 set or the thresholds; runs on any host other than TASL-7.
