# G.5 engine ENGINEERING smoke on TASL-2 (23 November 2026)

**Status: ENGINEERING_ONLY — no G.5 label or evidence run, no signed G.5 note, no G.5 evidence row, nothing sealed,
committed or pushed.** This report covers the smoke that harness report `G5_ENGINES_20261123` §6 items 1–15 and the
paper-side follow-up `G5_FOLLOWUPS_20261123` §3 (READY 96) require before any EVIDENCE G.5 job. All outcomes below are
synthetic/fake-engine outcomes on TASL-2's real host, real delegated scope, real file system and the real paper-side
job (`sweep2/t1_tasl/g5_job.run_job`) at paper main `76a3c71f`; the harness engines themselves were **not** run.

| Field | Value |
|---|---|
| Host / uid | TASL-2 / `dowling` (uid 1008) |
| GPU / lease | `GPU-4d623e76-7587-ee15-a633-46f60d220d94`; `~/r1_locks/gpu0.lock`; free before and after |
| Scope | `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0`, `taskset -c 16-31` |
| Paper checkout | `/home/dowling/r1_tracks/t1_tasl/paper_g5smoke` detached at `76a3c71fe94082e0c1274a1200c7e103a06b90bf`, clean |
| Harness checkouts | `harness_g5_7` @ `52e3c0b00df5753a96f323a8956338d88f365276`; `harness_g5_ar` @ `00829da116dd206a116e12ee9b108db40c2b5cbf`; both clean, `audit_g5.py` sha256 `1089dbac…d2d4` at both |
| Smoke root (TASL-2) | `/home/dowling/r1_engineering/tasl2_g5_smoke_20261123/` (`bin/`, `spec/`, `fake_harness_g7/`, `fake_harness_ar/`, `runs/`, `captures/`, `logs/`) |
| Report captures (Mac) | `docs/r1/reports/tasl_chain_20261122/G5_TASL2_ENGINE_SMOKE_20261123_captures/` (`SHA256SUMS` verifies) |
| TASL-7 | untouched; no llama-server started (item 13 NOT-EXERCISED) |
| HTCondor / deepthought | not used |

**Method (disclosed).** The job driver (`bin/driver.py`) runs *inside* a real delegated scope started with the exact
`systemd-run` argv of `t1_tasl_node.sh`'s g5 kind, exports the real `AR_TEST_CGROUP_PARENT`, and calls the real
`sweep2/t1_tasl/g5_job.run_job` with the real `g5_tasl`/`g1b_tasl`/`g4_tasl` helpers. The engine it invokes is a
*fake* engine (`code/audit_g5_fake.py`) committed in two scratch git checkouts (`fake_harness_g7`, `fake_harness_ar`)
that carries the contract marker/schemas/`TruncationInvalidManager` and writes synthetic campaign ledgers, audit rows
and `ar_*` child cgroups. Synthetic spec: copied from the committed unsigned `g5_tasl_spec.json`, nodes replaced by
twelve `smoke_*` nodes (all cpus 16-31, small runtimes), fake proposer `get`, synthetic `server_record.json`. No
sealed tree, real runs tree, real data, repo file, model or GPU compute was touched. See §8 for the exact commands.

## 1. Result table (harness report `G5_ENGINES_20261123` §6 items 1–15)

