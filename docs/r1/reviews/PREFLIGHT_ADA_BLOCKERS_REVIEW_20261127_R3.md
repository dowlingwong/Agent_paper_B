# Independent re-review — D.3 HTCondor preflight (round 3, 27 November 2026)

Verdict: CHANGES REQUIRED

**Reviewer.** I am the independent, AI-assisted reviewer of rounds 1 and 2. This round I re-checked only the
remaining round-2 findings against commits `14fad99b` and `8b97a4a1` on top of `c2a5e425`: the two checksum
manifests, the revised capacity/dating/memory wording, and the A100 slot sentence. I opened no credential, secret,
label, evaluation or sealed file, made no SSH connection and changed nothing except writing this review file. The
reviewed branch was not modified.

**Summary.** Four of the five round-2 findings are fixed cleanly. The report-level `SHA256SUMS` now verifies over
24 files and the nested `captures/SHA256SUMS` verifies over all 19 captures with no self-entry, both from the
report directory. The timestamp is now `03:07–03:20 UTC`, the submission count is three (two card targets, one
superseded A100 attempt), the memory text correctly says the job ad shows `131,100 MB` for a `131,072 MB` request
(28 MB above) without the false quantum claim, and the `-better-analyze` 23-slot view is now explained as the
submit pool rather than the TOpAS collector. One contradiction remains: the record still says `167` has no free
or unclaimed parent GPU, while its cited capture shows `slot1@c03-001-167` with `Gpus = 1`. The conclusion that
no A100 is runnable is still correct — `167` and `179` have `Start`/`Requirements` `undefined`/`error` and `175`
has `Start = false` — but the stated free-GPU reason is wrong for `167`.

## Inputs reviewed

| Input | Ref | sha256 |
|---|---|---|
| Reviewed tip | `origin/compute-preflight-blockers-20261127` @ `8b97a4a1d3a96ff5b79807dd9d4e576f00a50b9a` | — |
| Round-2 tip | `c2a5e42528f4916c2702c46bda34b9a6af810a36` | — |
| Base | `origin/main` @ `e153df24ee3435bbe0b2fa994297b15250550c30` | — |
| D.3 record (revised) | `docs/r1/reports/d3_preflight_20261127/D3_HTCONDOR_PREFLIGHT_20261127.md` | `a8afb2d6660bbf59d7c596f0b4d304dd61bfc25c0a53bf33f628e92754998be4` |
| Report manifest (regenerated) | `…/d3_preflight_20261127/SHA256SUMS` | `9bb1686922f1107c536b23f00762c063ed18a4bf3174c05b368256be626aef72` |
| Capture manifest (report-relative) | `…/d3_preflight_20261127/captures/SHA256SUMS` | `7dc676b36b742f07a3e3f436529f3f4d624bd39e0a5424386df317640484a80c` |
| A100 slot refresh | `…/captures/topas_a100_slots_fix.txt` | `9704178e8e268ea0c069c129cca7d166782d7f3a78a96e9688bc39caec94808d` |
| `760152` analysis | `…/captures/condor_q_better_analyze_a100_fix.txt` | `eb34fae9d1e66a82f1f30cb81e2e0461064cdc70ea39c0d742c39aa23860f07d` |
| `760152` queue capture | `…/captures/condor_q_a100_fix.txt` | `2197b7155c86308758ead44972848969e6bfcfb23418ba2979fed67502d67e99` |
| Ada record (unchanged) | `docs/r1/reports/ada_p4_20261127/ADA_P4_PROBE_BLOCKER_20261127.md` | `3bff106bfb393fc65b980998d90d7db08980bd07a6e8cc85413e3f72bdfd468f` |

## Verification method (read-only)

- `git diff --stat c2a5e425..8b97a4a1` and `--name-status`: three changed paths, all under
  `docs/r1/reports/d3_preflight_20261127/` (the record and the two manifests). No code, config, data, label,
  evaluation, sealed path or Ada file changed.
- Ran `shasum -a 256 -c SHA256SUMS` and `shasum -a 256 -c captures/SHA256SUMS` from the report directory and
  recorded exit codes and OK counts; checked that the nested manifest lists no `captures/SHA256SUMS` line.
- Read the revised record against `topas_a100_slots_fix.txt`, `condor_q_a100_fix.txt`,
  `condor_q_better_analyze_a100_fix.txt` and the earlier slot captures.
- Checked the arithmetic of the memory sentence and the cluster ids against the commit times and the `condor_q`
  local-time display.
- Re-read the round-2 findings and marked each one fixed or open.

