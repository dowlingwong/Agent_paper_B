# Independent re-review — D.3 HTCondor preflight and Ada P.4 runtime blocker (round 2, 27 November 2026)

Verdict: CHANGES REQUIRED

**Reviewer.** I am the independent, AI-assisted reviewer of round 1. This round I read only the changes in
`c2a5e425` on top of the previously reviewed `c4918964`, re-ran the manifest and hash checks on the changed
artifacts, and compared the revised record against its new captures. I opened no credential, secret, label,
evaluation or sealed file, made no SSH connection and changed nothing except writing this review file. The
reviewed branch was not modified.

**Summary.** The two MAJOR findings of round 1 are fixed in substance. The A100 leg now receives its own expected
GPU name and capability, and the `760149` gap is replaced by an explicit superseded-attempt row plus job `760152`
with queue, analysis and removal captures. The nested capture manifest now verifies over all 19 captures and
excludes itself, and `PREFLIGHT_INPUTS.sha256` is committed with the three hashes matching `origin/main`. Three
defects remain: the report-level `SHA256SUMS` was not regenerated and no longer verifies, the record's A100
slot sentence contradicts its own dated slot capture, and the dating/memory wording introduced in this round is
arithmetically or temporally wrong. These do not change the capacity conclusion, but the evidence bundle still
does not verify end to end.

## Inputs reviewed

| Input | Ref | sha256 |
|---|---|---|
| Reviewed tip | `origin/compute-preflight-blockers-20261127` @ `c2a5e42528f4916c2702c46bda34b9a6af810a36` | — |
| Round-1 tip | `c491896472ba6b17052c3f91ec384a49d991902a` | — |
| Base | `origin/main` @ `e153df24ee3435bbe0b2fa994297b15250550c30` | — |
| D.3 record (revised) | `docs/r1/reports/d3_preflight_20261127/D3_HTCONDOR_PREFLIGHT_20261127.md` | `041fadbeac45e1fe4722d3214bc7b2229db624b49c605b413396e2e261dc3592` |
| Report manifest (unchanged) | `…/d3_preflight_20261127/SHA256SUMS` | `ef0f8970ef7f87bd85ecc493a36d54240f4d1a64fd1ebf42e8ef42a92fae7c28` |
| Capture manifest (regenerated) | `…/d3_preflight_20261127/captures/SHA256SUMS` | `15e31167bfec094fb7b96fa6e0f9edfa1ac2ef605ef953fd93f152ea4415944d` |
| Payload (parameterised) | `…/d3_preflight_20261127/preflight.sh` | `d1dae0a7f0883cc7996f404cd76dd24be025e0a181953219d397e05c4873c45f` |
| L40S JDL | `…/d3_preflight_20261127/preflight_l40s.jdl` | `e3160564503d87cef07975c30ca7e61ec22050f5956170c862ee5789bbdd105d` |
| A100 JDL | `…/d3_preflight_20261127/preflight_a100.jdl` | `7ff4a18d2394a781f5f8aae71af56349df485920cde0a6fb00768eba6b597a4b` |
| Input manifest (new) | `…/d3_preflight_20261127/PREFLIGHT_INPUTS.sha256` | `6181e9bfa75f7e21b42dabfda4b7ea226e9200069bac8684968a5bf931f6a6c3` |
| `760152` queue capture | `…/captures/condor_q_a100_fix.txt` | `2197b7155c86308758ead44972848969e6bfcfb23418ba2979fed67502d67e99` |
| `760152` analysis | `…/captures/condor_q_better_analyze_a100_fix.txt` | `eb34fae9d1e66a82f1f30cb81e2e0461064cdc70ea39c0d742c39aa23860f07d` |
| A100 slot refresh | `…/captures/topas_a100_slots_fix.txt` | `9704178e8e268ea0c069c129cca7d166782d7f3a78a96e9688bc39caec94808d` |
| ETP slot refresh | `…/captures/etp_gpu_slots_fix.txt` | `da1f38428b65be32360f353c351b400911ffac8c612d30a046548d20682c5815` |
| `760152` removal | `…/captures/condor_rm_a100_fix.txt` | `4ad90377d47d9a5f71d99bcb2f33790f6b6b339a3102768ad4eabf5bd5643263` |
| `760152` submit | `…/captures/preflight_a100_fix.submit` | `68bf4bb6e4c2d525f486dc1c398c10147e9dfd9477d5842f4ef45fd50a2958c0` |
| Ada record (unchanged) | `docs/r1/reports/ada_p4_20261127/ADA_P4_PROBE_BLOCKER_20261127.md` | `3bff106bfb393fc65b980998d90d7db08980bd07a6e8cc85413e3f72bdfd468f` |
| Direct launcher (unchanged) | `r1/scripts/htcondor/trackp_p4/p4_direct.py` @ `origin/main` | `29ee656b0897aaa8cab351969e61736d661953da2b97b3aca515e06fa38be087` |
| Host-config filler (unchanged) | `r1/scripts/htcondor/trackp_p4/p4_fill_host_config.py` @ `origin/main` | `f65d8f7671a7e0bf69f63280612cea014d123921926e2aac76e35e4a76a1cff4` |

