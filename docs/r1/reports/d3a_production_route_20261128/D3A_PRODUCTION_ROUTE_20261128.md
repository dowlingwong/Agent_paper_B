# D.3a production route — launch manifest, environment disposition, endpoint-to-lease proof

**ENGINEERING_ONLY. No campaign, no audit, no outcome, no label or evaluation value was read.**
Task `compute/20261128-22`. Base `origin/main` `c3a484055f717865e4e6826833e405af41771013`; the
deliverable branch and its tip are stated in the `coord/compute` report. Frozen revision 5 is bound by
sha256 `700d93ca…`; this record does not change any signed value.

**Result.** The production route is prepared on TASL-2: the campaign manifest validates against the
G1 adapter with the frozen rev 5 pins; one exemplar deployment launch record and a 49-chunk matrix
validate against `r1_d3_launch/v1` and the retry ledger; and a short engineering start proves the
endpoint → listening process → GPU UUID → canonical lease chain on the RTX 4090. The route is **not
launched**. It waits for Local to bind `paper_commit`/`run_id` in the D.3a note, re-run P10/P11 at that
commit, and for the author's P9. G.5 keeps the TASL pair first.

## 1. Production launch manifest

`manifest.json` is a `r1_d3_campaign_manifest/v1` at the production work root
`/home/dowling/r1_tracks/work/d3a_prod_20261128/`. It was validated by
`r1.c3.d3.adapter.load_manifest(..., repo_root=<clean c3a48405 checkout>, check_files=True)`; the
command and output are in `captures/validation.txt`.

| Pin | Value |
|---|---|
| Pre-declaration | `docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261128_R5.md`, `700d93cac277a23f527f20a49f8606987e63f615547b435cf924b2706ec778ad` |
| G2 constants | `docs/r1/reports/d3_g2_20261127/d3_constants.json`, `4f5f686be8f0210bcb27dfe0968296d68cf54e7266fb72c9038e741163776a93` |
| Noise summary | `results/r1/noise/D28_REPAIR_20261027/summary.json`, `3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310` |
| P3 split | `r1/c3/splits/c3_p3_split_v1.json`, `b5967dd74a5b2a8bfd5f936aa57d00a231199eb36eedad5f005e3e0d6a71e569` |
| Design source | `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_REV6_LAUNCHERS_20261126.md`, `0d696535d94395c85592c7ac9483790483966bbe0bf48961d132c50aa49b922d` |
| Harness | `9bb416805175149eb87b71f28d77530572aa4bce` (clean checkout on the host) |
| Model / binary | GGUF `2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75`; `llama-server` `646caa007c99a5c9e644dac1c1a6a75f84ed78c5ca08da39a2fb690073d61e5b` |
| Design values | stage a; seven D.3 nodes; arms A0, A0R, A1, A2, FIXR3, EGATE, LADDER; W = 20; LLM cap = 80; trial budget 80; `append_only_summary`; verify seeds 20010+; split policy `vary` |

The route block pins `TASL-2`, RTX 4090 `GPU-4d623e76-7587-ee15-a633-46f60d220d94`, driver
`535.309.01`, canonical GPU lease `/home/dowling/r1_locks/gpu0.lock`, canonical CPU lease
`/home/dowling/r1_locks/cpus-16-31.lock`, CPU set `16-31` (TASL-2 CPUs 8–11 are never used), the
server argv, and the 20 GiB (`20G`) user scope. `manifest.json` sha256 is
`426705844e6dc35f1a8f16f17a1098df6e384db792014fd0e3e0b516b8eb4fa3`.

The server argv is exactly the frozen rev 5 §2 runtime, with the accepted P7 exact-runtime
`--no-webui`:

```
llama-server -m google_gemma-4-31B-it-Q4_K_M.gguf --host 127.0.0.1 --port 8095 \
  -ngl 999 -c 32768 -np 1 --jinja \
  --chat-template-kwargs {"enable_thinking":false} \
  --cache-type-k q8_0 --cache-type-v q8_0 --no-webui
```

