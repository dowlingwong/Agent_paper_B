# local/20261127-08 — D.3 pre-declaration revision 4: complete it for freezing (R1-D3-PREDECL-R4)

Owner: local. Runbook §2 order 2A. PLAN **R1-D3-PREDECL-R4** (`8b01ef6a`): the author settled §13 items 21–31 as recommended and
signed. Item 16 stays open. The document becomes binding in its own order (its "How it becomes binding" steps).
When G2 (`local/20261127-06`) and the harness unit (`local/20261127-07`) are reviewed and merged: fill the constants sha256, the new
harness pin, the verify-seed block with the disjointness check's result, the SMAC3 version and the gate-report path for (e); apply
items 21, 22, 23, 25, 26 to the script where the draft says **[sha]** (if not already built) and re-pin §9/§14; leave `signed_by` and
`frozen_utc` for the coordinator. Then step (5), an independent review of the complete document, script and tests, and a diff-only
re-check against revision 4's reviewed text. Report the branch tip and the verdict; the coordinator then freezes and publishes it.
A change to any settled choice goes back to the author.
