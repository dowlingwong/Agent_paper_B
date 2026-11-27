# local/20261127-14 — the declared gate-report output for revision 4 §7.5(e) (your STOP of 06:07)

Owner: local. Runbook §2 order 2A; PLAN R1-D3-PREDECL-R4 (2). Decided by the coordinator (level 1, routing).

`r1/c3/gate.py` prints its report to stdout, and revision 4 §7.5(e) needs a pinned output path and key. Do **not** change `gate.py`:
its hashes are bound by the preregistration. Build a separate post-freeze output unit that runs the gate exactly as declared, captures its
stdout, validates the report's schema, and writes one JSON file at a declared path with the key §7.5(e) reads, plus a sha256 manifest. It
refuses to overwrite and refuses any input that `refuse_sealed` refuses. Tier E (it parses gate output): tests on synthetic inputs, full
suite, independent review. Its path and key then fill revision 4's gate-report TODO. No gate read happens before the arms-frozen record and the
release order.
