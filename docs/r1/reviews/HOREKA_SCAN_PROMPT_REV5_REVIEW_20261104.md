# Review — HoreKa 2 read-only scan prompt, revision 5 (4 Nov 2026)

**Reviewer:** an independent agent (Claude), AI-assisted. I reviewed documents only and made no connection to HoreKa or any other cluster. I committed nothing. This file is the only file I wrote in the repository.

**Scope:** `docs/r1/prompts/HOREKA_SCAN_PROMPT_20261104.md` at `c5691d4d` (revision 5), mainly `git diff 88b219d9 c5691d4d`. Revision 5 lets the agent start the session itself, follow a bounded part of the one-time setup, open the tunnel, run the gates and the scan, and end the session.

**Sources checked (WebFetch, 4 Nov):**
- <https://docs.nhr.kit.edu/usage/login/>: the AI-agent rule, SSH keys, 2FA and host names.
- <https://docs.nhr.kit.edu/services/ides/>: `start-vscode-remote-ssh.sh` and the tunnel.
- <https://docs.nhr.kit.edu/usage/login/sshkeys/>: FeLS key management and key validity.
- <https://docs.nhr.kit.edu/usage/slurm/>: the `agent` partition row and the 30 s polling rule.

The script's source and the format of its output are not public. A web search for `start-vscode-remote-ssh.sh` found nothing.

**Local tests.** I ran these on Linux with OpenSSH 9.6p1, using a throw-away `sshd` on 127.0.0.1 with a test key. macOS ships OpenSSH 9.x, and the features below behave the same there, but I did not test on macOS.

| Test | Result |
|---|---|
| `nohup ssh -tt -o BatchMode=yes host script > log 2>&1 < /dev/null &` | Works. A remote pty is allocated (`tty: /dev/pts/0`). Output streams to the log with CRLF line ends. `$!` is the `ssh` PID, because `nohup` execs. The process survived across separate shell calls of this harness |
| `kill` of that PID | The remote script receives SIGHUP |
| A remote `read` under `-tt` with stdin `/dev/null` | It blocks (no EOF reaches the pty). It returned only on its own `-t 8` timeout (rc 142) |
| `BatchMode=yes` on the `-tt` session | It does not affect remote interactivity. It only suppresses client-side prompts |
| `ssh -F snippet -G` with a CRLF snippet | Parses correctly: `\r` is stripped as whitespace |
| The same with no `User` line | `user` falls back to the local user, so Gate 1 STOPs (fail-safe) |
| The same with ANSI colour codes around a value | The codes stay in the value, so Gate 1 STOPs (fail-safe) |
| `-F` with a snippet that holds `StrictHostKeyChecking no` and `UserKnownHostsFile /dev/null` | The command-line `-o UserKnownHostsFile=$S/known_hosts -o StrictHostKeyChecking=accept-new` wins |
| `-F` with no `IdentityFile` | ssh still offers `~/.ssh/id_rsa`, `id_ecdsa`, `id_ed25519` and the rest, plus any ssh-agent keys |
| `ssh -N -L p:…` when local port `p` is already taken | Prints "cannot listen to port", **keeps running** and exits 0 only when killed. With `-o ExitOnForwardFailure=yes` it exits 255 at once |
| `ssh -N -L …` through an existing ControlMaster | The client **exits at once**, so `$!` is dead. The forward lives on in the master, and the port still answers after `kill $!` |
| `ssh-keygen -N '' -f <existing file> < /dev/null` | Asks "Overwrite (y/n)?", reads EOF and exits 1. The file is unchanged (fail-safe) |
| `bash -n` on all 9 bash blocks (tunnel placeholder substituted) and all 9 inline commands (`<that id>` → a number) | All pass |
| `bash -n` on the fix snippets proposed below | All pass |

## Summary

| Class | Count |
|---|---|
| BLOCKING | 1 |
| MAJOR | 3 |
| MINOR | 9 |

