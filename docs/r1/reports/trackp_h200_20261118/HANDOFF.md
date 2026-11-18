# Image v2 and H200 Track P handoff

| Unit | Status | Evidence or next gate |
| --- | --- | --- |
| Image v2 | Published by Actions | Tag `20261115-v2-e1cb6d8e`, source report at `htc-image-v2-20261115` `cbd0238e`. GPU digest `b1144ecec7ffe07642ff108fb9624aa34775cb873ed17f835ea3e3c87bc024fd`. CPU digest `08a36eff19718b439574829e37c84b865c7df74a1e12fba5228cd06236d7a5bb`. |
| I2 CPU | PASS, ENGINEERING_ONLY | Job `5045197.0`, all four v1 reference worker log hashes verified. See I2_V2_RESULT.md and its independent review. |
| I3 NEMO2 L40S | Preserved on operator hold | Job `5045198.0`, portal1 schedd, stage `/work/dwong/paperb/work/trackp-v2-20261118.e5GVGU/i3_nemo2`. At fallback the job was idle with zero starts and zero NEMO2 L40S matches. |
| I3 TOpAS V100S | Queued, ENGINEERING_ONLY | The user authorized the TOpAS option while NEMO2 was unavailable. Job `5045199.0` passed scheduler dry-run and entered the portal1 queue after job `5045198.0` was held. At 01:33:26 UTC, it had zero starts and zero matching V100S slots. The V100S probe covers image and llama-server functionality. |
| H200 Track P smoke | Staged, independently reviewed, scheduler dry-run PASS | Use v2 GPU image and paper D `8662e35991659f7a661fb7ed6be4980791d302f3`. Submit after completed v2 I2/I3 and independent review. |
| H200 E0 | Staged, independently reviewed, scheduler dry-run PASS | The preregistered TASL-7 Kev-0.8B DRYRUN config and comparison tolerances carry forward, with exact historical code and host paths relocated. Submit after an accepted H200 smoke. |

Authority is R1-QTORCH-AMEND and R1-HTC-QTORCH on published main. The operating sequence is v2 I2 and I3, then H200 Track P smoke, then the E0 host-equivalence check. Track P Unit B and attempt-1 artifacts remain in the experiment agent's scope. The branch carries preparation and the I2 result. A successful validation of the H200 stages requires allocated device identity, scoped NVML process checks, locked TORCH/registry inputs, and both runtime result reviews.

The staged jobs and expected hashes are in `stages/`. H200 scheduler dry-runs are at `/work/dwong/paperb/work/trackp-h200-dry-20261118.BySvEJ`. I3 adds a verified model alias, a short completion with cache disabled, a positive GPU layer-offload requirement and a bounded FP32 CUDA matmul diagnostic. The H200 stages scope the historic lease's compute query to the sole assigned GPU UUID. Their scientific comparator and runner bytes remain pinned. The smoke checks installed fast kernel bindings as well as numeric passes. E0 hands back both prediction arrays and the training traces for independent recomputation.

The fallback submission record is in `/work/dwong/paperb/work/trackp-v2-20261118.e5GVGU/i3_topas/` on portal1. The v2 image and staged script/JDL hashes matched the independent pre-submission review. H200 smoke and E0 depend on the runtime I3 result and review.
