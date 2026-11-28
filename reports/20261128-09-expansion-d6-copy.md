# compute/20261127-36 — expansion D6 copy delivered (review running)

**Result: the expansion `g1b-x-tasl-20261126-a` copy was produced and the three hashes match the sealed source
byte for byte (1,840 rows). Review in progress.**

- Task: `compute/20261127-36` with the reviewed handoff `local/20261128-01`; code `35849909` published on
  `origin/main` `73524055`.
- Deliverable branch: `compute-relcopy-x-20261128` @ `c70fed2c6fde7facdd8df5c6c4ac2bd781fa9dbc`.
- Run: TASL-2, fresh detached checkout `paperB_relcopy_x_20261128T004723Z` at `35849909`,
  `g5_tasl.py rel-copy … --kind x`; destination was free before the run.
- Copy:
  - `summary.json` sha256 `67355b668aad1d930814b51e91ccd76620bdad349516d7d630a467d884feaa10`
  - `ASSEMBLY.json` sha256 `b4c90ec6a622dcd4c762ff0504751f85dde45fe5421fbb4780a61c5f565af077`
  - `runs.jsonl` sha256 `c23dec91a97cc04f3fb51e15d6248833dfa536a56cf7fda7d75713d82d6808a7` (1,840 rows)
  - `COPY_RECORD.json` sha256 `84ad2edd43e64e3dff9419ab8e8c3d0845df7a75d7b718b2b149486d9f30c841`
- Nodes: `gc7rc_etth1`, `gc7rc_forestcover`, `mlgym_metamaze`, `mlgym_titanic`; `d21_verdict` all
  `does_not_qualify` (reported, not a selector).
- Source and copy kept; no label/test/evaluation value read.

**Next:** the fresh source-to-copy review on `compute-relcopy-x-20261128-review`; then the coordinator publishes
the accepted copy, and local's expansion P10 step uses it.