**What holds.**
- **The design direction is sound.** The Claude process and its API calls stay on the Mac, and all scan work goes to the compute node through `$SSH`. The session script and the `-N -L` forward are the two commands the IDE page gives a person, and they put the same load on the login node whoever types them. The IDE page itself says the tunnel is how "to run AI agents on a dedicated compute node". It does not say a human must start the script. Starting it from the agent is a reasonable reading, but it is the author's judgement call; it is not a finding.
- **Background session.** `nohup ssh -tt … < /dev/null &` does what the prompt needs: a remote pty, a log, a PID, survival across shell calls, and SIGHUP on `kill`. Slurm's `salloc` releases its allocation on SIGHUP (from the `salloc` man page, from memory). So killing the session `ssh` should end the job, as Ctrl+C would.
- **`$T` is not applied to the session or tunnel.** This is correct: `timeout 600` would cut both after 10 minutes.
- **`BatchMode` on the session `ssh`** does not break the script. A prompt from the script cannot be answered, because stdin is `/dev/null`, but it blocks and then trips the 5-minute STOP. That is fail-safe.
- **`-F $S/vscode_ssh_config` plus command-line `-o`.** The user's `~/.ssh/config` and `~/.ssh/known_hosts` are not touched. The command-line host-key options override whatever the snippet says. A missing `User` or a garbled value makes Gate 1 STOP.
- **Gates 1 and 2 are unchanged from the accepted rev 4.2.** They still run in the right order, before any scan command.
- **Read-only scan, single probe, polling of 5 minutes or more, `sacctmgr modify` forbidden to the agent:** all unchanged.
- **Stale options.** Option B is fully gone, and §0, §6 and §7 no longer refer to it.

**What fails.**
- The one-time-setup exception requires a write on HoreKa from the login node. The prompt elsewhere forbids that and claims it does not happen (BLOCKING-1).
- The tunnel command as printed is likely to fail, or to fail silently (MAJOR-1).
- The teardown cannot reach `scancel`. It can pick the wrong job, and it can kill a reused PID (MAJOR-2).
- The `%L` rule can loop forever (MAJOR-3).

## Findings

### BLOCKING

**BLOCKING-1 — The one-time key setup needs a third login-node command and a `~/.ssh` write on HoreKa. The prompt forbids both elsewhere, and "where the guide says" is open-ended.**
- *Where:* §1 step 2, "One-time setup"; §0, "On the login node you run exactly two things"; §2 rule 3, "No dotfile edits", and "The only files you create on HoreKa are under `~/r1_scan_20261104/`"; the brief's claim that credentials are never handled.
- *Problem:*
  - **Route.** The only way to "install that new public key … on HoreKa" before the tunnel works is a command on the login node, for example `ssh hk2 'cat >> ~/.ssh/<file>' < key.pub`. The compute-node `sshd` cannot be reached until the key is in place. So §0's "exactly two" becomes three, or four with step 1's `true` (MINOR-1).
  - **Target.** The write lands in `~/.ssh` on HoreKa. Rule 3 forbids dotfile edits and any file outside `~/r1_scan_20261104/`. The agent gets two contradictory instructions, and the explicit exception will probably win.
  - **Open-ended scope.** NHR disables self-managed `authorized_keys` for its own `sshd` ("Self-managed `~/.ssh/authorized_keys` files are disabled … All keys are managed centrally through FeLS"). If the guide says "register the key in FeLS", then "where the guide says" covers a web portal. An agent with browser access to the author's logged-in FeLS session could then register a passphrase-less, agent-held key as a 6-month interactive login key for his account. The prompt's STOP list catches "an OTP" but not an already-open browser session.
  - **The key is a credential.** It must be passphrase-less, because the agent cannot type a passphrase under `BatchMode`. It is written under `~/Documents/…`, which macOS may sync to iCloud ("Desktop & Documents Folders"). It sits inside the repository, and `.claude-worktrees/` is not in `.gitignore` on this branch (`git check-ignore` returns nothing). Nothing removes it, or the installed public key, afterwards.
