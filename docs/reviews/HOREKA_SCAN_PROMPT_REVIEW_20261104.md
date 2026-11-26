# Review — HoreKa 2 read-only scan prompt and R1-T1-HOREKA propagation (4 Nov 2026)

**Reviewer:** an independent agent (Claude), AI-assisted. I reviewed documents only: no SSH, no cluster contact, nothing committed or pushed. This file is the only one I wrote.
**Scope:** `docs/r1/prompts/HOREKA_SCAN_PROMPT_20261104.md`; the PLAN §10 row R1-T1-HOREKA; the propagation lines in commit `387798ed` (RUNBOOK banner, STATUS, MAC_LOCAL M10 line, OPERATOR host-table row).
**Sources checked:**
- the author's cheat sheet (chat attachment `horeka_job_submission.md`);
- <https://docs.nhr.kit.edu/usage/slurm/> and <https://docs.nhr.kit.edu/get-started/migration/>, fetched 4 Nov;
- `docs/r1/proposals/HOREKA_T1_JOBS_DRAFT_20261104.md` (rev 2), §0, §1, §4 and §6;
- `prompts/TRACK_G_RUNBOOK.md` and `prompts/OPERATOR_RUNBOOK_20261104.md` O8, for propagation;
- local bash tests of the word splitting in the `$shape` loop and of stdin consumption under `bash -s`.

## Summary

| Class | Count |
|---|---|
| BLOCKING | 0 |
| MAJOR | 7 |
| MINOR | 14 |

**What holds.**
- The prompt is clearly scoped: "It authorizes nothing beyond the scan described here." The author's request is quoted verbatim.
- Every cluster command is a read-only query: `sacctmgr show`, `sshare`, `sreport`, `scontrol show`, `squeue`, `sacct`, `module avail/spider`, `df`, `mount`, `curl -I`. `sbatch --test-only` submits nothing.
- The only writes are `mkdir -p ~/r1_scan_20261104`, the probe script and the job's output file.
- The rules exclude everything that would change state: no `sacctmgr modify`, `ws_allocate`, `module save`, installs, clones, downloads or dotfile edits.
- Credentials: the prompt says STOP on any password or OTP prompt and never read keys or `secrets.env`. The `ControlMaster` approach matches the cheat sheet.
- Polling: the 60 s interval is stricter than NHR's 30 s.
- Exactly one dev job: 1 GPU, 15 minutes, 8 CPUs. The prompt says STOP if a dev job already exists, never try another partition, and never cancel without the author.
- Shell details that are correct:
  - `${PROJECT:+"$PROJECT"}` is the right idiom.
  - The `$shape` word splitting gives the intended arguments. I tested it: `[-p][gpu-h100][--gres=gpu:4][--exclusive][-t][24:00:00][-N][1][--wrap][true]`, and the strings contain no glob characters.
  - `echo "--- $shape"` prints literally.
  - `--wrap "true"` means sbatch does not read its stdin.
  - `#!/bin/bash -l` defines `module` in the job.
  - `--output=probe-%j.out` resolves against the submit directory, because the submission does `cd ~/r1_scan_20261104 && sbatch probe.sh`.
- The probe takes about 1–2 minutes of its 15. Its curls are bounded at 10 s each.
- Local governance: the prompt keeps away from the main working tree, writes nothing to the repository and does not commit or push.
- The PLAN row quotes the author's 13:45 words verbatim and marks its additions *(proposed)* and *(open)*. STATUS and the RUNBOOK banner say "No run started" and say the job design is adopted only by a later row.

**What fails.**
- **Compliance.** The prompt leans on an unrecorded claim that the author knows about the AI-agent rule, and it contradicts draft §4 and the new OPERATOR row (MAJOR-1).
- **Its own rules.** The polling loop breaks the prompt's own "no loops of separate SSH calls" rule (MAJOR-2).
- **Local files.** Relative local paths can land the scan's files in the main working tree (MAJOR-3).
- **Budget.** The budget question will very likely come back "not found" with the commands given (MAJOR-4).
- **Account.** There is no `--account` step for a multi-project user (MAJOR-5).
- **Propagation.** The M10 line goes past the PLAN row (MAJOR-6). OPERATOR O8 and TRACK_G still send the census to Ada (MAJOR-7).

## Findings

### MAJOR

