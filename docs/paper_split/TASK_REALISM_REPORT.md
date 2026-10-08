# Task-realism report — F9 (run on CPU, before any Ada time)

Task: `experiments/paper_b/task_cc_live/` (F8).  Runner:
`cc_live_realism.py`.  Scripted agent behaviours of varied quality — careless,
typical, careful — drive the task; no leaf value is hand-set.  Thresholds in
`THRESHOLDS` were frozen before the run.

**Verdict: FAIL (repaired once).**  R1 and R4 fail for the *typical* behaviour.
Per the fix queue this stops F10 and is a legitimate outcome.  It is **not**
tuned further.

## Frozen thresholds (before the run)

| # | Check | Pass rule |
|---|---|---|
| R1 | Decision room | each of now-best, later-best, never-best best in ≥1 family per behaviour |
| R2 | Context-dependent waiting value | between-family SD of (later−never) > 0.02 |
| R3 | Checkpoint-2 information legitimately new | disjoint splits; hidden not in workspace |
| R4 | Verifier not redundant | verify beats ordinary refit by > 0.02 U in ≥1 mechanism class |
| R5 | Harm possible | ≥1 family where verification lowers U |
| R6 | U has spread | baseline mean in [0.2, 0.8] and root SD > 0.05 (typical) |
| R7 | Reachability | checkpoint 2 reached in 50–90%; early termination < 50% |
| R8 | Cost fits the cap | 512 leaves × ~1,350 tokens ≤ 2M; 512 × 12 s ≤ 10 h |
| R9 | Old failure mode cannot recur | fit tool returns the executable candidate; submission is a round-trip |

## Run 1 (pre-repair)

The original target (`target == target[0]`) was trivially solvable; careless used
`verifier=False`, so now ≡ never and never-best was structurally impossible.

| Behaviour | regimes (now/later/never best) | reach | harm | verify gain max | wait SD | baseline mean | root SD |
|---|---|---|---|---|---|---|---|
| careless | 6 / 2 / 0 | 0.75 | yes | +0.02 | 0.063 | 0.833 | 0.098 |
| typical | 2 / 4 / 2 | 0.75 | yes | +0.12 | 0.133 | 0.888 | 0.070 |
| careful | 3 / 3 / 2 | 0.75 | yes | +0.00 | 0.065 | 0.910 | 0.033 |

Checks: R1 **FAIL**, R6 **FAIL**; all others pass.

## Repair pass (one, recorded)

In `cc_live_generator.generate_family`: a balanced, harder derived target (a
fixed random linear separator at its median) with 20 % label noise, so the task
is not trivially solvable.  In `cc_live_realism.BEHAVIOURS`: careless keeps a
restricted fit but invokes the verifier (`feature_indices='first'`,
`max_candidates=2`), so now can differ from never.

## Run 2 (post-repair)

| Behaviour | regimes (now/later/never best) | reach | harm | verify gain max | wait SD | baseline mean | root SD |
|---|---|---|---|---|---|---|---|
| careless | 3 / 3 / 2 | 0.75 | yes | +0.04 | 0.136 | 0.540 | 0.070 |
| typical | **0** / 5 / 3 | 0.75 | yes | **−0.04** | 0.112 | 0.578 | 0.087 |
| careful | 2 / 3 / 3 | 0.75 | yes | +0.10 | 0.070 | 0.598 | 0.110 |

Checks: **R1 FAIL** (typical has no now-best family), **R4 FAIL** (typical's
verifier never beats ordinary refit by > 0.02; its best is −0.04, i.e. it can
harm).  R2, R3, R5, R6, R7, R8, R9 pass.

## Interpretation

- The task is now non-trivial (baseline U ≈ 0.54–0.60), has spread, harm, real
  reachability and a fine cost envelope.
- The realism failure is concentrated in the *typical* behaviour: for a
  competent fit, the verifier does not reliably add value over ordinary refit
  and verification is never the best checkpoint-1 choice.  That is a genuine
  signal about the task/verifier pair, not a tuning artefact.
- No further tuning is permitted by the queue.  F10 (Ada tooling) is **stopped**
  and reported; F11–F13 proceed as they do not depend on F10.
