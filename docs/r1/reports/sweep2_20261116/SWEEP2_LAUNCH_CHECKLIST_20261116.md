# Sweep 2 launch checklist — P1–P7 status, specs, commits, authorization fields

**Status snapshot: 16 Nov 2026 ~23:10 CET.** Authority: `author-decisions-20261116b` @ `025bfc16` (= `main`);
work plan `docs/runbooks-16nov` @ `b3289232`. **Nothing in this checklist launches EVIDENCE; it STOPS for the
author.** R1-BX-D8 analysis lock unchanged.

## P1–P7

| # | Prerequisite | Status | Evidence / blocker |
|---|---|---|---|
| P1 | R1-SWEEP-HOST-HTC signed | **PASS** | `author-sweephost-20261116` @ `4651469a`; on main `025bfc16` |
| P2 | Published paper code on `main` (S2-M2 integration) | **PASS** | `main` = `025bfc16`; S2-M2 integration `9ae6d877` is an ancestor; sweep-2 code path present |
| P3 | Author-committed `docs/r1/authorizations/c3_sweep2_<date>.md` | **ABSENT** | only the template exists (`sweep2/s2_c5_authorization.template.md`, `approved: false`); the author must write it |
| P4 | Deployment check (S2-C3) | **RAN on H200, NOT PASS (author decision)** | S2-C3 ran on the first GPU type (H200, `s2c3-20261116-a`, jobs 759756-759758, sealed `/ceph`): 12/12 roots, worker crashes 0, offload 61/61, parse 0/240, throughput 1637 s — but the **pre-declared criteria 1 and 3 are NOT PASS** (ionosphere s9011 |Δ|=0.068 > 0.02; credit s9011 0.0204 > 0.02; diagnostics 25/38/25 vs 20/33/20). No relaxation; STOP for the author. S2-C3b liveness is running (759759) on H200: no NEMO2 L40S ads at snapshot (only H200 `g44xx`, CPU `n3xxx`, deepthought2 portal L40S) |
| P5 | Timing pilot + layout fixed | **PASS (17 Nov H200 re-measure)** | S2-C4 16k pilot + **32k smoke** (`759728/759729`, `sweep2-main-20261116` @ `f172d299`, sealed `/ceph/.../s2smoke-20261116-a/`); **R1-SWEEP2-LAYOUT-AMEND**: the 32k numbers are **void** (no training ran); worker env/gates fixed (reviewed); re-measured 2-instance smoke required; then walltime = 1.5 x the measured chunk, disk/memory re-derived; no resume path (killed/non-clean chunk rerun whole in a new dir, old moved aside, disclosed) |
| P6 | Real submission enabled only for the authorized run ID (S2-C5) | **DISABLED, not enabled** | switch unit `s2c5-switch-20261116` @ `84a0dc30` (review **ACCEPTED, remains disabled**; two-key gate `--enable` + `S2C5_ENABLE_REAL=1`, both absent; committed-note + JDL-sha binding, 32k layout, P1–P7 all PASS) |
| P7 | Image digest frozen in the authorization | **PENDING P3** | S2-C1 proposal: v1 gpu `ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35f093b4064525efa6fbd8bda48253f56f3b81baab6f21b7c93cc05296`; the authorization template freezes it; no digest switch (v2 `b1144ece…` remains unapproved) |

**Additional run prerequisites:** S2-C3b (pick D28 liveness on 8 nodes + prompt-length re-measure) unit is
**ACCEPTED for an ENGINEERING run** (`s2c3b-fix-20261116` @ `f1dff01f`, 129 tests); its run is ordered after
S2-C3. e1 environment replay under **R1-E1-OPENML-AMEND: PASS** (`ops-e1-replay-amend-20261117` @ `7f1e09aa`,
16/16 exact tokens, amended identity (b)/(i)–(iv), seccomp no-network; independent run review **ACCEPTED**).
The pre-amendment identity audit (`e1-openml-20261116` @ `b3b957e6`) remains the accepted "identity unprovable" record. Sweep 1 recorded OpenML data ids + a pre-launch loaded-data fingerprint but **no
md5/sha256 of any OpenML data file or cache tree** and no dataset-byte binding to the six nodes/16 cases; the
author must choose: replay only the 4 non-OpenML cases (protocol/authorization amendment), a R1-MAIN-PROPOSER (g)2
exception, an amended identity standard (author row + review), or leave e1 at STOP. G.1b waits for the Ada G.0 census (provisional cap 100 GPU-h, R1-G1B-CAP).

## Exact job specs at the accepted 32k layout

