# Independent review — Track P image v2.2 run records for P5 (I2 759993, I3 759994, H200 smoke 759997, E0 760000), 25 November 2026

Reviewer: `reviewer-v22-runs-p5`, fresh-context delegated subagent; independent and read-only.
Workspace `/Users/wongdowling/Documents/agent_paper_B`; review window 2026-11-25 12:46–13:02 CET (11:46–12:02Z).
Read-only `ssh` as `dwong` on `deepthought.etp.kit.edu` (its clock at review time: `2026-11-25T12:55:47CET` =
`11:55:47Z`; its condor logs are CET). No job submitted, edited, held, removed or re-run; nothing written on
deepthought; no image pulled; no registry, GitHub or network access; no label or evaluation block opened. The only
write is this review file (plus throw-away `/tmp` scratch).

**Object.** The four image-v2.2 qualification records, as committed in
`docs/r1/reports/trackp_v22_20261123/V22_BUILD_20261124.md` (main `a20bd02e482bcfea9c8567e65b93c742c28eafd5`,
merged at `ac981011c500dc32a423ef0897fdd7ab30e8477e`; blob sha256
`90059f814e091070a165626ae561670862dae7917b95a8839f09bd913d96e695`):

| Job | Stage | Image digest (HTCondor ad = report) | Host | Exit | RemoteWallClock | TimeExecute | Verdict |
|---|---|---|---|---|---|---|---|
| **759993**.0 | I2 (CPU worker determinism) | `r1-htc-cpu@sha256:a3b3a07424743b84c99101ae61b610f9bd4b6ffe1f2f48c0f6d099fbb84d46b8` | `ms02.etp.kit.edu` (ETP local) | 0 | 68 s | 27 s | `I2_PASS` |
| **759994**.0 | I3 (GPU image + pinned GGUF serving) | `r1-htc-gpu@sha256:49dd9900e0bbb004fe1f45573583cf0cffeb9fe3d98f0ef6d3aa16fb4fe75949` | `g4402.nemo.privat` (NEMO2 H200) | 0 | 571 s | 570 s | `I3_PASS` |
| **759997**.0 | staged Track P H200 smoke | `r1-htc-gpu@sha256:49dd9900…5949` | `g4402.nemo.privat` (NEMO2 H200) | 0 | 585 s | 582 s | `pass: true`, kernels bound |
| **760000**.0 | staged E0 host equivalence | `r1-htc-gpu@sha256:49dd9900…5949` | `g4402.nemo.privat` (NEMO2 H200) | 0 | 1,393 s | 1,389 s | `equivalent: true` |

All four: `JobStatus = 4`, `ExitCode = 0`, `NumJobStarts = 1`, one `LastJobStatus = 2` (running) epoch, no holds,
no evictions, no retries. I2's `requirements` are the ETP-local `ProvidesETPResources`; the three GPU jobs require
`TARGET.CloudSite =?= "BwForCluster-Nemo2"` **and** `TARGET.GPUs_DeviceName =?= "NVIDIA H200"`. Stage workdir:
`/work/dwong/paperb/work/trackp-h200-v21-20261121.R7XUMd/` (I2 output:
`/work/dwong/paperb/work/s4_759993.0_20261124T004946Z/`).

**Authority.** The SFT authorization draft rev 4.2, `docs/r1/proposals/TRACKP_P4_SFT_AUTHORIZATION_DRAFT_20261121.md`
§10 (`## 10. Needs a cluster test (NEMO2 H200, image v2.1)`, line 404) and prerequisite **P5** (§7, line 339);
`docs/r1/reports/trackp_p4_runner_20261122/P4_CLUSTER_TEST_PLAN_20261124.md` §0 item 1 and F8 (which apply §10 to image v2.2 and name this review as
the missing P5 item); the phase-1 note draft `docs/r1/proposals/TRACKP_P4_PHASE1_NOTE_DRAFT_20261122.md` (`P5` line);
PLAN §10 rows `R1-TRACKP-IMAGE-V22` (PLAN.md:1489), `R1-TRACKP-IMAGE-V22-B` (:1501), `R1-HTC-QTORCH`,
`R1-QTORCH-AMEND`, `R1-TRACKP-P4-RUNNER-DECISIONS` (:1509), `R1-TRACKP-I2-DISK` (:1430) and `R1-TRACKP-I2-MEM`
(:1451); image build record `docs/r1/reports/trackp_v22_20261123/V22_BUILD_20261124.md`; image
Dockerfile/workflow review `docs/r1/reviews/TRACKP_V22_IMAGE_REVIEW_20261124.md` (round 2 **ACCEPTED** at
`3c54a0e893098c7d6cc95d6581114c64435cfa30`, pushed as `667bb9c2f2d8948a5c6e981adaf54c668a39a9a9`).

