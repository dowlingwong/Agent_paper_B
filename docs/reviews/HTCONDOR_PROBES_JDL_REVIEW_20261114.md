# Independent pre-submission review — HTCondor probe wave 1 (P1–P7), night of 13/14 Nov 2026

**Reviewer role:** fresh, independent, read-only reviewer. Not the author, not the executing agent; I did
not write, submit or run any of the reviewed files and I have no cluster access.

**Date/time of review:** 13 November 2026, 23:44–00:02 CET (Europe/Berlin).

**Reviewed unit:** `docs/r1/reports/htcondor_prep_20261114/probes/` — `probe.sh`, `P1.jdl`–`P7.jdl`, and
`dryrun/P1.dry`–`P7.dry` + `dryrun/P1.dry.log`–`P7.dry.log`. Branch `htcondor-prep-20261114`, HEAD
**`c78f8c4a`**; the unit is **untracked** in the working tree at review time, so it is pinned below by
SHA-256 (16-hex prefixes; a later byte-level change invalidates this review and needs a re-check).

**Operative procedure reviewed against:** runbook `docs/r1/prompts/HTCONDOR_PREP_RUNBOOK_20261114.md`
§0.2 (smoke-first: dry rendering → fresh review → one real job), §0.4 C (≤10 jobs, walltime ≤3600 s, one
whole GPU each, ≤6 GPU-h), §4 (probe content), §4.1 (P1–P7 table and step order), §4.2 (queue-time
record), §0.5 (STOPs); errata `docs/r1/prompts/HTCONDOR_PREP_RUNBOOK_ERRATA_20261114.md` §A4
(timetable/priority), §A6 (GPU-hour and 10-job accounting), §A7 (F12 P3 best-effort, F13, etc.), §B
(fact policy); measured evidence `raw/host_facts_A.txt`, `raw/host_facts_B.txt`, and (context only)
`POOL_FACTS.md`.

**Hard limits of this review (deliberate).** No SSH, no HTCondor commands, no job submission, no git
commit/push, no file written except this review. Every statement about *current* cluster state comes
from the measured raw files (collected 23:38–23:44 CET), not from me; where the raw files are ambiguous
I say so. I read the operator's adjacent files `POOL_FACTS.md`, `HTCONDOR_QUESTIONS_20261114.md` and the
two scripts that appeared at 23:46 (`submit_probe.sh`, `parse_queue_times.py`) only as context — they
are not part of this unit and are not accepted or rejected here.

---

## 1. Files reviewed and pinned (SHA-256, 16-hex prefix)

| File | Bytes | SHA-256 (prefix) |
|---|---|---|
| `probes/probe.sh` | 1228 | `7e10f6ba0204a96e` |
| `probes/P1.jdl` | 367 | `0fd917255a0fae61` |
| `probes/P2.jdl` | 369 | `738ad2aea4540e80` |
| `probes/P3.jdl` | 342 | `432e56ea6042c4d8` |
| `probes/P4.jdl` | 425 | `721a678cda4009be` |
| `probes/P5.jdl` | 425 | `7f6e0e8dabe90fa3` |
| `probes/P6.jdl` | 460 | `8c3eeaa1906addce` |
| `probes/P7.jdl` | 460 | `5fcfe3bb151491ca` |
| `probes/dryrun/P1.dry` … `P7.dry` | 1597–1748 | `242def74e8cc8416`, `c9de73f2b08e5d29`, `d6cc83f77d00f16f`, `bb0393668838dacd`, `ea2c467beb1aca65`, `e3bb785442e40348`, `7af461cd70ceea01` |
| `probes/dryrun/P*.dry.log` (all seven identical) | 47 | `a40749b0dcc3f78c` |

Hashes of the seven JDLs and seven dry-run ClassAds were re-checked after the 23:46 additions and are
unchanged; the dry runs therefore correspond to the JDLs reviewed here.

---

## 2. Checks performed, and results

### 2.1 `probe.sh` against runbook §4 and the task checklist

