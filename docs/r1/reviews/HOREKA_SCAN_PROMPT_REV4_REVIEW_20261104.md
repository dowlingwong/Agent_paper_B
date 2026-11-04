# Review — HoreKa 2 read-only scan prompt, revision 4 (4 Nov 2026)

**Reviewer:** an independent agent (Claude), AI-assisted. I reviewed documents only. I made no SSH connection, contacted no cluster, and committed nothing. This file is the only one I wrote.

**Scope:** `docs/r1/prompts/HOREKA_SCAN_PROMPT_20261104.md` at `0f53c0dd` (revision 4), mainly the diff against the accepted revision 2 (`9adf179f`). For propagation only, I also read the three companion edits in the same commit: the STATUS line, the OPERATOR HoreKa 2 row, and the draft §4 update box.

**Sources checked (WebFetch, 4 Nov):**
- <https://docs.nhr.kit.edu/usage/login/>: the AI-agent admonition, the login-node rules and the host names.
- <https://docs.nhr.kit.edu/services/ides/>: `start-vscode-remote-ssh.sh`, the tunnel, and the `agent` default.
- <https://docs.nhr.kit.edu/usage/slurm/>: the partition table, the `agent` partition, the dev limits, the 30-second polling rule and `sinfo`.

A direct `curl` of docs.nhr.kit.edu was refused by this sandbox's egress proxy. The quotations below therefore come from WebFetch extracts. The script's source is not public; a web search found nothing.

**Local tests:**
- `bash -n` on all four bash blocks: the preamble, the preflight, `scan_queries.sh` and `probe.sh`. All four pass.
- `bash -n` on every inline command, with `<id>` replaced by a number. All pass.
- A fake-`ssh` expansion test of `$SSH` with `$T` empty. The arguments come out as intended: `[-o][BatchMode=yes]…[vscode-hk2][hostname; echo "job=$SLURM_JOB_ID …"]`. The remote string stays single-quoted, so it expands on the remote side.
- A simulation of the gate proposed in MAJOR-2. It passes a localhost:22222 config and stops on a login host and on a ProxyJump.

## Summary

| Class | Count |
|---|---|
| BLOCKING | 0 |
| MAJOR | 3 |
| MINOR | 9 |

**What holds.**
- **Compliance design.**
  - The agent never runs on a login node itself. The author runs `start-vscode-remote-ssh.sh` and the tunnel; the prompt says "never run them yourself". All agent commands go to `vscode-hk2`.
  - This matches the IDE page: the script "submits an interactive Slurm job, starts an unprivileged `sshd` on the allocated compute node". Without arguments it uses the `agent` partition. You then forward with `ssh -N -L 22222:<node>:22222 …` and connect to the printed `vscode-hk2` host. The page adds that "Login nodes cannot be used as proxy jump hosts".
  - The Claude Code process and its API calls stay on the Mac. The login node only carries the encrypted port forward, the same pattern the docs give for IDEs. Nothing the login page lists ("running AI agent processes, API calls, or similar interactive workloads on login nodes") happens on a login node under option A.
- **Fail-safe direction of the preflight.** On a login node, `SLURM_JOB_ID` is empty in a non-interactive SSH session, so the current check STOPs. A wrong host therefore stops the scan; it cannot let it pass. The weaknesses are in feasibility and in defence in depth (MAJOR-1 and MAJOR-2), not a hole.
- **Polling.** Status checks run at most once every 5 minutes. That is well above the 30-second minimum on the Slurm page ("Do not use time intervals smaller than 30 seconds") and the OPERATOR row's once a minute.
- **Read-only safety.** Rev 4 adds one remote command, the preflight `hostname; echo …`. It adds no write.
  - The `sacctmgr modify` in §1 step 1 is the author's own action. It is not in the agent's command set, and rule 3 still forbids it for the agent.
  - The only files created on HoreKa are still `~/r1_scan_20261104/{probe.sh,probe-<id>.out}`.
