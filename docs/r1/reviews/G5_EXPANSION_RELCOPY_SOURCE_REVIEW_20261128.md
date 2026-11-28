# Independent source-to-copy review — expansion D6 copy of `g1b-x-tasl-20261126-a`

Verdict: ACCEPTED

Task `compute/20261127-36`, reviewed handoff `local/20261128-01`
(`coord/local` @ `fb0af9f3`, code `3584990916ac32a05394ee8e7c3cea9d0fecf594`, published on
`main` `73524055`). Deliverable branch `compute-relcopy-x-20261128` @
`c70fed2c6fde7facdd8df5c6c4ac2bd781fa9dbc`, base `origin/main`
`73524055d4a05f4375d48a98ae0b58ca0569278f`. Reviewed in a fresh worktree at the
deliverable tip; the deliverable was not modified. ENGINEERING_ONLY / `--kind x`.

## 1. Branch diff

`git diff --name-status origin/main..c70fed2c` adds exactly six files, all under
`docs/r1/reports/g5_rel_t1_g1b_20261128/x/`:

| File | Lines |
|---|---|
| `ASSEMBLY.json` | 160 |
| `COPY_RECORD.json` | 56 |
| `README.md` | 28 |
| `SHA256SUMS` | 5 |
| `runs.jsonl` | 1,840 |
| `summary.json` | 538 |

No other path is added, modified or deleted (2,627 insertions total). `runs.jsonl` is
tracked in the commit and is shadowed by the inherited `.gitignore:49` `*.jsonl` rule
(`git check-ignore --no-index` confirms), so it was force-added as stated. The fresh
worktree is clean at the tip, so the on-disk bytes reviewed below are the committed
bytes.

`SHA256SUMS` verifies for every one of its five listed files
(`shasum -a 256 -c SHA256SUMS`: `ASSEMBLY.json`, `COPY_RECORD.json`, `README.md`,
`runs.jsonl`, `summary.json` all `OK`).

## 2. Source-to-copy byte identity (TASL-2, read-only)

`sha256sum` on TASL-2 in
`/home/dowling/r1_tracks/t1_tasl_x/assembly/g1b-x-tasl-20261126-a/` yields the same
digest for each of the three sealed files as the branch copies:

| Copy path | SHA-256 (copy = source) | Source path |
|---|---|---|
| `docs/r1/reports/g5_rel_t1_g1b_20261128/x/summary.json` | `67355b668aad1d930814b51e91ccd76620bdad349516d7d630a467d884feaa10` | `/home/dowling/r1_tracks/t1_tasl_x/assembly/g1b-x-tasl-20261126-a/summary.json` |
| `docs/r1/reports/g5_rel_t1_g1b_20261128/x/ASSEMBLY.json` | `b4c90ec6a622dcd4c762ff0504751f85dde45fe5421fbb4780a61c5f565af077` | `/home/dowling/r1_tracks/t1_tasl_x/assembly/g1b-x-tasl-20261126-a/ASSEMBLY.json` |
| `docs/r1/reports/g5_rel_t1_g1b_20261128/x/runs.jsonl` | `c23dec91a97cc04f3fb51e15d6248833dfa536a56cf7fda7d75713d82d6808a7` | `/home/dowling/r1_tracks/t1_tasl_x/assembly/g1b-x-tasl-20261126-a/runs.jsonl` |

All three match the hashes listed in `COPY_RECORD.json` and in the accepted handoff.
`summary.json` and `ASSEMBLY.json` are also listed in `SHA256SUMS` and verified there.

## 3. `runs.jsonl` contents

- Exactly **1,840 rows** (`wc -l`, and 1,840 parsed JSON objects).
- Exactly the four nodes, 460 rows each: `gc7rc_etth1`, `gc7rc_forestcover`,
  `mlgym_metamaze`, `mlgym_titanic`.
