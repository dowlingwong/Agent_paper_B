# Script sources for this node's U2 capture

- `run_node.sh`, `verify_u2_records.py`, `compute_sampler_max.py`: the Ada scripts in their final (post-fix)
  state, copied from `/home/dowling/r1_engineering/u2_iso_20261119/scripts/`.
- The campaign fixed two launcher/verifier defects after some launches; both patches are preserved here:
  - `_patch2_verifier_s002_fix.py` — verifier special-case for the deliberately divergent `s002` (applied
    before the mlab_cifar10 re-verification; the original false-negative output is preserved in that
    directory as `verify_full.v1_verifier_bug.json`).
  - `_patch3_mid_watcher_fix.py` — mid-run watcher loop-variable fix (bash resets the special `_` variable).
    For `mlab_cifar10` and `mlab_imdb` the launch-time runner had the buggy watcher, so their dedicated
    full mid snapshot is absent and `gpu/gpu_mid.txt` is sampler-derived (labelled); later nodes ran the
    fixed runner and have a direct mid snapshot.
- The runner state at launch for this node is described in the report's **Deviations** section.