- **Budget.** Still exactly one 15-minute 1-GPU `dev-gpu-h100` job (0.25 GPU-h), never resubmitted, never moved to another partition. The author's `agent` session adds one core for about an hour (see MINOR-4).
- **STOPs.** All revision-2 STOPs remain, including the MINOR-6 wording that refusals from `sinfo` and `--test-only` are findings, not STOPs. Rev 4 adds the right new one: a login node, no job, or the session ending.
- **Single core is enough for the query script.** It makes about 30 light Slurm, Lmod, `df` and `curl` client calls. The `curl` calls are capped at 10 s each, and the whole call at 600 s. Its output streams to `query_scan.txt`, so a timeout keeps partial results. The Slurm page lists `mem-per-cpu=1945mb` for `agent`, which is ample. The only slow step could be `module -t spider` when the Lmod cache is cold, and the 600 s cap covers it.
- **Slurm clients from an `agent` job.** No page says that `sacctmgr`, `sreport`, `scontrol` or `sbatch` work from compute nodes. The Slurm page does say the `agent` partition is "for AI agent workloads", and its polling rule addresses automated tools that call Slurm. Both imply that Slurm client calls from agent jobs are expected.
  - Missing tools or a `slurmdbd` refusal are findings under rule 4. They are not STOPs, and they cannot cause harm.
  - Submitting from the node can still be blocked by the partition's `AllocNodes` (MINOR-3).
- **`ssh -G` fields.** `ssh -G` prints lowercase keys and always prints `hostname`, `port` and `user`. It prints `proxyjump` and `proxycommand` only when they are set. The grep therefore picks the right lines, and if the snippet uses `HostName localhost`, `Port <n>` and `User ka_ir7683`, it shows exactly those. The check needs an action, though (MAJOR-2).
- **Account note.** The IDE page confirms the multi-project failure ("you must set a default Slurm account with `sacctmgr`, or `salloc` and the script will fail"). The prompt leaves that choice and command to the author.
- **Shell syntax.** `bash -n` is clean for all four blocks and every inline command. The `$shape` loop, the `main … </dev/null` wrapper and the `cut -d';'` and numeric checks are unchanged from the accepted revision.

**What fails.**
- The preflight's positive test, that `SLURM_JOB_ID` is set in the SSH session, will probably fail on a correct agent node. The host-name test is unspecified (MAJOR-1).
- The `ssh -G` check has no pass or fail action, and the host-name override can point `$SSH` at a login host (MAJOR-2).
- The session steps omit the script's one-time key setup and the host-key acceptance. Under `BatchMode=yes`, the first `$SSH` call then fails (MAJOR-3).

## Findings

### MAJOR

**MAJOR-1 — The preflight's positive test probably fails on a correct agent node, and the login-node test is unsound.**
- *Where:* §1 preflight, second command, and its first bullet; §7 first bullet.
- *Problem:*
  - The check requires that "a job id is set", read from `$SLURM_JOB_ID` and `$SLURM_JOB_PARTITION` inside the SSH session. But OpenSSH's `sshd` does not hand its own environment to the sessions it starts. A session gets a fresh environment: `USER`, `HOME`, `PATH`, `SHELL`, `SSH_*`, plus `SetEnv` or `~/.ssh/environment` only if the daemon is configured for them.
  - The `SLURM_*` variables of the job that started `sshd` are therefore absent, unless `start-vscode-remote-ssh.sh` injects them explicitly. The IDE page does not say that it does: it "doesn't list any `SLURM_*` variables or other session environment variables", and the script's source is not public.
  - The likely result is `job= partition=` on the correct compute node, a STOP, and option A that never runs.
  - "The host name is not a `login` host" names no test. The real login-node host names are not documented, and the agent cannot rely on the string `login` appearing in `hostname`. Legacy HoreKa's login nodes, for example, were `hkn199x`.
- *Fix:* replace the second command with a Slurm-side check that works whether or not the variables reach the session. Run it only after the gate in MAJOR-2:
  ```bash
  $SSH 'h=$(hostname -s); echo "host=$h job_env=${SLURM_JOB_ID:-unset}"; scontrol show node "$h" 2>&1 | grep -oE "(NodeName|Partitions|State)=[^ ]*"; squeue -h -u "$USER" -p agent -t R -o "%i %N %L" 2>&1' > "$S/preflight.txt" 2>&1
  ```
  - *Pass* only if `scontrol show node` finds `$h` with `Partitions=` containing `agent`, and `squeue` lists one running `agent` job of the author's whose node list is `$h`. A login node is not a Slurm compute node, so `scontrol` answers "Node … not found" there.
  - Otherwise STOP.
  - Record `job_env` as a finding. It is not part of the decision.
  - `%L` gives the session's remaining time, which MINOR-2 uses.