| Required print (§4) | Location | Result |
|---|---|---|
| `hostname` | L8: `hostname -f 2>/dev/null \|\| hostname` | ✓ with fallback if FQDN lookup fails in the container |
| `nproc` | L10 | ✓ printed (interpretation caveat M4) |
| CPU model | L11: first `model name` line from `/proc/cpuinfo` | ✓ |
| `free -g` | L12: `free -g 2>&1` | ✓ printed; image-tool dependence N2 |
| `df -h` of `/work`, `/ceph`, `/ceph/srv`, `/cvmfs` and the job scratch | L13–L19: loop over `/work /ceph /ceph/srv /cvmfs /scratch /tmp "$PWD"`, `-e` guarded, `MISSING` otherwise, values extracted with `awk` | ✓ (also `/scratch` and `/tmp`); raw `df` lines not kept (N2) |
| `env \| grep -E 'NVIDIA\|CUDA\|_CONDOR'` | L20 (`NVIDIA\|CUDA`, head -20), L21 (`^_CONDOR_`, head -40) | ✓; split over two commands, truncation only |
| `nvidia-smi -L` plus a query | L23–L28: guarded by `command -v nvidia-smi`; `-L`, then `--query-gpu=name,uuid,memory.total,driver_version,compute_cap`; `MISSING` branch | ✓ (no bare full `nvidia-smi` table — N1) |
| exits 0 | L30: unconditional `exit 0` | ✓ as the runbook requires; a hard environment failure still exits 0 (by design; stdout carries the evidence) |
| cannot write outside the job sandbox | No redirection to files, no `mkdir`/`rm`/`mv`; only `echo`, `df`, `free`, `env`, `grep`, `sed`, `cut`, `awk`, `nvidia-smi`; no network, no `sudo`, no docker socket, no credentials | ✓ |
| safe in the official image | `#!/bin/bash` shebang; plain POSIX constructs; only comment on L3 is UTF-8 (`§`); uses `free`, `awk`, `cut`, `sed`, `grep`, `head`, `nproc`, `df` | ✓ for bash/dash-safe syntax; presence of `free`/`awk` in `cverstege/alma9-gridjob` is an image-content question (N2), not a script defect — the script degrades without failing |

Also checked: the script transfers nothing but `probe.sh`, writes nothing, and its `_CONDOR_*`/GPU output
contains no credentials. The dead helper on L29 (`show()`) is unused (N3).

Expected-output note: in `universe = docker` only the job sandbox is bind-mounted; `/work`, `/ceph`,
`/ceph/srv`, `/cvmfs` may legitimately print `MISSING` even on a local ETP slot. That is a measurement,
not a probe failure, and the report should read it that way (the "/work is mounted" question is what I1
would have tested with our own image, which A3 defers).

### 2.2 Each JDL against runbook §4.1

All seven: `universe = docker`; `docker_image = cverstege/alma9-gridjob`; `should_transfer_files = YES`;
`when_to_transfer_output = ON_EXIT`; `transfer_input_files = probe.sh`; `executable = probe.sh`;
`+RequestWalltime = 1800`; distinct `output`/`error`/`log` (`Pn.out`/`Pn.err`/`Pn.log`); explicit
`RequestCPUs`, `RequestMemory` (MB) and `request_disk` (kB); one `queue 1`. The JDL field names used
(`RequestCPUs`, `RequestMemory`, `request_GPUs`, `request_disk`, `+RequestWalltime`, `+RemoteJob`) were all
accepted by the installed `condor_submit` (25.0.12) — proven by the ClassAds below, so there is no
silent-typo risk.

| ID | Site selection (requirements / attributes) | CPUs | Mem MB | Disk kB | GPUs | RemoteJob | §4.1 match |
|---|---|---|---|---|---|---|---|
| P1 | `requirements = TARGET.ProvidesETPResources` (local CPU) | 1 | 2048 | 5 000 000 | – | – | ✓ |
| P2 | as P1, 8 cores | 8 | 16384 | 10 000 000 | – | – | ✓ |
| P3 | no `requirements`; `+RemoteJob = True` (remote CPU, best effort) | 1 | 2048 | 5 000 000 | – | True | ✓ (F12: best effort, no `ProvidesETPResources` requirement) |
| P4 | `+RemoteJob = True`, `request_GPUs = 1`, `TARGET.GPUs_DeviceName =?= "NVIDIA A100-PCIE-40GB"` | 2 | 4000 | 5 000 000 | 1 | True | ✓ |
| P5 | as P4 with `"Tesla V100S-PCIE-32GB"` | 2 | 4000 | 5 000 000 | 1 | True | ✓ |
| P6 | `+RemoteJob = True`, `request_GPUs = 1`, `TARGET.CloudSite =?= "BwForCluster-Nemo2" && TARGET.GPUs_DeviceName =?= "NVIDIA L40S"` | 2 | 4000 | 5 000 000 | 1 | True | ✓ |
| P7 | as P6 with `"NVIDIA H200"` | 2 | 4000 | 5 000 000 | 1 | True | ✓ |

