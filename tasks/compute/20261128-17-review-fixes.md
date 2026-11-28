# compute/20261128-17 — two reviews to close: P11 complete matrix and P7 exact runtime

1. **P11 complete matrix** (`compute-g5-p11-matrix-complete-20261128-review` @ `fac6da68`, R2 CHANGES REQUIRED): B1 `SHA256SUMS` lists 18 captures that are
   absent (commit them, force-adding ignored files unchanged, or correct the manifest); M1 explain the 32-minute gap before the sealed determinism attempt
   from the captures; m1 `-closeserver` server-1 wording; restart timing citation. Re-check. All four scenarios' evidence holds per the reviewer.
2. **P7 exact runtime** (`compute-d3a-p7-exact-20261128-review` @ `05d86fb1`, CHANGES REQUIRED): apply the findings (incl. m4: soften the causal sentence;
   the co-tenant note). Keep the verdict against the stated base (rev 4, 12.99 %); add one line that R1-D3-REV5 (`main` `53f58881`) sets 18.53 % and that
   the gate is re-read after rev 5 is frozen (the coordinator does that). Re-check.
3. Then `compute/20261128-16` (E0 fresh runs: Ada now; TASL-7 now that P11 is done).
