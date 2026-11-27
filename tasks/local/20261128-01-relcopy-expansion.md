# local/20261128-01 — expansion variant of the D6 copy step (`g5_relcopy.py`)

Compute (`compute/20261127-36`) reports that `g5_relcopy.py` supports only the `seven`/`ar` sets, and the expansion assembly (`g1b-x-tasl-20261126-a`,
result on `main` `f43823da`) is outside `sealed_g1b`. Add an expansion variant: copy the expansion run's summary, `ASSEMBLY.json` and `runs.jsonl` out of
its sealed tree with `COPY_RECORD.json`, same rules as the seven-node copy (read-only source, nothing overwritten, no audit seed 7001–7010, sha256 of
each copy), bound to the expansion run id and the PRE-SPLIT v2 amendment (`970d3e45…`). Targeted tests, full suite base vs tip, tier-E review. Report
the tip and the exact command compute runs on TASL-2. Priority: before any other local card except `local/20261127-31` (screening deepthought2).