`cache_prompt` is not a server flag; the harness default is false
(`LLAMACPP_CACHE_PROMPT`/`LLAMACACHE_PROMPT` unset in the sweep-2 record) and remains the
per-request pin. The launch record binds the SHA-256 of the canonical JSON argv array,
`94ba043497d324cb63e95b14ff56e01642c79c5e39bda1cad4ce33e8839a0517`; the captured shell-quoted
file hashes to `9ed9d647a7e2c9ededf14f12a170271577a3f12c2eb5abf8239756bc4f436ab6`, which is
byte-identical to the accepted P7 exact-runtime `server_argv.txt`.

## 2. Launch record, retry ledger, chunk matrix, run ID

`launch_A0_digits_mlp_r0.json` is one `r1_d3_launch/v1` chunk record. It is the exemplar for all 49
chunks. It carries the manifest pin, `observed: {probe: true}`, the bound proposer UUID, the
environment freeze, the canonical leases, the 20 GiB (`20G`) scope, and a `r1_d3_retry_ledger/v1` with
`run_id = d3a-prod-20261128-a`, one current attempt `a01`, and the chunk identity. It passes
`validate_deployment_launch`; output in `captures/validation.txt`.

The driver sequence is fixed (the executed proof is the same sequence without step 4):

1. a bash wrapper takes `flock -n` on `/home/dowling/r1_locks/cpus-16-31.lock` (fd 8) and
   `/home/dowling/r1_locks/gpu0.lock` (fd 9);
2. `python -m r1.c3.d3.probe --launch … --manifest … --observed … --lease-path …` writes
   `observed.json` while fd 9 is inherited (pre-server, as the chunk requires);
3. `llama-server` starts on the frozen argv under `taskset -c 16-31` and the same descriptors, and
   the driver waits for `/props`;
4. the reviewed `chunk_argv` (`python -m r1.c3.d3.campaign_chunk` with `--launch`, `--out`,
   `--manifest`, `--observed`) runs the chunk under the 20 GiB (`20G`) scope;
5. the server is stopped and both leases are released.

`production_driver.sh` in this directory is that driver. It was **not executed with `RUN_CHUNK=1`**;
it is a template for the launch, and its probe/server path is the one exercised by
`endpoint_run.sh`. The chunk branch is gated and was not run.

The reviewed `launch_ssh.launch` helper is **not used unchanged** on this host. A dry run
(`captures/launch_ssh_dryrun.txt`) shows two integration facts: its default scope is 16 GB, below the
20 GiB scope derived from the decimal 1.4× basis, and its rendered remote script calls `python3`, which on TASL-2 is 3.10.12, not the
3.11.17 audit venv; it also does not set `PYTHONPATH`/`AR_HARNESS_ROOT`. The driver supplies those
explicitly and passes the 20 GiB (`20G`) scope; the chunk/probe modules and their argv are unchanged. The
launcher code is not edited in this record.

`chunk_matrix.json` declares all 49 `(node, arm)` chunks at repetition 0, each with the same run id,
manifest sha256, 18 instance seeds 6201–6218, GPU model/UUID and canonical leases. It is a routing
record, not a claim that any chunk ran; the 49-row uniqueness/hash/seeds check is ad hoc in
`captures/validation.txt`, not a reviewed schema validator.

The exemplar's `hardware.environment_freeze.repo_commit` names the code base
`c3a48405` used for this engineering proof. At launch the record names the published launch commit
(a docs-only descendant whose code tree outside `docs/` and the spec is identical); the chunk's
runtime `observed.json` is generated on the host, not copied from this directory.

`run_id_ledger.json` records `d3a-prod-20261128-a` as **allocated and unused**. Before allocation no
host directory, report, record or branch used it; no Paper B job was running on TASL-2, TASL-7, Ada
or deepthought, and `condor_q -submitter dwong` held zero jobs at 19:28Z
(`captures/active_jobs_20261128.txt`). Any retry reuses the same `run_id`, adds a distinct
`attempt_id`, and seals the lost attempt under §3.1; no chunk starts in an existing directory.

