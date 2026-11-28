# Expansion D6 copy — g1b-x-tasl-20261126-a (28 Nov 2026)

Task `compute/20261127-36` with the reviewed handoff `local/20261128-01` (`coord/local` @ `fb0af9f3`, code
`3584990916ac32a05394ee8e7c3cea9d0fecf594`, published on `main` `73524055`). ENGINEERING_ONLY.

- **Source:** `/home/dowling/r1_tracks/t1_tasl_x/assembly/g1b-x-tasl-20261126-a/` (TASL-2 engineering assembly
  from the sealed G.1b expansion run `g1b-x-tasl-20261126-a`).
- **Destination:** this directory, produced by
  `g5_tasl.py rel-copy … --kind x` from a clean detached checkout of `35849909` at
  `/home/dowling/r1_tracks/work/paperB_relcopy_x_20261128T004723Z` (stamp `20261128T004723Z`).
- **Nodes:** `gc7rc_etth1`, `gc7rc_forestcover`, `mlgym_metamaze`, `mlgym_titanic`.
- **Rows:** 1,840 in `runs.jsonl`, byte-identical to the sealed runs file.

| File | sha256 |
|---|---|
| `summary.json` | `67355b668aad1d930814b51e91ccd76620bdad349516d7d630a467d884feaa10` |
| `ASSEMBLY.json` | `b4c90ec6a622dcd4c762ff0504751f85dde45fe5421fbb4780a61c5f565af077` |
| `runs.jsonl` | `c23dec91a97cc04f3fb51e15d6248833dfa536a56cf7fda7d75713d82d6808a7` |
| `COPY_RECORD.json` | `84ad2edd43e64e3dff9419ab8e8c3d0845df7a75d7b718b2b149486d9f30c841` |

Bindings carried in `COPY_RECORD.json`: signed G.1b spec `d0dce0584b5c1c446e989bd7f8981242b36e30f6008f0c38eb43428524cfd238`,
PRE-SPLIT v2 amendment `970d3e45b5177f0d9f6668e9495905e1878a4ffa8eab3d73c4df6b9292a3bea7`, copy list amended
by R1-T1-FEAT-DECISIONS D6 A and PRE-DELTA A. Audit seeds 7001–7010 are excluded by the copy step; no label,
test or evaluation value was read. `qualifies_D21` / `d21_verdict` in the copy record are all
`false` / `does_not_qualify` for the four nodes (reported, not a selector).

The source and the copy are kept. `SHA256SUMS` binds the five files. The local expansion P10 step uses this
accepted copy once the coordinator publishes the reviewed record.