## Verification method (read-only)

- `git diff --stat c4918964..c2a5e425` and `--name-status`: 12 changed paths, all under
  `docs/r1/reports/d3_preflight_20261127/`; no code, config, data, label, evaluation or sealed path is touched and
  the Ada files are unchanged.
- Read the full `preflight.sh` diff and traced the argv plumbing: `arguments = $(ClusterId).$(ProcId) <NAME> <CAP>`
  reaches `$1/$2/$3`, the underscores become the first space only (both names have exactly one underscore), and
  the `nvidia-smi` and torch asserts use the exported values.
- Read the revised record and compared every new sentence with `condor_q_a100_fix.txt`,
  `condor_q_better_analyze_a100_fix.txt`, `topas_a100_slots_fix.txt`, `etp_gpu_slots_fix.txt`,
  `condor_rm_a100_fix.txt` and `preflight_a100_fix.submit`.
- Ran `shasum -a 256 -c SHA256SUMS` inside `captures/` (19/19 OK, exit 0) and from the report directory, and
  `shasum -a 256 -c SHA256SUMS` on the report-level manifest (exit 1).
- Recomputed the three `PREFLIGHT_INPUTS.sha256` hashes against
  `r1/scripts/configs/trackp_ada_v1.json`, `r1/scripts/htcondor/trackp_p4/p4_probe_spec.json` and
  `docs/r1/reports/d3_predecl_r4_20261127/D3_PREDECL_R4_20261127.md` on `origin/main`.
- Checked cluster ids against commit times: `c2a5e425` is `2026-11-27 04:20:25 +0100` (`03:20:25Z`), 16 s after
  the `03:20:09Z` capture, which fixes the timezone of the earlier `condor_q` display.

## Round-1 findings: disposition

| Round-1 finding | Status | Evidence |
|---|---|---|
| MAJOR: A100 job carried an L40S-only payload | **FIXED** | `preflight.sh` reads `$2`/`$3` (defaults L40S/8.9); `preflight_l40s.jdl` passes `NVIDIA_L40S 8.9`, `preflight_a100.jdl` passes `NVIDIA_A100-PCIE-40GB 8.0`. If `760152` had matched, the name check would compare `NVIDIA A100-PCIE-40GB` and the capability check `8.0`, which match `nvidia-smi` and `torch.cuda.get_device_capability` for an A100-PCIE-40GB. The leg is now a valid A100 preflight payload. |
| MAJOR: `760149` state uncaptured | **FIXED** | The record labels `760149` a superseded attempt with no queue capture and adds `760152`. `condor_q_a100_fix.txt` shows `JobStatus = 1`, no `RemoteHost`/`AssignedGPUs`, `RequestMemory = 131100`; `condor_q_better_analyze_a100_fix.txt` shows 0/23 matching and 0 willing; `condor_rm_a100_fix.txt` shows the removal. This supports "Idle, no match, removed" for `760152`. |
| MINOR: nested manifest self-entry stale | **FIXED** | The regenerated `captures/SHA256SUMS` has no self-entry, lists all 19 captures, and `shasum -c` passes from inside `captures/` (exit 0). |
| MINOR: `PREFLIGHT_INPUTS.sha256` missing | **FIXED** | Committed; its three hashes equal the three `origin/main` files and the record's table. |
| MINOR: dates and memory wording | **PARTIAL** | The effective `131,100 MB` is now stated, but the explanation and the timestamps are wrong (findings 2 and 3 below). |

