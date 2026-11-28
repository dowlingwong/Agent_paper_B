# Paper B Local round close — 28 November 2026

for: coordinator

Latest published main `474c998d32552f67766fd8250d1de86c6b4555ce`, queue
`2076c0a755ad536caeb34359803bc764842f0c6d`, Compute reports
`d43b2d82a3967761e6b8322eb6434fdb4cfc399e` and Writer reports
`3f46a838867db592b5386144aca81be5470fd18b`. Local has no further runnable card after the three handoffs.

| Task | Delivery | Review and next step |
|---|---|---|
| `local/20261128-04` | `local-20261128-04-d3-step8` @ `ad6e5f18faeca24f4e82b9bacc85cfbfb1bd2e5b` | Tier-E re-check **ACCEPTED**, published by the coordinator at `474c998d`. D.3 smoke and campaigns follow their own cards. [Tests, bindings and hashes](20261128-04-d3-step8.md) |
| `local/20261128-05` | `local-20261128-05-addenda-p10` @ `4299fd66174429f11cf7f1937db5e78434fa3be4` | Tier-E re-check **ACCEPTED**. Coordinator publishes the P10 unit and routes each final addendum after the main G.5 note. [Tests and four draft hashes](20261128-05-addenda-p10-fill.md) |
| `local/20261128-02` follow-up from `compute/20261128-09` | `local-20261128-p11-host-repair` @ `2f110e269819ed20e85fe6566d1fedc3367ba7ed` | Tier-E **ACCEPTED**. Coordinator publishes and reissues the engineering matrix. Compute checks leases and uses fresh IDs. [Tests, hashes and Compute handoff](20261128-p11-host-repair.md) |

## Dependencies and jobs to check next round

- **Houseprice S14 complete.** `tasl2-cpuset-mlgym_houseprice-20261128` passed with three bit-identical seals
  on CPUs 0–7. The three maxima of 3.810, 3.858 and 3.848 s satisfy 9.486 s. The accepted result is published.
  The reviewed rerun command remains in the [Compute handoff](20261127-27-houseprice-two-attempts.md#compute-handoff).
- **G.5 base render pending.** `local/20261126-08` needs the rerun of `compute/20261128-09` and its independently
  reviewed P11 record, then the final `paper.commit`, strict checks and fresh tier-E review. The first matrix's
  `g5-p11-20261128T014000Z` scenarios stopped on the fixture and CLI defects. Keep those scenes and check the
  Compute ledger for fresh IDs, leases and receipts after repair publication. Final expansion checks also need
  the published G.5 note and each addendum's complete launch, harness and host bindings.
- **Rows (g) and audit expansion pending.** The accepted inventory is on `mac-rows-g-inventory-20261127`
  @ `c2c04079d13e3259a1cfe4b97f96d811644fcf3e`. The accepted proposal puts its monitor and repeat-list
  implementation after the owner's `R1-G5-SHARED-REPEAT` decision, with the original recorded STOPs retained.
  `local/20261126-06` unit 2 stays parked for placement and binding disposition.
- **P.4 E0 repeats complete.** Ada `p5_e0_rep_20261128_ada/e0e` (last recorded PID `3548655`) and
  TASL-7 `p5_e0_rep_20261128_tasl7/e0e` (last recorded PID `2431912`) are complete and their leases ended.
  The accepted record on main `989e8f22` reports within-host RPS changes of +9.66% on Ada and +26.13% on
  TASL-7 against the existing 10% tolerance. TASL-7's within-host result fails the criterion. P.4 phase 1 and
  A5 SFT await the author/coordinator disposition under R1-P4-E0-REPEATABILITY, timing and a published note.
- **D.3 HTCondor blocked.** The latest published start check, `914e1cf9`, recorded TOpAS A100 `c03-001-175`
  and ETP L40S at `Start=false`. No new job was submitted. Compute should check actual eligibility before retrying.
  Earlier unmatched requests `760148`, `760149`, `760152` are removed. `759624` and `759625` were removed
  after the Idle check and H200 request `760065` was withdrawn. The accepted screening run is complete.
- **Compute idle in the last report.** `coord/compute` at `d43b2d82` records no active Paper B job, free TASL
  leases and idle Ada card 0 and deepthought2. HTCondor `760158.0` is an R2 job and is running elsewhere.
- **Writer idle and Paper C waiting.** The writer awaits an assigned result-table card and released evidence.
  Paper C CPU measurements await operator pins and authorization. `compute/20261127-28` E-INT awaits its
  bound Ada lease and smoke receipt under R1-PAPERC-EINT-CENSUS. Check the new Compute report for IDs.
  The Paper B gate awaits the G.5 release and arms freeze.

Decided alone to keep the assigned linked worktree's pre-existing bytes in place. Twelve of the sixteen
pre-existing changed paths match the published base. The four others match the earlier published expansion
binding at `1afa7d62` and precede the published P11 changes. The shared Git metadata refused writes, so
the fetch, task branches and role report used the writable nested worktrees inside the assignment.
Local submitted zero host jobs.
