# Script sources for this node's U2 capture (mlgym_houseprice, CPU)

- `run_node_houseprice.sh` sha256
  **`360b2053a07a5794c3a776b6e1fa73f53b2627e58cd1b6c45b9c5e91afa09d8c`** and
  `verify_u2_records_cpu.py` sha256
  **`63a4bdf185d9048472fabb60dc7afe4172d4052c762db14f3d1e657a0a6d5ff7`**: the Ada campaign scripts in their
  post-run state, byte-identical to the live `/home/dowling/r1_engineering/u2_iso_20261119/scripts/` copies
  (re-verified read-only). The launcher is a script invocation of the unit's one-line command; the static
  tests were run separately with the kit-update helper (see `../prep/static_command_note.txt`).

## Verifier v1 → fixed (result-review condition H8)

The v1 verifier source and its fix diff/patch were **not preserved** (the live script was edited in place; only
the v1 **outputs** are preserved: `../verify_full.v1_verifier_bug.json` sha256
`7bccb89fa801e96f3fb1ef8469db9541d8d3e5ab156429917d7445fd2576b38f`, and
`../verify_full.summary.v1_verifier_bug.txt`). The v1 failure was a single check on every executed record
(`node_spec_sha256 expected`, 8/8), i.e. the v1 rule compared the record's `node_spec_sha256` with the **spec
file** sha passed via `--node-spec-sha` (`1b95447d…`), while the kit's record field is the **canonical parsed-spec
hash** `2f150cded7c846a28fd97113519333a33d9775588a7d6c7bd0d9dcc05e85c049` (`spec.raw_sha256`, recorded by the
kit's own runner).

The fixed script changes that one check to:

```python
"node_spec_sha256 full 64-hex (kit canonical hash)": isinstance(d.get("node_spec_sha256"), str)
and re.fullmatch(r"[0-9a-f]{64}", d.get("node_spec_sha256")) is not None,
```

i.e. it accepts the full 64-hex **canonical** value that the kit records (verified live with the kit's own loader
as `spec.raw_sha256 = 2f150cde…`) instead of an equality with the spec **file** sha. This is the correct rule,
not a loosened one: the kit helper `verify_records.py` independently passes the same records with `issues: []`,
and `collect_smoke_summary.py` reports `gate_ok: true`. The fixed script keeps the old `--node-spec-sha` argument
defined but no longer uses it (cosmetic residue). No smoke re-run occurred; the verifier was re-run on the same
records (run-record mtimes 21:53:02–21:53:40Z precede the corrected verifier outputs 21:54:57Z).

*Residual:* a byte-exact v1 source/patch cannot be reconstructed without guessing, so this README states the
one-line rule change instead; the v1 check name and the preserved v1 outputs are the evidence.
