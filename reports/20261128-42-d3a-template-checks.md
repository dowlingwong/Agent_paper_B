# compute/20261128-23 — D.3a production template: per-chunk endpoint identity guard

**Result: engineering unit delivered; no campaign and no job.** The production template now refuses
to start a chunk unless the endpoint is served by the server process it started on the leased card.
The success path and the two failure paths (foreign responder; failed bind) are tested. Independent
review: **ACCEPTED WITH MINORS**, no blockers.

- Task: `compute/20261128-23` (local's stub finding, `coord/local` `1a6a2cf5`).
- Base: `origin/main` `c66603ae8ac5f176ffe6a3b649cdb8b3d87d51de`.
- Deliverable: `compute-d3a-template-checks-20261128` @ **`d617fd3299a24938621e5009846be943889fcd46`**.
- Review: `compute-d3a-template-checks-20261128-review` @ **`6aaac39e28500f133b8b5f90fb8bc22bf426cbb9`**,
  verdict **ACCEPTED WITH MINORS** (review file sha256 `5e8c4dae6659ba714032b2a351f5b5516b6606d3e96e92c74faeef219b0110d4`).
- Record: `docs/r1/reports/d3a_production_route_20261128/D3A_PRODUCTION_ROUTE_20261128.md`, new §4.1;
  record root `SHA256SUMS` sha256 `b30d03bc41f96227288e88dd6e850f3da4c4acc1a9d4726443fed8c5a0be695f`
  (binds the record and `captures/SHA256SUMS` `ac7a6503…`).
- Tests: `r1/tests/test_d3_endpoint_guard.py` **23 passed** on TASL-2 (22 passed / 1 skipped on the
  Mac); the three stub driver cases `success`, `foreign`, `bindfail` all **PASS**; full `r1/tests`
  base `c66603ae` vs code tip `0354083d` shows **zero new failures**.
- Job IDs: **none created**. No Paper B job on TASL-2, TASL-7, Ada or deepthought/ETP; no run ID was
  consumed and `d3a-prod-20261128-a` remains unused.

## What the guard enforces

Local showed that a readiness answer on `/props` is not proof of identity: when the template's own
server failed to bind, a separate responder answered `/props` and the template proceeded to the
chunk. The template now calls `r1.c3.d3.endpoint_guard` after readiness and immediately before every
chunk (including the optional `CHUNK_ROWS` multi-chunk path). The guard fails closed unless all hold:

| Check | Evidence |
|---|---|
| listener owner | `ss -ltnp 'sport = :<port>'` names exactly the started PID and no other |
| `/props` model | `model_path` equals the manifest `server_argv` `-m` path |
| `/props` context | `default_generation_settings.n_ctx` equals the manifest `server_argv` `-c` |
| `/props` slots | `total_slots` equals the manifest `server_argv` `-np` |
| compute PID | `nvidia-smi --query-compute-apps` lists that PID exactly once |
| compute card | that PID's GPU UUID equals the manifest `route.gpu_uuid` |
| canonical lease | the guard's inherited fd 9 and a server fd match the `route.gpu_lease_path` inode |
| leased card | `nvidia-smi -i <lease index> --query-gpu=uuid` equals the manifest UUID |
| pre-server probe | `observed.json` has the same UUID, `lease: true` and the same lease path |

On a mismatch the guard writes `endpoint_check_<tag>.json` (`r1_d3_endpoint_check/v1`), the driver
writes `STOP.json` (`r1_d3_endpoint_stop/v1`), stops the started server, seals the capture directory
with `SHA256SUMS` and exits **90** before `r1.c3.d3.campaign_chunk` is imported. Nothing is deleted.
The reviewed chunk argv is unchanged.

## Tests and seals

| Check | Result |
|---|---|
| `pytest r1/tests/test_d3_endpoint_guard.py -q` (TASL-2, 3.11.17) | **23 passed** |
| same on the Mac (Linux-only `HostProbe` test skipped) | **22 passed, 1 skipped** |
| stub driver `success` | guard passes after readiness and before the chunk; chunk stub called; exit 0 |
| stub driver `foreign` | started PID alive, another process owns the port; STOP `listener_pid`; no chunk; seal OK; exit 90 |
| stub driver `bindfail` | started server exits, foreign responder answers `/props`; STOP `server_alive`; no chunk; seal OK; exit 90 |
| focused D.3 set (`test_d3_*.py`) at base and tip | base `515 passed, 9 failed, 2 skipped`; tip `538 passed, 9 failed, 2 skipped`; same 9 failure IDs |
| full `r1/tests` (ignoring two modules that fail collection identically at both tips) | base `53 failed, 4888 passed`; code tip `0354083d` `52 failed, 4912 passed`; **zero tip-only FAILED/ERROR IDs** |
| record seals at `d617fd32` | root `shasum -a 256 -c SHA256SUMS` OK; `captures/` check OK |

The final commit after `0354083d` adds only the SPID-0 seal guard, record text, captures and seals;
the guard module and tests are unchanged from the tested code tip.

## Review minors from the D.3a route review

- **R1 fixed:** the dry-run capture now names the positional `launch_path`.
- **R2 fixed:** the environment block is recorded at its `19:33:44Z` file mtime (the earlier text
  rounded it to 19:34Z).
- **R3 fixed:** `cache_staging.txt` has a provenance header; it states honestly that the staging
  command line was not retained.
- **R4 fixed:** this report states the record root hash.

## Independent review (fresh agent, `6aaac39e`)

The reviewer worked from a fresh clone and left the deliverable branch untouched. At `d617fd32` it
re-ran the guard set (`23 passed` on TASL-2; `22 passed, 1 skipped` on the Mac), the three stub
driver cases (`success` rc 0 with the chunk called; `foreign` rc 90 `listener_pid`; `bindfail` rc 90
`server_alive`; both failures sealed and neither called the chunk), both record seals (root 43/43,
captures 34/34), and every §8 hash. It added two checks not in the unit: a patched `ss` that changes
identity between readiness and the chunk stops at `chunk_01` before `campaign_chunk` and releases both
leases; `CHUNK_ROWS` with two rows shows the guard pass immediately before each chunk. It also parsed
real `ss`/`nvidia-smi` output and confirmed the `exec 9>` inheritance and `gpu0.lock` → UUID binding.
It accepted the full-suite capture without re-running it.

Non-blocking residuals (none lets a foreign responder reach the chunk): the STOP record collapses
per-check detail to `failed=guard` rather than naming the foreign PID; `wait "$SPID"` has no
KILL fallback; the guard is a point-in-time check (inherent TOCTOU); `$REPO` must contain the new
guard module or the first check fails closed at 90; the full-suite capture omits the command and full
ID lists; the stub seal check is Linux-only; `CHUNK_ROWS` would treat a comment line as a row.

## Hashes

| Object | sha256 |
|---|---|
| `r1/c3/d3/endpoint_guard.py` | `a1ef4184ad680bf37d5d2b1632b18b50e7706811da18266930b933423129ed92` |
| `r1/tests/test_d3_endpoint_guard.py` | `6f23da54ad09aa94999e20504a324debb99a97261cc6d2fdb52b0cbfe1e17615` |
| `production_driver.sh` | `00c04cc8343b672308c8ceb57458b9af4e7ae869972e39087a2ff8bf58410e3c` |
| `endpoint_guard_driver_test.sh` | `0d6b2d84a519467bddbab1ae38fd417afabbe9404d3e1942b51f7aff9a2c7b6d` |
| record root `SHA256SUMS` | `b30d03bc41f96227288e88dd6e850f3da4c4acc1a9d4726443fed8c5a0be695f` |
| `captures/SHA256SUMS` | `ac7a6503d0945d76f3b653aa0808b90ab07ff2b08d4073b108409a899f8abaf0` |

## Hosts (read-only, 20:36–20:37Z)

| Host | State | Paper B job |
|---|---|---|
| TASL-2 | RTX 4090 353 MiB / 24,564 MiB, 0 %; no compute apps; `gpu0` lease free; load 0.22 | none |
| TASL-7 | RTX 4090 44 MiB, 0 %; no compute apps; load 0.00 | none |
| Ada | 8 × RTX 6000 Ada; cards 2, 5, 6, 7 empty (~5 MiB), cards 0, 1, 3, 4 busy with other users; `/data1` ~1.9 T free | none |
| deepthought | load 0.88; 457 GiB available; `condor_q -submitter dwong` 0 jobs | none |
| deepthought2 | load 10.77; 912 GiB available | none |

No other user's process was touched; no request was edited; no sealed, test or label value was read.

## Round status

No runnable compute card remains after `20261128-23` in this round. The queue has no card after it.
`kit c1` and expansion G.1b are complete (all four nodes 460/460, determinism PASS, merged
`166db0eb`/`cbc86fc5`); there is no G.1b action this round.

| Item | State | Waits for / job ID |
|---|---|---|
| D.3a launch (environment) | blocked | author **"签 D.3 rev 6 A"** (or B); the rev 6 row then re-review/freeze/step (8) |
| G.5 launch `compute/20261128-18` | blocked | author **"G.5 启动 A"**; coordinator merge of `2178bc6e`; no job |
| G.5 campaigns `compute/20261126-06` | blocked | the launch decision and addenda bindings; no job |
| P.4 phase 1 `compute/20261128-19` | blocked | author signs `befb58c8`'s exact bytes; no job |
| D.3 batch preflight `compute/20261128-03` | not due | next pool read **21:16:04Z**; no job |
| E-INT census `compute/20261127-28` | blocked | published census authorization and signed spec |
| Paper C 3B fixed-memory census | blocked | design/author task, cap, pin, lease |

**Idle/running elsewhere:** Local and writer are idle on compute's handoff; the coordinator owns the
D.3 rev 6 and G.5 decisions. No Paper B job is running on any host.

## Next round, in order

1. At or after `21:16:04Z`, read `c03-001-175`, the ETP L40S and NEMO2; submit only on
   `Start = true` under `compute/20261128-03`/`-21`; record the exact expressions and job ID.
2. Read `AUTHOR.md` for the D.3 rev 6 reply and the G.5/P.4 replies; take the next unit that lands.
3. Read `coord/local` for the D.3a note binding and re-run P10/P11 at that SHA; no campaign before
   the published note.
4. Keep the recurring host/pool sample; no date decides anything.

**Rows (g) acknowledged:** placement is free within the rows; no request was edited to get a slot;
no wall-clock limit decided anything; no sealed, test or label value was read; no other user's
process was touched.

Decided alone: to implement the guard as a testable module rather than inline shell, to use exit 90
for an endpoint-identity STOP, to seal the capture directory only after the started server is
quiescent, and to run the stub driver cases on TASL-2 with the real `/proc`/HTTP path. No signed
value, spec, seed, request or image digest was changed.
