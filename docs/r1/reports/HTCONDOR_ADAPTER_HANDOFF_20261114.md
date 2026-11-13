# HTCondor adapter (desktop part) — hand-off for the cluster agent (14 November 2026)

**AI-assisted (Claude, Mac-local agent). Synthetic tests only: no `condor_*` binary, pool or real job was used.** This is Unit 2 of `prompts/MAC_OVERNIGHT_RUNBOOK_20261113.md`, applying the interpretations of its accepted review (S7, S8, N6). It covers paper branch `mac-htcondor-20261114` (from `mac-int-20261107`) and harness branch `r1-local-trackg-htc-20261114` (from `r1-local-trackg-20261109` @ `76bc49f2`). Nothing here submits a job: `real_submission_enabled` is false, and `--submit` is refused even when it is true (this draft has no submission path).

## 1. What is in it

| File | Purpose |
|---|---|
| `r1/scripts/htcondor/htc_config.json` | Settings with a `ruled:` / `measured:` / `proposed:` status, as in `hk2_config.json`. ETP-wiki facts are `proposed:` until your `POOL_FACTS.md` confirms them |
| `r1/scripts/htcondor/htc_submit.py` | `htc_job/v1` manifest → JDL; `--dry-run` writes the JDL and runs `condor_submit -dry-run` when it is on PATH |
| `r1/scripts/htcondor/htc_events.py` | Job event log → `queue_times.tsv` rows in the format of `HTCONDOR_PREP_RUNBOOK_20261114.md` §4.2, plus the M10 infrastructure outcome of HTCondor-level events |
| `r1/scripts/htcondor/htc_units.py` | Resume-safe work units for jobs that may be evicted and restarted |
| harness `src/autoresearch/trackg/gpu_identity.py` | HTCondor's short-UUID GPU assignment → full UUIDs for the M10 runner |
| `r1/tests/htcondor/test_htc_adapter.py`, harness `tests/trackg/test_trackg_gpu_identity.py` | Synthetic tests |

## 2. The manifest and the guards

`htc_job/v1` keys (no others): `name`, `kind` (`probe` or `track_g`), `image`, `cpus`, `memory_mb`, `disk_kb`, `walltime_s`, `gpus`, `gpu_device_name`, `placement` (`local` / `remote`), `executable`, `arguments`, `transfer_input_files`, `transfer_output_files`; optional `cloud_site`, `etp_ceph`, `accounting_group`, `executable_in_image` (renders `transfer_executable = False`), `resume_dir` (see §4); for `track_g` also `table_id`, `runner_timeout_s` and `runs_per_job`.