**MAJOR-1 — The compliance basis is an unrecorded claim, and it contradicts draft §4 and the OPERATOR row.**
- *Where:* prompt §2 rule 1, third bullet ("The author knows about the rule and has asked for this scan"); OPERATOR host-table row HoreKa 2 ("the author submits, monitors and copies back"); draft §4 items 1–2(a).
- *Problem:*
  - The migration page prohibits "AI agent processes, API calls, or similar interactive workloads on login nodes".
  - Draft §4(a) asks NHR@KIT exactly whether "an AI agent outside the cluster [may] run `sbatch`, `squeue` and `rsync` through SSH". The draft and the OPERATOR row both say the author does this until NHR answers.
  - The prompt has an agent run the login script, copy a file, submit a job, poll `squeue` and fetch the output, all through SSH on the login node. The question is still unanswered.
  - The author did ask for an agent-run scan ("我让一个能ssh进horeka的agent去扫"). But "the author knows about the rule" is the chat session's statement, not the author's words. The prompt then uses it to tell the executing agent to proceed despite the cluster rule.
- *Fix:*
  - Add a step 0 before the first SSH call. The agent shows the author the quoted rule and the planned SSH calls, gets an explicit yes, and quotes that yes in the report. Replace the sentence "The author knows about the rule…" with "The author asked for this scan; before the first SSH call, confirm with him (step 0)."
  - Offer option B in the prompt. Both scripts are fixed, so the author can run the two commands himself in about 2 minutes (`ssh hk2 'bash -l -s' < scan_login.sh > login_scan.txt 2>&1`, and the copy and submit). The agent then only writes the report from the files. The author picks A or B.
  - Add to the OPERATOR row: "except the one-time read-only scan in `prompts/HOREKA_SCAN_PROMPT_20261104.md`, if the author confirms it (step 0)".

**MAJOR-2 — The polling loop contradicts the prompt's own rules, and the login-node footprint is not minimal.**
- *Where:* prompt §2 rule 1 ("no loops of separate SSH calls"), §2 rule 3 ("never call `squeue` or `sacct` more often than once every 60 s"), §3 lines 75–77 and 85, §4 lines 91 and 123.
- *Problem:*
  - §4 polls with a fresh `ssh hk2 squeue` every minute for up to 45 minutes. That is up to about 45 separate login-node sessions, which is exactly the loop that §2.1 forbids.
  - The login script itself runs `squeue` three times and `sacct` once within seconds. That breaks §2.3 as worded, even though it is not polling in NHR's sense. An executing agent may either STOP on the contradiction or ignore both rules.
  - Copying the probe and submitting it are separate calls.
- *Fix:*
  - **Reword rule 3:** "Repeated status checks: at most once every 60 s. The one-off queries in §3 are not polling."
  - **Merge the two count queries:** `squeue -p gpu-h100 -h -o %T 2>&1 | sort | uniq -c`.
  - **Copy and submit in one call:** `ssh hk2 'cat > ~/r1_scan_20261104/probe.sh && cd ~/r1_scan_20261104 && sbatch --parsable probe.sh' < "$S/probe.sh"`.
  - **Poll less:** every 5 minutes, at most 9 checks in 45 minutes. Once the job is gone from `squeue`, run one `sacct -j <id> -n -P -o JobID,State,ExitCode,Elapsed`, then fetch the output.
  - **Count the calls:** state the total, about 4 + polls.
  - **Waiting:** allow any wait of at least 60 s that the harness offers. Some Claude Code harnesses block a foreground `sleep`.

**MAJOR-3 — Relative local paths can put the scan files into the main working tree.**
- *Where:* prompt §3 line 47 ("Save this as `scan_login.sh` locally … `> login_scan.txt`"), §4 line 91 (`probe.sh`), §2 rule 6.
- *Problem:*
  - `scan_login.sh`, `login_scan.txt`, `probe.sh` and the fetched `probe-<id>.out` are named relative to the agent's current directory. A Claude Code agent started in `~/Documents/agent_paper_B` would create them in the main working tree. That tree has someone else's uncommitted changes, so this breaks rule 6.
  - The snapshot folder itself sits inside that tree's directory (`.claude-worktrees/`), and the repo `.gitignore` does not exclude `.claude-worktrees/`. Unless a global or `info/exclude` rule covers it, the folder shows up as untracked in the main tree.
- *Fix:*
  - Start §3 with `S="$HOME/Documents/agent_paper_B/.claude-worktrees/_snapshots/horeka_scan_20261104"; mkdir -p "$S"`.
  - Use `"$S/…"` for every local file, including the redirect targets and the `scp` destination.
  - Add: "never `cd` into `~/Documents/agent_paper_B`; check `git -C ~/Documents/agent_paper_B check-ignore -q .claude-worktrees/_snapshots` and, if it is not ignored, tell the author before writing."
  - Alternatively, use a folder outside the repo.

