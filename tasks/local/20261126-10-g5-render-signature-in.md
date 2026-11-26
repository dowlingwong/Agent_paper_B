# local/20261126-10 — G.5: the signature is on main (first input of local/20261126-08)

The author signed G.5 on 26 Nov 2026: row **R1-G5-SIGNATURE**, merged to `main` as `ef06a65c`. Its choices: S1 A; S2 216.9;
S3 as drafted; **S4 (a), the CUDA-IPC acceptance line** (`cuda_ipc.mode` accordingly); S5 A; **S6 (c), freeze-wait release
date 2027-12-31** (the spec's `key_values.freeze_wait_release_date`; no "moved by author row" suffix, because it is the
spec's own date); S7 as proposed; S8 as listed; S9 not decided; S10 the two rows; S11 K = 10; S12 as rendered; S13 0-7 with
the two flock leases; S14 A.

`local/20261126-08`'s second input, the reviewed REL-T1-G1B copy (`compute/20261126-05`), is **not** on `main` yet. Do the
"prepare now" part of -08 at once, with these values. Render the final note only after a later task file names the copy's
merge commit. Row (2) is the publication rule: a render that changes any choice, or needs a code change, goes back to the
author through the coordinator.
