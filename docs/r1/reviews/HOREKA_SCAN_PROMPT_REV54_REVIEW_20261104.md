# Review — HoreKa 2 read-only scan prompt, revision 5.4 (4 Nov 2026)

**Reviewer:** an independent agent (Claude), AI-assisted. I reviewed documents only and made no connection to HoreKa or any other cluster. I did not edit the prompt and committed nothing. This file is the only file I wrote in the repository.

**Scope:** `docs/r1/prompts/HOREKA_SCAN_PROMPT_20261104.md` at `0abfaf2b` (revision 5.4), mainly `git diff 959eeac0 0abfaf2b`. Revision 5.4 drops `-S none` and the fresh-2FA hour. The login-node commands now reuse the author's open ControlMaster (`-o ControlMaster=no`). The forward is added with `-O forward` and removed with `-O cancel`, and the master is never stopped. Context: `reviews/HOREKA_SCAN_PROMPT_REV5_REVIEW_20261104.md`.

**Version note.** When I finished, the working tree held an uncommitted revision 5.5 of the prompt, which someone else wrote while I was reviewing. It has differing local and remote ports, a `tail -f /dev/null |` session wrapper, and a new FIRST-TIME SETUP rule. This review covers the committed 5.4 (`0abfaf2b`) only. MAJOR-1 and MINOR-1 to MINOR-3 still apply to 5.5's mux calls as far as I can see. But 5.5's new session wrapper changes what `session.pid` points to, and that needs its own check of step 5.3.

**Sources checked:** <https://docs.nhr.kit.edu/services/ides/> (re-fetched 4 Nov). The script starts an "unprivileged `sshd`" on the compute node, and its setup guide covers "SSH key generation" and the `~/.ssh/config` snippet. So the compute-node login uses the session's own key. It does not depend on the FeLS one-hour validity of interactive keys, and dropping the 2FA-hour rule is consistent. The page does not state this outright; it is my reading.

## Local tests

I ran these on Linux with OpenSSH 9.6p1, against two throw-away `sshd`s on 127.0.0.1: one stood in for the login node, the other for the compute node. The stand-in for `~/.ssh/config` had `ControlMaster auto`, `ControlPersist 8h` and a `ControlPath` with `%C`. The wrappers were the prompt's, with `-F <test config>` added. macOS ships OpenSSH 9.x, and the mux code below is the same there, but I did not test on macOS.

| Test | Result |
|---|---|
| `hk2ssh -O check hk2`, no master | `Control socket connect(…): No such file or directory`, rc 255 |
| `hk2ssh hk2 cmd`, no master | **Falls back to a direct connection** (here it succeeded, because the key was valid). No socket is created, so it never becomes a master. On HoreKa, past the key's hour, this is run 2's `Permission denied`. Fail-safe |
| `hk2ssh -O check hk2`, master up | `Master running (pid=N)`, rc 0. `BatchMode` has no effect on `-O` |
| `hk2ssh -v hk2 cmd`, master up | `mux_client_request_session: master session id: 2`. It runs through the master, with no authentication |
| `hk2ssh -tt hk2 'tty; read -t 5 x'` with stdin `/dev/null`, via the mux | A pty is allocated (`/dev/pts/0`). `read` blocks until its own timeout (rc 142), as without the mux. The client prints `Shared connection to … closed.` |
| `hk2ssh -O forward -L p:host:p hk2` | rc 0, **no output**. `lsof` shows the **master's** PID listening on `p` |
| The same forward a second time | rc 0, silently, as a duplicate |
| `-O forward` on a port that is already bound | `Port forwarding failed` / `master forward request failed`, rc 255. The master survives, even with `ExitOnForwardFailure yes` in the config |
| `nodessh` (`-F vscode_ssh_config`) through the forward | Works. With `-v`, no mux lines appear: a fresh TCP connection to `localhost:p` that the master forwards. It is independent of the mux socket |
| `kill` of the background `-tt` session client | The client exits 255. The remote command is gone (it gets SIGHUP when `sshd` releases the pty). The master is still running, with the same PID |
| `-O cancel -L p:host:p hk2` | The listener is gone. The master is still running |
| `-O cancel` of a forward that does not exist | Prints `port not forwarded` / `master cancel forward request failed`, but **rc 0** |
| **`LocalForward 5555 …` in the `hk2` block, then `-O cancel -L 3333:…`** | **Both 3333 and 5555 are cancelled.** The author's own forward is gone from his master |
| The same with `-o ClearAllForwardings=yes` | Nothing is cancelled: it also clears the command-line `-L` |
| `ssh -F none -o ControlMaster=no -o ControlPath=<path from ssh -G hk2> -O cancel -L 3333:… x` | Only 3333 is cancelled; 5555 stays |
| `ssh -G hk2` with `ControlPath ~/.cmt-%r@%h:%p` | Prints the fully expanded path |
| `ps -p $! -o command=` for the session client | `ssh -o BatchMode=yes -o ControlMaster=no … -tt hk2 <cmd>`. It matches the step 5 pattern `^ssh .*hk2 start-vscode-remote-ssh\.sh` in form, and `$!` is the ssh PID, because `nohup` and the wrapper both exec |
| `bash -n` on all 11 bash blocks (placeholders substituted) and the 7 inline commands | All pass. `zsh` was not available to test |
| The wrapper block, run with a fake `$HOME` | It writes both wrappers correctly. `nodessh` expands to `timeout 540 ssh -F … vscode-hk2` |
| `bash -n`, plus a run in the lab, of the fix snippets below | Pass. They print `FORWARD_OK`, `LISTENER_IS_MASTER pid=N`, `FORWARD_REMOVED` and `Master running` |