**MAJOR-4 — Q1 (the budget) will very likely be "not found" with the commands given.**
- *Where:* prompt §3 blocks 2–3; §5 Q1. Draft §6.1 and §9.4 need the remaining GPU-hours.
- *Problem:*
  - `sacctmgr show associations user=$USER` lists only the user's rows. A project's `GrpTRESMins` is normally set on the account row (no user), so the user rows show it empty.
  - `sacctmgr` never shows usage against a limit.
  - `sreport … -t hours` reports CPU-hours unless `--tres` is given.
  - The prompt's rule 5 ("do not try substitute tools") then guarantees "not found".
- *Fix:* add these read-only queries.
  ```bash
  scontrol show assoc_mgr users="$USER" flags=assoc 2>&1 | head -60   # limits with usage in parentheses, e.g. GrpTRESMins=gres/gpu=N(used)
  for a in $(sacctmgr show associations user="$USER" -n -P format=Account | sort -u); do
    echo "--- account $a"; sacctmgr show associations account="$a" -n -P format=Account,User,GrpTRESMins,GrpTRES,GrpWall 2>&1 | head -20
    scontrol show assoc_mgr accounts="$a" flags=assoc 2>&1 | head -30; done
  sreport -t hours --tres=cpu,gres/gpu cluster AccountUtilizationByUser user="$USER" start=2026-01-01 2>&1 | head -40
  ```
  Q1 should also tell the agent to say plainly if the budget is held only in the NHR project portal. In that case the author reads it there.

**MAJOR-5 — No `--account` decision for a user with more than one project.**
- *Where:* prompt §4 probe header; §3 test-only shapes. The NHR slurm page says `--account` is "Required if you belong to more than one project". The cheat sheet says "needed if you're in >1 project", and draft §3 sets `--account` in every template.
- *Problem:*
  - If block 2 shows more than one account, the test-only shapes and the probe may be refused.
  - Or the probe may be billed to whichever project is the default, which may not be the one the author means for T1.
  - The prompt collects the accounts (Q1) but never uses the answer. A refusal then STOPs the scan under §4 ("record the exact message"), and the scan's main job is lost.
- *Fix:* after the login part, if more than one account is listed, STOP and ask the author which account to use. Add `#SBATCH --account=<that>` to the probe and record the choice in the report. Never run `sacctmgr modify` to change the default; the prompt already forbids it.

**MAJOR-6 — The MAC_LOCAL M10 line adopts draft §5 into M10, which the PLAN row defers to a later row.**
- *Where:* `prompts/MAC_LOCAL_RUNBOOK_20261104.md`, the new line under M10: "M10 therefore also includes the HoreKa code of … §5 … Write it after the scan report". PLAN R1-T1-HOREKA, consequence 1.
- *Problem:*
  - The author decided the host, not the code.
  - The PLAN row itself marks the draft's "job design, its §5 code …" as *(proposed)*, "adopted only by a later row, after the read-only scan".
  - The M10 line states, without a marker, that M10 includes that code, and tells the Mac agent to write it once the scan report exists. That puts in force something the decision does not contain.
- *Fix:* "*(proposed)* If a later row adopts the draft's §5 (after the scan report), M10 also includes …. Until that row exists, write none of it."

**MAJOR-7 — OPERATOR O8 and TRACK_G still send the census, the floors and the T1 labels to Ada, with no pointer to the decision.**
- *Where:*
  - OPERATOR line 33 (Ada row: "the Track G census and GPU-node noise floors (O8 G.0), which R1-BX-D14 starts on Ada");
  - OPERATOR line 317 ("G.0 … start right after STOP 0, on Ada"), line 319 ("Ada first") and line 324 ("census on Ada first; the T1 label table on Ada");
  - TRACK_G lines 47 and 61 ("Ada first"), line 84 and line 109 ("Ada for T1 label runs").
  - Draft §0, last bullet, lists these places.
- *Problem:*
  - Only the RUNBOOK banner says "read HoreKa 2". The operator works from its own runbook, and O8 tells it to start G.0 on Ada right after STOP 0.
  - The operator could start work that contradicts R1-T1-HOREKA, or treat the HoreKa row and the Ada row in its own table as conflicting.
  - Also not covered: whether Ada work meanwhile continues for raw cost only (draft §0: Ada results stay valid for raw cost but set no H100 noise width), or stops.
- *Fix:*
  - Add a dated pointer at OPERATOR O8, at the Ada row, and at TRACK_G G.0, G.1b, §84 and §109: "4 Nov 13:45, R1-T1-HOREKA: the T1 census, floors and labels run on HoreKa 2; Ada is the whole-table fallback."
  - Add an *(open)* line for the author: "Meanwhile, may G.0 raw cost and liveness run on Ada (valid for raw cost only, draft §0), or does Track G GPU work wait for the HoreKa row?"
  - List these places in the PLAN row's amendment list too (see MINOR-13).

### MINOR

