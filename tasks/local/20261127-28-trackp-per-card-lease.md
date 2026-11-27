# local/20261127-28 — Track P gpu_lease: check the leased card only (blocks Ada P5 and P.4 SFT)

Compute's report (`compute-d3-smoke-20261127` @ `7ecc3594`, P5 blocker note): on Ada, cards 0 and 2 were empty, but the Track P `gpu_lease` helper in
`r1/c3/train/run.py` checks compute processes on **all** GPUs and refused because another user holds cards 1 and 3–7. Under R1-HOST-FREE and
R1-CARD-SHARE (5), a launcher checks the card it uses: that card is empty, or (for new launchers) has the free memory it needs. Make the lease per
card: the selected card's UUID or index, empty-card first, and its other compute processes recorded at start and end (count and memory only). Other
cards are ignored. Tier E: tests, full suite plus the torch files, review. Then compute reruns P5 (`compute/20261127-29`).
