Reviewed base: ee6567a0315356551b514180933cb4a4f2f1475d (paper); harness e5830af34d5527e0a8b301731910807c94297b78

# HTCondor adapter (desktop part) — independent review record (14 November 2026)

MAC_OVERNIGHT_RUNBOOK_20261113 Unit 2. Paper branch `mac-htcondor-20261114` (from `mac-int-20261107` @ `a15300ca`); harness branch `r1-local-trackg-htc-20261114` (from `r1-local-trackg-20261109` @ `76bc49f2`). Three rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude).
- Round 1: changes requested (nine should-fix items, eight notes).
- Round 2: changes requested (`resume_dir` bypassed the transfer limit).
- Round 3: **accepted** at paper `ee6567a0`, harness `e5830af3`.

Accepted commit (round 3, last): paper ee6567a0315356551b514180933cb4a4f2f1475d, harness e5830af34d5527e0a8b301731910807c94297b78

Round-3 notes, not blocking, left for the next change: `resume_dir` accepts a trailing or doubled slash (`big/`), which HTCondor would treat as "copy the contents" (resume would silently not work; no data lost) — refuse empty path parts; hand-off §7 says 67 paper tests, now 68.

The round texts are reproduced unchanged below.

---

# Independent review — Unit 2 (HTCondor adapter, desktop part), round 1

Reviewer: freshly spawned independent reviewer (Claude, AI-assisted), 14 Nov 2026. I did not write this unit. I changed none of the reviewed branches or worktrees. Scratch work was under `/tmp/rev_u2/` (a detached worktree of the base, plus probe scripts), and it has been removed.

Reviewed:
- paper `mac-htcondor-20261114` @ `6b7d483d2f03df354437fd3216db202c0d787acb` (parent `a15300ca` = `gh/mac-int-20261107`);
- harness `r1-local-trackg-htc-20261114` @ `f51d74c7ce105755587361e4517d9748753bf3cd` (parent `76bc49f2`);
- HTC-Q1 in `/tmp/pb/questions_20261114.md`.

Read against: runbook Unit 2 (`gh/docs/runbooks-14nov`), the cluster runbook §0.3 and §4.2, the runbook review's S7, S8 and N6, and the author's Q8 answer.

## 1. What I ran

| Check | Result |
|---|---|
| `pytest r1/tests/htcondor` (paper) | **49 passed** |
| `pytest r1/tests/hk2` | 45 passed, 43 subtests passed |
| `pytest r1/tests --co` at base `a15300ca` vs head | Same 25 pre-existing collection errors ("harness src not found", environment), 623 → 672 collected (+49). Nothing else changed |
| `pytest tests/trackg` (harness) | **176 passed** (base 161 + 15 new) |
| T0 tests in `test_trackg_t0_identity.py` | byte-for-byte `manager_proposal/v1` probe, structural test and normalisation test: all PASSED; the file is unchanged |
| `git diff --name-status 76bc49f2..f51d74c7` | Only `A gpu_identity.py` and `A test_trackg_gpu_identity.py`; no base file changed |
| `git diff --stat a15300ca..6b7d483d` | Only the 6 new files |
| Commit metadata | Both commits: author and committer `Dowling Wong <wangdowling@gmail.com>`; `Co-Authored-By` and `Claude-Session` trailers present |
| Probe script | JDL injection attempts, event-date variants, multi-hold logs and hold-text variants (results in the findings) |
| HTCondor manual | Hold reason codes page (fetched); JDL page (fetched: argument new syntax, `when_to_transfer_output`). The `condor_submit` man page fetch was blocked (permission not answered), so `-dry-run` order and `$` expansion are checked from the JDL page and my own knowledge |

## 2. Requirement coverage

