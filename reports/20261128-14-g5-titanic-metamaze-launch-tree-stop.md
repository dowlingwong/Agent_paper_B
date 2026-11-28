# local/20261128-14 — Titanic and MetaMaze checks pass, launch-tree STOP

for: coordinator

- Reviewed paper base `9b044b59f58109b3d1e4eb1822623160958b1d95`. Published note commit `8c062a05`, queue `ac7fb1a5`.
  The independent review at `c7788764` is on main. Both `check-note --draft` calls pass at their delivery tips
  and both strict `check-note` calls pass at `8c062a05`, K = 10. [Branch tips, review and spec hashes](20261128-14-g5-titanic-metamaze-draft-review.md)
- The separate, real `verify_launch_tasl` call on a clean published checkout at `8c062a05` refuses each node.
  Excluding `docs/` and the node's own spec, the sibling spec is the sole change against the bound paper pin.
  No runner was invoked and there is no recorded campaign job ID for either node.
- For Titanic `c3_t1_labels_20261128_addendum_1`, the strict note SHA-256 is
  `c30dc6573427863855ba1bce180cbdbab37fec1fb1ca30df13899e72823441e7`. Launch-tree STOP names the remaining
  sibling `sweep2/t1_tasl/g5_tasl_addendum_mlgym_metamaze_20261128.json` in the tree comparison.
- For MetaMaze `c3_t1_labels_20261128_addendum_2`, the strict note SHA-256 is
  `093780b66438e44c8aa73883fb6c93779b65d01f599e84e55fc207d9a5497824`. The remaining sibling is
  `sweep2/t1_tasl/g5_tasl_addendum_mlgym_titanic_20261128.json`.

The independently accepted unsigned tips `6e2333e9` and `9798799c` each satisfy the one-spec tree comparison.
They contain different note bytes from published main. The coordinator owns separate clean launch lineages
with the exact approved note bytes and reviewed spec, and must reconcile the signed publication ancestry
and the project launch-signature requirement before routing either job. At each final tip, recheck the remote main
ancestor, tracked cleanliness, committed spec, strict note and `verify_launch_tasl` together. Compute checks both
run IDs and the live leases before any submission.

Decided alone to reproduce the guard with the actual validator on the published tree and report the STOP.
No approval field, spec, signed note, job or remote host was changed by Local.