| # | Item | Status | What was exercised / exact evidence |
|---|---|---|---|
| 1 | Binary outputs, unread | **PASS** (job-side) | Campaign and audit `out.tar` hold binaries (`out/campaign/instance_*/runs/s001/work/model.pt`, `out/audit/runs/weights.npy`); the job read only named members and completed: `smoke_ok_campaigns_normal`, `smoke_ok_audits_normal` (`jobs/smoke_ok_*`, 13 / 6 tar members, binary members listed). |
| 2 | Edit-caused OOM | **PASS** (job-side; engine simulated) | Two synthetic edits allocated 9 GiB (> 8G `MemoryMax`) in `ar_*` children of the real scope. Kernel killed them (`memory.events` `oom`/`oom_kill` 0→1→2, `worker_rc=-9`, `parent_rc=-9`); the engine, job and wrapper survived (`ok=true`, wrapper rc 0). Rows written `divergent` (`nonzero_exit` for the killed worker, `oom_kill_memory_limit` for the killed frozen parent), never `infrastructure_failure`; `memory_events_cgroup` is the scope. Evidence: `jobs/smoke_oom_audits_oom.json` (`attribution`, `engine_meta`), `probe_scope.json`. |
| 3 | Edit-caused crash | **PASS** (job-side; engine simulated) | Synthetic worker raising → rc 1 and `ctypes.string_at(0)` segfault → rc -11; both rows `divergent`/`nonzero_exit`; job ok, no infrastructure failure. Evidence: `jobs/smoke_crash_audits_crash.json`. |
| 4 | Normalised code-state hashes (real campaign) | **NOT-EXERCISED** | Needs the reviewed engine's re-materialised normalised `code_state_sha256` on a real campaign. The fake engine writes synthetic hashes; `g5_job` accepted the synthetic kept chain (integrity) and the fake `chunk_record.json` reports `units_rematerialised = 6`, but the job does not read that field and no real normalised hash exists. Synthetic `chunk_record` with `units_rematerialised` in `jobs/smoke_ok_audits_normal.json`. |
| 5 | `outcome.value` finite | **PASS** | The real check `g5_seal.reduce_rows(spec, rows, chunk, "traindev")` ran on the real `smoke_ok` audit chunk: `read_rows` 60 rows, `traindev_rows` 30, `evaluation_rows_dropped` 30, no error (every `ok` row finite; eval-seed values checked then dropped). Evidence: `smoke_summary.json` → `paper_checks.reduce_rows_smoke_ok_audit`. |
| 6 | Isolation on every `ok`/`divergent` row | **PASS** (job-side) | All 60 rows of `smoke_ok` pass the real `g5_job.row_isolated` (`effective true`, `waivers {}`, `exceptions []`, `log_intact true`, no parent fields, no `gate_refusal`). Negative control: one row with `effective=false`/`waivers` through the real job gives `STOP 2 … not effectively isolated (stop_unisolated)`, class `node` (`jobs/smoke_gate_audits_gate-row.json`). The engine's own `noise_floor.check_effective` gate itself was not run (fake engine). |
| 7 | Infrastructure rows → STOP 7 | **PASS** | One synthetic final infrastructure row in the audit chunk gives exactly `STOP 7: final infrastructure failures in the audit chunk after the engine's reruns (a new attempt after diagnosis)`, class `infrastructure` (`jobs/smoke_infra_audits_infra.json`; row kinds `[infrastructure_failure, ok]`). |
| 8 | Not-run step carries top-level `code_state_sha256` | **PASS** (record-shaped) | The synthetic ledger's `not_run_duplicate` line carries the top-level `code_state_sha256`; the job's diagnostics count `counts.duplicate = 4`. Evidence: `jobs/smoke_ok_campaigns_normal.json` diagnostics + `out/campaign/instance_1_history/campaign_ledger.jsonl` in the attempt tar. The assembly-side reader for this field was not run. |
| 9 | Timing against the census | **PASS** (synthetic basis) | Synthetic run seconds 99 s > synthetic node basis 5 s gives `STOP: the median run time on the 4090 is above the declared timeout basis …`, class `timing` (`jobs/smoke_timing_campaigns_slow-run.json`); the normal runs (10 s vs basis 65 s) give `run_median_over_basis: 0`. Real C3/C5 census values were not used. |
| 10 | systemd OOM handling on the real scope | **PASS** | Host `systemd 249 (249.11-0ubuntu3.23)`; the g5 scope carries no `OOMPolicy` (and drops the unsupported property, per review M1); real scope `memory.oom.group = 0`, `memory.max = 8589934592`, `memory.swap.max = 0`; systemd-oomd manages `user@1008.service` (`ManagedOOMMemoryPressure=auto`) but does **not** monitor the scope (`oomd_monitors_scope=false`); the OOM that occurred was a kernel memcg OOM (memory.events rose), not a userspace kill. Evidence: `probe_scope.json`, `jobs/smoke_oom_audits_oom.json` → `cgroup_after` (`systemctl_show`, `oomd_lines`). |
| 11 | No orphans after deadline STOP / engine kill | **PASS** | Job deadline (`TimeoutExpired`): `out/run_cgroups_kill.json` `left: []`, `STOP 9 … ar_* run cgroups were killed (none left)`, scope scan after the job: no populated `ar_*` (`jobs/smoke_deadline_audits_deadline-child.json`). Deliberate external `kill -9` of the engine: engine rc -9, `run_cgroups_kill` `left: []`, no populated `ar_*` (`jobs/smoke_kill_audits_deliberate-kill.json`, `logs/job-kill-…log` line `deliberate_engine_kill pid=…`). The user can write `cgroup.kill` of an `ar_*` child in the delegated scope (`probe_scope.json` `kill_probe`). Empty leftover `ar_*` directories are removed by the smoke driver (recorded). |
| 12 | CPU-only node | **PASS** | `smoke_cpu` (device `cpu`): campaign and audit ran; engine argv has **no** `--gpu-uuid`; `CUDA_VISIBLE_DEVICES=""`. Evidence: `jobs/smoke_cpu_audits_normal.json` → `engine_meta.argv/cuda_visible_devices`. |
| 13 | Truncation on the real server | **NOT-EXERCISED** | No llama-server was started: a real server is not needed for an ENGINEERING job-path smoke and no G.5 authorization/label run exists. TASL-7 was not touched. The truncation rule (`TruncationInvalidManager`, `usage.completion_tokens == 4096` on `finish_reason: length`) remains engine/server-side and unexercised here; its contract string is recorded in every job record (`engine.truncation_invalid_in = autoresearch.trackg.audit_g5.TruncationInvalidManager`). |
| 14 | Disk | **PASS** (mechanism; real sizes not exercised) | Synthetic campaign `out.tar` 51,200 B; after the tar the attempt holds only `SHA256SUMS, attempt.json, diagnostics.json, job_record.json, out.tar` (the `out/` tree with working copies/snapshots is inside the tar; the tar therefore transiently doubles it before removal). Free disk at the end: 374,598,488,064 B (~349 GiB). Real per-wave sizes were not exercised (fake engine writes small payloads). Evidence: `jobs/smoke_ok_campaigns_normal.json`, `smoke_summary.json`. |
| 15 | The real job path | **PASS** (engineering-equivalent; literal g5 switch NOT-EXERCISED) | 21 job-scope invocations plus the orphan scenario's two in-scope runs (23 real `run_job` calls) through `g5_job.run_job` inside real delegated scopes created with the g5 wrapper's exact `systemd-run` argv; every job record has `cgroup.cgroup_parent` under `user@1008.service/app.slice/run-r….scope`. **The literal `t1_tasl_node.sh g5` path could not be exercised**: its first in-scope `g5_tasl.py` call refuses the ENGINEERING_ONLY spec (`STOP: spec must be g5_tasl_labels/v1, label EVIDENCE`, wrapper rc 2, no scope started, `logs/literal_g5_wrapper.log`) — correctly fail-closed, and it needs the signed note/real spec which must not be fabricated. |

