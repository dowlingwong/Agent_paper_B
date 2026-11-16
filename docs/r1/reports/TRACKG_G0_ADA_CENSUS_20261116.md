# Track G G.0 on Ada — read-only census and resumable-unit plan (16 November 2026)

**Scope.** Read-only census of Ada (`experiment_zhixu`, hostname `ucrtasl`) plus the plan for G.0 census
units. AI-assisted, read-only: no host write, no run, no other user's process touched. Authority:
`author-decisions-20261116` @ `4da73306`; PLAN `R1-ADA-CENSUS`, `R1-TRACKG-G1B-HOST` (16 Nov),
`R1-BX-D1/D2/D5/D14`, `R1-BX-REVISIONS(e)`; `docs/r1/prompts/TRACK_G_RUNBOOK.md`; harness
`r1-local-trackg-v2-20261114` @ `717ad835` (branch of the `autoresearch_harness` repo; reviewed at paper
`mac-trackg-v2-20261114` @ `52a40d57`).

## 1. Ada read-only facts (16 Nov 2026, 09:38–09:39 UTC; user `dowling`)

- Host `ucrtasl`; 8× NVIDIA RTX 6000 Ada Generation (49,140 MiB each); driver reported by `nvidia-smi`.
- GPU memory: cards 0/2/3/4 **in use** (14,173 / 12,944 / 36,911 / 35,646 MiB; 0/0/11/10 %), cards
  **1/5/6/7 free** (5 MiB, 0 %). Compute apps: other users' Ray jobs — `asif`
  (`EmbodiedDAGGERFSDPPolicy`, `MultiStepRolloutWorker`, `EnvWorker`; 6 processes) and `hongkunyang`
  (`RLTACFSDPPolicy`, `MultiStepRolloutWorker.evaluate`, `EnvWorker`; 5 processes). Their jobs are not ours;
  nothing was touched.
- Users: `dijiezhu` logged in on pts/2 (100.82.94.10); load average ≈ 9.7; host up 45 days.
- Disk: `/` 1.8 T, **183 G free (90 % used)**; memory/CPU not exhaustively recorded.
- Our home `/home/dowling`: Paper A checkout `agent-checkpoint-intervention` (latest commit
  `6b0ac021` "Record completed panel v4 live run and strict receiving outputs", 2026-10-17; untracked
  `._*` files and one protocol file), Paper A logs from Oct; **no active Paper A process**.
- Track G harness `r1-local-trackg-v2-20261114` is **not deployed** on Ada; no `configs/trackg/nodes/*`
  or ported node assets exist; no census script/unit exists on any supplied ref.
- Other users' occupancy is live and volatile; each census unit must re-check it (no repo record for
  16 Nov; this is an operator capture, not a repo record).

## 2. What G.0 is (and is not)

- **G.0 (Ada, R1-ADA-CENSUS, 16 Nov `R1-TRACKG-G1B-HOST`):** licence/availability of each candidate's
  repository, dataset and task assets; then **raw cost** at a fixed candidate step budget: run time, peak
  VRAM, CPU/RAM, on the table's GPU model; a `TRACKG_CENSUS_<date>.md` report with one row per candidate
  and the per-suite screening funnel (R1-BX-D12). ENGINEERING_ONLY/non-evidence.
- **Not G.0:** determinism, the 10-seed noise floor on the 3–5 declared edits (seeds 8001–8010), the D21
  verdict, D28 liveness — these are **G.1b on NEMO2 L40S** (16 Nov row), same GPU model as T1 labels
  (R1-SWEEP-HOST-HTC, R1-BX-D5). Ada must not measure noise floors, T1 label runs or sweeps.
- There is **no G.1a step** in the current rows; porting is assigned by stale HoreKa-agent text and is not
  moved to Ada by any 16 Nov row — an unresolved ownership item for the coordinator/author.

## 3. T1 candidate nodes (working list)

