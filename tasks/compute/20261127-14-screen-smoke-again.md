# compute/20261127-14 — screening smoke again (the ARFF fix is on main)

The content-based ARFF fix is on `main` `03a352d9` (merge of `mac-screen-arff-content-20261127` @ `cb684870`). Repeat
`compute/20261127-07` from a clean checkout of `origin/main`, with a **new** cache directory (the STOP directory
`..._STOP_arff_suffix` stays as it is). The same reporting applies: cache `tree_sha256`, `MANIFEST.json` sha256, 168/168 written with
no STOP, `failed_runs.jsonl` absent or empty.
