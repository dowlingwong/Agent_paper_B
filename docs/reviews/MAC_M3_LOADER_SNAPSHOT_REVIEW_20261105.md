# M3 synthetic OpenML loader snapshot — independent review

AI-assisted independent review, 5 November 2026. **Round 1: NOT ACCEPTED.** Reviewed candidate `8249284b7f6c701103ffc6165e5c5d70921857b3` against `14686a29dd502b7c5688523d853b576ebea830d1`, in an isolated checkout. This is an incremental snapshot helper and synthetic loader test, not M3 approval or permission to run a replay.

## Finding

**Major — inaccessible directories are silently omitted from the purported complete cache fingerprint.** `r1/c3/offline_preflight.py:43` uses `os.walk(root, followlinks=False)` without an `onerror` handler. The default `os.walk` suppresses directory enumeration errors. In a synthetic independent probe, a two-subdirectory cache with `os.scandir` made to raise `PermissionError` on one subtree returned a successful hash containing only the accessible file. Consequently a nonempty cache may be incorrectly described as fully fingerprinted. Fix by failing closed on traversal errors (including nested directory enumeration) and add a synthetic regression that checks `SnapshotStop`, then return the exact candidate for same-reviewer recheck. This issue does not lift any existing STOP.

## Independently checked

The diff from `14686a2` changes only the new `r1/c3/offline_preflight.py`, `r1/tests/test_m3_pinned_openml_loader.py` and the accompanying snapshot report. There is no diff to the five author-owned files `r1/c3/train/run.py`, `r1/c3/train/trainer.py`, `r1/c3/env.py`, `r1/c3/control.py` and `r1/c3/prior_model.py`; `r1/scripts/c3_env_replay.py` is also unchanged, leaving its existing production OpenML STOP intact.

The harness checkout used for the test resolves to `6adf3859de66c4814fcf376eed59880fbd8eeaf7`; installed scikit-learn reports `1.8.0`. Independent local synthetic test command:

```
AR_M3_PINNED_HARNESS=/private/tmp/paper-b-m3-harness-6adf385 R1_REQUIRE_M3_HARNESS=1 AR_HARNESS_ROOT=/Users/wongdowling/Documents/autoresearch_harness PYTHONDONTWRITEBYTECODE=1 /Users/wongdowling/Documents/autoresearch_harness/.venv/bin/python -m pytest -q -p no:cacheprovider r1/tests/test_m3_pinned_openml_loader.py
```

**7 passed**, with four scikit-learn invalid-cache warnings. The complete synthetic iris-derived cache exercises the actual pinned node loader without an intercepted Python `urlopen`; the missing, partial and wrong-ID cases are stopped by the test's Python interception, and the corrupt case raises `BadGzipFile`. A warning about redownloading is not evidence that the corrupt case actually attempted a network call. The tests also monkeypatch Python socket creation and `os.unlink`; this protects the fixture but is not Linux syscall or process-tree containment. No host, external service, model, GPU, training or real replay was used.

The report correctly discloses that a cache hash does not prove completeness, historical provenance or offline executability; the accepted Linux containment design, all-16-configuration preflight, independently reviewed implementation and separately authorized host qualification remain open. The report does not establish or authorize M3 execution.

## Same-reviewer recheck

**ACCEPTED for the incremental snapshot helper and synthetic loader tests only**, at candidate `73389d2675dd65da31fc22c6407cb3d481aa891e`. The helper now supplies `os.walk` with an `onerror` callback that raises `SnapshotStop`, and a synthetic traversal-error regression was added. In my independent nested-directory PermissionError reproduction, the helper now raises `SnapshotStop` instead of returning an incomplete fingerprint. Its code, tests and report in this independent checkout are byte-identical to the candidate.

The same local pinned-harness/scikit-learn command above returned **8 passed, 4 warnings**. The invalid-cache warnings are from scikit-learn; the disclosed Python-only interception remains a fixture, not isolation. The candidate still does not implement or prove the Linux supervisor, all-configuration offline preflight, historical cache provenance, actual host capability or scientific replay. The production OpenML replay STOP and all other author, review and host gates remain unchanged. No model, training, experiment, host or external service was used.
