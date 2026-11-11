# Independent staging review — B1 Paper offline stage, run HEAD `fffa45a1` (11 Nov 2026)

**Reviewer.** Freshly spawned independent reviewer; did not produce this unit. Nothing under `/Users/wongdowling/Documents/agent_paper_B` was modified. The payload and packed checkout were read; the reviewer's own throwaway `receive`/quote rehearsals were written only under `/private/tmp`. TASL-7 was contacted only with read-only checks (`hostname`, `id`, `ls`, `stat`, `df`, `git rev-parse`, `git --version`, `python3 --version`, `test`); no writes, signals or GPU use.

**Unit under review.** Accepted plan `docs/r1/proposals/B1_PAPER_OFFLINE_STAGE_20261108.md` and its filled local-to-TASL-7 `pack` (already executed) and `receive` (not yet executed) commands, for run HEAD `fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa` on branch `ops-b1-restart-20261111`.

| Item | Value (verified) |
|---|---|
| Plan copy `/tmp/B1_PAPER_OFFLINE_STAGE.md` | 50 lines; SHA-256 `c4d7dc40cb75275a73fd4f45a23051acc3f5fbd19bf937b9623116bf6c197643` |
| Plan blob at HEAD `docs/r1/proposals/B1_PAPER_OFFLINE_STAGE_20261108.md` | blob `b52a8d9361699eb3aa878361f57b622e08094ab4`; file SHA-256 `c4d7dc40…` — **byte-identical to the copy** (`diff` empty) |
| Script `/tmp/paper-b-paper-offline-stage-20261111-fffa/tools/r1/b1_paper_offline_stage_20261108.py` | SHA-256 `462b860e15b1cc8bac7e685ec3ddd7ecebf1850981df593b0063ef5e8cbe3b67` (equal to expected and to the HEAD-tree file) |
| Script blob at HEAD | `d1adfa2bca3c6f291a586ab2367e08180305e2f2` |
| Source `/tmp/b1_src` | HEAD `fffa45a1…`, tree `583d35e7179553c08b569a76bb92eeb61519a565`, 715 commits, 8,499 tracked paths |
| Pack log | **`/tmp/paper-b-final-paper-payload-20261111-fffa.log`** (sibling of `PACK`; see R-1), SHA-256 `443bee16b7aedfa553d781af9cea666c5d8a225e68e47078be308edcd56cd4d1`, 209 B / 2 lines |
| Payload `/tmp/paper-b-final-paper-payload-20261111-fffa/paper.tar` | SHA-256 **`4421706c78ae1e0522b68c7f192d8f45fd6f458e3e88ea81641dbe7fe7dd8971`**, 122,726,400 B |
| Packed checkout | `/tmp/paper-b-final-paper-payload-20261111-fffa/paper`, HEAD `fffa45a1…`, clean, no remotes |
| Destination | `/home/dowling/r1_b1_engineering/b1_paper_final_fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa` (87 chars; full-HEAD name) |

## 1. Plan applicability — PASS

`/tmp/B1_PAPER_OFFLINE_STAGE.md` is byte-identical to the plan committed in the accepted run-HEAD tree (§table). It is the "B1 final Paper checkout: offline stage candidate" plan whose requirements the filled commands claim to meet. Requirement-by-requirement:

- **Standalone, non-shallow, SHA-1 `.git`** — source, packed checkout and a rehearsal of the *actual* `receive` all report `is-shallow=false`, object-format `sha1`; packed/received `.git` is a real directory (not a symlink) with no `.git/shallow`.
- **No alternates / grafts / split index / promisor packs** — source: no `.git/objects/info/alternates`, no `.git/info/grafts`, no `*.promisor`, `git rev-parse --shared-index-path` empty, `git replace -l` empty. Packed and received `.git` contain exactly 6 regular files (HEAD, config, index, `objects/pack/*.{pack,idx,rev}`), `objects/info` empty; verification commands repeated on the received tree — all clean.
- **Copies tracked files + actual object db + index + minimal config; does not run clone/checkout/remote-remove/hook; copies no ignored outputs** — tar = exactly the tracked set plus the 6 `.git` files (§3), and the committed `.git/config` is the 3-line minimal core config.
- **Exclusive destination named by the full 40-hex HEAD, one-shot, no retry** — destination name embeds the full HEAD; `receive` calls `Path.mkdir(mode=0o700)` without `exist_ok` and opens `dest/paper.tar` with mode `xb`, so an existing destination/archive is refused before any write; the transfer block contains no retry loop and no cleanup/repair.
- **Preserve partial scenes; no remote deletion/overwrite** — the script contains no `unlink`, `rmtree`, `remove`, `rename` or `replace` call; on failure the partial destination/archive is left in place (verified: §4). It writes only under the new destination.
- **Digest verified before extraction; rejects traversal/special/duplicate/escaping/chained-link/nested-under-symlink entries; links created last** — implemented at script lines 110–148; validated on the real payload (§3–§4).
- **Standalone plan is not acceptance of a future payload; reviewer checks the filled commands and artifact** — this review.

