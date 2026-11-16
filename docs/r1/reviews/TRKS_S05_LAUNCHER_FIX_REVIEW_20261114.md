# Track S k=2 S0.5 launcher LIVE-guard fix + resume-unit update — narrow pre-deployment review

Reviewer: fresh independent agent (did not write the change). Date 2026-11-14, ~10:40Z.
Unit: repo `https://github.com/dowlingwong/Agent_paper_B.git`, branch `trackS-ops-20261030`, tip
`e253a423069d44248cd8496eddbeec587c49e489` (= `e253a423`, "Fix the k=2 S0.5 launcher LIVE guard and update the resume
unit sha"), fetched in a clean `/tmp` clone. Nothing under `/Users/wongdowling/Documents/agent_paper_B` was touched;
TASL-7 was only read (`ssh tasl7` read-only commands).

Subject bytes (re-hashed in the clone):

```
f823b86a85272ef6246ceb3ce9f5142057eb1b5f297a1d5ddd20394ebaba3dd3  r1/tracks/ops/launch/tasl7_digits_s05_20261113.sh
```

Previous revision (parent `e253a423^`), still what is installed on the host:

```
3e9574643a6736a14ce28f00dd0717a57de3987cc84242b7dc255139f7615151  r1/tracks/ops/launch/tasl7_digits_s05_20261113.sh
```

## 1. Launcher diff — PASS

`git diff e253a423^ e253a423 -- r1/tracks/ops/launch/tasl7_digits_s05_20261113.sh` is exactly one line, line 33:

```
-LIVE=$(pgrep -u dowling -f 'llama-server .*--port 1810[12]' | wc -l | tr -d ' ')
+LIVE=$( (pgrep -u dowling -f 'llama-server .*--port 1810[12]' || true) | wc -l | tr -d ' ' )
```

`--word-diff` shows only the wrapper tokens `(`, `|| true`, `)` changed; no other line, no reordering, 79 lines in
both revisions, no CRLF, no trailing whitespace, file ends in a newline, mode still `100755`. `bash -n` passes (rc=0)
on the new file.

Behaviour was reproduced (macOS, `set -euo pipefail`, `pgrep -u $(id -un)`): with **zero** matching processes the old
form aborts (subshell rc=1, exactly the reported silent rc=1) while the new form yields `LIVE=0`; with **two** live
processes whose argv matches `llama-server .*--port 1810[12]` the new form yields `2`, identical to the raw
`pgrep | wc -l` count. So the guard's counting semantics are unchanged and the zero-server case is now fail-safe
rather than fatal. Fail-closed property is preserved: a bogus `pgrep` (exit 2) is also masked to `LIVE=0`, which still
refuses when `trks_llm` exists with `K` servers, and the no-session branch additionally refuses on any GPU compute app
or a held `gpu0.lock`.

## 2. Resume unit text — FAIL (blocking)

`docs/r1/proposals/TRACKS_S05_T7_RESUME_20261114.md` (new sha256
`b2caed31a030b38aaaf1d63462117c4b7ec146999eb6ffce746c581ac4ba47f1`) was modified, and the added
first-resume paragraph is accurate (see below), but **the new launcher sha is never cited**:

- line 24 still reads "Deployed reviewed scripts: `tasl7_digits_s05_20261113.sh` sha `3e957464…` (takes `K`, starts
  `trks-servers $K` …)" — that is the **broken** revision that produced the rc=1 abort;
- line 30 then says "The fixed revision is the sha above." That pointer resolves to `3e957464…`, so the unit asserts
  simultaneously that `3e957464…` is the *previous, aborted* revision (line 27-29) and the *fixed* revision (line 30);
- `grep -rn f823b86a` over the whole clone finds **nothing**: `f823b86a…` appears in no file in the repo.

The recorded aborted attempt itself is accurate and consistent with the host: "an earlier attempt with the previous
script revision `3e957464…` aborted rc=1 before starting anything because its `LIVE=$(pgrep … | wc -l)` guard tripped
`set -euo pipefail` with zero servers; the STOP had already been renamed into `_to_delete` (verified, no deletion) and
no server/collector started." All of that is confirmed in §3 (no deletion, no process, no new log lines). The defect
is only the stale/wrong sha citation and its self-contradiction at line 30.

