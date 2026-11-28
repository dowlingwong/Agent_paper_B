# Independent tier-E review of the unsigned Titanic and MetaMaze G.5 addenda

Task `local/20261128-14`. Reviewed paper code pin and base for both specifications
`9b044b59f58109b3d1e4eb1822623160958b1d95`. Fresh reviewer independent of the spec and note author.

Verdict: ACCEPTED

This verdict covers the exact specs and unsigned note text, with the final citation to this review. Publish this
review and run the official `check-note --draft` on each candidate. Compute verifies the live run and lease ledger,
then runs preflight at the exact published per-node launch tip.

| Node | Run ID | Spec SHA-256 |
|---|---|---|
| `mlgym_titanic` | `c3_t1_labels_20261128_addendum_1` | `2b68a4f40212acbc30a84867486e07ae6485efd4134a4cb778392f2e9f50ad5b` |
| `mlgym_metamaze` | `c3_t1_labels_20261128_addendum_2` | `4112e44995dedf1136d1c926c57c9d9bd052a07be339cd0d93a134e070d0f85d` |

The reviewer ran the actual binder and validator on both drafts with only the review blob supplied as an explicitly
synthetic fixture. All other reads used published `main` at the paper pin. Both bound the strict signed base, K = 10,
W = 20 manager calls, 12 history-mode instances, signed audit seeds and the 425 worker-card GPU-hour reporting
threshold. The checks passed for the G.1b receipts and matching deterministic assembly, D6 copy and review,
PRE-SPLIT amendment and exact P3 v2 split, P10 law and exact G.5 host PASS record. All six prose hash citations in
each note verified. The existing independent switch review covers refusal for a missing or failed G.1b completion,
an unpublished note, a changed pin, an incompatible CPU placement, the wrong split and a 1GC supply request
(`G5_EXPANSION_BINDING_REVIEW_20261127.md`).

- Titanic uses CPUs 12–15 and `torch312` at the exact candidate `d2ce4701faf03f00efaf9c475879acf213411d3b`,
  its additional census lease and the Gaussian law. The run budget is 467.895 s. The reviewed planning estimates
  are 89.14 worker-slot hours and 12.20 TASL-7 proposer card hours.
- MetaMaze uses CPUs 0–3 and `venv_jax` at the exact candidate `3f92d3c3fa9a6c41e583bb6075e3f92f8caed685`.
  The census lease is already among the S13 leases. The law is Student-t with ν = 5 and sd-matched scale.
  The run budget is 163.878 s. The reviewed estimates are 37.63 worker-slot hours and 7.70 proposer card hours.
- Both nodes use CPU campaigns and audits on TASL-2, with the separately metered proposer on TASL-7. Both supply
  the T1 MLGym suite and primary gate after the signed releases. The independent projection recompute matched.
- Each checkout starts from the published paper pin and adds its own spec and unsigned note. Preserve each spec-only
  commit and the corresponding approved note in the same clean publication lineage. The sibling spec would count
  as a non-document difference under the literal launch binding. Publish and use the separate launch tips.

No host or sealed evidence access occurred in the review.
