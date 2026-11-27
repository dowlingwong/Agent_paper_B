# compute/20261127-31 — G6: remove the smoke audit path (it contradicts the frozen pre-declaration)

The D.3 smoke unit merged in `35c42b81` changed `r1/c3/d3/audit.py` so that seeds 6301–6302 get an audit block 6391–6410. The frozen pre-declaration
(revision 4, §4.1 "Engineering smoke") says the smoke instances are **never audited for Y**. The analysis refuses them, so nothing entered a table,
and 6391–6410 overlaps no declared block. But G6 should not carry a path the frozen document excludes. One small reviewed unit (tier E): restore
`audit_seeds` to refuse 6301–6302 as before (the `AuditStop` for seeds outside 6201–6218), keep or adjust `test_d3_audit_g6.py` so that it
asserts the refusal, and keep `r1/scripts/d3_smoke_engineering.py` only as a record of the 27 Nov engineering run (it must not be needed by any
evidence path). Full suite at harness `9bb41680`, fresh review. Also note: the card that asked you for a G6 audit in the smoke was the coordinator's
error, not yours. The pre-declared smoke (§11: `openml_climate`, 6301–6302, no Y) still runs later as the document says.
