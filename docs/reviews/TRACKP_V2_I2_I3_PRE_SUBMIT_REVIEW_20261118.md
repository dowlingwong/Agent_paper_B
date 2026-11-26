# Mission 3 independent review — HTCondor image v2 I2/I3 staging

**Final verdict: ACCEPTED for portal pre-submit checks.** The accepted file hashes and verification are in the two re-review sections below.

**Initial verdict: NOT ACCEPTED as staged.** I2 reproduces the v1 test and reference metrics. I3 can report PASS with zero GPU model layers offloaded, and the launch omits diagnostics named by the Mission 3 runbook.

**Inputs.** Local `origin/main` at `50176481cbc85fb9e5b5dd97887043dea6e528fb`, PLAN §10 R1-QTORCH-AMEND and R1-HTC-QTORCH, cluster prompt `e7e028ce` lines 69–74, HTCondor prep runbook §0.2 and §4.4 and errata A2/F18, v1 adapters and results in `docs/r1/reports/htcondor_chain_20261114/` and the 14 Nov chain report, v2 build report at `cbd0238e`, the v2 Dockerfile at `e1cb6d8e`, and the six staged files below. Checked shell syntax, executable permissions, staged-v1 differences and test source. The portal dry-runs and runtime checks are pending.

## I2 local CPU

