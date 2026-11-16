# Independent pre-submission review — S2 container-universe probes (ETP local / NEMO2 / TOpAS), 14 Nov 2026

**Reviewer role:** fresh, independent, read-only reviewer. Not the author of the JDLs, not the executing agent;
I did not write, submit or run any reviewed file and I have no cluster access.

**Date/time of review:** 14 November 2026, 10:54–11:04 CET (Europe/Berlin).

**Reviewed unit:** `docs/r1/reports/htcondor_chain_20261114/s2/` — `probe.sh`, `S2L_local_cpu.jdl`,
`S2N1_nemo2_l40s.jdl`, `S2N2_nemo2_h200.jdl`, `S2T_topas_v100s.jdl`, and
`dryrun/S2L_local_cpu.dry` … `dryrun/S2T_topas_v100s.dry` + `*.dry.log`. Branch `htcondor-chain-20261114`,
HEAD **`bff70706`** (commit "docs(r1): HTCondor chain — S2 container-universe probe JDLs + dry-runs (rc 0)";
the unit is committed; pinned below by SHA-256).

**Basis for the review:** the author's 14 Nov instruction S2 as reflected in the operative chain report
`docs/r1/reports/HTCONDOR_CHAIN_20261114.md` (authority L3: write scope, ≤10 concurrent, ≤10 GPU-h, whole
GPUs, no deletion) and the Lead's brief (four probes in `universe = container` with
`container_image = docker://cverstege/alma9-gridjob`; ETP local 1-core, NEMO2 L40S, NEMO2 H200, TOpAS V100S;
record queue times; NEMO2 must show whether Singularity can pull a docker image). Also read: S1 facts
`raw/s1_and_docker_20261114.txt` + chain report §S1; questions `HTCONDOR_CHAIN_QUESTIONS_20261114.md`
(Q-A1/B, Q-D1, Q-S4); adapter review record at paper `mac-htcondor-20261114` @ `68057612`
(`HTCONDOR_ADAPTER_REVIEW_20261114.md`, accepted at `ee6567a0`); upstream HTCondor 23.0 container-universe
docs, ClassAd attribute reference and `condor_attributes.h`/release notes for the container attributes
(links in §2.2/§2.4).

**Hard limits of this review (deliberate).** No SSH, no HTCondor commands, no submission, no git commit/push,
no file written except this review. Current cluster state comes from the committed S1 raw facts
(collected 14 Nov 10:51 CET), not from me; where the raw facts do not measure something I say so.

---

## 1. Files reviewed and pinned (SHA-256, 16-hex prefix)

