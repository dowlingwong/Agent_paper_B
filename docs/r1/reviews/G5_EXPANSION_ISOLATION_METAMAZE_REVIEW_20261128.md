Verdict: ACCEPTED WITH MINORS
# Independent review — MetaMaze TASL-2 host check at G.5 harness pin `3f92d3c3` (compute/20261128-20)

**Deliverable:** branch `compute-g5-expansion-isolation-titanic-20261128` @ `af191d0119976aeb2f47762f31ab11003d477e33`, base `origin/main` `66aa4e10`.
The MetaMaze record is `docs/r1/reports/tasl_chain_20261122/TASL2_ISOLATION_HOST_CHECK_X_mlgym_metamaze_20261128.md`,
SHA-256 `80581d24da323dd9a9ef212585bfe3908165b72f583bd6f40e09b9bf6f1231c0`.

**Reviewer:** a fresh independent reviewer (DeepSeek compute agent) who did not write the record. Read-only review from a
clean detached worktree; no host workload was run; no private key, dataset label, test partition or real evaluation
result was read. ENGINEERING_ONLY.

**Scope accepted:** the MetaMaze host-check receipt for the G.5 expansion addendum. The two minor findings below do
not affect the gate lines, C1–C7, or the pinned environment. No blocking finding.

## 1. Gate lines

The four required lines are at column 0, with no leading whitespace (`sed -n '7,10l'`):

```
host_check_host: TASL-2
host_check_harness_commit: 3f92d3c3fa9a6c41e583bb6075e3f92f8caed685
host_check_items: 1-7 PASS
host_check_verdict: PASS
```

`sha256sum` of the record is the published `80581d24…1231c0`. The record itself is byte-identical between the old
tip `c17dda52` and the force-pushed tip `af191d01`; `git diff --name-only c17dda52 af191d01` contains only four
`records/.../run.log` files.

## 2. Captures and manifest at `af191d01`

The earlier tip's `SHA256SUMS` listed two ignored MetaMaze `run.log` files that were absent from the commit, so
`shasum -c` failed. The new tip force-adds those logs (and the two Titanic logs) without changing any other capture
or the record. From a clean checkout:

```
$ cd docs/r1/reports/tasl_chain_20261122/TASL2_ISOLATION_HOST_CHECK_X_mlgym_metamaze_20261128_captures
$ shasum -a 256 -c SHA256SUMS
... all entries ...
rc 0; 32 OK; 0 FAILED; 32 manifest entries
```

- `SHA256SUMS` itself: `b10b628f1aa6e915c8160f4846390e2018b05c3d85a4b86dcb0a0bd3341343d7`.
- MetaMaze `records/metamaze_gpu_smoke/run.log`: `b42e9334b6db6d73bf4a79a933a03c40fb2f090c6aba37fff9fc9ce508e6684c`.
- MetaMaze `records/metamaze_smoke/run.log`: `9b7c8df0e97caccea061255b3d350cab087c50bca989c030df4b9194a62ff7d1`.
- Both hashes are the values already listed in the unchanged `SHA256SUMS`.
- `stop_items.txt` is empty: 0 bytes, SHA-256 `e3b0c442…b855`.
- `pytest_isolation.json`: `rc: 0`, `passed: 27`, `skipped: 1`; the tail records `27 passed, 1 skipped in 14.34s`
  (the skip is the root-only test).

## 3. C1–C7

All seven `condition_N_pass` flags are `true`.

| # | Result | Independently checked evidence |
|---|---|---|
| C1 | PASS | both captures `condition_1_pass: true`; five-flag user/mount/PID/net/cgroup unshare rc 0, uid 1008 mapped, real tmpfs mount/write, child PID 1; venv_jax and `/usr/bin/python3` |
| C2 | PASS | `ptrace_scope: 1`, `yama` in LSM; parent→child attach ok, unrelated same-uid sibling `EPERM`; `condition_2_pass: true` |
| C3 | PASS | `memory.max=8589934592`, `memory.swap.max=0`, `nsdelegate=True`, `cgroup.kill` exists, create→join→kill→empty→removed; `condition_3_pass: true` |
| C4 | PASS | euid/uid 1008; both interpreters `broad_entries: []`, `sandbox_config_ok: true`, `worker_sandbox_available: true`; `condition_4_pass: true` |
| C5 | PASS | outcome ok, `isolation.effective: true`, `exceptions: []`, `waivers: {}`, cgroup removed, log intact; `condition_5_pass: true` |
| C6 | PASS | torch312; full UUID `GPU-4d623e76-7587-ee15-a633-46f60d220d94`; sandboxed worker PID 1 allocated/synchronised a CUDA tensor; lease `~/r1_locks/gpu0.lock` acquired 14:10:43Z, released 14:10:45Z, flock-exclusive, lease log not written; no compute apps before/after; `condition_6_pass: true` |
| C7 | PASS | GPU 353 MiB and no compute apps before/after; lease free; all six leftover buckets empty; harness head `3f92d3c3…` matches the pin; seven-node checkout `c025f89a…`; Track P `897d83c8…` tracked-clean; 333.9 GiB free; `condition_7_pass: true` |

