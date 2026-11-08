# TASL-7 read-only baseline before the B1 diagnosis (9 Nov 2026, 00:55 CET)

Captured by the experiment agent before any B1 host action, under the B1 STOP diagnosis plan
(9 Nov): read-only, no host write, no signal, no rerun, no gate change. The capture records the
retained STOP scene of run `6835_20261108_a` and the TASL-7 state at that instant. It is not a
verification of future state and not an occupancy clearance for a restart.

Observed: run root `b1_6835_20261108_a` present with its top-level entries; marker
`~/r1_locks/trackx_evidence.active` dev 66306, inode 56261609, sha256
092023e438a3c2508574a169becce448fd8d652481547f4a974f20ae5bdca1af, contents
`{"head": "68357d3d8cd0c9f301005e483a49ecfd05f6e5bb", "run_id": "6835_20261108_a"}`, matching the
STOP report; `gpu0.lock` present and no lock holder; GPU 0
`GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1` at 236 MiB with no listed compute app; tmux
`trks_watch` running (Track S watcher, paused on the Track X marker); disk 585G free, 118.6M
inodes free, 62G RAM total; B1 handover directory tree intact.

`ssh.log` SHA-256 is in SHA256SUMS; `ssh.rc` is 0 (SHA-256
9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa). The capture contains
`SSH_EXIT=0` and `READONLY_DONE`.