Consequence if executed as written: the operator's deploy/verify step would compare the host file against
`3e957464…`, so either the corrected bytes are rejected ("any difference from reviewed bytes — preserve the scene and
report"), or the broken revision is re-installed and the resume aborts rc=1 again. This blocks the resume.

Minor, also worth fixing in the same edit: the document title still says "rev 4" although the content changed again
(should be rev 5), and `done` in the real manifest is nested at `sessions[0].done`, not top level, so precondition 2's
`done`/`done.status` wording should name that path (no top-level `done` key exists).

## 3. Read-only host state (TASL-7) — PASS, matches the unit

`ssh tasl7`, read-only:

- markers: `~/r1_locks/trackx_evidence.active` absent; `~/r1_locks/trackp_evidence.active` absent;
  `r1_tracks/trks_drill.active` absent.
- `out/digits_mlp/s05_t7_20261113/STOP` absent; `_to_delete/STOP.retired.20261114T103527Z` present, **0 bytes,
  inode 57048847**, sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty), mode 664, original
  pause mtime preserved (2026-11-13 05:47:35 -0800). `_to_delete` is mode 700 and its mtime is 2026-11-14
  02:35:27 -0800 (= 10:35:27Z), i.e. the rename happened then; the file was renamed, not deleted.
- processes: no `llama-server`, no `trks_llm`, no collector (`trks_s05_t7`); only the watcher
  (`1388759/1388760 trks-watch`). `tmux ls` shows only `trks_watch` (no `trks_llm`, no `trks_s05_t7`, no
  `trks_s05t7resume`).
- `gpu0.lock`: `flock -n` succeeds → FREE; `nvidia-smi --query-compute-apps` empty.
- manifest: `sessions` length 1; `sessions[0].done = {roots 22, forks 6, leaves 0, failed 0, exhausted 0,
  deadline_hit false, status "paused"}`; ledger counts agree (`roots.jsonl` 22, `forks.jsonl` 6, `audit_runs.jsonl`
  700); `harness a3fedbb…`, `paper 8237fd02…`, `host TASL-7`, prior sha `5c849d15…` all match the unit.
  Nothing under `$RUN` was written after the pause except `_to_delete` and its parent's mtime; the launch log is still
  `2026-11-13 04:25` and no `llama_1810*` log was touched at 10:35Z — confirming nothing was started by the abort.
- installed launcher on the host is still the **old** sha `3e957464…` (fix not yet deployed); S0.5b sha `3685dfe6…` as
  the unit states.

## 4. Commit scope, secrets, next action

- `git diff --name-status e253a423^ e253a423` lists exactly the two files; 5 insertions / 2 deletions total (docs
  4+/1-, launcher 1+/1-). No other path, no mode change, no generated artifacts.
- No secret material: pattern scan for keys/tokens/private keys over both changed files is empty; the commit message
  carries no credentials. The unit's content remains ENGINEERING_ONLY.
- After a corrected unit is accepted, the next action is unchanged and correct in shape: deploy `f823b86a…` to
  `$R/launch/tasl7_digits_s05_20261113.sh` on TASL-7, verify sha256 `f823b86a…` + `bash -n` on the host, then
  `K=2 bash $R/launch/tasl7_digits_s05_20261113.sh` inside tmux `trks_s05t7resume`, expecting `trks_llm` with 2
  servers (18101/18102) and collector `trks_s05_t7`, then requiring `trks_s05_t7.cmd` byte-identical to the captured
  paused command (captured now: 786 B, sha256
  `fe9fae36311875470f6682539479ec2496e8be9bfe7bd56c5a32837dbd84054b`; `trks-run` regenerates `.cmd` from the same
  argument vector with `printf %q`, so byte identity is the right expectation). Capture that file before the resume,
  as the unit already requires.

## 5. Residual notes (non-blocking) and verdict

- `manifest["K"] = 5` is the **audit** K (`--k-audit`, `DEFAULT_K = 5`), not the server count; the launcher's `K = 2`
  is the number of `llama-server` processes. They are different keys and the resume does not conflict with the
  manifest (`trks collect` compares `MANIFEST_KEYS`, which includes `K` from the argument default 5, so the resume
  matches). Still, "k = 2" in the unit next to a manifest `K: 5` reads like a contradiction; one clause
  ("audit K = 5 in the manifest; 2 servers") would remove the ambiguity.
- The pause STOP was retired into `_to_delete` before the fix was accepted, and the unit's step 2 still describes the
  retirement as a future step; the added note covers this, but step 2 should be read as already done (it will no-op on
  `$RUN/STOP` being absent). Not a blocker, but the operator must not treat the absent STOP as an anomaly.
- `~/r1_locks/_to_delete/` holds four retired `trackx_evidence.active.*` files (pre-existing, not active markers).
- No defect in the launcher change itself. The single blocking problem is the resume unit's sha citation, which is a
  one-line documentation fix plus a rev-5 title bump in a follow-up commit on `trackS-ops-20261030`; the launcher
  bytes `f823b86a…` can be accepted as-is once the unit points at them.

VERDICT: changes required
