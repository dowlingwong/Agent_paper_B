# G.5 Forest Cover addendum launch-base candidate

Task `local/20261128-17`, run `c3_t1_labels_20261128_addendum_4`. The candidate
descends from the reviewed delivery `9825ee84a9eb28e20be076a4caffbd4f9d1dbb40`
and binds paper commit `f532176f3f0241909c9fb8df63a58e6fbefaefbd`.

| Published input from `c3a484055f717865e4e6826833e405af41771013` | SHA-256 |
|---|---|
| `docs/r1/authorizations/c3_t1_labels_20261128_addendum_4.md` | `085126933b9cc013f159d76ba7010f9d11acaf9252704554eabea6f8923f0e12` |
| `sweep2/t1_tasl/g5_tasl_addendum_gc7rc_forestcover_20261128.json` | `2834327aac53e5172cef3dce4aafd4f646903c0c3f4af7dc86adfbc7551b1a78` |

The approved note and the committed spec match the published bytes. The
candidate tree equals the paper commit outside `docs/` and this run's spec.

The author decides the G.5 launch-base route. The coordinator records the
signing and publication disposition under LB A. After publication, Compute
fetches main and reruns the strict note and launch-binding checks from the
exact published checkout. Before submission, Compute checks the run ledger
and TASL-2 worker and CPU-set leases and the TASL-7 proposer lease.