**MINOR-1 — `bash -s` stdin hazard and stderr ordering.**
- *Where:* §3, the whole script.
- *Problem:*
  - Under `bash -s`, any command that reads stdin consumes the rest of the script, and the remaining blocks vanish silently. I reproduced this with `cat` locally. Candidates are a site wrapper (`sinfo_t_idle`, `ws_list`), a profile script, or `sbatch` if `--wrap` were ever dropped.
  - Over SSH, stdout and stderr are separate channels. Lines without an in-place `2>&1` (block 1, both `sacctmgr` lines in block 2) can land far from their header.
- *Fix:* wrap the body so bash parses it completely before running it, with stdin closed.
  ```bash
  main(){ exec 2>&1; set +e; …all blocks…; }
  main </dev/null
  ```

**MINOR-2 — The queue counts hide errors and may be wrong under `PrivateData`.**
- *Where:* §3 lines 75–76 (`squeue … 2>/dev/null | wc -l`).
- *Problem:* a failed `squeue` prints "pending jobs in gpu-h100: 0". If `PrivateData=jobs` is set, users see only their own jobs, so 0 is also what any healthy query shows. Q3 would then report a false empty queue.
- *Fix:* use the merged query from MAJOR-2 with `2>&1`. Add `scontrol show config 2>&1 | grep -E '^(PrivateData|MaxArraySize|MinJobAge|OverTimeLimit|PreemptMode|SchedulerParameters) '`, and have Q3 say whether other users' jobs are visible.

**MINOR-3 — `sinfo` is restricted to administrators.**
- *Where:* §3 line 59.
- *Problem:* the NHR slurm page says "The `sinfo` command is restricted to administrators and is not available to regular users". The call is harmless but produces an error. That error could read as a refusal and trip the policy STOP (MINOR-6).
- *Fix:* drop `sinfo -s`, or label it "(expected to be refused; NHR docs)". Keep `sinfo_t_idle`.

**MINOR-4 — The module grep misses category-prefixed names and spiders only CUDA.**
- *Where:* §3 lines 79–80; probe line 118.
- *Problem:* the anchored `^(cuda|…)` matches only flat EasyBuild names (`CUDA/12.4.0`). It misses categorized ones (`devel/CUDA/…`, `lang/Python/…`, legacy-KIT style `devel/cuda/…`), and hierarchical layouts hide CUDA until a compiler is loaded. Q6 needs GCC, CMake and Python pins, not only CUDA.
- *Fix:* `grep -i -E '(^|/)(cuda|cudnn|nccl|python|gcc|gcccore|cmake|git|apptainer|singularity|openmpi)(/|$)'`, and `for m in CUDA GCC GCCcore CMake Python; do module -t spider "$m" 2>&1 | head -15; done`.

**MINOR-5 — The resubmission test inside the job may hit the dev-partition limit.**
- *Where:* probe line 117 (`sbatch --test-only -p dev-cpu …`).
- *Problem:* dev partitions allow one submitted job per user (`MaxSubmitJobsPerUser=1`, NHR page). If the dev partitions share that limit, the running probe holds the slot. The test then fails with a QOS-limit message. That gives a false "no" for Q11 and can trip the "policy" STOP.
- *Fix:* test against a non-dev partition: `sbatch --test-only -p cpu -n 1 -c 1 --mem=1G -t 00:05:00 --wrap true 2>&1`.

**MINOR-6 — The "policy" STOP condition is too broad.**
- *Where:* §6, bullet 4.
- *Problem:* almost every motd links an acceptable-use policy, and Slurm refusals say "Job violates accounting/QOS policy". Read literally, the condition stops the scan after the login part, before the GPU job, on routine text.
- *Fix:* "STOP if the motd, a command or a message says something about AI agents, automated SSH or login-node use that is not already quoted in §2, or reports misuse of, or a restriction on, this account. Generic policy links and Slurm limit refusals during `--test-only` are recorded as data (Q12)."

**MINOR-7 — SSH preflight, non-interactive auth and timeouts.**
- *Where:* §1, §3, §4.
- *Fix:*
  - Check the config with `ssh -G hk2 | grep -E '^(hostname|user|controlmaster|controlpath) '`, not by reading `~/.ssh/config`. It resolves includes and keeps the agent out of `~/.ssh/`.
  - Check the master with `ssh -O check hk2`. If it is not running, STOP and ask the author for `ssh -fN hk2` before any other call.
  - Use `ssh -o BatchMode=yes hk2 …` on every call, so a missing master fails at once instead of prompting for a password or OTP.
  - Wrap the login call in `timeout 600` and raise the harness's command timeout; Claude Code's default is 2 min, and the login part can exceed it.

