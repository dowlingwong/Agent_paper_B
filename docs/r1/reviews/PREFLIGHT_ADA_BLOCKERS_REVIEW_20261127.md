# Independent review — D.3 HTCondor preflight and Ada P.4 runtime blocker (27 November 2026)

Verdict: CHANGES REQUIRED

**Reviewer.** I am an independent, AI-assisted reviewer in a fresh session. I did not write either record under
review, I did not submit either HTCondor job, and I did not connect to Ada or to any cluster. This was a desk
review of the committed records, captures and the reviewed launcher code: I opened no credential, secret, label,
evaluation or sealed file, made no SSH connection and changed nothing except writing this review file. The
reviewed branch was not modified.

**Summary.** The substantive findings are supported. Job `760148` asked for an L40S and could not match because
the only L40S slot has `Start = false`; the TOpAS A100 parents `c03-001-167` and `c03-001-179` have no free GPU
and `c03-001-175` is administratively closed. Under `zli538` the reviewed direct launcher has no usable runtime:
Apptainer is absent and Docker's socket is permission-denied, and the filled config may only say `apptainer` or
`docker`. Both records correctly stop short of claiming a preflight, probe, fill or evidence run, and both frame
the result as a capacity/host blocker rather than a STOP of evidence. Three defects nevertheless prevent
acceptance as written: the A100 job was submitted with an L40S-only payload that would refuse an A100 if it ever
matched, the `760149` no-match claim has no queue or analysis capture behind it, and the nested capture manifest
does not verify. Two further evidence gaps are minor.

## Inputs reviewed

| Input | Ref | sha256 |
|---|---|---|
| Reviewed branch tip | `origin/compute-preflight-blockers-20261127` @ `c491896472ba6b17052c3f91ec384a49d991902a` | — |
| Base | `origin/main` @ `e153df24ee3435bbe0b2fa994297b15250550c30` | — |
| D.3 record | `docs/r1/reports/d3_preflight_20261127/D3_HTCONDOR_PREFLIGHT_20261127.md` | `f678189449ea9b95293e9662aaa3c1a9d495e70a3da54cb9034bdfef8d94e8f9` |
| D.3 report manifest | `…/d3_preflight_20261127/SHA256SUMS` | `ef0f8970ef7f87bd85ecc493a36d54240f4d1a64fd1ebf42e8ef42a92fae7c28` |
| D.3 capture manifest | `…/d3_preflight_20261127/captures/SHA256SUMS` | `a2a489271e9ab7a48cadd447d205648c55f9921747b273da7247f963e0bd30cc` |
| D.3 payload | `…/d3_preflight_20261127/preflight.sh` (mode 100755) | `ed9e6d10dc0cf5f64998d0d5883c06ba898f05126922336f7dbacfada4a27894` |
| Ada record | `docs/r1/reports/ada_p4_20261127/ADA_P4_PROBE_BLOCKER_20261127.md` | `3bff106bfb393fc65b980998d90d7db08980bd07a6e8cc85413e3f72bdfd468f` |
| Ada host check | `…/ada_p4_20261127/host_check.txt` | `64622a2db84ee673916605549a0b7c6c2ade46a47abcf2d14d80ae2220bb74ff` |
| Ada report manifest | `…/ada_p4_20261127/SHA256SUMS` | `c52813f82273ae91be6a5faab93cfb9c388e486f59cbdf5169d30b9bd0b1b3cc` |
| Direct launcher | `r1/scripts/htcondor/trackp_p4/p4_direct.py` @ `origin/main` | `29ee656b0897aaa8cab351969e61736d661953da2b97b3aca515e06fa38be087` |
| Host-config filler | `r1/scripts/htcondor/trackp_p4/p4_fill_host_config.py` @ `origin/main` | `f65d8f7671a7e0bf69f63280612cea014d123921926e2aac76e35e4a76a1cff4` |
| D.3 task | `origin/coord/coordinator:tasks/compute/20261127-12-d3-htcondor-preflight.md` | `2e4f3222f3ffd54bb767f8a890fa0924a8b7a1232111ccf9bda092481333407a` |
| Ada task | `origin/coord/coordinator:tasks/compute/20261127-13-ada-probe-prep.md` | `4a901b664c6907de5e2c025df68d1d40d55532377b6cf3c502f206e24fb01252` |
| PLAN row | `docs/r1/PLAN.md` @ `origin/main`, `R1-P4-D3-GPU-PREFLIGHT` | `f429bce0b5bed5f8450dcfda278001d4842c5f0f15226b70385376f31a9d69d5` |

## Verification method (read-only)

- Recreated `origin/main` in a scratch worktree at the commit under review; read the two records and every
  capture with `git show`, `cat`, `grep` and `awk`.