## 3. Endpoint-to-lease proof

The engineering start ran 2026-11-28T19:27:30Z–19:27:37Z on TASL-2 (`captures/status.log`); the
executed script is `endpoint_run.sh`. One wrapper held the canonical GPU lease on fd 9 and CPU lease
on fd 8, ran the chunk-side probe **before**
loading the server, started the rev 5 server on the same descriptors, captured the chain, and stopped
the server. The probe must precede the server: `required_memory_mib = 22000` is free only on an empty
card, and the production chunk's `observed.json` is a pre-load record.

| Link | Evidence |
|---|---|
| Canonical GPU lease | `/home/dowling/r1_locks/gpu0.lock`, inode `66306:120088542`; wrapper PID 1673636 fd 9 and server PID 1673663 fd 9 (`captures/wrapper_fds.txt`, `captures/server_fds.txt`, `captures/lease_inodes.txt`) |
| Canonical CPU lease | `/home/dowling/r1_locks/cpus-16-31.lock`, inode `66306:120091889`; fd 8 in both processes; `Cpus_allowed_list: 16-31` |
| Endpoint | `ss -ltnp 'sport = :8095'` → `127.0.0.1:8095`, `llama-server`, pid 1673663, fd 12 (`captures/ss_listen.txt`) |
| Card actually used | `nvidia-smi --query-compute-apps`: `GPU-4d623e76-7587-ee15-a633-46f60d220d94, 1673663, 21618 MiB` (`captures/compute_apps_at_endpoint.txt`) |
| Chunk-side probe | `observed.json`: same host `TASL-2`, same UUID, `lease_path` = canonical `gpu0.lock`, `lease: true`, `memory_check: pass`, `other_processes_start.count: 0` |
| Runtime identity | `/v1/models` meta `n_ctx = 32768`; server log `n_ctx_slot = 32768, n_slots = 1`; build `b11669-620d2225c`; ftype `Q4_K - Medium` |
| Release | after SIGTERM: no compute app, card back to 353 MiB used, both leases closed (`captures/gpu_after_stop.txt`, `compute_apps_after_stop.txt`, `lease_end.txt`) |

A separate lock-only check at 19:31:35Z shows `FLOCK ADVISORY WRITE` on both canonical inodes
(`captures/lease_flock_check.txt`). `/proc/locks` names the transient `flock(1)` process that acquired
each lock; the lock itself lives on the open file description inherited by the wrapper and the server,
which is why the descriptor links above are the durable evidence. The check released both locks before
exit.

Every chunk uses this same proof by construction: the launch record names `gpu0.lock` and the bound
UUID; `probe.py` refuses a lease/UUID difference; `CampaignAccounting.from_job` compares the retry
ledger's GPU model with the observed live reservation and, for SSH, requires the observed UUID to
equal `hardware.proposer_gpu_uuid`; `campaign_chunk.check_hardware` refuses a host, model, proposer,
memory or lease difference before a campaign directory exists. The observed record in this directory
is the exemplar those checks consume.

The `/props` field `n_ctx` is absent in this llama.cpp build. The effective value is recorded by
`/v1/models` (`meta.n_ctx = 32768`) and by the server log line, as well as by the explicit `-c 32768`
argv; no context was lowered.

## 4. Campaign environment and image disposition

Rev 5 §2 pins the v1 GPU image
`ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296`
for the HTCondor proposer job. The selected production route is the reviewed direct SSH launcher on
TASL-2, where that container image cannot run: the `docker` socket is not accessible to the account
(no `docker` group; the read-only probe returns permission denied) and Apptainer/Singularity are
absent (`captures/environment_20261128.txt`). The route therefore runs the chunk in the host venv with
the P7 audit shim, not in the v1 image.

