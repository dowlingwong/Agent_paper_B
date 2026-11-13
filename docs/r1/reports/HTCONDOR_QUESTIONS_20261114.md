# Open questions for the author — HTCondor preparation night, 13/14 Nov 2026

**Authority:** `docs/r1/prompts/HTCONDOR_PREP_RUNBOOK_20261114.md` §7 and the errata `docs/r1/prompts/HTCONDOR_PREP_RUNBOOK_ERRATA_20261114.md` §B (the review's fact-status ledger is authoritative where the wiki is login-gated). The author is asleep; nothing here waits for an answer. Each item has a recommendation and a paste-ready answer line.

---

## Q1 (STOP, highest priority) — W2 identity check found differences on sweep 1

**What.** The start-message line W2 asked for the read-only `w2_execute_all_identity_check` on the sweep-1 `root_trials.jsonl*` files. It was run from a clean detached checkout of `origin/mac-w2-budget-20261109` (`0b62fb03`) with the sweep's own Python env (`/ceph/dwong/r1_prepare_20261025/venv`, Python 3.13.15) and `--runs-total 20` (the top-level `"runs": 20` of `r1/scripts/configs/c3_sweep_deepthought.json`, SHA-256 `2fa891f4…`). Inputs: the 288 ledgers of the two sweep-1 modes (`C3_sweep_append_only_summary_20261027T154834Z`: 144; `C3_sweep_none_20261027T224356Z`: 144). Only `budget_index`, `decision`, `worker_mode` and `extra.control` were read; no label, metric, delta or edit field was opened; sealed paths were refused by the script.

**Result: `STOP_DIFFERENCE`, exit 3 — 14 of 288 ledgers differ.** All differences are `precheck_rejection` rows (53 rows in total across the differing ledgers): rows whose `worker_mode` ends in `_precheck` ran no worker, so the exec-all identity "worker runs used = trial index" does not hold on those campaigns. Largest cases: `digits_mlp__s114` (20 of 33 rows differ, 13 precheck rejections), `digits_mlp__s224` (17, 9 rejections), `digits_mlp__s194`/`digits_mlp__s264` (15 each). The 274 other ledgers are `IDENTICAL`; `worker_runs_total` never exceeds the 20-run cap. This is exactly the outcome `reports/W2_BUDGET_FIELDS_20261109.md` predicted for sweep tables that contain precheck rejections: **a real difference between the trial-index definition and the worker-run definition, not a bug.**

**Why it is a STOP.** The W2 line says 如有差异 STOP 交我决定. Nothing was adopted, recomputed, edited or resubmitted. The full machine-readable summary is `docs/r1/reports/htcondor_prep_20261114/w2/w2_check.json`; the ledger list and the interpreter/checkout are recorded beside it.

**Options.**
- (a) Accept that W2's worker-run budget applies to the sweep-1 tables only on the 274 pure exec-all ledgers, and that the 14 precheck-affected campaigns keep the old trial-index budget in any re-analysis; record the split.
- (b) Declare the sweep-1 tables out of scope for W2 and use only the synthetic/golden identity results already reviewed on 9 Nov.
- (c) Re-run the check with a different definition after an author ruling (would need a new reviewed script; not done tonight).
**Recommendation:** (a) — it matches what the W2 report already says the difference means, and it keeps the 274-ledger identity evidence.

**Paste-ready answer:** `W2 采用 (a)：274 个 pure exec-all ledger 用 worker-run 定义，14 个含 precheck 的 campaign 保留旧 trial-index 定义并记录分割。`

---

## Q2 — No image tonight: docker daemon unreachable, registry unknown

**What.** `docker` is installed and the account is in the `docker` group, but `docker info` **cannot connect to the daemon** (measured twice). Under errata A3 the docker gate therefore stops §3 before any build, and no `docker login`/credential read is allowed. The local `docker save` route would not give a pullable image anyway. Consequence: **I1–I4 were not submitted**; the goal "pinned image on the batch system" is deferred; the probe wave used the official image (`cverstege/alma9-gridjob`) as designed.
**Options.** (a) next window: author starts the docker daemon / names a registry+namespace the pool can pull; (b) use `apptainer` locally and a `.sif` + question on docker-universe delivery; (c) abandon the image and run the ported environments via `/work` + apptainer.
**Recommendation:** (a) for the container goal, (c) as the fallback for env delivery.
**Paste-ready answer:** `镜像：下个窗口我处理 docker daemon；registry/namespace 用 <REGISTRY/NAMESPACE>。`

---

## Q3 — HTCondor `accounting_group` for the probes

**What.** The author has **no completed past HTCondor jobs** (`condor_history dwong` empty; `condor_userprio` shows `dwong@etp.kit.edu` with 0 weighted hours and last usage "20770+22:4"). At 23:40 CET one **idle job of the same account, not ours** was visible: cluster 759618 (`/work/dwong/r2_batch/tiny/exe.sh`) with `AcctGroup=cms`, `AccountingGroup=cms.dwong` — evidence that the `cms.dwong` group exists, but not a past-job convention and not ours. Per runbook §0.4 A the probes start **without** `accounting_group`; if the pool holds them for that reason the errata fallback is the documented `belle` (not the misattributed `cms.higgs`), CPU probes only, and recorded.
**Options.** (a) leave unset unless held; (b) author assigns `cms.dwong`; (c) `belle` from the start.
**Recommendation:** (a) now, (b) if the author wants the account's own group; do not use `cms.higgs`.
**Paste-ready answer:** `accounting_group 用 <cms.dwong | 先不设 | belle>。`

---

## Q4 — Which XRootD endpoint / transfer-size rule is current?

**What.** The runbook names `root://ceph-node-j.etp.kit.edu`; the reachable 2022 ETP tutorial names `root://ceph-node-a.etp.kit.edu`; the 100 MB HTCondor-transfer limit is not in the public tutorial (it says >2 GB input per 30 min runtime = data-intensive). Neither was used tonight (I3 deferred; `/ceph/srv/dwong` does not exist).
**Recommendation:** confirm both from the current wiki before any model transfer; treat ">2 GB per 30 min" as the input-size rule until then.
**Paste-ready answer:** `xrootd 端点 = root://ceph-node-<a|j>.etp.kit.edu；传输规则按 <wiki 原文>。`

---

## Q5 — Pool facts that differ from the runbook or are unverified

- **TOpAS GPU counts:** measured slots show V100S nodes with 8 GPUs each and A100 nodes; the runbook says V100S 16, the 2024 HEPiX deck says 24. The partitionable-slot listing does not settle the site total. **Question only.**
- **NEMO2 H200:** the only visible H200 slot (`g4401`) was **Drained** at 23:40 → probe P7 may stay idle; L40S slots were available. **Not a deviation, just a measurement caveat.**
- **ClassAd names:** `ProvidesETPResources`, `ProvidesEtpCeph`, `CloudSite`, `GPUs_DeviceName`, `request_GPUs` are confirmed by dry-run/measured slots except `ProvidesEtpCeph` (no I-probe tonight) and the "up to 8 GPUs" rule. **Recorded as unverified, not adopted.**
- **`bms2`** is not in the reachable public docs (2022 deck: `bms[1,3] portal1 deepthought`). **Question only.**
- **Fair-share "started 6 times is held"** is not in any reachable public source. **Unverified.**
**Paste-ready answer:** `Q5：<确认/更正哪一条>。`

---

## Q6 — `/ceph/srv/dwong` does not exist

**What.** `/ceph/srv` exists and is world-writable, but there is no `dwong` directory, so the I3 model-load-from-`/ceph/srv` route is unavailable tonight (I3–I4 deferred anyway). If the author wants the model path tested next window, they need to place the pinned GGUF (`509287f7…4d3c`) there or confirm the xrootd route.
**Paste-ready answer:** `模型：放 /ceph/srv/dwong 还是走 xrootd，<决定>。`

---

## Q7 — Queue behaviour and tonight's cut-offs (informational)

**What.** The pool was at 1051/1105 claimed when the probes were submitted; queue waits are the measurement, not a fault. The +6 h resubmission wave is dropped (errata A4) because it cannot complete before the 05:30 stop; the +3 h sample is attempted if the window allows. The `04:30` "all probes submitted" cut-off and the `03:30` "stop starting new moves" cut-off are the two that can drop work if the night slips.
**Paste-ready answer:** `Q7 已知，按 cut-off 执行。`

---

## Q8 (new, measured tonight) — NEMO2 GPU slots have no Docker: P6/P7 cannot run as designed

**What.** `condor_status` on the NEMO2 L40S/H200 slots shows `HasDocker=undefined` and `HasSingularity=true`; a docker-universe job therefore cannot match them (`P6`'s CloudSite+device terms matched 6 L40S slots, then `TARGET.HasDocker` matched 0 — measured, not inferred). P4–P7 were submitted as the runbook designs them (official image, `Universe=docker`); P6/P7 are **structurally un-runnable** on NEMO2, independent of queue load. P7 also has no eligible slot (the only H200 slot is Drained).
**Options.** (a) for a future window, author confirms from the wiki whether NEMO2 jobs must use a non-docker (vanilla + Singularity/apptainer) design; (b) keep NEMO2 out of the probe set and use TOpAS only (V100S ran: wait 212 s); (c) author asks the site to enable Docker on NEMO2.
**Recommendation:** (a)/(b); a JDL change needs its own reviewed unit, so it was **not** improvised tonight.
**Paste-ready answer:** `NEMO2：下一窗口用 <vanilla+singularity | 只用 TOpAS>；JDL 改动走新评审。`

## Q9 (new, measured tonight) — A100 capacity, and TOpAS routing confirmed

**What.** TOpAS **is** reachable by flocking (P5 V100S ran on `c03-001-159`, 212 s wait, exit 0). P4 (A100) does not match because the A100 partitionable parent `slot1@c03-001-167` advertises `TotalSlotGPUs=8` but `GPUs=0` and `Cpus=0`, all children Claimed/Preempting — the A100 node was fully allocated at 23:52–00:10. It may free later; the probe stays queued and is recorded as a capacity wait, not a design failure.
**Also measured:** all four ETP login hosts (`portal1`, `bms1`, `bms2`, `bms3`) are reachable from the Mac and mount `/ceph/dwong` (so `bms2` is **verified**, contrary to the wiki-derived note in §0.3).
**Paste-ready answer:** `Q9 已知，A100 等容量；bms2 可登录已确认。`
