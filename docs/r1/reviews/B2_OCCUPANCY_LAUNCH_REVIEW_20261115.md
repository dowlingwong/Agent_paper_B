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

---

## Re-review round 3

**Re-reviewed at** the Lead's pushed target `ops-b2-exec-20261115` @ **`c9e10e4e66b04b1310a99387607136ee2fd74226`**
(`origin/ops-b2-exec-20261115` = same; the run HEAD remains `8709dce792d45bbb5c05d9f7d239e19454efbb15`,
`origin/ops-b2-20261115` = same), 15 November 2026 ≈17:05–17:35 CET, before any marker or STATUS
publication, by the same reviewer. No SSH, no host command, no marker/STATUS touched; the only writes are
this review file and a throw-away marker-primitive test under `/private/tmp` (round 2).

**Commit-pinning note (P-14).** The shared worktree/branch has advanced **locally** to
`3c4fbd2091f8809657205dc5658af44d4635ea10` (unpushed; adds `monitor.sh` and one line in `deliver.sh`);
`origin/ops-b2-exec-20261115` is still the Lead's `c9e10e4e`. All SHAs below are the **`c9e10e4e`** bytes
(verified: PLAN `1f87931e`, READY_RECORD `6f36edcf`, bootstrap `d7b66b24`, deliver `1f54fcf8`, prechecks
`3296e520`, inventory_after `01e87cf5`, create_marker `2041094a`, postwatch `42e48827`, preflight
`621889ab`, start `3b0a3517`, receipt `ef2b244a`, publish_status `1edbd4c0`, pins expected `711e8d7a`,
venv_pins `1cc9dcc0` — all match the Lead's list). The `3c4fbd20` delta (deliver `36acf799` + monitor.sh
`4079243b`) was inspected here (a benign append-only capture script; no deletion) but it is not part of
`c9e10e4e`; see P-14.

### Fixes verified as correct

- **B-1 fixed.** `bootstrap.sh` creates `RUN_DIR` (0700, fresh, non-symlink) and the **empty** owned
  receipt STATUS (`: >` under `set -C`, `chmod 600`); `create_marker.sh` now requires the empty owned
  regular STATUS (the primitive opens it O_APPEND without O_CREAT), calls `b1_o2_marker.py create
  --phase b2`, validates the receipt (`run_id`, `head`, dev/ino, 64-hex sha) and then runs
  `inventory_after.sh`. Round 2's local primitive test (absent STATUS → FileNotFoundError, no marker;
  empty STATUS → marker + `## 2026-11-15 — Track X B2 running`) matches this design.
- **B-2 fixed.** `bootstrap.sh` creates RUN_DIR before `prechecks.sh`; prechecks requires it; the PLAN's
  step 0/1 order is bootstrap → deliver → prechecks.
- **P-1 mostly fixed.** `deliver.sh` installs the reviewed files into `$RUN_DIR` over `ssh -o BatchMode=yes
  tasl7`, remote no-clobber (`set -C; cat >`), `chmod 700`, local-vs-remote SHA-256 comparison, and a
  `delivered-receipt.txt` (incomplete; P-12/P-18).
- **P-2 mostly fixed.** `preflight.sh` and `start.sh` unset the inherited `PYTHON*`/`GIT_*` variables,
  check the harness pin `a3fedbb…` and clean state, and `preflight.sh` verifies the frozen-venv pins via
  `importlib.metadata` (the seven packages are confirmed by `B1_RUN_HEAD_D_REVIEW_20261113` §4: openai
  2.36.0, langchain_openai 1.2.1, langchain_core 1.3.3, langgraph 1.1.10, pydantic 2.13.4,
  pydantic_core 2.46.4, httpx 0.28.1; the extra three in `pins/venv_pins.txt` are P-17). Name
  normalization in `importlib.metadata.version` was tested (hyphen/underscore forms resolve), so the
  `langchain_openai`/`pydantic_core`/`scikit-learn` names are not a false-failure source.
- **P-3 mostly fixed.** `publish_status.sh` appends the exact heading `## 2026-11-15 — Track X B2
  running` + Run/HEAD lines, commits as Dowling Wong, pushes `HEAD:refs/heads/mac-b1-20261107` without
  force, verifies the remote SHA, STOPs on dirty/advanced/failed push; defects: B-4, P-15, and the exact
  invocation is not in PLAN step 3.