## Bottom line

**ACCEPTED.** The four records are genuine image-v2.2 runs on the recorded hosts, produced by the already-reviewed
stage units with **no assertion relaxed**; every expected assertion passes; E0's equivalence is independently
reproduced at the pre-declared tolerances; the output identities/seal hashes match the accepted v2.1 records and the
v2.2 build record; and no test or evaluation label was opened. The committed v2.2 report matches the host evidence
line by line. This supplies the independent review of the v2.2 run records that P5 and the phase-1 note draft list
as still open, so §10's first bullet / P5's image-qualification element is satisfied on the image of record.

Scope: this review is the **run-record** element only. It does not review the Dockerfile/workflow (separate review
ACCEPTED), the P.4 runner, the probe mode (F1) or the host-config fill; and it does not claim the SFT fit/timing
probe itself, which remains to be run after the reviewed probe mode and host-config fill land (P4 cluster test plan
§2, §4, STOP S4). The one addition this review makes to the open-field list is that the image-v2.2
`VERSIONS.txt` sha256 can be, and is, recorded here (see m4): `aaa1a304c2230466f603e63c96d7259d631f0668fa2d8b6486772fef22f0117a`.

## 1. Genuine v2.2 image and identity

The HTCondor container image in the job ads is the v2.2 digest pair of the committed build record, and no tag or
other digest is used: GPU `49dd9900e0bbb004fe1f45573583cf0cffeb9fe3d98f0ef6d3aa16fb4fe75949` (759994, 759997,
760000), CPU `a3b3a07424743b84c99101ae61b610f9bd4b6ffe1f2f48c0f6d099fbb84d46b8` (759993). The in-image evidence
captured by the jobs ties the runtime to the v2.2 build, not merely to a tag:

- I3 `i3_identity.txt` (`fe8ada81d2ffa0403bd90cfe4a81fcf0c3e409c4847f5cb9c47a3536d1585074`) prints
  `/opt/r1/VERSIONS.txt`: `image=r1-htc-gpu`, `build_utc=2026-11-24T00:30:00Z`, torch `2.6.0+cu124`, CUDA 12.4,
  `torch_cxx11_abi=False`, `env3_causal_conv1d_arch=8.0;8.9;9.0 (source build, CXX11 ABI 0, TORCH_CUDA_ARCH_LIST)`,
  `env3_sorted_diff=empty`, and exactly the build artefacts of the v2.2 report —
  sdist `3202758494eaa7b597ce1c282dfa188889506bfcb92cad3c407d26736bfcd32b`,
  `causal_conv1d_cuda` `.so` `8d6065c78eb5f80836afe7f61d8dbc14ed2a8a14a843996cfe419c92e7095159`,
  build log `fe872a3edc8f9745148c7e2fe5e02f3f02aebd3c47f5d7a686c610ec816d3312`,
  built wheel `9ec74ffedf802fbc081fb40bb5912d8db641166dcea2bddfb855c0fd5206772f`.
  `trackp_gpu_freeze_sha256=50238e5a…b9a08` (the R1-ENV-PIN freeze), harness/tracks freezes match the pin.
- The smoke's runtime report proves the ABI fix on the actual H200: `causal_conv1d` **1.7.0** with
  `causal_conv1d_fn` and `causal_conv1d_update` bound through
  `causal_conv1d.causal_conv1d_interface.*`, `fla` 0.5.2, torch `2.6.0+cu124`, CUDA 12.4, and no
  `kernel_import_error` (this is the exact failure of the superseded v2.1 image; see §5).