## 2. Source `/tmp/b1_src` — PASS

- HEAD `fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa`; commit has single parent `ac32231c5ee787401e7f67b9acb4650e68ad30d9`, author/committer `Dowling Wong <wangdowling@gmail.com>`, message "Update B1 candidate note for the R4 restart" — exactly the accepted run HEAD.
- `git status --porcelain --untracked-files=all` = 0 lines (clean including untracked); tree `583d35e7…`; 715 commits to root; `git fsck --connectivity-only --no-reflogs --no-dangling` rc 0, full `git fsck` rc 0.
- Not shallow; object format `sha1`; no alternates/grafts/promisor; `--shared-index-path` empty; `git replace -l` empty; 1 pack (`pack-364e2451…`, 13,310 objects in-pack).
- `.git/hooks`: 14 files, **all `*.sample`** (0 active hooks); no `core.hooksPath` override in the repo config.
- No credential-bearing metadata: `.git/config` is only core + plain `https://github.com/dowlingwong/Agent_paper_B.git` remote (no userinfo/token); `FETCH_HEAD`, reflogs, refs contain no secrets; the machine's global `osxkeychain` helper is outside the repo and is disabled by the script (`GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL=/dev/null`).
- The source retains its `origin` remote (expected for a local clone); the *packed* checkout has no remotes.

## 3. Script, pack log, packed checkout, payload and tar — PASS