| Item | Production direct route | Rev 5 §2 image / §7.2 audit basis |
|---|---|---|
| Python | 3.11.17 (`/home/dowling/r1_tracks/venv/bin/python`) | 3.13.18 in the v1 image; 3.13.15 in the e1 audit basis |
| Packages | pandas 3.0.3, scikit-learn 1.8.0, numpy 2.4.4, scipy 1.17.1 via `PYTHONPATH=…/d3p7_20261128/pydeps_audit` | same four package versions in §7.2 |
| Harness | `9bb416805175149eb87b71f28d77530572aa4bce`, clean | same pin |
| CPU / GPU | i9-14900KF, CPUs 16–31; RTX 4090 24,564 MiB, driver 535.309.01 | RTX 4090 for every node; driver recorded per job |
| Container | none for the chunk; host process in a 20 GiB (`20G`) user scope | v1 image digest for the HTCondor route |

The deepthought audit side is P8 (`D3A_P8_HOST_20261128`, re-check ACCEPTED at `b70cfa01`); this
record changes neither that host nor `r1/tests`. The environment capture's base sample header is
19:27:58Z; its Python/shim/docker block was appended at 19:33:44Z (the file mtime; the first
draft rounded this to 19:34Z).

**Adjacent observation.** `r1/c3/d3/launch.py` still carries
`D3_IMAGE = ghcr.io/dowlingwong/r1-htc-gpu@sha256:49dd9900…` (the v2.2 digest), while rev 5 §2 binds
v1 `69b06b35…`. The direct route uses neither image; the HTCondor route would need a reviewed image
binding before it is used. This record does not edit that code.

### Data cache staging

`manifest.json`'s `data_cache_root` is
`/home/dowling/r1_tracks/work/d3a_prod_20261128/data_cache`. It did not exist when the first draft was
written; three OpenML nodes failed `prepare_node_dir` and `openml_climate`/`openml_sonar` received the
harness's empty placeholder cache. The reviewed screening cache was staged there and the production
host now passes `prepare_node_dir` for all seven nodes.

| Item | Value |
|---|---|
| Source | `docs/r1/reports/screen_cache_rebuild_20261127/` (ENGINEERING_ONLY; built under screening harness `6adf3859`, package set pandas 3.0.3 / scikit-learn 1.8.0 / numpy 2.4.4 / scipy 1.17.1) |
| Cache MANIFEST | `1987cc004aba9ead9705788d98cf05720855c5c0977be5c8eb3404f375382c21` |
| Cache tree | `3843b53cddca6c32f00f5a1eeb96f34a78ca2871720900f4e6b8c0f724130d07` |
| Staged root | `data_cache/<node>/data_cache`; six nodes including `openml_wdbc` (unused by D.3) |

Only the raw cache files are used; no harness code from `6adf3859` is executed in production. The
`6adf3859` provenance describes the builder, not the D.3 runtime (harness `9bb41680`).

The staged root cache's per-node tree hashes (each node has four data files and one ARFF); the
prepared campaign data maps equal these, with the two placeholder files noted below as the only
extra entries:

| Node | tree_sha256 |
|---|---|
| `openml_breast_w` | `058343f9759365d02c51eee9c52489ba84097a5428d0e2cf2e95a4456dbe9c94` |
| `openml_climate` | `3dc7f6bb3b80f5cebe63bc2eb187279ce204ca57137d6f24da80f5fee411cebd` |
| `openml_credit_approval` | `1dc25c439ca26164d3b47584d8ee70fe4427c95d224edc6bc5184546c1bc7c40` |
| `openml_ionosphere` | `97951b0b5341d5a44c6e0f367c0d9cab4d46949dbd898dfc92005569725d1c6f` |
| `openml_sonar` | `36d193ed8aa2be9f8d12ea9233da83b5698bdc285b3061af52e3d215370f2253` |

Two harness node trees (`openml_climate`, `openml_sonar`) carry an ignored
`data_cache/.gitignore` + `.gitkeep` placeholder; `prepare_node_dir` treats the directory as present
and would skip the root cache. The reviewed cache files were therefore also installed into those two
ignored node `data_cache` directories on TASL-2. The harness checkout remains clean
(`git status --porcelain` empty; the files are ignored), and the prepared campaign caches contain
exactly the four expected data files and one ARFF per node. `captures/cache_staging.txt` records the
verification; the placeholder files are the only extra entries and the node loader ignores them. A
clean harness checkout on another host needs the same two-dir install before a campaign.

