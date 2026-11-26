# Independent staging review — B1 Paper offline stage `_c`, run HEAD `4b312844` (12 Nov 2026)

**Reviewer.** Fresh independent reviewer; did not produce this unit. No file under `/Users/wongdowling/Documents/agent_paper_B` was modified. TASL-7 was contacted only with read-only checks (`test`, `stat`, `ls`, `df`, `cat`, `env`, `umask`, `sha256sum`, `git rev-parse/status/remote` with `--no-optional-locks`, and `python3 -c` decode); no writes, signals, GPU or server use. Reviewer rehearsals and received copies are under `/tmp` only.

**Unit under review.** Accepted plan `docs/r1/proposals/B1_PAPER_OFFLINE_STAGE_20261108.md`, the filled local `pack` command (already executed), the filled local-to-TASL-7 `receive` command (not executed), and the produced payload for run HEAD `4b312844962e1106db04d5a60bf996fad0e3e514` on branch `ops-b1-restart-c-20261112`.

| Item | Value (verified) |
|---|---|
| Plan copy `/tmp/B1_PAPER_OFFLINE_STAGE.md` | 50 lines; SHA-256 `c4d7dc40cb75275a73fd4f45a23051acc3f5fbd19bf937b9623116bf6c197643` |
| Plan blob at run HEAD `docs/r1/proposals/B1_PAPER_OFFLINE_STAGE_20261108.md` | blob `b52a8d9361699eb3aa878361f57b622e08094ab4`; `cmp` byte-identical to the copy |
| Script `/tmp/b1_src_c/tools/r1/b1_paper_offline_stage_20261108.py` | SHA-256 `462b860e15b1cc8bac7e685ec3ddd7ecebf1850981df593b0063ef5e8cbe3b67`; 8,745 B; run-HEAD blob `d1adfa2bca3c6f291a586ab2367e08180305e2f2`; `cmp` identical |
| Source `/tmp/b1_src_c` | HEAD `4b312844962e1106db04d5a60bf996fad0e3e514`; parent `f1a776095216c77d6793a80dba998586b9c41254`; tree `760cf663470026691bb8b7036a7195a271c1a864`; 723 commits; 8,520 tracked (8,519 regular + 1 symlink); clean; detached; non-shallow; SHA-1 |
| Pack log `/tmp/paper-b-final-paper-payload-c-20261112-4b31.log` | 211 B, 2 lines; SHA-256 `9026875aca73a80a6198d5134f01b3a9792d46f3cd79a719aa3dbbe304a0fa3d` |
| Payload `/tmp/paper-b-final-paper-payload-c-20261112-4b31/paper.tar` | SHA-256 **`2c9f3286e870e89ccec52888e26709caa306d3cb0d8f564962349497ec4fd29b`**; 123,176,960 B |
| Packed checkout `/tmp/paper-b-final-paper-payload-c-20261112-4b31/paper` | HEAD/tree as source; clean; no remotes; `git fsck --full` rc 0; `.git` exactly 6 regular files |
| Destination | `/home/dowling/r1_b1_engineering/b1_paper_final_4b312844962e1106db04d5a60bf996fad0e3e514` (87 chars, full-HEAD name); absent |

## 1. Plan applicability — PASS

`/tmp/B1_PAPER_OFFLINE_STAGE.md` is byte-identical to the run-HEAD plan blob (§table). Requirement by requirement:

- **Standalone, non-shallow, SHA-1 `.git`; no alternates/grafts/split index/promisor** — source: `.git` real directory, `is-shallow=false`, object-format `sha1`, no `.git/shallow`, no `.git/objects/info/alternates`, no `.git/info/grafts`, no `*.promisor`, `rev-parse --shared-index-path` empty, no `refs/replace`. Packed and received `.git` contain exactly `HEAD`, `config`, `index`, `objects/pack/*.{idx,pack,rev}`; no alternates/grafts/hooks.
- **Exclusive destination named by full 40-hex HEAD, one-shot, no retry** — destination embeds the full HEAD; `receive` calls `Path.mkdir(mode=0o700)` without `exist_ok` before any write and opens `dest/paper.tar` with mode `xb`; no retry loop or cleanup in the block.
- **Digest before extraction; rejects traversal/special/duplicate/escaping/chained-link/nested-under-symlink entries; writes exclusively; links last** — script lines 110–148; verified on the real payload and on synthetic bad archives (§5).
- **No deletion/replacement; partial scene preserved** — script contains no `unlink`, `rmtree`, `remove`, `rename` or `replace`; wrong-digest and refusal rehearsals left the partial archive/destination in place (§5).
- **Git reads disable optional locks, system/global config and fsmonitor** — every `git` call uses `--no-optional-locks`, `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_COUNT=0`, `GIT_NO_REPLACE_OBJECTS=1`, `core.fsmonitor=false`, `core.hooksPath=/dev/null`.
- **No clone/checkout/remote-remove/hook; no ignored outputs** — script copies tracked files plus the actual object database and index; tar non-`.git` regular set equals the tracked regular set exactly (8,519 paths), symlink set equals the tracked symlink set; no untracked/ignored files (§3).
- **Standalone plan is not acceptance of a future payload** — this review examines the actual filled command and artifact.

