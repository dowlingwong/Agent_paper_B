# canon/ — the short canonical documents

**Only what an agent or a new session must know to act correctly.** Reports, reviews, drafts and records stay under
`docs/`. Authority: `docs/r1/PLAN.md` §10 rows control wherever a file here differs (R1-CANON-FOLDER). The coordinator
updates these files in the same merge as any row that changes them.

| File | Content |
|---|---|
| `PAPER_B_PLAN.md` | Paper B: question, claims, design, state, order of steps, next actions by owner |
| `PAPER_C_PLAN.md` | Paper C: the same, shorter |
| `COMPUTE.md` | hosts, accounts, file systems, CPU, GPU, memory, limits, known conditions |
| `agents/coordinator/SOUL.md` | the coordinator: watches, verifies, merges, hands out tasks |
| [`agents/design/SOUL.md`](agents/design/SOUL.md) | research questions, experimental contrasts, resource/cost design and runbook handoffs |
| `agents/writer/SOUL.md` | manuscript, figures, paper build and review responses |
| `agents/local_worker/SOUL.md` | the desk worker on the Mac |
| `agents/compute/SOUL.md` | the compute agent: every server; finds free resources and runs the work there |

The [documentation index](../docs/r1/README.md) locates experimental records and signed notes. The
[next-phase runbook](../docs/r1/runbooks/AUTOML_AS_DAC_NEXT_PHASE_20261126.md) gives the work order.
Paper B LaTeX lives in [paper_B_manuscript](https://github.com/dowlingwong/paper_B_manuscript) (R1-MANUSCRIPT-REPO). Writer delivery reports
on `coord/writer` name the manuscript repository, branch and commit.

## Who decides what

The author approves each research stage in one decision. Agents handle engineering and execution under
R1-AUTONOMY and R1-STAGE-APPROVAL.

| Level | Who | What | Where it is recorded |
|---|---|---|---|
| 0 | the agent doing the work | Everything inside its task that changes none of: which evidence is collected or how it is read; a cap or budget; a signed file; another agent's work; anything that cannot be undone. Examples: how the code is written, test design, review rounds until accepted, a retry after an infrastructure failure in a new attempt directory, waiting for a slot or a lease, CPU sets within the rows, read-only diagnostics, merging `main` into its branch | one line in its report ("decided alone: …") |
| 1 | the coordinator | Routing and priorities; splitting and ordering units; publishing a note that a row pre-authorises once its checks pass; merging reviewed units to `main` under R1-AUTONOMY (3); adopting a reviewed recommendation that is not level 2, as a row marked "(coordinating chat, under R1-AUTONOMY)"; settling an engineering disagreement between agents | the task file, the merge commit, or the coordinator row |
| 2 | the author | Claims and scope; signatures of preregistrations, pre-declarations and evidence notes; any read of a sealed or test partition; any change to a signed file; a cap raised or a change to what R1-HOST-FREE keeps bound; a blocked step that requires an author decision; a STOP that concerns the validity of evidence; deletion; credentials; anything PLAN does not cover | a PLAN §10 row |

When unsure of the level, take the higher one. Group related Level 2 choices in the stage decision, then bring
ready decisions together in the daily digest. Give the options, the recommendation and reason, the cost,
what each choice blocks, and the reply that approves it. Keep independent work moving while a decision is pending.

## Rules every agent keeps

1. **`main` is published by the coordinator only**: without asking for the classes R1-AUTONOMY (3) names, otherwise
   on the author's "推 main". No other role pushes `main`. No force push anywhere. Merges to `main`
   are merge commits (no squash, rebase or cherry-pick), so launch commits keep their hashes.
2. **Nothing is deleted.** A file to remove goes to `_to_delete/`; the author empties it.
3. **Credentials are never read:** `~/.config/r1/secrets.env`, key files, `~/.docker/config.json`, `.docker-config`.
   No `docker login`.
4. **Sealed data stays sealed.** Test labels and evaluation values are read only after their release row. A read by
   mistake is a STOP and is reported at once.
5. **Evidence runs start only from the launch commit a signed note names**, with the note's check passing. No
   assertion is relaxed, no request edited to get a slot, no run resumed into an old directory. Where a job runs is
   otherwise free (R1-HOST-FREE): only runs that are compared with each other stay on one hardware class.
   No wall-clock limit and no calendar date decides anything (R1-NO-TIMEOUT, R1-STEP-ORDER); a step starts when
   the steps it depends on are complete.
6. **A STOP is a result.** Stop that line, keep the scene, report it. Do not work around it.
7. **Every unit is reviewed by a fresh agent that did not write it**, until the review says "accepted"; code units
   also show the full `r1/tests` suite with zero new failures against their base.
8. **Other users' processes and files are never touched.** Shared hosts keep their limits (`COMPUTE.md`).
9. **Files are written in English. The author is addressed in Chinese, briefly.**

## How work moves

The repository carries the messages (R1-AUTONOMY):

- **Tasks.** The coordinator breaks down the next-phase runbook into one card per deliverable on `coord/coordinator`
  under `tasks/<role>/<YYYYMMDD>-<nn>-<slug>.md`. Each card gives its source, inputs, dependencies, acceptance checks
  and report. `STATE.md` orders the queue for each role and records current work and blockers. `AUTHOR.md` records
  decisions that wait on the author. Follow the [dispatch procedure](../docs/r1/runbooks/AUTOML_AS_DAC_NEXT_PHASE_20261126.md#7-dispatch-and-run-the-queues).
- **Reports.** Each agent writes one file per finished task or STOP to its own branch (`coord/local`,
  `coord/compute`, `coord/writer`): `reports/<YYYYMMDD>-<nn>-<slug>.md` with the task id, the result in five
  lines, each branch and tip, each sha256 that matters, what it decided alone, and what it needs. A report may carry
  `for: <role>`; that role treats it as a task (a direct hand-off).
- **One writer per branch**, so pushes never collide. The `coord/*` branches hold messages only, never code.
- **One coordinator at a time.** The file `COORDINATOR` on `coord/coordinator` names the session that holds the role.
  Only that session writes tasks and publishes `main`. A hand-over is one commit to that file by the session taking
  over; a session that finds another name there stops coordinating.
- **Rhythm.** A worker fetches after each task and takes the next ready card in its queue. It checks for new work
  every 30 minutes while idle. The coordinator looks at the report branches at least hourly, verifies and merges
  what is ready, and writes the next tasks.
- **The author** gets one Chinese digest a day with completed work, results, next steps and decisions.
  Raise a Level 2 decision immediately if it blocks the critical path. Follow existing incident and resource
  reporting requirements.

## Roles and what runs them (R1-AGENT-RUNTIMES, R1-AGENT-COMPUTE)

| Role | Runs on | Where |
|---|---|---|
| coordinator | Claude Opus 5.5, soft limit only | a tmux session that stays up |
| writing and brainstorming | Codex GPT-6.2 Sol, high reasoning effort | `paperb-writer` in Codex CLI signed in with ChatGPT, working in a [paper_B_manuscript](https://github.com/dowlingwong/paper_B_manuscript) checkout |
| design | session assigned by the coordinator or author | design handoff in the existing writer workflow until a dedicated channel is set |
| local worker | GPT-6.2 Sol, high reasoning effort | Codex CLI signed in with ChatGPT, `paperb-local` |
| compute agent | DeepSeek Flash through OpenCode | `paperb-compute`, with SSH to the hosts in R1-AGENT-COMPUTE |

A new session of any role starts by reading this file, its `SOUL.md`, `PAPER_B_PLAN.md`, `COMPUTE.md`, and the PLAN
§10 sections dated after the plan file's "as of" line.
