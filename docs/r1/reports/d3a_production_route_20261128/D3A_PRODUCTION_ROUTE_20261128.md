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
server argv, and the 20 GB user scope. `manifest.json` sha256 is
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
environment freeze, the canonical leases, the 20 GB scope, and a `r1_d3_retry_ledger/v1` with
`run_id = d3a-prod-20261128-a`, one current attempt `a01`, and the chunk identity. It passes
`validate_deployment_launch`; output in `captures/validation.txt`.

The driver sequence is fixed (the executed proof is the same sequence without step 4):

1. a bash wrapper takes `flock -n` on `/home/dowling/r1_locks/cpus-16-31.lock` (fd 8) and
   `/home/dowling/r1_locks/gpu0.lock` (fd 9);
2. `python -m r1.c3.d3.probe --launch … --manifest … --observed … --lease-path …` writes
   `observed.json` while fd 9 is inherited (pre-server, as the chunk requires);
3. `llama-server` starts on the frozen argv under `taskset -c 16-31` and the same descriptors, and
   the driver waits for `/props`;
4. `python -m r1.c3.d3.campaign_chunk --launch launch.json --out runs/<chunk> --manifest
   manifest.json --observed observed.json` runs the chunk with the reviewed `chunk_argv` under the
   20 GB scope;
5. the server is stopped and both leases are released.

`production_driver.sh` in this directory is that driver. It was **not executed with `RUN_CHUNK=1`**;
it is a template for the launch, and its probe/server path is the one exercised by
`endpoint_run.sh`. The chunk branch is gated and was not run.

The reviewed `launch_ssh.launch` helper is **not used unchanged** on this host. A dry run
(`captures/launch_ssh_dryrun.txt`) shows two integration facts: its default scope is 16 GB, below the
20 GB 1.4× basis, and its rendered remote script calls `python3`, which on TASL-2 is 3.10.12, not the
3.11.17 audit venv; it also does not set `PYTHONPATH`/`AR_HARNESS_ROOT`. The driver supplies those
explicitly and passes the 20 GB scope; the chunk/probe modules and their argv are unchanged. The
launcher code is not edited in this record.

`chunk_matrix.json` declares all 49 `(node, arm)` chunks at repetition 0, each with the same run id,
manifest sha256, 18 instance seeds 6201–6218, GPU model/UUID and canonical leases. It is a routing
record, not a claim that any chunk ran.

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

The `/props` field `n_ctx` is null in this llama.cpp build. The effective value is recorded by
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
| Container | none for the chunk; host process in a 20 GB user scope | v1 image digest for the HTCondor route |

The deepthought audit side is P8 (`D3A_P8_HOST_20261128`, re-check ACCEPTED at `b70cfa01`); this
record changes neither that host nor `r1/tests`.

This is a **disclosed substitution**, not a silent one: the direct route does not use the §2 image,
and Python differs from both the image and the audit basis. It reproduces the environment frozen by
the accepted P7 exact-runtime record itself (Python 3.11.17 and the same four package versions), so the
runtime gate was measured in this environment. The executable and shim are pinned:
`/home/dowling/.local/share/uv/python/cpython-3.11.17-linux-x86_64-gnu/bin/python3.11` sha256
`ff9b2ac4362b81c68622ffb1730f7138eb269177d9846399c521a44c5daffb0e`, and the audit shim tree
sha256 `1737028cdd5868c30d331e6f80133e5ec3b1c76f3d4f95df9de960d67370ef07` (regular files, no
`__pycache__`). `pyproject.toml` declares `requires-python = ">=3.11"`. Local and the author must
accept this disposition in the note's `image:` line, or the route needs a container runtime that
TASL-2 does not currently provide. No evidence run has started, so this is a binding decision, not a
STOP of existing evidence.

## 5. Resource basis

Measured at the exact runtime by the accepted P7 record
(`docs/r1/reports/d3a_p7_exact_20261128/D3A_P7_EXACT_RUNTIME_20261128.md`) and re-observed at the
endpoint start:

| Item | Value | Production bound |
|---|---|---|
| GPU memory peak | 21,999 MiB used; 2,184 MiB free minimum; 21,977 MiB at load | `required_memory_mib = 22000`; the empty-card probe read 23,830 MiB free |
| Host RAM peak | 14.27 GB of 67.12 GB total | 20 GB user scope = 1.4 × peak; `MemorySwapMax=0`; the endpoint proof did **not** exercise the cgroup, so this is a derived bound, not a measured scope |
| Scratch, one campaign | largest observed 858,382 B (A2, `openml_climate__s6301`); other arms 266–630 kB | 18 instances × largest = 15,450,876 B ≈ 14.7 MiB |
| Scratch, one chunk | run tree + OpenML cache (123,531 B) | ≈ 14.9 MiB measured basis; 32 MiB design floor, 1 GiB free-space check |
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

