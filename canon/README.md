# canon/ — the short canonical documents

**Only what an agent or a new session must know to act correctly.** Reports, reviews, drafts and records stay under
`docs/`. Authority: `docs/r1/PLAN.md` §10 rows control wherever a file here differs (R1-CANON-FOLDER). The coordinator
updates these files in the same merge as any row that changes them.

| File | Content |
|---|---|
| `PAPER_B_PLAN.md` | Paper B: question, claims, design, state, dates, next actions by owner |
| `PAPER_C_PLAN.md` | Paper C: the same, shorter |
| `COMPUTE.md` | hosts, accounts, file systems, CPU, GPU, memory, limits, known conditions |
| `agents/coordinator/SOUL.md` | the designer and coordinator |
| `agents/local_worker/SOUL.md` | the desk worker on the Mac |
| `agents/cluster/SOUL.md` | deepthought and the ETP HTCondor pool |
| `agents/experiment/SOUL.md` | TASL-2, TASL-7 and Ada |

## Who decides what

The author decides what matters; agents solve execution and engineering questions themselves. This section and the
next were drafted on 26 Nov 2026 at the author's request as row **R1-AUTONOMY**, and are **in force once that row is
on `main`**. Until then levels 0 and 2 describe the practice so far, level 1 covers only what a row pre-authorises,
the author carries the messages, and every push to `main` waits for the author's "推 main".

| Level | Who | What | Where it is recorded |
|---|---|---|---|
| 0 | the agent doing the work | Everything inside its task that changes none of: which evidence is collected or how it is read; a cap or budget; a milestone date; a signed file; another agent's work; anything that cannot be undone. Examples: how the code is written, test design, review rounds until accepted, a retry after an infrastructure failure in a new attempt directory, waiting for a slot or a lease, CPU sets within the rows, read-only diagnostics, merging `main` into its branch | one line in its report ("decided alone: …") |
| 1 | the coordinator | Routing and priorities; splitting and ordering units; publishing a note that a row pre-authorises once its checks pass; settling an engineering disagreement between agents that has no level-2 effect | the task file, or the merge commit |
| 2 | the author | Claims and scope; signatures of preregistrations, pre-declarations and evidence notes; any read of a sealed or test partition; any change to a signed file; a cap raised or a new host or GPU model for a table; a milestone that slips; a STOP that concerns the validity of evidence; deletion; credentials; anything PLAN does not cover | a PLAN §10 row |

When unsure of the level, take the higher one. A level-2 item reaches the author as one decision sheet: the options,
a recommendation, the cost, what it blocks, and the draft row text. An agent that hits a level-2 item keeps working
on everything the item does not block.

## Rules every agent keeps

1. **`main` is published by the coordinator only**, on the author's "推 main" or, once R1-AUTONOMY is signed, for the
   classes that row names. No agent pushes `main`. No force push anywhere. Merges to `main`
   are merge commits (no squash, rebase or cherry-pick), so launch commits keep their hashes.
2. **Nothing is deleted.** A file to remove goes to `_to_delete/`; the author empties it.
3. **Credentials are never read:** `~/.config/r1/secrets.env`, key files, `~/.docker/config.json`, `.docker-config`.
   No `docker login`.
4. **Sealed data stays sealed.** Test labels and evaluation values are read only after their release row. A read by
   mistake is a STOP and is reported at once.
5. **Evidence runs start only from the launch commit a signed note names**, with the note's check passing. No
   assertion is relaxed, no request edited to get a slot, no run resumed into an old directory.
6. **A STOP is a result.** Stop that line, keep the scene, report it. Do not work around it.
7. **Every unit is reviewed by a fresh agent that did not write it**, until the review says "accepted"; code units
   also show the full `r1/tests` suite with zero new failures against their base.
8. **Other users' processes and files are never touched.** Shared hosts keep their limits (`COMPUTE.md`).
9. **Files are written in English. The author is addressed in Chinese, briefly.**

## How work moves

From R1-AUTONOMY on, the repository carries the messages:

- **Tasks.** The coordinator writes one file per task to branch `coord/coordinator`:
  `tasks/<role>/<YYYYMMDD>-<nn>-<slug>.md` (what to do, inputs with commits and hashes, done-when, what to report).
  The same branch carries `STATE.md` (who is on what, what is blocked) and `AUTHOR.md` (what waits on the author).
- **Reports.** Each agent writes one file per finished task or STOP to its own branch (`coord/local`,
  `coord/cluster`, `coord/experiment`): `reports/<YYYYMMDD>-<nn>-<slug>.md` with the task id, the result in five
  lines, each branch and tip, each sha256 that matters, what it decided alone, and what it needs. A report may carry
  `for: <role>`; that role treats it as a task (a direct hand-off).
- **One writer per branch**, so pushes never collide. The `coord/*` branches hold messages only, never code.
- **Rhythm.** An agent looks for new tasks when it finishes one and every 15 minutes while idle. The coordinator
  looks at the report branches at least hourly, verifies and merges what is ready, and writes the next tasks.
- **The author** gets one digest a day in Chinese, and a message at once only when a level-2 item blocks work.

A new session of any role starts by reading this file, its `SOUL.md`, `PAPER_B_PLAN.md`, `COMPUTE.md`, and the PLAN
§10 sections dated after the plan file's "as of" line.
