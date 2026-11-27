# compute/20261127-26 — screening: rebuild the cache and repeat the engineering smoke (the fix is on main)

The cache fix is on `main` `83425c70` (`mac-screen-cache-layout-20261127` @ `e9d7f230`, code `c12136d6`). Follow the local report
`reports/20261127-23-screen-cache-layout.md` on `coord/local`: on deepthought, from a clean checkout of `origin/main`, build a **new** cache
directory with `data-cache` (it fills once, then verifies a fresh offline load writes nothing; the four pilot ARFF pins still apply), then the
168-run engineering smoke at seed 999 with the evidence worker-runtime checks (`python3` worker). Keep both earlier STOP scenes and the old cache.
Report the new cache `tree_sha256` and manifest sha256, 168/168 with no STOP, the per-job runtime records, captures on a branch. ENGINEERING only.
The local worker then prepares the second re-issue of the note (new `code_commit` and `data_cache_sha256`) for the author's signature.