## Verdict: PASS-WITH-FIXES

| Class | Count |
|---|---|
| BLOCKING | 0 |
| MAJOR | 1 |
| MINOR | 3 |
| NIT | 3 |

**What holds.**
- **Reuse works as intended (check 1).** `ControlMaster=no` together with the config's `ControlPath` makes `hk2ssh` a mux client of an existing master, and it never creates one. With no master it falls back to a direct `BatchMode` connection. That fails on HoreKa past the key's hour, and even if it succeeds it is not a master, and step 3's `-O forward` then fails and STOPs. `-O check`, `-O forward` and `-O cancel` work with `BatchMode` and the other `-o` options; mux clients ignore `ConnectTimeout` and `ServerAlive*`, which is harmless.
- **The `-tt` session through the mux** behaves like the direct one: a pty, output into `session.log` (the master writes it through the passed file descriptor), and a blocked `read` on stdin. Killing the client ends the remote session with SIGHUP and leaves the master alive. NHR's "Ctrl+C here to terminate the job and `sshd`" therefore has the same hangup equivalent as in revision 5.1.
- **`nodessh` is independent of the master's control socket (check 2).** `-F` replaces both `~/.ssh/config` and `/etc/ssh/ssh_config`, so `nodessh` has no `ControlPath` and never multiplexes. It neither uses nor disturbs the mux socket. It depends on the master only as transport, through the forward, which is the design. Gate 1 still checks that it points at localhost.
- **Safety (check 3).** No step opens, stops or exits the master. `-O exit` and `-O stop` are forbidden explicitly. No step writes `~/.ssh/config`. `known_hosts` is touched only through `nodessh`'s private `$KH`. No `-O` command handles a credential. Teardown order is right: `scancel` needs the forward, so it comes first, and only with `gate2_ok`; then `-O cancel`; then the PID-checked `kill`. The one exception is MAJOR-1.
- **Consistency (check 4).** No `-S none`, `tunnel.pid`, `ExitOnForwardFailure`, `-N -L` or 2FA-hour text is left outside the history paragraph. The §7 STOP list matches steps 0–4. All blocks parse. Every ssh call goes through a bash wrapper or a `bash -s` block, and the remaining single-line commands quote all expansions, so they are zsh-safe as well.
- **NHR rule (check 5).** Still met. `-O check` is local. `-O forward -L` and `-O cancel -L` are local listener changes, and the login-node `sshd` only sees `direct-tcpip` channels, exactly as for the documented `ssh -N -L` tunnel. The login node still runs only the session script and carries the forward's traffic. The Claude process and its API calls stay on the Mac.

## Findings

### MAJOR

