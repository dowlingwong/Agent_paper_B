# local/20261127-07 — harness unit: verify-seed base parameter (R1-D3-VERIFY-SEED)

Owner: local. Runbook §2 order 2A. PLAN **R1-D3-VERIFY-SEED** (`main` `8b01ef6a`). After `local/20261127-01` and `-05`.

In `dowlingwong/autoresearch_harness`, a branch from `a3fedbbd`: one parameter for the verify-seed base used by `_run_verify`
(`campaign.py:721`). The default reproduces `1000 + 10*budget_index + index` bit for bit: a test runs a fixed campaign at both commits
and compares the verify seeds and outputs. Nothing else changes (`git diff a3fedbbd` lists only that and its tests). Tier E: harness
tests, the paper repo's full suite at the new pin (an `AR_HARNESS_ROOT` comparison against `a3fedbbd`), and review. Then propose the
D.3 verify-seed block, disjoint from every namespace the pre-declaration declares, and the separate reviewed disjointness check that
the pre-declaration's §4.1 cites (outside `r1/c3/d3_analysis.py`). Report the new harness commit and the block.
