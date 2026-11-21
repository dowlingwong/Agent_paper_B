# G.1b dry-run evidence (no submission)

**What this is.** A real `condor_submit -dry-run` of the rendered G.1b layout-preview JDL on
`deepthought` (submit host), executed 16 Nov 2026. It processes the submit file and writes the ClassAd attributes to
a local file; **it does not submit a job to the SCHEDD and does not touch a GPU**. No job was queued; no file on the
shared cluster was modified except the throw-away scratch directory named below.

**Files**

| file | role |
|---|---|
| `g1b_layout_preview.jdl` | rendered JDL from `render_jdl.py --layout-preview` (placeholder stage; **NOT FOR SUBMISSION**) |
| `g1b_layout_preview.dryrun.txt` | raw `condor_submit -dry-run` output (the resulting job ClassAd) |
| `stage/` | staged job inputs used for the dry-run (`g1b_job.sh`, `g1b_lib.py`, and `g1b_spec.json` = the placeholder template) |

**Command (read-only in effect; writes only the local ad file)**

```
# on the Mac, from this directory
scp -q g1b_layout_preview.jdl stage/g1b_job.sh stage/g1b_lib.py stage/g1b_spec.json \
    deepthought.etp.kit.edu:/work/dwong/g1b_prep_20261116/
ssh deepthought.etp.kit.edu \
  'cd /work/dwong/g1b_prep_20261116 && condor_submit -dry-run g1b_layout_preview.dryrun.txt g1b_layout_preview.jdl'
# -> Dry-Run job(s). 1 job(s) dry-run to cluster 1.  RC=0
scp -q deepthought.etp.kit.edu:/work/dwong/g1b_prep_20261116/g1b_layout_preview.dryrun.txt .
```

**Why a layout preview and not a runnable chunk.** The G.0 census on Ada has not yet named the candidate T1 nodes,
so the spec carries the validated placeholder list and no real chunk can exist (§2 of `../G1B_PLAN.md`). The preview
JDL is generated from the placeholder template, is marked `+G1BPreview = True` and carries the header
`LAYOUT PREVIEW ONLY — NOT FOR SUBMISSION`; its staged spec is the placeholder template. If it were nevertheless
submitted, the container entry would STOP at spec validation (G.0 census incomplete) before it touched the GPU, and
no output would be produced. `render_jdl.py` refuses to write a preview JDL anywhere outside this directory.

**Key ClassAd fields from the dry-run (review evidence)**

| field | value |
|---|---|
| `JobUniverse` | `5` (container universe) |
| `WantContainer`, `WantDockerImage`, `ContainerImageSource` | `true`, `true`, `docker` |
| `ContainerImage` | `docker://ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296` (frozen v1 gpu image) |
| `RequestCpus` / `RequestMemory` / `RequestDisk` | `16` / `32000` MB / `42439718` kB (S2-C4 measured floor) |
| `RequestGPUs` | `1` |
| `RequestWalltime` | `10620` s (layout-preview chunk wall; ≤ the 10,776 s S2-C4 ceiling) |
| `RemoteJob` | `true` (`+RemoteJob = True`) |
| `G1BPreview` | `true` (preview marker; absent from a real JDL) |
| `Requirements` | `TARGET.CloudSite =?= "BwForCluster-Nemo2"` && `TARGET.GPUs_DeviceName =?= "NVIDIA L40S"` && `Arch == "X86_64"` && `OpSys == "LINUX"` && `Cpus >= 16` && `CpuFamily =?= 6` && `CpuModelNumber =?= 207` (plus the scheduler's `HasContainer && HasDockerURL && Disk/Memory/GPUs/FileTransfer` terms) |
| `TransferInput` | `g1b_job.sh,g1b_lib.py,g1b_spec.json` |
| `TransferOutput` | `out.tar,job_record.json,SHA256SUMS,g1b_run.log` |
| `ProvidesEtpCeph` | absent (NEMO2 slots do not advertise it; outputs transfer and are sealed later) |
| `machine_regex` / Docker image share | absent; the host class is pinned by CPU family/model, as in the reviewed S2-C2 pattern |

`CondorVersion="$CondorVersion: 25.0.12 2026-07-07 BuildID: 930047 PackageID: 25.0.12-1 $"`.

**Scratch directory left in place (no deletion):** `/work/dwong/g1b_prep_20261116/` on deepthought contains the
staged inputs, the preview JDL and the ad file. Nothing was removed.
