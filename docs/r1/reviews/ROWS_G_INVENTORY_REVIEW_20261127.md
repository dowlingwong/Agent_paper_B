# Review: rows (g) inventory and the G.5 shared-card monitor proposal (local/20261126-07)

- **Reviewer:** an independent tier-E reviewer (Claude subagent, AI-assisted) who did not write the unit. It modified nothing and read no credential, label, test or evaluation file.
- **Transcription:** the author of the unit transcribed this record from the reviewer's two hand-backs.
- **Object:** `docs/r1/reports/rows_g_20261127/ROWS_G_INVENTORY_20261127.md` on `mac-rows-g-inventory-20261127`.
  - Round 1: `94c79935`.
  - Re-check: `55ee5e46`.

## Round 1 (94c79935): NOT ACCEPTED

The inventory (item 1) was accurate and complete within the card's scope. About 25 file:line citations were spot-checked on `main`, and all were correct.

### Blocking findings

**B1.** Reading STOP 9, STOP 8 or the wave timing STOP as infrastructure "with the code the same" cannot work.
- `node_stopped` (`g5_job.py:671-685`), `check_order` (`:753-755`) and the TASL-7 claim checks (`:980-982`, `:1024-1026`) halt on any `node` or `timing` record.
- `g5_assemble._one_attempt` (`:283-285`) refuses such an attempt.
- So reclassification needs a reviewed code unit (tier E).

**B2.** A monitor file "sealed with the attempt" cannot work.
- The seal copies only `ATTEMPT_FILES` and `node.log` (`g5_seal.py:88`, `:333-342`).
- TASL-7 registration refuses foreign files (`g5_job.py:881`, `:1098-1101`).
- So the monitor must run per card, outside the job scopes and the attempt trees, with receipted segments.

### Minor findings

- **M1:** the after-engine check already makes a foreign process present at the end an infrastructure failure. Name the two uncovered cases.
- **M2:** the bias safeguards should be fixed in the row now: a metric-blind list, published first, every match repeated, unconditional replacement, a campaign repeated as its whole wave job, a gap rule, an attempt-window fallback, and disclosure.
- **M3:** the row should name the code unit and its tier.
- **M4:** define "our PIDs" by cgroup.
- **M5:** say how CPU-only nodes are treated.
- **M6:** row 5's one-run-per-day is a date gating a retry.
- **M7:** row 17's 86,400 s bounds the training call, so it is not a helper guard.
- **M8:** give row 13 an owner.
- **M9:** state the tiers.

### Nits

- **N1:** class R is undefined.
- **N2:** row 2 should have one class.
- **N3:** name the branch commit.
- **N4:** row 21 is arguably a helper guard.

### Bias analysis

Repeating only failures (budget, OOM) is unbiased for the empty-card outcome when the trigger is external and the rule is fixed in advance. M2 closes the remaining routes: case-by-case scope, step splicing, metric-visible reading, and an unruled monitor gap.

## Re-check (55ee5e46): ACCEPTED

- **B1 resolved:** one tier-E repeat-list unit honours a published reclassification list, and the originals are untouched. "Launches as it stands" is now limited to starting and to the run budget.
- **B2 resolved:** the monitor runs per card in its own scope and directory, with receipted segments matched to attempts by record times.
- **M1–M9 and N1, N2, N4:** addressed.

**N5 (open, for the unit's own review):** the wave timing STOP is also written to `wave_checks_wave*.json`, which `node_stopped` scans (`g5_job.py:681-684`). The list format must also be able to name a wave-checks entry by node and wave.

Verdict: ACCEPTED
