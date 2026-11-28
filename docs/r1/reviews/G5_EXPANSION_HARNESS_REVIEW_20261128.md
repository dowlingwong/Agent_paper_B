# Independent tier-E review of the four G.5 expansion harness pins

Task `local/20261128-14`, harness unit for `compute/20261128-20`. Paper base
`57e6d1ed5945ab48684e24e145b69d333b4f77d4`. A fresh reviewer who did not author the candidates inspected the exact
Git objects and ran the checks below independently of the Local worker's full-suite comparison.

**Verdict: ACCEPTED** for the exact harness candidates to proceed to TASL-2 isolation after the full-suite comparisons
pass. The filled addenda and their launch review are a later unit.

| Node | Signed census kit parent | Reviewed G.5 harness commit | Measurement paths |
|---|---|---|---:|
| Titanic | `3a67042ba7e4211feb9681524f3879643c8cf635` | `d2ce4701faf03f00efaf9c475879acf213411d3b` | 325 |
| MetaMaze | `aa354485bff6b5746c48ddadcb50d92e9c6f3645` | `3f92d3c3fa9a6c41e583bb6075e3f92f8caed685` | 329 |
| ETTh1 | `3a06d86721b0c1826b165b68a9781a561e4993f4` | `6fc553dfb1f8c368023b61c9f5b0b7ac55a0b53c` | 325 |
| Forest Cover | `85851664679d10889c5af406843c4a3fc38f7a49` | `3f7b09febf401a83f3aa881f00eecdd032024416` | 325 |

Each one-commit diff adds `src/autoresearch/trackg/audit_g5.py` and updates `campaign_v2_diff.py` in the same directory.
All six launch-checked engine paths match signed G5-7 `cbf7a0030d73fbc73e2735a6b0e33f25ddf04a98` in Git object,
type and mode. The two changed files have SHA-256 `5f384204c34e297191281bb3981db57607d58333222adab6def97e8d099e2690`
and `9d4f8e6838c31ebec835fd13434532b8afb8539e3cdd913188e52300d0c0a708`, respectively. Titanic retains the
CPU whitelist addition from its census kit. The other candidates' `src/autoresearch` trees match G5-7.

- The actual P5 measurement-path check and G.5 engine-contract check passed at all four pins. The 15-module noise
  measurement import closure is identical to each kit's and contains neither changed file.
- The signed G5-7 synthetic `test_trackg_audit_g5.py` and `test_trackg_diff_recount.py` returned 125 passed and 4
  deselected on G5-7 and, independently, on each candidate. The selection was `-k 'not real_campaign and not test_fuzz'`.
- The actual CPU-only engine wrapper imported each candidate's exact code for both the campaign and audit entry
  points. All eight checks applied only the declared node allowance, saw no GPU or scheduler state and wrote a
  structured refusal for deliberately malformed input before running a worker.
- The actual host-record checker accepted the four published TASL-2 records at their own census pins and refused
  them at the new pins on `host_check_harness_commit`. Compute must produce reviewed records covering items 1–7
  at the exact new pins. The desk review used published engineering metadata and synthetic fixtures.
- The reviewer verified the census CPU placements, environments, P10 and S9 routing. Titanic is 12–15 with
  `torch312`, Gaussian, main T1. MetaMaze is 0–3 with `venv_jax`, Student-t ν = 5, main T1. ETTh1 is 16–31 with
  `torch312`, Gaussian, separate output. Forest Cover is 4–7 with `torch312`, Gaussian, separate output.
