# Independent tier-E review — D.3 step (8) on frozen revision 5

**Verdict: ACCEPTED** for the §8 header binding, unsigned D.3a draft and P7 re-read, with the production launch hold recorded below.

I reviewed the seven-file diff for `local/20261128-12` at `32d9b5aec86456aae47086de322bf6f7b7b0b18a` against `d25938ed46953bd0ecd2d467aebd94a862e657dc` in a fresh Codex review session. I did not author the change. The initial review identified that the canonical path defaulted only in the engineering smoke CLI. The re-check verified the production assembly API, assembly CLI and G7 builder use it by default. Explicit paths remain available and must provide the exact signed bytes.

## Checks

- The D.3a draft and the production §8 builders name `docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261128_R5.md` and bind SHA-256 `700d93cac277a23f527f20a49f8606987e63f615547b435cf924b2706ec778ad`. R1-D3-PREDECL-R5 carries forward the accepted screening record at `bf4e0083`: 10,164 of 10,164 runs, zero failures, no `SHARED`, disposition `R1_THEORY_RHO_2_FINAL`.
- Standalone synthetic checks built, wrote and loaded complete D.3a (882 rows), D.3b (252 rows) and HPO-REF (252 rows) tables on the default G7 path. The production assembly API and CLI also built the 882-row D.3a table with no declaration path on the command line. Every header matched revision 5. G7 rejected revision 4 and altered revision 5 inputs and refused writing a table with revision 4's digest. The separate HPO-REF builder accepted revision 5 and rejected revision 4 and an all-zero digest.
- `python -B -m r1.c3.d3_verify_namespaces` passed for all 160 seeds (20,010–20,801). The full base/tip test comparison is tracked in the worker report. `git diff --check` passed.
- Frozen revisions 4 and 5, the pinned analysis and its tests, the verify-seed checker and the G2 artifact are byte-identical to the base. I recomputed their SHA-256 values below. The D.3a draft remains `approved: false` and P9 remains with the author.
- The exact-runtime P7 receipt and accepted re-check at `a70c8872` support the re-read under R1-D3-REV5. All 14 engineering campaigns completed across runs `d3a-p7-exact-20261128-c` and `d3a-p7-exact-20261128-d`. The 50 charged failures in 276 trials equal 18.11594%, about 0.41 percentage points below 18.53%. The receipt's original 12.99% STOP remains part of the engineering record. The new draft correctly cites the `-c 32768`, one-slot, q8_0 K/V command, the GGUF and binary hashes and the 28.85 GPU-hour engineering projection. These two smoke instances establish the recorded pass and sizing basis.

## Production launch hold

The accepted P7 receipt documents work-root locks for its engineering server. It lacks the canonical production lease capture for the selected endpoint and GPU UUID. The P8 comparison covers the v1 HTCondor image and the deepthought audit environment. The selected direct campaign environment and the image disposition under revision 5 §§2 and 7.2 remain open. The delayed host RAM sample and one-instance scratch measurements also leave the production resource request basis open. The published records contain the two engineering run IDs. The executable production binding requires the reviewed manifest, canonical reservation proof, environment and resource record and a fresh evidence ID reconciled with Compute's ledger. Keep `paper_commit` and `run_id` pending until those records exist. Re-run P10 and P11 at the exact launch SHA before P9. This review opened no sealed partition and made no host request.

| Object | SHA-256 |
|---|---|
| Frozen revision 4 | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |
| Frozen revision 5 | `700d93cac277a23f527f20a49f8606987e63f615547b435cf924b2706ec778ad` |
| Unsigned D.3a draft | `afdc44f9b257ae8971436b2b5061eaffdde5ad73cdf8263bd7702e8fdb3d9cb9` |
| Pinned analysis | `c0be039905e682e8b1702542e16607f09daf30a59be3363bbdf5a85c64a484ce` |
| Pinned analysis tests | `c6c56c332d838db0acb2260ad7dc0f1a0ef90cc3bd63849bbe30fd26bf6f01a4` |
| Verify-seed checker | `62a13172b028b315c92719da5fed184f0bbaa23739d44971259fcc07d9f9f6d2` |
| G2 constants | `4f5f686be8f0210bcb27dfe0968296d68cf54e7266fb72c9038e741163776a93` |
| Exact-runtime P7 report | `05d2d6e1be204be913fa209b699f50860abf326aefa0eb1cb70e094e580f9d8d` |
| Exact-runtime P7 review | `f4e32c0af8b8f8f87cf47b94e7a92861057eca57176c63a703f7ca7732f11a19` |
