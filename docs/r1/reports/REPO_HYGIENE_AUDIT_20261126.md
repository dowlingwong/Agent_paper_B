# Repository hygiene audit — 26 Nov 2026

Snapshot from the full remote branch graph at published main
`53b72f1ddd63eeb83dbc269124d811370e8f9e24`. The audit used commit ancestry, tags, current canonical references
and the coordinator branch's state, author sheet and task files. The
[branch inventory](repo_hygiene_20261126/branch_inventory.tsv) records the exact tip, tip date, tag at the tip
and disposition for each remote branch.

## Findings and changes

| Item | Finding or action |
|---|---|
| Remote refs | 203 branch heads. 155 tips are reachable from published main. The first pass retains 50 protected or currently cited branches and 39 other unmerged branches. The remaining 114 merged branches are retirement candidates for owner and reference review. |
| Paper C | Retain the active E-SYN line and the two divergent theory/RL branches until consolidation and comparison. A stale date alone cannot show that their work is redundant. |
| Worktrees | Removed one clean, detached patch-check worktree owned by this session after checking its HEAD and confirming it held no modified, untracked or ignored files. The other local review worktrees contain deliverables. No inventory from the Mac or compute hosts was obtained. |
| Scratch files | The reviewed source tree has no files matching the checked Paper B LaTeX build products or common `.bak`, `.swp` and `.tmp` patterns. Some large JSON and provenance files have historical or runtime roles. Treat them as inputs until their consumers and hashes are mapped. |
| Archive | Indexed the 1,677 tracked paths under the pre-R1 archive and kept their stable paths. The root `make legacy-test` enters the archived code tree. |
| Recovery | The 11 paths under `_to_delete/c3-recovery-source-data-20261031` are referenced by the recovery manifest. Their current directory name does not make them disposable. |
| Repository entry points | Updated the root README, added the docs and archive indexes, and linked the next-phase runbook and role files from canon. |

The candidate list is conservative and incomplete for retirement. It did not check every historical signed launch,
external harness pin, open review or another operator's worktree. A branch tip being reachable from main covers
its commits. A branch name can still be needed by a run note, job or checkout.

## Retirement handoff

1. The coordinator asks each checkout owner for `git worktree list --porcelain`, a status check of candidate
   worktrees, and any running job or task tied to the ref. The coordinator checks current and signed notes,
   open work, and external pins against the inventory.
2. For each remaining ref, record its exact tip, protection checks and recovery route. Use a reachable published
   commit or the established archive tag or bundle convention in [BRANCHES.md](../BRANCHES.md). Verify recoverability
   from a fresh checkout. A displaced unmerged tip needs its own verified recovery ref.
3. Present the exact retirement set to the author under the repository's deletion rule. Re-fetch and compare
   each tip with the approved SHA immediately before retiring it. A moved ref returns to review.
4. For temporary local files, the owner verifies that the producer can recreate them and that no job, manifest or
   worktree needs them. Remove clean disposable worktrees using Git's worktree command. Keep any dirty worktree
   or unpublished output for its owner to resolve.
5. For a future move of historical content, migrate the references, validate legacy/recovery consumers and record
   the old-to-new path before review. This audit found active path dependencies in both historical folders.

Remote branch retirement and deletion of archived contents require that owner/ref review. No remote ref or
tracked evidence file was removed in this pass.
