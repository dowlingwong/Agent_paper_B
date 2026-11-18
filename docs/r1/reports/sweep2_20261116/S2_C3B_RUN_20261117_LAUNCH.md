# S2-C3b liveness at the launch commit (H200/L40S; ENGINEERING_ONLY) — PASS 8/8

- Rerun at launch-commit candidate `50176481cbc85fb9e5b5dd97887043dea6e528fb` (origin/main @ 17 Nov; R1-S2C3B-RERUN),
  same v1 image `69b06b35…`, harness `a3fedbb…`, server settings; job 759770 on `g3609.nemo.privat` (NVIDIA L40S).
- Result: **8/8 nodes passed D28 liveness**, `max_prompt_tokens` 1537; the earlier `openml_wdbc` failure at
  `9ae6d877` did not recur, so it was not a persistent D28 failure at the launch commit. Worker runs real (fixed
  PATH/worker audit); no B.2.
- Sealed evidence `/ceph/srv/dwong/paperb/sweep2/s2c3b-20261116-a/liveness-prompt/` (SEAL_RECEIPT); the earlier
  7/8 STOP evidence is preserved aside as `liveness-prompt.stop-9ae6d877-*` (not deleted).
- Still needed: independent review of this launch-commit liveness report; and the overall launch remains blocked by
  the S2-C3 stack-difference STOP (R1-S2C3-DIAG), not by liveness.