- Seed fields exclude the audit band: `train_seed` values are `1001`–`1030` and
  `3001`–`3030` (plus `null` on the 640 `c0`/default records, which carry no seed);
  `split_seed` values are `2001`–`2030` and `3001`–`3030` (plus the same nulls). No
  `7001`–`7010` value occurs in either seed field, and no `run_id` carries that band.

## 4. `COPY_RECORD.json` bindings

`docs/r1/reports/g5_rel_t1_g1b_20261128/x/COPY_RECORD.json`
sha256 `84ad2edd43e64e3dff9419ab8e8c3d0845df7a75d7b718b2b149486d9f30c841`
(schema `g5_rel_t1_g1b_copy/1`) binds:

- the signed G.1b spec `d0dce0584b5c1c446e989bd7f8981242b36e30f6008f0c38eb43428524cfd238`
  (`sweep2/t1_tasl/g1b_tasl_x_spec.json`, independently re-hashed and matching);
- the PRE-SPLIT v2 amendment
  `docs/r1/authorizations/C3_SWEEP2_PREREG_AMENDMENT_SPLIT_V2_20261127.md`
  sha256 `970d3e45b5177f0d9f6668e9495905e1878a4ffa8eab3d73c4df6b9292a3bea7`
  (re-hashed and matching);
- the four nodes `gc7rc_etth1`, `gc7rc_forestcover`, `mlgym_metamaze`,
  `mlgym_titanic`;
- the sealed source, assembly and runs paths on TASL-2;
- the three copy paths with the three hashes above.

`d21_verdict` is `does_not_qualify` for all four nodes (`qualifies_D21` all `false`),
reported as such and not used as a selector. `label` is `ENGINEERING_ONLY`. No label,
test-split or evaluation value is present in `COPY_RECORD.json`; it carries only paths,
digests, node names, authority citations and the D21 report.

## `review_must_name` items (named explicitly)

- `docs/r1/reports/g5_rel_t1_g1b_20261128/x/summary.json`
- `67355b668aad1d930814b51e91ccd76620bdad349516d7d630a467d884feaa10`
- `/home/dowling/r1_tracks/t1_tasl_x/assembly/g1b-x-tasl-20261126-a/summary.json`
- `docs/r1/reports/g5_rel_t1_g1b_20261128/x/ASSEMBLY.json`
- `b4c90ec6a622dcd4c762ff0504751f85dde45fe5421fbb4780a61c5f565af077`
- `docs/r1/reports/g5_rel_t1_g1b_20261128/x/runs.jsonl`
- `c23dec91a97cc04f3fb51e15d6248833dfa536a56cf7fda7d75713d82d6808a7`
- `docs/r1/authorizations/C3_SWEEP2_PREREG_AMENDMENT_SPLIT_V2_20261127.md sha256 970d3e45b5177f0d9f6668e9495905e1878a4ffa8eab3d73c4df6b9292a3bea7`
- `d0dce0584b5c1c446e989bd7f8981242b36e30f6008f0c38eb43428524cfd238`

## Findings

None. All five review conditions hold at `c70fed2c6fde7facdd8df5c6c4ac2bd781fa9dbc`.
The deliverable is the byte-identical, correctly bounded D6 copy of the sealed G.1b
engineering assembly.

## Method

Fresh worktree at `c70fed2c6fde7facdd8df5c6c4ac2bd781fa9dbc`; branch diff against
`origin/main` `73524055`; `shasum -a 256 -c SHA256SUMS`; local re-hash of
`summary.json`, `ASSEMBLY.json`, `runs.jsonl`, `COPY_RECORD.json`, the signed spec and
the PRE-SPLIT v2 amendment; `ssh tasl2` read-only `sha256sum` of the three sealed
source files; JSON parse of `runs.jsonl` (row count, node coverage, seed-field
inventory) and of `summary.json` / `ASSEMBLY.json` / `COPY_RECORD.json`. No local live
runs file was opened; the source was read on TASL-2 only.