- I2's CPU identity (`i1_envs.txt`, `e5609f8c…`; `identity.txt`, `80d22184…`) shows `image=r1-htc-cpu`,
  `build_utc=2026-11-24T00:34:57Z`, UV 0.13.6, and the harness env `Python 3.13.4 / numpy 2.4.4 / sklearn 1.8.0 /
  pytest 9.0.3` — the documented `0.922225` reference stack — with env3 absent by design.

Limitation: no registry/network access, so the digest→commit binding rests on HTCondor's image ad plus the
in-image VERSIONS signatures above and on the committed build record; it is not re-derived from ghcr.io here.
The tag `20261124-v2.2-667bb9c2` and Actions run 45290856704 are not visible in run records and are cited from
the committed build record.

## 2. Expected assertions pass — and were not relaxed

Every stage file on deepthought was hashed and compared with the committed, pre-submit-reviewed v2.1 stage files.
All executables, the comparator, the reference files and the registry are **byte-identical** (the JDLs differ only
as itemised below):

| File (deepthought) | sha256 | Equal to accepted v2.1 unit |
|---|---|---|
| `i2/s4_run.sh` | `c963f6960253c9920cad87e333f57fca0a454e4959b66257060c905dc6e720fe` | yes (`STAGE_SHA256SUMS`) |
| `i3_nemo2/i3_run.sh` | `53b79bc669bbb466f96b2747eaea637f1af186910edb61acc6309813f7517be0` | yes |
| `smoke_h200/probe.sh` = `e0_h200/probe.sh` | `24688a109787d15be1718eb695167529ee615f72e32c41770f09be0cf04c148b` | yes (18 Nov pre-submit review) |
| `e0_h200/compare.py` | `bd957c0d3e984b4ec9e27ef090d29580654cfef91d73174bf05a615cd4bf6084` | yes |
| `e0_h200/configure_e0.py` | `c3a5491ad9ad2b15211474ef3aa01ba22171e2106cb5510dff62217809fad870` | yes |
| `e0_h200/reference.json` / `reference_manifest.json` | `bc1c9182…afc` / `340e7a03…913` | yes (TASL-7 record) |
| `smoke_h200/tasl7_smoke_reference.json` | `974f32cca778daf513a49f43925efb594ab9dedbef3b0c6ccbd099f8cc94a438` | yes |
| `*/registry.yaml`, `*/stage_models.py`, `*/nvidia-smi-scoped`, `*/probe_mode.txt` | `e60cdb28…`, `32cea598…`, `ec88ddfe…`, `8d76ef07…`/`4055915…` | yes |

JDL changes, by deterministic diff against the committed staged units through the saved `.before_v22` backups
(all four `probe.jdl` mtimes are 2026-11-24 01:48:42 CET, i.e. 00:48:42Z, five seconds before the 00:48:47Z
submission — no post-submission edits):

- **smoke 759997 and E0 760000:** committed v2 JDL → v2.1 → v2.2 changes **line 2, the container image, only**.
  The reviewed fields are present (`periodic_hold = (NumJobStarts > 1)`, whole-H200 NEMO2 requirements, unchanged transfer/output lists).
- **I3 759994:** line 2 image (v2 `b1144ece` → v2.1 `31478d99` → v2.2 `49dd9900`) **and** the reviewed
  L40S→H200 requirement (`R1-TRACKP-I3-H200`, accepted in `TRACKP_V21_UNIT_REVIEWS_20261121.md`); nothing else.
- **I2 759993:** line 2 image (v2 `08a36eff` → v2.1 `c152c329` → v2.2 `a3b3a074`) **and** the separately
  reviewed resource values `RequestMemory 8000→2000` (`R1-TRACKP-I2-MEM`) and
  `request_disk 30000000→2000000` (`R1-TRACKP-I2-DISK`); checks, script and expected values unchanged. The condor
  user log confirms the run used `Memory = 2048` MB allocated / `Disk = 2001920` KB and consumed 124 MB.

Assertions exercised, unchanged from the reviewed units:

- **I2:** two isolated pytest runs of `test_real_worker_run_is_seed_deterministic` (`pytest_rc=0` twice; 2 worker
  `run.log`s per run), 4 values, all `val_score 0.922225` and `train_loss 0.314016`, exactly the expected values;
  all four worker logs sha256 `0f4419b6010451339461a941e80262c7c5005a23716e40577176b3afa4ae1d94` (identical to the
  accepted v2.1 run). `i2_compare.txt` = `I2_PASS`, byte-identical (sha `854ca6b7…ac66e`) to the committed
  `i2_seal/i2_compare.txt`.
