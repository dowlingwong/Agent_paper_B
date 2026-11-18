# Image v2 I2 CPU determinism

**ENGINEERING_ONLY. I2 PASS.** HTCondor job `5045197.0` ran on `slot1_3@ms02.etp.kit.edu` and finished at 00:24:29 UTC on 18 November 2026 with exit 0. The job ran two serial pytest invocations in separate job-scoped scratch directories against the pinned synthetic worker fixture. Each invocation passed and produced exactly two worker logs.

| Check | Result |
| --- | --- |
| CPU image | `ghcr.io/dowlingwong/r1-htc-cpu@sha256:08a36eff19718b439574829e37c84b865c7df74a1e12fba5228cd06236d7a5bb` |
| Paper and harness | `60ecf1dae299ee424aa1bdfe078eab02a881b87e` and `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` |
| Worker metrics | 4/4 `val_score=0.922225` and 4/4 `train_loss=0.314016` |
| Worker log SHA-256 | All four match the v1 reference `0f4419b6010451339461a941e80262c7c5005a23716e40577176b3afa4ae1d94` |
| Retained evidence | `/ceph/srv/dwong/paperb/trackp-v2-20261118/i2_5045197` with verified `SHA256SUMS` |
| Raw worker logs | `/work/dwong/paperb/work/s4_5045197.0_20261118T002411Z/pytest_{1,2}/` |

The v2 CPU digest was already built and published by Actions as recorded at `cbd0238e`. The job reused the I2 worker test from the earlier chain, isolated the code via `git archive`, moved fixture scratch under the job-specific output directory, verified both checkout pins and required two logs per invocation. It omitted the unrelated S6 XRootD probe. The scheduler dry-run accepted the reviewed script and JDL with SHA-256 `c963f6960253c9920cad87e333f57fca0a454e4959b66257060c905dc6e720fe` and `fde29f60a3d3540fe8bfbe3ed16d9562cc6bbdca426eb7327cc4ed2eacbe9de0`, respectively. The pre-submission review is in `docs/r1/reviews/TRACKP_V2_I2_I3_PRE_SUBMIT_REVIEW_20261118.md`.

Authority is published PLAN R1-QTORCH-AMEND and R1-HTC-QTORCH. I2 establishes reproducibility for the pinned CPU fixture. The GPU image I3 serving and offload checks, H200 Track P smoke, and the E0 equivalence run each have their own result and review gates.
