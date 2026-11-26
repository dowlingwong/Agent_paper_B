# Independent result review for image v2 I2

_Paper B R1, 18 November 2026. HTCondor job `5045197.0`._

---

**ACCEPTED — I2 PASS (ENGINEERING_ONLY).** The approved v2 CPU image reproduced the pinned synthetic tabular worker fixture. Both serial pytest invocations passed. Each produced two recorded worker logs, and all four metric pairs and independently recomputed worker-log SHA-256 values match the archived v1 I2 reference. I found no blocking result discrepancies. The verdict covers the I2 CPU fixture under PLAN R1-QTORCH-AMEND and R1-HTC-QTORCH.[^plan][^v1][^bundle]

| Check | Evidence |
| --- | --- |
| Evidence integrity | I ran `shasum -a 256 -c SHA256SUMS` on the exact retained bundle snapshot. All 14 entries verified. Manifest SHA-256 is `d9f9be38c4d2f22960fc87386e56c73c6d57837f0c0c706137d67c0afd2c6dc1`.[^bundle] |
| Reviewed submission | The retained wrapper and JDL hashes match the final pre-submit review, `c963f6960253c9920cad87e333f57fca0a454e4959b66257060c905dc6e720fe` and `fde29f60a3d3540fe8bfbe3ed16d9562cc6bbdca426eb7327cc4ed2eacbe9de0`. The dry-run ClassAd resolves to the wrapper in a fresh submit directory and retains ETP-local placement, the container constraints, and the configured transfer and resource settings.[^staging][^bundle] |
| Actual image and runtime | The worker-side job ad records `ContainerImageSource=docker`, `WantContainer=true` and the approved digest `08a36eff19718b439574829e37c84b865c7df74a1e12fba5228cd06236d7a5bb`. I rehashed the captured `/opt/r1/VERSIONS.txt` text and matched `identity.txt`. The harness interpreter reports Python 3.13.4, NumPy 2.4.4, scikit-learn 1.8.0 and pytest 9.0.3.[^plan][^build][^bundle] |
| Source and fixture | Both checkout-head checks and the archive identities record paper `60ecf1dae299ee424aa1bdfe078eab02a881b87e` and harness `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`. The verified wrapper archives those commits, sets OMP, MKL and OpenBLAS to one thread, clears CUDA visibility and runs the same fixture in separate scratch directories. Both raw pytest logs report the archived paper root and the exact test ID. The pinned test runs two worker trials with seed 7001 in each invocation. I reproduced the paper archive SHA-256 `f9d2813fa5a1654c7a0785c08738dd7c23d506f7e2a0c2c0cf90401ae9ace842` and matched the image version record's harness lock SHA-256 against `uv.lock` from the pinned harness commit.[^errata][^staging][^bundle] |
| Scheduler result | The event log records one execution on `slot1_3@ms02.etp.kit.edu` with zero GPUs, zero hold or eviction events and normal exit 0. On 18 November, the CET event timestamps yield submit 00:22:26 UTC, execute 00:23:39 UTC and termination 00:24:29 UTC. Wait was 73 s and elapsed execute-to-termination time was 50 s. Job stdout ends with `I2_PASS` and `S4_DONE … fail=0`. Job stderr is empty.[^bundle] |
| Reproduction | I independently parsed the v1 and v2 summaries. Both v2 pytest logs show one pass and the summary records exit 0 for each. Four distinct job-specific worker paths split 2/2 by invocation. I matched the four copied raw worker logs to those paths, checked both metrics directly, and rehashed each file. All four contain `val_score=0.922225` and `train_loss=0.314016`, and have the v1 worker-log SHA-256 `0f4419b6010451339461a941e80262c7c5005a23716e40577176b3afa4ae1d94`. The archived v1 job is `759693.0`.[^v1][^bundle][^raw] |

The review used the operator-provided bundle snapshot and copies of the raw v2 worker logs after direct Portal SSH failed DNS resolution. The archived v1 summary provides the reference hash. For precision, the result draft can call the two tests “serial pytest invocations in separate job-scoped scratch directories.”[^bundle][^raw][^v1]

[^plan]: Paper B `origin/main` at `50176481cbc85fb9e5b5dd97887043dea6e528fb`, `docs/r1/PLAN.md` §10 decisions R1-QTORCH-AMEND and R1-HTC-QTORCH.
[^build]: Paper B commit `cbd0238e3b91ac79f2fba3f381451d8d98ec8103`, `docs/r1/reports/htcondor_image_20261115/BUILD_V2_20261116.md`.
[^errata]: Paper B `origin/main` at `50176481cbc85fb9e5b5dd97887043dea6e528fb`, `docs/r1/prompts/HTCONDOR_PREP_RUNBOOK_20261114.md` §4.4 and `docs/r1/prompts/HTCONDOR_PREP_RUNBOOK_ERRATA_20261114.md` A2.
[^v1]: Paper B `origin/main` at `50176481cbc85fb9e5b5dd97887043dea6e528fb`, `docs/r1/reports/HTCONDOR_CHAIN_20261114.md` S4 and `docs/r1/reports/htcondor_chain_20261114/s4/out/s4_759693.0_20261115T002553Z/i2_summary.txt`.
[^staging]: `docs/r1/reviews/TRACKP_V2_I2_I3_PRE_SUBMIT_REVIEW_20261118.md`, final I2 re-review.
[^bundle]: Portal evidence `/ceph/srv/dwong/paperb/trackp-v2-20261118/i2_5045197`. Verified files include `SHA256SUMS`, `s4.log`, `s4.out`, `identity.txt`, `i1_envs.txt`, `probe.ad`, `probe.jdl`, `s4_run.sh`, `i2_summary.txt`, `i2_compare.txt` and `i2_run{1,2}.log`.
[^raw]: Four v2 `run.log` files copied from `/work/dwong/paperb/work/s4_5045197.0_20261118T002411Z/pytest_{1,2}/`.
