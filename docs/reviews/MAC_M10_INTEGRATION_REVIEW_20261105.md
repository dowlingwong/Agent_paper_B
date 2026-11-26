# M10 integration review — 5 November 2026

Independent fresh reviewer, AI-assisted (Codex). Verdict: **ACCEPTED for the staged code/document integration and local mock tests**, not for live site behavior or a new job authorization. This is a review of the staged integration on the Mac coordinator's independent clone, against its parent `f4024358dbf121ab82b0970ed2775dafb7ead36c`, and `eba5f03` (the accepted M10 code/review head). No server, GPU, model, real Slurm command or real scheduler was used.

## Scope and identity

The staged index tree at inspection was `399c100268a525df31f7d5ff16cb271b01370ad6`; all staged paths listed below were additions, with bytes identical to `eba5f03` at the same path. `docs/r1/PLAN.md` was outside the staged diff and its checkout SHA-256 was `2d6cc9c611597f38734b71396fca685adb9681087af5d589fa343e4ac728d425`. Any changed staged file or PLAN after this snapshot requires rechecking the relevant changed bytes.

| Path | SHA-256 |
|---|---|
| `docs/r1/proposals/HK2_GUARD_DESIGN_20261104.md` | `1f2c961f41fffccbceb15bdd75ea844d99665fc403900764729ef6e7b89f95b9` |
| `docs/r1/reviews/MAC_M10_OVERNIGHT_REVIEW_20261105.md` | `0e057749b1654fcf88da0d3c24a3cc0a236ef981d8c631b59d89653fa47c89eb` |
| `r1/scripts/hk2/hk2_bundle_preview.py` | `7c090bff947c7af760850088c8af3ad49a8bb61b53441bae377f59d96560df97` |
| `r1/scripts/hk2/hk2_common.py` | `9cb4bd855c1d58e854f5972ecbe720f6a8c2d27eef81497eac9ff2edcd7b0328` |
| `r1/scripts/hk2/hk2_config.json` | `028508f3b5697b69de2fc7a1288b6d3437c2ecb33c66a4b2617be348ac737f0a` |
| `r1/scripts/hk2/hk2_status.py` | `f56706ed19ebf1210fc5231e554721560736599cfe63523fc192596e47d4b923` |
| `r1/scripts/hk2/hk2_submit.py` | `1da94a56316a914ecb3f41e9b122125208d210fad7ad268ec9b2ec07cf7dba1c` |
| `r1/tests/hk2/test_bundle_preview.py` | `e7a5628cf6e341fd4b18558d36522758dbcdf7b81df36993c866f8480b2dc77d` |
| `r1/tests/hk2/test_hk2_tools.py` | `fe0fe577c0d64e695513f6223b90493e716e8303f11e30b8aeff4e23b918edc3` |

No tracked file outside these paths was staged at inspection. The previously accepted code patch remains byte-identical; integration does not silently pick up a different worker revision.

## Checks

- Both actual dated PLAN §10 rows are present, nonempty, and accepted by the integrated parser: `R1-HOREKA-AGENT-SUBMIT` and `R1-HOREKA-UNIFIED-SUBMISSION`. The prior standalone branch's stale PLAN is not used in this integrated tree. This verifies the parser against these committed local PLAN bytes, not the authenticity of an independent host checkout or any live site access.
- The shipped config has one `real_submission_enabled` value, `false`. The enabled branch is covered only by fake-scheduler tests; the setting has not been changed here. The code retains separate evidence-phase restrictions, as the accepted unit review explicitly states.
- F, C and D remain proposed config values; the common loader checks their order. The status helper reports D time state, not proof that copy-back did or did not occur. It does not itself copy results.
- On a separate local review clone, `/usr/bin/python3` 3.9.6 ran `PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest discover -s r1/tests/hk2 -v`: **33 passed**, all scheduler interactions mocked. The staged diff passed `git diff --cached --check`.

## Limits and HK1

This acceptance does not enable the switch or prove the real site's field formats, accounting delay, PrivateData visibility, or shared-lock behavior. At HK1 the authorized agent must verify those facts and coordinate other submission routes; a project-scoped procedure does not technically control unrelated user tools. The reconciler cannot establish that an unobserved, not-yet-accounted unrelated job does not exist. A reviewed manifest's declared kind/phase is not automatic semantic proof of its argv. Evidence submissions remain separately refused until their required authorization gate exists. These are the same explicit limits of the accepted unit and must not be represented as a successful production or EVIDENCE run.