- *Fix (preferred):* keep the one-time setup with the author. It happens once, so revision 5's aim of no per-scan steps for him still holds.
  > **One-time setup.** If the log shows a one-time setup guide, or asks for a key that does not exist, do not follow it. Copy the guide verbatim into the report, end the session (step 5), STOP, and ask the author to do the setup once himself. On the next run the guide no longer applies.

  Then drop the key bullets from step 2, and drop "If you generated a key in step 2…" from step 3.
- *Fix (if the author insists the agent does it):* make the exception exact, and make every other section agree with it.
  - Key: `ssh-keygen -t ed25519 -N '' -C r1-horeka-agent -f "$K/id_vscode_hk2"`, where `K="$HOME/Library/Application Support/r1_horeka_agent"` is created with mode 0700. That is outside `~/Documents` and outside the repository. Never overwrite a key; my test shows `ssh-keygen` refuses without a tty anyway.
  - Install it only into the one file under `~/.ssh` on HoreKa that the guide names for the session `sshd`, with one command: `ssh -S none $OPTS hk2 'umask 077; mkdir -p ~/.ssh && cat >> ~/.ssh/<that file>' < "$K/id_vscode_hk2.pub"`. Never FeLS, never a browser or web portal, never a file the guide does not name.
  - §0: list it as a third login-node command, run once. Rule 3: add it as the one exception to "no dotfile edits". Report: give the key path and fingerprint, and the exact line installed, and tell the author how to remove both.

### MAJOR

**MAJOR-1 — The printed tunnel command will probably fail under `BatchMode`, or keep running without a forward. With a ControlMaster, its PID is dead at once.**
- *Where:* §1 step 3, the tunnel block; step 1, "or to open a master connection with `ssh -fN hk2`".
- *Problem:*
  - **Host.** The printed command names `<user>@hk2-x86-login.scc.kit.edu`, the IDE page's host. The login page lists only `hk2-x86`, `hk2-x86-login1` and `hk2-x86-login2`. The tunnel runs without `-F`, so it reads the author's `~/.ssh/config`, but his `Host hk2` block does not match that host name.
    - His `IdentityFile` for `hk2` may then not be offered.
    - His `~/.ssh/known_hosts` probably has no entry for that name. Under `BatchMode=yes` this gives "Host key verification failed", and the prompt forbids adding the entry.
    - Either way the tunnel exits, Gate 2 gets "connection refused" three times, and the agent STOPs. Revision 4.1 had adopted the review's MINOR-8, to use the `hk2` alias; revision 5 dropped it.
  - **Silent bind failure.** If the local port is already taken, `ssh -N -L` prints "cannot listen to port" and keeps running (tested). The port could be held by the author's own VS Code tunnel, or by a forward left over from an earlier run. Then `$SSH` connects to whatever is listening there. If that is his own `agent` session, Gate 2 passes, because "a running `agent` job of the author's whose node list is that host" is his. The agent would then scan on his session, and step 5 would `scancel` his job (MAJOR-2).
  - **Multiplexing.** If `ssh -N -L` goes through a ControlMaster, which step 1 explicitly offers, the client exits at once. `tunnel.pid` is then a dead PID, and the forward lives on in the author's master after step 5 (tested: the port still answers after `kill`).
  - **Key validity.** NHR interactive keys "are only valid for one hour after the last 2-factor login". The tunnel, and any restart, must authenticate within that hour.
