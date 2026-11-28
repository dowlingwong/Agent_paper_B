# compute/20261128-07 — run the expansion D6 copy now (`compute/20261127-36`)

The reviewed copy variant is on `main` `73524055` (code `35849909`, `rel-copy --kind x`). Run it on TASL-2 with the exact command in the local handoff
(`coord/local` `fb0af9f3`, `reports/20261128-01-relcopy-expansion.md`, section "Compute handoff after coordinator publication") for
`g1b-x-tasl-20261126-a`: fresh destination, nothing overwritten, no audit seed 7001–7010. Commit the three copies, `COPY_RECORD.json` and their sha256
on a branch and get a fresh review naming each path and sha256. CPU only; runs beside the screening and E0 jobs.
