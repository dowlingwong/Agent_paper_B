# local/20261127-05 — screening data-cache: identify the ARFF by content, not by suffix (compute's STOP)

Owner: local. Runbook §2 order 2A. Base: `bd406db9`. **Before the Student-t unit's review round if it is waiting; otherwise next.**

Compute's STOP `reports/20261127-06-screening-smoke-stop.md` on `coord/compute` (`compute-screen-smoke-stop-20261127` @ `33767535`):
`STOP: openml_breast_w's cache holds 0 ARFF files, not one`. Under the pinned scikit-learn 1.8.0, `fetch_openml` stores the download
as `<id>.gz` (`52350.gz`). Its decompressed sha256 equals `PILOT_ARFF_SHA256["openml_breast_w"]`, but `check_pilot`
(`r1/noise/screen_measure.py` l.233–238) counts only `.arff`/`.arff.gz`. Fix: identify the ARFF file by content (gzip whose
decompressed bytes start with an ARFF header, and for pilot nodes whose decompressed sha256 is the pinned one); exactly one such file
per node, as before. Add the `<id>.gz` layout to the tests. Tier E, full suite, review (a re-check by the same reviewer is enough). Then
compute repeats `compute/20261127-07` from a fresh cache directory (the STOP scene stays).