- **I3:** pinned GGUF at HF revision `13fb94bf…`: 4,683,073,536 B downloaded (19 s), sha256
  `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c` = expected; `llama-server` ready in 4 s,
  `/v1/models` exposes `paperb-i3`, one short completion with `cache_prompt: false`, log shows
  `offloaded 29/29 layers to GPU`; `I3_PASS`. `i3_PASSFAIL.txt` (`323368d3…b97`) and `i3_sha.txt` (`aadf129a…44e`)
  are byte-identical to the committed v2.1 copies.
- **Smoke:** the wrapper's post-check passes: `pass: true`, `device: NVIDIA H200`, no `kernel_import_error`,
  `kernels_bound` **equal** to the TASL-7 reference (`causal_conv1d_fn`, `causal_conv1d_update`,
  `torch_chunk_gated_delta_rule`, `torch_recurrent_gated_delta_rule`), the same three checks
  (`bf16_matmul`, `deltanet_forward_float32`, `deltanet_forward_bfloat16`), all `pass: true`. I re-ran the
  wrapper's exact CHECK block on the fetched `gpu_smoke.json` + reference: PASS; a negative control simulating a
  torch fallback (missing `kernels_bound` + `kernel_import_error`) is rejected.
- **E0:** see §3.

## 3. E0 equivalence — independently reproduced

