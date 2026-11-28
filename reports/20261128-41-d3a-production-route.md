# compute/20261128-22 — D.3a production route records (manifest, environment, endpoint-to-lease proof)

**Result: engineering records delivered; no campaign.** The TASL-2 production manifest validates against the G1 adapter with the frozen rev 5 pins; one deployment launch record and the 49-chunk matrix validate; the endpoint → listening PID → GPU UUID → canonical lease chain is proven; the run ID is allocated and unused. The launch stays held for a Level 2 image/environment author row, Local's `paper_commit`/`run_id` binding and the author's P9.

- Task: `compute/20261128-22`. Base `origin/main` `c3a484055f717865e4e6826833e405af41771013`.
- Deliverable: `compute-d3a-production-route-20261128` @ **`6120d0e7b5f26d2cb8a844cb7c557aacd92c9f9d`**. Record `docs/r1/reports/d3a_production_route_20261128/D3A_PRODUCTION_ROUTE_20261128.md`; root `SHA256SUMS` sha256 `9007304fe54bdd25d6a1dc5d5fd1db5febe176218683d9867e64210c6ba7c6ff` (binds the record and `captures/SHA256SUMS` `6690c5f2…`).
- Review: `compute-d3a-production-route-20261128-review` @ **`e814b1ab1d9f3c8da42da5ad47cf80101849277f`**, verdict **ACCEPTED WITH MINORS** (no blockers). The minors (driver status order, GiB scope, derived scratch, cache provenance, adjacent image note, dry-run call details, `n_ctx` wording, ad-hoc matrix check) are applied in the final tip; residual notes are non-blocking.
- Tests: `97 passed in 2.74s` (`test_d3_launchers`, `test_d3_g1_chunk`, `test_d3_adapter`, `test_d3_g8_accounting`) on TASL-2 at `c3a48405` with harness `9bb41680` and the audit package set; P10 `PASS` for 160 seeds 20010–20801; P11 analysis sha256 `c0be0399…` and 53 analysis tests pass; `bash -n` clean for the two driver scripts.
- Job IDs: **none created**. No Paper B job on TASL-2/TASL-7/deepthought at 19:27–19:29Z (Ada not reachable; last read 18:49Z); `condor_q -submitter dwong` 0 jobs at 19:28Z.

## What is ready

| Item | Result |
|---|---|
| `manifest.json` | `r1_d3_campaign_manifest/v1`, sha256 `426705844e6dc35f1a8f16f17a1098df6e384db792014fd0e3e0b516b8eb4fa3`; seven nodes/seven arms, W=20, cap 80, rev 5 pins, RTX 4090, server argv |
| `launch_A0_digits_mlp_r0.json` | `r1_d3_launch/v1`, sha256 `e90c9c7624…`; passes `validate_deployment_launch`; run id `d3a-prod-20261128-a`, attempt `a01` |
| `chunk_matrix.json` | 49 `(node, arm)` chunks, sha256 `0a3297d3…`, same manifest hash/run id/leases |
| `run_id_ledger.json` | `d3a-prod-20261128-a` allocated, state `unused` |
| `observed.json` | `r1_d3_observed/v1`, sha256 `da07e834…`; TASL-2, UUID `GPU-4d623e76…`, `gpu0.lock`, memory check pass, 0 other processes |
| Data cache | reviewed screening cache `1987cc00…` / tree `3843b53c…` staged for the five OpenML nodes; all seven `prepare_node_dir` pass, five data maps equal the MANIFEST |
| Endpoint proof | `llama-server` pid 1673663 listening on 127.0.0.1:8095, compute app on the same UUID, fd 9 → `/home/dowling/r1_locks/gpu0.lock`, fd 8 → `cpus-16-31.lock`, cpus 16–31; stopped cleanly in 7 s |

## Environment / image (needs an author row)

