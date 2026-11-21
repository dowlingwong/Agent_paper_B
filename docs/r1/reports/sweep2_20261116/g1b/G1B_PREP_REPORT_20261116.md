# G.1b T1 GPU-node noise-floor job — preparation report (16 November 2026, ENGINEERING; NOT RUN)

**Status: prepared, not run, not submitted, not authorized to run.** No job was submitted, no GPU was used, no
labels were read, no server was started, and nothing was pushed to `main`. This report records what the unit
delivers, what it still needs from the G.0 census, the pre-declared caps, the cost projection and the residual risks.

**Branch:** `g1b-noise-20261116`, based on `origin/main` `9ae6d87783f53f9da27200869085c9ed0e7697e2`.
**Unit commit:** `1280219c025ee53224f8d9567a3eef1c3f3797f7` (`prepare(r1): G.1b T1 GPU-node noise-floor job for NEMO2
L40S (spec/JDL/docs/tests only; NOT RUN)`). This report follows it (`1bd478bd`), with two follow-ups on the branch:
`3df54893` (the offline summary now records the authority-fixed `vary` split separately from `e1_report`'s
descriptive split proposal) and `1b67274c` (the committed layout preview and `condor_submit -dry-run` ad were
regenerated from the final wrapper so they reproduce from the committed files). Branch tip at hand-off:
`1b67274c33b886e308ac90afdd429abb671063b1`; `origin/main` is untouched at `9ae6d877` and no force push occurred.

**Authority.** PLAN row `R1-TRACKG-G1B-HOST` (`author-decisions-20261116` @ `4da73306`): the G.0 census stays on Ada
(`R1-ADA-CENSUS`); the G.1b T1 GPU-node noise floor moves to **NEMO2 L40S (HTCondor)**, the same GPU model as the T1
labels (`R1-SWEEP-HOST-HTC`, `R1-BX-D5`). Also applied: `R1-BX-D5` (fixed step/token budget, one GPU model per
table), `R1-BX-REVISIONS (e)` census and `(f)` cost, `R1-ADA-CENSUS`/`R1-ADA-OVERFLOW`, the 22 Oct `D21` rule and its
uniform-application/pool rows, `R1-SWEEP2-SETTINGS` (1) 32,768 context and (5) the 60 GPU-h / 48 h author STOP, and
the sweep-2 HTCondor work plan (`docs/runbooks-16nov` @ `b3289232`).

## 1. What is prepared

| Deliverable | Where | State |
|---|---|---|
| Exact protocol, D21 qualification math, pre-declared decision procedure, recording/manifest fields, pinned environment, caps/chunking, STOP list, review checklist | `sweep2/g1b/G1B_PLAN.md` | complete for review |
| Spec template with the validated placeholder node list (8 `G0_PENDING_NODE_*` slots) + JSON Schema + runtime validator (refuses placeholders, G.0-empty lists, plan drift, placeholder run times/edit sets/runner, raised caps, plan-foreign chunks) | `sweep2/g1b/g1b_spec.template.json`, `g1b_spec.schema.json`, `g1b_lib.py` | complete; refuses to run today |
| Container entry (`ENGINEERING_ONLY`), spec validation, 552-run chunk expansion, E1-schema run rows, job record + manifest with host/GPU/CPU/library/image/harness/paper/runner pins, determinism gate, offline D21 summary, `/ceph` seal | `sweep2/g1b/g1b_job.sh`, `g1b_lib.py` | complete |
| JDL renderer/template (reviewed S2-C2 pattern: container universe, v1 gpu digest, `+RemoteJob`, L40S + CpuFamily 6 / CpuModelNumber 207 requirements, tarred outputs, no `ProvidesEtpCeph`, no machine regexp) | `sweep2/g1b/render_jdl.py` | complete |
| Dry-run evidence on deepthought (`condor_submit -dry-run`, no submission) | `sweep2/g1b/g1b_dryrun/` | rc 0; `JobUniverse=5`, `WantContainer=true`, digest `69b06b35…`, `RequestGPUs=1`, `RequestCpus=16`, `RequestDisk=42439718`, `RequestMemory=32000`, `RequestWalltime=10620`, `+RemoteJob=True`, L40S/Nemo2/CPU-class requirements; raw ad committed |
| Synthetic tests (no job/network/GPU): template + placeholder refusal (empty census, placeholder nodes/run times/edit sets/runner), D21 math (2 material edits, mean P(wrong) ≥ 0.10, σ_joint > 0, 30 seeds fixed), 60 GPU-h/48 h and chunk-wall STOPs, chunk plan/expansion, determinism pairing, JDL requirements, preview-not-submittable | `r1/tests/htcondor/test_g1b.py` | **23 passed** |

