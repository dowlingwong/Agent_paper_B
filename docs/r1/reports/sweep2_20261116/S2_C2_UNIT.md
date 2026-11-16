# S2-C2 — sweep-2 HTCondor job wrapper (unit for independent review; ENGINEERING, not launched)

**Authority:** `docs/r1/prompts/SWEEP2_HTCONDOR_RUNBOOK_20261116.md` (`docs/runbooks-16nov` @ `a2789ea6`), §3
S2-C2 and §1 P1–P7. **This is a work plan, not a decision:** EVIDENCE launch is gated on the PLAN row
`R1-SWEEP-HOST-HTC` (not present on `author-x7-20261116`; verified 0 matches) and P1–P7; this unit only prepares the
ENGINEERING path. Reviewer of the required gate is `docs/r1/reviews/S2_C2_REVIEW_20261116.md` (to be written by
the independent reviewer).

## What the unit is

Branch `sweep2-cluster-20261116` from `origin/docs/runbooks-16nov`. Files:

| file | role |
|---|---|
| `sweep2/s2_c2_lib.py` | the reviewed wrapper: spec validation, label resolution from the authorization only, frozen-image identity, GPU/CPU/driver identity, GGUF fetch+sha256, owned llama-server with the exam flags and a full-offload check, harness root-campaign collection (`r1.headroom.e1b_collect`, `langgraph` manager, `llamacpp/<alias>`), sealed output + job record + SHA256SUMS, resume by the collector's own `--resume` |
| `sweep2/s2_c2_job.sh` | container-job entry point (runs the wrapper with the harness-env python) |
| `sweep2/render_jdl.py` | renders the JDL with the **fixed** requirements template |
| `sweep2/spec.example.json` | the reviewed example spec (frozen v1 gpu digest, pick GGUF pinned by HF revision+sha256, L40S/NEMO2/CPU-class requirements, sealed `/ceph` output) |
| `sweep2/dryrun/` | rendered JDL + the `condor_submit -dry-run` ad (evidence below) |
| `r1/tests/htcondor/test_s2_c2_unit.py` | 11 synthetic tests (no job, no network, no GPU): spec/label/sealed-path/requirements/W=20/schema/JDL/collector-argv/server-argv/CPU-class; the R1-SWEEP1-CLASSIFY defect regression is explicit |

## Requirements pinned (from `condor_status` on deepthought, 16 Nov 2026)

- GPU model **`NVIDIA L40S`** (9 slots advertised; the other L40S ad is ETP-local `deepthought2`, excluded by the
  CloudSite requirement).
- CloudSite **`BwForCluster-Nemo2`** (one GPU model per table; no V100S/H200/TITAN X).
- CPU class: the ads do **not** carry `CpuModel` (it is `undefined` on every slot); the class is pinned as
  `Arch == X86_64 && OpSys == LINUX && Cpus >= 16 && regexp("^g36[0-9]{2}\.nemo\.privat$", Machine)`, which is
  exactly the NEMO2 L40S node family (`g3605`, `g3608`, `g3612`, …, 16 CPUs each). The wrapper records
  `/proc/cpuinfo`'s model name and logical CPUs; a spec `cpu_model_contains` pins the observed model once the
  S2-C4 timing pilot has recorded it (required for EVIDENCE, optional for ENGINEERING).
- Sealed output: `TARGET.ProvidesEtpCeph =?= True`; the output root must be under
  `/ceph/srv/dwong/paperb/sweep2/<run_id>/` (the wrapper refuses anything else and refuses `r1_sealed` as an
  output). Nothing in the job reads labels; the collector writes them sealed.

## Label rule (R1-SWEEP1-CLASSIFY defect fixed and tested)

The table label is taken **only** from the authorization note (path + SHA-256 pinned in the spec; the note must be
`approved: true`, name the run id and carry `label: EVIDENCE`). Without a note the label is `ENGINEERING_ONLY`.
A sweep-index label (`PILOT`/`ENGINEERING_ONLY`) is refused as a table-label source; the regression test
`test_index_label_may_never_select_the_table_label` fails if that path is reintroduced.

## Frozen image (S2-C1 proposal)

The unit pins the v1 gpu digest
`ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35…` and verifies the image identity markers from
`/opt/r1/VERSIONS.txt` (`image=r1-htc-gpu`, `build_utc=2026-11-14T23:10:24Z`,
`llama_server_sha256=f8d35fd3…`, `llama_cpp_commit=620d2225…`) plus the llama-server binary SHA-256. v2 is not used
until the author approves its digest; one digest per table.

## Reviewed dry-run evidence (deepthought, no submission)

`condor_submit -dry-run` on the rendered JDL (rc 0, 1 job dry-run to cluster 1), ad fields:
`JobUniverse=5`, `WantContainer=true`, `ContainerImageSource=docker`,
`ContainerImage="docker://ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35…"`, `RequestGPUs=1`, `RequestCpus=16`,
`RequestDisk=30000000`, `RequestMemory=64000`, `+RemoteJob=True`, and the requirements exactly as rendered
(CloudSite Nemo2 + GPUs_DeviceName L40S + Arch/OpSys/Cpus 16 + machine regexp + ProvidesEtpCeph + scheduler-added
`HasContainer && HasDockerURL`). Raw: `sweep2/dryrun/s2_c2.dryrun.txt`. No job was queued and no submission was
enabled.

## STOP conditions of the unit (fail-closed, no retry, no deletion)

Wrong/unpinned spec fields; non-sealed or `r1_sealed` output; label source invalid/mismatched; image identity
markers or llama-server hash mismatch; GPU not L40S or CUDA unavailable; CPU outside the pinned class; GGUF
size/sha mismatch; server build not the pinned one or not full offload; collector rc ≠ 0 (the sealed record and
outputs are kept; the wrapper never deletes them); resume only when a completed collector manifest exists, and a
root started but not completed is re-run whole by the collector's own A.5 semantics (never patched).

## Not part of this unit

S2-C3 (L40S deployment check) and S2-C4 (timing pilot) are separate units and separate reviews; S2-C1 is a proposal
for the authorization; S2-C5 (real-submission switch) is a separate reviewed change. P2 (integration branch on
`main`) and P3 (authorization) do not exist yet, so no EVIDENCE launch is possible; this unit's dry-run path is
reviewed now so the ENGINEERING checks can start when the author's gate allows them.
