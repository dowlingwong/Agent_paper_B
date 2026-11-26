# Paper B path map

The local layout preview starts at main commit `4cb92b70`. Its first commit moves files with
their original Git blob IDs and modes. The second commit updates the navigation links used to
browse the preview.

| Previous path | Preview path |
|---|---|
| `docs/r1/` | `docs/` |
| `papers/r1/` | `papers/` |
| `results/r1/` | `results/` |
| `tests/r1/` | `tests/` |
| `tools/r1/` | `tools/` |
| `r1/` | `paperb/` (proposed Python package name) |

Keep historical manifest and authorization paths as recorded. For a historical commit, read the
path against the cited commit. Use this table to locate the corresponding file in the preview.

Before switching main, resolve the local checkout collisions and verify the live authorization
lookups, harness pin, Python import and CLI compatibility, and test parity. The R1-LAYOUT-FLATTEN
decision in PLAN §10 records the coordinated cutover.
