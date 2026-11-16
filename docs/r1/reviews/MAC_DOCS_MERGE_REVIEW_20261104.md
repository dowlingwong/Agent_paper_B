# Review: mac-int docs merges `210aa99e` and `316ba2a5` (4 Nov 2026)

**Independent reviewer (Claude, fresh subagent; AI-assisted).** Scope, per the author's instruction (4 Nov 17:01, "……只审这段 diff"): only `fe193b3b..316ba2a5` on `mac-int-20261104`. Commits before `210aa99e` are reviewed elsewhere. Everything below was verified from git objects (`git cat-file`, `git diff-tree`, `git merge-tree --write-tree`, blob ids). Nothing was modified, staged, committed or pushed apart from this untracked file. No servers, LLMs or GPU were used.

## Verdict: **accepted**

There are no BLOCKING or MAJOR findings. Both commits reproduce the three-way merge of their sources exactly, at the tree level, and change nothing else. The MINOR findings below are all about the content of the merged inventory document, which is merged as-is, and none of them requires changing either commit.

## Check 1: `210aa99e`, `docs/runbooks-04nov` `0abfaf2b..8e455234`

**Source range.** `0abfaf2b` is an ancestor of `8e455234`, and their merge-base is `0abfaf2b`.

| Commit | Subject | Paths |
|---|---|---|
| `7f99da11` | HoreKa scan prompt rev 5.5 (+ REV54 review fixes) | M `docs/r1/prompts/HOREKA_SCAN_PROMPT_20261104.md`; A `docs/r1/reviews/HOREKA_SCAN_PROMPT_REV54_REVIEW_20261104.md` |
| `3defa7b6` | HoreKa scan prompt rev 5.6; review round 2 fixes | M the prompt; M the REV54 review |
| `8e455234` | review round 3, rev 5.6 PASS, prompt unchanged | M the REV54 review (+35 lines) |

The net change of the source, `git diff --name-status 0abfaf2b 8e455234`, is the same two paths. `git diff --name-status fe193b3b 210aa99e` gives exactly the same two paths (M prompt, A review). Nothing else changed.

**Three-way result.** `git merge-tree --write-tree --merge-base=0abfaf2b fe193b3b 8e455234` gives the tree `5dc9b101a20c…`. That equals `210aa99e^{tree}`, so the whole tree matches, file modes included.

**Per-file blob check.**
- Prompt: `0abfaf2b` = `fe193b3b` = `b5915aa6`. So mac-int had not touched the prompt since `0abfaf2b`, which is consistent with the commit message. `8e455234` = `210aa99e` = `8b0eddd2`.
- Review (added file): absent at `0abfaf2b` and at `fe193b3b`. `8e455234` = `210aa99e` = `e56cdae0`, so the two are byte-identical.

**Author's description "rev 5.5–5.6 和三轮审查".** It matches the range. The REV54 review file is new in this range: round 1 (of rev 5.4) arrives with `7f99da11`, round 2 (`# Round 2 — revision 5.5`, PASS-WITH-FIXES) with `3defa7b6`, and round 3 (`# Round 3 — revision 5.6`, PASS) with `8e455234`. No round was merged earlier. Rev 5.4 itself (`0abfaf2b`) was integrated earlier by `4ca40393`, but its review round 1 was not on `0abfaf2b`, so all three rounds enter in this range. The earlier HoreKa reviews (`HOREKA_SCAN_PROMPT_REVIEW`, `_REV4_`, `_REV5_`) were already on mac-int before `210aa99e` and are not touched.

## Check 2: `316ba2a5`, `docs/repo-tidy-20261104` @ `d413dc81`

- `git rev-list --count 009d859a..d413dc81` gives 1. `d413dc81`'s only parent is `009d859a`, and `origin/docs/repo-tidy-20261104` is at `d413dc81`.
- `d413dc81` changes three paths: A `docs/r1/BRANCHES_20261104.md`, A `docs/r1/prompts/README.md`, and M `README.md`. The README change is exactly one line (`-1/+1`, the `docs/r1/` row of the path table).
- `README.md` is unchanged on mac-int in `009d859a..210aa99e`.
- `git merge-tree --write-tree --merge-base=009d859a 210aa99e d413dc81` gives the tree `2979cc41…`, which equals `316ba2a5^{tree}`.
- Blobs at `d413dc81` and `316ba2a5` are identical for all three paths: README `0cab26e6`, BRANCHES `342691b4`, prompts/README `ee5a3a3f`.
- `git diff --name-status 210aa99e 316ba2a5` lists the same three paths and nothing else.

## Check 4: `plan_row_check.py`

The command was run as given, with `--result 316ba2a5` and the six sources. The result is **MISSING total: 0**. Every source reports all its items present byte-identical: 853, 847, 856, 798, 817 and 887. There are three RESULT-ONLY items, all of them mac-int's own records from before `210aa99e` (the M1 integration, the 16:13 replies, and R1-EXAM-A1-M1-REQUIREMENTS). Neither commit under review adds a §10 row or a STATUS entry.

