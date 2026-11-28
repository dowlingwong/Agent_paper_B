# compute/20261128-10 — P11 matrix rerun: primary PASS, four TASL-7 scenarios blocked

**Result: PARTIAL / BLOCKED, not a finished P11 matrix.** The repaired code runs the primary `-lease` matrix to
completion on both nodes (two campaign waves, all audit chunks, TASL-7 chunk side, seals, meter) and the `-infra`
STOP 7; `-determinism`, `-restart`, `-tar` and `-closeserver` could not start because another user holds the
TASL-7 GPU. No P11 PASS is claimed for those four.

- Task: `compute/20261128-10` (reissue of `compute/20261128-09`), PLAN R1-G5-P11, ENGINEERING_ONLY.
- Base `origin/main` `f7dc4945` (repair `2f110e26` published); clean checkout of `f7dc4945` on both hosts.
- Branch `compute-g5-p11-matrix-rerun-20261128` @ `15ec39887e0b370603ae794fa2653a9ff584a547`.
- Record `docs/r1/reports/g5_p11_engineering_20261128_rerun/G5_P11_ENGINEERING_RERUN_20261128.md`, sha256
  `910a1395f6598aabf344b7f60e095ee18a8f104ed7a56952f80a4259deaa9c8c`; `SHA256SUMS` sha256
  `a78f4e7c3ec25b373a33f44c717a2ee5c149ae9f48702ef26935c3f885b3b657`, 289 files verified.
- Fresh review: **not requested**; the record is explicitly partial and not offered as the final P11 record.

## What passed

- Setup: `p11-init` byte-identical on both hosts; primary spec sha256
  `f5365e84ae6147c3a24e0f8169332286fae0ed6a192826ce459a282c3c2eddc5`; `validate --launch --engineering` PASS.
- Campaigns: `mlab_imdb` and `mlgym_breakout_minatar`, waves 1 and 2, all `stop: null`, `baseline_failed = 0`,
  `invalid = 0`; proposals/ran/kept as recorded.
- Audits: 3 wave-1 chunks and 2 wave-2 chunks per node, K = 10, all `stop: null`; every deadline reproduces
  `started + 1800 + ceil(n * run_seconds * 1.5 * 1.25)` to the second (C5).
- C11/C16: claim, plan transfer, server-holds-lease refusal, chunk-holds-lease refusal, TASL-7 run, registration
  (`47807f81…`), `finalize-remote`, seal (`out.tar` `33a47644…`).
- C6/C9/C15 pre-run: every primary attempt sealed; node and run seals; server-1 span 949 s and server-2 span
  2071 s sealed and registered; meter worker 0.885 GPU-h, proposer 3020 s (0 open); table marker; release
  negative control exits at `STOP: P11 engineering outputs cannot enter a G.5 release`.
- C14: `-infra` records one infrastructure row and `STOP 7` as expected.

## The block

The TASL-7 card is not empty of foreign compute. A `tianyu` Jupyter kernel (PID 2599483, 802 MiB) and one or more
`jiachenl` benchmark jobs (e.g. PID 2637639, 696 MiB; earlier PID 2633157, 8402 MiB) are on the card. The reviewed
G.5 code refuses to start its server beside them:

```
STOP: foreign compute processes on the leased GPU before the server: [{'pid': 2624911, 'used_memory': '386 MiB'}]
(no shared card)
```

That exact refusal is on the `-determinism` start. `-restart`, `-tar` and `-closeserver` were not started because
they need the same server. The condition is infrastructure, not an outcome; nothing was killed, adapted or
worked around. The primaries' `gpu0.lock` is free, but the code's own foreign-process check still refuses.

## Hashes that matter

| Item | SHA-256 |
|---|---|
| Primary spec | `f5365e84ae6147c3a24e0f8169332286fae0ed6a192826ce459a282c3c2eddc5` |
| Server-1 record | `27174cf70d6bf3215c2258430f166aee26a9867761ff0cc8ffe457731f2adb72` |
| Server-2 record | `5a4e34eec084a510200c348405dd2e35baa3cfbd5495a9f3d1e835937f50389e` |
| TASL-7 chunk registration | `47807f81cd1a508bc7fc8c77adc287f05492114c83cc69d49c057a9e1fccb0a8` |
| TASL-7 chunk `out.tar` | `33a4764458eadfb27f4626b7c90714c2d4f82b26d9bfcad63866e5edc5390730` |
| Primary `seal-run` | in `…lease.seal_run.json`; bound by `SHA256SUMS` |
| `-infra` spec | `33edf99de2ec76c6b9e9a9c7a91c6f0a01bdec552e17017e5d04a1607e3f9354` |
| `-closed` spec | `8349e77f731392653c889137f31009ce5e3f8288b5e57563e1ce1ae7fc093559` |

## Next

When the TASL-7 card is free of foreign compute, run the four remaining scenarios from the same clean `f7dc4945`
checkout (the specs are already created under `~/r1_engineering/g5-p11` with stamp `20261128T033600Z`), add their
sections and captures to the record, regenerate `SHA256SUMS`, then request one fresh review of the complete item
table. The primary result and captures stay as they are.

Decided alone: host placement (TASL-2 worker, TASL-7 proposer and one audit chunk), the shared stamp and fresh
IDs, stopping the server for the C11 chunk, and stopping each scenario's server after its last job. No tolerance,
seed, note, spec or request was changed; no label, test or evaluation value was read.
