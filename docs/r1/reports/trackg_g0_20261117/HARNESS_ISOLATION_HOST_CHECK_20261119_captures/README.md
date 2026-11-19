# Captures for HARNESS_ISOLATION_HOST_CHECK_20261119

Evidence for `../HARNESS_ISOLATION_HOST_CHECK_20261119.md` (Ada `ucrtasl`, uid 1030, 19 Nov 2026 UTC).
Copied from `/home/dowling/r1_trackg_20261117/host_check_g0_20261119/` on Ada. `SHA256SUMS` lists every file.

| Path | What it is |
|---|---|
| `captures/host_facts.txt` | host/sysctl/cgroup/systemd//sys/GPU inventory (condition 1–4, 7 context) |
| `captures/probe_userns.txt` | real `unshare()` probes with the launcher's flags (condition 1) |
| `captures/probe_remount_flags.txt` | flag-by-flag `/sys` bind-remount result (root cause A) |
| `captures/mounts_after_unshare1_*.txt` | same mounts under `unshare(1)`; shows the operations themselves work |
| `captures/probe_cgroup.txt` | the unit's own `RunCgroup` in a `systemd-run --user --scope -p Delegate=yes` (condition 3) |
| `captures/probe_interp_sandbox.json` | `sys.path` and the unit's `_sandbox_config` hard check, three interpreters (condition 5) |
| `captures/probe_sandbox_unit_py3.json` | `worker_sandbox_available()` refusal, `/usr/bin/python3` (condition 6) |
| `captures/probe_sandbox_unit_torch312.json` | same, `envs/torch312/bin/python` (condition 6) |
| `captures/probe_smoke.json` | the runner refusing the sandboxed smoke (`RunnerError` at `runner.py:472`) |
| `captures/probe_smoke_control_no_sandbox.json` | labelled `no_worker_sandbox` diagnostic control run (record in `records/`) |
| `captures/pytest_targeted.txt` | the unit's targeted test failing with the same refusal |
| `captures/pytest_isolation_deselect.txt` | unit test file with the one hanging test deselected: 14 failed / 9 passed / 1 skipped / 1 deselected |
| `captures/pytest_isolation_full.txt` | full-file run that hung at `test_elapsed_time…` after 5 passed / 7 failed; copy `…_hung_20261119.txt` is byte-identical |
| `captures/paper_a_status.json` | Paper A gate: `clear_finished`, `paper_a_live_waiting_for_card: false` |
| `captures/gpu_compute_apps_live_wrapper.txt` | other users' GPU jobs at check time (idle GPUs 2 and 6) |
| `captures/gpu_state_live_wrapper.txt` | **empty by design**: `nvidia-smi-live`'s awk filter drops `--query-gpu` rows (it is built for `--query-compute-apps`); raw GPU inventory is in `host_facts.txt` |
| `captures/fixcheck/` | scratch-copy diagnostic (`/tmp/ada_iso_fixcheck`, not an accepted worktree): preserve-flags probe results, the uv-venv PID-1 `execve` failures, the minimal diff, and a diagnostic `effective: true` smoke record from `/usr/bin/python3` |
| `records/` | exact run directories: the labelled control run and the scratch-fix diagnostic run; refused runs have no `run_record.json` |
| `scripts/` | every probe and capture script, so the check can be re-run |

Notes:

- `probe_sandbox_diag*.txt`, `probe_mounts_only.py` and `probe_sandbox_diag*.py` are intermediate diagnoses kept
  for completeness; their first versions had a diagnostic bug (uid captured after `unshare`, tmpfs fstype omitted)
  and are superseded by `probe_remount_flags.txt` and `mounts_after_unshare1_*.txt`.
- The `fixcheck/` record (`records/g0_scratch_fix_systempy_20261119T005346Z/`) proves only that the host is
  otherwise sufficient when the two bind-mount defects are fixed in a scratch copy; it is **not** the accepted
  unit and does not satisfy the condition-6 smoke requirement.