**MAJOR-1 — `-O cancel` (and `-O forward`) also act on any `LocalForward`, `RemoteForward` or `DynamicForward` in the author's `Host hk2` block. Step 5 can then remove his own forwards from his master.**
- *Where:* §1 step 3.4 and step 5.2; §0, "Never open, stop or exit the master"; step 5.2, "only that forward".
- *Problem:*
  - The mux client sends the master **every** forward in its resolved options: the command-line `-L` and also those from `~/.ssh/config`. For `-O cancel` this means it cancels all of them (tested: `LocalForward 5555` in the block plus `-O cancel -L 3333:…` removed both).
  - `-O forward` and the step 2 session client also send the config forwards. When those are already active they count as duplicates and nothing changes. When they are not active, for example because the master was opened with `-o ClearAllForwardings=yes`, they are added to his master.
  - `-o ClearAllForwardings=yes` is not a fix: it also clears the command-line `-L`, so nothing is cancelled (tested).
  - Whether his `hk2` block has forwards is unknown to the prompt. If it has, the step's promise "only that forward" is false, and the agent reconfigures the author's master, which revision 5.4 is meant to rule out.
- *Fix (minimal):* add a local check to step 1, after the `ssh -G` line:
  ```bash
  ssh -G hk2 | grep -E '^(localforward|remoteforward|dynamicforward) ' && echo "STOP: hk2 has config forwards" || echo NO_CONFIG_FORWARDS
  ```
  and add: "If it prints any forward, STOP and tell the author: `-O cancel` would also remove these forwards from your master." Add to §7, step 1: "or `ssh -G hk2` lists a `LocalForward`, `RemoteForward` or `DynamicForward`."
- *Fix (if the author has forwards he wants to keep):* send the two control commands with no config file, through the master's resolved socket path. This is tested: only the agent's forward is cancelled.
  - In step 0, add a third wrapper:
    ```bash
    cat > "$S/hk2ctl" <<'W'
    #!/bin/bash
    S="$HOME/Documents/agent_paper_B/.claude-worktrees/_snapshots/horeka_scan_20261104"
    exec ssh -F none -o BatchMode=yes -o ControlMaster=no -o ControlPath="$(cat "$S/controlpath")" "$@"
    W
    ```
  - In step 1: `ssh -G hk2 | awk '$1=="controlpath"{print $2}' > "$S/controlpath"`.
  - Use `"$S/hk2ctl" -O forward -L … mux.invalid` in step 3.4 and `"$S/hk2ctl" -O cancel -L … mux.invalid` in step 5.2. `.invalid` never resolves, so these calls can never open a connection of their own; with no master they fail at once.

### MINOR

**MINOR-1 — Step 3.4 drops the exit status of `-O forward`, writes `forward_spec` even on failure, and does not tie the listener to the master.**
- *Where:* §1 step 3.4.
- *Problem:*
  - `…; echo … > forward_spec` discards the exit status. A successful `-L` forward prints nothing (tested), so the agent can tell success from failure only by reading `tunnel.log` or by `lsof`. The prompt says "must succeed" but gives no way to see it.
  - "`lsof` must show an ssh process listening" is also met by someone else's `ssh` (for example a VS Code tunnel) that took the port between steps 3.3 and 3.4. Gate 2's job-id check would still catch that later, but the check here should already be exact.
  - `forward_spec` written after a failed forward makes step 5 cancel a forward that the agent never added. That cancel is harmless only when MAJOR-1 does not apply.
- *Fix:* replace the block with:
  ```bash
  if "$S/hk2ssh" -O forward -L <port>:<node>:<port> hk2 > "$S/tunnel.log" 2>&1; then
    echo "<port>:<node>:<port>" > "$S/forward_spec"; echo FORWARD_OK
  else echo "FORWARD_FAILED rc=$?"; cat "$S/tunnel.log"; fi
  mp=$("$S/hk2ssh" -O check hk2 2>&1 | sed -n 's/.*pid=\([0-9]*\).*/\1/p')
  lp=$(lsof -nP -t -iTCP:<port> -sTCP:LISTEN | sort -u)
  [ -n "$mp" ] && [ "$lp" = "$mp" ] && echo "LISTENER_IS_MASTER pid=$mp" || echo "STOP: listener ($lp) is not the master ($mp)"
  ```
  Then change the following sentence to: "It must print `FORWARD_OK` and `LISTENER_IS_MASTER`. Otherwise STOP after step 5." In §7, step 3: "`-O forward` fails, or the listener is not the master."