- Ran `git diff --stat` and `git diff --name-status origin/main...origin/compute-preflight-blockers-20261127`,
  and `git log --oneline origin/main..origin/compute-preflight-blockers-20261127`; confirmed a single commit and
  22 added files, all under `docs/r1/reports/`.
- Recomputed every sha256 in both report manifests and in `captures/SHA256SUMS` with `shasum -a 256 -c`; also
  recomputed the three input hashes against the same files on `origin/main`.
- Reconciled the submit files, the slot ad, the startd `START` capture, the `condor_q` captures and the
  `-better-analyze`/`-reverse` output against each sentence of the D.3 record, including job ids, request values,
  state, GPU model, free-GPU counts and removal.
- Read `p4_direct.py` (`RUNTIMES`, `load_descriptor`, `run_container`) and `p4_fill_host_config.py`
  (`ADA_CHOICE`, the `ada_rtx6000` rules) on `origin/main` to test the Ada blocker independently.
- Checked the cited venv commits `a1d0cf74` and review `a2efbb40`, the freeze line count, the Python versions and
  the 0.53 s smoke claim against the committed venv record.
- Confirmed the branch adds no file outside `docs/r1/reports/`; `preflight.sh` is report-local text committed as
  an executable payload, not a change to `r1/scripts`, a config, data, label, evaluation or sealed path.

## Findings

### MAJOR 1 — the A100 job carried an L40S-only payload

`preflight_a100.jdl` uses `executable = preflight.sh`, and that script hard-codes the L40S checks:

```
[ "$gpu_name" = "NVIDIA L40S" ] || { echo "STOP: GPU is $gpu_name, not NVIDIA L40S"; exit 2; }
[ "$gpu_cap" = "8.9" ] || { echo "STOP: compute capability $gpu_cap != 8.9"; exit 2; }
...
assert out["device_name"] == "NVIDIA L40S" and out["capability"] == [8, 9]
```

An `A100-PCIE-40GB` has compute capability 8.0, so if `760149` had matched, the in-job payload would have
exited 2 at the identity step and would never have read the inputs or run the torch check. The record presents
the TOpAS attempt as the task's allowed alternative and does not disclose that its payload could only validate an
L40S. The capacity conclusion is unaffected (no A100 was runnable), but the A100 leg as committed is not a valid
A100 preflight.

**Required:** parameterise the payload for the target card (`NVIDIA A100-PCIE-40GB`, capability 8.0, matching
torch assert), or add a separate A100 script, and state in the record that the job as submitted was a scheduler
probe only. Do not re-use the L40S assertions for an A100 retry.

### MAJOR 2 — `760149` has no capture of its queue state or non-match

The only direct evidence for cluster `760149` is its submit line and its removal line
(`captures/preflight_a100.submit`, `captures/condor_rm_a100.txt`). `captures/condor_q_all.txt` is time-stamped
`11/27/26 04:08:46` and lists only `760148`; the record says the A100 job was submitted at 04:10. There is no
`condor_q 760149`, no `-better-analyze 760149`, no job log and no `preflight.out`. Consequently the row's
"Idle, no match" and the sentence "No container was started" are inferred from the slot table, not captured for
that job. The inference is very likely right — no A100 slot was runnable in the same capture — but the evidence
bundle does not prove the job's state, and the slot captures are undated.

**Required:** add a `condor_q -better-analyze 760149` (or a `condor_q` of the cluster) capture taken before
removal, or reword the table and the "no container was started" sentence to say what is actually captured: no
runnable A100 slot at the captured time, and the idle cluster removed without a committed job log.

### MINOR 3 — the nested capture manifest does not verify

`captures/SHA256SUMS` contains a line for itself, `da51c1aa4bd6c41c46f265aa331b307ab601782e860ca6e9e55174785f4958ca  captures/SHA256SUMS`,
but the file's actual sha256 is `a2a489271e9ab7a48cadd447d205648c55f9921747b273da7247f963e0bd30cc`. Running
`shasum -a 256 -c captures/SHA256SUMS` from the report directory reports
`captures/SHA256SUMS: FAILED` (one computed checksum did not match); every other entry passes, and the parent
`SHA256SUMS` has the correct `a2a489…` for the manifest. The self-entry records an earlier version of the file
and cannot be correct as written (a file cannot contain its own hash).

**Required:** remove the self-entry, or document that the manifest excludes itself and regenerate the line from
the final bytes. Leave the parent manifest's correct hash in place.

### MINOR 4 — the transferred hash manifest is not committed