**MINOR-8 — Probe-job hygiene.**
- *Where:* §4.
- *Fix:*
  - add `#SBATCH --deadline=now+2hours`, so a job still pending is removed by Slurm rather than left to start unattended after the agent gives up;
  - add `#SBATCH --mem=16G` (the dev default is 186 GB per GPU, more than a probe needs);
  - submit with `--parsable`;
  - "Never resubmit: if `sbatch` prints no job id, run `squeue -u $USER` once and STOP."

**MINOR-9 — Coverage gaps for draft §1, §6.5 and §0.**
- *Where:* §3, §4, §5.
- *Fix (all read-only):*
  - add `compute_cap` to the `nvidia-smi --query-gpu` list, since draft §1 needs the CUDA arch flag (`sm_90` expected);
  - add `stat -f -c %T "$HOME" ${PROJECT:+"$PROJECT"}` for the file-system type;
  - print proxy variable names only: `env | grep -i _proxy | cut -d= -f1`. Their values may hold credentials;
  - add `env | grep -E '^(PROJECT|WORK|SCRATCH|TMPDIR|WS_)' | sort` to find storage variables;
  - add `cat /etc/motd.d/* 2>/dev/null | head -40`;
  - Q2: tell the agent that `OverSubscribe=FORCE` means `--exclusive` is ignored, while `NO` or `EXCLUSIVE` means it is honoured;
  - Q4: add the reservation `Flags` (MAINT, IGNORE_JOBS) and what happens to pending jobs (draft §6.5). From the Mac, with no cluster cost, read the NHR@KIT maintenance or news page, because the reservation may not exist yet;
  - add `--deadline=<cutoff>` to one `--test-only` shape, to show that draft §5's `--deadline` guard is accepted.

**MINOR-10 — `nvidia-smi -L` inside the job cannot see other GPUs.**
- *Where:* probe line 112.
- *Problem:* with cgroup device confinement, a 1-GPU job sees only its own GPU. The header "all gpus on this node (other users' processes?)" invites a false "no co-tenancy" in Q9.
- *Fix:* relabel the header "GPUs visible to this job", and have Q9 say that co-tenancy on other GPUs is not observable from a 1-GPU job.

**MINOR-11 — The draft may not be available on the Mac.**
- *Where:* §5 ("anything that contradicts the draft …").
- *Problem:* the main tree has another branch checked out, and `387798ed` may not be pushed. The scanning agent may not find the draft and must not open the main tree.
- *Fix:* give a read-only route: `git -C ~/Documents/agent_paper_B show <branch-or-commit>:docs/r1/proposals/HOREKA_T1_JOBS_DRAFT_20261104.md`, or have the author paste the draft's §1 table. If neither works, compare against §2 and §5 of the prompt and say so.

**MINOR-12 — List the unavoidable side effects.**
- *Where:* §2 rule 4.
- *Problem:* `module avail/spider` may write Lmod's user cache (`~/.cache/lmod` or `~/.lmod.d`). The first SSH may add a `known_hosts` entry locally. Neither is in `~/r1_scan_20261104`.
- *Fix:* name both as expected, so the agent neither STOPs on them nor reports "nothing outside the scratch directory".

**MINOR-13 — The amendment list sits in the decision cell and is incomplete.**
- *Where:* PLAN R1-T1-HOREKA decision cell ("This amends, as listed in … §0: …").
- *Problem:* the author named the tier and the host, not the rows. The list is the recording agent's mapping, taken from the draft, but it sits inside the bold decision cell. It also omits draft §0's last bullet: RUNBOOK G.0's GPU list, and "Ada first" in G.0/G.1b, TRACK_G and OPERATOR O0/O8 (see MAJOR-7). The host name `hk2-x86.scc.kit.edu` comes from the cheat sheet, not the 13:45 words. That is acceptable, but cite it.
- *Fix:* keep the author's sentence in the cell. Move "This amends …" under "Consequences noted by the recording agent" as "*(recording agent's mapping, from draft §0)*" with the full list, and cite the cheat sheet for the host name.

**MINOR-14 — The OPERATOR row's who-acts rule is unmarked.**
- *Where:* OPERATOR host-table row HoreKa 2.
- *Problem:* "Until NHR@KIT confirms … the author submits, monitors and copies back" comes from draft §4, which is not adopted. The PLAN row keeps it *(open)*. The rule is conservative, which is fine, but it carries no marker and no exception for the scan (see MAJOR-1).
- *Fix:* add "*(from draft §4, proposed; PLAN R1-T1-HOREKA open item)*" and the scan exception.

## Coverage against draft §0 and §6

