# B1 `_d` Paper staging — independent review of filled commands and payload (13 November 2026)

**Reviewer.** Fresh, independent; I did not produce this unit. Read-only on `/Users/wongdowling/Documents/agent_paper_B`; nothing there was modified. Read-only SSH (`ls`/`stat`/`df`/`git rev-parse`) on `tasl7`; no writes, signals, GPU or server. Only this file and `/tmp` were written. Host checks were limited to the permitted read-only set.

## Scope and bindings

- Plan read at the run HEAD: `docs/r1/proposals/B1_PAPER_OFFLINE_STAGE_20261108.md` = SHA-256 `c4d7dc40cb75275a73fd4f45a23051acc3f5fbd19bf937b9623116bf6c197643` (50 lines), byte-identical to `/tmp/B1_PAPER_OFFLINE_STAGE.md`.
- Run HEAD `7912b7fffb4c1adeb39688bdb3852a919bdc71c8` (parent `999759b7fec7158e930950544db6aac4988569bb`, tree `e29971bcaed1dd8c8e1bfa90807bce3a8114737c`), from `/tmp/b1_src_d`.
- Staging script `tools/r1/b1_paper_offline_stage_20261108.py`: SHA-256 `462b860e15b1cc8bac7e685ec3ddd7ecebf1850981df593b0063ef5e8cbe3b67`; run-HEAD blob `d1adfa2bca3c6f291a586ab2367e08180305e2f2`, 8,745 B. The blob content hashes to the same `462b860e…` value.
- Payload `/tmp/paper-b-final-paper-payload-d-20261113-7912/paper.tar`: SHA-256 **`c719fad563902cec9c7f0afc57cc1db465227c5dc12104044ef13e5328dc7b2a`**, **123,473,920 B**, independently recomputed. Pack log `/tmp/paper-b-final-paper-payload-d-20261113-7912.log` contains exactly `HEAD 7912b7ff… CLEAN and NO REMOTE: PASS` and the same payload path/SHA.

## 1. Plan requirements — PASS

Standalone non-shallow SHA-1 `.git`: `.git` is a real directory, `--is-shallow-repository` = `false`, object format `sha1`; no `objects/info/alternates`, no `info/grafts`, no `*.promisor`, empty `--shared-index-path`, no `commondir`/`shallow`. Full-HEAD exclusive destination, digest-before-extraction, no deletion and partial-scene preservation are implemented in the receiver (`dest.mkdir` exclusive; archive hash checked before `tarfile` extraction; no unlink/rename; links created last). Plan hash is unchanged at the run HEAD.

## 2. Source and script — PASS

`/tmp/b1_src_d` HEAD is exactly `7912b7ff…`, clean (`status --porcelain --untracked-files=all` empty), 732 commits, 13,484 objects, full `git fsck --connectivity-only` rc 0. Detached HEAD; the only ref is `refs/remotes/origin/ops-b1-restart-d-20261113`, also `7912b7ff…`. Script SHA/byte-count/tree blob match the accepted value above.

## 3. Payload and packed checkout — PASS