## Round-2 findings: disposition

| Round-2 finding | Status | Evidence |
|---|---|---|
| MAJOR: report-level `SHA256SUMS` stale | **FIXED** | `shasum -a 256 -c SHA256SUMS` from the report directory exits 0 with 24/24 OK. It now lists all 19 captures, the record, `PREFLIGHT_INPUTS.sha256`, `preflight.sh` and both JDLs, and no self-entry. |
| MINOR: nested manifest bare paths | **FIXED** | `captures/SHA256SUMS` uses `captures/<name>`; `shasum -c captures/SHA256SUMS` from the report directory exits 0 with 19/19 OK; `grep -c "captures/SHA256SUMS"` returns 0 (no self-entry). |
| MINOR: dates/counts stale | **FIXED** | The record now says `03:07–03:20 UTC` and "Three ENGINEERING_ONLY submissions (two card targets; one A100 attempt was superseded)". No "two jobs", "neither" or "both idle jobs" remains; "both allowed cards" and "two JDLs" are correct. |
| MINOR: 128 MB quantum claim | **FIXED** | The record now says the job ad shows `131,100 MB`, "28 MB above the request". `131,100 − 131,072 = 28`; no quantum claim remains. |
| MINOR: `167` free-GPU contradiction | **OPEN** | See below. |

## Remaining finding

### MINOR — `167` still has a free parent GPU in the cited capture

The record's summary says (line 5) "the other A100 parents have no free GPU", and the evidence bullet says
(lines 40–41) "`167` and `179` have no unclaimed parent GPU (their child slots carry the assigned GPUs)". The
cited dated capture says otherwise:

```
slot1@c03-001-167.gridka.de Unclaimed 8 1 NVIDIA A100-PCIE-40GB undefined error
slot1@c03-001-175.gridka.de Unclaimed 8 5 NVIDIA A100-PCIE-40GB false false
slot1@c03-001-179.gridka.de Unclaimed 8 0 NVIDIA A100-PCIE-40GB undefined error
```

`167` is `Unclaimed` with `Gpus = 1`; the one remaining GPU is not carried by a child slot (the child allocations
sum to 7 of the node's 8). So "no free GPU" and "no unclaimed parent GPU" are both false for `167`. `179`
(0 free) and `175` (5 free, `Start = false`) are described correctly. The conclusion "none of the three is a
runnable A100 target" is still right, because `167`/`179` have `Start`/`Requirements` `undefined`/`error` and
`175` has `Start = false`; only the free-GPU reason is wrong.

**Required:** say `167` has 1 free parent GPU but is not runnable because `Start`/`Requirements` are
`undefined`/`error`; `179` has 0 free; `175` has 5 free but `Start = false`. Adjust the summary sentence from
"the other A100 parents have no free GPU" to the same effect. Because the report manifest now hashes the record,
regenerate `SHA256SUMS` after the edit and re-run `shasum -c` from the report directory.

## What is now verified

- **Manifests.** Both manifests verify from the report directory; the report manifest covers 24 files (19 captures,
  the record, `PREFLIGHT_INPUTS.sha256`, `preflight.sh`, two JDLs) and the nested manifest covers 19 captures with
  no self-entry.
- **Timing and counts.** Three submissions, two card targets, one superseded; `03:07–03:20 UTC` is consistent with
  the `condor_q` local display and the `03:20:09Z` capture.
- **Memory.** `131,100 MB` reported for `131,072 MB` requested, 28 MB above; arithmetic correct.
- **Pool explanation.** The `-better-analyze` 23-slot view is the submit pool; the TOpAS A100 evidence is the
  separate `condor_status -pool c03-001-140` capture. This matches the committed pool facts
  (`docs/r1/reports/htcondor_prep_20261114/POOL_FACTS.md`: the analyze view does not include the c03/TOpAS slots),
  and it resolves the round-2 0/23-versus-three-A100-parents inconsistency.
- **`760152`.** The queue capture supports `JobStatus = 1`, `RequestMemory = 131100`, no `RemoteHost`/`AssignedGPUs`;
  the analysis supports 0/23 matching; the removal capture supports the removed state.
- **Ada.** Unchanged and still accepted: apptainer/singularity/podman absent, Docker socket permission-denied under
  `zli538`, launcher limited to `apptainer`/`docker`; no fill, probe or training is claimed.

**Decided for this re-review:** to require changes for the single remaining `167` free-GPU sentence, not for the
capacity or runtime conclusions. Everything else in round 2 is fixed; this is a one-sentence correction plus a
manifest regeneration.