This is a host staging condition, not a manifest change: the manifest hash above is unchanged.

This is a **disclosed substitution**, not a silent one: the direct route does not use the §2 image,
and Python differs from both the image and the audit basis. It reproduces the environment frozen by
the accepted P7 exact-runtime record itself (Python 3.11.17 and the same four package versions), so the
runtime gate was measured in this environment. The executable and shim are pinned:
`/home/dowling/.local/share/uv/python/cpython-3.11.17-linux-x86_64-gnu/bin/python3.11` sha256
`ff9b2ac4362b81c68622ffb1730f7138eb269177d9846399c521a44c5daffb0e`, and the audit shim tree
sha256 `1737028cdd5868c30d331e6f80133e5ec3b1c76f3d4f95df9de960d67370ef07` (regular files, no
`__pycache__`). `pyproject.toml` declares `requires-python = ">=3.11"`.

**This is a Level 2 binding, not a Local edit.** The note's §2 image pin is signed; changing the
`image:` line locally would itself leave the job record differing from a signed pin under §10. The
author needs one PLAN §10 row (or note amendment) that binds the direct-route environment, for
example:

```
image: none — direct SSH on TASL-2; host venv Python 3.11.17 + audit shim tree 1737028c…
       (v1 digest 69b06b35… remains the HTCondor-route image and is not used here)
```

Python 3.11.17 also has no field in the current key block, so the same row must bind it (or add an
`environment_sha256` field). The alternative is a container runtime on TASL-2 that can run the v1
image; none is currently available. Until that row exists, no D.3a campaign starts. No evidence run
has started, so this is a binding decision, not a STOP of existing evidence.

### 4.1 Endpoint identity guard before every chunk (compute/20261128-23)

Local's stub check (`coord/local` `1a6a2cf5`) found that when the template's own server failed to
bind, a separate responder on `127.0.0.1:8095` answered `/props` and the template went on to the
chunk. Readiness alone therefore does not prove which process serves the endpoint.

The production template now calls `r1.c3.d3.endpoint_guard` **after readiness** (so a foreign
responder is caught before the probe result is trusted) and **immediately before every chunk**. The
guard fails closed unless all of the following hold:

| Check | Evidence |
|---|---|
| listener owner | `ss -ltnp 'sport = :8095'` names exactly the PID the driver started, and no other PID |
| `/props` model | `model_path` equals the manifest `server_argv` `-m` path |
| `/props` context | `default_generation_settings.n_ctx` equals the manifest `server_argv` `-c` value |
| `/props` slots | `total_slots` equals the manifest `server_argv` `-np` value |
| compute PID | `nvidia-smi --query-compute-apps` lists that PID exactly once |
| compute card | that PID's GPU UUID equals the manifest `route.gpu_uuid` |
| canonical lease | the guard's inherited fd 9 and a server fd both point at the manifest
`route.gpu_lease_path` inode (`~/r1_locks/gpu0.lock`) |
| leased card | `nvidia-smi -i <lease index> --query-gpu=uuid` equals the manifest UUID |
| pre-server probe | `observed.json` has the same UUID, `lease: true` and the same lease path |

A mismatch writes `endpoint_check_<tag>.json` (`r1_d3_endpoint_check/v1`), then `STOP.json`
(`r1_d3_endpoint_stop/v1`), stops the server, seals the capture directory with `SHA256SUMS` and
exits **90** before `r1.c3.d3.campaign_chunk` is imported. The scene is kept, not deleted. A
multi-chunk driver may pass `CHUNK_ROWS` (tab-separated launch/out rows); the guard is called for
each row. The reviewed chunk argv is unchanged.

**Engineering test (no GPU, server process, campaign or label).**
`endpoint_guard_driver_test.sh` runs the production template with stub host commands and a real
HTTP `/props`; the guard itself is the repository module and reads `/proc` and the real response.

