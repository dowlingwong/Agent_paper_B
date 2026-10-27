# Deepthought preparation test failures — 27 October 2026

AI-assisted (OpenAI Codex); independent scoped review by a separate Codex reviewer. The author explicitly instructed “允许提交并重新准备”.

The author-approved fresh batch `/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_18wc1y` records paper `3c4651d00e03f49fb64d83abc0ae3437de01e84d`, harness `6adf3859de66c4814fcf376eed59880fbd8eeaf7`, and `prepare.json` `ok: false`. Its paper suite had 553 passed, 38 skipped and two failures; the harness failure set was accepted by the existing checker. The full failed batch and logs remain unchanged and are not a launch candidate.

The dryrun push-URL test inherited `R1_C3_BATCH_ROOT` from the launcher. Its own fixture now clears the `R1_C3_` prefix, while still exercising the real guard and push-URL refusal; no production guard changed. The historical scripted live golden used the current repaired wdbc starting configuration. Its test now reads the exact golden-recorded harness commit `9c4902d0d8776f18a081e1ff2478d651fc7096c1` and writes that historical config only into the temporary node; it compares all outputs against the unchanged golden. Missing Git objects fail closed. The golden tests the historical starting point and does not establish behavior of the new starting configurations; those have separate D21/D28 evidence.

The two changed tests passed in an independent diagnostic worktree on deepthought using the repaired harness and the launcher's `R1_C3_BATCH_ROOT`; the independent reviewer also reproduced 2 passed. No scientific configuration, data, golden, prepare gate, or evaluation threshold changed. A new batch must repeat both full suites and pass the unmodified preparation gate before launch; an earlier STOP is never resumed or overwritten.
