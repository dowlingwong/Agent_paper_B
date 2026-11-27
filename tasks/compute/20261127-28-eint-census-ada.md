# compute/20261127-28 — Paper C E-INT development census on Ada (R1-PAPERC-EINT-CENSUS)

Owner: compute. PLAN **R1-PAPERC-EINT-CENSUS** (`main` `d669b0bf`). Run instructions `paperC/docs/PAPERC_EINT_CENSUS_DRAFT_20261127.md` (sha256
`cc01c370…`) with `paperC/src/paperc/eint_batches.py` and `eint_census.py`. **After `compute/20261127-27` (D.3 smoke) has its card**, on a
second **empty** Ada RTX 6000 card under `zli538` (cards 0 and 2 were empty at the last sample; another user's cards are not touched). Use the
reviewed P.4 venv only if it carries the packages the census needs (torch, pyarrow and the tokenizer); otherwise build a separate venv from
the census instructions and record its freeze. Do not change the P.4 venv.

1. The smoke: baseline repeatability, the allocator cap and the process-memory sensor, identical validation targets, receipt completeness.
   A smoke failure is a STOP: report it.
2. Then the census: `baseline / A / B / A+B` on matched seeds, a fixed allocator cap and fixed effective training tokens, exactly as the
   instructions say. Record per cell: feasibility (OOM or not, with the cause), peak allocated and reserved memory, tokens contributing to
   loss, wall time, tokens/s, GPU-seconds, exit status, and held-out quality.
3. **Paper B first:** if P.4 SFT or D.3 needs the card, stop at the next safe point and report. An attempt lost to that is infrastructure.
Commit the receipts on a branch and get a fresh review. Report whether A changes B's feasibility or gain, so that the next stage can be decided.
