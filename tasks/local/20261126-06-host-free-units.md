**NOT IN FORCE until the rows of 26 Nov (f) and (g) are on `main`** (they are drafts on branch `coordinator-rows-fg-20261126`; see `HANDOVER.md` §4.1).

# local/20261126-06 — units for R1-HOST-FREE (first after local/20261126-01)

1. **P.4 off HTCondor** (unblocks the SFT; the pool has no batch GPU): a direct-launch path beside the HTCondor one,
   same job logic, started over SSH under a GPU lease; a host configuration for a 48 GB sm_89 card (Ada), filled by
   the fill hook from the compute agent's survey; the env3 freeze check unchanged; the charge files count
   GPU-hours on any card. Revise the phase-1 note draft to R1-HOST-FREE (the GPU model is recorded, not fixed; one
   arm's training run stays on one card). Tier E.
2. **G.5 audit hosts beyond the TASL pair:** generalise `tasl7_audits` to a list of audit hosts, each admitted per
   node by a short cross-check PASS against the sealed TASL-2 attempt (as xc3), a host check, and the lease of that
   host; the spec for the short cross-check on Ada for the eight nodes; an addendum note to the G.5 note. The G.5
   note itself is signed as drafted (revision 13) so that G.5 starts on the TASL pair now.
3. **D.3 pre-declaration revision 4** (local/20261126-03) follows R1-HOST-FREE (2)(c): one GPU model per instance
   across its arms, not one GPU model for the whole of D.3.

Done when: each unit's branch is pushed with review verdict and suite counts; unit 1 first.
