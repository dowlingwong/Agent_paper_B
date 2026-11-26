# coord/coordinator — tasks and state (messages only)

Rules: `canon/README.md` on `main` ("How work moves", R1-AUTONOMY). One writer: the session named in `COORDINATOR`.

- `tasks/<role>/<YYYYMMDD>-<nn>-<slug>.md`: one file per task, oldest first. A task file is not edited after an agent
  has started it; a change is a new file that names the one it replaces.
- `STATE.md`: who is on what, what is blocked.
- `AUTHOR.md`: what waits on the author.

Roles on `main` (since `95249de3`, R1-AGENT-COMPUTE): `compute` (replaces `cluster` and `experiment`), `local`, `writer`, and
`design` (added to `canon/` on 26 Nov without a PLAN row).
- `sheets/`: decision sheets for the author, written by the coordinator.
**Start with `STATE.md`; `HANDOVER.md` is the interim coordinator's view of 26 Nov 20:30Z.**

Agents report on their own branch `coord/<role>` under `reports/`, one file per finished task or STOP:
task id, result in five lines, each branch and tip, each sha256 that matters, "decided alone: …", what is needed next.