## Remaining findings

### MAJOR 1 — the report-level `SHA256SUMS` was not regenerated and no longer verifies

The revised commit regenerated `captures/SHA256SUMS` but left `docs/r1/reports/d3_preflight_20261127/SHA256SUMS`
at its round-1 content. Running `shasum -a 256 -c SHA256SUMS` from the report directory exits 1:

```
captures/SHA256SUMS: FAILED
preflight.sh: FAILED
preflight_l40s.jdl: FAILED
preflight_a100.jdl: FAILED
shasum: WARNING: 4 computed checksums did NOT match
```

The old manifest also omits the six new captures (`condor_q_a100_fix.txt`,
`condor_q_better_analyze_a100_fix.txt`, `condor_rm_a100_fix.txt`, `etp_gpu_slots_fix.txt`,
`preflight_a100_fix.submit`, `topas_a100_slots_fix.txt`) and `PREFLIGHT_INPUTS.sha256`. The nested manifest is
correct; the parent is stale. This is the same class of bundle defect as round 1 and is a regression introduced
by fixing only the nested file.

**Required:** regenerate the report-level manifest from the current tree (all captures, `PREFLIGHT_INPUTS.sha256`,
`preflight.sh` and both JDLs; exclude the manifest itself), then confirm `shasum -a 256 -c SHA256SUMS` exits 0 from
the report directory.

### MINOR 2 — the A100 slot sentence contradicts its own dated capture

The record says (lines 34–36): "`167` and `179` advertise A100-PCIE-40GB but have `GPUs = 0` free; `175` has 5
free GPUs but `Start = false`/`Requirements = false`. Captured at 2026-11-27T03:20:09Z in
`captures/topas_a100_slots_fix.txt`." That capture shows:

```
slot1@c03-001-167 ... Unclaimed 8 1 NVIDIA A100-PCIE-40GB undefined error
slot1@c03-001-179 ... Unclaimed 8 0 NVIDIA A100-PCIE-40GB undefined error
slot1@c03-001-175 ... Unclaimed 8 5 NVIDIA A100-PCIE-40GB false false
```

`167` has **1** free GPU in the cited capture, not 0. It is still not runnable, but for a different stated
reason: its `Start`/`Requirements` are `undefined`/`error`. The same capture and the analyze also disagree at the
aggregate level — the analyze reports 0/23 slots matching even the device-name condition, i.e. no A100 ad at all
in that view, while the slot capture shows three A100 parents. The record does not reconcile the two views. The
"Idle, no match" conclusion is still supported by the job ad, the 0/23 analysis and the removal, but the stated
slot-level reason is wrong.

**Required:** correct the sentence to the captured state (167: 1 free, Start/Requirements undefined/error; 179: 0
free; 175: 5 free, Start false), and either explain why the 23-slot analyze sees no A100 or stop using it as the
slot-level explanation.

### MINOR 3 — timestamps are local time labelled UTC, and the job counts are stale