- *Fix:* run the documented forward through the alias that step 1 has just verified, without multiplexing, and fail loudly.
  ```bash
  P=<port>; N=<node>            # from the printed tunnel command
  lsof -nP -iTCP:"$P" -sTCP:LISTEN >/dev/null 2>&1 && { echo "STOP: local port $P already in use"; exit 1; }
  nohup ssh -S none $OPTS -o ExitOnForwardFailure=yes -N -L "$P:$N:$P" hk2 > "$S/tunnel.log" 2>&1 < /dev/null &
  echo $! > "$S/tunnel.pid"
  ```
  - In the next call: `ps -p "$(cat "$S/tunnel.pid")" -o command= | grep -q -- "-L $P:" || { echo "STOP: tunnel not running"; cat "$S/tunnel.log"; exit 1; }`.
  - Use `-S none` in step 1's check (`ssh -S none $OPTS hk2 …`) and in step 2's session `ssh`. Drop the "master connection" alternative from step 1: the activated key is then the only path.
  - Check that the snippet's `Port` equals `$P`, else STOP.
  - Say in §0 that this is the docs' tunnel command, with the login host given as the `hk2` alias.

**MAJOR-2 — Teardown: `scancel` is unreachable, the job id is ambiguous on a shared node, and `kill` trusts PID files.**
- *Where:* §1 step 5.
- *Problem:*
  - **Order.** Step 5 kills the tunnel first, and then runs `$SSH "scancel …"` "if `$SSH` still answers". `$SSH` goes through that tunnel, so it never answers, and the `scancel` is dead code.
    - Normally this does not matter, because killing the session `ssh` sends SIGHUP and `salloc` releases the job.
    - But if the script detaches the job (for example `sbatch` plus `sshd`), the job keeps running. The `agent` partition allows `time=3-00:00:00`, so a forgotten one-core job could run for up to 3 days on the project's account. The agent cannot check from the Mac, because a login-node `squeue` is forbidden.
  - **Which job.** "The `agent` job id you recorded in `preflight.txt`" is not well defined. Gate 2's `squeue -u $USER -p agent` lists all the author's running `agent` jobs. The partition is "Shared" with one core per job, so his own VS Code or agent session can sit on the same node. Once the order is fixed, the agent could cancel his session. With MAJOR-1's bind failure, it would cancel exactly his session.
  - **PIDs.** `kill "$(cat …)"` kills whatever process now holds that PID. About an hour later, or after a dead ControlMaster client, that may be an unrelated process of the author's.
- *Fix:*
  - In step 2, record the session's job id from `session.log` (for example a line like `Granted job allocation <id>`, or the id the script prints) into `$S/session_job.txt`.
  - Gate 2 passes only if that id is the one row with `%N` equal to `$h`. If no id is printed, Gate 2 passes only if exactly one row is on `$h`; otherwise STOP.
  - Step 5, in this order:
    ```bash
    J=$(cat "$S/session_job.txt" 2>/dev/null)
    [ -n "$J" ] && grep -qE '^[0-9]+$' "$S/session_job.txt" && $SSH "scancel $J"
    for f in tunnel session; do
      p=$(cat "$S/$f.pid" 2>/dev/null) || continue
      ps -p "$p" -o command= | grep -qE 'start-vscode-remote-ssh\.sh|-N -L ' && kill "$p"
    done
    ```
  - The `scancel` from inside the session ends that session, which is expected.
  - In the report, state whether `scancel` ran. If it did not, write: "release of job `<id>` not verified; please check `squeue -u ka_ir7683 -p agent`".

**MAJOR-3 — The `%L` rule can loop without end. Each loop is another login-node session start, and each new session STOPs on its own host key.**
- *Where:* §1 step 4, "If it is under about 75 minutes, end the session (step 5) and start a fresh one"; §2 rule 2, "about one core for about an hour".
- *Problem:*
  - The prompt itself expects the session job to last "about an hour". If the script's default time limit is 75 minutes or less, which is unknown and not documented, every fresh session is again under the threshold. Each restart is a new script run on a login node and a new `agent` job. There is no bound.
  - Revision 4.2 said "ask the author" here; revision 5 replaced that with an automatic restart.
  - Each fresh session also meets a stale `[localhost]:<port>` entry in `$S/known_hosts` from the last session, so it STOPs on "REMOTE HOST IDENTIFICATION HAS CHANGED" (MINOR-5). A rerun may also print no snippet (MINOR-3).