1. Local binds `paper_commit` to the published launch commit (a docs-only descendant of `c3a48405`
   with the same code tree outside `docs/` and the spec) and `run_id = d3a-prod-20261128-a` in the
   D.3a note, and fills the pending layout request fields from §5.
2. Local re-runs P10 and P11 at that exact launch SHA. At the base they already pass: P10 returns
   `PASS` for 160 seeds 20010–20801 (`captures/p10_verify_namespaces.txt`); P11's analysis sha256 is
   `c0be039905e682e8b1702542e16607f09daf30a59be3363bbdf5a85c64a484ce` and
   `r1/tests/test_d3_analysis.py` passes 53 tests (`captures/p11_analysis_pin.txt`).
3. The author signs P9; the coordinator publishes the note byte-identically on `main`.
4. Only then does a chunk launch, after `validate --launch`, the strict note check, the canonical
   lease and the empty-card/foreign-process check. G.5 has the TASL pair first; D.3a waits for it.

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

No repository code changed in this unit; it is records, one manifest, JSON launch/ledger data and a
capture script. The full `r1/tests` suite is not required for a docs-only record, but the focused
launcher/chunk/adapter/accounting set that consumes these files passes, and P10/P11 pass at the base.

## 8. Hashes

| Object | sha256 |
|---|---|
| `manifest.json` | `426705844e6dc35f1a8f16f17a1098df6e384db792014fd0e3e0b516b8eb4fa3` |
| `launch_A0_digits_mlp_r0.json` | `e90c9c7624cb84cdaeb43f7199e39e391e4eb96239eb928c3c13f49bb56bb5ac` |
| `chunk_matrix.json` | `0a3297d323b4ead4e845f09b16253356d1db396c3907c1b0fc8d09ca7f2cf0fe` |
| `run_id_ledger.json` | `62becc147a2b321cd5c1b082ac451bedd0941662bff93d3cfb06374639cd9d38` |
| `observed.json` | `da07e83499a821c229c509d9bd4aefb0087f242d8c600e8fe0b911c79370a42f` |
| `endpoint_run.sh` | `d2b088d652bb5f1604f30fb9515af0d32eb44e8583bbe465ecbf7894e39ae3ad` |
| `production_driver.sh` | `113bc5c022cfad5dfee7ba7d2443a49d461c9555c5f7e7f74c050c3b2a2d5c94` |
| `captures/server_argv.txt` | `9ed9d647a7e2c9ededf14f12a170271577a3f12c2eb5abf8239756bc4f436ab6` |
| `captures/props.json` | `92fc6b976fe98a295033ac162beabdddc6ebd0b5af691de16fd524155b6f57da` |
| `captures/models.json` | `2ff596bf1be4a6c9354949f8ff6e8d4342b252b7c98d3f1ce7cc8a0f1ef420e4` |
| `captures/environment_20261128.txt` | `3637c4c615d96da8b7aaf18fd2bc51bdb941c42f95fc957bf65b22e006152d21` |
| `captures/launch_ssh_dryrun.txt` | `f63344562a0fd3afea4bf394006e15c3a42f14f9b7387a7ac25a4b1605888d24` |
| `captures/SHA256SUMS` | `72e4fc3c9b96602da7c6ad0dfa95c83d356366be00189c161f36c5172a9d5b71` (covers every capture file) |
| `SHA256SUMS` (record root) | binds this record and `captures/SHA256SUMS`; its hash is stated in the `coord/compute` report |

## 9. Decided alone

To use the reviewed direct SSH launcher on TASL-2 with the canonical `~/r1_locks/` leases rather than
the work-root locks of the P7 engineering receipt; to probe the card before starting the server, as
the production chunk must; to set the user scope at 20 GB from the 1.4 × 14.27 GB basis; to record the
direct-route environment as a disclosed substitution for the §2 image after finding Docker
inaccessible and no Apptainer; to allocate `d3a-prod-20261128-a` after checking that no host
directory, report or job used it; and to run only a seven-second endpoint start, no campaign. No
signed value, pin, seed, request, image digest or harness byte was changed; no label, test or
evaluation value was read; no other user's process was touched.