| Runbook item | Status |
|---|---|
| JDL from an `htc_job/v1` manifest: image, CPUs, memory, disk, walltime, GPUs, device name, site constraints, local/remote, accounting group, executable and arguments, transfer lists | ✔ (`htc_submit.py:51–184`, `199–239`) |
| `real_submission_enabled` defaults to false; `--submit` refused | ✔ (`htc_config.json:4`, `htc_submit.py:272–275`) |
| `--dry-run` runs `condor_submit -dry-run <file> <jdl>` when on PATH | ✔ The argument order is right (`htc_submit.py:247`). See S6 on the working directory |
| `RequestGPUMemoryMB` refused | ✔ by key, and again on the rendered text |
| > 100 MB transfer input refused | ✔ (counts MiB; executable not counted, see N4) |
| GPU job needs `+RemoteJob = True` and an exact `GPUs_DeviceName` | ✔ |
| Remote jobs never get `ProvidesETPResources` | ✔ (only added for `local`, plus a post-render check) |
| Statuses `ruled:` / `measured:` / `proposed:`; wiki facts `proposed:` (N6) | ✔ |
| Queue-time logger 000/001/004/005/012/013 → §4.2 rows; `wait_s` and `run_s` as N6; `site`/`host`/`gpu_name` from history | ✔ logic. See S2, N2 and N3 |
| Resume-safe units (atomic manifest, skip completed, `_to_delete` set-aside, nothing deleted) | ✔ helper. ✘ Not wired into the rendered JDL: see S4 |
| Outcome mapping (Q8; distinct reasons from the runner's `timeout`, S8) | ✔ distinct reasons. ✘ Fail-closed and code handling: see S1 and S3 |
| Track G GPU manifest without a device name refused; walltime > runner timeout + margin (S8) | ✔ per manifest. See S5 and S7 |
| GPU identity: short UUID → full UUID via `nvidia-smi -L`, ambiguity refused, environment never written, harness branch per S7 | ✔. See S8 |
| Hand-off for the cluster agent | ✔ mostly accurate. Gaps listed under S4, S9 and N7 |

## 3. Findings

### Blocking

None.

### Should-fix

**S1. An unrecognised hold does not always fail closed.** `r1/scripts/htcondor/htc_events.py:144–147`.

`infrastructure_outcome` returns on the **first** hold, whatever it is. The docstring (`:141`) and the hand-off (§3 table, "any other hold → `unclassified`") say an unrecognised hold wins.

Probe: a memory hold (code 34), then a release, then `via condor_hold (by user dwong)` gives `infrastructure_failure/htcondor_memory_hold`. The unclassified hold disappears.

*Fix:* classify all holds. If any one is `unclassified`, return `unclassified` and list every hold reason in `detail`. Otherwise return the first recognised hold. Add the two-hold case to `test_unrecognised_hold_is_unclassified_not_infrastructure`.

**S2. An explicit time-zone suffix in the event log is parsed and then discarded.** `htc_events.py:38` (HEAD regex) and `:50–59` (`_when`).

The regex accepts `+01:00` and `Z`, and then ignores them. `2026-11-14 01:00:00+01:00` becomes `01:00:00Z`, one hour wrong, silently. If a log carries `Z` and the caller also passes `--utc-offset-minutes`, the offset is applied twice. (As I remember it, HTCondor's `UTC` log option marks times with `Z`; the cluster agent should confirm.)

*Fix:* capture the suffix. If one is present, convert with it, and refuse a non-zero `--utc-offset-minutes` in the same call. Use the offset only for zone-less times. Add a test for `+01:00`, `Z` and `Z` with an offset.

**S3. The hold classification ignores the subcode of code 34 and misses HTCondor's own walltime and image codes.** `htc_events.py:91–99`.

From the HTCondor hold-reason table:
- code 34 (JobOutOfResources) means memory with subcode **102** and disk with subcode **104**;
- code 35 is InvalidDockerImage;
- codes 46 and 47 are JobDurationExceeded and JobExecuteExceeded.

Problems in the current code:
- `code == 34` maps **any** code-34 hold to `htcondor_memory_hold`. Probe: "exceeded its allocated disk; Code 34 Subcode 104" gives memory. The author's Q8 answer lists memory holds, not disk holds, so a disk hold should go to a human.
- Text precedence puts memory first. Probe: "periodic hold: walltime 3600 exceeded; MemoryUsage 100" gives memory.
- `"error response from daemon"` matches any Docker daemon error. Probe: "could not select device driver … [[gpu]]" gives `htcondor_image_pull`. It is still infrastructure, but the label is wrong.

*Fix:*
1. Decide by code and subcode first: 34/102 → memory; 34/104 → `unclassified` (or a separate `htcondor_disk_hold`, put to the author); 35 → image; 46/47 → walltime.
2. Fall back to text only when there is no code, or the code is a policy code (3 or 26, where ETP's `+RequestWalltime` policy will likely land).
3. Narrow the daemon-error rule to pull or manifest wording.
4. Add tests for 34/104, 35, 46 and 47.
5. Update the hand-off §3 table.

**S4. Resume-safe units do not survive an eviction with the JDL as rendered.** `htc_submit.py:228` (`when_to_transfer_output = ON_EXIT`) and `htc_units.py`. Hand-off §4.

HTCondor's JDL documentation says that with `ON_EXIT`, a job that is evicted and restarted "will start with only the executable and input files in the scratch directory sandbox". `UNIT_COMPLETE.json` files kept in the sandbox are therefore lost on eviction. Units then skip nothing, unless `root` is on persistent storage:
- local jobs: `/work`;
- remote jobs (every GPU job): none. TOpAS has `/ceph/srv`, NEMO2 has nothing.

The helper is correct. The integration does not meet the runbook's "a restarted job … detects completed units and skips them".

*Fix (either):*
- (a) Add an optional manifest key (e.g. `resume_dir`). When it is set, render `when_to_transfer_output = ON_EXIT_OR_EVICT` with that directory in `transfer_output_files`, so it comes back on restart. The cluster agent should check that this setting is supported on the pool's HTCondor version.
- (b) At minimum, state in the hand-off and in the `htc_units` docstring that `root` must be on `/work` (local jobs only), and that remote jobs currently lose completed units on eviction.

**S5. The walltime > runner timeout + margin check assumes one run per job, and the HTC-Q1 premise depends on it.** `htc_submit.py:174–183`; HTC-Q1.

A Track G job that runs several runs of a table in sequence can hit the job walltime during a later run, before that run's own runner timeout. That is exactly the escape from the item-8 cap that S8 wanted closed. Also:
- `runner_timeout_s` is self-declared; the runner's real timeout is factor × measured (`runner.py:112–116`);
- setup time (image start, environment, model load) is not part of it.

HTC-Q1's sentence "a walltime hold should only occur if the runner itself hangs" holds only for one run per job.

*Fix:*
- Add `runs_per_job` (int ≥ 1, required for `track_g`), and require `walltime_s > runs_per_job × runner_timeout_s + margin`.
- Or state and enforce "one run per Track G job".
- Say in the hand-off that `runner_timeout_s` must be the value the runner will use (factor × measured, or the provisional value).
- Reword HTC-Q1's premise to match.

**S6. `condor_submit -dry-run` runs in the caller's working directory, not the JDL's.** `htc_submit.py:247`; also `:165–171` and `:268`.

Validation resolves relative transfer inputs against the manifest's directory. The JDL can be written to `--out` (another directory). `condor_submit` resolves `executable`, `transfer_input_files` and `log` relative to its own working directory. So the dry run can check different files from the ones validated.

*Fix:*
- Pass `cwd=jdl_path.parent` to the runner.
- Either refuse `--out` different from the manifest directory when relative paths are present, or render `initialdir = <manifest dir>`.
- Have the test's fake `condor_submit` record `pwd`.

**S7. "Pinned device name per table" is enforced per manifest only.** `htc_submit.py:174–183`.

Q8's condition is one GPU model **per table**. Two `track_g` manifests with the same `table_id` and different `gpu_device_name` both pass.

*Fix:* an optional `--table-pins FILE` (JSON `table_id → device`), created on first use and checked afterwards. Or at least state "one table, one device name across all its manifests" in the hand-off and the docstring, as an operator rule.

**S8. `gpu_identity` compares raw strings, and its handling of index-form `CUDA_VISIBLE_DEVICES` is loose.** Harness `src/autoresearch/trackg/gpu_identity.py:67–80`.

- (a) The two sources are compared as raw strings (`:68–70`). If one holds the short form (`GPU-1a2b3c4d`) and the other the full UUID, which is plausible inside a docker-universe job, they are refused as "disagree", though they name the same GPU. This fails closed, but it would block real jobs.
- (b) A mixed `CUDA_VISIBLE_DEVICES` (`GPU-…,1`) is "ignored", not refused (`:75`).
- (c) An index form is ignored. The runner sets `CUDA_DEVICE_ORDER=PCI_BUS_ID` (`runner.py:249`), which matches `nvidia-smi` order. So it can be checked cheaply: the indices must be < the number of listed GPUs, and `{listed[i]}` must equal the resolved set. That is what S7 meant by "require them to agree".

*Fix:*
- Resolve each source separately against `nvidia-smi -L` and compare the full-UUID sets.
- Refuse mixed lists.
- Check index forms against the `nvidia-smi` order instead of ignoring them.
- Add tests: short vs full agreeing; index `1` with one visible GPU refused.

**S9. The hand-off does not say how `infrastructure_outcome` combines with a job that finished normally.** `htc_events.py:138–153`; hand-off §3.

Probe: user hold → release → normal termination, return value 0. `exit=0`, but `infrastructure_outcome` = `unclassified`. Likewise an eviction followed by success returns `infrastructure_failure/htcondor_eviction`. The docstring says this is "for the resume logic". A cluster agent or Unit 3 consumer could still override a good run with an infrastructure failure.

*Fix:* return two fields:
- `final`: infrastructure only if the job did not end with 005 normal termination;
- `attempts`: a list of every eviction or hold with its reason.

Or document the precedence rule explicitly in the hand-off §3.

### Notes

- **N1. Macro expansion in arguments** (`htc_submit.py:102–109`, `187–196`). `$(Cluster)`, `$ENV(HOME)` and `$$(Name)` are accepted and rendered verbatim. `condor_submit` expands them at submit time and the starter expands them at match time. No extra line can be injected (newlines and commas in paths are refused; quotes are escaped correctly per the JDL page's new-syntax example), but values can be. Refuse `$` in arguments, or render it as `$(DOLLAR)`. Also refuse all control characters (`\x0b`, `\x0c`) and U+2028/2029 in arguments. HTCondor treats them as literal, but Python `splitlines()`-based tools would see extra lines.
- **N2. A missing terminator merges two events** (`htc_events.py:65–76`). A header line inside an open event is taken as body text, so two events merge silently. Real body lines are indented. Raise when `HEAD` matches at column 0 while an event is open.
- **N3. State after an eviction** (`htc_events.py:116–127`). A job whose last event is 004 is reported `running`; it is idle again. Use the last state event.
- **N4. Transfer-size count** (`htc_submit.py:165–173`). The executable, which HTCondor transfers by default, is not counted toward the 100 MB limit. The limit is computed in MiB (104.9 MB); use 10⁶ to stay strictly under the wiki's "100 MB", or label it MiB. There is no way to set `transfer_executable = False` for an executable that lives in the image (e.g. `/bin/bash`, which is accepted and would be shipped from the submit host).
- **N5. Small inputs.** `name` accepts `.` and `..` (`SAFE`); refuse names that are all dots. `--submit` writes the JDL before refusing (harmless). `--probe 123.000=P1` silently fails to match job `123.0`; normalise the key.
- **N6. Consistency checks the config cannot make.** `etp_ceph` with NEMO2's `cloud_site` (no `/ceph/srv`) would never match. Device/site consistency is not checked. Both are worth a sentence in the hand-off.
- **N7. Hand-off accuracy.** The test counts match (49 and 176). Unconfirmed wiki facts are labelled `proposed:` (N6 of the runbook review) ✔. "No base file changed" ✔. Add to §6 (feedback list): the hold codes and subcodes actually seen, the event-log time-zone suffix, and whether `ON_EXIT_OR_EVICT` is usable (for S4).
- **N8.** HTC-Q1 otherwise has options, a recommendation and a Chinese paste-ready line ✔. After S5, consider an option (c): count a walltime hold as a timeout when the job had one run and its runner timeout was below the walltime.

## 4. Summary

The unit covers every runbook item. The guards are correct where it matters most:
- whole GPUs only;
- remote-only GPU jobs with an exact device name;
- no `ProvidesETPResources` on remote jobs;
- submission off;
- correct `-dry-run` argument order;
- new-syntax argument quoting that matches the manual's example;
- line injection blocked.

The harness part is clean: new files only, both T0 tests unchanged and passing, and the environment never written.

Changes are requested for correctness of the M10 outcome mapping and of resume-safety:
- S1 (fail-closed holds), S2 (time-zone suffix discarded) and S3 (code-34 subcodes, codes 35/46/47) contradict the unit's own docstrings or the manual;
- S4 means resume-safe units do not work for evicted jobs with the rendered JDL;
- S5 to S9 are small.

All are cheap to fix.

Verdict: changes requested

---

# Independent review — Unit 2 (HTCondor adapter, desktop part), round 2

Reviewer: the same independent reviewer as round 1 (Claude, AI-assisted), 14 Nov 2026. I did not change the reviewed branches or worktrees. Scratch work was under `/tmp/rev_u2/`, and it has been removed.

Reviewed:
- paper `mac-htcondor-20261114` @ `57f39f4a02a5265c1a6db8411778a2b7b28731d1` (one commit on `6b7d483d`);
- harness `r1-local-trackg-htc-20261114` @ `e9d7e2bafb090fb61e7ba3ac1d23c675a87886c4` (one commit on `f51d74c7`);
- HTC-Q1 (revised) and HTC-Q2 in `/tmp/pb/questions_20261114.md`.

## 1. What I ran

| Check | Result |
|---|---|
| `pytest r1/tests/htcondor` | **67 passed** |
| `pytest r1/tests/hk2` | 45 passed, 43 subtests passed |
| `pytest r1/tests --co` | 690 collected (623 at base + 67), with the same 25 collection errors that exist at the base (environment: "harness src not found") |
| `pytest tests/trackg` (harness) | **177 passed**. The three T0 tests (byte-for-byte probe, structural, normalisation) PASSED |
| `git diff --name-status 76bc49f2..e9d7e2ba` | Only the two added files; no base file changed |
| Commit metadata | Both new commits: author and committer `Dowling Wong <wangdowling@gmail.com>`, with the `Co-Authored-By` and `Claude-Session` trailers. Both worktrees are clean |
| Probe script (scratch) | Re-ran the round-1 probes plus new ones for `resume_dir`, `runs_per_job`, codes and subcodes, zone suffixes, merged events and the `CUDA_VISIBLE_DEVICES` forms (results below) |

## 2. Round-1 findings

| Finding | Status | Evidence |
|---|---|---|
| S1 fail-closed holds | ✔ resolved | memory 34/102 → release → `condor_hold` code 1 gives `final.kind = unclassified` with all hold texts (probe and test) |
| S2 zone suffix | ✔ resolved | `+01:00` → 00:00Z; `Z` kept; `.5-0130` → 02:30Z; `Z` with an offset is refused |
| S3 codes and subcodes | ✔ resolved | 34/102 memory; 34/104 unclassified; 35 image; 46 walltime; code 1 unclassified; 26 + "walltime … MemoryUsage" gives walltime; 26 + "started 6 times" gives restart limit; a daemon error without pull wording is unclassified. The table matches the HTCondor hold-reason page. HTC-Q2 added |
| S4 resume across eviction | ✔ resolved in the JDL and the hand-off (`resume_dir` with `ON_EXIT_OR_EVICT`; pool support is feedback item 7). **But it opens a new guard gap: see R1** |
| S5 runs per job | ✔ resolved (`runs_per_job` required, integer ≥ 1, `True` refused). HTC-Q1's premise has been reworded and option (c) added |
| S6 dry-run working directory | ✔ resolved (cwd = manifest directory, absolute JDL path; the test records `pwd` with `--out`) |
| S7 table pins | ✔ resolved (`--table-pins` required for `track_g`; atomic write; a conflicting device is refused) |
| S8 GPU identity | ✔ resolved. Short and full forms of one GPU agree; index `0` is checked against `nvidia-smi` order; `1` is refused when it names another GPU; mixed lists are refused; the environment is unchanged after every call |
| S9 final vs attempts | ✔ resolved and documented in hand-off §3 |
| N1–N7 | ✔ resolved. `$`, `\x0b` and U+2028 refused; all-dots names refused; `--submit` refuses before writing; `--probe` keys normalised; a missing `...` terminator raises; 004 with no later 001 gives `idle`; the executable is counted (decimal MB) unless `executable_in_image` is set; hand-off §6 extended |

## 3. New findings

### Blocking

None.

### Should-fix

**R1. `resume_dir` bypasses the 100 MB transfer-input guard and is not checked to exist.** `r1/scripts/htcondor/htc_submit.py` (the `resume_dir` validation block in `validate_manifest`, and `render_jdl`, where it is added to `inputs`).

`resume_dir` is rendered into `transfer_input_files`, but nothing under it is counted toward `max_transfer_input_mb`, and it is never checked on the submit side. Probes:
- `resume_dir = "."` is **accepted**. It renders `transfer_input_files = .` and `transfer_output_files = .`, which transfers the whole manifest directory in, uncounted.
- `resume_dir = "units"` that does not exist is accepted. On the first start, the input transfer would fail. That is a hold (code 13), which the adapter correctly calls `unclassified`, but it is avoidable.
- Any existing large directory named as `resume_dir` is shipped regardless of the runbook's "over 100 MB of transfer input is refused".

*Fix:*
1. Refuse a `resume_dir` whose path parts include `.` or `..`, or that is empty after normalisation (`Path(resume).parts` must be non-empty and contain no `.` or `..`).
2. Require it to exist under the manifest directory as a real directory (not a symlink).
3. Add the sizes of all regular files under it (walk without following symlinks; refuse symlinks inside) to `total` before the limit check.
4. Add tests: `"."` refused; missing directory refused; a directory whose contents push the total over 100 MB refused.

### Notes

- **N1.** Hand-off §2's "Rendering:" sentence still says "file transfer `YES` / `ON_EXIT`". Add "`ON_EXIT_OR_EVICT` with `resume_dir`; `transfer_executable = False` with `executable_in_image`".
- **N2.** `CUDA_VISIBLE_DEVICES=""` or `-1` is refused with the message "mixes UUID and index forms". Refusing is fine (fail closed), but say "empty or negative" in the message.
- **N3.** `check_table_pin` writes the pin on a `--dry-run`, before `render_jdl`. A mistaken first dry run pins the table, and the operator must edit the file. This is acceptable as "entries are only added". Consider pinning only after rendering succeeds, and state in the hand-off that a dry run pins.
- **N4.** `final` after an eviction followed by abnormal termination (signal) is the eviction. Both are infrastructure, so there is no misclassification of kind. The runner's own `killed` record will also exist; Unit 3 should prefer the runner record when one exists.
- **N5.** HTC-Q2's rationale ("the request was too small, not the proposal") is arguable: a proposal can also cause large disk use (for example frequent checkpoints). The same is true for memory, which the author already put under infrastructure, so recommendation (b) is consistent. The question could name this trade-off in one line.
- **N6.** Whether `ON_EXIT_OR_EVICT` brings back the original inputs as well as the spooled files on restart is not settled from the desktop. The manual says the spooled files "will be transferred instead of the input files". The cluster agent should test one eviction before relying on `resume_dir`. Feedback item 7 covers this; its wording could name this point.

## 4. Summary

Every round-1 finding is resolved and tested. Harness: base files untouched, both T0 tests unchanged and passing, the environment never written. One new gap remains, R1: `resume_dir` can carry uncounted transfer input (including `.`), which defeats a runbook guard. It is a few lines and three tests to fix.

Verdict: changes requested

---

# Independent review — Unit 2 (HTCondor adapter, desktop part), round 3

Reviewer: the same independent reviewer as rounds 1 and 2 (Claude, AI-assisted), 14 Nov 2026. I did not change the reviewed branches or worktrees. Scratch work was under `/tmp/rev_u2/`, and it has been removed.

Reviewed:
- paper `mac-htcondor-20261114` @ `ee6567a0315356551b514180933cb4a4f2f1475d` (one commit on `57f39f4a`);
- harness `r1-local-trackg-htc-20261114` @ `e5830af34d5527e0a8b301731910807c94297b78` (one commit on `e9d7e2ba`);
- HTC-Q2 (revised).

## 1. What I ran

| Check | Result |
|---|---|
| `pytest r1/tests/htcondor` | **68 passed** |
| `pytest r1/tests/hk2` | 45 passed, 43 subtests passed |
| `pytest r1/tests --co` | 691 collected (623 at base + 68), with the same 25 collection errors that exist at the base (environment) |
| `pytest tests/trackg` (harness) | **177 passed**. The three T0 tests (byte-for-byte probe, structural, normalisation) PASSED |
| `git diff --name-status 76bc49f2..e5830af3` | Only the two added files; no base file changed |
| Commit metadata | Both new commits: author and committer `Dowling Wong <wangdowling@gmail.com>`, with the `Co-Authored-By` and `Claude-Session` trailers. Both worktrees are clean |
| Scratch probe of `resume_dir` (Python 3.13.18) | `"."` and `"./big"` refused; a symlinked directory refused; hidden files under it are counted (60 MB hidden + 50 MB → refused as over 100 MB); a missing directory refused (covered by the tests) |

## 2. Round-2 findings

| Finding | Status |
|---|---|
| R1: `resume_dir` bypasses the transfer limit and is not checked to exist | ✔ Resolved. `.` and `..` parts are refused; it must be an existing, non-symlink directory; files under it, hidden ones included, count toward the total; a symlink inside it is refused. Tests cover a missing directory, `.`, over 100 MB, and a symlink |
| N1: stale rendering sentence in the hand-off | ✔ |
| N2: message for an empty or negative `CUDA_VISIBLE_DEVICES` | ✔ (harness `gpu_identity.py`: a separate message; mixed forms keep their own) |
| N3: a dry run pins the table | ✔ Documented in hand-off §2. Keeping pin-before-render is acceptable: `render_jdl` can only fail on its two internal assertions, which `validate_manifest` already prevents |
| N4: the runner's record decides the run outcome | ✔ hand-off §3 |
| N5: HTC-Q2 rationale | ✔ The trade-off is named |
| N6: test one eviction before relying on `resume_dir` | ✔ hand-off §6, item 7 |

## 3. New findings

### Blocking

None.

### Should-fix

None.

### Notes (optional; they do not block acceptance)

- **N1. Trailing or doubled slash in `resume_dir`.** `"big/"` and `"big//"` are accepted (`htc_submit.py`, the `resume_dir` check splits on `/` and does not refuse empty parts). In HTCondor's `transfer_input_files`, a trailing `/` transfers the directory's *contents* into the sandbox root rather than the directory itself. The resume root would then not round-trip, and units would rerun. That wastes compute, but loses no data and is not a guard bypass. The string comparison with `transfer_output_files` also misses `"big/"` vs `"big"`. Suggested follow-up: refuse empty parts, i.e. `any(p in ("", ".", "..") for p in resume.split("/"))`.
- **N2. Stale test count.** Hand-off §7 still says "paper `r1/tests/htcondor` 67 passed"; it is now 68.

## 4. Summary

Every finding from rounds 1 and 2 is resolved and tested. The runbook's Unit 2 requirements are met:
- the guards: whole GPUs only; remote-only GPU jobs with an exact device name; no `ProvidesETPResources` on remote jobs; the 100 MB transfer limit, now including the executable and `resume_dir`; `$` and control characters refused; submission off by default;
- `condor_submit -dry-run` with the right argument order, run in the manifest's directory;
- the queue-time logger, with zone handling and fail-closed parsing;
- resume-safe units, with eviction-surviving rendering and the pool-support test left to the cluster agent;
- the Q8 / S8 outcome mapping, with distinct HTCondor reasons, codes and subcodes first, fail-closed on unrecognised holds, and `final` vs `attempts`;
- the Track G pins and the `runs_per_job` walltime check;
- the harness GPU identity, with base files untouched, both T0 tests unchanged and passing, and the environment never written.

The two notes above are optional follow-ups.

Verdict: accepted
Accepted commit: paper ee6567a0315356551b514180933cb4a4f2f1475d, harness e5830af34d5527e0a8b301731910807c94297b78