| Need | Covered by | Status |
|---|---|---|
| Accounts | block 2, Q1 | yes; `--account` choice missing (MAJOR-5) |
| GPU-hour budget used and left | blocks 2–3 | likely "not found" (MAJOR-4) |
| Exclusivity | `scontrol show partition`, `--test-only --exclusive`, probe `scontrol show job` | yes, with the OverSubscribe reading (MINOR-9) |
| Queue | `--test-only` shapes, `squeue` counts | estimates yes; counts unreliable (MINOR-2) |
| Downtime exact times, pending jobs | `scontrol show reservation`, motd | start and end only if a reservation exists; pending-job handling missing (MINOR-9) |
| Storage (`PROJECT`, `$HOME` quota, workspaces, GPFS) | block 6 | yes; FS type and variable discovery missing (MINOR-9) |
| Modules (CUDA, GCC, CMake, Python) | block 8, probe | partial (MINOR-4) |
| Network from login and from compute | block 10, probe | yes; proxy variable names missing (MINOR-9) |
| H100 specs (memory, driver, CUDA, MIG, compute mode) | probe | yes; `compute_cap` missing (MINOR-9) |
| Local scratch | probe `df /tmp $TMPDIR /scratch` | yes |
| Self-resubmission | probe `sbatch --test-only` | yes, but the dev-cpu target may give a false no (MINOR-5) |
| Policy, `agent` partition | motd, `scontrol show partition agent`, Q12 | yes; motd.d missing (MINOR-9) |
| NHR@KIT question (draft §4) | not scannable | correctly out of scope |

## Governance

- **PLAN row.** It records the author's 13:45 words verbatim, and its additions are marked *(proposed)* or *(open)*. Two exceptions: the amendment list in the decision cell (MINOR-13), and the host name (cite the cheat sheet).
- **Prompt.** It authorizes nothing beyond the scan. It relies on an unrecorded "the author knows" (MAJOR-1). It keeps away from the main working tree in intent but not in mechanics (MAJOR-3).
- **Propagation.** The M10 line goes past the row (MAJOR-6). O8 and TRACK_G are stale (MAJOR-7). The OPERATOR row's rule is unmarked (MINOR-14). STATUS and the RUNBOOK banner are accurate.

## Verdict

Seven MAJOR findings. MAJOR-1, MAJOR-2, MAJOR-3 and MAJOR-5 affect how the scan runs on the cluster and on the Mac. MAJOR-4 means the scan probably misses its first question. MAJOR-6 and MAJOR-7 are governance and propagation. None is BLOCKING: no command in the prompt changes cluster or account state, and the STOPs are in place. But the prompt should not be handed to an SSH agent until MAJOR-1 to MAJOR-5 are fixed.

Verdict: not accepted

---

## Round 2 — re-check against `454587cf` (4 Nov 2026)

**Scope:** `git diff 387798ed 454587cf` covers the prompt (revision 2), PLAN R1-T1-HOREKA, OPERATOR (host table, O8), TRACK_G (G.0, G.1b, G.3, §6) and the MAC_LOCAL M10 line. Documents only; nothing committed.

**Shell checks run locally:**
- I extracted the four `bash` blocks of the prompt: the local-path block, the SSH preflight, `scan_login.sh` and `probe.sh`. **`bash -n` passes on all four.**
- I ran `scan_login.sh` under `bash -s`, as the prompt runs it, with stub versions of every Slurm, Lmod and site command on `PATH`. The stub `sinfo_t_idle` reads stdin on purpose.
  - All 11 section headers and `end` print.
  - The stdin-reading stub did not swallow the rest of the script. The `main … </dev/null` wrapper works.
  - The five `--test-only` shapes expand to the intended argument lists, including `--deadline=2026-11-22T00:00:00`.
- `shellcheck` is not installed here, so I did not run it.

### Status of the round-1 findings

