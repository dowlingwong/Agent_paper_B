# Track P readiness on TASL-7 — read-only report (16 November 2026)

**Authority.** `author-decisions-20261116` @ `4da73306`; PLAN §10 `R1-TASL7-TRACKP`, `R1-P3A-READY`,
`R1-P3A-OOM-OPTION3`, `R1-P3A-BUDGET-CLOCK`, `R1-E0-*`, `R1-TRACKP-CHOICES`, `R1-W2-3-STOP`,
`R1-B2-REPAIR-SCOPE-ACK`, `R1-BX-D8`, `R1-TASL2-LOCK`; Track P runbook `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md`
(Track P work reads the "portal" as TASL-7 under `R1-TASL7-TRACKP`), Phase 5 (P.3a) and the host-change header.
AI-assisted, read-only: no host write, no run, no process signalled; nothing deleted.

## 1. TASL-7 host facts (16 Nov 2026, 09:37–09:40 UTC; user `dowling`)

- Host `TASL-7`; RTX 4090 24,564 MiB, **driver 580.178.04**, 236 MiB used, 0 %; no GPU compute app.
- `~/r1_locks/gpu0.lock` **FREE**; no `trackx_evidence.active`, no `trackp_evidence.active`,
  no `trks_drill.active`, no tmux server; no experiment/Track S/Track P process.
- Disk `/home/dowling`: 1.9 T, **524 G free** (71 % used) — above the Track P runbook's ≥150 GB.
- Track P tree `/home/dowling/r1_trackp`: `Agent_paper_B` @ `b9ad6f8f` on branch `trackp-20261026`, clean;
  `autoresearch_harness` @ `897d83c8efa364ec2fdd37288241cc42e01d7274`, clean; `venvs/trackp-gpu`
  (Python 3.12.15, torch 2.6.0+cu124); `models/` holds the 8 pinned repos; `runs/` holds the preserved
  P.3a attempt 1 and the 26 Oct equivalence run.
- `~/r1_locks/bin/trackp-evidence` present, sha256
  `f457a04ef1bbaba1750d9c04aa9211d51df1692ac36139bb720318f2d2533cec` == committed
  `docs/r1/proposals/trackp-evidence.sh` (mode 755, 3,949 B, 4 Nov 08:55 -0800) — the marker helper the
  amendment requires is installed.

## 2. Environment pin check against the recorded TASL-7 freeze

Compared the venv's installed distributions to
`docs/r1/reports/tasl7_phase2_20261026/pip_freeze_trackp-gpu_tasl7.txt` (121 lines; the three `@ git+…`
lines are `kev@2074cc44…`, `laya@a478221b…`, `startlux-decide@a99977d9…`):

- **Every pinned package is present at the pinned version; 0 version differences.**
- The venv additionally shows those three code distributions as `kev`, `laya`, `startlux-decide` (the
  `@ git+` lines of the pin file) — no other extras.
- Conclusion: **freeze matches the recorded TASL-7 Phase-2 pin**; the portal freeze and TASL-7 freeze
  were recorded identical (121 lines) and the 26 Oct migration/equivalence reviews accepted it.

## 3. Host-equivalence gate (R1-TASL7-TRACKP): **DONE, accepted**

`docs/r1/reports/TRACKP_TASL7_EQUIVALENCE_20261026.md`: one portal E0-v2 DRYRUN configuration
(`kev-0.8b/fresh_soft_lr0.0001`: fresh LayerNorm+linear head, soft labels, adapter lr 1e-4, head lr 1e-3,
seed 0, 2,000-step stage caps, eval every 100, patience 5, batch 8) reproduced on TASL-7 with identical
`config_sha256`, data manifest, bases/revisions, environment, seed and head form; adapter/head hashes
differ as expected. Pre-declared tolerance and `compare.py` were committed before the run (`f3567e9`,
22:47:40Z; run started 22:52Z). Result: **equivalent** — Δ width slope −0.0095 (≤0.05), Δ mean slope
+0.0077 (≤0.05), RPS −2.5 % (≤10 %). Review `docs/r1/reviews/TRACKP_TASL7_MIGRATION_REVIEW_20261026.md`
accepted the migration (5 minor findings fixed). This is the host-equivalence record; it is **not** the
R1-E0-PROTOCOL two-model DRYRUN and not a cluster/Q-TORCH gate.

## 4. Track P progress and the next unit