**MAJOR-2 — The `ssh -G` check is not a gate, and the host-name override can aim `$SSH` at a login node.**
- *Where:* §1, step 4 ("He tells you the host name of the snippet…"); the preamble's "replace `vscode-hk2` if he named another host"; the preflight's first line.
- *Problem:*
  - The `ssh -G` line carries only a comment, "expect the tunnel … and ka_ir7683". Revision 2's "If the host name or user differs, STOP" was dropped, and no bullet says what to do if the check fails.
  - The second preflight command therefore runs remotely whatever `ssh -G` showed. Suppose the author names `hk2`, or a snippet resolves to a login host or uses a `ProxyJump`. Then the agent's first remote command, and with a weak check possibly more, would run on a login node: exactly what §0 forbids.
  - Today only the `SLURM_JOB_ID` test catches this, and MAJOR-1 asks to replace that test.
  - The `ssh -G` check is the one test that needs no remote command, so it should be the gate.
- *Fix:* make it a hard gate before any `$SSH` call:
  ```bash
  ssh -G vscode-hk2 | grep -E '^(hostname|port|user|proxyjump|proxycommand) ' > "$S/ssh_G.txt"
  grep -qxE 'hostname (localhost|127\.0\.0\.1|::1)' "$S/ssh_G.txt" \
    && grep -qx 'user ka_ir7683' "$S/ssh_G.txt" \
    && ! grep -qx 'port 22' "$S/ssh_G.txt" \
    && ! grep -qE '^(proxyjump|proxycommand) ' "$S/ssh_G.txt" \
    || { echo "STOP: vscode-hk2 is not the local tunnel endpoint"; exit 1; }
  ```
  - I tested this gate locally. It passes `localhost` / `22222` / `ka_ir7683`. It stops on `hk2-x86.scc.kit.edu:22`, and on `localhost` with `proxyjump hk2`.
  - Add to step 4: "Never accept `hk2`, any `*.scc.kit.edu` name or any login host as the session host."
  - Add to §7: "`ssh -G` does not show a localhost tunnel endpoint."

**MAJOR-3 — The one-time key setup and the host-key acceptance are missing, so the first `BatchMode` call fails.**
- *Where:* §1, steps 1–4.
- *Problem:*
  - The IDE page says the script's output includes "a one-time setup guide (SSH key generation, `~/.ssh/config` snippet)". The page also says the node and port are "session-specific". Step 2 mentions only the config snippet.
  - The compute-node `sshd` is new. It has its own host key and sits at `[localhost]:<port>`. With the default `StrictHostKeyChecking` and `BatchMode=yes`, an unknown key gives "Host key verification failed".
  - A changed key gives "REMOTE HOST IDENTIFICATION HAS CHANGED". That happens with a new node or session on the same port.
  - In either case the preflight fails. The agent then cannot tell whether to "ask the author" (connection refused) or STOP ("fails for authentication"). If key setup is incomplete, the call fails or prompts the same way.
  - The IDE page's own verification step ("simply type `ssh vscode-hk2` in a local terminal") is also not among the author's steps.
- *Fix:*
  - Step 2: "Follow the script's printed one-time setup (SSH key generation) and add its config snippet."
  - Add a step 3b: "In a local terminal, run `ssh vscode-hk2 hostname` once yourself. Check the host key against the script's output if it shows one, and accept it. Then check that `ssh -o BatchMode=yes vscode-hk2 true` returns without any prompt."
  - In the preflight bullets: "A host-key or authentication failure: ask the author to repeat step 3b. Never edit `known_hosts` or `~/.ssh/config` yourself."

### MINOR

**MINOR-1 — The §0 quotation is not verbatim, and the paraphrase has propagated.**
- *Where:* §0. The same paraphrase appears in the STATUS line ("Agents should run on a compute node through the SSH tunnel") and in the draft §4 update box.
- *Problem:* the login page's admonition has this title and text:
  - Title: **"Interactive AI agent usage on login nodes is prohibited."**
  - Body: "Interactive use of AI agents (such as ChatGPT, Claude, or similar tools) on login nodes is not allowed. This includes running AI agent processes, API calls, or similar interactive workloads on login nodes. … Use the SSH tunnel to compute nodes to run AI agents on a dedicated compute node instead."
  - The prompt shows "…is prohibited. Agents should run on a compute node through the SSH tunnel described at …" in quotation marks, but that sentence is not on the page. The link anchor `#ssh-tunnel-to-compute-nodes` is correct.
- *Fix:* quote the title and the two operative sentences as above, in §0, STATUS and the draft box. The rule is unchanged, but this record quotes sources verbatim.