Deviations/notes that are not defects: §4.1 does not give CPU/memory for P4–P7, but §4 requires explicit
requests; 2 CPUs / 4000 MB fits every measured GPU slot (NEMO2 16 CPUs / ~126 GB; V100S node 14 CPUs /
~109 GB; A100 node ~435 GB in `host_facts_A.txt` L84–L106). §4.1 fixes no disk value; 5 000 000 kB (P2:
10 000 000 kB) is explicit and small. No `accounting_group` is set, as §0.4 A / A7-F16 require with no
usable history; no `+RequestGPUMemoryMB` (forbidden, whole GPU only); no node/site fields beyond §4.1.

### 2.3 Dry-run ClassAds (`condor_submit -dry-run` output)

All seven ClassAds carry `JobUniverse=5` (docker), `WantDocker=true`,
`DockerImage="cverstege/alma9-gridjob"`, `ShouldTransferFiles="YES"`, `WhenToTransferOutput="ON_EXIT"`,
`TransferInput="probe.sh"`, `RequestWalltime=1800`, the per-probe `RequestCpus`/`RequestMemory`/
`RequestDisk`, `RequestGPUs=1` for P4–P7 (absent for P1–P3), `RemoteJob=true` for P3–P7 (absent for
P1/P2), and the matching `Out`/`Err`/`UserLog`/`Args`/`JobSubmitFile=<Pn>.jdl`. `QDate=1794609766` is
2026-11-13T22:42:46Z = 23:42:46 CET; each `.dry.log` says "1 job(s) dry-run to cluster 1". The ads are
therefore genuine `condor_submit -dry-run` output for these JDLs (the exact command loop is not recorded
— N5).

Synthesized `Requirements` are consistent with the JDLs and with the local/remote rule:

- P1: `(TARGET.ProvidesETPResources) && (TARGET.Arch == "X86_64") && TARGET.HasDocker && (TARGET.Disk >= RequestDisk) && (TARGET.Memory >= RequestMemory) && (TARGET.HasFileTransfer)`
- P2 adds `(TARGET.Cpus >= RequestCpus)` (correct: with `RequestCPUs = 8` the clause is needed; with the
  default 1 it is correctly omitted for P1/P3).
- P3: no `ProvidesETPResources` term — **correct**, a remote job must not require it.
- P4/P5 add `(TARGET.Cpus >= RequestCpus) && (TARGET.GPUs >= RequestGPUs)` and the device-name term; no
  `ProvidesETPResources` term — **correct** for `+RemoteJob = True`.
- P6/P7 add `(TARGET.CloudSite =?= "BwForCluster-Nemo2" && <device>)`; the parenthesis keeps `=?=` pairs
  separate under the `&&`, i.e. "CloudSite AND device name", which is the intended reading.

No expression would send a probe to a demonstrably wrong site: the A100 and V100S strings occur only on
TOpAS in the measured pool, and the two NEMO2 device strings are combined with `CloudSite`. The one
wrong-site hazard is that `NVIDIA L40S` **also** exists on the local `deepthought2.etp.kit.edu` slot
(`host_facts_A.txt` L86, `host_facts_B.txt` L29): if the `TARGET.CloudSite` term were ever deleted or
mistyped, P6 would match the local L40S (wrong site). See M1.

### 2.4 Device strings against the measured pool (must match exactly)