The direct route runs the host venv, not the §2 v1 image: TASL-2 has no `docker` group and no Apptainer. Python 3.11.17, pandas 3.0.3, scikit-learn 1.8.0, numpy 2.4.4, scipy 1.17.1 via the P7 audit shim; harness `9bb41680` clean. This reproduces the accepted P7 exact-runtime environment, but differs from the v1 image (Python 3.13.18) and the audit basis (3.13.15). **This is a Level 2 item**: the record asks for a PLAN §10 author row/note amendment binding the direct-route Python 3.11.17 environment; a Local-only `image:` edit is not sufficient, and no D.3a campaign starts until the row exists.

Also recorded: the cache staging had to install the two ignored harness placeholder dirs (`openml_climate`, `openml_sonar`); the harness stays clean. Adjacent finding for the HTCondor route: `r1/c3/d3/launch.py` still carries v2.2 `49dd9900…`, while rev 5 §2 binds v1 `69b06b35…`; the direct route uses neither, but the HTCondor route needs a reviewed image binding. `launch_ssh.launch` is **not used unchanged** — its default scope is 16 GiB and its remote interpreter is `python3` (3.10.12 on TASL-2), so the direct driver sets PATH/PYTHONPATH/AR_HARNESS_ROOT and passes 20 GiB; the chunk/probe modules and the reviewed argv are unchanged.

## Round status

No runnable compute card remains after `20261128-22`. `kit c1` and expansion G.1b are complete (all four nodes 460/460, determinism PASS); no G.1b action.

| Item | State | Waits for / job ID |
|---|---|---|
| G.5 launch `compute/20261128-18` | blocked | author **"G.5 启动 A"**; coordinator merges `compute-g5-launch-base-20261128` @ `2178bc6e`; no job |
| G.5 campaigns `compute/20261126-06` | blocked | the launch decision and addenda bindings; no job |
| P.4 phase 1 `compute/20261128-19` | P5 timing PASS; P3 STOP | author signs `befb58c8`'s exact bytes; no job |
| D.3 batch preflight `compute/20261128-03` | not startable at 18:16Z | next pool read **21:16:04Z**; no job |
| D.3a production launch | records delivered | Local binds `paper_commit`/`run_id`, P10/P11 at the launch SHA, author P9; no job |
| E-INT census `compute/20261127-28` | blocked | published census authorization and signed spec |
| Paper C 3B fixed-memory census | blocked | design/author task, cap, pin, lease |

**Idle hosts:** TASL-2 RTX 4090 353 MiB, 0 % and no compute apps; TASL-7 44 MiB, 0 %; both cards idle before and after. deepthought: 0 `dwong` jobs, load 0.51, 457 GiB available. deepthought2: load 10.39, 908 GiB available. Ada was not reachable from this session (alias unresolvable at 19:35Z); last read 18:49Z, cards 2/5/6/7 empty. TASL-2 `/home` 334 GiB free; TASL-7 291 GiB free.

**Running elsewhere:** Local is idle pending these records; coordinator owns the merge and publication; writer idle.

## Next round, in order

1. Read `AUTHOR.md` for the G.5 launch reply. On **"G.5 启动 A"**, wait for the coordinator's merge of `2178bc6e`, launch `c3_t1_labels_20261128` from its tip after `validate --launch` and the strict `check-note`, and record launch time plus per-node/wave job IDs.
2. Read for the P.4 P3 signature; take the phase-1 unit if it lands.
3. At or after `21:16:04Z`, read `c03-001-175`, the ETP L40S and NEMO2; submit only on `Start = true`.
4. Check `coord/coordinator` for any card after `20261128-22` and `coord/local` for the D.3a note binding; no D.3a campaign before the published note.
5. Keep the host sample; retry the Ada alias.

**Rows (g) acknowledged:** placement free within the rows; no request edited to obtain a slot; no wall-clock limit decided anything; no sealed/test/label value read; no other user's process touched.

Decided alone: to use the reviewed direct-driver pattern on TASL-2 with canonical leases rather than the P7 work-root locks; to probe before starting the server; to set the 20 GiB (`20G`) chunk scope from the decimal 1.4 × 14.27 GB basis; to document the image substitution after finding Docker inaccessible; to allocate `d3a-prod-20261128-a` after checking it unused; and to run only a seven-second endpoint start, no campaign. No signed value, pin, seed, request, image digest or harness byte was changed.
