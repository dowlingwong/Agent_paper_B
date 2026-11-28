Attempt A (2026-11-28T05:49-06:27Z) is a disclosed engineering rehearsal.  Its proposer server
was pinned to CPUs 16-31 but the driver/worker processes were not, so it did not establish the
card's CPU exclusion.  Attempt B (06:41-07:16Z) repeats the same seeds with the whole job
(driver, workers, server) under taskset -c 16-31 and is the P7 receipt.  Attempt A reproduced the
same 33/271 = 12.18 % worker-failure rate and the same 6301 A2 trial-071 ParserError; its full
tree stays on TASL-2 at /home/dowling/r1_tracks/work/d3p7_20261128.  These two JSONs are kept as
the consistency check only; attempt B's tree is the captured evidence.