The unit has no dependency on unpushed code: the reviewed S2-C2 wrapper/renderer live on `sweep2-main-20261116` (not on
`main` at this base), so their pattern and constants were ported into a standalone `sweep2/g1b/` set.

## 2. What still needs the G.0 census (and cannot be invented here)

1. **Node names** — the candidate T1 node list from the experiment agent's G.0 census on Ada, with the census report
   path under `docs/r1/reports/` and its sha256. The spec carries a placeholder list; the job refuses to run with it
   (and refuses an empty list).
2. **Task assets** — the T1 nodes' `NodeSpec`, data, fixed-budget wrapper, metric parser and the reviewed code-diff
   measurement runner (module + sha256). The runner contract is declared in the plan; the engine does not exist yet
   (R1-BX-D4 diff support + T1 port review are prerequisites). No node can be measured before that.
3. **Per-node edit sets** — the five declared standard E1 edits (patch assets + sha256), scope/frozen paths. Fewer
   than five is an author STOP, not a reduced set.
4. **Per-node L40S run time** at the fixed budget (census, or the declared timing probe), metric name/direction, and
   request memory/disk from the measured peak (≥ the S2-C4 floors 32,000 MB / 42,439,718 kB).
5. **Harness pin** — the reviewed T1 label-table harness commit (template placeholder `PENDING_T1_HARNESS_PIN`); the
   noise floor and the T1 label table must share it (one environment; if the label pin later changes, σ̂ is re-measured).
6. **Paper commit** — the pushed commit carrying `sweep2/g1b/` + the runner (template placeholder today); the job
   verifies the transferred wrapper against the pinned tree.
7. **Author cap decision** — if the projection exceeds the 60 GPU-h / 48 h cap (likely; §3), the author raises the cap
   with a new row or narrows the candidate list **before any measurement** (D21 uniform application forbids trimming
   seeds or dropping nodes silently). The job refuses to run before that decision.
8. **Independent review** of this unit and the cluster-agent submission hand-off; no submission happens in this unit.

## 3. Estimated GPU hours per candidate and total (formula; measured run times pending)

`per-node GPU-h = 552 runs × run_seconds / 3600 = 0.15333 × run_seconds` (552 = 6 configurations × (30 train + 30
split + 30 joint + 2 default); one GPU per job and one GPU run at a time, so one-slot wall hours are GPU-hours).

| run_seconds | per candidate | 4 candidates | 6 candidates | 8 candidates |
|---|---|---|---|---|
| 30 | 4.60 | 18.4 | 27.6 | 36.8 |
| 60 | 9.20 | 36.8 | 55.2 | 73.6 |
| 90 | 13.80 | 55.2 | 82.8 | 110.4 |
| 120 | 18.40 | 73.6 | 110.4 | 147.2 |
| 300 (ceiling) | 46.00 | 184.0 | 276.0 | 368.0 |