**MINOR-2 — `-O cancel` returns 0 even when nothing was cancelled, and nothing records that the master survived.**
- *Where:* §1 step 5.2; §6, "whether teardown succeeded".
- *Problem:* `ssh -O cancel` of a forward the master does not have prints `master cancel forward request failed` but exits 0 (tested). So its exit status cannot show that the forward is gone. The prompt's central safety promise is that the master stays up, yet no step checks it after teardown.
- *Fix:*
  - In step 1, save the check: `"$S/hk2ssh" -O check hk2 > "$S/master_check_before.txt" 2>&1`.
  - After step 5.2, add:
    ```bash
    lsof -nP -iTCP:"$(cut -d: -f1 "$S/forward_spec")" -sTCP:LISTEN >/dev/null 2>&1 && echo FORWARD_STILL_LISTENING || echo FORWARD_REMOVED
    "$S/hk2ssh" -O check hk2 > "$S/master_check_after.txt" 2>&1; cat "$S/master_check_after.txt"
    ```
  - In §6, have the report give: forward removed yes or no, and the master PID before and after (it should be the same).

**MINOR-3 — The step 1 STOP does not tell a blocked control socket from a missing master, and step 2 would fall back silently.**
- *Where:* §1 step 1, second bullet; §7, step 1.
- *Problem:* `-O check` and every mux call connect to a Unix socket at the `ControlPath`. If the Claude Code sandbox on the Mac blocks Unix-socket connections, as its macOS sandbox does unless they are allowed, the error is `Control socket connect(…): Operation not permitted`. The prompt then tells the author to open a master that is already open. In step 2, the same block makes `hk2ssh` fall back to a direct connection without a word, which reproduces run 2's `Permission denied`.
- *Fix:* replace the bullet with: "`"$S/hk2ssh" -O check hk2` must report `Master running`. If it says `No such file or directory` or `Connection refused`, STOP and ask the author to open the master (`ssh -fN hk2`). If it says `Operation not permitted`, or anything else, STOP and quote it: the local sandbox is blocking the control socket, and the author must allow it." Mirror this in §7.

### NIT

**NIT-1 — History paragraph.** The 5.4 entry comes before the 5.3 entry. The 5.1 entry ("the tunnel goes through `hk2` with no master connection", "fresh 2FA") now reads as current. *Fix:* move the 5.4 entry after 5.3, and add "(superseded by 5.4)" to those two clauses of 5.1.

**NIT-2 — §0, "These are the same commands the docs give a person."** The forward is no longer the docs' `ssh -N -L` command; it is the same forward, added to an existing connection. *Fix:* "They put the same load on the login node as the commands the docs give a person."

**NIT-3 — Side effects on the master to mention to the author.**
- The forward is bound with the master's own `GatewayPorts` setting. If his `hk2` block has `GatewayPorts yes`, the port is open to his LAN for the length of the scan. *Optional fix:* use `-L 127.0.0.1:<port>:<node>:<port>`, with the same spec in `forward_spec`. Gate 1 already accepts `127.0.0.1`, and ssh tries `127.0.0.1` after `::1` for `localhost`.
- The agent's session client keeps the master busy, so `ControlPersist 8h` counts from the end of the scan. The master may stay open longer than it would have. *Fix:* one line in the Chinese end message: "主连接仍开着；如需关闭请自行 `ssh -O exit hk2`."

## Answers to the five checks

| # | Check | Result |
|---|---|---|
| 1 | OpenSSH correctness | **Holds**, with MAJOR-1 (config forwards go along with `-O cancel` and `-O forward`), MINOR-1 (exit status of `-O forward`) and MINOR-2 (`-O cancel` exits 0 on failure). The `-tt` session through the mux and the client `kill` behave correctly, and the master survives |
| 2 | `nodessh` independence | **Holds.** `-F` drops the user's config, so there is no `ControlPath` and no mux. It uses the master only as transport, through the forward |
| 3 | Safety and teardown order | **Holds, except MAJOR-1.** Nothing stops the master, edits `~/.ssh/config` or `~/.ssh/known_hosts`, or handles credentials. The order `scancel` (only with `gate2_ok`), then `-O cancel`, then the checked `kill` is right |
| 4 | Internal consistency | **Holds.** No leftovers outside the history paragraph (NIT-1). The STOP list matches the steps. `bash -n` passes. Zsh-safety is preserved |
| 5 | NHR rule | **Holds.** The `-O` calls are local, and the login node still runs only the session script and the forward's `direct-tcpip` traffic |

Once MAJOR-1 is fixed (the one-line `ssh -G` precondition is enough), the prompt is fit to run. MINOR-1 to MINOR-3 are small and worth applying in the same pass.