## Check 5: commit messages

- Both messages quote the author's 17:01 instruction verbatim, name the source and range correctly, describe the three-way merge and the "unchanged on mac-int, so result equals source" reasoning (verified above), and carry "AI-assisted (Claude, Mac-local agent)." plus the Co-Authored-By and Claude-Session lines. Both commits are SSH-signed.
- `210aa99e` lists `7f99da11` (rev 5.5), `3defa7b6` (rev 5.6) and `8e455234` (review round 3, prompt unchanged). All three are accurate. The message abbreviates the prompt path to its basename, which is harmless.
- `316ba2a5`'s "one commit on top of mac-int 009d859a … one line" is accurate.

## Findings

### BLOCKING
None.

### MAJOR
None.

### MINOR (content of the merged documents; merged as-is, no change to either commit required)

1. **The inventory is a snapshot that this very merge makes stale.** `BRANCHES_20261104.md` was written at `009d859a` and says:
   - `mac-int-20261104` tip `009d859a`. On this branch the tip is now `316ba2a5`.
   - `docs/runbooks-04nov`: "Integrated into `mac-int` up to `0abfaf2b`; scan prompt rev 5.5–5.6 and its three review rounds are not yet integrated". After `210aa99e` they are integrated.
   - `docs/repo-tidy-20261104`: tip "this commit". On mac-int, "this commit" no longer exists as such, because the merge is a single-parent commit.

   A reader of mac-int would take these claims as current. *Optional:* a later dated note, or a one-line "as of `009d859a`" qualifier. Not for this merge.
2. **"Can be deleted once merged" does not hold under mac-int's integration method.** Both `210aa99e` and `316ba2a5`, like the earlier `4ca40393` and `7da89e8c`, are single-parent integration commits. So `7f99da11`, `3defa7b6`, `8e455234` and `d413dc81` are **not** ancestors of mac-int (checked with `git merge-base --is-ancestor`: no for all four). By the inventory's own rule ("Content integrated but commits not merged → tag, then delete"), `docs/runbooks-04nov` and `docs/repo-tidy-20261104` belong in the "tag, then delete" class, not "delete once merged". This matters more for `docs/runbooks-04nov`: `docs/main-proposer-03nov`'s tip `14dc0fea` is an ancestor of `docs/runbooks-04nov` (verified). Deleting runbooks-04nov without a tag would drop that review history too, unless `archive/docs/main-proposer-03nov` is tagged first as the inventory recommends. The inventory's statement that main-proposer's commits "are not ancestors of any kept branch" is also not quite true while `docs/runbooks-04nov` exists. Deletion is author-only, so nothing acts on this automatically.
3. **`trackp-20261026`, "one commit not elsewhere".** Two commits on `origin/trackp-20261026` are reachable from no other ref: `08aeaff9` (Guard P.3a execution and GPU lease budget) and the merge `b9ad6f8f`. Substantively it is one content commit plus a merge, so this is cosmetic.

### Not verifiable here (no finding)

The clone's fetch refspec covers only `main` and `mac-int-20261104` (plus remote refs already present). The branches `dt-sweep1-20261026`, `local-20261026`, `local-h8-20261027`, `trackS-20261029`, `ops/c3-sweep1-classify-20261028`, `codex/trackx-seed-20261031`, `exam-x-20261026` and `dt-sweep1-20261025` have no local refs, so their "contained in" claims were not checked.

What was checked and is consistent:
- The tips of `main` (`36b89773`), `codex/coordinator-20261031` (`10742f85`, an ancestor of mac-int: yes), `codex/trackx-stagea-cooperative-20261031` (`74a07907`), `codex/b2-repair-20261031` (`f98e315e`), `trackS-ops-20261030` (`f5d5c6b0`), `trackp-20261026` (`b9ad6f8f`) and `docs/runbooks-04nov` (`8e455234`) match the remote refs.
- `docs/main-proposer-03nov`'s "2 in PLAN, 12 in RUNBOOK" lines not verbatim in mac-int @ `009d859a` reproduces exactly: 2 and 12.

`prompts/README.md` was also checked:
- It covers all 26 other files in `docs/r1/prompts/` at `316ba2a5` (8 in use, 18 history).
- It names `HOREKA_SCAN_PROMPT_20261104.md` as rev 5.6 with round 3 PASS, which is true after `210aa99e`.
- `MAC_LOCAL_RUNBOOK_20261104.md` is rev 3.3; M10–M15 and O8, O10 and O11 exist in the runbooks.
- The cited rows R1-HANDOVER-04NOV, R1-SERVER-AGENTS-TWO, R1-TASL7-TRACKP and R1-TRACKX-HANDOVER-RULING exist in PLAN.
- `../BRANCHES_20261104.md` and `../PLAN.md` resolve.

No inconsistency was found.