| unit | spec/commit | layout |
|---|---|---|
| sweep-2 chunk wrapper (S2-C2) | `sweep2/spec.example.json` on `sweep2-main-20261116` @ `4ca705b1` (wrapper code; JDL dry-run ad committed) | `request_memory 32000`, `request_disk 42460977`, `+RequestWalltime 12203`, container v1 digest, transfer `out.tar/work.tar/job_record.json/SHA256SUMS/llama-server.log` |
| S2-C3 deployment check | `s2c3-driver-fix-20261116` @ `3e2ebbf0`: `sweep2/spec.replay.{example,openml_credit_approval,openml_ionosphere}.json`; 37 staged inputs + JDL in `sweep2/dryrun/replay/` | same 32k numbers; 3 jobs × 4 roots/node; declared inputs 25/25; ENGINEERING_ONLY |
| S2-C3b liveness/prompt | `s2c3b-fix-20261116` @ `f1dff01f`: `sweep2/spec.c3b.example.json`, `sweep2/dryrun/c3b/` | same 32k numbers; 8 nodes liveness + tokenizer prompt classes; `liveness_seed_policy=sweep1_d28_reuse` (accepted) |
| S2-C5 switch | `s2c5-switch-20261116` @ `1c57a6de`: `sweep2/s2_c5_switch.py`, template | submits only the reviewed EVIDENCE JDL for the authorized run id + digest; disabled |

## Commits that must reach `main` before the EVIDENCE launch (author decision)

Each is reviewed/review-pending as marked; no force push, author merges.

1. **S2-C2 sweep-2 wrapper + 32k layout** — `sweep2-main-20261116` @ `4ca705b1` (branches from `main` `9ae6d877`;
   includes the round-5/5.1 wrapper and the 32k dry-run ad). This is the code that will run the sweep chunks.
2. **S2-C3 driver** — `s2c3-driver-fix-20261116` @ `3e2ebbf0` (final reviewer verdict pending; merge only after
   ACCEPTED and after the 3-job ENGINEERING run, or as the author requires).
3. **S2-C3b liveness/prompt** — `s2c3b-fix-20261116` @ `f1dff01f` (ACCEPTED for an ENGINEERING run; run pending).
4. **S2-C5 switch** — `s2c5-switch-20261116` @ `1c57a6de` (review pending; merge while still disabled; the author
   decides when/how to enable it for the authorized run).
5. If a v2 image digest is approved instead of v1: the v2 commit `htc-image-v2-20261115` @ `cbd0238e` (digests
   `b1144ece…` gpu / `08a36eff…` cpu) and the I2/I3-on-v2 evidence — **not** part of the v1 plan.

## Authorization fields the author needs to supply (P3/P7)

Copy `sweep2/s2_c5_authorization.template.md` to `docs/r1/authorizations/c3_sweep2_<date>.md` and fill:

- `approved: true`, `label: EVIDENCE`, `run_id: <id>`;
- `image: ghcr.io/dowlingwong/r1-htc-gpu@sha256:69b06b35…` (v1) — or the approved v2 digest with its I2/I3 evidence;
- `layout_request_walltime_s: 12203`, `layout_request_disk_kb: 42460977`, `layout_request_memory_mb: 32000`,
  `layout_chunks: 16`, `layout_gpu_hours: 41.72` (R1-SWEEP2-LAYOUT);
- `P1:`–`P7:` each with the PASS evidence pointer; `b2_audits: none` (this authorization carries no B.2 audits);
  `d8_lock: true`;
- anything the author wants to add: nodes (8 sweep-1 nodes), 18 instances, W=20, both memory modes, `vary` split,
  `manager_proposal/v1`, temperature 0.2/D26, noise source `3d12ce05…`, audit K=10 seeds 7001–7005/7006–7010,
  host = NEMO2 L40S (GPU L40S + CPU class family 6/model 207), harness `a3fedbb…`, GGUF `2959c1b0…`, cache_prompt
  false, 32k server flags, sealed path, STOPs.

## Environment / blocking findings at the snapshot

- **No NEMO2 L40S ads** (`g36xx` absent; H200 `g4401/g4402` and CPU `n31xx/n32xx/n33xx` are present; only the
  deepthought2 portal L40S advertises). The 3 S2-C3 jobs and the S2-C3b run are **queued behind cluster
  availability**; they will be submitted/retried when `g36xx` L40S slots return.
- S2-C3 driver final independent review is in progress; S2-C3 must not run before it is accepted.
- e1 mechanism in progress; its outcome is independent of the sweep-2 launch.
- No EVIDENCE job has been started; no sweep-2 labels were read; no B.2 audit or 7001–7010 seed was touched.

## STOP for the author

The cluster side holds at: **P3/P4/P6/P7 open**. The author needs to (i) commit the `c3_sweep2_<date>` authorization
(fields above), (ii) confirm the v1 digest freeze (P7) or approve v2 with I2/I3, (iii) decide when S2-C5 may be
enabled for the authorized run id, and (iv) once the L40S nodes return, let the reviewed ENGINEERING S2-C3 and
S2-C3b runs complete. Until then nothing launches EVIDENCE.