From `R1-BX-D1/D2` and `R1-BX-REVISIONS(e)`: **autoresearch** (short fixed-step variant, 1 task);
**MLGym** lighter tasks (CIFAR-10, Fashion-MNIST, House Price, a MinAtar/MountainCar-type RL task);
**MLAgentBench** light tasks (cifar10, imdb, ogbn-arxiv) as the third suite; 1GC-7RC is not a suite
(public datasets may be extra tasks; tier/fold open until G.3). Working estimate ≈8 T1 candidates
(`proposals/HOREKA_T1_JOBS_DRAFT_20261104.md` §0.4). Determinism/noise/D21/D28 and the final T1/T2 split
are fixed later (G.3) and on L40S.

## 4. Prerequisites and gates for Ada census units

1. **Paper A first (R1-ADA-CENSUS):** "No Paper B GPU job starts there while a Paper A campaign waits for
   a card." Observable: `r1/scripts/paper_a_status.py` returns JSON `paper_a_live_waiting_for_card`;
   the runner refuses on `true` or a missing key. Its Ada config
   `r1/scripts/configs/paper_a_status_ada.json` is still all `null` with seven
   "verify_before_first_use" checks, so today it returns `unknown` and a launch is refused
   (`--not-applicable` is refused on `ucrtasl`). **Configuring and verifying this is prerequisite unit 0**
   (no GPU job).
2. **Co-tenancy (RUNBOOK):** before each GPU job, free VRAM on the chosen card must be ≥ measured
   footprint + 2 GiB; never disturb other users; OOM/CPU fallback = STOP; resumable units only
   (interrupted unit re-runs whole); no Paper B job while Paper A waits.
3. **Harness + porting:** deploy `r1-local-trackg-v2-20261114` @ `717ad835` on Ada; port each T1 node
   (`configs/trackg/nodes/<node>.yaml`, `nodes/<node>/representative_edits/E*.diff`, fixed-step wrapper)
   per `TRACKG_PORT_CHECKLIST.md`; this porting unit has no assigned owner yet (see §2).
4. **Census reproducibility:** the census measures 10 seeds while D21's adopted rule uses 30 — any "D21
   verdict" from the census is provisional/not rule-comparable; needs an author line (worksheet row).

## 5. Proposed resumable units (for review, after the read-only report)

- **U0 — deploy + Paper A status verification (no GPU):** deploy the harness at `717ad835`; fill and
  verify `paper_a_status_ada.json` against the Paper A checkout/run/state/tmux/process patterns; record
  `paper_a_live_waiting_for_card` values; STOP if it cannot be made `clear_*`. Owner: operator.
- **U1 — licence/availability audit (docs only):** per candidate task/suite record repository, dataset
  and task-asset licence/availability; flag the 1GC-7RC non-suite status; no GPU. Resumable per suite.
- **U2 — per-node raw-cost unit (GPU, resumable one node at a time):** choose a free card, re-check
  co-tenancy + Paper A gate, run the suite's fixed-step budget, record run time/peak VRAM/CPU/RAM, STOP on
  OOM/fallback, capture the per-node JSON; one node per unit so eviction loses at most one node.
- **U3 — porting units (GPU/CPU, per node):** port each candidate to the harness per the checklist; smoke
  checks (frozen-path edit refused, complete manifest); needed before U2 for autoresearch/MLGym-style
  nodes. Ownership unresolved (§2) — needs a coordinator/author decision before committing to it.
- **U4 — compile census:** `TRACKG_CENSUS_<date>.md` with per-candidate rows, per-suite funnel, raw
  records; "functional qualification" = port smoke passes + runs at the fixed budget on the target GPU
  with ok metrics and known determinism, with D21/D28 handled by G.1b on L40S; non-qualifiers go to the
  R1-BX-D12 appendix.

## 6. Open items / risks

- Paper A status config is unverified; no Paper B GPU job on Ada until it is configured and reviewed.
- Ada occupancy is other users' live Ray jobs; 4 free cards at the check; status will change.
- Harness/porting not deployed; porting ownership unresolved.
- Live Ada facts here are an operator capture (no repo record for 16 Nov); re-check in every unit.
- G.1b measurements on Ada are forbidden by the 16 Nov row; the L40S/cluster agent owns them.
