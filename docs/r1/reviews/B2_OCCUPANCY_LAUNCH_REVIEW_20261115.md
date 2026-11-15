# Independent review — B2 read-only occupancy check and marker-first launch/handover sequence — 15 November 2026

**Reviewer role:** fresh, independent, read-only reviewer. Not the author, not the B2 executor, not the
author of the exec record or the B1 patterns. No SSH/server access; no script was executed on TASL-7; no
commit or push; no secrets read. The only file written is this review file. The marker-primitive tests
below were run in a throw-away directory under `/private/tmp` (not the repository, not the host, not the
real lock directory) and created only `/private/tmp/b2marker-test/**`; nothing in the repo was changed.

**Reviewed unit.** Run HEAD **`8709dce792d45bbb5c05d9f7d239e19454efbb15`** (unchanged; `origin/ops-b2-20261115`
= same), run ID **`8709_20261115_b2`**, exec record on branch **`ops-b2-exec-20261115` @
`6bb27a8540644ff235a68527fd2b776e357ccd60`** (`origin/ops-b2-exec-20261115` = same; it adds only
`docs/r1/reports/b2_exec_20261115/*` and the accepted `docs/r1/reviews/B2_RUN_HEAD_REVIEW_20261115.md`;
the run-HEAD files PLAN/authorization/config are untouched — `git diff 8709dce7 6bb27a85` for them is empty).

Reviewed files (SHA-256 at `6bb27a85`; these are the bytes a launch should be held to):

| File | SHA-256 |
|---|---|
| `PLAN.md` | `5f1a9d527f078593daf0d315d01b68c99fb99882e2653300d002352fecfbc5f1` |
| `READY_RECORD.md` | `6f36edcfd47899918597c0962c39b994019d36edcf6f448581eaada01a061c07` |
| `prechecks.sh` | `db4ca3eb1b301056b68a5ac46cc2b37d29cbb944fd20f141513345ad13e5dbb1` |
| `create_marker.sh` | `28ca318747ba1853ac665ad579044b8fc9e0fd79dc82bf4769c72b38a0c13f23` |
| `preflight.sh` | `328d1c6e129e698f996895640db9c29fc9dfa7aa56261992d1d1c19ed403cc4f` |
| `start.sh` | `3c7f8b2d0a30194e29146256d183fc0d2aefa75018caf6d3399e7bd5fbd9c3af` |
| `receipt.sh` | `3867f24831b01900013934a04798120aa7be85ea8357d6ed2fb3c2ad67c65a6e` |

Review inputs: hand-off `proposals/B2_HANDOFF_EXEC_20261115.md` §5 steps 1–9 (at `8709dce7`); B1 patterns
`proposals/B1_TASL7_O2_EXECUTABLE_DRAFT_20261107.md`, `proposals/B1_FINAL_HOST_PREFLIGHT_INVOCATION_20261108.md`,
`reports/B1_TASL7_HANDOVER_COMMAND_BOUNDARY_20261107.md` (read by `git show` at their commits); the
operator's read-only TASL-7 census of 15 Nov (used as context only — it is a snapshot, not proof); the
local `b1-status-20261115` worktree; the Mac `READY.txt`.

---

## 1. What was checked and how