Largest per-run time inside the cap: **97.8 s for 4 candidates, 65.2 s for 6, 48.9 s for 8**. With R1-BX-D5's 1–2 min
label budget the eight-slot placeholder list projects **73.6–147.2 GPU-h**, i.e. the cap is very likely hit. Note
that `R1-BX-REVISIONS (f)` budgeted "about 2 GPU-h" for a node's noise floor from a 10-seed training-only floor; the
D21 protocol needs 552 runs, **9.2× that line**, so at 120 s/run it is 18.4 GPU-h per node. This is a cost finding for
the author, not something the unit may work around.

**Chunking (pre-declared, from the measured S2-C4 layout):** one chunk = `(node, condition, contiguous seed part)` or
the node's 12-run `default` chunk; `walltime = 900 + ceil(runs × run_seconds × 1.35)` and seed parts are sized so every
chunk fits the 10,776 s ceiling (per node: 4 chunks at 30 s/run, 7 at 60 s, 10 at 90–120 s, 25 at the 300 s ceiling).

## 4. Pre-declared caps and STOPs

- **60 GPU-h total** and **48 h wall** (R1-SWEEP2-SETTINGS (5)): checked at validation and again at run time, with the
  per-node projection reported on STOP. A spec may lower these but may not raise them; a raise needs a new author row.
- **10,776 s per chunk**, **48 h per node's chunk total**, and **≤ 8 concurrent L40S slots** to keep the projected wall
  under 48 h; a pre-submit `condor_status` check is declared.
- Fail-closed STOPs: incomplete/placeholder G.0 census, plan/census drift, placeholder run time/edit set/runner,
  raised cap or over-cap projection, chunk outside the pre-declared plan, wrong image/marker/llama hash, off-class
  host/CPU/GPU, pinned-library mismatch, wrong harness/paper commit, wrapper/runner hash mismatch, D21 rule drift,
  missing/duplicate/extra run, non-deterministic fixed seed, deadline with unfinished runs, seal SHA mismatch or
  existing sealed target. Evidence is preserved, nothing is retried ad hoc, nothing deleted, no force push, never
  push `main`.

## 5. Residual risks

1. **The 60 GPU-h cap very likely triggers the author STOP** (9.2× the (f) noise-floor cost model); the author must
   decide between a raised cap and a smaller candidate list before G.1b runs.
2. **The T1 measurement runner does not exist yet** — the contract is declared and pinned by sha256 but has not run
   against a real T1 port; a stub-manager smoke run and a port review are prerequisites.
3. **Harness/paper pin coupling** — the noise floor must share the T1 label-table harness pin; the paper pin must be
   pushed before it can be pinned in the spec.
4. **Run-time uncertainty** — `run_seconds` is the projection's main lever; a census/probe underestimate trips the
   cap, an overestimate wastes wall.
5. **GPU determinism** — the job serialises GPU runs and fails the node rather than publishing σ̂ if a fixed-seed pair
   differs; the first real default chunk is the test.
6. **Image dependency coverage** — the v1 gpu image was frozen for the LLM label stack; T1 task dependencies may not
   be present, in which case an author-approved v2 digest (S2-C1 process) is needed and this spec must be re-reviewed.
7. **Disk/memory for T1 tasks** is not yet measured; the S2-C4 layout numbers are floors and G.0 must record the peaks.
8. **No analysis-lock risk declared:** no labels are read; the R1-BX-D8 lock is untouched. The only risk is a later
   misreading of these ENGINEERING rows as labels, which the label and manifest state explicitly.

## 6. Evidence index

- Plan/spec/JDL/wrapper/tests: `sweep2/g1b/`, `r1/tests/htcondor/test_g1b.py` (unit commit `1280219c`).
- Dry-run (deepthought, 16 Nov 2026, no submission, rc 0): `sweep2/g1b/g1b_dryrun/g1b_layout_preview.dryrun.txt`
  and `README.md`; scratch dir `/work/dwong/g1b_prep_20261116/` on deepthought left in place.
- Tests: `python -m pytest r1/tests/htcondor/test_g1b.py -q` → 23 passed.