| Probe | String in JDL | Measured evidence | Match |
|---|---|---|---|
| P4 | `NVIDIA A100-PCIE-40GB` | `host_facts_B.txt` L26: `slot1@c03-001-167.gridka.de NVIDIA A100-PCIE-40GB … 8 Unclaimed`; `POOL_FACTS.md` §2 | ✓ exact |
| P5 | `Tesla V100S-PCIE-32GB` | `host_facts_B.txt` L12–L25 (c03-001-159 slots); `POOL_FACTS.md` §2 | ✓ exact |
| P6 | `NVIDIA L40S` | `host_facts_B.txt` L30–L32 (three `nemo2_gpu-*@g3606.nemo.privat` slots, Unclaimed); L29 local deepthought2 (excluded only by `CloudSite`) | ✓ exact (site term M1) |
| P7 | `NVIDIA H200` | `host_facts_B.txt` L33 (`nemo2_gpu-71f4f514cf@g4401.nemo.privat`, **Drained** at ~23:40 CET); `host_facts_A.txt` L90 had it Idle at 23:38 CET; `POOL_FACTS.md` §2 | ✓ exact string; availability M3 |

`CloudSite` and `ProvidesETPResources` themselves are **not** present in the measured raw output, so the
attribute *names/values* used in P1/P2/P6/P7 are not verified by tonight's facts (M1, M2).

### 2.5 10-job cap, 6 GPU-h cap and ordering (A6 / §0.4 C / A4)

- **Jobs:** wave 1 = 7 jobs ≤ 10. The account's one non-owned idle/held job (759618, `POOL_FACTS.md` §1)
  is not ours and is not counted.
- **GPU hours:** P4–P7 × 1800 s = 7 200 s = **2.0 GPU-h**, below the A6 5.0 GPU-h stop margin and the
  §0.4 C 6 GPU-h cap; each requests exactly one whole GPU (`request_GPUs = 1`) and no shared-memory
  attribute. Idle probes add no GPU time; evictions/restarts are counted by A6's
  `RemoteWallClockTime` register, which fits 2.0 GPU-h with large margin.
- **Wave 2 (if reached):** A4 resubmits P1, P3, P4, P6. A6's "≤ 6 own active before a resubmission" makes
  it 6 + 4 = 10, so the 10-job cap is not breached; added GPU time is +1.0 GPU-h → ~3.0 GPU-h register,
  below the 5.0 stop and the 3.5 P6-drop trigger.
- **Ordering:** A6/§2 requires P4–P7 in wave 1; nothing in the JDLs or the unit fixes an order. The
  required order remains P1 alone → inspect its result → P2–P7 together (`submit_probe.sh`, which appeared
  at 23:46 and is outside this unit, submits exactly one JDL per invocation and does not batch all seven,
  so it is compatible with that order). No conflict between the 10-job cap and P1-first.
- **Timetable:** A4 wants the review accepted before submission (00:50–01:10 window, all wave 1 by 01:15;
  clock shifted, 05:30 anchored). The submission must not start before this verdict is accepted.

### 2.6 Safety, credentials, other users

- No JDL or script in the unit contains a secret, token, path under another user's home, `condor_rm`,
  `condor_hold`, SSH, docker or registry command, or any write outside `/work/dwong/htcondor_prep_20261114/`
  and the per-job sandbox. The probe writes nothing at all; it only reads metadata/env/GPU state.
  `submit_probe.sh` (outside unit) writes only `clusters.tsv` in our probes directory; `parse_queue_times.py`
  queries only `condor_history dwong` / `condor_q dwong` (own jobs) and writes only `queue_times.tsv`.
- No submission evidence exists in the worktree at review time (no `clusters.tsv`, `queue_times.tsv`,
  `P*.log/out/err`), and `host_facts_B.txt` L5–L8 showed zero own jobs at 23:39 CET — consistent with the
  smoke-first rule being respected. If a submission happened before this file was written, it violates
  §0.2 and must be reported, not covered up.

---

## 3. Findings

**No BLOCKING findings. No MAJOR findings.** The unit is conformant, safe and dry-runs cleanly; the
findings below are verification gaps and presentation/interpretation issues, each with an exact fix.

### MINOR