- **P-4 fixed.** `preflight.sh` requires `gate.exit=0`, the exact `GATE_PASS <HEAD> <rule-sha>` line,
  `PREFLIGHT_PASS`, rc 0, then re-checks no GPU compute app and free `gpu0.lock`; `start.sh` re-checks
  `preflight.exit`, `PREFLIGHT_PASS`, the gate line, marker receipt, P.3a, GPU, clean HEAD, harness.
- **P-5/P-7 fixed.** Preflight capture is no-clobber (`set -C`; refuses existing `preflight.log`/exit) and
  the script exits with the preflight rc; `start.sh`/`receipt.sh` preserve no-retry semantics.
- **P-6/P-11 fixed.** Both scripts unset the B1-invocation list and preflight checks CAP/OUT/CACHE/PAPER/
  HARNESS/PY existence/symlink state (CAP must exist; OUT/CACHE absent).
- **P-8 largely fixed.** `prechecks.sh` is fail-closed: expected GPU UUID, 100 GB disk floor, lease,
  markers/locks, watcher (pgrep + tmux list-panes + watcher script SHA + watch.log position),
  collectors/trks_llm/P.3a, GPU compute apps, full `ps`, manifest/STOP inventories with `find` traversal
  errors as STOP, explicit sibling STOP presence/absence, `_d` retirement record, STATUS-source hashes,
  `PRECHECKS_PASS` + `prechecks/prechecks.ok` only on full pass. Caveats: P-19 (over-strict policy and
  no documented re-run path) and P-21 (census identity not explicitly compared).
- **P-9 partly fixed.** `postwatch_check.sh` implements watch.log growth, `priority marker seen`,
  `FORCED` STOP, servers-stopped check, GPU/lease/P.3a/collector/marker checks, and the touched-STOP
  sibling check; defects: B-3 (missing postwatch dir) and P-13 (stale inventory/timing).
- **P-10 fixed.** `start.sh` validates the marker receipt `run_id`/`head`, P.3a and GPU; `receipt.sh`
  writes `b2.log`/`b2.exit` with no-clobber and exits the runner rc.
- **N-1…N-4 fixed.** READY_RECORD integrated in the PLAN ("three-way base and gate (closed)"; no OPEN
  QUESTION), redirections corrected, capture suffix `_b` consistent, lease check labelled transient.

### Findings — round 3

**BLOCKING**

- **B-3 — the postwatch directory is never created, so `postwatch_check.sh` cannot run.**
  `bootstrap.sh` creates `$RUN_DIR/prechecks`, `$RUN_DIR/postmarker` and `$RUN_DIR/monitor` only (c9e10e4e
  L13; PLAN step 0 says "three subdirs"); `postwatch_check.sh` L12 requires `[ -d "$PW" ]` where
  `PW=$RUN_DIR/postwatch` and exits "missing postwatch dir" otherwise. The sequence therefore fails at
  step 4 **after** the marker is created and Track S paused (the handover stalls with the marker and a
  paused Track S; preflight/start then also stop). Fix: `bootstrap.sh` must create
  `mkdir -m 700 "$RUN_DIR/postwatch"` (and PLAN step 0 say four subdirs), or `postwatch_check.sh` must
  create it after an absent/non-symlink check.
- **B-4 — `publish_status.sh` cannot run from the prepared status checkout.**
  `publish_status.sh` L14 requires the checkout's current branch name to be exactly `mac-b1-20261107`;
  the prepared clean worktree `.claude-worktrees/b1-status-20261115` is on branch
  `b1-status-20261115-local` (upstream `origin/mac-b1-20261107`, HEAD `fcf52c09`, clean; verified). The
  STATUS publication therefore STOPs with "status checkout branch mismatch" at step 3, after the marker.
  Fix: either create/rename the local branch in the prepared checkout (e.g.
  `git -C ... switch -C mac-b1-20261107 --track origin/mac-b1-20261107` at `fcf52c09`) or relax the guard
  to a clean separate checkout whose HEAD equals `git ls-remote origin refs/heads/mac-b1-20261107` with
  the upstream set; record the exact invocation in PLAN step 3.

**MAJOR**

- **P-12 — delivery verifies transfer integrity, not the reviewed bytes.** `deliver.sh` compares each
  file's local SHA with the remote SHA (self-consistent), but it does not pin/verify the local exec
  checkout (HEAD, clean) nor compare against the reviewed file SHAs; `pins/expected.txt` contains only
  HEAD/rule/paper/harness/PY/prefix pins (no file SHAs) and is not read by any script; the delivered
  receipt records only 4 of the delivered files. The local branch is currently at the **unpushed**
  `3c4fbd20` while the reviewed/pushed target is `c9e10e4e`, so a delivery from the local worktree would
  ship an unreviewed delta. Fix: pin the exec commit (c9e10e4e, or a pushed 3c4fbd20 with this delta
  reviewed), require the local checkout clean at that commit, verify every delivered file's SHA against
  the reviewed commit (add file SHAs to `pins/expected.txt` or a file-SHA manifest), and record the exec
  commit + all delivered SHAs + UTC in `delivered-receipt.txt`.