## 2. READY 96 additions (`G5_FOLLOWUPS_REVIEW_20261123` open items / `G5_FOLLOWUPS_20261123` §3)

| Addition | Status | Evidence |
|---|---|---|
| (a) real scope path contains `user@<uid>.service` | **PASS** | Every job record's `cgroup.cgroup_parent` = `/sys/fs/cgroup/user.slice/user-1008.slice/user@1008.service/app.slice/run-r<hex>.scope`; probe reports `user_manager_component_present: true`. |
| (b) sibling scopes under `app.slice` are readable | **PASS** | Probe read sibling units' `cgroup.events`/`cgroup.procs` (incl. a named `smoke-sibling-probe-*.scope`); the orphan test read a populated `ar_*` in a default-named sibling `run-r….scope` and its start-of-job scan refused. `probe_scope.json`, `jobs/smoke_orphan_rule.json`. |
| (c) `memory.oom.group = 0`, systemd-oomd leaves the scope alone | **PASS** | `probe_scope.json` and `jobs/smoke_oom_audits_oom.json` → `cgroup_after.memory_oom_group = "0"`; `oomd_monitors_scope = false`; `oomctl` monitors `user@1006/1008.service`, not the scope; `ManagedOOMMemoryPressure=auto` on `user@1008.service`; kernel OOM observed with systemd 249 (no scope `OOMPolicy`). |
| (d) no `ar_*` processes after a deadline STOP and after a deliberate engine kill; inspect/clean after an orphan before the next job | **PASS** | Deadline and kill: `run_cgroups_kill.left == []`, no populated `ar_*` after the job (empty dirs removed and recorded). Orphan: a populated `ar_*` in a sibling scope gives the start-of-job refusal `STOP: ar_* run cgroups … hold processes: 1 populated ar_* run cgroup(s) in unit(s) run-r7e628b3ff3c244908a06aa7bb9c51b49.scope; operator rule: inspect user@<uid>.service/app.slice/*/ar_* …`; the operator then killed both pids, removed the `ar_*`, stopped the sibling scope (`cleanup.scope_gone=true`), and the rerun succeeded (`jobs/smoke_orphan_rule.json`). |
| Refusal names an old scope in `run-r…`/`run-u…` form | **PASS** | Refusal text above names `run-r7e628b3ff3c244908a06aa7bb9c51b49.scope` (SAFE_UNIT form); `ar_*` names never appear. |
| `check_engines` passes on both family checkouts (four needles) + `truncation_invalid_in` recorded | **PASS** | Real checkouts `harness_g5_7` @ `52e3c0b0` and `harness_g5_ar` @ `00829da1`, both clean, both `audit_g5.py` sha256 `1089dbac…d2d4`; `check_engines` returned the contract on both (`smoke_summary.json` → `paper_checks.check_engines_contract`); job records carry `engine.truncation_invalid_in = autoresearch.trackg.audit_g5.TruncationInvalidManager`. |
| Gate refusal gives STOP 2, node class, through the job | **PASS** | `STOP 2: audit run ('B', 7001) is not effectively isolated (stop_unisolated)`, class `node` (`jobs/smoke_gate_audits_gate-row.json`). |
| Engine's own deadline STOP through the job, both engines | **PASS** | Campaign `stop_kind=deadline` → `STOP 9: the campaign engine stopped at the job deadline …` class `node`; audit `stop_kind=deadline` → same for the audit engine; the next job on that node is refused (`STOP: smoke_stopdl has a STOP on record …`); the engines' text (a unique secret marker in `campaign_record`/`chunk_record` and stdout) never reaches a clear file (`secret_in_clear_files=false`). Evidence: `jobs/smoke_stopdl_campaigns_engine-deadline.json`, `jobs/smoke_stopdl_a_audits_engine-deadline.json`, `jobs/smoke_stopdl_campaigns_normal.json` (refusal), `logs/`. |
| Exit-time check on a clean exit: `out/run_cgroups_kill.json` with `left: []` | **PASS** | Every completed campaign and audit attempt contains `out/run_cgroups_kill.json` with `left: []` (e.g. `jobs/smoke_ok_*`, `jobs/smoke_cpu_*`). |