**MINOR-2 — The session's lifetime and what to do when it ends are not set.**
- *Where:* §1 step 1; §7 first bullet.
- *Problem:*
  - The IDE page states no time limit for the session job. The scan needs up to about an hour: the query, a submit, 9 × 5-minute checks and the fetch.
  - If the session ends after the probe is submitted, the probe still runs. The prompt then only says STOP, and nothing stops an agent from "helpfully" retrying through `ssh hk2`, a command that appears verbatim in option B.
- *Fix:*
  - The preflight's `%L` (MAJOR-1) prints the remaining time. If it is under about 75 minutes, ask the author before §3.
  - Add to §7: "If the session ends, never fall back to `hk2` or any login host. Tell the author the job id and give him option B step 3 to fetch the output."

**MINOR-3 — Submission from the `agent` node can be blocked by `AllocNodes`. Use §3's own evidence as the go or no-go, and offer the author a fallback.**
- *Where:* §3 "After it runs, before §4"; §4 "Copy and submit".
- *Problem:*
  - Slurm partitions have an `AllocNodes` list: the nodes allowed to submit, `ALL` by default. If `dev-gpu-h100` restricts it to login nodes, the submission from the agent node is refused.
  - The prompt then STOPs (correct, and fail-closed), but the GPU probe is lost.
  - §3 already prints `scontrol show partition dev-gpu-h100` (which includes `AllocNodes=`) and an `sbatch --test-only -p dev-gpu-h100 …` line from the same node. The prompt does not use either one.
- *Fix:*
  - Add before §4: "If section 4 shows `AllocNodes` for `dev-gpu-h100` other than `ALL`, or the section 7 `dev-gpu-h100` test-only line is refused, do not submit. Report it, and offer the author option B step 2 for the probe alone."
  - Q11 is also answered directly under option A: the agent session is itself a job. Note this in the report.

**MINOR-4 — "Exactly one short job" and the `dev-*` STOP do not account for the session job.**
- *Where:* §2 rule 2; §3 "If the author already has a job in a `dev-*` partition"; §3 sections 7 ("my jobs") and 11.
- *Problem:*
  - Under option A, "my jobs" and `sacct` will always list the author's `agent` job, and rule 2 reads as if no other job of his may exist.
  - The STOP is worded for `dev-*`, so it is correct. But an agent may hesitate over the `agent` row, or report it as a surprise.
  - The session also costs one core-hour or so on the project account. That belongs in the budget statement.
- *Fix:*
  - Rule 2: "Exactly one job of your own (the probe). The author's `agent` session job is expected; it appears in 'my jobs' and `sacct`. It is not a `dev-*` job, and not a STOP."
  - §0 option A: "plus the author's 1-core `agent` session for about an hour".

**MINOR-5 — The default-account step is incomplete.**
- *Where:* §1 step 1.
- *Problem:*
  - The Slurm page says that after `sacctmgr modify user $USER set defaultaccount=…`, you must log out and back in for the change to take effect fully. The prompt does not say so.
  - The script may also accept `--account=<project>`. The IDE page shows `--partition` and `--gres` being passed through to the job, but it does not confirm `--account`. That would avoid a persistent change.
  - If the author sets a default for this session, §3's "more than one account → STOP and ask" fires anyway.
- *Fix:*
  - Add the logout-and-back-in note.
  - Add "(alternatively, if the script accepts it, `start-vscode-remote-ssh.sh --account=<project>`; unverified)".
  - In §3: "If he already chose an account in §1, use it, and quote his choice."

**MINOR-6 — Under option A, nobody measures the login node's network any more, but staging is planned there.**
- *Where:* §3 section 10 and Q8; draft §6 item 6 (`hk2_stage.py`, "run by the author on the login node").
- *Problem:*
  - Revision 2's Q8 measured network from the login node and the compute node, because "Where staging must happen" depends on it.
  - Rev 4 measures the agent node and the GPU node. Under option A, the login node, where the draft stages, goes unmeasured.
- *Fix:* choose one.
  - Add to the author's session steps one line he runs himself on the login node: `for u in https://huggingface.co https://pypi.org/simple/ https://github.com; do printf '%s ' "$u"; curl -sI -m 10 -o /dev/null -w '%{http_code}\n' "$u"; done`.
  - Or have Q8 state "login node: not measured (option A)".

