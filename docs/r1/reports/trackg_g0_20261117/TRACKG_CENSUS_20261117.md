# TRACK G — G.0 census report (Ada), 17 November 2026

**Status.** G.0 on Ada: **U0 done (deploy + Paper A gate), U1 done (licence/availability), U2/U3 pending**
(no Track G port kits exist yet on origin; `R1-TRACKG-PORT-OWNER` assigns them to the Mac agent), **U4**
this report. ENGINEERING_ONLY; **no noise floor, no D21/D28 verdict** (G.1b on L40S, `R1-TRACKG-G1B-HOST`).
Authority: `R1-TRACKG-G0-GO`, `R1-TRACKG-PORT-OWNER` (`author-d8-confirm-20261117` @ `26177d82`),
`R1-ADA-CENSUS`, `R1-TRACKG-G1B-HOST`. AI-assisted.

## 1. Host facts (Ada, 17 Nov 2026)

- `ucrtasl`, user `dowling`; 8× RTX 6000 Ada 49,140 MiB; disk 152–162 G free (91 % used); other users'
  Ray/RL jobs occupy most cards (at check: free VRAM 10–35 GiB per card; owners asif/hongkunyang/
  zihaozhao and 4 stale zero-memory entries filtered by the status wrapper); one interactive login.
- Harness deployed: `/home/dowling/r1_trackg_20261117/autoresearch_harness` @
  `717ad835df32bbe1047d032fb5bb8dde5384a258`, branch `r1-local-trackg-v2-20261114`, clean.
- Paper repo worktree `/home/dowling/r1_trackg_20261117/Agent_paper_B_main_16185b0b` at `16185b0b`; the
  only dirty path is the deployed `paper_a_status_ada.json` (same bytes as the ops branch commit).
- Our disk footprint so far: harness clone + worktree + small scratch/captures (< 1 GB); the U2 budget cap
  of 100 GB is not approached.

## 2. Unit status

| Unit | Status | Record |
|---|---|---|
| **U0** deploy + Paper A gate | **DONE / ACCEPTED** (harness deployed; three-check gate verified: newest v4 `live_*` == configured run dir, no Paper A process, `paper_a_status.py` `clear_finished`/key false/unidentified 0; fail-closed nvidia-smi wrapper `7e0ec81a…`; R3 review `00529912…`) | `proposals/TRACKG_U0_DEPLOY_20261117.md` + `reports/trackg_g0_20261117/TRACKG_U0_RESULT_20261117.md`, `u0_status_20261117.json` (capture `6b62dd2a…`) + reviews `TRACKG_U0_DEPLOY_REVIEW…` (R3 accepted) |
| **U1** licence/availability | **DONE** (docs-only audit accepted; author decisions handed up) | `reports/trackg_g0_20261117/U1_LICENCE_AVAILABILITY_20261117.md` + `reviews/TRACKG_U1_LICENCE_REVIEW_20261117.md` |
| **U2** raw cost (one node/unit) | **PARTIAL** — `autoresearch_fixedtokens` PASSED (`CHECKLIST_E_PASSED`; baseline 67.9 s, baseline peak VRAM 5,211 MB, val_bpb 1.291068); the other seven nodes need their own reviewed per-node units | `reports/trackg_g0_20261117/TRACKG_U2_AR_RESULT_20261117.md`; kit/env details there |
| **U3** porting | **PENDING** — Mac agent owns the port kits; none on origin at 17 Nov 01:45Z | — |
| **U4** this report | **DONE (partial by design)** | this file |

## 3. Candidate rows (census table; raw cost pending port kits)

| Candidate / suite | Licence/availability (U1) | Raw cost (U2) | Census row |
|---|---|---|---|
| autoresearch (1 task) | MIT declared in README, no LICENSE file; climbmix MIT-claimed | **DONE**: baseline 67.9 s, peak VRAM 5,211 MB, val_bpb 1.291068; checklist E passed (card 0, 64G cgroup cap) | **DONE** — `TRACKG_U2_AR_RESULT_20261117.md` |
| MLGym — CIFAR-10 | MLGym CC-BY-NC-4.0; CIFAR-10 licence unknown | pending kit | pending |
| MLGym — Fashion-MNIST | MLGym CC-BY-NC-4.0; Fashion-MNIST MIT | pending kit | pending |
| MLGym — House Price | MLGym CC-BY-NC-4.0; Kaggle terms (bundle identity inferred) | pending kit | pending |
| MLGym — RL (MinAtar/MountainCar) | MLGym CC-BY-NC-4.0; Gymnax Apache-2.0 | pending kit | pending |
| MLAgentBench — cifar10 | MIT; CIFAR-10 licence unknown | pending kit | pending |
| MLAgentBench — imdb | MIT; IMDb licence "other"/unknown | pending kit | pending |
| MLAgentBench — ogbn-arxiv | MIT; ODC-BY | pending kit | pending |
| 1GC-7RC extras (TinyShakespeare, Forest Cover, ETTh1, AG News, ogbg-molhiv) | not a suite; licences: PD/no metadata, CC BY 4.0, conflicting, unknown/research-use, MIT | not ported (tier/fold open at G.3) | not in census |

**Functional qualification** is not claimed for any node: U2 cannot run until a kit exists, and D21/D28 are
G.1b on L40S (not Ada).

## 4. Blockers / decisions

- **Port kits missing** (Mac agent, `R1-TRACKG-PORT-OWNER`): U2/U3 blocked; no branch matching
  `trackg|port|g0|census` on `origin` or in the harness repo at 17 Nov 01:45Z.
- **Author decisions from U1**: MLGym CC-BY-NC acceptance; CIFAR-10/IMDb/AG News unstated terms; ETTh1
  licence choice; Kaggle House Price terms; 1GC-7RC 404 (keep 4 Nov fallback).
- **Coordinator**: amend `TRACKG_PORT_CHECKLIST.md` with the licence/provenance step.
- **Experiment agent**: container/root runtime (Docker/Podman vs Apptainer `.sif`), egress allowlists,
  7.25 / 21.8 GB image pulls.
- Every later U2 must re-run the U0 three-check Paper A gate before launching (newest live dir, pgrep, status).


## 19 November 2026 — U2 on the isolated kits (five nodes, ENGINEERING_ONLY)

See `TRACKG_U2_ISO_RESULTS_20261119.md` for the six accepted rows (mlab_cifar10, mlab_imdb,
mlab_ogbn_arxiv, mlgym_cifar10, mlgym_fmnist, mlgym_breakout_minatar), their B1/B2 times, metrics, whole-smoke VRAM upper bounds
and committed-file pins. Blocked: autoresearch_fixedtokens (isolation condition 7 CUDA IPC) and mlgym_houseprice
(no `~/r1_inputs/house-prices/train.csv`). No evidence/noise/D21/D28.