**M1 — `TARGET.CloudSite =?= "BwForCluster-Nemo2"` (P6/P7) is not confirmed by any measured fact.**
*Evidence:* `P6.jdl` L17, `P7.jdl` L17; `host_facts_A.txt` L84–L106 and `host_facts_B.txt` L27–L33 report
only slot name, device string, driver/version, GPU count and state — no `CloudSite` attribute. `POOL_FACTS.md`
§2 confirms the four **device strings** only, and errata §B itself lists "the exact CloudSite string" as
UNVERIFIED (L88). `HTCONDOR_QUESTIONS_20261114.md` Q5 says the ClassAd names are "confirmed by
dry-run/measured slots"; the dry run only proves that `condor_submit` accepts the expression — it cannot
prove that a machine carries `CloudSite` — so for `CloudSite` that claim is unsupported.
*Impact:* if the attribute name or value differs, P6 and P7 evaluate to false/undefined and both idle
forever; 2 of the 4 GPU probes yield nothing, and the idle could be misread as "NEMO2 has no capacity".
Mutating the term is worse: without `CloudSite`, P6 can match the local `deepthought2` L40S (see §2.3) —
the wrong site.
*Exact fix (before P2–P7):* one read-only check on the pool, e.g.
`condor_status -pool f03-001-140-e.gridka.de -constraint 'TotalSlotGPUs>0' -af Name CloudSite GPUs_DeviceName`
(and the same against the default collector), recorded verbatim in `POOL_FACTS.md` / the report. If the
attribute exists with the documented value: no change. If it exists with a different value: substitute
the **measured value** in both JDLs and record the substitution (literal substitution of a measured
fact — no new review round). If the attribute is absent: submit as-is, and if P6/P7 idle run
`condor_q -better-analyze` and record "CloudSite absent/unmatched" as a question; **do not** replace the
term with a fabrication and do not drop it.

**M2 — `TARGET.ProvidesETPResources` (P1/P2) is not confirmed by tonight's measured facts.**
*Evidence:* `P1.jdl` L15, `P2.jdl` L15; the attribute appears nowhere in `raw/host_facts_A.txt` or
`raw/host_facts_B.txt` (the §2 queries did not ask for it), errata §B L88 lists its exact ClassAd name as
UNVERIFIED, and the earlier review's fact ledger marks it UNVERIFIED
(`HTCONDOR_PREP_RUNBOOK_REVIEW_20261114.md` L112).
*Impact:* if the name is wrong, P1 — the smoke job whose result gates everything — and P2 match nothing;
an idle P1 would be evidence about a wrong expression, not about local CPU capacity.
*Exact fix:* after submitting P1 and before drawing any conclusion from an idle, run the read-only
`condor_status -af Name ProvidesETPResources HasDocker` (local collector) and
`condor_q -better-analyze <P1 cluster>`; record both. If the attribute is absent, record it and do **not**
submit P2 under the same requirement (P2 shares it); P3–P7 are independent remote classes and may proceed
once P1's result is recorded. Add the finding to the question list. Note also that
`A9`/`POOL_FACTS.md` show the docker daemon unreachable **on deepthought** — local docker-universe
capacity is exactly what the P1 smoke is there to measure; an idle or held P1 must be checked against
`TARGET.HasDocker` before being read as "pool busy".

