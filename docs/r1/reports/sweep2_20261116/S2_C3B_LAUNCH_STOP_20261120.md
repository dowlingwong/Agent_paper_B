# S2-C3b liveness at the sweep-2 launch commit — STOP (7/8), no launch

**20 November 2026, 22:00 CET. ENGINEERING_ONLY. Launch commit `df58bcd5bdeeb7d1cb1cd1c3beddc29376b3575e`
(published main; sweep-2 note sha `ef4325c5…`).** R1-S2C3B-LAUNCH requires 8/8 before launch; this run failed one
node, so **sweep 2 was NOT launched** and S2-C5 was not enabled.

- Job **759810** on `g4401.nemo.privat` (NVIDIA H200), v1 image `69b06b35…`, harness `a3fedbb…`; one liveness job
  (`s2c3b-20261120-a` / `liveness-prompt`), rc 2 STOP, wall 21:42:19Z–21:57:20Z.
- **Result: 7/8 nodes pass.** The failing node is **`openml_wdbc`**, and the only failed D28 condition is
  **`invalid_rate`: observed 0.30, required `< 0.30`** (boundary; the other two criteria on wdbc pass:
  active_novelty_fraction 0.70 ≥ 0.5; keep_after_trial_1 = 2). All other seven nodes pass all three criteria.
- Sealed STOP evidence: `/ceph/srv/dwong/paperb/sweep2/s2c3b-20261120-a/liveness-prompt/`
  (`job_record.json`, `SHA256SUMS`, `SEAL_RECEIPT.json`, server log).
- Launch assets were staged but **not submitted**: 16 H200 chunk specs/JDLs at the launch commit
  (`/work/dwong/sweep2_launch_20261120/paper/chunks/`); S2-C5 keys absent; queue unchanged.
- Author decision (R1-S2C3B-RERUN): whether to run with 7 nodes plus disclosure, or investigate/rerun the wdbc
  invalid-rate boundary. No node is dropped silently and no threshold was relaxed.