| Finding | Status | Evidence in revision 2 |
|---|---|---|
| MAJOR-1 compliance basis | **Fixed** | §0 quotes the rule and offers option A (the agent) or option B (the author runs the commands). It asks the agent to quote the author's answer and to do nothing on HoreKa without an explicit choice; §7 makes that a STOP. The OPERATOR row adds the scan exception "only under the author's explicit option A". The sentence "The author knows about the rule" is gone |
| MAJOR-2 polling and SSH-call count | **Fixed** | §2.1: one login call, one copy-and-submit call, at most 9 checks at least 5 minutes apart, one final `sacct` plus fetch (about 12 calls, as §0 states). The two counts are merged into `squeue -o '%T' \| sort \| uniq -c`. Submission uses `--parsable`, and §2.2 says never resubmit |
| MAJOR-3 local paths | **Fixed** | §1: one absolute `$S` for every file; never `cd` into the main tree; no `git add` or `commit`. The ignore check of `.claude-worktrees/_snapshots` was not added; this is acceptable, because `.claude-worktrees/` is the established worktree location. See also N2 |
| MAJOR-4 budget | **Fixed** | `scontrol show assoc_mgr … flags=assoc`, a per-account `sacctmgr` and `sshare` loop, and `sreport -t hours --tres=cpu,gres/gpu`. Q1 names these sources |
| MAJOR-5 `--account` | **Fixed** | After §3: if more than one account is listed, STOP and ask, then add `#SBATCH --account`. §7 lists it, and the probe's `scontrol show job` grep now includes `Account` |
| MAJOR-6 M10 scope | **Fixed** | M10 line: "*(proposed; only once a later PLAN row adopts the HoreKa job design, after the scan; write nothing before that row)*" |
| MAJOR-7 O8 and TRACK_G still on Ada | **Fixed, with a residual (N6)** | Pointers to R1-T1-HOREKA are added at the OPERATOR Ada row, O8 items 1 and 3, the O8 Hosts line, TRACK_G G.0, G.1b, G.3 and §6 item 2. The Ada question is recorded as *(open)* on the O8 Hosts line |
| MINOR-1 stdin and stderr | Fixed | `main(){ exec 2>&1; … }; main </dev/null`; the probe has `exec </dev/null 2>&1` |
| MINOR-2 queue counts and PrivateData | Fixed | `2>&1` on the merged count; `scontrol show config \| grep PrivateData …`; Q3 asks about PrivateData |
| MINOR-3 `sinfo` | Fixed | Kept, labelled "sinfo may be restricted; a refusal is a finding". But see the residual under MINOR-6 |
| MINOR-4 module grep | Fixed | `(^\|/)(cuda\|…)`; `spider` loop over CUDA, GCC, CMake, Python |
| MINOR-5 dev-cpu resubmission test | Fixed | The test now targets `-p cpu -n 1 -c 1 --mem=1G -t 00:05:00` |
| MINOR-6 policy STOP too broad | **Partly fixed** | Narrowed; "a plain Slurm refusal of a partition is a finding". But the bullet still STOPs on a message saying "a command or job was blocked by policy". Two outputs the script can be expected to produce match that wording: Slurm's QOS refusal text "Job violates accounting/QOS policy …" from a `--test-only` shape, and the `sinfo` refusal that §3 labels a finding. Fix: add "Refusals from `sinfo` and from `--test-only` (including QOS or accounting-limit messages) are findings, not STOPs." |
| MINOR-7 SSH preflight and timeouts | Fixed, but see N1 | `ssh -G`, `ssh -O check`, `BatchMode=yes`, `timeout 600`, and a harness timeout above 600 s |
| MINOR-8 probe hygiene | Fixed | `--deadline=now+2hours`, `--mem=16G`, `--parsable`, never resubmit, final `sacct` |
| MINOR-9 coverage | Fixed | `compute_cap`; `df -hT` and `stat -f`; proxy names only; storage variables; `/etc/motd.d`; a `--deadline` test shape; reservation flags in Q4; §5 maintenance page from the Mac, including what happens to pending jobs. The OverSubscribe=FORCE reading is not spelled out in Q2 (optional) |
| MINOR-10 `nvidia-smi -L` | Fixed | Header relabelled; Q9 says to draw no co-tenancy conclusion |
| MINOR-11 draft on the Mac | Fixed | `git -C … show docs/runbooks-04nov:… > "$S/draft.md"`, with a fallback to `origin/…`, then ask the author |
| MINOR-12 side effects | Fixed | §2.3 names the Lmod cache and `known_hosts` |
| MINOR-13 PLAN decision cell | Fixed | The cell now holds the author's sentence, with the host name cited to the cheat sheet. The mapping is moved to the consequences, marked "*(the recording agent's mapping, possibly incomplete)*", and now includes RUNBOOK G.0/G.1b, TRACK_G and OPERATOR O0/O8 |
| MINOR-14 OPERATOR row marker | Fixed | "*(proposed, from the HoreKa draft §4)*" and the scan exception |

### New findings (round 2)

All are MINOR. Each one fails safe (a refused or failed command, no state change), but each can stall the scan or invite improvisation.

**N1 (MINOR) — `timeout` is not part of macOS.**
- *Where:* prompt §1 ("Every later call uses `timeout 600 ssh …`"), §3, §4.
- *Problem:* the agent runs on the author's Mac. Stock macOS has no `timeout`; Homebrew coreutils installs it as `gtimeout`. Without it, every SSH call fails with "command not found". That fails safe, but the agent then hits "any need to run something not listed" and STOPs, or improvises.
- *Fix:* add to §1: `T=$(command -v timeout || command -v gtimeout)`, and use `${T:+$T 600} ssh -o BatchMode=yes -o ConnectTimeout=20 -o ServerAliveInterval=15 -o ServerAliveCountMax=4 hk2 …`. If neither exists, the harness tool timeout is the bound.