**MINOR-7 — Option B is not consistent with the rest of the prompt.**
- *Where:* §0 option B; §3 section headers 9 and 10; Q7 and Q8; §4 final fetch.
- *Problem:*
  - (a) The three commands use `"$S/…"`, but `$S` is not set in the author's own terminal. As written, `< "$S/scan_queries.sh"` reads `/scan_queries.sh`.
  - (b) Steps 1 and 2 run back to back. The §3 checks never run before the probe is submitted: an existing `dev-*` job, or more than one account with `--account` chosen. A multi-project probe may be refused, or charged to the wrong default account.
  - (c) Step 3 fetches only the `.out` file. It has no `sacct` line and no check that the job finished, unlike §4.
  - (d) Under option B, the query script runs on a login node, but its sections 9 and 10 are headed "on the agent node", and Q8 asks about "the agent-partition node". The report would mislabel login-node results.
  - Option B's own compliance is consistent: a person on the login node may run "batch commands such as `sbatch`, `salloc`, and `squeue`" and "short pre- and post-processing runs on a few cores". The agent runs nothing there.
- *Fix:*
  - (a) Give the author the three commands with the absolute path expanded.
  - (b) Split option B into two hand-offs. After step 1 he hands back `query_scan.txt`. The agent applies the §3 checks, finalises `probe.sh`, and only then gives step 2.
  - (c) Make step 3 the same as the §4 final call (`sacct … ; cat …`), to run once `squeue -j <id>` shows nothing.
  - (d) In §6: "Under option B, sections 9 and 10 and Q7 and Q8 describe the login node; label them so."

**MINOR-8 — The tunnel command may ask for an OTP a second time.**
- *Where:* §1 step 3.
- *Problem:*
  - The printed tunnel command addresses a full login host. The IDE page shows `username@hk2-x86-login.scc.kit.edu`; the login page lists `hk2-x86.scc.kit.edu` and `…-login1` and `…-login2`. That host may not match the author's `hk2` alias, its `ControlMaster` or its key, so it can prompt for an OTP again.
  - Any login node can forward to `<node>:<port>`, so the host choice does not matter for the forward.
- *Fix (optional):* "You may instead run `ssh -N -L <port>:<node>:<port> hk2`, which reuses your existing `hk2` connection."

**MINOR-9 — Small text issues.**
- §0 says "about 12 non-interactive SSH calls". The new remote preflight makes it 13: preflight, query, submit, up to 9 checks, fetch.
- §7 has a blank line after its first bullet, which splits the list in two.
- §1 step 1 says the job starts "usually immediate". The IDE page says it "usually starts immediately", so this is fine; it is not a guarantee, and the prompt should not be read as one.

## Checklist against the request

| Check | Result |
|---|---|
| Tunnel workflow matches the docs | Yes. The script runs on the login node, by the author; the job goes to `agent` by default; the tunnel is `-L`, with no ProxyJump; the session host is `vscode-hk2`. Missing: the one-time key setup and the verification step (MAJOR-3) |
| Login-node detection sound | Fail-safe, but the positive test is probably wrong (MAJOR-1). There is no pre-execution gate (MAJOR-2) |
| Any step still on a login node | None by design. A wrong session host lets one preflight command reach a login node (MAJOR-2). A retry through `hk2` after the session ends is not forbidden explicitly (MINOR-2) |
| `sacctmgr`, `sreport`, `scontrol` and `sbatch` from an `agent` job | Not documented. Expected to work, and a failure is a harmless finding. `sbatch` may hit `AllocNodes` (MINOR-3) |
| One core enough | Yes, with 1945 MB per CPU and the 600 s cap |
| `ssh -G` fields | The right fields; the action is missing (MAJOR-2) |
| Dev GPU job from inside the agent job | Normally yes. Gate it on §3's test-only and `AllocNodes` (MINOR-3) |
| Read-only safety, budget, STOPs | Intact. The budget wording should mention the session job (MINOR-4) |
| `bash -n` | All 4 blocks and all inline commands pass |
| Option B consistency | Compliant, but the paths, the sequencing, the fetch and the labelling need fixing (MINOR-7) |

## Verdict

There are no BLOCKING findings: no step in revision 4 lets the agent change cluster state or work from a login node unchecked. Three MAJOR findings make option A likely to stop at its preflight, or lean on a weak gate. MAJOR-1 is the job check through environment variables. MAJOR-2 is that `ssh -G` is not a gate. MAJOR-3 is the missing key and host-key setup. Fix those three, and preferably MINOR-2, MINOR-3 and MINOR-7, before handing the prompt to the agent on the Mac.

Verdict: not accepted (0 BLOCKING, 3 MAJOR, 9 MINOR)