## 3. STOPs, refusals and orphans observed (all intentional; nothing left behind)

- `smoke_deadline_audits_deadline-child`: node-class `STOP 9` from the job's own subprocess timeout; `left: []`. This is
  the intended outcome, not a failure.
- `smoke_kill_audits_deliberate-kill`: the engine was SIGKILLed externally mid-run; the job recorded an
  infrastructure-class STOP for the missing rows, ran the same `ar_*` kill and tarred with `left: []`.
- `smoke_infra_audits_infra` (STOP 7), `smoke_gate_audits_gate-row` (STOP 2 node), `smoke_timing_campaigns_slow-run`
  (timing STOP), `smoke_stopdl*` (STOP 9 node) are the expected class mappings.
- `smoke_orphan_rule`: one refusal before any attempt (no attempt used), two processes killed by the operator, the
  empty `ar_*` removed, sibling scope stopped, rerun clean.
- No orphan STOP remained open; no populated `ar_*`, no leftover `run-*` scope, no engine/job process at the end
  (`logs/final_hygiene.txt`: `lease_free`, `nvidia-smi --query-compute-apps` empty, no `run-*.scope`, no
  `sleep`/`driver.py`/`sibling_scope` processes, GPU 353 MiB baseline / 0 % util).
- Empty `ar_*` cgroups created by the fake engine on deadline/kill are removed by the smoke driver inside the scope
  (recorded per capture); the scope itself is destroyed when the wrapper exits.