- Tar: 12,376 members — 8,534 regular files, 3,841 directories, 1 symlink; every name is `paper/…` (no absolute path, no `..`, no `./` alias, no duplicates, no control/backslash names, no special entry). No member lies under the symlink.
- Single tracked symlink `archive/old_b_2026-10-09/code/experiment_scaffold/pi_extensions/node_modules` (mode `120000`, blob `1684370ee0…`) has target `../../third_party/pi/node_modules`, a relative target resolving inside `paper/`; intact in the tar and the packed checkout.
- Content: all 8,534 regular members except `paper/.git/config` are byte-identical to `/tmp/b1_src_d`; the only difference is the expected minimal `.git/config` (`[core] repositoryformatversion = 0, filemode = true, bare = false`). No tracked file is absent and no extra file exists.
- Packed checkout `/tmp/paper-b-final-paper-payload-d-20261113-7912/paper`: HEAD `7912b7ff…`, detached, `status --porcelain --untracked-files=all` empty, no remotes, minimal config, full `git fsck --no-reflogs --no-dangling` rc 0, 732 commits, 8,529 tracked entries, 13,484 objects.
- Note `docs/r1/authorizations/trackx_b1_20261105.md`: blob `0173672c82d4e96e59667f183b9bacdaf90dda14`, 1,751 B, SHA-256 `976abe264dbb303a992ffff92075ee6eb5f7709afceeff8d3f98abc34b6d033d`; line 3 contains the `_d` restart prose (base `999759b7…`, `paper_commit` re-pin, `B1_RESTART_HANDOFF_D_20261113.md`); the ```` ```json ```` fence-through-EOF block is 770 B, SHA-256 **`7a0486d5478aafe1499273a55f725b2f534ca2ad8449c76c9608c0e0738d14be`**, matching the accepted value.
- `paper_commit` in `r1/scripts/configs/exam_b1_v2.json` = **`02a914944cc546fc33a6428b1eb92a8993542bef`**.

## 4. Filled command correctness/safety — PASS

Script and payload hashes are re-checked before use; `OUT` is a fresh `mktemp -d` capture; `CODE` is base64 of the already-verified script; `set -C` precedes the one-shot `ssh`. The local double-quoted remote command escapes `$HOME` correctly and expands only the reviewed `$CODE` (base64 alphabet has no quote/backslash/`$`), `${HEAD}` and `$PAYLOAD_SHA`; the remote prelude checks `HOME`, the non-symlink `/home`, `/home/dowling` and `/home/dowling/r1_b1_engineering`, then `exec`s Python `-I -B` on the embedded script with `receive <full-HEAD dest> $HEAD $PAYLOAD_SHA`, stdin = payload. `rc` is captured and both `receive.log` and `exit.txt` are hashed. The receiver creates the dest exclusively, writes only `dest/paper.tar` and `dest/paper/…`, verifies the full digest before extraction, writes files with `xb`, creates links last, and never deletes. A local rehearsal of the same base64/argument/quotation path (dest under `/tmp`) returned rc 0 with `HEAD … CLEAN and NO REMOTE: PASS`, reproduced the payload SHA, and produced a clean checkout at `7912b7ff…`; reusing an existing dest returned rc 1 untouched, and a wrong digest returned rc 1 leaving only the partial `paper.tar` in place (no extraction). No existing staged scene or marker is referenced by the command.

## 5. Site preconditions — PASS (read-only)

Destination `/home/dowling/r1_b1_engineering/b1_paper_final_7912b7fffb4c1adeb39688bdb3852a919bdc71c8` is absent (`test -e` false). `/home`, `/home/dowling` and `/home/dowling/r1_b1_engineering` are real directories, not symlinks; the latter is `dowling:dowling` mode 775. Available space is 566,245,593,088 B (528 GiB) — ample for the 123 MB archive plus the ~250 MB received scene. The three existing scenes `b1_paper_final_68357d3d…`, `…_fffa45a1…`, `…_4b312844…` are present with matching HEADs and are not touched by this command. `~/r1_locks/trackx_evidence.active` is absent. Host `git 2.34.1`, `python3 3.10.12` are compatible with the index (v2) and the 3.10-safe script.

## Findings

None. The command and artifact meet the accepted plan for the `_d` restart.

## Non-blocking notes

1. The filled transfer omits the plan template's final `printf 'Private capture: %s; SSH exit=%s\n' "$OUT" "$rc"`; the random `$OUT` path is therefore not echoed (it remains in the session variable and is findable under `/private/tmp/paper-b-paper-final-capture-d-20261113.*`). Adding that line would restore exact traceability.
2. The filled pack command and transfer do not set `set -u`; with unset `$PAYLOAD`/`$PAYLOAD_SHA`, the guards could compare empty strings. This is fail-safe here: the pack log and file verify `c719…`, and any empty `$HEAD`/digest is rejected by `receive` before `mkdir`, so no host write occurs. Binding all five variables in the executing session is required.
3. The filled pack command also omits the template's `set -u`, `umask 077`, `set -C` and `|| exit 1`; the pack nevertheless exited successfully (log has both PASS lines) and the artifact verifies, while the `0700` pack directory bounds the `0644` payload/log. Contents are non-secret hashes/paths. Remote `dest` is still `0700` and `paper.tar` `0644` inside it.
4. `paper.tar` is written to the destination before its digest is checked; a digest failure therefore leaves a 123 MB partial archive. This matches the accepted "partial scene preserved" rule.
5. GPU idle / lease-free / Track S paused were not independently re-verified (outside the permitted read-only `ls`/`stat`/`df`/`git rev-parse` set); disk and the absent marker were verified.

VERDICT: accepted