The record still says "Submitted from: deepthought, `dwong`, 27 Nov 2026 04:07–04:10 UTC" (line 10). The new job
is dated `2026-11-27T03:20:09Z`, which is earlier than that range despite the higher cluster id. The commit time
resolves the contradiction: `c2a5e425` is `04:20:25 +0100` = `03:20:25Z`, 16 s after the `03:20:09Z` capture. The
`condor_q` display (`11/27 04:07`, `04:08:46`) is schedd local CET (UTC+1), so `760148` is `03:07Z` and the three
jobs span about `03:07–03:20Z`, not `04:07–04:10Z`. The summary and decisions are also stale for three jobs: "Two
ENGINEERING_ONLY jobs" (line 3), "neither could run" (line 4), and "remove both idle jobs" (line 68) still assume
two attempts.

**Required:** state the timezone and the full range for all three jobs (e.g. `03:07–03:20 UTC / 04:07–04:20 CET`),
and update "two"/"neither"/"both" to the actual three clusters, noting `760149` is superseded.

### MINOR 4 — the effective-memory explanation is arithmetically wrong

The record says `131,072 MB` requested and "the slot analyzer reports the effective 131,100 MB after the 128 MB
quantum". `131,072` is already exactly `1024 × 128`, so a 128 MB quantum cannot turn it into `131,100`.
`131,100` is not a multiple of 128 (it is `1024.21875 × 128`); the observed value is consistent with a 100 MB
rounding, not a 128 MB one. The effective number is right; the explanation is not.

**Required:** either give the correct rounding rule or simply say the analyzer reports `131,100 MB` without the
quantum claim.

### MINOR 5 — the nested manifest's path convention changed

The regenerated `captures/SHA256SUMS` uses bare filenames (`condor_q_all.txt`), whereas the round-1 file and the
report-level manifest use report-relative paths (`captures/condor_q_all.txt`). `shasum -a 256 -c
captures/SHA256SUMS` from the report directory therefore fails with "No such file or directory"; it passes only
from inside `captures/`. This is a documentation/usability defect, not a hash error.

**Required:** restore the `captures/` prefixes (as the report-level manifest uses) or state in the record that the
nested manifest is checked from inside the capture directory.

### Note — `760152`'s payload is inferred, not captured

`condor_q_a100_fix.txt` records the state, memory and resources but not `Arguments`/`Cmd`, so the ad does not
show that `760152` itself carried `NVIDIA_A100-PCIE-40GB 8.0`. The corrected payload is verified statically in the
committed JDL/script and is consistent with the commit 16 s after the capture, but a future job-ad capture should
include `Arguments`/`Cmd` if the payload version matters. No change is required for this round.

## Scope, Ada and framing checks

1. **Diff scope — PASS.** Only 12 D.3 report paths changed; the Ada record, `p4_direct.py`,
   `p4_fill_host_config.py` and all repository code/config are untouched.
2. **A100 payload validity — PASS statically.** The script would compare the A100 name and capability `8.0`; both
   match the card the JDL targets. The `760152` job never matched, so this remains a static check, not an in-job
   observation.
3. **`760152` Idle/no-match/removal — PASS.** The queue capture, the 0/23 analysis and the removal capture support
   the row. The slot-level reason is corrected in finding 2.
4. **Ada blocker — PASS (unchanged).** The round-1 conclusion still holds: `host_check.txt` shows
   apptainer/singularity/podman absent, Docker socket permission-denied under `zli538`, and the reviewed launcher
   admits only `apptainer`/`docker`; the record claims no fill/probe/training and frames the choice as a Level 2
   host/engineering decision. Nothing in this commit weakens or alters that.
5. **Framing — PASS.** The revised record still calls the result a capacity finding, not a STOP of evidence and not
   the D.3 per-arm smoke; the Ada note still does not claim a fill or probe.

**Decided for this re-review:** to require changes again, because the report-level manifest does not verify, the
record's A100 slot sentence contradicts its cited capture, and the rewritten date/memory wording is wrong. None of
these overturns the capacity or runtime conclusions, and all are confined to documentation and manifests.