- *Fix:*
  > Never start a second session in one run. Record `%L`. If `%L` is under 15 minutes, end the session and STOP. Otherwise go on, but cap the §4 status checks at `min(9, floor((%L − 15 min) / 5 min))`. If the session ends before the fetch, the existing §7 rule applies: no login-host fallback; report the job id.

  Remove "start a fresh one" from step 4.

### MINOR

**MINOR-1 — Step 1's `ssh $OPTS hk2 true` is itself a login-node command.**
- *Where:* §1 step 1; §0, "exactly two things"; §2 rule 1.
- *Problem:* `true` runs in a shell on a login node. It is trivial, but it makes §0's "exactly two" untrue.
- *Fix:* either list it in §0 ("plus one `true` to check that the key works without a prompt"), or drop it. If dropped, a `BatchMode` failure of step 2's session `ssh` gives the same signal in `session.log`, with "Permission denied" and no job.

**MINOR-2 — Revision 5 dropped the tool-timeout line, and gives no way to wait.**
- *Where:* the preamble paragraph. Revision 4.2 had "Set your own tool timeout above 600 s for these calls"; revision 5 removed it.
- *Problem:*
  - Claude Code's Bash tool defaults to 2 minutes. The query call (`timeout 600`; `module spider` on a cold Lmod cache, and 4 × 10 s of `curl`) can be cut part-way, which leaves a partial `query_scan.txt`. Rule 1 allows only one query call.
  - Steps 2 and 4 ("wait 30 s") and the 5-minute status checks need waits. Some harnesses block a long foreground `sleep`.
  - In this harness, `nohup … &` survived across calls. Claude Code may still reap background children when its session or turn ends.
- *Fix:* add:
  > Set your tool timeout to at least 660 s for `$SSH` calls. Wait with your harness's own background or monitor facility, not a long foreground `sleep`. If your harness offers a run-in-background option, use it for the session and the tunnel, and still record their PIDs. Do not end your turn while the session is open, except at a STOP after step 5.

**MINOR-3 — Snippet parsing: the format is undocumented, so build the file from extracted values instead of copying it verbatim.**
- *Where:* §1 step 3, "Copy the printed snippet **verbatim**".
- *Problem:*
  - Under `-tt`, the log has CRLF line ends. `ssh_config` tolerates them (tested). It does not tolerate ANSI colour codes, which a script may print when it sees a tty (tested: Gate 1 then STOPs).
  - The snippet may lack `User`. Under `-F` the user then falls back to the local Mac user, and Gate 1 STOPs (tested).
  - It may name an `IdentityFile` that does not exist on the Mac.
  - Per the IDE page, the snippet is part of the "one-time setup guide", so a later run may not print it at all. Step 2's "no snippet after 5 minutes" would then STOP a session that works.
  - If the log ends in a question, the script is waiting on a stdin that cannot answer (tested: `read` blocks).
- *Fix:*
  - Clean the log first: `sed -e $'s/\x1b\\[[0-9;]*[A-Za-z]//g' "$S/session.log" | tr -d '\r' > "$S/session_clean.log"`.
  - Write `$S/vscode_ssh_config` from the snippet's `Host`, `HostName`, `Port`, `User` and `IdentityFile` values only. Add `User ka_ir7683` if it is missing. Add `IdentitiesOnly yes` (MINOR-4). Keep the printed text verbatim in the report, and note any line you changed.
  - If no snippet is printed but `$S/vscode_ssh_config` exists from an earlier run, reuse it; Gate 1 still checks it.
  - If the log ends in a prompt or question, STOP and quote it.

