# Independent re-review — D.3 HTCondor preflight (round 5, 27 November 2026)

Verdict: ACCEPTED

**Reviewer.** I am the independent, AI-assisted reviewer of rounds 1–4. This round I re-checked only the
round-4 finding: whether the record's top-line summary now agrees with its A100 evidence bullet and with
`captures/topas_a100_slots_fix.txt`, and whether both manifests still verify from the report directory. I opened
no credential, secret, label, evaluation or sealed file, made no SSH connection and changed nothing except writing
this review file. The reviewed branch was not modified.

**Summary.** The summary is now correct and internally consistent. It says the parent with the most free A100 GPUs
(`175`, five) is `Start = false`, `167` has one free but `Start`/`Requirements` are `undefined`/`error`, and `179`
has none free. That matches the evidence bullet and the capture exactly. Both `shasum -c` checks pass from the
report directory: the report-level manifest covers 24 files (including the new record hash) and the nested capture
manifest covers 19 captures with no self-entry. No round-1–4 finding remains open, and the records' capacity,
scope and Ada framing are unchanged and still correct.

## Inputs reviewed

| Input | Ref | sha256 |
|---|---|---|
| Reviewed tip | `origin/compute-preflight-blockers-20261127` @ `28352976e3218ad864a8892ed1689c1ceb1c24ed` | — |
| Round-4 tip | `0a345bccc12c366097146463481f841c19ebd849` | — |
| D.3 record | `docs/r1/reports/d3_preflight_20261127/D3_HTCONDOR_PREFLIGHT_20261127.md` | `43e8fb334266f1d58fd670f3a2b6b345a3751d074952b87cfc85035ed4dceca3` |
| Report manifest | `…/d3_preflight_20261127/SHA256SUMS` | `6ae0790695209548a353451eca06b16cfba8844a78f2164cd51b402ae4389d78` |
| Capture manifest (unchanged) | `…/d3_preflight_20261127/captures/SHA256SUMS` | `7dc676b36b742f07a3e3f436529f3f4d624bd39e0a5424386df317640484a80c` |
| A100 slot capture | `…/captures/topas_a100_slots_fix.txt` | `9704178e8e268ea0c069c129cca7d166782d7f3a78a96e9688bc39caec94808d` |
| Ada record (unchanged) | `docs/r1/reports/ada_p4_20261127/ADA_P4_PROBE_BLOCKER_20261127.md` | `3bff106bfb393fc65b980998d90d7db08980bd07a6e8cc85413e3f72bdfd468f` |

## Verification method (read-only)

- `git diff --stat 0a345bcc..28352976` and `--name-status`: two changed paths (the record and the report-level
  manifest), both under `docs/r1/reports/d3_preflight_20261127/`; no capture, code, config, data, label,
  evaluation or sealed path changed.
- Read the revised summary and the A100 bullet and compared both with the parent/child lines in
  `topas_a100_slots_fix.txt`.
- Ran `shasum -a 256 -c SHA256SUMS` and `shasum -a 256 -c captures/SHA256SUMS` from the report directory; counted
  OK lines and checked for a self-entry.
- Recomputed the record's sha256 and compared it with the line in the report manifest.
- Grepped the record for any remaining "no free", "no unclaimed", "only TOpAS", "other A100" or "0 free" phrasing.

## Checks

1. **Summary versus capture — PASS.** The capture has `slot1@c03-001-175` with `Gpus = 5` and
   `Start = false`/`Requirements = false`, `slot1@c03-001-167` with `Gpus = 1` and `Start`/`Requirements`
   `undefined`/`error`, and `slot1@c03-001-179` with `Gpus = 0` and `undefined`/`error`. The summary says exactly
   that: `175` (five free) is `Start = false`; `167` has one free but is unusable; `179` has none free. "The
   parent with the most free A100 GPUs" is correct (`175` 5 > `167` 1 > `179` 0).
2. **Summary versus bullet — PASS.** The bullet states `167` 1 free / `179` 0 free / `175` 5 free with the same
   `Start`/`Requirements` values and the same "none ... runnable" conclusion. The two paragraphs no longer
   contradict each other.
3. **Report manifest — PASS.** `shasum -a 256 -c SHA256SUMS` exits 0 with 24/24 OK, including the record hash
   `43e8fb33…`, all 19 captures, `PREFLIGHT_INPUTS.sha256`, `preflight.sh` and both JDLs; no self-entry.
4. **Nested manifest — PASS.** `shasum -a 256 -c captures/SHA256SUMS` exits 0 with 19/19 OK; no
   `captures/SHA256SUMS` line; unchanged from round 3 and still report-relative.
5. **No stale wording — PASS.** The grep finds no remaining "no free GPU", "no unclaimed parent GPU", "only
   TOpAS … free", "other A100 parents" or "0 free" claim. The only free-GPU statements are the corrected summary
   and bullet.

## Prior findings

All round-1–4 findings are closed:

- A100 identity payload parameterised and statically valid for `NVIDIA A100-PCIE-40GB` / `8.0` (round 1).
- `760149` labeled superseded; `760152` has queue, 0/23 analysis and removal captures (round 1).
- Nested manifest excludes itself and verifies; report manifest regenerated and verifies (rounds 1–2).
- `PREFLIGHT_INPUTS.sha256` committed with three hashes matching `origin/main` (round 1).
- Timestamps `03:07–03:20 UTC`, three-submission count and the 131,072 → 131,100 MB (28 MB above) wording correct
  (round 2).
- `167` free-GPU statement corrected in the evidence bullet (round 3) and now in the summary (round 4).

## Scope and framing

The branch remains documentation-only: this commit changes the record and the report manifest only. It still
describes a capacity finding, not a STOP of evidence and not the D.3 per-arm smoke, and it does not claim a
container start or an in-job input read. The Ada record is untouched and remains accepted: Apptainer/Singularity/
Podman absent, Docker socket permission-denied under `zli538`, the reviewed launcher limited to `apptainer`/`docker`,
no fill/probe/training claimed, and the decision correctly left at Level 2 host/engineering.

**Decided for this re-review:** to accept. The remaining finding is fixed, both manifests verify, the capacity
conclusion is supported by the captures, and no new inconsistency was introduced.
