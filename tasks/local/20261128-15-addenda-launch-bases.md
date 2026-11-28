# local/20261128-15 — clean launch bases for the published addenda (same design as the G.5 main launch base)

Your STOP (`831b8bfc`) is right: with both addendum specs in one tree, each node's launch checkout differs from its paper pin by the sibling spec.
`verify_launch_tasl` (`sweep2/t1_tasl/g1b_tasl.py`) is built for launching from a **published ancestor** of `origin/main` whose tree equals the paper
commit outside `docs/` and the node's own spec — the same design as compute's G.5 main launch base `compute-g5-launch-base-20261128` @ `2178bc6e`. For
addendum 1 (Titanic) and 2 (MetaMaze): from each reviewed tip (`6e2333e9`, `9798799c`), make a branch whose only change is the approved note bytes copied
unchanged from `main` `2a58f7ac` (`approved: true`; sha256 `c30dc657…` and `093780b6…`), plus a short launch-base record. Show on each: tree vs its paper pin outside
docs/ and its spec = equal; note and spec byte-identical to main; `check-note` strict and `verify_launch_tasl` (with origin/main simulated to contain the
base, or after merge). Do the same for ETTh1 and Forest Cover when their addenda are published. You mention a "project launch-signature requirement":
name its source (row, code line) — `verify_launch_tasl` has no signature check; if a signed launch commit is required somewhere, cite it.
These bases are merged into `main` only after the author's G.5 launch decision (A covers this design). Priority: first.
