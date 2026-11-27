# compute/20261127-07 — screening smoke: the fix is on main (the later task file compute/20261126-08 waits for)

Owner: compute. Runbook §2 order 2A. **Ready now.** The fix is on `main` `bd406db9` (merge of `mac-screen-measure-fix-20261126` @
`d1f239ee`; review accepted, both re-checks committed; coordinator full suite: zero new failures).

Run exactly the block "What compute runs next" in the local report `reports/20261127-02-screen-smoke-fix.md` on `coord/local`
@ `1defc8fc`, on deepthought, from a clean checkout of `origin/main` (containing `bd406db9`): `data-cache` once, then
`run --engineering-smoke` with `--data-cache`. Do not reuse the 26 Nov command line (its `--deadline` is now refused). Keep the 26 Nov
scene and the new cache directory. ENGINEERING only; the evidence run waits for the author's signature of the screening note.

Report: the cache `tree_sha256` and the `MANIFEST.json` sha256; planned, written and failed runs (P4 needs 168/168 with no STOP and
`failed_runs.jsonl` absent or empty); any STOP with its scene; captures on a branch with sha256.
