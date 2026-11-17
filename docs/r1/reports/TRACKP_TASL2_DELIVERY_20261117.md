# Track P code D delivery to TASL-2 — done; Unit B input gap (17 November 2026)

**Authority:** `R1-TRACKP-TASL2-HOST` (`author-decisions-20261117b` @ `45fb94cc`). ENGINEERING; no
evidence run.

## Delivery

- Clean checkout `/home/dowling/r1_engineering/unitb_rehearsal_20261117/delivery_D_20261117` (git worktree
  from the TASL-2 clone) at **`8662e35991659f7a661fb7ed6be4980791d302f3`** (D), detached, **clean**
  (`git status --porcelain -uall` empty).
- Runner `r1/scripts/trackp_p3a_guarded.py` sha `c045475b…`; child `r1/scripts/trackp.py` sha
  `d2a30ec2…`; `b9ad6f8f` is an ancestor; branch not merged into `main`/`trackp-20261026`.
- No GPU job, no evidence root, no marker, no deletion; the rehearsal/equivalence scratch roots are
  separate and never counted.

## Unit B input gap (real STOP for Unit B on TASL-2)

`trackp_p3a_guarded.py --probes-only` loads attempt-1 `EVIDENCE/<base>/final/saved` for both the DRYRUN
(`kev-0.8b`) and the EVIDENCE (`qwen3.5-4b-base`) units. Those are TASL-7 attempt-1 artifacts
(`/home/dowling/r1_trackp/runs/p3a_operator_20261027/...` on TASL-7). On TASL-2:
`…/EVIDENCE/qwen3.5-4b-base/final/saved` is **ABSENT**, no `p3a_operator_20261027` root exists, and only
the unrelated `p4`/`p5` scratch outputs are present. TASL-7 is unreachable, so the inputs cannot be copied
now. Running Unit B without `--load` would evaluate untrained bases and is **not** the authorized evidence
run — not done.

**Needed:** either (a) TASL-7 comes back and the attempt-1 `EVIDENCE/<base>/final/saved` directories (and
their manifest hashes) are copied to TASL-2 under the authorized delivery route, or (b) the author approves
a different route for the attempt-1 inputs. Until then Unit B on TASL-2 is STOPPED (not a defect of D or of
the rehearsal/equivalence checks, both of which passed).
