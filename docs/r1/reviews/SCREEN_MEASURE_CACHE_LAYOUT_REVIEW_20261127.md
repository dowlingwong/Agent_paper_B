# Independent tier-E review of screening cache layout

Code-Commit: c12136d664ae588a2539b76b2602e36742979ce8
Verdict: ACCEPTED

**Task** `local/20261127-23`
**Base** `ab32029ec6af333d48e49262130ff928b105737f`
**Runner SHA-256** `ba05e1a4a1ff5ee643e749e60fbd6e3aa4e6681209ef2f5af940e6cafd4fdb69`

The six pinned OpenML nodes use the same `_load_frame()` for training that the builder now invokes in
a fresh `python3` process. The first load populates the exact cache paths that the loader reads. The
second overrides the network entry point in the pinned scikit-learn 1.8.0 loader and must succeed with
identical paths, compressed bytes and decompressed content. Publication follows both the pilot check
and the offline check.

I compared `cache_tree`, `read_data_cache`, `check_pilot`, `run_one_lineage`, `preflight_evidence` and
`execute` against base and verified that their source is identical. M1 still checks the launch-pinned
cache before staging and the node copy after each job. Smoke now requires the replay-verified evidence
environment and passes the same per-worker interpreter, prefix, versions and package-list checks as
evidence. It still runs at seed 999 and records `ENGINEERING_ONLY`. Evidence requires the signed
publication gate.

The former smoke and STOP manifests report the same cache tree. The breast-w description payload
matches the old manifest’s decompressed SHA-256
`27baffae3b11d330604b06a9c975f31cf9e6e417a4640dcf1941729945dc5620` and names
`52350/breast-w.arff`. The pinned stock loader derives its cache key from that URL, independently of
seed and editable configuration. The old smoke used a separate harness checkout at the same commit
and recorded the coordinator process’s package versions without per-worker runtime receipts. Those
records cannot establish which runtime or loader accounted for the historical PASS. The revised smoke
closes the observable path gap.

I independently ran `python3 -m pytest -q -p no:cacheprovider r1/tests/test_screen_measure.py` in a
fresh scratch directory with Python 3.13 and scikit-learn 1.8.0. All 83 tests passed in 10.39 s,
including the synthetic legacy-path rejection and canonical-path fixed point.
`git diff ab32029e..c12136d6 --check` passed. I verified that the local engineering manifest lists
exactly one canonical ARFF per node. Its tree SHA-256 is
`f018ad3b8d9887f82d6b8ca0ec28d9f4b82dbcbbc101d6e3c4f27e35bfb93e7d`.

Compute should build and smoke with the replay-verified batch harness and the evidence venv’s
`python3` first on `PATH`. The fresh Compute cache and worker receipts are required before a second
note re-issue. No server was accessed, no evidence was run, and no sealed partition was opened for
this review.