| File | Bytes | SHA-256 (prefix) |
|---|---|---|
| `s2/probe.sh` | 1228 | `7e10f6ba0204a96e` (byte-identical to last night's reviewed probe) |
| `s2/S2L_local_cpu.jdl` | 386 | `24b83c2167dd10e2` |
| `s2/S2N1_nemo2_l40s.jdl` | 487 | `53ea745094b39301` |
| `s2/S2N2_nemo2_h200.jdl` | 487 | `6072d87572c656b5` |
| `s2/S2T_topas_v100s.jdl` | 444 | `f9a00c6b6790d636` |
| `s2/dryrun/S2L_local_cpu.dry` | 1737 | `b03d16b82898ff07` |
| `s2/dryrun/S2N1_nemo2_l40s.dry` | 1898 | `9b561ac4309431e0` |
| `s2/dryrun/S2N2_nemo2_h200.dry` | 1898 | `c4c67e8f3844114d` |
| `s2/dryrun/S2T_topas_v100s.dry` | 1855 | `705271fc0c9e07bb` |
| `s2/dryrun/*.dry.log` (all four identical) | 47 | `a40749b0dcc3f78c` |

All four dry runs carry `QDate=1794650020` = **2026-11-14T09:53:40Z** (10:53:40 CET), i.e. they are genuine
`condor_submit -dry-run` output for this unit; each `.dry.log` says "1 job(s) dry-run to cluster 1"; the
`JobSubmitFile` in each ad names the matching JDL. Nothing in this unit has been submitted (no
`*.log`/`*.out`/`clusters*`/`queue_times*` under `s2/` at review time).

---

## 2. Checks performed, and results

### 2.1 JDLs against the author's S2 spec

All four: `universe = container`; `container_image = docker://cverstege/alma9-gridjob`;
`executable = probe.sh`; `should_transfer_files = YES`; `when_to_transfer_output = ON_EXIT`;
`transfer_input_files = probe.sh`; `+RequestWalltime = 1800`; own `arguments`/`output`/`error`/`log`;
explicit `RequestCPUs`, `RequestMemory` (MB), `request_disk` (kB); `queue 1`; **no `docker_image` key**;
no `accounting_group`; no `+RequestGPUMemoryMB` (whole-GPU rule).

| ID | JDL | Role per brief | CPUs / Mem MB / Disk kB | GPU | `+RemoteJob` | Requirements (line) |
|---|---|---|---|---|---|---|
| S2L | `S2L_local_cpu.jdl` | ETP local CPU, 1 core | 1 / 2048 / 5 000 000 (L12–14) | – | – | `TARGET.ProvidesETPResources` (L15) |
| S2N1 | `S2N1_nemo2_l40s.jdl` | NEMO2 L40S | 2 / 4000 / 5 000 000 (L12–14) | `request_GPUs = 1` (L15) | `True` (L16) | `TARGET.CloudSite =?= "BwForCluster-Nemo2"` **and** `TARGET.GPUs_DeviceName =?= "NVIDIA L40S"` (L17) |
| S2N2 | `S2N2_nemo2_h200.jdl` | NEMO2 H200 | 2 / 4000 / 5 000 000 (L12–14) | `request_GPUs = 1` (L15) | `True` (L16) | same `CloudSite` **and** `TARGET.GPUs_DeviceName =?= "NVIDIA H200"` (L17) |
| S2T | `S2T_topas_v100s.jdl` | TOpAS V100S | 2 / 4000 / 5 000 000 (L12–14) | `request_GPUs = 1` (L15) | `True` (L16) | `TARGET.GPUs_DeviceName =?= "Tesla V100S-PCIE-32GB"` (L17) |

Result: **conforms to the brief.** Remote jobs carry no `ProvidesETPResources` requirement; the local
smoke does (same selector S1 used to count the 245 ETP-local slots, chain report L21). Device strings are
quoted exactly; `request_GPUs = 1` requests a whole GPU; per-probe CPU/memory requests are explicit although
the brief only fixed them for the 1-core local probe (2 CPUs / 4000 MB is inside every measured GPU slot).

### 2.2 HTCondor container-universe semantics (the core of this unit)

Checked against upstream documentation/source, not assumed:

- `universe = container` (optional but accepted) plus `container_image = docker://<image>` is the documented
  container-universe form; HTCondor parses the image, advertises its type and "will select an appropriate
  runtime" — link: [Container Universe Jobs, HTCondor 23.0 manual](https://htcondor.readthedocs.io/en/23.0/users-manual/container-universe-jobs.html).
  The upstream docs' own example uses `should_transfer_files = YES`, so that combination is supported.
- `ContainerImageSource = "docker"` is the documented value for a docker-registry image; `ContainerImage`,
  `WantContainer`, `WantDockerImage` are real job attributes
  ([`.h` source](https://raw.githubusercontent.com/htcondor/htcondor/main/src/condor_includes/condor_attributes.h):
  `ATTR_HAS_CONTAINER "HasContainer"`, `ATTR_HAS_DOCKER_URL "HasDockerURL"`, `ATTR_WANT_CONTAINER`,
  `ATTR_WANT_DOCKER_IMAGE`), and the machine docs define `HasContainer` as "capable of executing container
  universe jobs" ([machine ClassAds](https://htcondor.readthedocs.io/en/latest/classad-attributes/machine-classad-attributes.html)).
  `JobUniverse = 5` with `WantContainer = true` is the vanilla-with-container encoding, not an error.
- The singularity starter path does accept `docker://` URLs: upstream commit
  [52b2030 / HTCONDOR-3638](https://github.com/htcondor/htcondor/commit/b7d690151db5b5ebe68927113d316eeb97648949)
  fixes "container universe jobs whose image is an url (like docker://) now work when file transfer is off"
  (25.10.1). Our unit uses file transfer **on**, so it does not depend on that fix; it documents that
  `docker://` URLs are served by the Singularity/Apptainer starter, which is exactly the author's premise for
  NEMO2 (no Docker, singularity only).
- Caveat recorded under M3: automatic `--nv`/`--rocm` for Apptainer/Singularity container-universe GPU jobs
  is listed as a **25.14.1** feature in
  [the v25 release notes](https://raw.githubusercontent.com/htcondor/htcondor/main/docs/version-history/v25-version.hist)
  ("Container universe jobs that use the apptainer or singularity runtime now detect AMD or nvidia gpus, and
  add --nv or --rocm appropriately"), while the site is at 25.0.12 (S1 raw L6).

So the design is semantically sound; nothing in the JDLs contradicts HTCondor 25 container-universe behaviour.

### 2.3 Dry-run ClassAds

All four ads show the expected container-universe encoding and all requests:

| Attribute | S2L | S2N1 | S2N2 | S2T | Evidence lines |
|---|---|---|---|---|---|
| `JobUniverse` | 5 | 5 | 5 | 5 | S2L:26, S2N1:27, S2N2:27, S2T:27 |
| `WantContainer` | true | true | true | true | S2L:41, S2N1:43, S2N2:43, S2T:43 |
| `ContainerImage` | `docker://cverstege/alma9-gridjob` | same | same | same | S2L:43, S2N1:45, S2N2:45, S2T:45 |
| `ContainerImageSource` | `"docker"` | same | same | same | S2L:60, S2N1:62, S2N2:62, S2T:62 |
| `WantDockerImage` | true | true | true | true | S2L:50, S2N1:52, S2N2:52, S2T:52 |
| `docker_image` / docker-universe key | absent | absent | absent | absent | grep over the four ads |
| `ShouldTransferFiles` / `TransferInput` | YES / `probe.sh` | same | same | same | S2L:58/40, others :60/:42 |
| `RequestWalltime` | 1800 | 1800 | 1800 | 1800 | S2L:49, others :51 |
| `RequestCpus` / `RequestMemory` / `RequestDisk` | 1/2048/5000000 | 2/4000/5000000 | 2/4000/5000000 | 2/4000/5000000 | S2L:28–29,39; others :29–30,41 |
| `RequestGPUs` | – | 1 | 1 | 1 | S2N1:31, S2N2:31, S2T:31 |
| `RemoteJob` | – | true | true | true | S2N1:20, S2N2:20, S2T:20 |
| `Out`/`Err`/`UserLog`/`Args` | S2L.* | S2N1.* | S2N2.* | S2T.* | per ad |

Synthesized `Requirements` (S2L:34; S2N1/S2N2:36; S2T:36) add `TARGET.HasContainer && TARGET.HasDockerURL`
and the per-request checks (`Disk`, `Memory`, `Cpus`, `GPUs`, `HasFileTransfer`); the S2N1/S2N2 CloudSite and
device-name terms and the S2T device-name term are the ones written in the JDLs; **no remote job carries
`ProvidesETPResources`**. No expression can send a probe to a demonstrably wrong site: the A100/V100S/H200
strings are unique to TOpAS/NEMO2 in the measured pool, and the L40S string is confined to NEMO2 by the
`CloudSite` term (L40S also exists on the local `deepthought2` slot — the `CloudSite` term is what keeps S2N1
off it; do not delete that term).

### 2.4 Device strings, site selectors and the measured pool (S1)

| Probe | JDL string/selector | Measured evidence | Result |
|---|---|---|---|
| S2L | `TARGET.ProvidesETPResources` | chain report L21: 245 ETP-local slots counted under this selector | ✓ selector in use; S1 selected the local site this way |
| S2N1 | `CloudSite =?= "BwForCluster-Nemo2"` + `NVIDIA L40S` | chain report L22 (2422 NEMO2 slots), L25 (6× `NVIDIA L40S`); raw L44–L47 | ✓ exact string |
| S2N2 | same + `NVIDIA H200` | chain report L22, L25 (5× `NVIDIA H200`); raw L44 | ✓ exact string |
| S2T | `Tesla V100S-PCIE-32GB` | chain report L23 (253 TOpAS slots), L25 (14× `Tesla V100S-PCIE-32GB`) | ✓ exact string |

S1 raw L13–L29 confirms `HasSingularity` true on 244/245 ETP, 2422/2422 NEMO2 and 253/253 TOpAS slots, and
`HasDocker` true on 237/245 ETP and 253/253 TOpAS, undefined on NEMO2 — consistent with the author's premise
(NEMO2 singularity-only). The synthesized match gates `HasContainer`/`HasDockerURL` themselves are **not**
among the measured attributes — see M1.

### 2.5 `probe.sh`

Byte-identical (`7e10f6ba…`) to the executable reviewed and accepted last night; I re-read it in full.
It prints: hostname (L8), date (L9), nproc (L10), CPU model (L11), `free -g` (L12), `df -h` of
`/work /ceph /ceph/srv /cvmfs /scratch /tmp $PWD` with a `MISSING` branch (L13–19),
`env | grep -E 'NVIDIA|CUDA'` (L20) and `_CONDOR_` (L21), `nvidia-smi -L` plus a `--query-gpu` line
(L23–28) with a `MISSING` branch, and ends with `exit 0` (L30). It writes nothing (no redirection, no
`mkdir`/`rm`/`mv`), needs no credentials, touches no other user's data, and degrades without failing if an
optional tool is absent (no `set -e`). Expected under container universe: `/work`, `/ceph`, `/ceph/srv`,
`/cvmfs` may legitimately print `MISSING` inside the container; that is a measurement, not a probe failure.
It carries last night's header (L2–L4) and the dead helper `show()` (L29) — N1/N2.

### 2.6 Caps, order and account limits

- **Jobs:** 4 probes ≤ 10 concurrent; whole GPUs (`request_GPUs = 1`, no `+RequestGPUMemoryMB`).
- **GPU hours:** 3 GPU probes × 1800 s = 5 400 s = **1.5 GPU-h** ≤ the author's 10 GPU-h round cap.
- **Walltime:** 1800 s per probe (≤ the earlier 3600 s limit; the 14 Nov instruction sets no stricter one).
- **Order:** S2L (ETP local) alone first, its result inspected, then the three GPU probes — as the brief
  requires. All four are independent single jobs; nothing in the unit submits them together.
- **Pre-existing jobs:** the 10-concurrent cap is account-wide; last night's 7 probes were allowed to stay
  queued (last night's §4.2 "a probe still idle after 4 hours stays queued"), so the operator must read the
  own queue before adding four — M2.

### 2.7 Safety, credentials, write scope

- No JDL or script contains a secret/token/credential, an `condor_rm`/`condor_hold`/SSH/docker/registry
  command, or a path under another user's home. The image `cverstege/alma9-gridjob` is public, so no registry
  credentials are involved (no `docker login`, no proxy).
- Writes stay inside the allowed scope: `log`/`output`/`error` and the transferred outputs land in the submit
  directory `/work/dwong/htcondor_prep_20261114/chain_20261114/s2` (the dry ads' `Iwd`, allowed by chain
  report L3); the probe itself writes nothing; no `/ceph` write. "No deletion anywhere" is respected (nothing
  in the unit deletes or moves anything).
- The unit is read-only against other users' jobs/files: only `condor_submit` of our own four jobs is
  needed; no `condor_q`/`condor_history` of other users is needed by the unit (the recorder queries
  `dwong` only).

### 2.8 Recorder: `r1/scripts/htcondor/htc_events.py` (adapter branch)

- **Right script/right version:** it is the reviewed adapter's queue-time logger, accepted in
  `HTCONDOR_ADAPTER_REVIEW_20261114.md` (adapter @ `68057612`; accepted paper commit `ee6567a0`; the file's
  blob `6e168540…` is identical at both commits). It is **not** on the chain branch, so take it from
  `origin/mac-htcondor-20261114` (`git show origin/mac-htcondor-20261114:r1/scripts/htcondor/htc_events.py`),
  which is a read-only use. It is stdlib-only (`argparse, csv, datetime, json, re, sys, pathlib`), so it runs
  as a plain `python3 htc_events.py …` script (no `-m`, no repo imports, unlike last night's W2).
- **Call shape (from its `main`, lines 216–224):**
  `python3 htc_events.py <log> [--probe JOB=NAME …] [--history history.json] [--year YYYY] [--utc-offset-minutes N] --tsv OUT.tsv`
  — `log` positional (the HTCondor user-log file), `--probe` repeatable (`123.0=P1`), `--tsv` required,
  `--history` optional JSON `{ "<cluster>.<proc>": {"site": "", "host": "", "gpu_name": ""} }`,
  `--year` only needed for the old `MM/DD` log format (HTCondor ≥ 8.8 writes ISO dates; site is 25.0.12),
  `--utc-offset-minutes` decides how zone-less log times are converted to UTC. Its output columns are exactly
  the runbook §4.2 row (`probe, cluster.proc, submit_utc, execute_utc, end_utc, wait_s, run_s, site, host,
  gpu_name, evictions, holds, exit`), and it exits 2 with `STOP:` on a parse error (fail-closed). This is the
  right recorder; the invocation details that matter are in M4 (four separate per-job logs must be combined or
  run per log; the writer overwrites; pass the CET offset).

---

## 3. Findings

**No BLOCKING findings. No MAJOR findings.** The four JDLs are correct for HTCondor 25 container universe and
for the author's S2 design, the dry runs are consistent, the device strings are exact, the caps and the
smoke-first order are fine, and no credential/other-user/write-scope rule is violated. The findings below are
verification and recording items; the first one is the only thing that could make a job match nothing, and it
is fixed by one read-only command recorded before submission.

### MINOR

**M1 — the synthesized match gates `TARGET.HasContainer && TARGET.HasDockerURL` are not in the committed
measured evidence.** *Evidence:* the four dry ads require them (S2L:34; S2N1/S2N2:36; S2T:36); the committed
S1 raw measures only `HasSingularity` and `HasDocker` (raw L13–L29; chain report L19–L23) and does not query
`HasContainer`/`HasDockerURL`; the numbers in the brief (ETP 241/245, NEMO2 2424, TOpAS 247) are not in the
committed raw, whose committed counts are `HasSingularity` 244/245, 2422, 253 and `HasDocker` 237/245,
undefined, 253. `HasDockerURL` is a real HTCondor attribute constant
(`ATTR_HAS_DOCKER_URL`, `condor_attributes.h`) generated by the site's own `condor_submit` 25.0.12, and the
values are expected true because `HasSingularity` is true on every measured slot (a `docker://` URL is served
by either docker or singularity) — but "expected" is not "measured".
*Impact:* if `HasContainer`/`HasDockerURL` were undefined or false on a site, its probe would **idle** —
a match failure — and would be indistinguishable from a pull failure when answering the author's question.
*Exact fix (before submission):* run the read-only per-site query and keep it as raw evidence, e.g.
`condor_status -constraint '<site selector>' -af Name HasContainer HasDockerURL HasSingularity HasDocker`
for the three site selectors, save the output under `raw/` and record the counts in the S2 report. If all
target sites show true: proceed (no JDL change). If any shows undefined/false: do not read an idle job as a
pull failure; record `condor_q -better-analyze <id>` and report the match gate as the cause.

**M2 — the 10-concurrent cap is account-wide; read the own queue before adding four jobs.** *Evidence:*
chain report L3 (≤10 concurrent); last night's probe wave (7 jobs) was explicitly allowed to remain queued
for hours (last night's runbook §4.2), and the committed chain facts do not record the own queue.
*Impact:* if last night's probes are still idle/running, adding S2L + 3 GPU probes could exceed the author's
concurrent-job cap. *Exact fix:* before the first `condor_submit`, record
`condor_q dwong -af ClusterId ProcId JobStatus HoldReason` (and the summary line) in the S2 raw directory and
the report; if own active + 4 > 10, run the smoke job only and sequence the GPU probes as slots free, or put
the conflict in the question list — do not delete or remove anything (author: no deletion anywhere).

**M3 — record the runtime actually used and do not read an empty in-container `nvidia-smi` as "no GPU".**
*Evidence:* HTCondor container universe selects the runtime (docker or singularity) per EP; the measured pool
has docker+singularity on ETP (237/245 docker) and TOpAS, singularity only on NEMO2 (raw L13–L29); the
automatic `--nv`/`--rocm` for Apptainer/Singularity container-universe GPU jobs is a 25.14.1 release-note
feature while the site runs 25.0.12 (raw L6; upstream v25 notes), so GPU visibility *inside* the container is
not guaranteed even when the slot allocation is correct. The probe's `env` grep does not include
`SINGULARITY_*`/`APPTAINER_*` (probe.sh L20–21), and the bare `nvidia-smi` table is not printed (query only,
L24–25).
*Impact:* for NEMO2 the key result is "did the job start at all" (i.e. could Singularity pull the docker
image); a missing `nvidia-smi` is a container-flag artefact, not a failed GPU match, and must not be recorded
as the GPU identity. *Exact fix (no JDL change):* per job, record `LastRemoteHost` and that host's
`HasDocker HasSingularity SingularityVersion HasContainer HasDockerURL`; take the GPU identity from the job/host
ad (`GPUs_DeviceName` of the execute host, or `MachineAttr*` if configured) and from the probe stdout when
present; if `nvidia-smi` is MISSING inside the container, record that as an observation. Optional (one-line
edit, needs a re-review): add `env | grep -iE 'SINGULARITY|APPTAINER|DOCKER'` to probe.sh.

**M4 — exact recorder invocation (right script, but the call shape has traps).** *Evidence:* `htc_events.py`
`main` lines 216–224 (per §2.8); each JDL has its **own** `log` file (`S2L.log`, `S2N1.log`, `S2N2.log`,
`S2T.log`), so a single call needs a combined log, and `write_tsv` overwrites its target; the event log is
zone-less local time (host is CET, S1 raw L3–L4) while the recorder treats zone-less times as UTC unless
told otherwise; the per-job site/host/gpu_name come only from the optional `--history` JSON.
*Exact fix:* after the jobs reach a terminal state:
`cat S2L.log S2N1.log S2N2.log S2T.log > s2_all.log` (or run once per log to four one-row TSVs and merge,
dropping repeated headers); build `history.json` `{"<cluster>.<proc>": {"site": …, "host": …, "gpu_name": …}}`
from `condor_history dwong -limit 100 -af ClusterId ProcId MachineAttrCloudSite0 LastRemoteHost ExitCode RemoteWallClockTime`
(record which attributes existed; GPU identity from probe stdout if no machine attribute is propagated);
then
`python3 htc_events.py s2_all.log --probe <c_S2L>.0=S2L --probe <c_N1>.0=S2N1 --probe <c_N2>.0=S2N2 --probe <c_T>.0=S2T --history history.json --utc-offset-minutes 60 --tsv queue_times.tsv`
Passing the CET offset matters for the `*_utc` columns (wait_s/run_s are differences and unaffected);
verify it once by comparing event 000 of S2L with the recorded submit time, and pass `--year 2026` only if
the logs turn out to use `MM/DD` dates. Record the recorder's exit code (2 = `STOP:` parse failure; never
hand-edit a log to make it parse).

**M5 — the ETP-local smoke may not exercise the Apptainer path, and may land on an old Apptainer.**
*Evidence:* ETP local slots mostly have docker (237/245) as well as singularity (244/245), so the container
universe runtime choice may be docker for S2L; the ETP fleet's `SingularityVersion` is mixed 1.2.5/1.3.4/1.5.x
(chain report L21, L27; Q-S4), and NEMO2 (the actual Apptainer pull test) is all 1.5.4.
*Impact:* an S2L pass validates the universe/image/transfer/pull path but not necessarily Singularity; an
S2L failure on a 1.2.5/1.3.4 node is an environment finding, not a JDL defect. *Exact fix:* record S2L's
`LastRemoteHost` and that host's `HasDocker HasSingularity SingularityVersion` (M3); say in the S2 report
which runtime the evidence supports; do not retry blindly.

### NIT

**N1 — stale probe header.** `probe.sh` L2–L4 still says "night of 13/14 Nov 2026" with the 13/14 Nov runbook
as authority; the file is byte-identical to the reviewed one, so this is cosmetic. Record "S2 uses the
reviewed 13/14 Nov probe unchanged (hash `7e10f6ba…`)" in the S2 report, or re-label in a later edit.
**N2 — dead helper / no bare `nvidia-smi`.** `probe.sh` L29 defines an unused `show()`; L23–25 print
`nvidia-smi -L` and a query but not the full table. Carried from last night's review; no action required for S2.
**N3 — image-tool dependence.** `free`/`awk` presence in `cverstege/alma9-gridjob` cannot be verified
read-only; the script degrades gracefully, and S2L's stdout is the test. If the `df[...]` values are empty,
add a raw `df -h` fallback (one-line edit + re-review).
**N4 — floating image tag.** `docker://cverstege/alma9-gridjob` resolves to `:latest`; the S2 result is
against whatever image was current at pull time. Record the pull time (event log) and, if obtainable, the
image digest/Singularity version; no JDL change needed.
**N5 — submit from the directory that holds `probe.sh`.** `executable = probe.sh` is relative; the dry ads
resolve it to `/work/dwong/htcondor_prep_20261114/chain_20261114/s2/probe.sh` from that `Iwd`. Copy the
committed unit there byte-identically (hashes in §1) and `condor_submit` from that directory; record the exact
commands and cluster IDs.
**N6 — dry-ad `TransferIn=false`.** Legacy submit-side attribute; the authoritative switches
(`ShouldTransferFiles="YES"`, `TransferInput="probe.sh"`, `WhenToTransferOutput="ON_EXIT"`) are all present.
Verify on the real S2L ad (`condor_q -af TransferIn ShouldTransferFiles TransferInput`) if convenient; not a
defect.
**N7 — dry-run command not recorded.** Each `.dry.log` only says "1 job(s) dry-run"; record the exact
`condor_submit -dry-run` loop in the S2 report so the dry output is reproducible.

---

## 4. Verdict, expected submission order, what must be recorded

**What this review accepts:** the four hand-written container-universe JDLs and their `probe.sh`, as hashed
in §1, for submission under the author's S2 design and the chain report's limits — this is the
independent-review gate required by author option (b) for S2 (Q-A1 in the questions file applies option (b)
to S2/S4/S5; it is satisfied for S2 by this review, not for S4/S5).

**Expected submission order (exact):**

1. Accept this verdict. **Do not submit before it.** No submission exists at review time.
2. Pre-submission read-only records: **M1** match gates (`HasContainer`/`HasDockerURL` per site, raw file),
   **M2** own queue (`condor_q dwong`), and the current state of the three target sites (esp. NEMO2 H200
   availability and TOpAS V100S slots). Put them in the S2 raw directory.
3. Copy/verify the unit at `/work/dwong/htcondor_prep_20261114/chain_20261114/s2/` (hashes §1), submit
   **`S2L_local_cpu.jdl` alone** from that directory, and record the cluster ID + submit UTC.
4. Inspect S2L's result before scaling: terminal state, `.out`/`.err`/`.log`, event 000/001/004/005/012,
   `ExitCode`, and (if idle) `condor_q -better-analyze`; a hold on image pull is recorded as the pull
   outcome, not retried. **If S2L fails because of the universe/image/transfer, do not submit the GPU probes
   until the cause is understood** (they share the JDL shape).
5. Then submit **`S2N1_nemo2_l40s.jdl`, `S2N2_nemo2_h200.jdl`, `S2T_topas_v100s.jdl`** (the brief requires
   only that S2L's result comes first; the three are independent — submitting them together is within the
   cap, or sequence them if you want a smaller blast radius). For each: cluster ID, submit/execute/end UTC,
   terminal state, `.out`/`.err`/`.log`, site/host, runtime evidence (M3), GPU identity, and — for NEMO2 —
   the explicit distinction start-vs-idle-vs-pull-hold.
6. Run the recorder per **M4** and produce the S2 `queue_times.tsv` (four rows; runbook §4.2 columns) plus
   `clusters.tsv`/history raw; then commit the S2 report and raw files with the review file.

**What must be recorded per job:** event log (`log=`), stdout/stderr (`out=`/`err=`), submit/execute/end UTC,
wait/run seconds, site and host (`MachineAttrCloudSite0`/`LastRemoteHost`, saying which attribute existed),
GPU identity, evictions/holds/exit, the container runtime and the execute host's `HasDocker`/`HasSingularity`/
`SingularityVersion`, and the image-pull outcome (start = pull worked; hold/`InvalidDockerImage`/event text =
pull failure — the recorder classifies it as `htcondor_image_pull`).

**Residual risk I carry (none of it blocking):**

1. **Match-gate values (M1)** are the only "may match nothing" risk: expected true because singularity is
   present on every measured slot, but not committed — the single read-only check above settles it.
2. **NEMO2 egress / pullability** is untested: whether the EPs can reach Docker Hub / the apptainer transport
   is exactly what S2 measures; a pull hold is the answer, not a JDL bug.
3. **Runtime selection and in-container GPU visibility (M3)** may make the GPU section of the probe incomplete
   even on a correctly allocated GPU; record the allocation separately.
4. **Pre-existing own jobs (M2)** may consume the 10-concurrent cap; check before adding four.
5. **Old Apptainer on part of the ETP local fleet (M5/Q-S4)** could make S2L fail on an otherwise-fine JDL;
   record the node/version and treat it as an environment finding.
6. **Floating `:latest` image (N4)**: the S2 result is tied to the image pulled at job start, not to a pinned
   digest.
7. **No cluster access here:** current slot states (drained H200s, unclaimed V100S, NEMO2 queue) are unknown
   to me; they are read at submission time and recorded.

VERDICT: ACCEPTED
