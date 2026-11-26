# Report — D.3 launcher design revision (`compute/20261126-02`)

**Result: PASS.** The short design revision for one chunk script with HTCondor or direct SSH launchers is
**ACCEPTED FOR CODE** by an independent review. No code was written in this task; G1/G6 implementation is
`cluster/20261126-02`, the next ready unit.

- **Branch:** `compute-d3-launcher-design-20261126`
- **Tip:** `459398f2c0d729055c75e7db02e8bb723f980195`
- **Revision:** `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_REV6_LAUNCHERS_20261126.md` (revision 6b)
  sha256 `0d696535d94395c85592c7ac9483790483966bbe0bf48961d132c50aa49b922d`
- **Final review:** `docs/r1/reviews/D3_G1_G6_LAUNCHER_REV6B_REVIEW_20261127.md` sha256
  `2022536288ff1fc792b9982f62ca083cec3cc89f8244c49020e3ad08e06e2755` — `ACCEPTED FOR CODE`
- **First review:** `docs/r1/reviews/D3_G1_G6_LAUNCHER_REV6_REVIEW_20261126.md` — `CHANGES REQUIRED` (4 MAJOR, 14
  MINOR). Revision 6b answers them; the first review is committed on the branch for the chain.

## What the revision settles

- **One script, two launchers.** `campaign_chunk.py` owns all chunk logic; HTCondor and the direct SSH launcher
  invoke the same script with the same `launch.json`/argv. Only `launcher`, `request`/`scope` and `lease_path`
  differ, and each launcher emits the inapplicable field as `null`. The launcher is recorded
  (`htcondor`/`ssh`/`direct`). No scheduler request is edited to get a slot.
- **Independent model source.** The model check is against `campaign_model_source` (the reviewed note/PD pin, or
  the campaign spec before the note) and a locked `campaign_manifest.json` with a per-instance `instance_model`
  and the campaign's `proposer_model`. The chunk does not self-declare its model. The record carries
  `stage`/`arm`/`instance_id`/`repetition`, expected/observed proposer model, host, model, UUID, driver, memory,
  required memory, memory check, environment freeze and start/end process counts.
- **Refusals.** The GPU **model identifier only** is compared with the declared model; a second host with the
  same model, another UUID or driver is allowed and disclosed. All arms of one instance share the manifest's
  `instance_model`; the campaign's proposer model is fixed. A mismatch is a placement refusal (wait/re-place);
  a campaign already moved off its declared model is a campaign-level STOP. A lease held by another of our jobs is
  waited out; foreign processes may share when memory fits (R1-CARD-SHARE). The lease is per card used, not a
  fixed `gpu0.lock` on a multi-GPU host.
- **Wall time.** The accepted design's `chunk walltime` STOP is explicitly **withdrawn** under R1-NO-TIMEOUT; the
  smoke's measured time and 1.5× are descriptive planning values. A slow shared-card attempt is an
  infrastructure failure, sealed and repeated, never a STOP or an outcome. No wall-clock value decides a result.
- **"Both stages".** D5b:13's "one GPU model for both stages" is explicitly replaced by R1-HOST-FREE (2)(c) and
  the paired-comparison rule: D.3a and D.3b for one instance use one `instance_model`; an arm's campaign keeps its
  proposer model for its whole life.
- **G6.** CPU-only on deepthought after campaign seal, 16 workers and ≥10 of 40 cores free, `direct` or HTCondor
  CPU launcher; a direct process is attempt-recorded and sealed like a job; no TASL-style CPU lock is invented on
  deepthought.

## Review

The first review found no BLOCKING and four MAJORs: the composite model/uuid/driver refusal; the self-referential
model source and missing identity/proposer fields; the shared-card walltime conflict; and the unamended "both
stages" sentence. Revision 6b separates the model identifier from UUID/driver, anchors the check to the
note/PD pin plus a locked campaign manifest, withdraws the walltime STOP with the 1.5× made descriptive, and
replaces the "both stages" sentence. The second review finds **no BLOCKING and no MAJOR**, all M1–M4 answered, all
prior MINORs closed or explicitly unit-level, with four wording/schema notes left for the G1/G6 unit (intro wording
on the walltime withdrawal, tying `campaign_model` to `instance_model`, the breadth of "no wall-clock value decides
a result" versus the preserved per-run budget, and the manifest's proposer key scope). None is a design blocker.

## Tests

Design-only: no code, no test, no GPU job, no campaign/audit/evidence run. The branch adds the revision and the two
review records; `git diff --stat origin/main` is documentation only.

## What happens next

`cluster/20261126-02` (G1/G6 code) is the next ready unit: two tier-E branches from current `main`, tests with each
unit, the full `r1/tests` suite on base and tip with zero new failures (listed by test id), a fresh independent
review each, CPU-only ENGINEERING dry runs only. The design's constants that the pre-declaration fixes are read
from a constant with the source named; the D.3 pre-declaration revision 4 and the per-arm smoke remain the local
worker's / later dependencies. The four expansion G.1b jobs continue running; they do not block the code.