| Case | Result |
|---|---|
| `success` | guard passes after readiness and before the chunk; chunk stub is called; exit 0 |
| `foreign` | the started PID is alive but another process owns the port; STOP at `listener_pid`; chunk not called; seal OK; exit 90 |
| `bindfail` | the started server exits and a foreign responder answers `/props`; STOP at `server_alive`; chunk not called; seal OK; exit 90 |

The pytest set `r1/tests/test_d3_endpoint_guard.py` covers every identity check, the foreign-responder
case, the CLI STOP record and a real `HostProbe` integration against `/proc` and a live `/props`.
On TASL-2: **23 passed**. Captures are under `captures/endpoint_guard/`.

## 5. Resource basis

Measured at the exact runtime by the accepted P7 record
(`docs/r1/reports/d3a_p7_exact_20261128/D3A_P7_EXACT_RUNTIME_20261128.md`) and re-observed at the
endpoint start:

| Item | Value | Production bound |
|---|---|---|
| GPU memory peak | 21,999 MiB used; 2,184 MiB free minimum; 21,977 MiB at load | `required_memory_mib = 22000`; the empty-card probe read 23,830 MiB free |
| Host RAM peak | 14.27 GB (decimal) of 67.12 GB total | 20 GiB (`20G`) cgroup ≈ 21.47 GB decimal, ≈ 1.50× the 14.27 GB decimal peak; the decimal 1.4× calculation (19.98 GB) is rounded to a 20G scope. `MemorySwapMax=0`; the endpoint proof did **not** exercise the cgroup, so this is a derived bound, not a measured scope |
| Scratch, one campaign | largest observed 858,382 B (A2, `openml_climate__s6301`); other arms 266–630 kB | 18 instances × largest = 15,450,876 B ≈ 14.7 MiB |
| Scratch, one chunk | 18 × largest P7 campaign (858,382 B) + OpenML cache (123,531 B) | ≈ 14.9 MiB **derived**, not a measured 18-instance chunk (P7 §4 warns against multiplying its smoke); 32 MiB design floor, 1 GiB free-space check |
| Wall time | no scheduler on the direct route | no wall-clock limit (R1-NO-TIMEOUT); per-arm 1.5× requests, if a scheduler is ever used: A0 3,268 s; A0R/A1 3,424 s; A2 7,470 s; FIXR3 1,089 s; EGATE 467 s; LADDER 3,113 s |
| GPU-hours | 28.85 GPU-h seven-node projection; 32.91 A0R sensitivity | reporting threshold 140 GPU-h |

The 49 chunks are serial on one RTX 4090 by the reviewed per-node placement: expected elapsed
≈ 28.85 h, 32.91 h in the A0R sensitivity, plus gaps. A second RTX 4090 (TASL-7) is the same GPU
model and may serve a node only after that node's own host check; it does not change the per-instance
model rule. Disk free at the production root was 349,887,284 KB (≈ 334 GiB) at start.

For the D.3a note's pending fields, the values this basis supports are: `layout_request_walltime_s`
= none (direct SSH; if a scheduler is used, 7,470 s for the A2 arm and the per-arm rows above);
`layout_request_disk_kb` = 22,000 if a scheduler requests disk (15,450,876 B × 1.4 ≈ 21,631 KB,
rounded), otherwise none with a 32 MiB design floor and a 1 GiB free-space check;
`layout_request_memory_mb` = 20,000 (14.27 GB × 1.4 ≈ 19,978 MB); `layout_wall_hours` = 28.85
(32.91 sensitivity). The reviewed HTCondor request's fixed 150,000,000 KB disk and 3,600 s walltime
are for the HTCondor route and are not edited or used here.

## 6. What remains before an evidence launch

1. The author (via the coordinator) records the Level 2 image/environment row described in §4; the
   signed note must bind the direct-route Python 3.11.17 environment or the route needs a container
   runtime. A Local edit of the signed `image:` line alone is not sufficient.