- **P-13 — the postwatch "touched STOP" check reads the wrong inventory.** It iterates
  `$RUN_DIR/postmarker/stop_inventory_after.txt`, which `inventory_after.sh` captured immediately after
  marker creation — before the watcher's 60 s poll. The watcher's new STOPs are therefore never
  inspected, and the sibling check only re-validates pre-existing STOPs (which the prechecks inventory
  already guarantees). Fix: `postwatch_check.sh` must take a **fresh** manifest/STOP inventory after the
  watch.log pause (into `postwatch/`), compare it with `prechecks/manifest_inventory_before.txt` and
  `prechecks/stop_inventory_before.txt` (new/changed dev/ino/size/mtime), require every new/changed STOP
  to be a sibling of a known `manifest.json`, and STOP on any other changed path; keep a file-existence
  check for the postmarker inventory if it is still used.
- **P-14 — the exec branch has advanced to an unpushed, unreviewed commit.** The Lead's reviewed/pushed
  target is `c9e10e4e`; the local branch/worktree is at `3c4fbd20`, which adds `monitor.sh` and one
  `deliver.sh` line. The `3c4fbd20` content was inspected here (append-only capture; no deletion; it
  records runner/exit/log/batch_state/manifests/journal/GPU/lease/marker) and is benign, but it is not in
  the reviewed `c9e10e4e` file set. The PLAN step 0 still says "ten reviewed files" while the local
  deliver lists eleven. Fix: pin the exec commit for delivery (see P-12) and either (a) deliver from
  `c9e10e4e` (monitor optional/manual; PLAN unchanged) or (b) push `3c4fbd20`, update the PLAN step 0
  file list to eleven, and have the monitor delta covered by the pinned review; do not deliver from an
  unpinned worktree.
- **P-15 — publish commit identity and marker binding.** `publish_status.sh` commits as
  `Dowling Wong <dowling@users.noreply.github.com>`; the author's commits in this repository use
  `Dowling Wong <wangdowling@gmail.com>` (standing git instruction / B1 pattern). It also verifies only
  that the host marker receipt is non-empty (`ssh ... test -s`), not that its `run_id`/`head` match the
  arguments. Fix: use the author's commit identity; verify the host marker receipt contents
  (run_id/head/dev/ino/sha) before appending; record the receipt SHA; add the exact invocation to PLAN
  step 3.
- **P-16 — the frozen-venv/harness pin check runs only after the marker.** The venv-pin check is in
  `preflight.sh` (after marker/STATUS/watcher); if a pin differs, the failure stops after Track S is
  paused. The seven packages are verified from B1 §4; the extra three are P-17. Consider running the
  read-only pin checks in `prechecks` (pre-marker) or verifying the pins on the host before the marker;
  the hand-off places preflight after the marker, so a fail-closed STOP is safe but expensive.

**MINOR / NIT**

- **P-17.** `pins/venv_pins.txt` adds `pytest=9.0.3`, `numpy=2.4.4`, `scikit-learn=1.8.0` beyond the
  seven packages the cited `B1_RUN_HEAD_D_REVIEW_20261113` §4 confirms; these three are consistent with
  the B1 harness-lock docs (e.g. `BATCH_A_24OCT_HANDOFF.md`: scikit-learn 1.8.0, numpy 2.4.4, pytest
  9.0.3) but not with the §4 list. Cite the exact source or verify the exam venv before the marker (the
  preflight check will fail-closed if wrong).
- **P-18.** PLAN step 0 says "three subdirs" (add `postwatch`) and "ten reviewed files" (monitor delta,
  P-14); the bootstrap/deliver exact invocations and the local working directory/commit are not in the
  PLAN (deliver must be run from the exec-branch `docs/r1/reports/b2_exec_20261115/` directory; bootstrap
  transport to the host is unspecified); `deliver.sh` installs `publish_status.sh` on the host although it
  runs on the Mac; `delivered-receipt.txt` records only 4 SHAs; PLAN step 3 lacks the exact
  `publish_status.sh <status_checkout> <run_id> <head>` invocation.
