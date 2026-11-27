# local/20261127-12 — screening measurement: complete the evidence note for the author's signature

Owner: local (drafter). Runbook §2 order 2A. PLAN R1-SCREEN-MEASURE, R1-SCREEN-MEASURE-CHOICES (items (1)–(9) settled on 23 Nov,
so P7 is PASS; option (a) stands, and the P7 sentence "item 1 now includes (d)" in the draft is stale wording to correct, not a new choice).
Base: `main` `98c571d2`.

The engineering smoke PASSED: `docs/r1/reports/screen_smoke_repeat_20261127/SCREEN_SMOKE_REPEAT_20261127.md` (168/168, no STOP,
`failed_runs.jsonl` absent; cache `tree_sha256` `c0c2a364…`, `MANIFEST.json` `74e688e7…`; the cache directory kept on deepthought).
Prepare `docs/r1/authorizations/screen_measure_<YYYYMMDD>.md` from `SCREEN_MEASURE_AUTHORIZATION_DRAFT_20261123.md` **with
`approved: false`**: every P line PASS with its record and sha256 (P4 with the cache hash and directory), `data_cache_sha256`, code_commit
at the merged fix (`03a352d9` or later), the pre-declaration's published path and sha256 (publish its draft as the pre-declaration
file if the draft's order requires), and the run id from CHOICES (5). Run the note's draft check. Get a re-check by the screening reviewer of
the filled lines. Push a branch and report what the author signs. The coordinator then brings it to the author; nothing launches before
the signed note is on `main` and its check passes.
