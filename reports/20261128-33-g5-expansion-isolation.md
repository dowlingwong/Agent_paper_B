# compute/20261128-20 — G.5 expansion host checks: Titanic and MetaMaze PASS; ETTh1/Forest Cover blocked on Local

**Result: two of four nodes PASS at their exact G.5 harness pins; both independently ACCEPTED WITH MINORS.**
TASL-2 host checks 1-7 pass for `mlgym_titanic` at `d2ce4701` (CPUs 12-15, torch312) and `mlgym_metamaze` at
`3f92d3c3` (CPUs 0-3, venv_jax). `gc7rc_etth1` (`6fc553df`, CPUs 16-31) and `gc7rc_forestcover` (`3f7b09fe`,
CPUs 4-7) are prepared but not run: Local has not yet published their per-node handoff/full-suite confirmation.

- Task `compute/20261128-20`; base `origin/main` `66aa4e10`; queue `coord/coordinator` `216f33ea`.
- Deliverable branch `compute-g5-expansion-isolation-titanic-20261128` @
  **`af191d0119976aeb2f47762f31ab11003d477e33`** (record commits `af6843fa` Titanic, `c17dda52` MetaMaze; `af191d01`
  force-adds the ignored `records/.../run.log` captures).
- No GPU job, G.1b/G.5/G.4 chunk, label, test or evaluation value; TASL-2 only; no host commit/push/deletion.

| Node | Pin | CPU set / env | Record sha256 | Review |
|---|---|---|---|---|
| `mlgym_titanic` | `d2ce4701faf03f00efaf9c475879acf213411d3b` | 12-15 / torch312 | `3d76372dc02ccfe01dfccb15f4c9180fbf59c2d33fa035d5a66faee9d3ece1f2` | `b07ae34db8aeff81dc4ca76ab570710b9013a44c`, **ACCEPTED WITH MINORS** |
| `mlgym_metamaze` | `3f92d3c3fa9a6c41e583bb6075e3f92f8caed685` | 0-3 / venv_jax (C6 torch312) | `80581d24da323dd9a9ef212585bfe3908165b72f583bd6f40e09b9bf6f1231c0` | `9f930de3266e6e730795b664497fdaeb5ef12a3d`, **ACCEPTED WITH MINORS** |

Both records carry at column 0 `host_check_host: TASL-2`, the exact `host_check_harness_commit`,
`host_check_items: 1-7 PASS`, `host_check_verdict: PASS`. Both capture sets verify **32/32 OK** from a clean
checkout; `stop_items.txt` is empty; the pin's isolation test is 27 passed / 1 skipped.

| Check | Titanic | MetaMaze |
|---|---|---|
| C1 unprivileged namespaces | PASS | PASS |
| C2 Yama ptrace | PASS | PASS |
| C3 delegated cgroup v2 / cgroup.kill | PASS | PASS |
| C4 non-root + interpreter sys.path | PASS | PASS |
| C5 sandboxed CPU smoke, effective | PASS | PASS |
| C6 GPU smoke under lease, full UUID | PASS | PASS (torch312) |
| C7 end state / leftovers / checkouts | PASS | PASS |

Pins: Titanic node spec `059fd0d5…`, committed pin `0368a73d…`, edits `fd464c6e…`, data `c8ccedd0…`; MetaMaze
node spec `d97bb182…`, committed pin `759d6bf0…`, edits `6de5741f…`, data `e2338195…`. Environments equal the
committed freezes: torch312 `d2e70fe4…` (77 lines), venv_jax `630ed6e1…` (56 lines).

## Review minors (documentation; records unchanged)

- Both records say the capture set is "31 files + `SHA256SUMS`"; after adding `commands.txt` it is 32 files +
  `SHA256SUMS`. The gate lines, C1-C7 and the bound record shas are unaffected; changing the text would change
  the record shas and require re-binding, so the reviewed records are left byte-identical.
- CPU affinity to the node set is stated in the record/`commands.txt`; no capture records `taskset` or
  `Cpus_allowed_list` (same minor as the 26 Nov G.1b record). Not gate-relevant.
- Titanic `host_facts` also shows the older G.1b checkout; the C7 capture binds the new worktree at the exact pin.

## Blocked

`gc7rc_etth1` and `gc7rc_forestcover`: worktrees, run roots, data links and patched node rows are prepared at
`6fc553df`/`3f7b09fe`, but Local has published only the Titanic and MetaMaze handoffs. Start each when its
handoff (full suite at the candidate pin, tier E) appears; if Local changes a candidate, rerun that node.

**Next:** coordinator publishes the two records; Local fills the two addendum gates and runs the draft checks.
No job ID is open.