The E0 job used the staged, reviewed unit unchanged: it cloned paper `8e13e77c…` and harness `897d83c8…` (both
equal to the TASL-7 reference manifests' commits), staged the pinned `Qwen/Qwen3.5-0.8B-Base@dc7cdfe2` and
`jaredpalmer/kev-0.8b@788ddbdd` files, asserted the run's `data_manifest_sha256` equals the reference's, and ran the
historical E0 v2 recipe (`kev-0.8b`, `DRYRUN`, `fresh`, lr 1e-4, seed 0, soft target) followed by `compare.py`.

Independent checks I ran on the bytes fetched read-only from the host:

- `reference.json` on deepthought is byte-identical to the committed TASL-7 reference (`bc1c9182…afc`), and
  `compare.py` is the committed comparator (`bd957c0d…6084`).
- Re-running the committed comparator on the fetched reference and H200 `report.json` gives output **byte-identical**
  to the job's `comparison.json` (sha `710bc61a…ced`) with exit 0; mutating `lora.test.rps` by ×3 makes it exit 1
  (fail-closed confirmed).
- Criteria, all pass, at the pre-declared tolerances: `width_slope_vs_label` 0.913484 (TASL-7) vs 0.910688 (H200),
  Δ −0.0028 ≤ 0.05; `mean_slope` 1.019260 vs 1.012878, Δ −0.0064 ≤ 0.05; `rps` 1.9400e-4 vs 1.8337e-4,
  rel. 0.0548 ≤ 0.10. `equivalent: true`, and the wrapper is `set -e` so the job's exit 0 is the comparator's exit 0.
- Data provenance: the E0 fixture at the paper commit `8e13e77c` is the committed synthetic
  `r1/c3/train/data/e0_v1.jsonl.gz` (sha256 `4f4db29b6a4c0ca0181825e5c2c0fb031521e034a006990b93686cd5fffc8290`), and
  the run's `data_manifest_sha256` `b963be2dd378241e0b0689907d4051bfa62922a8e4968aa40061ed7ef275bfef` equals the
  reference manifest's — the 26 Oct TASL-7 dataset digest, which predates any sweep-1 B.2 label.
- Config provenance: I recomputed `config_digest` of the paper-commit `r1/scripts/configs/trackp_portal.json`
  (canonical sorted JSON) = `588869fa8e721eec2005607dc25f6f46229aa0960bd3f64dbf5155323094f4b9`, exactly the
  reference manifest's `config_sha256` that `configure_e0.py` asserts; the produced `e0_config.json` differs from
  it **only** in `host`, `gpu.{name,compute_capability,lock_path}`, `work_dir`, `runs_dir`, `models_dir`,
  `hf_home`, `venv.path` and the two `bases.kev-0.8b` local paths, and its digest `d93dbaa4…6610` equals the run
  manifest's `config_sha256`.
- `comparison_identity.txt` (`fba790d7…eba`) records the comparator mapping (`portal` = TASL-7 reference,
  `tasl7` = H200) as the pre-submit review requires; the manifest records `evidence_label: DRYRUN`,
  `protocol: trackp_e0/v2`, paper `8e13e77c` and harness `897d83c8`, both clean.

## 4. No test or evaluation labels opened

I searched every stage directory (scripts, JDLs, logs, stdout/stderr and handbacks) for the exact strings
`label_block.jsonl`, `evaluation_block.jsonl`, `label_sweep`, `y_eval` and `evaluation_block`: **no hits**. The
apparent hits from a looser numeric regex were substring matches inside metric floats (`7006`/`7010` inside
`1.7000…e-05`, `4.937010…e-05`), not label seeds. The four runs read only: pinned code commits for I2
(`60ecf1da…`/`a3fedbbd…`, checked clean by the script), pinned model files for I3/smoke/E0 (sizes + sha256 recorded
in `model_sha256.txt`), and the committed synthetic `e0_v1` fixture for E0 (above). The committed report's
"labels/evaluation remain sealed" is consistent with what the outputs contain; 759993–760000 are
ENGINEERING_ONLY/DRYRUN records.

## 5. Cross-checks, ordering and residual wording

- **Committed report vs host:** all claims in `V22_BUILD_20261124.md` that can be checked on the host match:
  digests (§1), I2 values (`0.922225`/`0.314016`), I3 PASS / exit 0 / wall 571, smoke PASS / exit 0 / wall 585 /
  `kernels_bound` with both `causal_conv1d` entries / no `kernel_import_error` / "assertion unchanged", E0
  `equivalent=true` / exit 0 / wall 1,393, and the build artefact sha256s. The report's `I3 759994` and
  `E0 760000` status lines are the post-run version of commit `a20bd02e`.
- **Ordering held:** I2 PASS (00:50:12Z) → I3 PASS (01:05:05Z) → smoke submitted 01:05:58Z → smoke PASS
  (01:15:49Z) → E0 submitted 01:15:58Z → E0 finished (01:48:18Z). The staged gate (I2/I3 before smoke, smoke before
  E0) was honoured within seconds; no job was launched early.
- **Superseded attempt:** the failed v2.1 smoke **759983** (return 1) was the `causal_conv1d` C++11-ABI import
  failure recorded in `V22_BUILD_STOP_20261123.md` and `R1-TRACKP-IMAGE-V22`; it belongs to the v2.1 attempt, is not
  hidden, and the v2.2 chain replaces it. The P5 "diagnostic job" element is the v2/v2.1 diagnosis (759916 and the
  V22 STOP) plus the independently accepted v2.2 source-build Dockerfile review; no separate v2.2 diagnostic job was
  run, which is the correct consequence of that diagnosis and fix.
- **Output hashes** (all on deepthought; this is the durable hash record for the P5 file since the raw handbacks are
  not committed): I2 — `i2_compare.txt` `854ca6b7…c66e`, `i2_summary.txt` `8d1dac40…22db`, `i2_run1.log`
  `dade0408…b80`, `i2_run2.log` `47138c56…5590`, `identity.txt` `80d22184…da1`, `i1_envs.txt` `e5609f8c…2c82`.
  I3 — `i3_PASSFAIL.txt` `323368d3…b97`, `i3_sha.txt` `aadf129a…44e`, `i3_identity.txt` `fe8ada81…85074`,
  `i3_download.txt` `c9b82065…db90`, `i3_download.log` `a6c3d5b8…caae0`, `i3_cudalibs.txt` `11e9f5fe…fa9b`,
  `i3_server.txt` `c6daa7c3…2110`, `i3.out` `9f093713…68b1a`. Smoke — `handback/exit_status.txt` `9a271f2a…86aa`
  (`0`), `handback/gpu_smoke.json` `cf19025a…3422`, `handback/job.log` = `probe.out` `8e4b2574…6da9`,
  `handback/lease.jsonl` `7949adb7…6a02`, `handback/model_sha256.txt` `1f269abd…43de6`. E0 —
  `handback/comparison.json` `710bc61a…ced`, `handback/report.json` `b2a484cd…a3f`, `handback/manifest.json`
  `0e638a63…45c`, `handback/exit_status.txt` `9a271f2a…86aa`, `handback/comparison_identity.txt` `fba790d7…eba`,
  `handback/e0_config.json` `a4db1ab7…1dd`, `handback/pred_test_head_fit.npy` `d52bd136…c7464`,
  `handback/pred_test_lora.npy` `54034148…de9`, `handback/head_fit/curve.jsonl` `13324899…d70a`,
  `handback/lora/metrics.jsonl` `7c303c6f…67c2c`, `handback/lora/best.json` `7902703d…1a52`,
  `handback/model_sha256.txt` `5aceae19…f7c`, `probe.out` = `handback/job.log` `1ccb0a10…2d70`. The wrapper's
  `probe.err` are empty (`e3b0c442…b855`) for all GPU stages; the smoke lease (01:14:25–01:15:44Z) and E0 lease
  (01:33:39–01:48:11Z) fall inside their job windows and are recorded in `lease.jsonl`/`manifest.json`.

## Findings

No blocking or major finding. Minors, none of which changes a result:

- **m1 — committed durability.** The raw v2.2 handbacks exist only on deepthought; the committed record is the
  report, and unlike v2.1 (`i2_seal/`, `i3_h200_20261121/`) the small output files are not in the repository. The
  §5 hash list makes this review citable, but the coordinating session should commit this review (and, optionally,
  the small handbacks) so P5's "committed result record and an independent review" is durable on `main`. Not a
  defect of the runs.
- **m2 — wording.** "4 seeds" (report line 16 and the task text) is imprecise: the four values are two independent
  pytest runs × two worker `run.log`s; the v2.1 record calls them runs and the assertion is the exact four-value
  equality. Use "two runs, four worker outputs".
- **m3 — draft text says v2.1.** The draft's §10/P5 literally names image v2.1; it is superseded by
  `R1-TRACKP-IMAGE-V22`/`V22-B` and the P.4 runner refuses v2/v2.1. Applying §10 to v2.2 (as the accepted P4 cluster
  test plan §0 item 1 does, and as the phase-1 note's `image:` already does) is the only coherent reading; the
  phase-1 note/draft should name the v2.2 digest and cite this review, not v2.1. Administrative, not evidence.
- **m4 — image VERSIONS sha256 now derivable.** The note lists the v2.2 `VERSIONS.txt` sha256 as open
  (`TODO_VERIFY_ON_HOST`). It can be derived from the job's own byte-faithful `cat` in `i3_identity.txt`:
  **`aaa1a304c2230466f603e63c96d7259d631f0668fa2d8b6486772fef22f0117a`** (25 lines). I validated the extraction
  method on the CPU image, where it reproduces the reported `versions_sha256`
  `870329e951816f656836f9c09a2d0c650c91b3624038af7878fedc8061e8fff0` exactly. The plan's T1 job can still read it
  directly; until then this value is the best available and is reproducible.
- **m5 — tag/Actions binding.** The run records can only bind the digest, not the image tag
  `20261124-v2.2-667bb9c2` or Actions run 45290856704; those rest on the committed build record and the accepted
  Dockerfile/workflow review. The digest is the security-relevant identity and it matches. No action needed beyond
  keeping note citations on the digest.

## What I did not do

No job action; no write on deepthought; no image pull or registry/GitHub query; no edit to any code, data, report,
note or job file; no label or evaluation block opened; no attempt to fill or validate the phase-1 note's other open fields. I
did not re-derive the TASL-7 reference values (read from the committed reference) or the E0 `pred_test_*.npy`
predictions (used only through the comparator's aggregate report). The review is independent of the agent that ran
the jobs and of the authoring sessions; it did not see their working notes.

VERDICT: ACCEPTED

Accepted scope: the image-v2.2 run-record element of §10/P5 (I2 759993, I3 759994, smoke 759997, E0 760000) for the
SFT probe, once this review is committed on `main` and cited in the phase-1 note. The SFT fit/timing probe itself is
not run here and still requires the reviewed probe mode (F1), the host-config fill (P7) and the T1 `VERSIONS.txt`
read (P4 cluster test plan §2/§4, STOP S4); those are separate units, not defects in these records.