**M3 — P7 has no eligible H200 slot in the measured pool (expected, record don't misread).**
*Evidence:* `host_facts_B.txt` L33: the only visible H200 slot
`nemo2_gpu-71f4f514cf@g4401.nemo.privat` is **Drained** (~23:40 CET); `host_facts_A.txt` L90 had it
`Unclaimed Idle` at 23:38 CET; `POOL_FACTS.md` §2 says "Drained at 23:40; previously Idle". Only one H200
slot is visible in either snapshot.
*Impact:* P7 will very likely stay idle (or wait for the slot to return). That is a valid measurement,
not a JDL defect, and no device string or request is wrong. It must not be read as "H200 unavailable" in
general, and it must not trigger a JDL edit or a different site.
*Exact fix:* submit P7 with the wave as A6 mandates ("wave-1 P4–P7 are mandatory"); record the slot state
at submit time, the `condor_q -better-analyze` output if it idles, and `>4h (still idle at <time>)` per
§4.2 if it lasts; register 0 GPU-h for an idle P7. Do not let P7 block P4–P6 or the +3 h sample, and do not
`condor_rm` it except under A6's own-idle-duplicate rule before a resubmission.

**M4 — `nproc` is not the job's allocated CPU count.**
*Evidence:* `probe.sh` L10 prints `nproc`; the jobs request 1/8/2 CPUs (`P*.jdl` L12, P2 `RequestCPUs = 8`).
In docker universe the allocation is a CFS quota, not a CPU-affinity mask, so `nproc` inside the container
normally reports the **host's** CPUs, not `RequestCpus`.
*Impact:* the runbook-required `nproc` is printed (check passes), but a reader could mistake it for the
allocation; the queue-time/environment record must use the requested value from the job ad.
*Exact fix:* no JDL change required; in `queue_times.tsv`/the report record the requested CPUs from the
job ad (`condor_q -af RequestCpus`) next to `nproc`, and note the difference. Optionally add
`cat /sys/fs/cgroup/cpu.max 2>/dev/null` (cgroup v2) to the probe — a small edit that would need a
one-line re-review.

**M5 — request-disk/MB values are fine, but one measured A100 line is ambiguous — check P4 at submission.**
*Evidence:* the runbook §2 GPU query is `-af:t Name CPUs Memory Disk GPUs`; `host_facts_A.txt` L99 shows
`slot1@c03-001-167.gridka.de 0 445614 2509185867 0`, i.e. under that attribute order 0 CPUs / 0 GPUs,
whereas `host_facts_B.txt` L26 shows the same slot as `NVIDIA A100-PCIE-40GB … 8 Unclaimed` and
`POOL_FACTS.md` §2 lists 8 GPUs, Unclaimed. The raw files do not record the exact §2 commands, so the
column mapping cannot be resolved here.
*Impact:* if the A100 partitionable slot really advertises 0 CPUs/0 GPUs, P4 (`RequestCPUs = 2`) matches
nothing; if (more likely, per the device listing) it is Unclaimed with 8 GPUs, P4 is fine.
*Exact fix:* no JDL change. If P4 idles, run `condor_q -better-analyze` and
`condor_status -pool c03-001-140.gridka.de -constraint 'Name =?= "slot1@c03-001-167.gridka.de"' -af Name Cpus Memory Disk GPUs`,
record it, and report the ambiguity of the §2 record rather than guessing.

### NIT

**N1 — no bare `nvidia-smi` table.** `probe.sh` L24–L25 prints `-L` and the targeted query (which covers
device name, UUID, total memory, driver version, compute cap) but not the full `nvidia-smi` output that
runbook L162 literally asks for ("`nvidia-smi -L` plus `nvidia-smi`"). The task's own check accepts "a
query"; the essentials are captured. *Fix (optional):* add `nvidia-smi 2>&1 | head -40`.

**N2 — image-tool dependence for `free` and `awk`.** `free -g` (L12) is procps-ng and `awk` (L15) is used
only to summarize `df`; neither is guaranteed by an AlmaLinux 9 base (a "gridjob" image probably has
them, but this cannot be verified read-only). The script is robust (no `set -e`, unconditional `exit 0`):
a missing tool prints an error/blank field rather than failing the job. P1's stdout is the test; if the
`free`/`df[...]` values are empty there, add a fallback that also prints raw `df -h "$p" | tail -n +2`
and record it (small edit, one-line re-check). *Not a defect until P1 shows it.*

**N3 — dead `show()` helper** on `probe.sh` L29 is never called. *Fix:* delete L29.

**N4 — untracked unit / no recorded dry-run command.** The whole `probes/` tree is untracked
(`git status` → `?? docs/r1/reports/htcondor_prep_20261114/`); this review pins it by hash, and
`P*.dry.log` only says "1 job(s) dry-run". *Fix:* commit `probes/` + `dryrun/` together with the report
(the A4/F23 deliverable list does not name them), and record the exact dry-run loop in the report so the
dry output is reproducible.

**N5 — render path binds the submission CWD.** `executable = probe.sh` is relative; the dry ads show
`Cmd="/work/dwong/htcondor_prep_20261114/probes/probe.sh"` and `Iwd=…/probes`, i.e. the dry run was done
from that directory. `submit_probe.sh` (outside unit) does `cd` there, so this is handled — but any other
`condor_submit` invocation must also run from `probes/` (or use absolute paths), otherwise submission
fails fast. Also recorded: runbook §4's "one directory per probe" is implemented as one shared `probes/`
directory with per-probe file prefixes; benign (no filename collisions — see the dry ads), but the
deviation should be stated in the report. *Fix:* document "submit from `/work/dwong/htcondor_prep_20261114/probes/`"
or use absolute paths.

**N6 — dry-run artifact `TransferIn=false`.** All ads show `TransferIn=false` beside
`ShouldTransferFiles="YES"` and `TransferInput="probe.sh"` (`P1.dry` L24, `P6.dry` L25). `TransferIn` is a
legacy submit-side attribute; the authoritative switches are the three above. *Fix:* verify on the real P1
ad with `condor_q -af TransferIn ShouldTransferFiles TransferInput`; if `probe.sh` were not transferred the
job fails fast (executable missing) — the smoke step catches it.

**N7 — image tag is floating.** `docker_image = cverstege/alma9-gridjob` resolves to `:latest`; the probe
environment is therefore not pinned to an image digest. Acceptable for a resource/queue probe, but the
report should say the environment fingerprint is image-`latest`-dependent. *Fix:* record the resolved
image (e.g. digest seen at the execute site, if exposed) with the probe outputs.

---

## 4. Verdict, expected submission order, residual risk

**What this review accepts:** the unit `probes/{probe.sh,P1.jdl..P7.jdl,dryrun/*}` as hashed in §1,
executed under runbook §0.2/§0.4 C/§4.1/§4.2 and errata A4/A6/A7/§B: all seven JDLs conform to the
§4.1 table, all required requests are explicit and present in both the JDLs and the synthesized
ClassAds, `probe.sh` prints everything §4 requires, exits 0, writes nothing it should not, and contains no
secrets or cross-user paths, the device strings match the measured pool exactly, the dry runs are
consistent with the JDLs, and the wave is inside the 10-job and 6 GPU-h caps.

**Expected submission order (must be followed):**

1. Accept this verdict; **do not submit before it** (and note M4/M1/M2 first). No submission evidence
   exists in the worktree as of 23:48 CET; if there is one, report it as a §0.2 breach.
2. Run the two read-only checks in **M1** (`CloudSite` on the NEMO2 slots) and **M2**
   (`ProvidesETPResources`, `HasDocker` on the local slots); record them. Correct a wrong measured
   `CloudSite` value literally, never delete the term.
3. Submit **P1 alone** (`./submit_probe.sh P1`), then inspect its result per §4.2: `P1.out`/`P1.err`,
   event log 000/001/005/012, `ExitCode`/`JobStatus`, and the GPU/CPU fingerprint. If it is idle or held,
   run `condor_q -better-analyze` and check `TARGET.HasDocker`/`ProvidesETPResources` before reading it as
   a capacity measurement. Do not submit P2 while P1's failure is plausibly the shared local requirement.
4. Only after P1's result is recorded, submit **P2–P7** together (one `submit_probe.sh` call each, same
   directory); fill `clusters.tsv` and then `queue_times.tsv` exactly as §4.2 + A7-F13 describe, with the
   site/host from the actual machine attribute used.
