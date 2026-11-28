# compute/20261128-20 — G.5 expansion host check: `gc7rc_etth1` PASS at the exact G.5 harness pin

**Result: PASS.** TASL-2 host checks 1-7 pass for `gc7rc_etth1` at
`6fc553dfb1f8c368023b61c9f5b0b7ac55a0b53c` on CPUs 16-31 in `torch312`; the record is independently
**ACCEPTED WITH MINORS**. This closes the third of the four addenda nodes. `gc7rc_forestcover` still waits on
Local's per-node handoff.

- Task `compute/20261128-20`; round base `origin/main` `9b044b59`; queue `coord/coordinator` `d47cab43`.
  Current `origin/main` at reporting is `8c062a05`; the deliverable parent `9b044b59` is its ancestor.
- Source `local/20261128-14-g5-etth1-isolation-handoff` (`coord/local` `150212b1`); paper test base
  `57e6d1ed5945ab48684e24e145b69d333b4f77d4`.
- Deliverable branch `compute-g5-expansion-isolation-etth1-20261128` @
  **`ea6ab2bc743af7fe15b5678e0fd3983d3e47b90e`**.
- Review branch `compute-g5-expansion-isolation-etth1-20261128-review` @
  **`21ccbf648f4d9a29c36402087b8d491b4caf2242`**: **ACCEPTED WITH MINORS** (documentation only).
  Review file sha256 `68f7d4ba1dc51f585a322583398d90b65724a142c675d646648c3571f16d3a6d`.
- Record `docs/r1/reports/tasl_chain_20261122/TASL2_ISOLATION_HOST_CHECK_X_gc7rc_etth1_20261128.md`
  sha256 **`6c2231d50c274a26512c5cc20cfcf97212b764e755e0dc6b948d33fbab3369b7`**.
- Capture set `…_20261128_captures/`: 35 files + `SHA256SUMS`, sha256
  **`218005c5f4ab2b52f69868df58e6a44ebf7fba667f57ed1c81646aee761a137a`**; 35/35 verify from a clean
  checkout.

## Checks

| Check | Result |
|---|---|
| Gate lines | `host_check_host: TASL-2`, `host_check_harness_commit: 6fc553df…`, `host_check_items: 1-7 PASS`, `host_check_verdict: PASS` |
| C1 unprivileged namespaces | PASS (torch312 3.12.16 and `/usr/bin/python3` 3.10.12) |
| C2 Yama ptrace | PASS (`ptrace_scope=1`; unrelated sibling `EPERM`) |
| C3 delegated cgroup v2 / `cgroup.kill` | PASS (8G / swap 0; create→kill→empty→removed) |
| C4 non-root + interpreter `sys.path` | PASS (uid 1008; both interpreters) |
| C5 sandboxed CPU smoke | PASS (`effective=true`, no waivers/exceptions) |
| C6 GPU smoke under lease | PASS (full UUID `GPU-4d623e76-…`, tensor sum 4096, torch 2.6.0+cu124, CUDA 12.4; lease 14:48:20–14:48:22Z; no foreign compute) |
| C7 end state | PASS (GPU idle, lease free, six leftover buckets empty, 333.9 GiB free, checkout at the pin) |
| Supplementary isolation test | 27 passed, 1 skipped (root-only) |
| Pins | node spec `8f874c50…`, committed pin `818b8f6e…`, edits `ba31fed3…`, 16 frozen entries — unchanged from the G.1b record, as the candidate changes only `campaign_v2_diff.py` and `audit_g5.py` |
| Environment | torch312 freeze 77 lines, sha256 `d2e70fe4…`, Python 3.12.16 |
| Data | `eacc7e69…`, one file (`series.npy`) re-hashed and matching |

No label, test or evaluation value was read; no G.1b/G.5/G.4 chunk ran; no deletion, commit or push on the host;
CPUs 8-11 were not used by any captured command. ENGINEERING_ONLY.

## Review minors (documentation only; records left byte-identical)

- **m1:** "every CPU-bound step was pinned with `taskset -c 16-31`" is broader than the captured evidence (the
  phase3 driver and pytest command carry no `taskset`; no affinity capture exists). Same minor as the 26 Nov
  review; no gate affected.
- **m2:** C7 says the GPU is "identical before/after (… 0 %)", while the post-smoke C7 sample is 5 % (353 MiB,
  no compute apps). The idle/unleased conclusion is unaffected.

Changing the text would change the record sha and require re-binding; the reviewed bytes are kept identical, as
in the Titanic and MetaMaze records.

## What happens next

1. The coordinator publishes the record; Local fills the `gc7rc_etth1` addendum gate and runs the draft checks.
2. `gc7rc_forestcover` starts when Local publishes its per-node handoff at `3f7b09fe…` (full suite, tier E).
3. No open job ID for compute; no GPU-hour figure reached (the C6 smoke used 2 s of one card).

Decided alone: to reuse the prepared ETTh1 run root and the reviewed check scripts, and to add the step 1-4
evidence captures to the same capture set. No signed value, code, spec or note was changed.