| # | Check | Evidence / result |
|---|---|---|
| 1 | (a) Read-only inventory covers §5.2 items | `prechecks.sh` records: GPU UUID + memory, GPU compute apps, `gpu0.lock` lease (`flock -n`), disk, `~/r1_locks` listing, Track X marker absence + Track P glob, watcher pgrep + watch.log line count, collectors with the hand-off's exact `--stop-file` pattern, `trks_llm`, P.3a, every `manifest.json` and `STOP` with device/inode/size/owner/group/type/mtime, STOP content hashes, `_d` retirement receipt + `_to_delete` listing. **Mostly PASS**; gaps in finding P-1. |
| 2 | (b) Bindings and B1-path separation | RUN_ID `8709_20261115_b2` (first four hex of the run HEAD + UTC date + phase — correct); RUN_DIR `…/b2_handover_8709_20261115_b2` (distinct from `b1_handover_7912_20261113_d`); output tree `…/exam-x/work/b2_8709_20261115_b2` (fresh direct child of `work_dir`, distinct); local receipt STATUS `$RUN_DIR/status-receipt.md` (not the run checkout's STATUS); gate+preflight capture `…_b` (distinct from the B1 `…_a`); preflight `--out …_a` (fresh direct child, distinct from `b1_host_preflight_20261108_a`); staged checkout `b2_paper_final_<HEAD>/paper` (distinct from `b1_paper_final_…`). The harness (`b1_harness_offline_stage_20261107_a/harness`, `a3fedbb`) and venv (`/home/dowling/exam-x/work/venv`, Python 3.13.4) are the B1 `_d` artifacts **by design** (hand-off §2/§5.6, "if the venv changed, STOP") — they are read-only inputs, not B2-owned paths; see finding P-2 (no venv-unchanged check). |
| 3 | (b)/(g) RUN_DIR exists before it is used | `prechecks.sh` L10 requires `[ -d "$RUN_DIR" ]` and writes `$RUN_DIR/prechecks.log`; the plan's bindings call RUN_DIR "new, absent" and the hand-off's `mkdir "$RUN_DIR"` is in step 3 (after the step-2 prechecks). **FAIL: the first step as written exits "STOP: run dir missing" unless the operator improvises a `mkdir`** — B-2. |
| 4 | (c) Marker creation | `create_marker.sh` calls `b1_o2_marker.py create --phase b2` with the new RUN_DIR, local receipt STATUS, exact HEAD/run ID, `set -C` receipt, empty-receipt STOP, and never the run checkout STATUS. **FAIL: it requires the STATUS file to be absent (`[ -e "$STATUS" ] && STOP`) while the marker primitive opens `--status` with `O_APPEND` and no `O_CREAT`, i.e. it requires the receipt file to already exist (B1 O2 draft; hand-off review R2-N1). Reproduced locally: with the STATUS absent the primitive raises `FileNotFoundError` and creates no marker; with an empty pre-created STATUS it creates `{"run_id":"8709_20261115_b2","head":"8709dce7…"}` and appends `## 2026-11-15 — Track X B2 running` — B-1.** |
| 5 | (d) STATUS publication | The clean separate worktree `.claude-worktrees/b1-status-20261115` is at `fcf52c09` (`origin/mac-b1-20261107`), branch `b1-status-20261115-local`, upstream `origin/mac-b1-20261107`, clean; current `docs/r1/STATUS.md` ends with the 14 Nov B1 `_d` entry. The plan's step 4 states the requirement in prose ("clean separate checkout of mac-b1-20261107 (Mac side), commit as Dowling Wong, push without force, verify remote") but does **not** give the exact heading, commit message/identity, commit-and-push commands, remote-verification command, or the B1-pattern STOP conditions (branch advance, dirty checkout, remote mismatch, failed push → preserve marker and STOP; no force/overwrite/retry). This is a mutation step and is not exact — P-3. |
| 6 | (e) Preflight → launch chain | `preflight.sh` runs after the plan's watcher step, uses `b1_host_preflight --head <HEAD> --out <fresh child>`, records `preflight.exit`, checks gate.log/gate.exit and marker; `start.sh` checks clean exact HEAD, marker, `preflight.exit=0`, unsets `LLAMACPP_CACHE_PROMPT`, uses `exam_runner b2` with `exam_b2_v2.json`, and `receipt.sh` launches it writing `b2.log`/`b2.exit` with no-clobber. **Partly PASS**; gaps: PREFLIGHT_PASS / exact GATE_PASS / owned-server-exit checks missing (P-4), evidence clobber on preflight re-run (P-5), environment unsets missing vs the reviewed B1 invocation (P-6), preflight exit status not propagated (P-7), script delivery to the host undefined (P-8). |
| 7 | (f) STOP conditions, no-retry, no-deletion, B1 untouched, Track S paused | The plan lists the STOPs (collector that cannot stop within 1 h, FORCED risk, P.3a running, any ambiguity; after-marker FORCED/unexpected touch/lost identity; preflight failure; missing logs/exit; marker/receipt mismatch at retirement). Scripts contain **no `rm`/`unlink`/`truncate`**; failed temp/log/exit files are preserved; B1 `_a`–`_d` paths are read-only; the marker is the Track S pause trigger. **Mostly PASS**; the preflight clobber (P-5) and the missing PREFLIGHT_PASS/cleanup checks (P-4) weaken the no-retry/STOP guarantees. |
| 8 | (g) READY.txt record | `READY_RECORD.md` is committed on the exec branch; Mac `READY.txt` SHA-256 is **`0ad9dd6f8f45e70e1bf43ac167c5f0b90885c8596434939553da803538d33faf`** (21,784 B) — matches; item 26 (lines 201–205) and item 27 (line 211) are quoted verbatim (verified programmatically); three-way base PASS is stated and I independently verified the code-unit review's `Reviewed base:`/last `Accepted commit:` and the config `paper_commit` all `37282ec3…`. **PASS — this closes the prior review's MINOR-3 and the hand-off's third leg.** |
| 9 | Run HEAD unchanged / exec branch scope | `origin/ops-b2-20261115` = `8709dce7`; the exec branch adds only `docs/r1/reports/b2_exec_20261115/*` and the accepted HEAD review file; the run-HEAD PLAN/note/config are byte-unchanged. The census snapshot is consistent with the plan's expectations (no marker, lease free, no GPU apps, GPU `GPU-ab72fb4a-…`, watcher pane 1388759/bash 1388760, no collectors/trks_llm/P.3a, manifests with some STOP files, `_d` receipts, staging clean exact HEAD, harness `a3fedbb`, venv Python 3.13.4). |

---

## 2. Findings

Severity: **BLOCKING** = the marker-first sequence as written fails or violates a standing rule and must
be fixed before the marker; **MAJOR** = a mutation/launch gate is not exactly specified or not enforced
as the plan/hand-off requires; **MINOR** = hardening/recording; **NIT** = wording.

| ID | Sev | Finding and evidence | Exact fix |
|---|---|---|---|
| **B-1** | **BLOCKING** | **`create_marker.sh` cannot create the marker.** L13 `[ -e "$STATUS" ] && STOP` forbids the local receipt STATUS; the primitive (`r1/scripts/b1_o2_marker.py:create`) opens `--status` with `O_WRONLY\|O_APPEND\|O_NOFOLLOW` and **no `O_CREAT`**, so it requires the receipt file to exist (B1 O2 draft: "`STATUS` to the existing B1-owned local receipt STATUS file"; hand-off review R2-N1: "$LOCAL_STATUS must exist before the marker step"). Local test: STATUS absent → `FileNotFoundError`, marker not created; STATUS present empty → marker created and heading appended. The hand-off step 3's inline code does `mkdir "$RUN_DIR"` but likewise does not create the receipt file. | In `create_marker.sh`: remove the "STATUS exists → STOP" check; create the receipt first with exclusive/no-clobber semantics and safe ownership (e.g. `umask 077; set -C; : > "$STATUS"` after checking `$STATUS` and its parents are non-symlink, or `install -m 600 /dev/null "$STATUS"`), verify it is an owned regular non-symlink file, then call the primitive (which appends the heading). Record the receipt inode/device and the creation order in the run record. Add the same pre-creation step to the plan §5.3/READY_RECORD so the sequence is self-contained. |
| **B-2** | **BLOCKING** | **`prechecks.sh` cannot run before the marker as sequenced.** L10 requires `$RUN_DIR` to exist; the plan's bindings call it "new, absent"; the hand-off creates `RUN_DIR` with `mkdir` in step 3 (after the step-2 prechecks). As written the first step exits `STOP: run dir missing`, before any inventory. | Add an explicit pre-marker `mkdir -m 700 "$RUN_DIR"` (after an absent/non-symlink/owned check, `umask 077`) at the start of plan step 2, before `prechecks.sh`; record it in the plan and prechecks log header. Alternatively write the pre-marker inventory to a separate dated capture directory and reserve `RUN_DIR` for the marker step, but then update all paths. |
| **P-1** | **MAJOR** | **Script delivery to TASL-7 is undefined.** The plan names `prechecks.sh`, `create_marker.sh`, `preflight.sh`, `receipt.sh`, `start.sh`, but never says where they live on the host or how the reviewed bytes get there; `receipt.sh` hard-codes `/bin/bash "$RUN_DIR/start.sh"`, so `start.sh` must exist on the host in `$RUN_DIR`; none of the exec files contains an `ssh`/`scp`/`install`/`cp`/here-doc delivery step. | Add a reviewed delivery step: install the exact reviewed scripts (the SHA-256s in the header) into `$RUN_DIR/scripts/` (or `$RUN_DIR/`) with exclusive no-clobber creation and record their SHA-256s and modes; update `receipt.sh` (or the plan) to use the installed paths; state that no script is edited after the SHA record. This is a mutation before the marker and must be in the exact sequence. |
| **P-2** | **MAJOR** | **Frozen venv/harness pin not checked before the launch chain.** The hand-off §2 requires "the frozen venv of hand-off `_d` §0.3; **if the venv changed, STOP**", and the harness `a3fedbb`; the plan lists the venv (Python 3.13.4) and harness, but no script checks the venv package set/identity or the harness commit/cleanliness before preflight/start (`start.sh` only checks the directory and `-x "$PY"`; preflight relies on the tool). A changed venv would be detected only by a later runner failure, after Track S has been paused. | Add a pre-preflight check: `"$PY" -VV` = Python 3.13.4, the `_d` frozen-venv identity (e.g. `pip freeze`/`uv pip freeze` SHA or the recorded freeze) matches, and the harness `git -C "$HARNESS" rev-parse HEAD` = `a3fedbb…` and clean; STOP on mismatch. Record the checks in the gate/preflight capture. |
| **P-3** | **MAJOR** | **STATUS publication is not an exact, reviewed mutation.** Plan step 4 is prose only; the B1 pattern requires: clean separate `mac-b1-20261107` checkout with only the intended STATUS append; after the marker, append the dated `## <date> — Track X B2 running` heading with the run ID and the run HEAD; commit as Dowling Wong (B1 pattern adds Codex as committer); push without force to `refs/heads/mac-b1-20261107`; verify the remote branch points to the status commit and record its SHA; STOP on branch advance/dirty/remote mismatch/failed push, preserve the marker, no force/overwrite/retry. The prepared worktree is correct (`fcf52c09`, upstream `origin/mac-b1-20261107`, clean), but the exact command block is missing. | Add a reviewed `status_publish.sh` (or an exact command block) with: HEAD/clean checks; the exact heading text (the marker primitive uses `## YYYY-MM-DD — Track X B2 running` + `Run: \`<run id>\`; reviewed checkout HEAD: \`<head>\`.`; the pushed STATUS heading should match "with the run ID and the run HEAD" — specify the exact lines), the commit identity/message, `git push origin HEAD:refs/heads/mac-b1-20261107` without force, `git ls-remote` verification equals the commit SHA, and the STOP conditions. |
| **P-4** | **MAJOR** | **Launch PASS conditions not enforced.** Hand-off §5.6 and the B1 invocation require both gate and preflight exits 0 **and** `PREFLIGHT_PASS`, the exact `GATE_PASS <HEAD> <rule>` line, a held-lock contention refusal/live server-descriptor/model-offload checks from the preflight, and independent verification that the owned server exited and the lease was released. `preflight.sh` checks only `gate.log` non-empty + `gate.exit=0` (not the exact `GATE_PASS` HEAD/rule), and only records `preflight.exit`; `start.sh` checks only `preflight.exit=0` — neither checks `PREFLIGHT_PASS`, the gate line, or the post-preflight lease/GPU state. The plan's step 6 claims "both gate and preflight exits 0 + PREFLIGHT_PASS", so the scripts under-enforce the plan. | In `preflight.sh`: require `grep -Fq "GATE_PASS $HEAD 53018aa7" "$CAP/gate.log"`; after the run, require `grep -Fq PREFLIGHT_PASS "$CAP/preflight.log"`; verify no compute app and `flock -n "$HOME/r1_locks/gpu0.lock" true` succeeds after the tool returns; STOP otherwise. In `start.sh`: re-check `preflight.exit=0` **and** `PREFLIGHT_PASS` in `$CAP/preflight.log`, plus the post-preflight idle-GPU/lease state before `exec`. |
| **P-5** | **MAJOR** | **Preflight can overwrite its own evidence on a re-run.** `preflight.sh` has no `set -C`; it writes `> "$CAP/preflight.log"` and `> "$CAP/preflight.exit"`; a retry (or a second invocation) silently clobbers the previous preflight evidence, against the hand-off/B1 rule "a failed, interrupted or unclear gate/probe/cleanup is STOP; retain evidence and do not retry" and the no-overwrite/no-deletion discipline. The B1 template uses exclusive (`set -C`, fresh capture) creation and `exit "$probe_rc"`. | Add `set -C` (and pre-checks that `$CAP/preflight.log`/`preflight.exit` are absent), or use a unique run-specific suffix; preserve any existing evidence; `exit "$rc"` at the end and add the missing B1-template CACHE/CAP symlink/ownership checks. |
| **P-6** | **MAJOR** | **B1 invocation environment hygiene missing.** The reviewed B1 invocation unsets `PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONUSERBASE GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_CONFIG_COUNT GIT_CONFIG_PARAMETERS GIT_CONFIG_GLOBAL GIT_CONFIG_SYSTEM` before the gate/preflight/launch. `preflight.sh` and `start.sh` export a few variables but do not unset these; a contaminated operator shell could make the checkout/config/git resolution load the wrong objects. | Add the same `unset` list to `preflight.sh` and `start.sh` (and to `create_marker.sh` for the checkout HEAD/clean checks), as in the B1 template; record the git/HEAD/clean checks in the capture. |
| **P-7** | **MINOR** | **`preflight.sh` exit status does not reflect the preflight result.** The last command is `tail -20 "$CAP/preflight.log"`, so the script exits 0 even when `preflight.exit` records a non-zero rc; a caller chaining `preflight.sh && ...` would continue after a failed preflight. | `exit "$rc"` after writing `preflight.exit` (and keep the rc visible in the log). |
| **P-8** | **MINOR** | **Pre-marker inventory gaps vs the hand-off §5.2 and the B1 boundary pattern** (the script records most but not all of: expected GPU UUID comparison; full `ps -eo user,pid,ppid,stat,etime,comm`/owners of GPU compute apps; the census watcher identity (`tmux` pane 1388759 / bash 1388760) and the watcher's script hash/three marker paths; `watch.log` presence/current position; full STATUS sources; traversal errors (the `find` calls use `2>/dev/null`, silently dropping permission/traversal errors); explicit sibling-`STOP` absence per manifest; a post-marker inventory command to compare against the pre-inventory; fail-closed on the unambiguous STOPs (marker present, `LEASE-BUSY`, collectors/`trks_llm`/P.3a running)). | Harden `prechecks.sh`: record expected-vs-actual GPU UUID (`GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`); add `ps -eo user,pid,ppid,stat,etime,comm` and `ps -o … -p 1388759,1388760`; hash `~/r1_tracks/bin/trks-watch`; list all three marker paths; require `watch.log`; capture `find` stderr and STOP if non-empty; record explicit sibling-STOP absence; add the exact post-marker inventory command (same find, new output) and require the operator to compare; make marker-present/lease-busy/collector/P.3a matches exit non-zero with a STOP message (or a separate `--gate` mode) so the unambiguous STOPs are enforced, not just logged. |
| **P-9** | **MINOR** | **The "handover check" half of hand-off step 6 is not in the sequence.** Step 6 requires "Host preflight **and handover check**, now" following the B1 boundary pattern; the exec plan/preflight cover the native preflight only; the boundary-doc read-only checks are partly in the pre-marker prechecks, not repeated after the watcher pause. | Add the post-watcher read-only handover check (process/owner/lease/marker/STOP-effect census) to plan step 5/6, or state explicitly that prechecks covers it and record the after-pause re-check (and its output path) in the capture. |
| **P-10** | **MINOR** | **`start.sh` does not verify the marker identity/receipt or P.3a.** It checks marker presence only; the hand-off step 9 treats a marker/receipt mismatch as a STOP, and step 5 requires P.3a safely paused/absent; `start.sh` checks neither. | Before `exec`, verify `$RUN_DIR/marker-receipt.json` `run_id`/`head` equal `8709_20261115_b2`/`8709dce7…` and the marker content matches; record P.3a absent/paused (from the post-watcher check); STOP otherwise. |
| **P-11** | **MINOR** | **No explicit venv/harness/checkout symlink and CACHE checks in `preflight.sh`** (B1 template: `[ ! -L "$CAP" ]`, `[ ! -L "$OUT" ]`, `[ ! -L "$CACHE" ]`, `[ -d "$PAPER" ] && [ ! -L "$PAPER" ]`, `[ -d "$HARNESS" ] && [ ! -L "$HARNESS" ]`, `[ -x "$PY" ]`); only `OUT` is checked. | Add the missing B1-template checks to `preflight.sh` before invoking the tool. |
| **N-1** | **NIT** | Plan step 1 still says "see OPEN QUESTION about READY.txt"; `READY_RECORD.md` now resolves it (three-way PASS, sha `0ad9dd6f…`). | Replace the stale reference with a pointer to `READY_RECORD.md` and the PASS line; record the READY record's SHA in the run record. |
| **N-2** | **NIT** | `prechecks.sh` L34–L35 redirection order: `ls -la … 2>&1 >&9` sends stderr to the terminal (not the log), and the missing-predecessor `echo` in L34 goes to the terminal; a missing retirement receipt is not visible in `prechecks.log`. | Use `>&9 2>&1` consistently (or a helper) so all diagnostics land in the log. |
| **N-3** | **NIT** | `preflight.sh` CACHE path uses suffix `_a` (`b2_final_gate_pycache_8709_20261115_a`) while the capture is `_b`; harmless but confusing, and CACHE is not checked absent/non-symlink. | Rename to `…_b` (and add the CACHE check from P-11). |
| **N-4** | **NIT** | `prechecks.sh` runs `flock -n … gpu0.lock` inside a "read-only" inventory; this is a transient lock acquisition (and would create the lock file if missing). The plan labels the step read-only. | Keep the check (it is the hand-off's lease check), but label it "transient lease probe, releases immediately; no writes to others' files" in the plan/log, and record the lock's device/inode/owner/type. |

---

## 3. What is verified as correct (no action)

- **Run HEAD / run ID / exec branch:** run HEAD stays `8709dce7…` (origin ref unchanged); exec-branch
  `6bb27a85` adds only the exec record and the accepted HEAD review file; run-HEAD files are unchanged.
- **Bindings:** RUN_ID = `8709_20261115_b2`; RUN_DIR, output tree, gate+preflight capture `_b`, fresh
  preflight `--out …_a`, staged checkout, and local receipt STATUS are correctly named, fresh/absent
  (host-side), and distinct from the B1 `_a`–`_d`/handover/gate paths; the harness and venv are the
  intended B1 `_d` read-only artifacts (hand-off §2/§5.6).
- **Marker primitive:** `--phase b2` exists and writes the `Track X B2 running` heading; the marker is
  exclusive-create, binds run ID + HEAD, records device/inode/SHA, and retirement is a separate reviewed
  unit; the local test reproduces the creation behaviour.
- **No deletion / B1 untouched / Track S pause:** no `rm`/`unlink`/`truncate` in the exec scripts; failed
  evidence is preserved; B1 `_a`–`_d` paths are read-only; the marker is the Track S pause trigger; the
  plan's STOP list matches the hand-off.
- **READY record:** Mac `READY.txt` SHA-256 `0ad9dd6f…` (21,784 B) matches the committed READY_RECORD;
  items 26/27 are verbatim; three-way base PASS verified independently → prior MINOR-3 and the hand-off's
  third leg are closed.
- **STATUS checkout:** `.claude-worktrees/b1-status-20261115` is clean at `fcf52c09` with upstream
  `origin/mac-b1-20261107`; the current STATUS ends with the 14 Nov B1 `_d` entry.
- **Census context:** consistent with the plan's expectations (marker absent, lease free, no GPU apps,
  GPU `GPU-ab72fb4a-…`, watcher pane 1388759/bash 1388760, no collectors/trks_llm/P.3a, manifests with
  some STOP entries, `_d` receipts, staging clean exact HEAD, harness `a3fedbb`, venv 3.13.4) — but it is
  a snapshot and the prechecks must re-collect it at B2 start (as the plan says).

---

## 4. Verdict

The occupancy check and launch sequence are close, but they are **not yet executable as written and do
not yet enforce every launch condition**. The two BLOCKING defects stop the sequence at its first two
steps: `prechecks.sh` cannot run before `RUN_DIR` exists (the plan creates it later), and
`create_marker.sh` forbids the local receipt STATUS file that the marker primitive requires to exist, so
the marker — the first mutation and the Track S pause trigger — cannot be created. The MAJOR items leave
the STATUS publication, script delivery, frozen-venv pin, and the preflight/launch PASS/no-clobber
guarantees under-specified or under-enforced.

**Minimal fixes required before the marker** (then re-submit the changed scripts/plan at the new SHAs):
1. B-2: create `RUN_DIR` (fresh, absent, 0700) before `prechecks.sh`, or move the prechecks capture out of RUN_DIR.
2. B-1: pre-create the local receipt STATUS (`$RUN_DIR/status-receipt.md`) with safe exclusive creation and remove the "STATUS exists → STOP" check; keep the empty-receipt STOP.
3. P-1: add the exact, reviewed script-delivery step (install the reviewed bytes into `$RUN_DIR`, no-clobber, record SHA-256; update `receipt.sh`/`start.sh` paths).
4. P-2: add the frozen-venv (Python 3.13.4 + freeze identity) and harness (`a3fedbb`, clean) checks before preflight/launch.
5. P-3: add the exact STATUS publication commands (heading/identity/commit/push refspec/remote verification/STOP conditions).
6. P-4: enforce `PREFLIGHT_PASS`, the exact `GATE_PASS <HEAD> <rule>`, and the post-preflight owned-server-exit/lease-release checks in `preflight.sh`/`start.sh`.
7. P-5: make preflight evidence creation exclusive/no-clobber (set -C or unique suffix) and propagate its exit status.
8. P-6/P-7/P-11: add the B1-template unsets, exit rc, and CAP/OUT/CACHE/PAPER/HARNESS/PY checks.
9. P-8/P-9/P-10: harden the prechecks (expected GPU UUID, process owners, watcher identity, watch.log, traversal-error STOP, explicit STOP absence, post-marker inventory, fail-closed unambiguous STOPs), add the post-watcher handover check, and check the marker receipt/P.3a in `start.sh`.
10. N-1…N-4: wording/recording fixes.

Do not create the marker or publish the STATUS until these are corrected and re-reviewed. Once corrected
(at a new exec-record commit; the run HEAD `8709dce7…` remains unchanged), the marker-first handover may
proceed under the monitored order `prechecks → marker → STATUS → watcher → preflight → launch`.

VERDICT: NOT ACCEPTED