2. Local binds `paper_commit` to the published launch commit (a docs-only descendant of `c3a48405`
   with the same code tree outside `docs/` and the spec) and `run_id = d3a-prod-20261128-a` in the
   D.3a note, fills the pending layout request fields from §5, and confirms the reviewed cache is
   staged for the five OpenML nodes (the production host already has it; a fresh harness needs the
   two-dir install from §4).
3. Local re-runs P10 and P11 at that exact launch SHA. At the base they already pass: P10 returns
   `PASS` for 160 seeds 20010–20801 (`captures/p10_verify_namespaces.txt`); P11's analysis sha256 is
   `c0be039905e682e8b1702542e16607f09daf30a59be3363bbdf5a85c64a484ce` and
   `r1/tests/test_d3_analysis.py` passes 53 tests (`captures/p11_analysis_pin.txt`).
4. The author signs P9; the coordinator publishes the note byte-identically on `main`.
5. Only then does a chunk launch, after `validate --launch`, the strict note check, the canonical
   lease, the empty-card/foreign-process check, and the endpoint identity guard (§4.1) after
   readiness and immediately before every chunk. G.5 has the TASL pair first; D.3a waits for it.

No campaign, audit, G6/G7 step, label read or outcome was produced here. This record does not change
the note's `approved: false` state.

## 7. Tests

On TASL-2, in the clean `c3a48405` checkout with harness `9bb41680` and the audit package set:

```
python -B -m pytest -q -p no:cacheprovider -rfE \
  r1/tests/test_d3_launchers.py r1/tests/test_d3_g1_chunk.py \
  r1/tests/test_d3_adapter.py r1/tests/test_d3_g8_accounting.py
97 passed in 2.74s
```

The endpoint guard unit and integration set on this tip:

```
python -B -m pytest r1/tests/test_d3_endpoint_guard.py -q
23 passed
```

That set includes the Linux-only `HostProbe` integration (fake `ss`/`nvidia-smi`, a live `/props`,
a real lease inode); on macOS the same set is 22 passed and 1 skipped. The stub driver test
(`endpoint_guard_driver_test.sh`) passes the success, foreign-responder and failed-bind cases; its
outputs are in `captures/endpoint_guard/`.

The full `r1/tests` suite was run on clean checkouts of the published base `c66603ae` and this tip
with harness `9bb41680`. Two modules (`test_trackp_p4_runner.py`, `test_trackp_sft_select_stop.py`)
fail collection identically at both tips and were ignored. Base: `53 failed, 4888 passed, 162
skipped, 3 errors`; tip: `52 failed, 4912 passed, 162 skipped, 3 errors`. The sorted `FAILED`/`ERROR`
ID sets differ by one base-only flaky entry
(`test_t1_tasl_crosscheck.py::test_default_part_on_both_hosts_seal_and_compare`) and **zero tip-only
entries**: no new failure. The counts and ID comparison are in
`captures/endpoint_guard/full_suite_compare.txt`.

Cache staging: `read_data_cache` returns the reviewed tree `3843b53c…` and all five OpenML
`prepare_node_dir` data maps equal the MANIFEST (four files, one ARFF each);
`captures/cache_staging.txt` has the output. This guard unit changes one new module, its tests and
the production template; it changes no manifest, launch record, signed value or experiment code
path. The focused launcher/chunk/adapter/accounting set that consumes those files passes, and
P10/P11 pass at the base.

## 8. Hashes