`checkout_end.txt` records `head=3f92d3c3fa9a6c41e583bb6075e3f92f8caed685`, detached, and the only untracked
entry is the expected `third_party/mlgym/nodes/mlgym_metamaze/data` link.

## 4. Pins and environment

| Item | Record / capture | Reference |
|---|---|---|
| node spec | `d97bb182a6469cc4381262960bccf58eec984996cb9a8cd89c39083b4679dbb9` | same as the 20261126 kit record |
| committed pin | `759d6bf0562a3a9334982b30b3e23c80f222c828e44847b66e743102c87d03db` | same |
| edits manifest | `6de5741f7107d9f924a3686fce85f6509ed7fb0c47ee7cc2c9fc16732d66f0b2` | same |
| data manifest | `e233819526e8214bb898c4f9dd76a8c30be7b0dcabd710b60efb815e99c38000`, 9 files, all match | same |
| venv_jax freeze | `630ed6e1b823e0e2183c64ffb09bebd9994f755f518db2867ee538f388f5fdd9`, 56 lines | byte-identical to `main` `sweep2/g1b/env/venv_jax.freeze.txt` |
| interpreter | `23bc148d2b48964b621c5561ff2b81c1d9c7b717967a7491efbf12f4304882b5`, 31,028,464 B, Python 3.12.16 | same as 20261126 record |

`pins_mlgym_metamaze.json` has `condition_pass: true`, `frozen_entries: 19`, and all nine data files matching.
`env_venv_jax.json` reports `freeze_sha256_equal: true`, `freeze_committed_file_sha256: true`, and all three
`bin/python*` links resolving to the same interpreter.

## 5. Scope and overclaim

- Only the synthetic `fake_isolated` CPU smoke and `tasl2_gpu_smoke` GPU smoke are recorded. No G.1b/G.5/G.4 chunk
  record exists in the capture set.
- No dataset labels or test partition were read. The two result-channel files are the same 43-byte synthetic
  fixture, SHA-256 `4ffec570…1117c0`, identical to the accepted 20261126 CPU and GPU smoke records; they are kit
  probes, not a dataset evaluation.
- The record states CPUs 0–3 and says CPUs 8–11 were not used; see M2 for the evidence limit.
- No host commit or push is recorded; the branch diff at this tip contains only documentation and the four force-added
  logs.
- The record does not claim the other nodes ran here. It explicitly says Titanic is delivered separately and that
  ETTh1 and Forest Cover wait for their own handoffs at `6fc553df…` and `3f7b09fe…`.

## Findings

**M1 (minor, documentation).** The capture-count sentence still says “31 files + `SHA256SUMS`”. After the force-add
there are 32 capture files plus `SHA256SUMS` (32 manifest entries), so the count is one low. Update it when the
record is next touched; the manifest itself is correct and verifies 32/32.

**M2 (minor, evidence gap for a rerun).** The record asserts every CPU-bound step was pinned with `taskset -c 0-3`,
and `commands.txt` repeats the CPU set, but no capture records a `taskset` invocation or a
`Cpus_allowed_list`/affinity check. This is consistent with the stated method but not independently provable from
the captures. If the check is rerun, add one affinity capture.

## What remains

1. Coordinator publishes the record unchanged (SHA-256 `80581d24…`) and Local fills the `mlgym_metamaze` addendum
   `host_check` gate, then runs the draft checks.
2. Correct the capture count (M1) on the next record touch; add the affinity capture (M2) only if the check is rerun.
3. Titanic is a separate review; ETTh1 and Forest Cover remain blocked on their own per-node handoffs.
