# Independent re-review — D.3 HTCondor preflight (round 4, 27 November 2026)

Verdict: CHANGES REQUIRED

**Reviewer.** I am the independent, AI-assisted reviewer of rounds 1–3. This round I re-checked only the
round-3 finding (`167` free-GPU wording) against the cited capture and re-ran both manifest checks. I opened no
credential, secret, label, evaluation or sealed file, made no SSH connection and changed nothing except writing
this review file. The reviewed branch was not modified.

**Summary.** The evidence bullet is now correct: it says `167` shows 1 free parent A100 GPU but is unusable
because `Start`/`Requirements` are `undefined`/`error`, `179` has 0 free, and `175` has 5 free but `Start=false`,
so none is runnable. Both manifests verify from the report directory: the report-level `SHA256SUMS` covers 24
files (including the new record hash) and the nested `captures/SHA256SUMS` covers all 19 captures with no
self-entry. One stale sentence remains in the record's top-line summary: it still says "the only TOpAS A100 parent
with free GPUs is also `Start = false`; the other A100 parents have no free GPU", which the revised bullet itself
contradicts (`167` has 1 free). This is a one-sentence correction plus a manifest regeneration.

## Inputs reviewed

| Input | Ref | sha256 |
|---|---|---|
| Reviewed tip | `origin/compute-preflight-blockers-20261127` @ `0a345bccc12c366097146463481f841c19ebd849` | — |
| Round-3 tip | `8b97a4a1d3a96ff5b79807dd9d4e576f00a50b9a` | — |
| D.3 record | `docs/r1/reports/d3_preflight_20261127/D3_HTCONDOR_PREFLIGHT_20261127.md` | `e849afbe6cc107ec0b427aa4abdf7491df67411f7cb288c2879d76e679d69a5b` |
| Report manifest | `…/d3_preflight_20261127/SHA256SUMS` | `1d8381917d7005ccf1e4f10d105b556e80d0895a9c4dcf7c6f5fc0ecdf3fdc3f` |
| Capture manifest | `…/d3_preflight_20261127/captures/SHA256SUMS` | `7dc676b36b742f07a3e3f436529f3f4d624bd39e0a5424386df317640484a80c` |
| A100 slot capture | `…/captures/topas_a100_slots_fix.txt` | `9704178e8e268ea0c069c129cca7d166782d7f3a78a96e9688bc39caec94808d` |

## Verification method (read-only)

- `git diff --stat 8b97a4a1..0a345bcc`: two changed paths (the record and the report-level manifest), both under
  `docs/r1/reports/d3_preflight_20261127/`; the nested manifest and all captures are unchanged.
- Read the revised A100 bullet and compared it line by line with `topas_a100_slots_fix.txt`.
- Ran `shasum -a 256 -c SHA256SUMS` and `shasum -a 256 -c captures/SHA256SUMS` from the report directory;
  checked the OK counts and the absence of a self-entry.
- Grepped the whole record for `free GPU`, `no unclaimed`, and `167` to find any other stale phrasing.

## Checks

1. **A100 bullet versus capture — PASS.** The capture has
   `slot1@c03-001-167 ... Unclaimed 8 1 ... undefined error`,
   `slot1@c03-001-179 ... Unclaimed 8 0 ... undefined error`, and
   `slot1@c03-001-175 ... Unclaimed 8 5 ... false false`. The record now says exactly that: `167` 1 free but
   `Start`/`Requirements` `undefined`/`error`; `179` 0 free; `175` 5 free but `Start=false`; none runnable. The
   child allocations in the capture (2+1+2+1+1 = 7) plus the parent's 1 are consistent with the node's 8 GPUs.
2. **Report manifest — PASS.** `shasum -a 256 -c SHA256SUMS` exits 0 with 24/24 OK, including the new record
   hash `e849afbe…`, all 19 captures, `PREFLIGHT_INPUTS.sha256`, `preflight.sh` and both JDLs; no self-entry.
3. **Nested manifest — PASS.** `shasum -a 256 -c captures/SHA256SUMS` exits 0 with 19/19 OK; no
   `captures/SHA256SUMS` line.
4. **Top-line summary — FAIL.** Line 5 still reads: "the only TOpAS A100 parent with free GPUs is also
   `Start = false`; the other A100 parents have no free GPU." `167` has 1 free parent GPU, so neither "only …
   with free GPUs" nor "the other A100 parents have no free GPU" matches the cited capture, and the sentence
   contradicts the corrected bullet two paragraphs later.

## Required change

Rewrite the summary clause to match the bullet, for example: "the only A100 parent with a usable free allocation
(`175`) is `Start = false`; `167` has one free GPU but `Start`/`Requirements` `undefined`/`error`, and `179` has
none free." Then regenerate the report-level `SHA256SUMS` (the record hash changes) and re-run `shasum -c` from the
report directory. The nested manifest is unaffected.

**Decided for this re-review:** to require the summary correction, not because the capacity conclusion is wrong —
it is right, and the evidence bullet now states it accurately — but because the record's own top-line sentence
still contradicts its capture and its evidence section. Everything else in rounds 1–3 remains fixed, and the Ada
record remains accepted and unchanged.