- Phases 0–4 are complete and independently accepted (host facts, code, environment/pins, P.0 spikes on
  all 8 bases, P.1/P.2 toy batch). E0-v2 DRYRUNs and the two-stage driver DRYRUN are recorded
  (`TRACKP_E0V2_DRYRUN_20261026.md`, `TRACKP_E0V2_TWOSTAGE_DRYRUN_20261026.md`,
  `TRACKP_P3A_DRYRUN_20261026.md`).
- **P.3a attempt 1 (EVIDENCE) ran 27–29 Oct on TASL-7 and STOPped.** Preserved at
  `/home/dowling/r1_trackp/runs/p3a_operator_20261027` (journal 81 lines): E0 screen/select/final/hard/
  native completed for all four bases; E6 probes completed for `kev-0.8b`
  (`report.json` sha `f04df4e1…`), `kev-4b` (`fae7c9cb…`), `qwen3.5-0.8b-base` (`73894af6…`); the
  `qwen3.5-4b-base` probes unit **OOM**ed at 2026-10-29T01:25:17Z (CUDA OOM in the descriptive A3
  history-length loop), total **130,745.38 GPU-s = 36.318 GPU-h** of the 45-h lease STOP / 60-h cap.
  Attempt 1 is preserved; it is not re-run or overwritten (R1-P3A-OOM-OPTION3).
- **Remaining P.3a evidence** (authorized by `trackp_p3a_amend_20261104.md`): the **`qwen3.5-4b-base`
  E6 probes only** — A3 runs only its specified rows (0/25/50/100 % of the remaining token budget at the
  1,024-token limit), **not** the descriptive 2k/8k rows; A4; A5 descriptive. E0/final/native and the
  other three bases' probes already exist and are not re-run.
- **Next unit = P.3a attempt 2, probes-only**, from the retained `final/saved` of `qwen3.5-4b-base`
  (attempt 1 root), in a **new output root**; no P.3b/P.4/P.5/P.6 is authorized (no
  `trackp_p3b_*`/later authorization exists).

## 5. Gates the next unit still needs

| Gate | Status |
|---|---|
| Host-equivalence (one E0-v2 DRYRUN reproduced on TASL-7) | **PASS, accepted** (§3) |
| Run venv freeze vs TASL-7 record | **PASS** (§2) |
| Driver / no unplanned reboot | PASS at check: 580.178.04; each job must record uptime, `/proc/driver/nvidia/version`, `nvidia-smi` driver |
| Disk ≥150 GB | PASS (524 G) |
| Lease + empty compute census + Track P evidence marker | Pass now (lease free, no compute, no marker); marker must be set for the run via `~/r1_locks/bin/trackp-evidence` |
| Authorization notes | 27 Oct note + 4 Nov amendment present; pins, STOPs, 60 GPU-h cap (incl. attempt 1), 45-h lease STOP (8.68 h left) |
| Code pin `trackp-20261026` @ `b9ad6f8f`, clean; harness `897d83c8` clean | PASS |
| **Code delta for option 3** | **OPEN**: `exam_run.probes()` always runs the descriptive long A3 levels when `--budget` is used (`r1/c3/train/exam_run.py:274–280`); a reviewed switch is needed to skip the 2k/8k rows, and the amendment then requires a DRYRUN-first if code changed |
| **M13 template-version inventory** | **OPEN**: attempt-1 per-run manifests must be inspected/provided so every result can record its serialisation template version (`reports/MAC_M13_TEMPLATE_INVENTORY_20261105.md`; template pin is still `TODO_VERIFY`) |
| **A6 probe (`exam_run.py`)** | **OPEN/ambiguous**: option 3 says A6 quantifies the template difference; A6 is only "(proposed)" in the spec and not implemented — needs its own reviewed unit or an author decision |
| Independent review of the unit/code | **Required before execution**; then STOP 5 review recomputes slopes/rule hash and the report `TRACKP_P3A_<date>.md` is submitted |

## 6. Track P data inputs (v3/v2) — status and scope