Refused:
- any GPU-share request: the key `gpu_memory_mb` or any key containing "GPUMemory" (`RequestGPUMemoryMB` is never rendered);
- a GPU job that is not `remote`, or that has no exact `GPUs_DeviceName` from the config list;
- `cloud_site` or `etp_ceph` on a local job; a remote job never gets `ProvidesETPResources`;
- transfer inputs that are missing, symlinks, or over 100 MB (10^6 bytes) in total, the executable included unless it lives in the image (use `/ceph` or xrootd for larger data);
- `$` in arguments (HTCondor expands `$(...)` macros) and control characters;
- a `track_g` manifest whose walltime does not exceed `runs_per_job` × `runner_timeout_s` plus the margin (600 s, `proposed:`; it must also cover setup such as image start and model load), so every run's own runner timeout fires before an HTCondor walltime hold. `runner_timeout_s` must be the value the runner will use (factor × measured run time, or the provisional value);
- a `track_g` GPU table without a pinned device name. CUDA OOM counts as `divergent` only with one GPU model per table (author's answer to Q8). `--table-pins FILE` (required for `track_g`) records each table's device name on first use and refuses a later manifest of the same table with another one.

Not checked (operator's care): site and device consistency, e.g. `etp_ceph` together with NEMO2's `cloud_site` (NEMO2 has no `/ceph/srv`) would never match.

Rendering: `universe = docker`, `docker_image`, the resource requests, `+RequestWalltime`, `request_GPUs` and `+RemoteJob = True` for remote jobs, `requirements` from the placement, device name, cloud site and `ProvidesEtpCeph`, an optional `accounting_group`, file transfer `YES` / `ON_EXIT`. Arguments use HTCondor's quoted "new syntax".

## 3. Queue-time rows and outcomes

`htc_events.py LOG --probe 123.0=P1 [--history H.json] [--year Y] [--utc-offset-minutes M] --tsv queue_times.tsv`:
- `wait_s` = first 001 − 000;
- `run_s` = 005 − last 001;
- `evictions` = number of 004 events, `holds` = number of 012 events;
- `exit` is one of: return value, `signal N`, `aborted`, `held`, `idle` or `running`.

The event log alone does not give `site`, `host` or `gpu_name`. Pass a JSON file `{job: {site, host, gpu_name}}` built from `condor_history -af …`, and record which attributes you used.

**Log time zone:** the parser takes event times as UTC unless `--utc-offset-minutes` says otherwise. Check how the pool writes them and set the offset.

M10 outcome of an HTCondor-level event (`infrastructure_outcome`) — each case has its own reason, and none of them is the runner's own `timeout`:

| Event | Kind | Reason |
|---|---|---|
| eviction (004) | `infrastructure_failure` | `htcondor_eviction`; `htcondor_preemption` if the text says "preempt" |
| hold code 34 subcode 102 (memory); or code 34 with another subcode, 3 or 26 or none and text "gone over (cgroup) memory limit" / "memory … exceed" | `infrastructure_failure` | `htcondor_memory_hold` |
| hold code 46 or 47 (duration or execute time exceeded); or a policy hold whose text names walltime (checked before memory) | `infrastructure_failure` | `htcondor_walltime_hold` |
| hold code 35 (invalid Docker image); or pull / manifest wording | `infrastructure_failure` | `htcondor_image_pull` |
| hold after 6 starts | `infrastructure_failure` | `htcondor_restart_limit` |
| hold code 34 subcode 104 (disk), any other code, or unrecognised text | `unclassified` | a human decides; never mapped silently |

`infrastructure_outcome` returns `{"final", "attempts"}`. `attempts` lists every eviction and hold with its reason. `final` is None when the job ended with a normal termination (005 with a return value): the run's own outcome then comes from the runner and its log, and earlier evictions or holds are history. Otherwise `final` is `unclassified` if any hold is unrecognised (all hold texts listed), else the first recognised hold, else the last eviction. An explicit time-zone suffix in the log (`Z`, `+01:00`) is applied; with one, `--utc-offset-minutes` must be 0.

The repeated-timeout cap (Unit 3) counts only the runner's `timeout` reason. Whether walltime holds should count toward it is an open author question.

## 4. Resume-safe units

`run_units(root, units, work)` skips every unit whose `UNIT_COMPLETE.json` exists and whose listed outputs still match (size and SHA-256).
- **Where `root` must live.** With `when_to_transfer_output = ON_EXIT` (the default rendering), a job restarted after an eviction starts with only its inputs (HTCondor manual), so markers in the sandbox are lost. Either put `root` on persistent storage (`/work`, local jobs only), or set the manifest's `resume_dir` and use it as `root`: it is then rendered as input and output with `ON_EXIT_OR_EVICT`, so it comes back on restart. Remote GPU jobs have no `/work`, so they need `resume_dir`; check that the pool's HTCondor supports `ON_EXIT_OR_EVICT`.
- **Writing the manifest.** The manifest is written atomically after the outputs: temporary file, fsync, `os.replace`, then fsync of the directory.
- **Interrupted unit.** If a unit was interrupted (for example by an eviction), its partial files are moved into `<unit>/_to_delete/attempt-<n>/`. Nothing is deleted, and the unit then runs again.
- **Mismatch.** A manifest whose outputs no longer match is a STOP (`UnitError`). The unit is not redone silently.

## 5. GPU identity inside a job

`gpu_identity.resolve_from_job(os.environ)` works as follows:
1. It reads the assignment from `NVIDIA_VISIBLE_DEVICES` and `_CONDOR_AssignedGPUs`. These must be UUID forms (index forms and `all` are refused).
2. It runs `nvidia-smi -L`, resolves each source separately (each id a unique prefix of a listed UUID, so short and full forms of one GPU agree), and requires the sources to name the same GPUs.
3. It returns the full UUIDs for `ResourceLimits.gpu_uuids`. The runner then sets its child's `CUDA_VISIBLE_DEVICES` to the full UUID.

`NVIDIA_VISIBLE_DEVICES` is never written. If `CUDA_VISIBLE_DEVICES` holds UUIDs, they must resolve to the same GPUs. If it holds indices, they are checked against `nvidia-smi -L` order (the runner sets `CUDA_DEVICE_ORDER=PCI_BUS_ID`; a container lists only its GPUs, numbered from 0). A list mixing both forms is refused.

## 6. What your report should feed back

1. The exact `GPUs_DeviceName` strings of the slots. The V100 32 GB string in the config is a guess.
2. Site limits on walltime.
3. Whether event-log times are local time or UTC.
4. What `NVIDIA_VISIBLE_DEVICES`, `CUDA_VISIBLE_DEVICES` and `_CONDOR_AssignedGPUs` contain inside a docker-universe GPU job (probe P4–P7 print them).
5. The real hold-reason texts, codes and subcodes seen for memory, disk and walltime holds on this pool.
6. Whether event-log times carry a time-zone suffix.
7. Whether `when_to_transfer_output = ON_EXIT_OR_EVICT` works on the pool (for `resume_dir`).

Each confirmed value moves from `proposed:` to `measured: <report>`, in a reviewed change.

## 7. Tests

- Paper: `pytest r1/tests/htcondor`.
- Harness: `PYTHONPATH=src pytest tests/trackg`. This includes the unchanged byte-for-byte `manager_proposal/v1` probe and the structural test; no base file changed.

Results (Mac VM, `/tmp/trackg_venv`): paper `r1/tests/htcondor` 67 passed; harness `tests/trackg` 177 passed (161 at `76bc49f2` plus 16 new, counting parametrized cases).