**MINOR-4 — Under `-F`, ssh still offers the author's default keys and his ssh-agent keys to the compute-node `sshd`.**
- *Where:* the preamble's `$SSH`.
- *Problem:* with no `IdentityFile`, or alongside one, ssh tries `~/.ssh/id_ed25519` and the other default files, plus every key loaded in ssh-agent (tested with `ssh -G`). This is not a leak, since public-key authentication reveals no secret. But it is wider than needed, and it runs against the spirit of "never read the author's `~/.ssh/*` key files".
- *Fix:* add `IdentitiesOnly yes` and the session's `IdentityFile` to `$S/vscode_ssh_config` (MINOR-3).

**MINOR-5 — `$S/known_hosts` is shared across sessions, so any later session STOPs on a changed key.**
- *Where:* the preamble; §1 step 4, last bullet.
- *Problem:* every session sits at `[localhost]:<port>`. A new node, or a new per-session host key, under the same port gives "REMOTE HOST IDENTIFICATION HAS CHANGED". That is a STOP on every later run, and on any restart.
- *Fix:* key the file to the session, for example `-o UserKnownHostsFile=$S/known_hosts.$(cat "$S/session_job.txt")`. Or, at step 2, move an old `$S/known_hosts` aside to `known_hosts.prev`; it is the agent's own file. Within one session, keep the STOP on a changed key.

**MINOR-6 — Stale and duplicated text.**
- §3, line 203: "Option A does not measure the login node's network." Option A no longer exists. Fix: "The login node's network is not measured: Q8's login-node part is 'not measured'."
- §3 go/no-go: "If either fails, do not submit. Do not submit; report it as a finding." Fix: "If either fails, do not submit; report it as a finding."
- §2 rule 3: "SSH may update `known_hosts`". It is now `$S/known_hosts` only, and `~/.ssh/known_hosts` must not change. Fix: "SSH adds the compute node's key to `$S/known_hosts`."
- §7: "more than one account with no choice made". §3 now always STOPs on more than one account, because there is no earlier choice. Fix: "more than one account (STOP and ask)".
- §7, session ends: "its output stays … for a later fetch". It does not say who fetches. Fix: "The author fetches it himself; you never fall back to a login host."

**MINOR-7 — The STOP list does not match the steps.**
- *Where:* §7 against §1.
- *Problem:* §1 has STOPs that §7 does not list:
  - step 1, host or user differs;
  - step 2, no snippet after 5 minutes;
  - step 2, the account error;
  - step 2, the guide asks for anything else;
  - step 3, a tunnel command that does not match the expected form;
  - step 4, connection refused after 3 retries;
  - step 4, "REMOTE HOST IDENTIFICATION HAS CHANGED".

  §7 also does not say that a STOP after step 2 first runs step 5.
- *Fix:* add one bullet for each of these. Add the new STOPs from BLOCKING-1 and MAJOR-1 to MAJOR-3: one-time setup needed, local port in use, tunnel not running, ambiguous session job, `%L` under 15 minutes. Then add a lead line: "On any STOP after step 2, run step 5 first."

**MINOR-8 — The account error loses revision 4.1's log-out note.**
- *Where:* §1 step 2, "Account error".
- *Problem:* the Slurm page says that after `sacctmgr modify user … set defaultaccount=…` you must log out and back in. The STOP message should tell the author so. Otherwise the next run fails again, if he has an open master connection.
- *Fix:* "…STOP and ask him which project. Tell him the command is his, `sacctmgr modify user $USER set defaultaccount=<project>`, and that he must then log out and back in."

**MINOR-9 — Rule 1's call list does not count the new calls.**
- *Where:* §2 rule 1.
- *Problem:* the list names the query, the submit, up to 9 checks and the fetch. Gate 2, its up to 3 retries and the teardown `scancel` are missing.
- *Fix:* "Gate 2 (at most 4 tries), the query, the submit, at most 9 status checks, the fetch, and one `scancel` of the session job."

## Checklist against the request

