# Independent tier-E review of D.3 step (8)

Task `local/20261128-04`. Base `914e1cf90fcc1a87dd2a59cc4984842281438eeb`.
Independent Codex reviewer `review_step8` reviewed the branch without writing the implementation.

**Initial verdict: NOT ACCEPTED** at `150d63a9d3d871a7b6f7ee687b2c251970eb2b1b`.
Five existing HPO end-to-end tests errored during setup because their fixture supplied an arbitrary digest
to `HPO.build_table`. The focused run had 117 passes and one optional skip.

**Re-check verdict: ACCEPTED** at `950e9303e225b353e7513775b74c098a5323d31f`.
The follow-up changes only the fixture's digest, preserving the existing assertions and resolving all five errors.
There are no open review findings.

- Verified that the freeze `9cd5863c` and the accepted screening record `bf4e0083` are ancestors of the base.
  The screening completed all 10,164 runs with zero failures. No node returned `SHARED` and all three published
  decision fields read `R1_THEORY_RHO_2_FINAL`. This releases revision 4 under R1-D3-STEP8-HOLD (3).
- Recomputed the frozen declaration SHA-256 from published Git bytes. It is
  `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745`.
  The candidate retains the exact frozen declaration, pinned analysis and pinned analysis test bytes.
  The D.3a authorization draft stays `approved: false` and carries the exact declaration digest.
  Its SHA-256 is `7f8a38b35c71100a23aef1b68867d9c4932e8113f7ac11aaf8887aeac550e841`.
- Exercised the production `r1.c3.d3.assemble.main` entry point on synthetic G1/G6 records for D.3a
  (882 rows), D.3b without A6 (252), D.3b with A6 (378) and HPO-REF (252). All four persisted headers
  used the independently computed digest. Each variant refused a declaration with one extra newline and
  created no output. The focused suite also checks the alternate HPO builder and direct G7 write refusal.
- `git diff --check` passed. The focused command below passed 122 tests with one optional ConfigSpace skip.
  Python 3.11.5, fresh `TMPDIR`, clean harness `9bb416805175149eb87b71f28d77530572aa4bce`.
  The full-suite comparison is listed separately in the task handoff.

```sh
python -B -m pytest -q -p no:cacheprovider -rfE \
  r1/tests/test_d3_outcome_table.py r1/tests/test_d3_integration.py \
  r1/tests/test_d3_analysis.py r1/tests/test_d3_hpo_ref.py
```