Both `.jdl` files transfer `PREFLIGHT_INPUTS.sha256`, and the record reports three input hashes, but that
manifest is not in the branch. The three reported hashes do match the current files on `origin/main`
(`trackp_ada_v1.json`, `p4_probe_spec.json`, `D3_PREDECL_R4_20261127.md`), so the numbers are supported; the
submit-side artefact itself is not preserved.

**Required:** commit `PREFLIGHT_INPUTS.sha256` as a capture, or state in the record that the submit-side manifest
was not retained and that the table was recomputed against the named main files.

### MINOR 5 — undated slot captures and the effective memory value

`l40s_slot_ad.txt` and `topas_gpu_slots_start.txt` carry no capture timestamp, so the reader cannot tie the slot
state to the 04:07/04:10 submissions. Separately, the record gives `request_memory = 131,072` (the `.jdl` value)
while `condor_q_better_analyze` reports `RequestMemory = 131100`, presumably the scheduler's effective rounding;
the record should say which value it is quoting.

**Required:** add the capture time (or a dated `condor_status` wrapper) and one sentence on the 131,072 vs
131,100 difference, or quote the effective value.

## Scope and framing checks

1. **Diff scope — PASS.** The branch is one commit on `origin/main` adding 22 files, all under
   `docs/r1/reports/`; no code, config, data, label, evaluation, sealed file or note is modified. The executable
   `preflight.sh` is a report-local submitted payload, not an import or a change to `r1/scripts`.
2. **D.3 scheduler claims — PASS for `760148`, PARTIAL for `760149`.** The L40S ad shows
   `State = Unclaimed`, `Activity = Idle`, `GPUs = 1`, `GPUs_DeviceName = "NVIDIA L40S"`,
   `GPUs_GlobalMemoryMb = 45468`, driver `570.211.01`, capability `8.9`, `Start = false`; the reverse analysis
   reduces to `never Start`; the analyze shows 21 slots rejected by job requirements and 1 by its own, 0 willing
   to run. `startd_START.txt` is `False`. The A100 slot table shows `167`/`179` with 0 free GPUs and `175` with 5
   free but `Start = false`; the `760149` state itself is not captured (MAJOR 2).
3. **No request edit and no container/input read — PASS as stated, with the wording caveat above.** Both submit
   files have the same shape apart from the device name (1 GPU, 8 CPUs, 131,072 MB, 150,000,000 KB, walltime
   3600, pinned v2.2 digest `49dd9900…`); no capture shows an edit or a start, and the three input hashes match
   `origin/main`. The foreign `lucid` jobs `760142/760143/760145/760147` remain running in `condor_q_run.txt`,
   and only clusters `760148`/`760149` were removed.
4. **Ada claims — PASS.** `host_check.txt` records `zli538` uid 1008, driver `545.23.08`, two empty RTX 6000 Ada
   cards at 48,427 MiB free, `APPTAINER=absent`, `SINGULARITY=absent`, `PODMAN=absent`,
   `DOCKER=/usr/bin/docker version 28.3.3`, `DOCKER_INFO=permission denied … /var/run/docker.sock`, and
   `/data1` 2.1 TB free. `p4_direct.py` has `RUNTIMES = ("apptainer", "docker")` and refuses anything else;
   `p4_fill_host_config.py` has `ADA_CHOICE = {"direct.container_runtime": ("apptainer", "docker")}` and no venv
   runtime mode. The record claims no fill, no probe, no GPU job and no training, names no false runtime, and
   correctly calls the choice a Level 2 host/engineering decision rather than a compute code change.
5. **Severity framing — PASS.** The D.3 record says the result is a capacity finding, not a STOP of evidence and
   not the D.3 per-arm smoke; the Ada record says the probe and fill are blocked and the venv unit is unaffected.
   Neither overstates the blocker as an outcome.

## What is supported and what is not

Supported: the L40S non-match, the A100 capacity picture, the absence of a usable runtime under `zli538`, the
launcher's two-runtime restriction, the three input hashes, the untouched `lucid` jobs, and the venv record cited
by the Ada note (`a1d0cf74`, review `a2efbb40`; 121/121 freeze, Python 3.12.10 vs 3.12.15, torch 2.6.0+cu124,
0.53 s smoke).

Not supported as committed: that `760149` was Idle and never started (no capture), that the A100 leg could have
validated an A100 (the payload is L40S-only), and that the nested capture manifest verifies (self-entry is
stale). These are paperwork/payload defects, not a contradiction of the capacity or runtime conclusions; they
are all fixable without a new slot or a host decision.

**Decided for this review:** to require changes rather than accept, because one of the two preflight legs could
not have tested its target and one job's central state claim is uncaptured; no claim in either record about the
absence of evidence runs was found false.
