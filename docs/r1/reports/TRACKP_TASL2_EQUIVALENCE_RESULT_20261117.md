# Track P host-equivalence check on TASL-2 — RESULT: EQUIVALENT (17 November 2026)

**Status: PASSED — `equivalent: true`.** Authority `R1-TRACKP-TASL2-HOST`
(`author-decisions-20261117b` @ `45fb94cc`), `R1-TASL7-TRACKP`, `R1-TASL2-REHEARSAL-SCOPE`; unit rev 4
accepted by R4 review (`reviews/TRACKP_TASL2_EQUIVALENCE_REVIEW_R4_20261117.md`, sha `e0c65063…`;
0 BLOCKING/MAJOR). ENGINEERING, not evidence; **TASL-2 is the portal host**, so this is a same-host
reproduction of the reference, not a cross-host claim with TASL-7. Not a test of code D (D delivery is
separate).

## Run

- Clean reference-code worktree `Agent_paper_B_8e13e77` at **`8e13e77cd495…`** (clean), harness worktree
  `autoresearch_harness_897d83c` at **`897d83c8efa3…`** (clean), frozen venv (freeze 121 lines
  `50238e5a…`, torch 2.6.0+cu124), config file `10ead2a5…` / loaded `config_sha256 **588869fa…**` (the
  portal reference/TASL-7 digest), e0 = 2,000 steps / eval 100 / patience 5 / batch 8 / seed 0.
- Command: `python r1/scripts/trackp.py e0 --base kev-0.8b --evidence DRYRUN --variant fresh --lr 0.0001
  --run-dir …/ENGINEERING_equivalence_20261117T022235Z/kev-0.8b/fresh_soft_lr0.0001`; env protected
  (`PYTHONDONTWRITEBYTECODE=1 GIT_OPTIONAL_LOCKS=0 HF_HUB_OFFLINE=1`, `AR_HARNESS_ROOT`).
- rc 0, **wall 1,474 s (24.6 min)**; report sha `5cfc014f…`, manifest sha `eee2a20e…`;
  `manifest.evidence_label=DRYRUN`, `config_sha256=588869fa…`, `gpu_lease` two entries; report
  `max_steps=2000`, `patience=5`, `protocol` as reference.
- Comparison (`compare.py` sha `bd957c0d…`, reference report sha `7c1be5e9…`), exit 0:

| Metric | Portal | TASL-2 | Δ / rel | Tolerance | Pass |
|---|---|---|---|---|---|
| `width_slope_vs_label` | 0.922998 | 0.936691 | +0.013693 | 0.05 | yes |
| `mean_slope` | 1.011556 | 1.016713 | +0.005158 | 0.05 | yes |
| `rps` | 1.98913e-4 | 1.81196e-4 | 8.91 % | 10 % | yes |

- Captures under `reports/tasl2_equivalence_20261117/` (`SHA256SUMS`; comparison sha `2a6e1990…`).
- Side effects as pre-declared: lease log **191 → 193 lines** (sha `0a4a14ae…` → `edc8247b…`; two
  `start`/`end` lines, no `acquired`); the `8e13e77` worktree gitdir `FETCH_HEAD` was created
  (**104 B / `83c64a87…`**), the main clone `.git/FETCH_HEAD` untouched (`17,593 B / 69545606…`); tracked
  tree clean, `.pyc` 65 → 65, worktrees unchanged, GPU back to idle, lease released; no marker/evidence;
  no TASL-7 action.

## Disposition

The TASL-2 host/reference reproduction is equivalent. D `8662e359` was then delivered to a clean TASL-2
checkout (`delivery_D_20261117`: HEAD D, clean, runner `c045475b…`, child `d2a30ec2…`, `b9ad6f8f`
ancestor). **Unit B on TASL-2 is blocked by a separate, real gap:** its `--load` targets attempt-1
`EVIDENCE/<base>/final/saved`, which is a TASL-7 artifact and is **ABSENT on TASL-2** (`…/qwen3.5-4b-base/
final/saved` missing; no attempt-1 root anywhere on TASL-2). Unit B must not be run there without those
inputs or an author-approved route; TASL-7 remains unreachable. No evidence run was attempted.
