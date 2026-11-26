# local/20261126-13 — your checkouts: hygiene inventory (runbook order 0; nothing deleted)

Owner: local. Runbook §2 order 0; `docs/r1/reports/REPO_HYGIENE_AUDIT_20261126.md`; `canon/README.md` rule 2. Base: `ef06a65c`.
Lowest priority in your queue. Read-only, except for one report file.

The Mac checkout holds about ninety worktrees under `.claude-worktrees/`, and untracked `.tmp_*` / `.u2_iso_*` directories at
the root. One table: path, branch, tip, whether the tip is merged into `main` or held by a remote branch, dirty files, and a
proposal (keep, or retire with the recovery route: remote branch and tip). Also list the uncommitted edits in the main
checkout (`canon/README.md`, `canon/agents/coordinator/SOUL.md`, `README.md`, the next-phase runbook), with a diff stat.
Remove nothing and stash nothing. The author decides.

Report: the table pushed on a branch (tier D).
