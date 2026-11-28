# compute/20261128-19 — P.4 phase-1: the signed spec commit (P3) and the timing capture (P5)

From local's STOP (`coord/local` `7f6db2c0`, draft `local-20261128-13-p4-phase1-note` @ `be602ef3`).
1. **P3, project signature.** The reviewed one-file spec commit `befb58c8` (`docs/.../trackp_p4/p4_spec_ada_phase1_20261127.json`, parent `0b465954`) is
   unsigned. Reproduce exactly those spec bytes in an **SSH-signed** one-file commit on parent `0b465954`, with the project signing identity the launch
   builders already use for SSH-signed commits (`build_g1bx_launch.py` / `build_xc3_launch.py`; see `G1B_EXPANSION_PREP_20261126.md`). Push it on a branch,
   report the commit, `git verify-commit` output and the spec sha256 (must equal the reviewed bytes). Never read or copy key files; use the identity
   where it is configured. If no project signing identity is configured on any host you reach, STOP and report: it then goes to the author.
2. **P5, timing.** The timing receipts match the admitted Ada config but do not capture kernel binding. On the Ada card under the per-card lease, run the
   phase-1 timing probes with the same kernel-binding capture the staged smoke uses (per arm as the draft lists), ENGINEERING_ONLY; record per-arm time,
   GPU-h, kernel binding, peak memory; fresh review of the timing record. Local then writes the reviewed timing carry-forward into the note.
Priority: after the G.5 launch (waiting for the author on the launch base) — so now.