| Object | sha256 |
|---|---|
| `manifest.json` | `426705844e6dc35f1a8f16f17a1098df6e384db792014fd0e3e0b516b8eb4fa3` |
| `launch_A0_digits_mlp_r0.json` | `e90c9c7624cb84cdaeb43f7199e39e391e4eb96239eb928c3c13f49bb56bb5ac` |
| `chunk_matrix.json` | `0a3297d323b4ead4e845f09b16253356d1db396c3907c1b0fc8d09ca7f2cf0fe` |
| `run_id_ledger.json` | `62becc147a2b321cd5c1b082ac451bedd0941662bff93d3cfb06374639cd9d38` |
| `observed.json` | `da07e83499a821c229c509d9bd4aefb0087f242d8c600e8fe0b911c79370a42f` |
| `endpoint_run.sh` | `d2b088d652bb5f1604f30fb9515af0d32eb44e8583bbe465ecbf7894e39ae3ad` |
| `production_driver.sh` | `00c04cc8343b672308c8ceb57458b9af4e7ae869972e39087a2ff8bf58410e3c` |
| `endpoint_guard_driver_test.sh` | `0d6b2d84a519467bddbab1ae38fd417afabbe9404d3e1942b51f7aff9a2c7b6d` |
| `r1/c3/d3/endpoint_guard.py` | `a1ef4184ad680bf37d5d2b1632b18b50e7706811da18266930b933423129ed92` |
| `r1/tests/test_d3_endpoint_guard.py` | `6f23da54ad09aa94999e20504a324debb99a97261cc6d2fdb52b0cbfe1e17615` |
| `captures/server_argv.txt` | `9ed9d647a7e2c9ededf14f12a170271577a3f12c2eb5abf8239756bc4f436ab6` |
| `captures/props.json` | `92fc6b976fe98a295033ac162beabdddc6ebd0b5af691de16fd524155b6f57da` |
| `captures/models.json` | `2ff596bf1be4a6c9354949f8ff6e8d4342b252b7c98d3f1ce7cc8a0f1ef420e4` |
| `captures/environment_20261128.txt` | `3637c4c615d96da8b7aaf18fd2bc51bdb941c42f95fc957bf65b22e006152d21` |
| `captures/launch_ssh_dryrun.txt` | `a0d0b662dcd1bc7614ff2c7ba431eebd378c1ecd0488852df6ee71c2c10a6ad8` |
| `captures/cache_staging.txt` | `2dedbbc2d7983aaec3203e70f12477fed30ff0c5f14fbd1deb0186d6ed9a0dfb` |
| `captures/endpoint_guard/driver_success.txt` | `ac36d9ac70d5bfe5029f4d1fcae2e1e763c975f278289171d7968eb97c1cff70` |
| `captures/endpoint_guard/driver_foreign.txt` | `4d4646a53d8692fa069cf863ff1f80144820bb453b2266f274f6d1172851662e` |
| `captures/endpoint_guard/driver_bindfail.txt` | `30e23956c9fc688d7b19885c1fcb442b840725a40961d532af6b3946f0dc0ebe` |
| `captures/endpoint_guard/pytest_endpoint_guard.txt` | `e8dadd7e0388988b572b2c3977b6dda1c1c1b78b9368282b9e4eb8a229ba4245` |
| `captures/endpoint_guard/full_suite_compare.txt` | `eea0984e958a4a1fb97cf17368c4643bbcb6cd6b763b4bd24f040945ba0a1715` |
| `captures/SHA256SUMS` | `ac7a6503d0945d76f3b653aa0808b90ab07ff2b08d4073b108409a899f8abaf0` (covers every capture file, including `server.log`, `status.log` and the endpoint-guard runs) |
| `SHA256SUMS` (record root) | binds this record and `captures/SHA256SUMS`; its hash is stated in the `coord/compute` report |

## 9. Decided alone

To use the reviewed direct SSH launcher on TASL-2 with the canonical `~/r1_locks/` leases rather than
the work-root locks of the P7 engineering receipt; to probe the card before starting the server, as
the production chunk must; to set the user scope at 20 GiB (`20G`) from the decimal 1.4 × 14.27 GB basis; to record the
direct-route environment as a disclosed substitution for the §2 image after finding Docker
inaccessible and no Apptainer; to allocate `d3a-prod-20261128-a` after checking that no host
directory, report or job used it; and to run only a seven-second endpoint start, no campaign. For the
endpoint guard: to check listener PID, `/props` model/context/slots, the compute-app UUID, the
canonical lease inode and the leased card's UUID together, fail closed on the first mismatch, seal
the capture directory only after the started server is quiescent, and use exit 90 so an
infrastructure STOP cannot be mistaken for a chunk failure. No signed value, pin, seed, request,
image digest or harness byte was changed; no label, test or evaluation value was read; no other
user's process was touched.
