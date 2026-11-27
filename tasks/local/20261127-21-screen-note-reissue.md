# local/20261127-21 — screening note re-issue (R1-SCREEN-MEASURE-REISSUE), first in your queue

PLAN **R1-SCREEN-MEASURE-REISSUE** (`main` `96eb63da`). Prepare the re-issued note as a **new file** (the signed
`screen_measure_20261127.md` stays unchanged; choose a name the note check accepts, and say which). It differs only in: `python3` in the
launch command (the interpreter the worker spawns), the run stamp and output folder, and one sentence citing the row and the STOP record
(`docs/r1/reports/screen_measure_stop_20261127/`). Same `code_commit`, design, seeds, data cache, companion pre-declaration and hashes.
`approved: true` with the signature wording of the row. Run the note's draft or production check on it. The screening reviewer re-checks the
diff against the signed note and writes "accepted". Push and report the tip, the new file's sha256 and the diff. The coordinator publishes it;
compute then launches.
