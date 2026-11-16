# Independent review: B1 fake-service test portability (5 November 2026)

AI-assisted independent review (Codex); scope is only the synthetic test/fixture changes and new synthetic audit test. Verdict: **ACCEPTED for this test-only unit**, with the limitations below. No model, real GPU, remote host, real Slurm, or real model server was used; the local HTTP server is a test stand-in.

## Frozen inputs

Base `fcb5d5e`; tracked binary diff SHA-256 `b5fbbe5f693a688f6aac333d7156c3901aba5be97f86410ade0b4249ccfb6f3d`; new `r1/tests/test_b1_audit_synthetic_worker.py` SHA-256 `1b2ebfa8f15d23465b9a5467985159caa8d69bf5a5f747972aa0079ad6e5a5ca`. Reviewed in a separate local clone with the identical diff. Modified tracked paths are solely `r1/scripts/c3_fake_llama_server.py` and `r1/tests/test_llama_server_instance.py`; no production identity, process signalling, GPU, or worker code changes.

## Findings and checks

The fake nvidia-smi scanner still tests Linux zombie state through procfs and uses `kill(pid, 0)` only as a synthetic liveness proxy on non-Linux. The temporary `gpu_apps` state is produced by fake-server processes; this does not read a GPU. On Darwin, the test fixture substitutes command line, UID and liveness only for child fake servers already tracked by the fixture, and refuses unknown PIDs. The existing wrong-argv/port/process-group checks still exercise `orphan_matches` against the injected fake process identity, and the other-user test explicitly changes the fake UID and asserts `stop_orphan` does not signal it. This is an intentionally simulated identity, not evidence of Linux `/proc`, PID reuse, another user's actual processes, or production orphan safety. On Linux the actual fixture does not install this mock.

The added audit test replaces the harness worker, node and scratch cleanup with synthetic fixtures, checks that both train and split seeds reach the worker for two runs, and checks metric output mapping. It does **not** execute the real worker or establish numerical determinism. The distinct pre-existing `test_real_worker_run_is_seed_deterministic` remains unresolved and cannot be counted as passed by this test. The `test_exam_fake_end_to_end` cooperative-lease issue and nested rerun2 failures also remain open; B1 is not ready or authorized.

Independent local verification used Python from `/Users/wongdowling/Documents/autoresearch_harness/.venv`, `AR_HARNESS_ROOT=/Users/wongdowling/Documents/autoresearch_harness`, and `PYTHONDONTWRITEBYTECODE=1`, with loopback sandbox access for the fake server:

```
python -m pytest -q -p no:cacheprovider \
  r1/tests/test_llama_server_instance.py \
  r1/tests/test_llamacpp_offload_routes.py \
  r1/tests/test_llamacpp_probe.py \
  r1/tests/test_b1_audit_synthetic_worker.py
```

Result: **50 passed in 34.80 s**. These include the 12 previously failed fake-server test IDs identified in `MAC_M2_FAILURE_CLASSIFICATION_20261105.md`. Results cover this Mac fixture only, not real TASL-7 behavior. The reviewed diff may be integrated as a discrete test-only unit; an overall B1 review and required site checks remain separate.