- `c3_features/v3` + `trackp_prompt/v2` were rebuilt under the W2-3 unit: **W2-3 STOP check PASS**
  (288/288 ledgers × 20 worker runs, 0 differing, exit 0; `reports/W2_3_CHECK_20261115.md`,
  `w2_3_check_20261115.json`), and the rebuild run is accepted (branch `w2-3-rebuild-unit-20261115` @
  `2989f383`; `reports/W2_3_REBUILD_RUN_20261115.md`; table
  `…/tables/c3_features_v3_20261115T232007Z`, label EVIDENCE, 4,999 proposals / 302 configs / 5,813 replay
  rows; artifacts `proposals.jsonl d0048567…`, `configs.json b585b727…`, `build.json 7f56619c…`,
  `manifest.json 661f0fd8…`; repo evidence copy under `docs/r1/reports/w2_3_rebuild_20261115/`).
  **Not merged to `origin/main`**; the table lives on deepthought plus the repo evidence copy.
- **These are not inputs to P.3a** (P.3a uses the synthetic `e0_v1`, sha `4f4db29b…`; probes load
  attempt-1 native outputs). They are inputs to the later real-table stages (P.3b/P.4), which also need
  their own authorization notes that do not exist.
- **Scope fences recorded:** `R1-B2-REPAIR-SCOPE-ACK` lifts the Track P real-table ban only for the five
  reviewed `9bab3d6f` files (not M3 as a whole, not B.2); **sweep-1 tables only** for Track P;
  **sweep-2 tables are locked** until `R1-BX-D8-CONFIRM` exists (it does not; D8-V3-A items 4–5 open;
  gate v3 not implemented). Sweep 2/B.2 audits belong to the HTCondor/NEMO2 L40S cluster agent, not
  TASL-7.

## 7. TASL-2 — leftover `gpu0.lock` (unit proposed)

Read-only facts (16 Nov 09:37Z): `/home/dowling/r1_locks/gpu0.lock` inode `120090387`, size 0, sha256
`e3b0c442…`, mtime/ctime `2026-10-25T21:35:24.275265604-0700`; host boot id
`86c613a9-b90c-48be-9bd5-a0f99c940dae`, booted 2026-11-15 12:51 local; `/proc/locks` has **no entry** for
the inode; `lslocks` lists no `gpu0.lock`; no process holds it (`/proc/*/fd` scan); no user tmux/process;
`flock -n` on the file succeeds (`LEASE_ACQUIRABLE`). No owner process exists. Unit:
`proposals/TASL2_LOCK_RELEASE_20261116.md` (record holder/age, move aside, verify, nothing deleted).

## 8. Ada — Track G G.0 read-only census (plan)

Facts in `reports/TRACKG_G0_ADA_CENSUS_20261116.md`: host `ucrtasl`, 8× RTX 6000 Ada; cards 0/2/3/4 in use
by other users' Ray jobs (`asif`, `hongkunyang`; 12.9–36.9 GiB), cards **1/5/6/7 free** (5 MiB, 0 %);
one other user logged in (`dijiezhu`); load ≈9.7; `/` 183 G free (90 % used); our home holds the Paper A
checkout `agent-checkpoint-intervention` (latest commit 2026-10-17) with no running Paper A process; the
Track G harness `r1-local-trackg-v2-20261114` @ `717ad835` is **not deployed** on Ada and no T1 node
assets exist. G.0 scope is licences/availability + raw cost only; determinism/noise floor/D21/D28 are
**G.1b on L40S**, not Ada. Before any Paper B GPU job the Paper-A-first gate must be evaluable: the
`paper_a_status.py` config (`r1/scripts/configs/paper_a_status_ada.json`) is still all `null`
("verify_before_first_use"), so it returns `unknown` and refuses; configuring/verifying it is the first
Ada unit (proposed in §8 of the census report).

## 9. Proposed first units for independent review

1. **TASL-2 lock release** (`proposals/TASL2_LOCK_RELEASE_20261116.md`) — first unit to run (small, no GPU);
2. **P.3a attempt-2 plan + A3-skip code delta** (`proposals/TRACKP_P3A_ATTEMPT2_20261116.md`) — Track P
   first unit on TASL-7; execution waits for its review, the code-delta review, M13/A6 disposition, and
   the marker/lease checks;
3. **Ada G.0 unit 0** — deploy the Track G harness on Ada and configure/verify `paper_a_status` (no GPU
   job), then resumable raw-cost units per node.

## 10. Limits

- All host facts are point-in-time (16 Nov 09:37–09:40Z); TASL-7/TASL-2 remain idle and untouched.
- The attempt-1 numbers above are read from its preserved journal/report files; no result claim is made.
- P.3a remains STOP until the amended unit is reviewed and executed; P.3b+ remains unauthorized.