## 2. Source, script, pack log, packed checkout — PASS

- **Source** is detached at exactly `4b312844962e1106db04d5a60bf996fad0e3e514`; parent exactly `f1a776095216c77d6793a80dba998586b9c41254`; commit author/committer `Dowling Wong <wangdowling@gmail.com>`, Thu Nov 12 20:56:04 2026 +0100, subject “Update B1 candidate note for the _c restart (truncation fix)”; tree `760cf663…`; 723 commits to root.
- `git status --porcelain --untracked-files=all` = 0 lines; `git diff --quiet HEAD` and `git diff-index --cached --quiet HEAD` both SAME; `ls-files -s` sha256 `a7d2b396a74302115d67fce93135d5ad8b236f0af5f82851432b8b04bbc054a2`.
- Non-shallow, SHA-1, no alternates/grafts/split index/promisor, no submodules (modes: 8,498 `100644`, 21 `100755`, 1 `120000`), no sparse-checkout, no active hooks (only `*.sample` or none), `refs/replace` empty. Source retains a plain `origin` URL `https://github.com/dowlingwong/Agent_paper_B.git` (no credentials; `git config` has no token/password/extraheader/helper); the packed checkout has no remotes, as required.
- **Script** has the expected SHA-256 and is byte-identical to the run-HEAD blob. It performs no network access, no clone/checkout, no remote removal, no hook execution and no destructive calls.
- **Pack log** is the complete successful log: `HEAD 4b312844962e1106db04d5a60bf996fad0e3e514 CLEAN and NO REMOTE: PASS` / `PAYLOAD /tmp/paper-b-final-paper-payload-c-20261112-4b31/paper.tar SHA256 2c9f3286e870e89ccec52888e26709caa306d3cb0d8f564962349497ec4fd29b`.
- **Packed checkout** is HEAD/tree above, `status --porcelain` 0 lines, `git remote` empty, non-shallow, `sha1`, `git fsck --full --no-reflogs --no-dangling` rc 0; `.git` exactly 6 regular files (`HEAD`, `config`, `index`, `objects/pack/pack-38c7a5bee60e3f73aaf448d8615420f05fd006ef.{idx,pack,rev}`), no hooks/logs/packed-refs; index entries equal source (`ls-files -s` digest `a7d2b396…`); config is the 3-line minimal core config.

## 3. Payload and tar — PASS

- **Payload** independently hashed with Python `hashlib`, `shasum -a 256` and `openssl dgst -sha256`: **`2c9f3286e870e89ccec52888e26709caa306d3cb0d8f564962349497ec4fd29b`**, 123,176,960 B — matches the expected value.
- **Structure**: 12,367 members = 3,841 directories + 8,525 regular files + 1 symlink; file payload 101,966,301 B. Every member starts with `paper/`; no absolute, `..`, `.`/non-normalized, trailing-slash or duplicate names; no hardlinks, FIFOs, devices or other special members; no members nested under a symlink; no escaping or chained link target.
- **Tracked-set equality**: tar regular non-`.git` paths = exactly the 8,519 tracked regular paths; tar symlink set = exactly the one tracked symlink; no extra/ignored/untracked files. Apparent `__pycache__`/`.pyc` paths under `results/r1/...` are committed in HEAD (`git ls-files --error-unmatch` confirms), not untracked caches.
- **The one tracked relative symlink** is intact: `paper/archive/old_b_2026-10-09/code/experiment_scaffold/pi_extensions/node_modules -> ../../third_party/pi/node_modules`; lexically resolves inside `paper/` to `.../code/third_party/pi/node_modules`. The target directory is not committed (untracked `node_modules`), so the link is dangling by design but the link itself is the tracked relative link; no member is under it.
- **`.git` members** are exactly `HEAD`, `config`, `index`, and the three pack files; `.git/objects/info/` and `.git/refs/` are empty; no remotes, hooks, logs, shallow, alternates or grafts. Index version `DIRC` v2 and pack version 2 are readable by remote git 2.34.1.

## 4. Author-note binding at HEAD — PASS