5. Keep the A6 discipline for the +3 h sample (≤6 own active, GPU register, own idle duplicates only)
   and P7's expected idle (M3). No `condor_rm`, no resubmission, and no wave-2 work on a job that belongs
   to anyone else.

**Residual risk I carry (all non-blocking):**

1. **Unverified ETP ClassAds** `ProvidesETPResources`, `CloudSite` (M1/M2) — the only real "matches
   nothing" risk in the unit; mitigated by the two read-only checks, `condor_q -better-analyze`, and the
   fact that the probes are exactly the instrument for this question. Never "fix" an idle by dropping a
   requirement (P1/P2 would fall back to non-ETP slots; P6 could land on deepthought2's L40S).
2. **P7/H200 currently Drained** (M3) — P7 is likely an idle data point tonight; that is a measurement,
   not a failure, and it consumes no GPU time.
3. **Image contents/delivery not verifiable from here**: bash/`free`/`awk` presence in
   `cverstege/alma9-gridjob`, GPU runtime injection, and whether the execute sites can pull the image.
   P1's stdout/exit is the first evidence; a missing tool degrades the record, a failed pull fails fast.
   Docker daemon unreachable on deepthought (`host_facts_A.txt` L119–L123) says nothing definitive about
   execute nodes, so P1 is the smoke test for that too.
4. **Measured-fact ambiguities** carried from the §2 record (M5: the A100 slot's `-af:t` line; the
   H200 Idle→Drained transition between the two snapshots). The probes must be read against `condor_q
   -better-analyze`/`condor_status` at submission time, not against a stale assumption.
5. **Interpretation**: `nproc` and the docker-container `MISSING` `df` lines must be recorded as
   observations, not as allocation/availability conclusions (M4, §2.1).

VERDICT: ACCEPTED