| Check | Result |
|---|---|
| 1. Login node used only for the two documented commands | **No.** Step 1's `true` (MINOR-1). The key install in the one-time setup (BLOCKING-1). Unbounded session restarts (MAJOR-3). A forward left on a ControlMaster after teardown (MAJOR-1). With the fixes, it is the script and the forward, plus at most `true` |
| 2a. `nohup ssh -tt … &` for an interactive script | Works (tested): pty, log, PID, survives separate calls, SIGHUP on `kill`. Prompts cannot be answered and block (fail-safe). Harness reaping and timeouts: MINOR-2 |
| 2b. Parsing an undocumented snippet | Fragile but fail-safe through Gate 1: CRLF is OK, ANSI codes and a missing `User` STOP, and the snippet may be printed only once. MINOR-3 |
| 2c. `ssh -F` drops `~/.ssh/config` | The snippet resolves if it carries `HostName`, `Port` and `User`. Without `User`, Gate 1 STOPs. The command-line host-key options win (tested). The tunnel does **not** use `-F`, but it does not match the `hk2` alias either, so its key and host key are probably missing under `BatchMode`. MAJOR-1 |
| 2d. `BatchMode` on the session `ssh` | Does not break the script's interactivity (tested). It only removes client prompts |
| 3a. Key-generation exception | Not bounded enough. It conflicts with §0 and rule 3, and leaves a passphrase-less key in `~/Documents`, inside the repository. BLOCKING-1 |
| 3b. `accept-new` into a private `known_hosts` | Acceptable for a localhost endpoint behind Gate 2. It needs the bind check of MAJOR-1, and a per-session file (MINOR-5) |
| 3c. Kill only its own PIDs | Not ensured: PID files are trusted, and a ControlMaster client PID is dead at once. MAJOR-1, MAJOR-2 |
| 3d. `scancel` only its own job | Unreachable as written. Once reachable, it is ambiguous on a shared node. MAJOR-2 |
| 3e. Never editing `~/.ssh/config` | Held. `~/.ssh/known_hosts` is also untouched. On HoreKa, `~/.ssh` *is* written by the key install (BLOCKING-1) |
| 3f. Credentials never handled | Passwords and OTPs: held. A newly generated private key: not held (BLOCKING-1) |
| 4a. No stale option A or B references | One remains, at line 203 (MINOR-6) |
| 4b. STOP list matches the steps | No (MINOR-7) |
| 4c. `bash -n` on every block, placeholders substituted | All 9 blocks and all 9 inline commands pass |

## Verdict

Revision 5's mechanics mostly work: the background `-tt` session, `-F` with command-line overrides, and both gates. But one BLOCKING finding remains. The one-time-setup exception lets the agent write a credential on HoreKa through a login-node command, which the prompt's own §0 and rule 3 forbid, and it leaves a passphrase-less key in `~/Documents`. The simplest fix is to hand that one-time step back to the author. Three MAJOR findings would make a real run fail or misbehave:
- the tunnel's host, key and bind handling (MAJOR-1);
- the order and target of the teardown (MAJOR-2);
- the unbounded `%L` restart (MAJOR-3).

Fix these four before giving the prompt to the agent on the Mac. MINOR-2, MINOR-3 and MINOR-7 are worth doing at the same time.

Verdict: not accepted (1 BLOCKING, 3 MAJOR, 9 MINOR)

## Fixes applied (executing agent, 4 Nov) — revision 5.1

BLOCKING-1: key setup and the fresh-2FA hour are the author's (§0); on an undone setup guide the agent ends the session and STOPs. MAJOR-1: tunnel via `hk2` with `-S none`, `ExitOnForwardFailure=yes`, a free-port check and ps/lsof checks; master-connection option dropped. MAJOR-2: job id from session.log; scancel first, then kill only matching PIDs; teardown check. MAJOR-3: no restarts; status checks fitted to %L. MINOR-1 (no `ssh hk2 true`), -2 (timeouts, background waiting), -3 (config built from snippet values, CR/ANSI stripped), -4 (IdentitiesOnly), -5 (per-session known_hosts), -6 (stale text), -7 (STOP list per step, step 5 first), -8 (log out and back in), -9 (call budget).