- `docs/r1/authorizations/trackx_b1_20261105.md`: blob `0c5dd06ae9fe998d8fed4f0a576418fa7d9b588b`; 1,625 B; 21 lines; SHA-256 `0ef175aaad4544298a9944565ca15437abafb0346ed8e2d03a79fc8d920ed32e`; source, packed and received copies are byte-identical.
- Contains the `_c` prose: “This candidate is the `_c` restart of B1 after run `fffa_20261111_b` stopped on a truncated proposer reply”; names fix `1334c616`, reviewed base `f1a776095216c77d6793a80dba998586b9c41254` and hand-off `proposals/B1_RESTART_HANDOFF_C_20261111.md`.
- The ```json fence-through-EOF block is 770 B, SHA-256 **`7a0486d5478aafe1499273a55f725b2f534ca2ad8449c76c9608c0e0738d14be`**; parses to 13 keys with `approved: true`, `host: TASL-7`, `workers: 20`, `llm_call_cap: 80`.
- Fix commit `1334c61619f76e71a7c6ba83c837714f9d3f0720` is an ancestor of HEAD; the C restart hand-off exists at HEAD (SHA-256 `47b79bf55c673d8b4cbf81bc52082166f8ed3efa7447f8b9cd2c2e1c65d370cd`).

## 5. Filled command correctness and safety — PASS

- **Quoting/interpolation.** The exact filled transfer block was executed with a stub `ssh` (no TASL-7 contact). It produced the intended single remote command of 12,091 chars, SHA-256 `5be74c2149b47968ab3f3465706d3298a94b84a9d3de17fdd52a5643a37d06ce`, containing the literal guards `test "$HOME" = /home/dowling`, `test ! -L /home`, `test ! -L /home/dowling`, `test ! -L /home/dowling/r1_b1_engineering`, `test -d /home/dowling/r1_b1_engineering`, and `receive /home/dowling/r1_b1_engineering/b1_paper_final_4b312844962e1106db04d5a60bf996fad0e3e514 4b312844… 2c9f3286…`. The stub's stdin hashed to `2c9f3286…` (the payload); the capture `exit.txt` was `0`.
- **`$CODE`.** Base64 is 11,660 chars from the safe alphabet `A-Za-z0-9+/=` (no quotes/`$`/backticks); it decodes to 8,745 B with SHA-256 `462b860e…`, the verified script. Remote `python3 -I -B -c` decoded the 11,660-char argument to the same 8,745 B/SHA, and its `-c` argv shape (`['-c','receive',dest,head,sha]`, `__name__ == '__main__'`) was verified on the host; remote `ARG_MAX` is 2,097,152 > 12,091.
- **`set -C`/`mktemp`/capture.** Fresh `mktemp -d` per run (8 X's; `/private/tmp` exists, mode 1777); the block refuses to clobber `receive.log`, records `rc` in `exit.txt`, and prints `shasum` of both. The rehearsal used a stub `ssh` (by design) and substituted only the `mktemp` target (reviewer path); the remote command string above is the exact one that the real `ssh` would receive.
- **Real receiver rehearsal (disposable `/tmp` destination).** The actual script received the actual payload: rc 0; log `HEAD 4b312844… CLEAN and NO REMOTE: PASS` then `STAGED …/paper`; received checkout HEAD/tree `4b312844…`/`760cf663…`, clean including untracked, no remotes, non-shallow, `sha1`, `git fsck --full` rc 0, 723 commits, 8,520 tracked, `ls-files -s` digest `a7d2b396…`, index v2, pack v2, symlink intact, script SHA `462b860e…`, note SHA `0ef175aa…`.
- **Refusal/preservation tests.** Re-running into the existing rehearsal destination → rc 1 `FileExistsError`, destination unchanged (payload hash and stat unchanged). Wrong expected digest into a fresh destination → rc 1 `RuntimeError: payload hash mismatch`, `paper/` absent, fully streamed `paper.tar` (123,176,960 B) left in place. Synthetic `../evil.txt`, `paper/link/x` under a symlink, `paper/link -> ../../etc`, duplicate `paper/x`, and FIFO members each → rc 1 and `paper/` absent. No remote file was deleted or overwritten.
- **No writes outside the destination on the host.** The receiver writes only `dest`, `dest/paper.tar` and `dest/paper/...`; git is invoked with `--no-optional-locks` and hooks/system/global config disabled.

## 6. TASL-7 preconditions — PASS

Read-only checks on `tasl7` (2026-11-12):

- Host/user: `TASL-7`, user `dowling`, `HOME=/home/dowling`, login shell `/bin/bash`; git 2.34.1; python3 3.10.12; `ARG_MAX` 2,097,152; umask `0002`; remote environment has no `GIT_*`, `PYTHON*` or `BASH_ENV`; PATH includes `/usr/bin`.
- `/home`, `/home/dowling` and `/home/dowling/r1_b1_engineering` are real directories, not symlinks; the engineering directory is writable by `dowling`.
- **Destination is absent** (`test ! -e` and `test ! -L`); no `b1_paper_final_4b312844*` entry exists.
- Free space `df -Pk`: 554,308,020 KiB (~528.7 GiB; ~568.0 GB decimal) versus ~245 MB needed (123.2 MB payload + ~121 MB extracted checkout).
- Existing scenes untouched and distinct: `b1_paper_final_68357d3d8cd0c9f301005e483a49ecfd05f6e5bb` (`paper` HEAD `68357d3d…`) and `b1_paper_final_fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa` (`paper` HEAD `fffa45a1…`), both clean with no remotes; the `_b` marker `/home/dowling/r1_locks/trackx_evidence.active` has SHA-256 `23fa767be7346809d087d0a2352241e6042abdd04df2f198e476b8f39eab4c9a` and content `{"head": "fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa", "run_id": "fffa_20261111_b"}`. The transfer block names only the new destination; no existing checkout or marker is read or written by it.

## Residual notes (non-blocking)

- **R-1 — filled pack block is not the plan's exact pack template.** The plan's snippet (lines 17–31) also has `set -u`, `umask 077`, a pre-pack `[ shasum "$SCRIPT" = "$EXPECTED_SCRIPT" ] || exit 1`, `set -C`, `|| exit 1` on the pack call, and a final `printf`; the filled one-liner omits those and does not use its `EXPECTED_SCRIPT` variable. The pack has already run; its artifact was independently re-verified byte-for-byte, and the transfer block re-checks `$SCRIPT` and `$PAYLOAD`. Do **not** re-run `pack` (one-shot). Visible side effects: local `paper.tar`/log modes are 0644 inside a 0700 `PACK` directory instead of umask-077.
- **R-2 — filled transfer block omits the plan's final `printf 'Private capture: …'`.** The capture directory is still identifiable from the `shasum` output paths and `exit.txt`; evidence retention is unaffected.
- **R-3 — transfer block's final process status is `shasum`'s, not the SSH rc.** It preserves and prints `rc` in `exit.txt` and records `receive.log`; PASS must be read from `exit.txt` (0) plus `receive.log`, as the plan's template also requires. On a failed SSH the shell itself may still exit 0; the recorded evidence is authoritative.
- **R-4 — plan path absent from the `agent_paper_B` working tree.** `/Users/wongdowling/Documents/agent_paper_B` is on branch `exam-x-20261026` at `8a819f75cb301b073b498895524e0618f509a306`, where the plan path does not exist. The reviewed plan is the run-HEAD blob `b52a8d9361699eb3aa878361f57b622e08094ab4` and `/tmp/B1_PAPER_OFFLINE_STAGE.md` (`c4d7dc40…`), which are byte-identical. Traceability note only.
- **R-5 — verification reads may have refreshed index stat caches** in `/tmp/b1_src_c` and the packed checkout (`git status`/`fsck` read paths; worktree content unchanged; `ls-files -s` digest `a7d2b396…` identical everywhere). The payload `paper.tar` was created before this review and its SHA-256 is re-verified here, so the reviewed artifact is unmodified.
- **R-6 — reviewer-side scenes (not B1 artifacts).** `/tmp/b1_review_stage_c` (received checkout and refusal tests), `/tmp/b1_stage_c_rehearsal.EaDcUDRw` (stub-ssh capture; its capture path is reviewer-side, not the real template), `/tmp/note_head_c.md`, `/tmp/rev_*`, `/tmp/rev_remote_cmd.txt`. These must not be mistaken for a real transfer capture.
- **R-7 — separate gates remain.** This review establishes only staging safety. The author gate, current site preflight, handover/occupancy, data/lease/capacity and B1 launch remain separate; the destination must still be absent and the handover current when the one-shot command is executed (the receiver refuses any destination that appears first).

## Verdict

Executing exactly the filled transfer command, with `HEAD`, `PAYLOAD`, `PAYLOAD_SHA`, `SCRIPT` and `EXPECTED_SCRIPT` bound to the reviewed values, will stream the reviewed 123,176,960-byte payload (`2c9f3286…`) whose 8,745-byte script (`462b860e…`) reproduces a standalone, non-shallow, SHA-1, remote-less checkout at the accepted run HEAD `4b312844…`; the receiver is exclusive, verifies the digest before extraction, refuses reuse, rejects traversal/special/duplicate/link escapes, and preserves any partial scene. The plan, artifact, run HEAD and site preconditions all hold. All checks passed; residual notes R-1–R-7 are non-blocking.

VERDICT: accepted