- **Script** SHA-256 equals `462b860e…`; the HEAD-tree blob (`d1adfa2b…`) and the local reviewed copy have the same bytes. The script does no network access, no clone/checkout, no hook execution (`core.hooksPath=/dev/null`), no destructive calls.
- **Pack log** (actual path `/tmp/paper-b-final-paper-payload-20261111-fffa.log`) is the complete successful-run log:
  `HEAD fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa CLEAN and NO REMOTE: PASS` / `PAYLOAD …/paper.tar SHA256 4421706c78ae1e0522b68c7f192d8f45fd6f458e3e88ea81641dbe7fe7dd8971` — both bindings independently re-derived below. (The brief's stated path `PACK/paper.tar.log` does not exist; see R-1.)
- **Payload**: independently hashed SHA-256 `4421706c78ae1e0522b68c7f192d8f45fd6f458e3e88ea81641dbe7fe7dd8971`, 122,726,400 bytes — matches the expected value.
- **Packed checkout**: HEAD `fffa45a1…`, tree `583d35e7…`, `git status --porcelain` 0 lines, `git remote -v` empty, `git fsck --connectivity-only --no-reflogs --no-dangling` rc 0, non-shallow, `sha1`; `.git` contains only HEAD/config/index/objects/refs (no hooks, logs, packed-refs, remotes); `git ls-files -s` digest `3d9fcddf…` equals the source's.
- **Tar structure** (12,345 members: 3,840 dirs, 8,504 files, 1 symlink; file bytes 101,549,160): every member starts with `paper/`; no absolute, `..`, `./`, trailing-slash/non-normalized or duplicate names; no special/other-pax member types; exactly **one** symlink, `paper/archive/old_b_2026-10-09/code/experiment_scaffold/pi_extensions/node_modules -> ../../third_party/pi/node_modules` (intact, resolves lexically inside `paper/`); zero members nested under any symlink. Tracked arithmetic: 8,499 tracked = 8,498 regular + 1 symlink; tar regular 8,504 = 8,498 + the 6 `.git` files ⇒ exactly tracked files plus the committed object db/index/config, no ignored outputs or caches. `.git` members are exactly HEAD, config, index and the 3 pack files.
- **Author-note binding**: `docs/r1/authorizations/trackx_b1_20261105.md` in the packed checkout and in the source HEAD are byte-identical, blob `5c9bd52ad3d6a0613d2a1e637174799f6f47b955`, 21 lines / 1,697 bytes; the ```json fence-through-EOF block is 770 bytes, SHA-256 `7a0486d5478aafe1499273a55f725b2f534ca2ad8449c76c9608c0e0738d14be` — byte-identical to the JSON the accepted run-HEAD review found, parses to 13 keys with `approved: true`.
- **Committed config**: `r1/scripts/configs/exam_b1_v2.json` is unchanged by the run-HEAD commit; the note's rule/anchor/table bindings equal the reviewed values.

## 4. Filled command correctness and safety — PASS

- **Quoting/interpolation**: the exact filled transfer block (verbatim) parses under `bash -n` and `zsh -n`. Replaying it locally with a stub `ssh` (no TASL-7 contact) produced the intended single remote command (12,091 chars) containing the literal guards `test "$HOME" = /home/dowling`, `test ! -L /home`, `test ! -L /home/dowling`, `test ! -L /home/dowling/r1_b1_engineering`, `test -d /home/dowling/r1_b1_engineering`, and `receive /home/dowling/r1_b1_engineering/b1_paper_final_fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa fffa45a1… 4421706c…`.
- **`$CODE` interpolation**: base64 payload is 11,660 chars from the safe alphabet `A-Za-z0-9+/=` (no quotes/`$`/backticks), embedded inside the remote single-quoted `-c` argument; it decodes to exactly 8,745 bytes, SHA-256 `462b860e…` = the verified script. The replay's stdin stream hashed to `4421706c…` = the payload — i.e. the correct script and exact artifact reach the receiver.
- **`set -C` / `mktemp` / capture**: fresh `mktemp -d /private/tmp/paper-b-paper-final-capture-20261111.XXXXXXXX` per run; `set -C` prevents clobbering the capture files; `rc`, `receive.log` and `exit.txt` are retained; `shasum` of `receive.log`/`exit.txt` is printed (and the capture path is visible in that output even though the plan's final `printf` line is omitted — R-3).
- **Receiver behaviour on the real payload (local rehearsal, disposable `/private/tmp` destination)**: rc 0; log `HEAD fffa45a1… CLEAN and NO REMOTE: PASS` then `STAGED …/paper`. The resulting checkout: HEAD `fffa45a1…`, clean, no remotes, `git fsck --connectivity-only` rc 0, non-shallow, `sha1`, tree `583d35e7…` (= source), `ls-files -s` digest `3d9fcddf…` (= source), 8,499 tracked files, symlink intact, script SHA `462b860e…`, author note blob `5c9bd52…`.
- **Refusal/preservation paths tested**: re-running into the existing destination → rc 1 `FileExistsError`, existing payload untouched; wrong expected digest into a fresh destination → rc 1 `RuntimeError: payload hash mismatch`, `paper/` **absent** (digest verified before extraction) and the fully-streamed `paper.tar` left in place as the preserved partial. No remote file is removed or overwritten in either case.
- **SSH options / destination exclusivity**: `-o BatchMode=yes -o ConnectTimeout=12` (non-interactive; no host-key/password prompt; the same options succeeded during this review's read-only SSH, so the host key and key auth are in place); destination creation is exclusively enforced in Python, not merely by the wrapper.
- **No writes outside the destination**: the receiver's only write sites are `dest`, `dest/paper.tar` and `dest/paper/...`; git's temporary index lock stays inside the new `paper/.git`.

## 5. TASL-7 site preconditions for the transfer — PASS

Read-only checks on `tasl7` (2026-11-11):

- `hostname` = `TASL-7`; login user `dowling`; `HOME=/home/dowling`; login shell `/bin/bash`; git 2.34.1 (supports every `receive` git call); python3 3.10.12 (script is 3.7+-compatible; index inside the tar is `DIRC` v2, readable by git 2.34).
- `/home`, `/home/dowling` and `/home/dowling/r1_b1_engineering` are all real directories, not symlinks; the engineering directory exists and is writable by `dowling`.
- **Destination is absent** (`test ! -e`); no `b1_paper_final_fffa*` entry exists in the engineering directory.
- Free space on the destination filesystem: **578,970,923,008 B available** (`df -Pk`: 565,401,292 KiB; ~539 GiB) versus ~248.7 MB needed (122.7 MB payload + ~126.0 MB extracted checkout); inodes plentiful.
- Existing staged 6835 checkout is untouched and distinct: `/home/dowling/r1_b1_engineering/b1_paper_final_68357d3d8cd0c9f301005e483a49ecfd05f6e5bb` (inode 56362816, mode 700, mtime 1794097896; `paper.tar` 154,265,600 B, mode 664; `paper/.git/HEAD` mtime 1794097896; `paper/.git/index` inode 56379601, mtime 1794098109) with `paper` HEAD `68357d3d8cd0c9f301005e483a49ecfd05f6e5bb`. The transfer block never references it and writes only the new `b1_paper_final_fffa…` path.

## Residual notes (non-blocking)

- **R-1 — pack-log path in the handoff text is wrong.** The brief names `PACK/paper.tar.log`; the verified, complete successful log is the sibling **`/tmp/paper-b-final-paper-payload-20261111-fffa.log`** (SHA-256 `443bee16…`, 2 lines), exactly where the plan's `> "${PACK}.log"` redirect puts it. Content is consistent; no action on the payload, but the handoff record should cite the real path.
- **R-2 — the filled pack block is not the plan's exact pack template.** The plan's pack snippet (lines 17–31) also has `set -u`, `umask 077`, a pre-pack `[ shasum "$SCRIPT" = EXPECTED_SCRIPT ] || exit 1`, `set -C`, `|| exit 1` on the pack call, and a final `printf`. The filled pack command lacks those. The pack has already run and its artifact was independently re-verified byte-for-byte, and the transfer block re-verifies `$SCRIPT` and `$PAYLOAD` before streaming, so transfer safety is unaffected; the visible side effects are the sibling log path (R-1) and local modes 0644/0755 instead of umask-077 (the payload `paper.tar` is world-readable in `/tmp`). Do **not** re-run `pack` (one-shot); record the deviation if strict plan traceability is required.
- **R-3 — the filled transfer block omits the plan's final `printf 'Private capture: …'`.** The capture directory is still identifiable from the `shasum` output file paths and `exit.txt`; evidence retention is unaffected.
- **R-4 — verification reads may have refreshed index stat caches** in the packed and source checkouts (`git status` writes stat data only; worktree content unchanged). The *payload* was created before this review and its SHA-256 re-verified here, so the reviewed artifact is unmodified.
- **R-5 — separate gates remain.** This review establishes only staging safety: the real author gate, site preflight, handover/occupancy, data/lease/capacity and B1 launch remain separate and are not established by it. The destination must still be absent and the handover/occupancy check current when the one-shot command is executed; the receiver's exclusive creation refuses any destination that appears first.
- **R-6 — reviewer scenes (not B1 artifacts).** The disposable rehearsals are retained under `/private/tmp/b1-review-rehearsal-20261111.BdzOqfnE`, `/private/tmp/b1-review-codepath-20261111.CSSRkJef`, `/private/tmp/b1-review-wrongdigest-20261111.wLjTAirr` and the stub-ssh capture `/private/tmp/paper-b-paper-final-capture-20261111.DhbFlt4S`; they are reviewer-side noise and must not be mistaken for a real transfer capture (the real run will create its own fresh `mktemp` directory).

## Verdict

Executing exactly the filled transfer command, with `HEAD`, `PAYLOAD`, `PAYLOAD_SHA`, `SCRIPT` and `EXPECTED_SCRIPT` bound to the reviewed values, will safely stream the reviewed 122,726,400-byte payload (`4421706c…`) whose script (`462b860e…`) reproduces a standalone, non-shallow, SHA-1, remote-less checkout at the accepted run HEAD `fffa45a1…`; the receiver is exclusive, verifies the digest before extraction, refuses reuse, and preserves any partial scene. The plan, artifact, run HEAD and site preconditions all hold. All checks passed; residual notes R-1–R-6 are non-blocking.

## Addendum — transfer verification (11 Nov)

**Scope.** The one-shot transfer was executed exactly as reviewed (started c. 2026-11-11 02:19 PST and completed c. 02:23 PST / 10:23 UTC; destination mtime epoch 1794392605). This addendum verifies the operator's receipt and the actual received checkout on TASL-7 using read-only checks only (`ls`, `stat`, `find`, `df`, `sha256sum`, `readlink`, `git rev-parse/status/fsck/remote/replace/ls-files`); every git command was run with `GIT_OPTIONAL_LOCKS=0` and `--no-optional-locks` so no index refresh could write. No writes, signals or GPU use.

### Receipt (local capture) — PASS

- Capture dir `/private/tmp/paper-b-paper-final-capture-20261111.s0KM6CCG`, mode 0700, contains exactly `receive.log` (0600) and `exit.txt` (0600).
- `receive.log`: 173 B / 2 lines, SHA-256 `edacfdbef88427ade4743495a7916c5da3db93cf7d351a50365aac9adf5353f7`; content exactly:
  - `HEAD fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa CLEAN and NO REMOTE: PASS`
  - `STAGED /home/dowling/r1_b1_engineering/b1_paper_final_fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa/paper`
- `exit.txt`: 2 B, content `0\n`, SHA-256 `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa`; SSH exit 0.
- This is a new capture directory, distinct from the reviewer-side stub-ssh capture listed in R-6.

### Received destination on TASL-7 — PASS

- Destination exists **exactly once** (`find /home/dowling/r1_b1_engineering -maxdepth 1 -name 'b1_paper_final_fffa*'` count = 1); real directory, **not a symlink**; mode 700; inode 57187079; mtime epoch 1794392605.
- Top-level entries exactly `paper` and `paper.tar`; `paper` is a real directory, not a symlink.
- Stored payload `/home/dowling/r1_b1_engineering/b1_paper_final_fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa/paper.tar`: SHA-256 `4421706c78ae1e0522b68c7f192d8f45fd6f458e3e88ea81641dbe7fe7dd8971` (identical to the reviewed payload), 122,726,400 B, mode 664.
- `paper` checkout: HEAD `fffa45a12b5b43dbdcc6a8c88b509f71309fbbaa`; tree `583d35e7179553c08b569a76bb92eeb61519a565`; `status --porcelain --untracked-files=all` = 0 (clean including untracked); **no remotes** (`remote -v` empty); non-shallow (`rev-parse --is-shallow-repository` = `false`, no `.git/shallow`); no alternates, no grafts, no promisor files, no replace refs, no split index (`--shared-index-path` empty); `git fsck --connectivity-only --no-reflogs --no-dangling` rc **0**; 8,499 tracked paths; `ls-files -s` digest `3d9fcddf210ab88e1bb32ae55563bf97ab908d1c2f0f729da836cc12bc1e724a` (= source). `.git` contains exactly the 6 designed regular files (HEAD, config, index, `objects/pack/*.{idx,pack,rev}`).
- Tracked symlink intact: `archive/old_b_2026-10-09/code/experiment_scaffold/pi_extensions/node_modules -> ../../third_party/pi/node_modules`, git mode `120000`.
- Author note `docs/r1/authorizations/trackx_b1_20261105.md`: 21 lines / 1,697 B, blob `5c9bd52ad3d6a0613d2a1e637174799f6f47b955`; **JSON fence-to-EOF 770 B, SHA-256 `7a0486d5478aafe1499273a55f725b2f534ca2ad8449c76c9608c0e0738d14be`** — the accepted value.
- In-tree staging script `tools/r1/b1_paper_offline_stage_20261108.py`: SHA-256 `462b860e15b1cc8bac7e685ec3ddd7ecebf1850981df593b0063ef5e8cbe3b67` (= reviewed script).
- Received file counts: 8,504 regular files + 1 symlink (+ the 6 `.git` files among the 8,504) — exactly the tar's contents; no extra files.

### Isolation and preservation — PASS

- Parent `/home/dowling/r1_b1_engineering` now holds exactly the 7 pre-existing entries plus the new destination; **0 regular files**; the only entry with an mtime after 2026-11-11 00:00 is the new destination (its parent directory mtime also changed as expected when the entry was created). The transfer created no other B1 artefact; no duplicate/partial `b1_paper_final_fffa*` exists anywhere under `/home/dowling` (count = 1), and no `paper-b-paper-final*` residue exists in the host `/tmp`.
- Pre-existing 6835 staged checkout **unchanged** against the pre-transfer baseline captured in §5: `b1_paper_final_68357d3d8cd0c9f301005e483a49ecfd05f6e5bb` inode 56362816 / mtime 1794097896; `paper` inode 56362818 / mtime 1794097896; `paper/.git/HEAD` inode 56362839 / mtime 1794097896; `paper/.git/index` inode 56379601 / mtime 1794098109; `paper.tar` 154,265,600 B, mode 664, mtime 1794097896; `paper` HEAD `68357d3d8cd0c9f301005e483a49ecfd05f6e5bb`; and **no path under it has an mtime after 2026-11-08 00:00**.
- Free space after: 578,706,194,432 B available (unchanged in substance); nothing under the engineering directory was deleted or overwritten. The only `*.lock` path in the new tree is the tracked `archive/old_b_2026-10-09/code/requirements.lock` file, not a git lock.

**Result.** The receipt hashes/content, the stored payload digest, the received checkout's provenance/cleanliness/connectivity, the tracked symlink, the author-note JSON binding and the untouched 6835 scene all match the reviewed artifact and plan. The one-shot transfer succeeded with no side artefacts; the original verdict stands.

VERDICT: accepted