- **P-19.** `prechecks.sh` fails closed on *any* running collector/`trks_llm`/P.3a or a held lease, while
  the marker-first design expects the watcher to pause/stop Track S (hand-off §5.2 records them; step 5
  expects them stopped). This is safe (conservative) and passes the current quiet census, but it would
  block a legitimate handover while Track S is active; document the policy and, after a precheck STOP,
  the re-run path (prechecks refuses to re-run while `prechecks.log` exists; preserve the old log by
  moving/renaming it — a move, not deletion — then re-run with the same reviewed script).
- **P-20.** `preflight.sh` writes `$RUN_DIR/preflight.ok` and `postwatch_check.sh` writes
  `postwatch.ok`/`postwatch.log` non-exclusively (no `set -C`/pre-existence checks); `prechecks.sh`
  `: > prechecks.ok` is non-exclusive. Add the no-clobber checks (or unique suffixes).
- **P-21.** `prechecks.sh` records the watcher's `pgrep`/`tmux list-panes`/script SHA/watch.log position
  but does not explicitly compare them with the census identity (pane 1388759 / bash 1388760) or flag a
  changed pane/script hash; the operator must compare manually. Add a recorded comparison (or a
  `watcher_identity` block) so a lost/restarted watcher is a script-level STOP.
- **N-5.** `prechecks.sh` uses `tmux list-panes`; the B1 boundary report notes the tmux client's socket
  behaviour cannot be certified side-effect-free from the static report — accepted here as the B1
  read-only inspection does the same; note it in the run record.
- **N-6.** The `3c4fbd20` `monitor.sh` is not in PLAN step 7/0; if kept, add it to the plan and pin it.
- **N-7.** `deliver.sh` does not check the remote host identity (e.g. `hostname` = TASL-7) or that the
  remote `$RUN_DIR` is a non-symlink directory; add.
- **N-8.** `publish_status.sh` writes its local receipt to `$SC/../b2_status_receipt.txt` with
  `2>/dev/null || true`; record it (or make the write/its location explicit and fatal).

### What was not checked

The host-side state is not re-measured here (no SSH): the `_b` gate capture contents, the actual
frozen-venv package versions, the prepared checkout on the host, and the TASL-7 census (the operator's
snapshot) are taken as recorded; the run must re-collect them with the reviewed scripts. The prepared
Mac status checkout `b1-status-20261115` was verified clean at `fcf52c09` with upstream
`origin/mac-b1-20261107` (branch `b1-status-20261115-local`); the run HEAD is unchanged at `8709dce7…`.

### Verdict

The round-2 fixes are largely correct and the B-1/B-2/P-4…P-11/N-1…N-4 items are verified. Two BLOCKING
defects remain and both bite **after** the marker is created: the postwatch directory is never created,
and the STATUS publication refuses the prepared checkout's branch name. The delivery path also lacks a
pinned-commit/reviewed-bytes check, and the postwatch touched-STOP test is stale. **Do not create the
marker or publish the STATUS.** Minimal fixes before re-review:

1. B-3: create `$RUN_DIR/postwatch` in `bootstrap.sh` (PLAN: four subdirs).
2. B-4: fix `publish_status.sh` branch handling (rename/create the branch in the prepared checkout, or
   relax the guard to a clean checkout whose HEAD equals the origin `mac-b1-20261107`), and give the
   exact invocation in PLAN step 3.
3. P-12/P-14: pin the exec commit (c9e10e4e, or push 3c4fbd20 and review the monitor delta), verify the
   local checkout clean at that commit, verify every delivered file's SHA against the reviewed commit,
   and record the commit + all SHAs + UTC in the delivered receipt.
4. P-13: make `postwatch_check.sh` take and compare a fresh after-watcher inventory; verify every
   new/changed STOP against known manifest parents.
5. P-15/P-16: fix the publish commit identity and marker-receipt binding; move/also run the venv/harness
   pin checks pre-marker (or verify them on the host first).
6. P-17…P-21/N-5…N-8: the minor items above (venv-pin source, PLAN/bootstrap/deliver exactness,
   precheck re-run policy, no-clobber `.ok`/logs, watcher-identity comparison, tmux note, deliver host
   check, publish receipt).

After the fixes are committed and pushed at a single pinned SHA (run HEAD `8709dce7…` unchanged), the
marker-first handover may start under the monitored order `bootstrap → deliver → prechecks → marker →
STATUS → watcher → postwatch → preflight → launch`; not before.

VERDICT: NOT ACCEPTED