- `i2/probe.jdl` pins the approved CPU digest `08a36eff19718b439574829e37c84b865c7df74a1e12fba5228cd06236d7a5bb` and retains the v1 local `TARGET.ProvidesETPResources` selector and resource requests. The operative I2 is the S4 synthetic-tabular CPU worker test. The v2 proposal calls it a tiny-llama CUDA probe, but its own pre-build review identifies it as the CPU S4 test, the invoking runbook identifies the pytest test, and the built CPU image omits llama-server and the Track P environment.
- `s4_run.sh` uses paper `60ecf1dae299ee424aa1bdfe078eab02a881b87e` and harness `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, with the same `test_real_worker_run_is_seed_deterministic`, harness environment, cleared CUDA visibility and one thread each for OMP, MKL and OpenBLAS. The test creates two worker runs per invocation with seed 7001. V1 I2 job 759693 retained four worker logs with `val_score: 0.922225` and `train_loss: 0.314016`. The staged script repeats the pytest invocation twice in separate job-scoped directories and compares all four values of each metric.
- Use the overall exit status together with `i2_compare.txt` to classify I2. As written, the comparison file can say PASS after a pytest exit failure because the parser sees only metrics. Check two successful pytest exits and two worker logs per invocation alongside the four exact matches. A measured difference goes in the report under §4.4 as a determinism finding.
- Source provenance needs a cleanup or an explicit record. The baseline runbook calls for exact archive copies. Use job-scoped archives from the verified commits or document reuse of the v1 pinned checkouts and verify their inputs. The new `git status` guard omits untracked files and treats a failed status lookup as clean. At minimum check status success and tracked cleanliness, and verify untracked inputs cannot enter the job. The v1 adapter also preserves I1 version records, an obsolete v1 local-SIF identity check, and the S6 XRootD readback. Retain the version and v2 OCI image identity records. S6 was outside this I2 rerun and timed out on v1. It contributes no I2 PASS signal.

## I3 NEMO2 L40S and TOpAS V100S

- Both JDLs pin approved GPU digest `b1144ecec7ffe07642ff108fb9624aa34775cb873ed17f835ea3e3c87bc024fd`. NEMO2 retains container universe, `BwForCluster-Nemo2` + `NVIDIA L40S`, and 30,000,000 kB disk. TOpAS retains Docker universe, `Tesla V100S-PCIE-32GB`, and 12,000,000 kB disk. One GPU and 3600 s per job match the v1 staging. V100S is valid for this I3 llama.cpp probe because this build includes sm_70. R1-QTORCH-AMEND keeps V100S out of the Track P smoke, E0 and training path.
- Both scripts preserve author option e's fixed Hugging Face revision `13fb94bfda8c8cf22497dc57b78f391a9acb426a` and Qwen2.5-Coder-7B-Instruct Q4_K_M GGUF. Curl success, exactly 4,683,073,536 bytes, and SHA-256 `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c` gate model startup. The model stays in scratch. Readiness polls a loopback address. V1 first-run job 759707 has no offload lines in its retained log. Use the chain report's follow-up at verbosity 4 and TOpAS result, which describes 29 layers offloaded, as the GPU comparison.
- **Blocking I3 false PASS, lines 75–84.** The newly mandatory `GPU_USED` test accepts `ggml_cuda_init: failed to initialize CUDA` by itself. A GPU name or an attempted offload also matches. Gate the image v2 result on demonstrated offload, e.g. the last `offloaded N/M layers to GPU` line with `1 <= N <= M`, and retain that exact line in the output. The same pinned llama.cpp build has this log format in the repository's 30 Oct Track S Ops Phase 1 review. Keep broad CUDA lines for diagnosis. Verify the healthy server corresponds to the launched process and pinned model. Capture `/v1/models` curl status and test its JSON for `model.gguf` while that PID is alive. The current script truncates the response and ignores the HTTP call's outcome. Preserve the pin, download and hash checks.
- **Incomplete runbook checks, lines 15–24 and 54–74.** The invoked runbook §4.4 calls for CUDA device and a short matmul probe, `llama-server --version`, and one short completion with `cache_prompt: false`. Option e supplies the later model source, site and GPU choices. The v2 proposal defines its image acceptance evidence as pinned download, hash, ready server and GPU offload. Capture the runbook diagnostics in the job as well, including the completion status and a bounded response before shutdown. Keep `nvidia-smi` diagnostic if exercised, as the build report makes it optional. A V100S result here only describes I3.
- Keep the dry-run ads and scheduler evidence with the unit. Confirm the effective OCI/Docker attributes, placement constraints, resolved executable, requests and output transfer from each submit directory. Capture fresh GPU availability and own-queue snapshots. Run NEMO2 first and inspect its result before the TOpAS submission. Record placement and submit/execute/end, wait/run, holds, evictions and exit. The NEMO2 first pull can be part of run time.

## Reviewed file hashes

```text
fde29f60a3d3540fe8bfbe3ed16d9562cc6bbdca426eb7327cc4ed2eacbe9de0  i2/probe.jdl
3fdba3f81e9683213a74c8f390a77c536c9e465e4c29c4440e5d268eac5c6015  i2/s4_run.sh
3703466600c2d4c1ed26994a63dd457d7817cead24918461f9d332966b09681e  i3_nemo2/probe.jdl
89861b19f937050d62de58bfbb4d5a3a628fa318b6648fe7be96df4c60ee20ef  i3_nemo2/i3_run.sh
2652b948cece518a3066ecbec3b21c5d5e2ac5fce1138771844057f94bef9908  i3_topas/probe.jdl
89861b19f937050d62de58bfbb4d5a3a628fa318b6648fe7be96df4c60ee20ef  i3_topas/i3_run.sh
```

## Re-review — I3 revision

**I3 verdict: ACCEPTED for portal dry-run and pre-submit checks.** Both revised GPU scripts have SHA-256 `53b79bc669bbb466f96b2747eaea637f1af186910edb61acc6309813f7517be0` and pass `bash -n`. JDL hashes are as listed above.

- The new predicate requires a positive offloaded-layer count. A direct check rejected CUDA-init failure plus `offloaded 0/29 layers to GPU` and accepted `offloaded 29/29 layers to GPU`. This is the log format used by llama.cpp commit `620d2225` in the 30 Oct Track S Ops Phase 1 review.
- I3 now requires the launched PID to be alive at readiness and before the requests, validates the `paperb-i3` alias in `/v1/models`, and checks a nonempty native completion with `cache_prompt:false`. Results and the proven offload line are retained. The version, device and bounded 60-second fp32 matmul are recorded. The free-space check now exits before initiating the download.
- I2 remains separately subject to the source-provenance and result checks above.

## Re-review — I2 revision and final verdict

**Both I2 and I3 staging units ACCEPTED for submission once the portal checks on the exact staged bytes are complete.** I2 `s4_run.sh` SHA-256 is `c963f6960253c9920cad87e333f57fca0a454e4959b66257060c905dc6e720fe`. The I2 JDL and accepted I3 hashes are as above. The operator reports three successful original dry-runs and will repeat the I2 dry-run in the fresh submit directory. The portal ads and runtime outcomes were outside this static re-review.

- I2 now extracts tested inputs from the immutable commits into per-job directories, with the Paper archive restricted to the reviewed 263 `r1/` files. I independently reproduced the source reference archive hash `f9d2813fa5a1654c7a0785c08738dd7c23d506f7e2a0c2c0cf90401ae9ace842`. The harness commit is independently pinned and archived by the script from the worker-visible checkout. The worker test reads from those two extracted trees. The unrelated S6 network probe was removed.
- The archived v1 evidence contains exactly two successful pytest invocations, two worker logs each, four scores at `0.922225` and four losses at `0.314016`. The revised wrapper gates the overall exit status on the same counts, each invocation's return code and the metric comparison. Confirm `I2_PASS` and an overall zero exit status together. The remaining historical SIF lines in the CPU identity file are non-gating legacy diagnostics. Use its recorded HTCondor image ClassAd, approved v2 digest and the image's VERSIONS for actual image provenance.
