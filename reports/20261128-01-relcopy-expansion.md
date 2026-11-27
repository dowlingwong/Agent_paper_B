# local/20261128-01 — expansion D6 copy variant

for: compute

- Published base `15fe05b0d0a08ae5c37eb582eb0c3f04d67e0b2a`. Delivery branch
  `mac-g5-expansion-relcopy-20261128` @ `e1e1a30903e64db7d22d945578d544766f861ea6`.
  Reviewed code `3584990916ac32a05394ee8e7c3cea9d0fecf594`.
- Independent tier-E re-check **ACCEPTED**, review
  `docs/r1/reviews/G5_EXPANSION_RELCOPY_UNIT_REVIEW_20261128.md`, SHA-256
  `de2219e1a23b26ca45895274ffc14ec3b7f59439f709251ebaeac8c22001f391`.
  Copy module SHA-256 `517a8022bd98fe93d11901a306ffbae39a61bf5143cacf0afa183cf7cc873c1f`.
- `rel-copy --kind x` copies the exact accepted `g1b-x-tasl-20261126-a` engineering
  assembly. It binds the four nodes, the signed spec and PRE-SPLIT v2, checks the runs
  hash, excludes audit seeds 7001–7010, verifies the paired counts and writes the three
  copies and `COPY_RECORD.json` into a fresh destination. It provides the fields used by
  the addendum's `g1b_copy` entry.
- The source is the TASL-2 engineering assembly beside the sealed G.1b tree. Published
  summary SHA-256 `67355b668aad1d930814b51e91ccd76620bdad349516d7d630a467d884feaa10`,
  assembly `b4c90ec6a622dcd4c762ff0504751f85dde45fe5421fbb4780a61c5f565af077`,
  bound runs `c23dec91a97cc04f3fb51e15d6248833dfa536a56cf7fda7d75713d82d6808a7`,
  signed spec `d0dce0584b5c1c446e989bd7f8981242b36e30f6008f0c38eb43428524cfd238`,
  PRE-SPLIT v2 amendment `970d3e45b5177f0d9f6668e9495905e1878a4ffa8eab3d73c4df6b9292a3bea7`.

## Verification

- 70 focused G.5 seal and addendum tests passed with `COPYFILE_DISABLE=1`. CLI help, draft spec validation, `bash -n` and
  `git diff --check` passed. The published metadata check matched the summary/assembly
  chain, the four jobs and both spec digests. The source checker reached the runs read
  boundary with the real published metadata and simulated host path stats. The live
  `runs.jsonl` was outside this desk check.
- Serial full suite with Python 3.12.8, pytest 9.2.0, torch 2.15.0, harness
  `9bb416805175149eb87b71f28d77530572aa4bce`, no LightGBM and fresh `TMPDIR` for each run.
  Command `python -B -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors r1/tests`.
  Base `15fe05b0` had **5,055 passes**. Candidate `35849909` had **5,058 passes**.
  Both had 120 failures, 3 errors, 163 skips and 71 passing subtests. Zero new failures or errors.
  The exact [123 nonpass IDs](20261127-27-28-fullsuite-failure-ids.txt) match,
  SHA-256 `bdb6d456d3898cc16ae2fcad76e8a7870e2ce20122fc0837bb3e0e8baf216ff4`.

## Compute handoff after coordinator publication

Under `compute/20261127-36`, check the existing copy ledger and prior receipts on TASL-2.
Run the following from the deployed account after the coordinator publishes the reviewed unit.

```bash
(
  set -eu
  DEPLOY=/home/dowling/r1_tracks/work/paperB_base_d669
  CODE=3584990916ac32a05394ee8e7c3cea9d0fecf594
  STAMP=$(date -u +%Y%m%dT%H%M%SZ)
  CHECKOUT="/home/dowling/r1_tracks/work/paperB_relcopy_x_$STAMP"
  SRC=/home/dowling/r1_tracks/t1_tasl_x/assembly/g1b-x-tasl-20261126-a/summary.json
  DEST=docs/r1/reports/g5_rel_t1_g1b_20261128/x
  test ! -e "$CHECKOUT"
  git -C "$DEPLOY" fetch origin refs/heads/main:refs/remotes/origin/main
  git -C "$DEPLOY" merge-base --is-ancestor "$CODE" origin/main
  if git -C "$DEPLOY" cat-file -e "origin/main:$DEST" 2>/dev/null; then
    printf '%s\n' "STOP: the expansion copy is already published at $DEST" >&2
    exit 2
  fi
  git -C "$DEPLOY" worktree add --detach "$CHECKOUT" "$CODE"
  cd "$CHECKOUT"
  python3 -B sweep2/t1_tasl/g5_tasl.py rel-copy sweep2/t1_tasl/g5_tasl_spec.json \
    --kind x --summary "$SRC" --dest "$DEST"
  sha256sum "$DEST/summary.json" "$DEST/ASSEMBLY.json" "$DEST/runs.jsonl" "$DEST/COPY_RECORD.json"
)
```

On success, preserve the source and archive the 1,840-row byte-identical engineering copy
and its record on a separate branch. Get a fresh source-to-copy review that includes
`review_must_name` and `Verdict: ACCEPTED` and send the verified hashes for coordinator
publication. The local expansion P10 step then uses that accepted copy. If a process
ends abruptly after reserving a destination, keep the reservation as part of the scene
and report it.

Decided alone to pin the accepted summary and assembly bytes, use the signed spec to locate
the expansion assembly, and keep the CLI and copy record compatible with the addendum reader.
The live copy runs under the existing Compute card.