**N2 (MINOR) — `$S` does not persist between harness shell calls.**
- *Where:* §1, and every later `"$S/…"`.
- *Problem:* Claude Code shell state does not carry over between Bash calls. A later call with an empty `$S` targets `/scan_login.sh`, `/login_scan.txt` and so on. These are refused on macOS's read-only root, so it fails safe, but the run fails.
- *Fix:* "Start every shell call with the `S=…` line", or write the literal absolute path in each command.

**N3 (MINOR) — `sacct` takes `-o`/`--format=`, not a bare `format=`.**
- *Where:* §3 section 11 (`sacct -u "$USER" -S now-7days -n -P format=…`) and the final fetch in §4 (`sacct -j <id> -n -P format=…`). This was already in revision 1, and I missed it in round 1.
- *Problem:* the bare `format=` word is the syntax of `sacctmgr` and `sreport`. `sacct` documents only `--format`/`-o`, so depending on the Slurm version the word is rejected or ignored. The `;` before `cat` means the probe output is still fetched, but the job-state line may be lost.
- *Fix:* `sacct … -n -P -o JobID,Partition,State,Elapsed` and `sacct -j <id> -n -P -o JobID,State,Elapsed,ExitCode`.

**N4 (MINOR) — Make the job id robust and keep the submit error.**
- *Where:* §4, the copy-and-submit and status-check commands.
- *Problem:*
  - `sbatch --parsable` prints `jobid;cluster` on multi-cluster or federated setups. The status check puts that id inside a remote double-quoted command, so the remote shell would treat `;cluster …` as a second command. That is harmless but breaks the check.
  - A refusal message goes only to the terminal (stderr), not to a file.
- *Fix:* `… sbatch --parsable probe.sh' < "$S/probe.sh" 2> "$S/submit_err.txt" | cut -d';' -f1 > "$S/jobid.txt"`. Check that `jobid.txt` is numeric before polling, and copy `submit_err.txt` beside the report.

**N5 (MINOR) — Option B is under-described.**
- *Where:* §0, option B ("He runs the two commands of §3 and §4 himself").
- *Problem:* §4 is not one command. It is the copy-and-submit, the later status checks and the final fetch, and all of them use `$S` and `timeout`.
- *Fix:* "Option B: you write `$S/scan_login.sh` and `$S/probe.sh` and give him three commands: the §3 command, the §4 copy-and-submit, and the §4 fetch, the last to run once `squeue -j <id>` shows nothing. He hands back `login_scan.txt`, `jobid.txt` and `probe_out.txt`."

**N6 (MINOR, the residual of MAJOR-7) — O8 item 1 still reads as an instruction to start on Ada.**
- *Where:* OPERATOR O8 item 1; the O8 Hosts line; TRACK_G §6 item 2.
- *Problem:* item 1 still says "start right after STOP 0, on Ada", followed only by a parenthetical pointer. The Hosts line calls the Ada question *(open)*. An operator could still start G.0 GPU work on Ada before the author answers.
- *Fix:* add to O8 item 1: "GPU work of G.0/G.1b waits for the author's answer to the open item on the Hosts line; licence and repository checks may proceed." Separately, TRACK_G §6 item 2 opens "*(Earlier:" and never closes the parenthesis or the italics. Close both after "(R1-BX-PROPOSED-CONFIRM)".

### Round 2 verdict

All seven MAJOR findings are fixed. MAJOR-7 leaves a MINOR residual (N6).
- Twelve of the fourteen MINOR findings are fixed. MINOR-7 is fixed but has the macOS gap N1. MINOR-6 is only partly fixed.
- The six new findings are MINOR, and each fails safe.
- No command in revision 2 changes cluster or account state. The STOPs and the option A/B gate are in place.
- I recommend applying N1–N5 and the MINOR-6 residual before the prompt is handed to the SSH agent. N1 and N2 in particular can stop option A on a stock Mac.

Verdict: accepted

## Post-round-2 fixes (executing agent, 4 Nov)

N1 (macOS timeout: preamble with `timeout`/`gtimeout` or none, plus SSH ConnectTimeout/ServerAlive), N2 (preamble at the start of every shell call), N3 (`sacct -o`), N4 (`--parsable` id cut at `;`, numeric check, `submit_err.txt`, STOP), N5 (option B spelled out as three commands), N6 (OPERATOR O8 item 1 waits for the Ada answer; TRACK_G §6 item 2 parenthesis closed), MINOR-6 (sinfo and `--test-only` refusals are findings, not STOPs), and the optional OverSubscribe reading note in Q2.