## 4. Housekeeping / authority

- **No G.5 label or evidence run**: no real engine, no real data, no model, no llama-server, no sealed tree, no G.5
  note, no label run, no evidence row. The job records use the code's fixed `label: EVIDENCE` schema constant but are
  synthetic fake-engine records under the engineering runs tree, unsealed and outside `/home/dowling/r1_tracks/t1_tasl/
  runs` and `sealed_*`; the committed paper spec/authorization is untouched.
- **No repo modification**: `paper_g5smoke` detached at `76a3c71f`, clean; `harness_g5_7` @ `52e3c0b0` and
  `harness_g5_ar` @ `00829da1`, both clean; the shared `harness_g5` checkout untouched. **No commit, no push.**
- **No deletion**: trial/superseded trees were moved aside to `_moved_aside/` on TASL-2. Real G1b/G4/AR sealed
  attempts, Track P archive/lease logs and `/home/dowling/r1_tracks/t1_tasl/runs` were not touched.
- **Lease/GPU released**: `flock -n ~/r1_locks/gpu0.lock` succeeds; no compute apps on the leased GPU; GPU free.
- **No HTCondor/deepthought used; TASL-7 untouched.**

## 5. Residuals and blockers

1. **The reviewed harness engines were not run** — this smoke exercises the paper-side job/scope/cgroup path with a
   fake engine. Real engine-only behaviours (item 4 normalised hashes, item 13 truncation on a real llama-server,
   the engine's own attribution logic) remain for the post-authorization EVIDENCE path.
2. **The literal `t1_tasl_node.sh g5` invocation cannot run** without the signed note and a launch-valid spec: the
   wrapper's first `g5_tasl.py` call refuses an ENGINEERING_ONLY spec (`rc 2`, no scope); fabricating a
   `g5_tasl_labels/v1`/`label: EVIDENCE` spec was deliberately not done. The job path was therefore exercised through
   a byte-equivalent scope launcher (`bin/smoke_wrapper.sh` + `bin/inner.sh`) with the real `g5_job.run_job`.
3. **Item 14 real per-wave sizes** were not measured (fake engine payloads are small); only the tar/doubling mechanism
   and free disk were recorded.
4. The synthetic spec uses `taskset -c 16-31` (the delegation for non-GPU work) rather than the committed spec's
   `0-7`/`8-15`; this is an engineering choice and is disclosed in `spec/smoke_spec.json`.

## 6. Evidence inventory and hashes

TASL-2 root: `/home/dowling/r1_engineering/tasl2_g5_smoke_20261123/` — raw `runs/`, `logs/`, `captures/`, `spec/`,
`bin/`, `fake_harness_g7/`, `fake_harness_ar/`, `fake_harness_src/`, `_moved_aside/`.
Mac captures: `docs/r1/reports/tasl_chain_20261122/G5_TASL2_ENGINE_SMOKE_20261123_captures/` with its own
`SHA256SUMS` (56 files, verified).

| Artifact | sha256 |
|---|---|
| captures `SHA256SUMS` | `a13b7fdb48954c9728a3ba9595ab0be0952efce4d4c90f6e4a8996e92d201ffc` |
| `smoke_summary.json` | `96f6c2eac95c98f4b217ed9f02f61edea822393a79901779acab479cec9e931d` |
| `probe_scope.json` | `2a7edd5a7f67f77e7f88add721e7b52df9b658f0a559c8d42f1039ff567c7b01` |
| synthetic spec `smoke_spec.json` | `6bd1fc9790f0410a7f27d304421949ecfc2c58832e1c133711605f390182d825` |
| synthetic `server_record.json` | `6db701da43cf9ebfecd601679de90ef808109741e8e8b4b4ac4e77e6fab45e8d` |
| paper `sweep2/t1_tasl/g5_job.py` at 76a3c71f | `1a8179d759e33416332d012262a22137a43a9ae80626c953f95f3f95554b8bff` |
| paper `sweep2/t1_tasl/g5_tasl.py` | `a4e873de70f1e4d6b867ee577c7e22f0f6e1c7ff081915b94867d631da8af67e` |
| paper `sweep2/t1_tasl/t1_tasl_node.sh` | `8c39844e7f0de4e0b9efdfe7a4eae348946d57cbd51ca613b4d8a7f1e360ae57` |
| committed `g5_tasl_spec.json` at 76a3c71f | `b25fd7f1b06e3491a97f60c44af1dfede4e7147a941aa9dc87e3823542bd9d0f` |
| real harness `audit_g5.py` (both families) | `1089dbac962d8dace9a7fd124309ee9354bef6e44fbdb5ec1b7a9dc6d3d3d2d4` |
| fake engine `audit_g5_fake.py` | `ae527620efbc24622fd7a1c48689badda69bf3f624d03064b6b08e435dc05000` |
| smoke driver `driver.py` | `c34a779a062a57008c7437688937d0a0093e8884d4cf496134855212fb30b723` |
| wrapper `smoke_wrapper.sh` | `4ee5f1d55e5e2a2a78817616ad527b27a4ed7af94b0ab4a621ea689aa723705f` |

## 7. Exact commands (TASL-2)

Setup (checkouts; no repo writes):

```bash
git clone --depth 1 https://github.com/dowlingwong/Agent_paper_B.git /home/dowling/r1_tracks/t1_tasl/paper_g5smoke
git -C /home/dowling/r1_tracks/t1_tasl/paper_g5smoke checkout --detach 76a3c71fe94082e0c1274a1200c7e103a06b90bf
git clone --no-hardlinks /home/dowling/r1_tracks/t1_tasl/harness_g5 /home/dowling/r1_tracks/t1_tasl/harness_g5_7
git -C /home/dowling/r1_tracks/t1_tasl/harness_g5_7 checkout --detach 52e3c0b00df5753a96f323a8956338d88f365276
git clone --no-hardlinks /home/dowling/r1_tracks/t1_tasl/harness_g5 /home/dowling/r1_tracks/t1_tasl/harness_g5_ar
git -C /home/dowling/r1_tracks/t1_tasl/harness_g5_ar checkout --detach 00829da116dd206a116e12ee9b108db40c2b5cbf
```

One smoke run (the full driver; moves previous trials aside, never deletes):

```bash
bash /home/dowling/r1_engineering/tasl2_g5_smoke_20261123/bin/run_all.sh
# equivalent single scope (the g5 wrapper argv, real g5_job.run_job, fake engine):
taskset -c 16-31 $S/bin/smoke_wrapper.sh job campaigns smoke_ok normal
taskset -c 16-31 $S/bin/smoke_wrapper.sh job audits   smoke_ok normal
taskset -c 16-31 $S/bin/smoke_wrapper.sh job audits   smoke_deadline deadline-child       # ~65 s job-timeout path
taskset -c 16-31 $S/bin/smoke_wrapper.sh job-kill audits smoke_kill deliberate-kill        # external SIGKILL
taskset -c 16-31 $S/bin/smoke_wrapper.sh orphan                                            # sibling ar_* refusal/clear/rerun
taskset -c 16-31 $S/bin/smoke_wrapper.sh probe                                             # (a)(b)(c) scope probe
```

Per-item evidence: `captures/jobs/<node>_<kind>_<scenario>.json` (job record fields, attempt/tar members,
`run_cgroups_kill`, engine meta, post-job `ar_*` scan), `captures/probe_scope.json`,
`captures/smoke_summary.json` (all of the above + real `check_engines` on both families + real
`g5_seal.reduce_rows` run), `captures/repo_and_hygiene_checks.txt`, `logs/` (raw wrapper/scope logs), `spec/`.

---

*AI-assisted (Claude). ENGINEERING_ONLY: this report is not evidence, not a label run, and not an authorization.*
