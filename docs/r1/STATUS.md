# Paper B (route R1) — status log

- B1 read-only preparation (4 Nov): 15 candidate GGUFs plus the Qwen model anchor all present on TASL-2, each size and SHA matching the pinned Stage A registry; two software anchors need no GGUF. `df` showed 183.291 GB available on the exam filesystem. No download or B1 launched. Evidence: `reports/OPS_B1_PREP_20261104.md` and inventory text; independent review accepted (`reviews/OPS_B1_PREP_REVIEW_20261104.md`).

- Operator O3 `digits_mlp` S0.1 preflight STOP (4 Nov): no GPU job started. Pins and templates checked; the suffix-enabled launcher would overwrite old session `.cmd` files and append old logs, conflicting with the no-touch-existing-files rule. A scoped author ruling on unique sessions and append-only watcher/server logs is requested. The earlier invalid rerun remains preserved. See `reports/OPS_O3_S01_PREFLIGHT_20261104.md`; independent re-check accepted the preflight STOP record (`reviews/OPS_O3_PREFLIGHT_REVIEW_20261104.md`), not a launch.

- Operator O7 authorization check (4 Nov): installed the Track P marker helper on TASL-7, source/installed SHA `f457a04e…`; no marker or training job started. P.3a STOP: the committed note authorizes E6 A1–A5 by reference to spec §5.6, whose A3 includes the 2k/8k descriptive rows; an amended note excluding them has been requested. See `reports/OPS_O7_AUTH_CHECK_20261104.md`; independent review accepted for the documented installation and authorization assessment (`reviews/OPS_O7_REVIEW_20261104.md`), not a P.3a launch authorization.

- Operator O1 receiving audit (4 Nov; ENGINEERING_ONLY; read-only): `reports/OPS_O1_20261104.md` and `reviews/OPS_O1_REVIEW_20261104.md`. `t7j10` completed and released its validated lease; Qwen anchor metrics match `t7h8`, all eight model rows and repair-template hashes checked, including offline recomputation of 440 A1 template comparisons. Following the author's explicit ruling that matching N/A applicability and PASS satisfy the condition for `random_valid` and `scripted`, the same reviewer **ACCEPTED** the `t7j10` receiving review. O1's separate author acceptance row remains to be committed. No B1 launch; prior evidence retained unchanged.

- STOP 0 author reply (4 Nov): coordinator, Track S, Track P and deepthought operators reported stopped at safe points; Track X agent will stop after `t7j10` completes. Scoped Stage A / M1 recovery authorization on TASL-7 takes effect after that agent stops; no recovery authorization for other hosts or tracks. Details and a read-only deepthought owner check in `reports/OPS_STOP0_AUTHOR_REPLY_20261104.md`. Four sampled GPU processes belonged to `mmolch`; untouched. `t7j10` remained active at the check. O1 receiving work follows the Track X agent's stop.

- Operator O0 census (4 Nov; AI-assisted, read-only): `reports/OPS_O0_CENSUS_20261104.md`, supplemental evidence `reports/OPS_O0_SUPPLEMENT_20261104.txt`. `t7j10` active on TASL-7 under its guardian; all four deepthought GPUs had other users' compute processes; Ada GPUs 3 and 6 had no reported compute apps. Independent re-check accepted the documented census (`reviews/OPS_O0_REVIEW_20261104.md`). STOP 0 remains open: prior operators' actual stop state and the author's scoped recovery-authorization decision are unverified. No remote state changed; no experiment started.

- Author's replies to the M1 packet (4 Nov 16:13; verbatim in `proposals/AUTHOR_DECISIONS_20261104.md`) and the Mac agent's follow-up (AI-assisted record). Author: (1) R1-TRACKX-HANDOVER-RULING committed to PLAN §10 on his instruction (decision cell "按原定计划走", details under Consequences); (2) packet (a): the five out-of-scope b2-repair files are reviewed within M3, and he decides afterwards; (3) packet (k): cloud-run tests accepted; the three inherited `test_c3_launch_provenance` failures count as a known exception only once M3 fixes them; (4) `docs/runbooks-04nov` @ `0abfaf2b` (Mac runbook rev 3.3, HoreKa scan prompt rev 5.4) merged into `mac-int-20261104` separately; (5) M10 to start (local worktrees; harness write access requested for `r1-local-trackg-20261104` only); (6) M11 and M13 follow in the Mac agent's order. Mac agent: workers running under rev 3.3: M2 (`mac-x5v2-20261104` from `74a0790`), M3 (`mac-b2-20261104` from `f98e315e`), M10 (`mac-trackg-20261104` from `98e433e0`, harness `r1-local-trackg-20261104` from `897d83c`). Points (2) and (3) are not PLAN rows.
- M1 integration (4 Nov, Mac-local agent; AI-assisted, documents and merge only; MAC_LOCAL_RUNBOOK_20261104 rev 3.2): branch `mac-int-20261104` on coordinator `10742f85` (author, 15:38), integrating `docs/runbooks-04nov` @ `c15b1102` (⊃ `docs/main-proposer-03nov` @ `14dc0fea`), `codex/b2-repair-20261031` @ `f98e315e`, `docs/trackS-decisions-30oct` @ `13badb0` and `trackS-ops-20261030` @ `f5d5c6b0`. Row check `reports/MAC_PLAN_ROW_CHECK_20261104.md`: 0 missing. Code taken only from b2-repair (none from Track S): `r1/c3/audit.py`, `r1/c3/dataset.py`, `r1/c3/offline_eval.py`, `r1/scripts/c3_label_sweep.py`, `r1/scripts/c3_label_sweep_launch.sh` (the B.2 evidence-guard, split-audit and classification code MAC_LOCAL_RUNBOOK §1 names; none on §0's shared list or R1-HANDOVER-04NOV's out-of-scope list), the new `r1/c3/evidence_boundary.py` (the boundary those files import) and `r1/scripts/c3_mount_inode_candidate.py` (the branch's mount-inode replay check), with their tests. Held: the five out-of-scope files (packet (a)). Tests: `reports/MAC_M1_TESTS_20261104.md` (cloud workspace; 3 inherited `test_c3_launch_provenance` failures, packet (k)). Pin table: RUNBOOK §5 "Current code pins (4 Nov)". Decision packet: `proposals/AUTHOR_DECISIONS_20261104.md`, with the author's Track X handover ruling (15:33, 15:44) in §0 as draft row R1-TRACKX-HANDOVER-RULING (not yet in PLAN). Review `reviews/MAC_M1_REVIEW_20261104.md`: round 1 not accepted (0 BLOCKING, 3 MAJOR, 11 MINOR), re-check **accepted** at `a9eb5952`. **Handoff: `mac-int-20261104` @ `a9eb5952`** (this entry's hash line and the review file follow in the next commit). The operator hand-off waits for R1-TRACKX-HANDOVER-RULING in PLAN.
- M1 STOP 9 and relaunch (4 Nov): `t7i9` stopped at `qwen25_coder_7b` because the A1 amendment's 50 frozen non-generation checks were outside the legacy 6-row journal whitelist; no M1 evidence, t7i9 not reused. Recovery ended the preserved qwen25 server + guardian (LOCK-FREE, GPU idle; `~/exam-x/work/r1_stop9_shutdown_20261104T142243Z/`). Fix: stage_a records the exact expected non-generation rows and gates the `/tokenize` fallback on an actual A1 attempt; cache_order validates the declared rows (legacy None unchanged). Code `ab74203` + binding `74a0790`; reviews `131dad8d…` and v17b gating (`4fef681e…`, 410 passed/1 skipped). Fresh TASL-7 preflight `2a8fa22b…`; declared M1 relaunched as `r1_stagea_20261104_t7j10` (manifest `64a2712c…`, A1/10-model declaration, guardian 386549). M1 receiving review required before B1 eligibility; B1/B2, P.3a, B.2 remain STOP; t7h8/STOP1–8 untouched. See `docs/r1/reports/EXAM_TRACKX_STAGEA_STOP9_20261104.md`.

- HoreKa scan fully delegated (4 Nov 15:11, author: "直接让他全权处理扫描"): scan prompt revision 5 — the agent itself starts the `agent`-partition session and the tunnel (the two login-node commands NHR's IDE page gives), keeps its SSH config and host keys in its own folder, runs everything else on the compute node, and ends the session.
- A1 amendment implemented (4 Nov): code `e996af8` + binding `96f1146` after design review (`251f18a7…`) and code review ACCEPT with conditions (`90609c9b…`; v16b snapshot `55770d1b…`, 64/62, 408 passed/1 skipped). A1 template check = byte equality or one tokenizer-BOS prefix with HF ids == [bos]+ids(served) AND pinned-build `/tokenize` equality, applied to the 5 fixed + 50 frozen checks with per-check evidence; other checks unchanged; t7h8 evidence not retroactively modified. Declared M1 `r1_stagea_20261104_t7i9` (3 anchors + 4 BOS-artifact + 3 repaired, `--amendment A1`, declaration in `amendment_measurement`) is the next step, separate table, receiving review required; B1 eligible logic recorded in PLAN. Repairs SHA-pinned, probe==replay, launcher pins templates; B1/B2, P.3a, B.2 remain STOP.

- Two server agents (4 Nov 14:58, author: "按照你建议的执行"): PLAN §10 R1-SERVER-AGENTS-TWO — the operator (TASL-2, TASL-7, deepthought; Ada fallback) and a separate HoreKa agent (HoreKa 2, whole T1 tier). Operator runbook rev 3.2: O8 reduced to "T1 belongs to the HoreKa thread". The HoreKa runbook is written after the scan.
- Amendment v16 ready for code review (4 Nov): design-review conditions folded into the frozen v16 snapshot (`SHA256SUMS` `22f161c6…`, 61 files; subset **408 passed / 1 skipped**): A1 template check (byte equality or one tokenizer-BOS prefix with HF-id and pinned-build `/tokenize` equality, now applied to the 5 fixed and 50 frozen checks with per-check `template_check_evidence`); runner `--only`/`--amendment A1`/`--amendment-reason` (registry-validated subset, declaration recorded in `amendment_measurement`, normal Stage A unaffected); runtime/qualification-probe `--chat-template-file` plumbing with SHA checks; guardian `TRACKX_MANIFEST_SHA256`; launcher pinning of repair templates; registry `template_repair` entries and the three validated repair templates (olmo guarded-tools `5d275f78…`; devstral pinned HF `a0c0ed8a…`; ministral pinned HF `2f545122…`; validation `56d06c5b…`). No measurement executed yet; scoped code review requested; B1/B2, P.3a, B.2 remain STOP; t7h8 evidence untouched.

- Author chose **Option A** (4 Nov) for the template finding: prepare the amendment draft, the declared amendment measurement and the repair-template drafts, all for independent review before execution. Proposal committed (`docs/r1/reports/EXAM_TEMPLATE_AMENDMENT_PROPOSAL_20261104.md`): amended template check = byte-equality **or** single-leading-special-token + token-id equality with per-check evidence; declared amendment measurement `r1_stagea_20261104_t7i9` (new dirs, `--only` subset: the 4 BOS-artifact candidates + 3 repaired models, separate table not spliced into t7h8); repair templates: `olmo31_32b` guarded-`tools` (`5d275f78…`; server starts, renders byte-equal 5/5 + 50/50), `devstral_small2_24b` pinned HF template (`a0c0ed8a…`) and `ministral3_14b` pinned HF template (`2f545122…`) via `--chat-template-file` (both token-equal 5/5 + 50/50); validation artifact `~/exam-x/work/r1_repair_drafts_20261104/validation/validation.json` (`56d06c5b…`). No protocol/template/registry/code change made yet; implementation deltas are to be frozen and independently reviewed before execution. B1/B2, P.3a, B.2 remain STOP; t7h8 evidence untouched.

- Template failure map (4 Nov, diagnostic only): the post-Stage-A render diff shows 6 of the 9 template rows are a **BOS-prefix artifact** (`gemma4_31b`, `gemma4_26b_a4b`, `gemma4_12b`, `laguna_xs21`, `lfm25`, `muse`: server render == HF render minus the leading special token; token sequences equal — llama.cpp adds BOS at tokenization), 2 are genuine GGUF-vs-pinned-template mismatches (`devstral_small2_24b`, `ministral3_14b`), and `olmo31_32b` renders byte-equal (5/5, 50/50 with `--no-warmup`) but fails the pinned build's parser generation. `lfm25`/`muse` keep genuine grammar exclusions; grammar-only and offload rows are unrelated. Recommendation (awaiting author): reviewed token-equality amendment + new declared measurement for the four BOS-artifact candidates; targeted SHA-pinned/reviewed repairs for `olmo31_32b` and the two GGUF-mismatch models; build-pin only if the olmo repair fails, after a diagnostic. Artifact `~/exam-x/work/r1_template_diff_20261104/render_diff.json` (`c2a9d6c6…`); report `docs/r1/reports/EXAM_TEMPLATE_FAILURE_MAP_20261104.md`. B1/B2, P.3a, B.2 remain STOP; t7h8 evidence untouched.

- HoreKa scan back on HoreKa 2 (4 Nov 14:37, author: "改改扫描的runbook，我们在horeka2上扫"). Scan prompt revision 4: the agent works only on an `agent`-partition compute node through the SSH tunnel the author opens (`start-vscode-remote-ssh.sh`), per NHR@KIT's login page (section "Interactive AI agent usage on login nodes is prohibited", pointing to the SSH tunnel to compute nodes); option B (the author runs the commands) kept.
- HoreKa scan target (4 Nov 14:22, author): scan legacy HoreKa only (`ir7683@horeka.scc.kit.edu`), not HoreKa 2. `prompts/HOREKA_SCAN_PROMPT_20261104.md` revision 3 retargeted (partitions `accelerated`, `dev_accelerated`, `cpuonly`, …; H100 partitions probed only by `--test-only`). Retargeting not separately reviewed.
- Track X Stage A COMPLETE (4 Nov): attempt `r1_stagea_20261103_t7h8` on TASL-7 (code `3b3283f`, binding `19b8f33`; Stage A manifest `95bfc8b6…`, preflight `5f440643…`), started 2026-11-03T20:25:49Z, lease released 2026-11-04T12:44:31Z after the guardian's validated completion: `released:true`, `reason:validated_completion`, `records_verified:43` covering every `llama_server_*.json` (including the failed-start probe records), no `STOP.json`, lock free afterwards, GPU idle, 22/22 models. 24 rows: 2 software anchors + 20 candidates + `qwen25_coder_7b` + `olmo31_32b_think`; 8 candidates PASS (`glm47_flash`, `ornith10_35b`, `ornith10_9b`, `qwen35_9b`, `qwen36_27b`, `qwen36_35b_a3b`, `qwen38_27b`, `qwen3_coder_30b_a3b`), `template` 7, `grammar`+`template` 2, `grammar` only 3, `offload` 1 (`nemotron35_30b_a3b`, evidenced 32k + 16k). STOP-6/7/8 fixes validated live. Evidence: `~/exam-x/work/r1_stagea_20261103_t7h8` (`batch_state` `ae6adef5…`, table `00ab143d…`) and lease dir (`release` `415eb713…`). Stage A receiving review requested; template failure map + 5/50-prompt render-diff next; B1/B2, P.3a, B.2 remain STOP. See `docs/r1/reports/EXAM_TRACKX_STAGEA_COMPLETE_20261104.md`.

- T1 on HoreKa 2 (4 Nov 13:45, author; AI-assisted record): "T1 整层（census、噪声底、proposer、sweep、审计）搬到 HoreKa 2 的 H100，Ada 作整表后备" → PLAN §10 R1-T1-HOREKA. Read-only scan prompt for an SSH agent: `prompts/HOREKA_SCAN_PROMPT_20261104.md` (one login-node SSH call, one 15-min dev GPU job; no changes). No run started.
- 1GC-7RC replaced (4 Nov, 11:55 and 12:45, author; AI-assisted record): "1GC-7RC没公开repo" … "1GC-7RC 换成 MLAgentBench我同意". PLAN §10 R1-1GC-FALLBACK: the suites are autoresearch, MLGym and MLAgentBench; 1GC-7RC's public datasets may be extra tasks counting toward no suite. Draft for running T1 on HoreKa 2 by Slurm job submission: `proposals/HOREKA_T1_JOBS_DRAFT_20261104.md` (not adopted; the host choice is the author's).
- Author rulings (4 Nov, 11:29; AI-assisted record, documents only). Reply: "1. 1GC-7RC 仓库是什么仓库，不要说黑话 2. apptainer在deepthought2 3. T1是什么，为什么这么久 4. 其他决定按照你的建议来 5. 标 ⚠ 的缺口，你现在补". Recorded in PLAN §10 "4 November 2026 (11:29)": R1-HANDOVER-04NOV, R1-BX-PORTING-CONFIRM, R1-ADA-CENSUS, R1-APPTAINER-HOST, R1-EXAM-ALWAYS-ON-SKIP, R1-EXAM-B1-HARNESS-PIN, R1-B2-REPLAY-GO, R1-P3A-OOM-OPTION3, R1-TRACKS-S01-RERUN, R1-BX-PROPOSED-CONFIRM (item by item); the recommendations are kept as `proposals/RECOMMENDATIONS_1121_20261104.md`. **Pending** the author's confirmation after the explanations he asked for: the 1GC-7RC fallback (A4) and the B.7 timing (H1). Still open: see that subsection. Execution runbooks rev 3.1: operator O9 (A4), O10 (C.1–C.4, D.1 retraining), O11 (D.3); Mac M14 (B.3, A4 calibration, gate report), M15 (C.2 merge, C.4, D.1, D.2, D.4). Review `reviews/RULINGS_1129_REVIEW_20261104.md`. No run was started.
- Benchmark expansion adopted (4 Nov, author; AI-assisted, documents only): the author adopted `proposals/PAPER_B_REVIEW_BENCH_EXPANSION_20261104.md` in full. Recorded as PLAN §10 **R1-BX-D1 … R1-BX-D14** and **R1-BX-REVISIONS** (ids distinct from the problem-spec D1–D28): CPU pool → testbed T0; GPU label nodes T1 and evaluation nodes T2 from autoresearch, 1GC-7RC and MLGym; leave-one-suite-out primary; code-level diffs on GPU nodes; fixed step budgets; K = 6 only if the sweep-1 subsampling check passes (it needs sweep-1 B.2 first); aggregate C3 gate (IQM gap closed, probability of improvement), to be confirmed before any sweep-2 label is analysed; A4 as the self-control arm, R-B optional; practitioner baselines; information-matched TabPFN; API proposer in closed loop; Track S GPU nodes and a 15 Dec fallback; B.6 cut; Stage D on 1–2 T1 nodes; targets B.7 ≈ 8 Dec, D.3 ≈ 3 Jan, manuscript 10 Jan. RUNBOOK (Track G rewritten as the critical path; Track S additions), C3_DESIGN, TRACK_P_POST_TRAINING, TECH_ROUTE, `prompts/TRACK_G_RUNBOOK.md`, the Mac-local and operator runbooks (revision 3) and README revised; `proposals/TRACK_S_GPU_EXTENSION_20261104.md` added. *(proposed)* and *(open)* items in the rows await the author. No run was started. Independent review `reviews/BENCH_EXPANSION_REVISION_REVIEW_20261104.md`: round 1 not accepted (5 MAJOR, 12 MINOR; porting routed to the operator, a separate R1-BX-D8-CONFIRM prerequisite, the D3 check restricted to label seeds, proposer-host conditions marked proposed, TabPFN on TASL-7, and the minors), fixed; round 2 accepted (remaining MINORs applied afterwards, recorded in the review file).
- Main proposer decision (3 Nov, author; AI-assisted, documents only): **R1-MAIN-PROPOSER** — the Track X pick, thinking off, becomes Paper B's main proposer; C3 training data and the B.7 gate come from a new **sweep 2 (RUNBOOK B.1b)** on the same instances as sweep 1, on one RTX 4090 host; sweep 1 (`qwen2.5-coder:7b`) becomes the second source and replaces B.6's second manager; X.6/X.7 amended (thinking-off B2 run for every eligible finalist; pick chosen on thinking-off Y). Prerequisites: the exam rule `x5_rule_v2` before B1; thinking off as a server flag set by the paper-side sweep; a harness pin carrying the `cache_prompt` switch. Proposed, for the author to confirm: deepthought-CPU audits for sweep 2, a 4-day projection STOP, Track S keeping the 7B. Revised 4 Nov after an independent review (not accepted: 1 BLOCKING, 6 MAJOR): the exam's frozen rule must become `x5_rule_v2` before B1; thinking off is a server flag set by the paper-side sweep, not a harness change; sweep-1 B.2 precedes the harness pin; sweep-1/sweep-2 stack differences listed; twin-instance leakage handled by one shared split; R1-SWEEP-HOST amended explicitly. Independent review accepted on the third round (`reviews/MAIN_PROPOSER_PLAN_REVIEW_20261104.md`). Branch `docs/main-proposer-03nov`; not merged. No run started or stopped.
- Track X Stage A STOP 8 and restart (3 Nov): attempt `t7g7` STOPped entering the 16384 retry for `nemotron35_30b_a3b` with `GPU not available for independent qualification` — a transient teardown artefact of the just-exited 32k probe server read by a single instantaneous observation. Before the stop, 11 rows were valid including the evidenced 32k OOM mechanical-failure row, and the STOP-7 fix was validated on two real failed starts (`olmo31_32b` and the nemotron 32k probe: SAME-OFD `lease_inheritance` + `stopped_utc` + `returncode` present). Recovery under the standing authorization ended only the retained guardian (LOCK-FREE, GPU idle; evidence `~/exam-x/work/r1_stop8_shutdown_20261103T202105Z/`); t7g7 is engineering evidence only. Fix: bounded `await_idle_gpu()` (12 observations, 5 s apart) at the pre-qualification call site, criterion unchanged/fail-closed, foreign workload still STOPs, unknown census STOPs immediately. Independently reviewed ACCEPT with conditions (snapshot v15 `23689415…`, 394 passed/1 skipped). Committed `3b3283f`, binding `19b8f33`; fresh TASL-7 preflight passed and the new attempt `r1_stagea_20261103_t7h8` was launched at 20:25 UTC under the reviewed guardian holding the real `gpu0.lock`. STOP-1..8 evidence untouched and not reused; B1/B2 not started; P.3a and B.2 remain STOP. See `docs/r1/reports/EXAM_TRACKX_STAGEA_STOP8_20261103.md`.

- Track X Stage A STOP 7 and restart (3 Nov): attempt `t7f6` COMPLETED all 24 rows (batch `status: COMPLETE`; every replay offload record `route:log_line`; STOP-4 template rows and STOP-6 32k-OOM→16k-retry validated live) but the runner's lease-completion check stopped because three failed-start qualification probe records (olmo31_32b template parser error; nemotron35_30b_a3b 32k/16k KV OOM) lacked `stopped_utc` and `lease_inheritance`; the guardian correctly retained the lease. Recovery under the standing authorization ended only the retained guardian (LOCK-FREE, GPU idle; evidence `~/exam-x/work/r1_stop7_shutdown_20261103T093541Z/`); t7f6 is preserved engineering evidence, not Stage A evidence. Fix: capture the SAME-OFD lease proof immediately after Popen (before the readiness loop) and finalize failed-start records with `stopped_utc`/`returncode`/`stopped_before_ready`; a gone child yields no invented proof (fail-closed), a genuine proof failure with the child alive still STOPs. v14 was BLOCKed (guardian also requires inheritance), v14b ACCEPTed with conditions (snapshot v14b `9724933f…`, 391 passed/1 skipped; reviews in `docs/r1/reviews/`). Committed `6f1b90b`, binding `70a7a6f`; fresh TASL-7 preflight passed and the new attempt `r1_stagea_20261103_t7g7` was launched at 10:49 UTC under the reviewed guardian holding the real `gpu0.lock`. STOP-1..7 evidence untouched and not reused; B1/B2 not started; P.3a and B.2 remain STOP. See `docs/r1/reports/EXAM_TRACKX_STAGEA_STOP7_20261103.md`.

- Track X Stage A STOP 6 and restart (2 Nov): attempt `t7e5` stopped at `nemotron35_30b_a3b` qualification on a real 32k KV-cache cudaMalloc OOM that the old classifier could not evidence (real startup probes leave `server_stop`/`pins_match` unset and prefix the OOM line with timestamp/level), so the runbook's intended 16k retry was unreachable and the batch stopped after 11 rows (not Stage A evidence; the template-classification fix had been validated in-run: `olmo31_32b` became a `template` row and the batch continued). Recovery under the standing authorization ended only the retained guardian (LOCK-FREE, GPU idle; evidence `~/exam-x/work/r1_stop6_shutdown_20261102T164722Z/`). Fix: real-shape `known_load_oom` (retained in-attempt log+SHA, top-level gpu/binary/build/model pins, recorded startup exit, OOM line anywhere in the log, healthy-idle census) plus a runner evidence re-check; 16k fallback only through the evidenced healthy-idle OOM. Committed `14b9f79`, binding `9d2e213`; independent scoped review ACCEPT with conditions, and the fixture-provenance condition was verified byte-identical against the retained log (snapshot v13 `75e37587…`, 388 passed, 1 skipped). A fresh TASL-7 preflight passed and the new attempt `r1_stagea_20261102_t7f6` was launched at 16:54 UTC under the reviewed guardian holding the real `gpu0.lock`; periodic checks include progress. STOP-1..6 evidence untouched and not reused; B1/B2 not started; P.3a and B.2 remain STOP. Template policy decision (a now / targeted b after completion / c only after diagnostic) recorded in PLAN. See `docs/r1/reports/EXAM_TRACKX_STAGEA_STOP6_20261102.md`.

- Author template-policy decision (2 Nov): (a) keep the running attempt `t7e5` and record template-class exclusion rows now; (b) after completion, produce the failure map and 5/50-prompt render byte-diff evidence, then targeted one-repair-per-model proposals only where renders are byte-equal and the parser generates, SHA-pinned/declared/reviewed and measured in a new declared repair attempt (priority `olmo31_32b`, `gemma4_31b`, `muse_glimmer_30b`); (c) build-pin change only if needed, after a diagnostic new-build screen with no exam evidence. No template or build changes without that evidence and review. `t7e5` continues; B1/B2, P.3a and B.2 remain STOP.

- Track X Stage A STOP 5 and restart (2 Nov): attempt `t7d4` stopped at its first qualification with `observed server count or identity mismatch` because a stale CPU-only (`-ngl 0`) `llama-server` (pid 2589942, `ornith10_9b`) had survived the killed template-screen diagnostic; the census correctly failed closed, no evidence from this attempt is used. Under the standing recovery authorization the stale server, the preserved qwen25 server and the guardian were ended (LOCK-FREE, GPU idle; evidence `~/exam-x/work/r1_stop5_shutdown_20261102T070948Z/`). Fix: the reviewed launcher refuses to prepare a run when a `llama-server` executable or a GPU compute process is visible (occupancy check, not exclusivity proof; runtime census unchanged), committed `caa2f70`, binding `5d66967`; independent scoped review ACCEPT with conditions (snapshot v11 `f2c6adf5…`, 386 passed, 1 skipped). A fresh TASL-7 preflight passed and the new, separately identified attempt `r1_stagea_20261102_t7e5` was launched at 07:14 UTC under the reviewed guardian holding the real `gpu0.lock`; periodic checks include progress. STOP-1..5 evidence untouched and not reused; B1/B2 not started; P.3a and B.2 remain STOP. Open author decision: template coverage/repair/new build pin. See `docs/r1/reports/EXAM_TRACKX_STAGEA_STOP5_20261102.md`.

- Track X Stage A STOP 4 and restart (2 Nov): attempt `t7c3` stopped at 04:00 UTC when `olmo31_32b`'s pinned GGUF template made the pinned llama.cpp build fail automatic parser generation (`tools | tojson` on undefined tools) and the server exited at startup — a pinned-build template incompatibility, not offload/GPU/lease/cache. Seven rows had completed (all offload `route:log_line`, no fallback; `muse_glimmer_30b` recorded candidate failures `template`+`grammar`). Under the author's standing recovery authorization the retained guardian was ended (lock free, GPU idle; evidence `~/exam-x/work/r1_stop4_shutdown_20261102T062008Z/`). Fix: a retained, pinned, in-attempt log with the explicit template parser error + model-loading failure and a recorded startup exit is classified as a candidate `template` failure (row recorded, no server, no 16k fallback, batch continues); review v9 BLOCKed on real-shape preconditions and the corrected v10 was ACCEPTed with conditions (reviews in `docs/r1/reviews/`, snapshot v10 `4f387beb…`). Published code `140e7d0`+`0d4e987` (retained probe/log fixtures), config binding `746b3d6` (`paper_commit=0d4e987`). A fresh TASL-7 preflight passed and the new, separately identified attempt `r1_stagea_20261102_t7d4` was launched at 06:38 UTC under the reviewed guardian holding the real `gpu0.lock`; periodic checks include progress. STOP-1/2/3/4 evidence untouched and not reused; B1/B2 not started; P.3a and B.2 remain STOP. Open author decision: template coverage/repair/new build pin for the affected candidates. See `docs/r1/reports/EXAM_TRACKX_STAGEA_STOP4_20261102.md`.

- Track X Stage A STOP 3 and restart (1 Nov): attempt `r1_stagea_20261101_t7b2` stopped at 21:13 UTC on `TimeoutError: STOP: campaign deadline` while the always-on-thinking `muse_glimmer_30b` was replaying (~58 s/request; the five always-on candidates need ~5–6 h each); every offload record before the stop was `full:true, route:log_line` with no fallback, qualification PASS, cold true-first observed — a tooling/deadline STOP, not a model/offload/cache failure. The author authorized recovery (executed and recorded: preserved server 2256704, orphan worker 2256930 and guardian 2206538 ended; lock free; evidence `~/exam-x/work/r1_stop3_shutdown_20261101T214210Z/`), the deadline fix (`root_timeout_seconds` 3600→43200, committed `7a386f8`, independently reviewed scoped ACCEPT) and a multi-night continuous run. A fresh TASL-7 preflight passed under the v8 config (route (i), FD/OFD kcmp rc 0, validated release) and the new, separately identified attempt `r1_stagea_20261101_t7c3` was launched at 21:47 UTC under the reviewed guardian holding the real `gpu0.lock`; checks are periodic and include progress. STOP-1/2/3 evidence untouched and not reused; B1/B2 not started; P.3a and B.2 remain STOP. See `docs/r1/reports/EXAM_TRACKX_STAGEA_STOP3_20261101.md`.

- Track X Stage A moved to TASL-7 (1 Nov, author decision): the host-pin delta (`APPROVED_EXAM_HOSTS={TASL-2,TASL-7}`, `cfg.host` pinned to the node, explicit `EXAM_X_ROOT`) and the launcher `--candidate` narrowing were independently reviewed (scoped ACCEPT; reviews in `docs/r1/reviews/`). TASL-7 environment: code `9b7fdd1` clean, harness `897d83c8` clean, copied pinned llama-server `b70f4882…`, frozen prompts `70872a77…`, venv/uv Python 3.13.4 with deps, HF cache, lock present. A fresh TASL-7 real-lock preflight PASSED: route (i) `offloaded 29/29`, no fallback, guardian→runner and runner→native-server `kcmp(KCMP_FILE)` rc 0, FD 4 dev 66306 ino 56251186 exact FD set, zero generation, validated-completion release, lock free after. The 22 GGUFs are being re-downloaded on TASL-7 from the pinned HF sources with per-file size+SHA-256 verification (3/22 verified at writing; ~8 h remaining); the new Stage A starts only after 22/22 verification. TASL-2 STOP evidence untouched; neither stopped batch resumed; B1/B2 not started; P.3a and B.2 remain STOP. See `docs/r1/reports/EXAM_TRACKX_STAGEA_STOP2_20261101.md` and the TASL-7 reviews.

- Track X portal shutdown (1 Nov ~10:24 UTC, author-authorized): all `dowling`-owned experiment processes on TASL-2 were ended and the STOP-2 preserved site was recovered — preserved server 3005245, guardian 2920661 (real `gpu0.lock`), two 6-day-old Track P C3 DRYRUN wrappers, Track S `trks-watch`, the old Track P `claude` session and all `dowling` tmux sessions. Verified: lock free and lock file unchanged, no `dowling` experiment process remains, evidence directories and the stopped namespace fixture untouched, no retry/resume/relabel. A root-owned unrelated GPU process and other users' services were left alone. Operational record: `/home/dowling/exam-x/work/r1_shutdown_20261101T102406Z/`; see also `docs/r1/reports/EXAM_TRACKX_STAGEA_STOP2_20261101.md` §Recovery. B1/B2 and a new Stage A attempt remain unstarted; P.3a and B.2 remain STOP.

- Track X Stage A STOP 2 (1 Nov): the route-(i) repair worked in the real run (`qwen25_coder_7b` and `qwen38_27b` offload `route: log_line`, `offloaded N/N`, no fallback), but the attempt stopped during the descriptive replay because the `/proc` executable census raised a hard STOP on an unreadable/vanished unrelated pid (`STOP: unexpected executable census error for pid 3075253`, `cache_proc.py:81`). Fixed at `0d9e4ed` (+ config binding `4722e10`): plausible `/proc`-race errnos are recorded as observation gaps (counts + errnos + samples), other errnos still STOP with the code, and the exactly-one-owned-server identity check is unchanged; scoped independent review ACCEPT (`docs/r1/reviews/TRACKX_STAGEA_STOP2_FIX_REVIEW_20261101.md`; snapshot v5 `6a1607ec…f93fe`, relevant subset 373 passed, 1 skipped). The site is preserved: guardian pid 2920661 holds the real flock, preserved native server pid 3005245 retains the same FD/OFD (kcmp rc 0), nothing signalled/cleaned/retried. The attempt is not Stage A evidence. Recovery and a new separately identified attempt require the author's authorization. Same-UID non-interference remains an assumption; host-global single-server NOT CHECKABLE. B1/B2 not started; P.3a and B.2 remain STOP. Report: `docs/r1/reports/EXAM_TRACKX_STAGEA_STOP2_20261101.md`.

- Track X Stage A STOP 1 fix (1 Nov): the author chose route A first / route B fallback; the fix pins `EXAM_SERVER_ARGS` with `-lv 4`, restoring the route (i) `load_tensors: offloaded N/N layers to GPU` evidence at the pinned llama.cpp build (620d222, v0.7.0-dev), with route (ii) unchanged as fallback and no tolerance added. Independent scoped review: ACCEPT with conditions (`docs/r1/reviews/TRACKX_STAGEA_STOP1_FIX_REVIEW_20261101.md`; snapshot v4 `SHA256SUMS` `6354e8b2…71e5be`, relevant subset 370 passed, 1 skipped). Published at code `5bf7065`, config binding `9bfabe5` on `codex/trackx-stagea-cooperative-20261031`. A fresh real-lock preflight passed with the new argv (`offloaded 29/29 layers to GPU`, FD/OFD chain kcmp rc 0, validated release, lock free). A new, separately identified Stage A attempt was then launched (`r1_stagea_20261101_b3d7f2`, manifest `35d21383…a14d3`); its result is recorded separately. The STOP-1 batch is untouched and is not Stage A evidence. Same-UID non-interference is an author assumption; host-global single-server is NOT CHECKABLE. B1/B2 not started; P.3a and B.2 remain STOP.

- Track X Stage A cooperative-lease (1 Nov): implementation repaired, independently reviewed and published at `82dfaf5`/`9418d75` on branch `codex/trackx-stagea-cooperative-20261031` (review `docs/r1/reviews/TRACKX_STAGEA_COOPERATIVE_REVIEW_20261101.md`, ACCEPT with conditions after an earlier BLOCK; `82dfaf5` = reviewed v3 bytes, then config binding `aa45dd1` and two accepted launcher deltas). A real-lock preflight with the real pinned llama-server PASSED: guardian→runner and runner→native-server `kcmp(KCMP_FILE)` rc 0, `/proc` FD dev/ino equal, no generation, validated-completion release, lock free afterwards. A new Stage A attempt then STOPped on an infrastructure/tooling defect: the `qwen25_coder_7b` replay server measured 5782 MiB against the 5784 MiB footprint pinned by its own qualification, so route (ii) reported "below the pinned footprint". The site is preserved: guardian pid 2576846 holds the real flock (`STOP.json`, `lease_retained: true`, `retry_permitted: false`), preserved native server pid 2611135 retains the same lock FD/OFD (kcmp rc 0), nothing was signalled/cleaned/retried. No Stage A table; a new attempt needs the author's resolution decision and a newly reviewed footprint-floor fix. Same-UID non-interference remains an AUTHOR ASSUMPTION; host-global single-server NOT CHECKABLE. B1/B2 not started; P.3a and B.2 remain STOP. Reports: `docs/r1/reports/EXAM_D3_COOPERATIVE_LEASEGUARD_20261101.md`, `docs/r1/reports/EXAM_TRACKX_STAGEA_STOP1_20261101.md`.

- Track X author permits cooperative same-UID assumption and observable checks for a new Stage A, subject to repaired code, independent review, published pins and valid lease/preflight; same-UID noninterference remains an assumption. Stopped fixture remains immutable; P.3a and B.2 remain STOP.

- Track X synthetic namespace fixture STOP (31 Oct): same-UID user→network setns succeeded; namespace exclusivity not proven. Preserve `/tmp/d3_namespace_fixture_20261031_d61db5e9b02188f7`, do not retry; Stage A BLOCK. See `docs/r1/reports/EXAM_D3_NAMESPACE_FIXTURE_STOP_20261031.md`. P.3a and B.2 remain STOP.

- Author allows the D3 single-resident-server proof within an isolated user+network namespace, with host-wide status disclosed NOT CHECKABLE. Independent CPU isolation verification and proof of GPU, lease and server compatibility remain required; Stage A is still BLOCK.

- 31 Oct author D2 amendment: 50 Stage A prompts frozen at 2026-10-31T11:02:44Z; SHA-256 `70872a7702a36dc13b5612abd7a8580414f01c43bb8e19179942ca70a2ed510a`; historical-source exception and incomplete Track S request coverage disclosed in `results/r1/engineering/trackx_stagea_promptset_20261031/PROVENANCE.md`. CPU-only Track S regeneration remains a post-freeze disclosure check. Stage A still requires D1/D3/config independent review; P.3a and B.2 remain STOP.

## 31 October 2026 — coordinator decisions recorded (AI-assisted; no execution)

- The author's revised D3/D5 decisions are recorded in `docs/r1/authorizations/COORDINATOR_DECISIONS_REVISED_20261031.md` and PLAN §10: explicit false for Track X throughout; Stage A cold-true descriptive condition remains gated; B1/B2 require the Track S operator's separately reviewed new harness pin. The recorded sweep-1 harness builder omitted an explicit cache setting; actual per-call HTTP bodies were not retained. Its LLM outputs are not claimed seed-replayable call by call, and recorded observations stay unchanged. The B.1 freeze covers trajectories and provenance, not absent fresh-seed soft labels.
- Track S D6 was accepted by the author; R1-TRACKS-S01-FOLLOWUP-REV records the separately dispatched operator's harness fix and full S0.1 rerun, superseding the prior pre-change author STOP. The coordinator schedules leases only. D6 itself is not an S0.1 pass or Phase 3 authorization.
- B.2 zero-tolerance environment-replay plan: the reviewed 16-case plan reconstructs worker configurations from retained structured edits and compares worker primary metrics, with no manager LLM request or comparison of LLM outputs. The actual replay driver and its eventual execution remain NOT CHECKABLE; this is not a claim of an executed replay or proof of its future behavior. See `docs/r1/reviews/C3_B2_REPLAY_LLM_SCOPE_REVIEW_20261031.md`. B.2 remains STOP.
- Track X Stage A and B1/B2 remain BLOCK: the independently reviewed engineering draft blocks their entry points while the required cold-true-first experiment, per-call cache evidence and single-server enforcement are incomplete. The separate paper-side A4 observer also needs explicit false; the independently reviewed Track S harness pin remains a B1/B2 gate. The recovered prompt file and ledger bundle were published as UNFROZEN, but prior candidate/evaluation exposure and selection independence remain NOT CHECKABLE.
- Independent exposure review found 21 of the 50 recovered context digests in 62 distinct later manager calls in historical rerun-2 continue/verify branches: all 62 have positive completion tokens and timestamps after the matching source-root call. Those branches use the historical source manager, not an identified other exam candidate. The author has explicitly allowed and requires disclosure of these historical branch calls under R1-EXAM-PROMPT-HISTORICAL-BRANCHES; other candidate exposure and selection independence remain NOT CHECKABLE. See `docs/r1/reviews/EXAM_PROMPT_EXPOSURE_REVIEW_20261031.md`; keep the set UNFROZEN.
- B.1 trajectory and source-provenance corpus frozen on the coordinator branch by `docs/r1/authorizations/C3_B1_CORPUS_FREEZE_20261031.md`, following independent published-integration review `docs/r1/reviews/C3_B1_PUBLISHED_INTEGRATION_REVIEW_20261031.md`. This does not freeze fresh-seed soft-label tables, authorize B.2, or satisfy the labels-freeze requirement for layout flattening.
- Author clarified the freeze object, historical anchor exception, and Stage A seed in PLAN §10: freeze the verified B.1 trajectory/source corpus first and actual soft-label tables separately after audit; permit and disclose the historical source manager's outputs while keeping exam-candidate and later-evaluation restrictions; use each source ledger's D26-derived historical seed at call time without modifying prompt bytes. These decisions do not themselves establish any freeze, authorize B.2, satisfy the layout gate, or authorize Stage A.
- Track X STOP 2 receiving condition: after the author's later conditional authorization, all 22 files were independently rehashed and matched; the independent verdict in `docs/r1/reviews/EXAM_STOP2_VERDICT_20261031.md` ACCEPTS receiving, source-pin comparison and reproduced fit estimates with its stated limitations. The author's conditional STOP 2 acceptance is recorded. The 32k table is an estimate, not a measured fit. This does not authorize Stage A, whose prompt-set conditions remain unresolved.
- Author decisions D1–D6 are recorded in PLAN §10 as R1-EXAM-STOP2-ACCEPT, R1-EXAM-PROMPTSET-FREEZE, R1-EXAM-CACHE, R1-P3A-OOM, R1-B2-DECOUPLE and R1-TRACKS-S01-FOLLOWUP; full conditional instructions: `docs/r1/authorizations/COORDINATOR_DECISIONS_20261031.md`.
- This entry originally recorded decisions only. STOP 2 receiving/source/fit review was subsequently completed as recorded above; prompt freeze checks, Stage A review, B.1 final integration and Track S follow-up reviews remain pending. P.3a was diagnosed and remains at STOP. B.2 is not authorized to start. The 4 November layout gate remains unchanged.
- Census: prior coordinator temporary worktrees and OPS_LOG are absent; local-only B.2 candidates `9fe7f2a` and `00d35d3` were not found in the local Git object database. TASL-2 retains two orphaned DRYRUN server wrapper processes; no GPU compute process was seen. Preserve and investigate read-only.

## 31 October 2026 — R1-CACHEPROMPT-FALSE: harness change accepted; Track S pins moved (AI-assisted; code + procedure)

- **Author ruling** `R1-CACHEPROMPT-FALSE` (31 Oct), file `docs/prompts/TRACKS_CACHEPROMPT_FIX_PROMPT_20261031.md`, recorded as a PLAN §10 row. Diagnosis accepted from D6: llama-server's prompt cache is the cause; an absent field equals `cache_prompt: true`.
- **Harness change (accepted).** Branch **`cacheprompt-20261031`** from `115df37`, head **`a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`**, pushed to `origin`; **not merged into `r1`** (`origin/r1` still `897d83c`). The `llamacpp` provider sends `cache_prompt` explicitly on every request via `extra_body` (the OpenAI SDK merges it into the JSON body), default **false** from `LLAMACPP_CACHE_PROMPT`, with `LLMConfig.cache_prompt` as the config field and rejection of a non-boolean value. Records: `llm_meta`/`llm_call` and the LangChain proposal extra carry it (omitted, never null, when the backend does not carry it or an injected stub is used), and `llm_call_failed` carries it too.
- **Track S side (accepted).** Paper pin **`d10b05b738fc0e0dba54e0e692c248bedf095482`** on `trackS-ops-20261030`: the collector's manifest `manager` block records `cache_prompt` (delegated to the harness so the two cannot drift); the S0.1 probe flattens the SDK's `extra_body` merge so it posts exactly the harness body, and its report gains a top-level `cache_prompt` with the author's label "absent (= true, llama-server default)" for pre-change records; the **A4 observer and `ManagerQuestionPrior`** `chat_client` now send and record it (review R1, BLOCKING).
- **Reviews.** Round 1 NOT ACCEPTED (R1 BLOCKING: the paper-side A4/`ManagerQuestionPrior` paths were missed; R2 MAJOR: pin wiring; R3–R9 minor). Round 2: **ACCEPTED** (`reviews/TRACKS_OPS_CACHEPROMPT_REVIEW_20261031.md`), conditional on completing the pin step before the S0.1 re-run.
- **Tests.** Harness `tests/stage2/test_r1_cache_prompt.py` **12 passed**; full harness suite `115df37` **21 failed/455 passed/2 errors/53 subtests** vs `a3fedbb` **21/467/2/53** with an **identical failure set** (true delta **+12 passed**); paper `r1/tests/test_cache_prompt.py` **5 passed**, `test_tracks_probes.py` **8 passed**; Track S suite **169 passed** on TASL-7 with the new pins. Pre-existing and not from this change: the legacy `tests/test_legacy_noop_skip.py` collection error (imports a tree absent at this commit) and two `test_r1_llamacpp_provider.py` failures on the Mac venv (openai 3.42 renames the connection exception) — both present before and after.
- **Pins.** `trks-status` now pins paper `d10b05b7…` / harness `a3fedbbd…`; both hosts' `work/Agent_paper_B` and `work/autoresearch_harness` are moved to those commits (see the pin entry below). **R4 consequence:** a pre-change langgraph manifest cannot be resumed (`manager` is in `MANIFEST_KEYS`, so the resume guard refuses); new phases use fresh output directories.
- **Open.** The full S0.1 re-run under the new pins (Step 2) and its post-run review; `k` unset; Phase 3 not started.

## 31 October 2026 — Track S D6 follow-ups F1/F2 run on both hosts: `cache_prompt` is the cause (AI-assisted; ENGINEERING_ONLY / DIAGNOSTIC)

- **Authority.** Author decision **D6 / R1-TRACKS-S01-FOLLOWUP (31 Oct)**: run both STOP-1 follow-ups on both hosts. **Not a phase**: `k` unset, Phase 3 not started, no pinned code changed. Report: `reports/TRACKS_D6_FOLLOWUP_20261031.md`.
- **Pre-use review (required before first use).** Three rounds: NOT ACCEPTED (B1 — `pgrep` over-matched Track P's Python-wrapped servers and the `trks-servers` wrapper; M1–M3), NOT ACCEPTED (B2 — the pinned build never logs request paths, so the log-based cold gate was vacuous and the post-run check always failed; N1 — the EXIT trap could kill a server it did not start), then **ACCEPTED** (`reviews/TRACKS_OPS_D6_PREUSE_REVIEW_20261031.md`). The accepted design identifies the server by the port-18101 listener tied to the single GPU compute pid, proves coldness by process age instead of log parsing, asserts (never takes) the lease, and starts/stops its own server per invocation.
- **Results — identity (200 prompts, 3 repeats):**

| configuration | servers | cache_prompt | digits_mlp | tabular_mlp |
|---|---|---|---|---|
| S0.1 (30 Oct) | 2 | absent | 0.930 | 0.870 |
| **F1 cold control** | 1 | `true` | **0.930** | **0.870** |
| **F2 plain repeat** | 1 | absent | **0.930** | **0.870** |
| 30 Oct test | 1 | `false` | 1.000 | 1.000 |
| 30 Oct control | 1 | `true` (warm) | 1.000 | 0.990 |

- **F1 ≡ F2.** Same identity, the *identical* set of differing prompt indices (14 on digits, 26 on tabular), identical evaluated-token totals (99 801 / 99 807); the bodies differ only by the `cache_prompt` key. **Omitting the field equals `cache_prompt: true`** — `true` is the server default, which is what the harness body currently gets.
- **S1 differences resolved.** Server count: **no effect** (F2, one server, reproduces S0.1's two-server numbers prompt-for-prompt). Cache warmth: **explains the 30 Oct control** (cold `true` 0.930/0.870 vs warm `true` 1.000/0.990). Contrast size: the real contrast is `false` 1.000 vs `true`/default 0.930/0.870, cold on both sides — 14 and 26 of 200 prompts, not 2.
- **Coldness**: 0/200 **complete** first-call cache hits on all four runs (`prompt_n == 1` never occurred); only the order-0 call evaluated a full prompt, the other 199 first calls still re-evaluated most of theirs (reusing ≈22–23 % of prompt tokens). Each server was freshly started by its own invocation and stopped afterwards.
- **Cost of `false`**: full prompt re-evaluation (≈640 evaluated tokens/call vs ≈166 in the cached mode) and **+6.06 %** mean latency on digits (0.6828 vs 0.6438 s) / **+6.27 %** on tabular (0.6985 vs 0.6573 s), against the cold F1 baseline. (The ≈+8 % figure would compare against the warm control, which is not the right baseline.)
- **Post-run review: ACCEPTED** (`reviews/TRACKS_OPS_D6_REVIEW_20261031.md`; 0 BLOCKING, 0 MAJOR, 6 MINOR, all corrected or recorded in the report's §7). The reviewer recomputed every number from the raw JSON, confirmed the four host originals are sha256-identical, found distinct server pids per invocation with no residual processes, confirmed the lease was asserted not taken and the listener tied to the single GPU compute pid, and found the F1≡F2 claim holds more strongly than stated (identical per-prompt contents for all 600 calls and an F2 body byte-identical to the S0.1 body).
- **Recommendation (not acted on).** Accept the diagnosis; do the harness/collector `cache_prompt: false` switch with review, new pins and a PLAN row, then a full S0.1 re-run under the new pins. `k` stays unset and Phase 3 unstarted until S0.1 passes.
- **State.** Lease free, no GPU compute process, no 18101 listener, no `trks_llm`, watcher running, markers absent; both hosts clean at the pins; raw outputs copied back with sha256 recorded in the report.

## 30 October 2026 — STOP-1 diagnostic: `cache_prompt: false` gives 100 % identity (AI-assisted; ENGINEERING_ONLY / DIAGNOSTIC)

- **Authority.** The author's ruling on STOP 1 (30 Oct): **option 2, an authorised diagnostic re-run** — not a final STOP, not a halt. **Not a phase**: no k is set and Phase 3 was not started.
- **Question.** Is llama-server's default prompt caching the cause of the S0.1 serial non-identity (0.930 digits / 0.870 tabular)? Report: `reports/TRACKS_S01_CACHEPROMPT_DIAG_20261030.md`.
- **Method.** A committed diagnostic (`r1/tracks/ops/diag/cache_prompt_diag.py`, runner `trks-diag`, launch scripts `tasl{2,7}_diag_cache.sh`) reuses the **pinned** S0.1 probe unchanged — fixed prompts, per-prompt seeds, harness `chat_payload` body, the serial interleaved schedule (`order_seed 1`, `url_index 0`, `client 0`), `identity_rate`/`latency_stats`/`cpu_census` — and adds **only** one request field, `"cache_prompt"`: `false` (test) then `true` (control), identical prompts/seeds/body/order. One server per host (`trks-servers 1`, port 18101, under the lease); raw responses kept. No pinned code changed.
- **Result — the trigger condition is met.**
  - `cache_prompt: false` identity **1.0000 (200/200) on both hosts**.
  - `cache_prompt: true` control: **1.0000** (digits) and **0.9900** (tabular; prompts 60 and 92 differ).
  - Latency cost of `false`: **+8.2 %** (0.6828 s vs 0.6309 s) on digits, **+7.7 %** (0.6985 s vs 0.6488 s) on tabular.
  - **The field is genuinely honoured**: prompt tokens *evaluated* fall from 383 781 / 387 381 (≈640 per call) with `false` to 600 / 4 865 with `true` (**mean 1.0 / 8.1 per call, max 684**) — not a null test. `usage.prompt_tokens` is identical across modes (639.635 / 645.635), so the prompts and body were unchanged.
  - Output sha256: digits `4ada2f72b17524903a3adac7865918f399cb9017f0ef8435b8ea734c98313a40`, tabular `4407899844d3e2940d5fee3d283875580de460d334c5ae8076031f6910da613f`.
- **Observation flagged, not interpreted.** The control (`cache_prompt: true`, 1.000/0.990) did **not** reproduce the original S0.1 serial failure (0.930/0.870). Three differences are visible in the data: (i) the diagnostic used **one** server whereas S0.1's serial probe ran with **two** resident (only 18101 used); (ii) the control ran on a cache **pre-warmed by the test run** — 200/200 (digits) and 197/200 (tabular) first `true`-phase calls were hits, vs 0/200 with `false`, while S0.1's serial server was cold; (iii) on **digits the control is already 1.000**, so the entire contrast is **2 of 200 tabular prompts**. The diagnostic therefore shows `false` gives 100 % identity under the single-server configuration but does **not** by itself establish prompt caching as the cause of the original failure. Two cheap follow-ups would settle it and were **not** run (outside the authorisation): a control-only run on a freshly started server (~7 min), and a single-server repeat of the plain S0.1 serial probe. Whether either is needed before the "code change + full S0.1 re-run" step is the coordinating session's call; the operator took no reading.
- **One out-of-scope write recorded (not attributable to Track S).** On TASL-2, `/home/dowling/.claude/.credentials.json` has mtime 04:23:43 PDT. It is a Claude Code credentials cache; no Track S command writes it, and the most plausible writer is the long-running interactive `claude` session in tmux `12` (predates Phase 0, untouched). The file was not opened. Flagged for the author; TASL-7 is clean.
- **Review: ACCEPTED** (`reviews/TRACKS_OPS_S01DIAG_REVIEW_20261030.md`; 0 BLOCKING, 0 MAJOR, 5 MINOR S1–S5, all fixed or recorded in the report's §7). The reviewer re-derived every number from the raw JSON and confirmed the trigger condition as a fact of this run while agreeing its evidential force for the *original* failure is limited.
- **Operator did not implement the next step.** The stated next step is a code change by the coordinating session (harness/collector switch, review, new pins, a PLAN row) and then a full S0.1 re-run. `9bb64ba` / `115df37` are unchanged.
- **State.** Servers stopped, lease released and verified free, no compute apps, watcher running, drill marker absent; results copied back; both hosts clean at the pins.

## 30 October 2026 — Runbook revision 3.3 received and adopted (AI-assisted; procedure only)

- **Revision of record is now 3.3.** Fetched from the refreshed bundle `.claude-worktrees/_snapshots/trackS_30oct.bundle` (sha256 `96dfdee13df767cb056bc8fc7cbb79aa520646105a765dde7404d8b18cb0d215`, matching `trackS_30oct.heads.txt`) and fast-forwarded the docs branch `docs/trackS-decisions-30oct` **`3ac0fbf4` → `13badb0d`**.
  - Runbook `docs/r1/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md` on `13badb0d`, sha256 **`a93fb84bd04f650d726ddb683acb0c6d0a621196d3dd5460d91be89ff4c82a53`** — byte-identical to the copy in the Mac main tree that was read at 11:24.
  - Paper pin **`9bb64ba`** and harness pin **`115df37`** are **unchanged** in the refreshed bundle.
  - The refresh also added `proposals/TRACKP_EVIDENCE_MARKER_20261030.md`, `proposals/trackp-evidence.sh` (rev 2) and `reviews/TRACKS_OPS_RUNBOOK_3_3_REVIEW_20261030.md` (no BLOCKING; re-check accepted).
- **§12 "Revision 3.2 → 3.3" read.** It confirms: the §0.6 2 % definition (`exhausted / (committed + exhausted)` over all shards), the Phase 3.0 pause drill with `$R/trks_drill.active` and the optional 3.0b Track P check, the §11.3/§11.4 drill-marker change plus the instruction to re-install and restart the watcher before Phase 3, the per-session count rules and `complete` status wording, and the Phase 0.3(c) gate for Phase 6+ on TASL-7.
- **Pre-Phase-3 handoff requirements verified as already satisfied.**
  - `r1/tracks/ops/trks-servers` and `trks-watch` are **byte-identical to the 3.3 §11.3/§11.4 templates** (sha256 `124316b5ce46d13129ff347b92356bb9904b56b025377f16917759f9d38ff22d` and `cf68843ea8dea38c22094ec86c3e864a3be7b79f3cbf144f224a1807993f8112`), installed identically on **both** hosts, `bash -n` clean.
  - `trks_watch` **restarted on both hosts**; `$R/trks_drill.active` **absent** on both, `~/r1_locks` holds only `gpu0.lock`, and there are **no** stale `STOP` files under `$R/out`.
  - The new drill gate was exercised safely earlier: with the drill marker present, `trks-servers` refused with `priority marker …/trks_drill.active` and rc=1 without starting a server.
- **Pause-drill mechanism settled by the author's 3.3 instruction:** the drill is Phase 3.0 using Track S's own `$R/trks_drill.active` on both hosts during S0.4 (required for STOP 3); 3.0b is only with the author's permission; another track's marker is **never** created by hand. The earlier request to create `trackp_evidence.active` by hand is therefore superseded and was never carried out.
- **Working rule restated:** count failed units as `exhausted / (committed + exhausted)` over all shards, read counts from the latest `sessions[-1].done` and from `roots.jsonl` / `leaves.jsonl` (never from `failed_units.jsonl`), treat a phase as finished only when a `--dry-run` of each shard shows `roots_todo = leaves_todo = 0`, and **flag — never re-read — any STOP rule** in a report.
- **Phase 1/2 are already complete** (see the entry below) and were executed under 3.2; §12/§12.1 change no Phase 1 or Phase 2 rule, so the **STOP 1 outcome stands unchanged under 3.3**. It remains open for the author: final STOP, an authorised re-run or changed server/probe setting, or halt.

## 30 October 2026 — Track S Phase 1 (S0.1) raises STOP 1; Phase 2 (S1.1) done (AI-assisted; ENGINEERING_ONLY)

- **Phase 1 / S0.1 did not reach 100 % identity in either setting**, so under the runbook's Phase 1 "Done when" rule the outcome is the **STOP** branch, not a k choice. Report: `reports/TRACKS_PHASE1_20261030.md`.
  - Serial (1 server, 18101): within-server identity **0.930** (digits_mlp, TASL-2) and **0.870** (tabular_mlp, TASL-7); latency mean 0.6446 s / 0.6582 s.
  - Concurrent (2 servers, 2 clients each): identity 18101 **1.000 / 1.000**, 18102 **0.925 / 0.855**, `cross_server_identity` **0.915 / 0.875**; latency mean 2.52 s / 2.60 s.
  - 0 transport errors in all four probes; requests carry a fixed per-prompt seed, so this is not a missing-seed artifact.
  - The rule's tiers: k = 2 needs 100 % on both URLs **and** 100 % cross-server (fails); k = 1 needs 100 % serial (fails); else STOP. **k is therefore unset and no later phase was started.**
- **Projection** (formula from §Phase 1; k undecided so both branches): digits 21.90 h (k=1) / 31.84 h (k=2); tabular 30.57 h / 36.91 h. No node crosses the 4-day fallback. Note k = 2 roughly quadruples per-call latency (0.64 → 2.52 s) and so doubles the LLM term — it buys no LLM throughput, only CPU overlap.
- **Phase 2 / S1.1** (CPU, no LLM; not a gate) completed on both hosts and on the Mac for `openml_breast_w`. All three MLP-node factor pairs have interactions whose 95 % t-interval excludes 0 (digits +0.0057/−0.0035/+0.0082; tabular +0.0026/−0.0027/+0.0049). `breast_w` `max_iter × C` is exactly 0 because `max_iter` 100 vs 200 is inert on `val_auc` (cells 00≡10, 01≡11).
- **Flags for the runbook owner (no operator reading adopted, per the author's instruction).**
  - The Phase 1 rule does not say what to do when the two concurrent servers disagree (here 18101 reached 1.000, 18102 did not) or whether a re-run is authorised before the STOP is final.
  - Runbook §0.6's "> 2 % failed units" STOP has no defined denominator; `failed_units.jsonl` counts failure events, and the TASL-7 manifest shows `done.failed: 0`, `roots: 1/1` for a still-logged attempt (carried from Phase 0).
  - `r1/tracks/probes/s1_factorial.py:139` raises `KeyError: 'ci95_t'` after writing its file when a pair yields no data (hit on the first `breast_w` attempt). No code changed.
- **Mac-side S1.1 environment.** Ran against a pinned harness clone at `115df37` in a scratch dir outside the worktree (not committed), Python 3.11, numpy 2.4.6 / scipy 1.17.1 / scikit-learn 1.9.1 / pandas (the node needs pandas for `fetch_openml(as_frame=True)`).
- **State.** Both hosts at the pins, lease free, no compute apps, watcher running; Phase 1/2 outputs copied back. Nothing after Phase 2 was started.

- **STOP 1 review: ACCEPTED** (`reviews/TRACKS_OPS_PHASE1_REVIEW_20261030.md`; 0 BLOCKING, 0 MAJOR, 6 MINOR P1–P6, all fixed or recorded in the report's §8). The reviewer independently re-derived every S0.1 value from the JSON, confirmed the copy-back sha256s, the probe provenance and order schedules, all four projection rows, all seven S1.1 contrasts, and that **no phase after Phase 2 was started**; it accepted that STOP 1 is correctly raised.
- **Runbook revised mid-execution: 3.2 → 3.3.** Phases 1–2 were executed under **3.2** (`1789c000…`); the author then revised the file at that path to **3.3** (`a93fb84b…`, 30 Oct 11:24). 3.3 changes §0.6, Phase 3 (3.0 pause drill, 3.0b Track P check), §0.3(c), §11.3/§11.4 and the session-status wording; it does **not** change the Phase 1 "Done when" rule or Phase 2, so **STOP 1 stands under both revisions**.
- **3.3 ops migration done** (required by 3.3 before Phase 3): `trks-servers` (`124316b5…`) and `trks-watch` (`cf68843e…`) updated to the 3.3 templates, reinstalled on **both** hosts (identical hashes), `bash -n` clean, `trks_watch` **restarted on both hosts** (new `watch started` lines). The new drill gate was tested safely: with `$R/trks_drill.active` present, `trks-servers 1` printed `priority marker …/trks_drill.active` and exited 1 without starting a server; the marker was removed and its absence verified.
- **Phase 0 m10 is resolved by runbook 3.3 §0.6**, which now defines the 2 % denominator as `exhausted / (committed roots + committed leaves + exhausted)` over all shards and states that reports never re-read a STOP rule. No operator reading was adopted.
- **Pause-drill mechanism needs an author ruling.** The earlier instruction for the Phase 3 drill was to create `~/r1_locks/trackp_evidence.active` by hand on TASL-7. Revision 3.3 now prescribes **Track S's own `$R/trks_drill.active`** for the 3.0 drill and states **"Never create another track's marker (`trackx_…`, `trackp_…`) by hand"**; creating the Track P marker is permitted only in the optional 3.0b check, through Track P's marker helper and with the author's permission. The operator has **not** created any marker. The two instructions conflict and the author's ruling is needed before the drill.
## 30 October 2026 — Track S Phase 0 complete on both hosts; STOP 0 **passed** (AI-assisted; ENGINEERING_ONLY)

- **Operator branch.** `trackS-ops-20261030` from paper `9bb64ba` (worktree `.claude-worktrees/trackS-ops-20261030`). Bundle `trackS_30oct.bundle` verified against `trackS_30oct.heads.txt`; `docs/trackS-decisions-30oct` fast-forwarded `cdb3cdc3` → `3ac0fbf4`. The main tree (`exam-x-20261026`, uncommitted `docs/r1/*` → `docs/*`) was not touched.
- **Hosts.** TASL-2 (`portal_zhixu`) and TASL-7 (`tasl7`) at paper `9bb64ba` and harness `115df37`, detached; `uv` + Python 3.11 venvs frozen identically (`pip_freeze.txt` byte-identical, 65 packages); llama.cpp **v0.7.0** at `620d2225…` built for sm_89 with CUDA 12.2 on both; pinned GGUF sha256 `509287f7…4d3c` matched on both.
- **Tests.** 168 passed (`r1/tests/test_tracks_*.py`) and 14 passed (harness `test_r1_track_s_arms.py`) on **both** hosts. Invocation deviation recorded: use `python -m pytest` (repo Makefile convention), not the `pytest` console script, which cannot import `r1`.
- **Ops scripts.** `trks`, `trks-run`, `trks-servers`, `trks-watch`, `trks-status` installed per host from `r1/tracks/ops/` (§11); all pin-injection, `--phase`/`--phase=` parsing and flag-refusal checks pass; watcher running.
- **Smoke (ENGINEERING_ONLY).** Full offload `29/29 layers`; digits_mlp one root `ok` (102 s); tabular_mlp attempt 1 failed one unit and the same command re-run as `trks_smoke_retry` completed one root `ok` (329 s). `t_run` = 0.9091 s (digits, n=77) / 1.9135 s (tabular, n=155, successful campaign only). GPU lease released and verified.
- **Ops hardening.** `trks-status` additionally verifies the three pinned HEADs (paper/harness/llama.cpp), reports tracked-file modifications, and finds manifests recursively so it works with both the flat Phase 0 `out/<phase>` layout and §0.1's `out/<node>/<phase>` layout; reinstalled on both hosts (sha256 `a217f6b8…`). The watcher stayed alive across an ~8.5 h operator-SSH outage (Tailscale was stopped after the Mac changed networks; `tailscale up` restored it — the hosts and tmux sessions were unaffected, which is why campaigns run on the hosts).
- **Report.** `reports/TRACKS_HOST_FACTS_20261030.md`. Branch pushed to both hosts' bare repositories **and** GitHub (where credentials exist).
- **Review round 1** (`reviews/TRACKS_OPS_PHASE0_REVIEW_20261030.md`): **NOT ACCEPTED** (1 BLOCKING, 1 MAJOR, 13 MINOR). Every finding was fixed or answered in the report's §8.
- **Review round 2: ACCEPTED — STOP 0 passed.** The reviewer's final read was 12 FIXED, 2 SATISFACTORILY ANSWERED (B1 0.3(c) author arrangement, M1 author decision), 1 STILL OPEN (m10): the m10 disposition row had claimed the §0.6 ">2 % failed units" denominator was stated in the report body when it was not. The sentence is now actually in §3 0.10 — the STOP is read with the denominator *permanently failed (`exhausted`) units over planned units*, not lines in `failed_units.jsonl` — so the counts are now **13 FIXED, 2 SATISFACTORILY ANSWERED, 0 STILL OPEN**. New MINOR residuals recorded in report §8: n1 the S0.4 sample is a coarse screen (20 units; rule of three 3/20 = 15 %, exact one-sided 95 % limit ≈ 13.9 %; one failure in 20 already exceeds the 2 % STOP), n2 the smoke used the flat `out/smoke` layout (Phase 3 onward uses `out/<node>/<phase>`; `trks-status` scans both), n3 the 0.3(c) arrangement is operator-relayed with **no Track P-side artifact** and the watcher pause path is unexercised (author action: have Track P record its side), n4 documentation residuals (fixed). Round 2 was taken by a second independent reviewer because the round-1 session was not resumable in this harness — a recorded deviation from "the same reviewer".
- **Phase 1 not started** in this session; it needs the GPU servers brought up (k = 2) and is the next step now that STOP 0 has passed.
- **Author decisions (30 Oct).**
  - **F5.1** a stale manager proposal (`old` no longer current) makes A2-U `forecast → replay → apply_edit` raise `ReplayError`; the unit is logged in `failed_units.jsonl` and retried (the harness tolerates the same event via its `PROPOSAL_PRECONDITION_FAILED` guard). Stochastic and recovered on retry, but §0.6 makes > 2 % failed units a STOP, so it must be measured before S0.7/S3e. **Decision: keep the pins, accept retries, and quantify the stale-proposal rate on S0.4**; report the rate at STOP 3 and before any EVIDENCE phase. The pinned code was **not** changed.
  - **0.3(c) resolved:** the author confirms the `~/r1_locks/trackp_evidence.active` arrangement is in place and Track P handles it; the marker is correctly absent between Track P evidence runs.
  - **TASL-2 residents expected:** the two idle, GPU-free Track P dry-run `llama-server` processes and the `r1p_agent` / `12` tmux sessions are expected and were left untouched per §0.4 ownership.
- **Timestamps.** TASL-2 is not NTP-synchronised; both hosts run PDT (7 h behind UTC). Report stamps are UTC; raw log excerpts keep the hosts' local PDT stamps.

## 30 October 2026 — Track S adopted; settings, framing and wording recorded (author; AI-assisted, documents only)

- Author decisions recorded (PLAN §10): **R1-TRACKS-ADOPT**, **R1-TRACKS-S02**, **R1-TRACKS-FRAMING**, **R1-WORDING-30OCT** and **R1-REPO-ACCESS**. Together with R1-TRACKS-HOST/-2 (29 Oct; previously uncommitted in the `c3-pool-28oct` worktree, committed here).
- Track S documents committed under `docs/r1/`:
  - the runbook, rev 7.4;
  - the decisions draft;
  - the seven design reviews and the code acceptance review;
  - the review prompts;
  - the operator runbook `prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md`, revision 3.1, with its independent review `reviews/TRACKS_OPERATOR_RUNBOOK_REVIEW_20261030.md` (revision 3 **accepted**; its four minors are fixed in 3.1). Next: the author starts the operator agent at Phase 0 and supplies the Phase 0.3 items;
  - the authorization draft `proposals/AUTH_DRAFT_trackS_20261030.md`.
- Wording corrections: TRACK_P §6.5 step 4; a C3_DESIGN note on A2.
- Track S code: paper branch `trackS-20261029` at **`9bb64ba`** after the ops-readiness round (168 Track S tests pass; the end-to-end synthetic test returns A on P2+ and "no gain found" on N0) and harness branch `trackS-20261029` (`115df37`, on GitHub). No host run has started.
- Branch `docs/trackS-decisions-30oct` (from `docs/c3-pool-28oct` `cefa389`), delivered as a bundle; for the coordinator. **Note:** the Mac's main working tree (`exam-x-20261026`) currently shows an uncommitted move of `docs/r1/*` to `docs/*`. It was not made by this session and was left untouched.

## 29 October 2026 — Track S host decision recorded (AI-assisted; documents only)

- Author decision recorded (PLAN §10): **R1-TRACKS-HOST**. If Track S runs, its LLM-backed steps run on zhixu portal after Track X releases the card or in Track X gaps, under the portal lease. deepthought keeps sweep 1 and B.2 only.
- Track S runbook revision 2 (`proposals/TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md`, untracked on the `exam-x-20261026` checkout) §2 and §9 are updated to match. Track S itself remains a proposal: not adopted, not authorized, and no run started.
- Later the same day: **R1-TRACKS-HOST-2**. Track S is split over two 4090 hosts: `digits_mlp` on TASL-2 (zhixu portal) and `tabular_mlp` on TASL-7, with Track X and Track P priority kept. The runbook (revision 3) §1, §2, §4 and §9 are updated to match.
- Edited in this worktree's files only; not committed (the chat session cannot run git writes in this folder). For the coordinator.

## 28 October 2026 — Mac-local preparation: NI masking test, TabPFN pin and A1-ctx proposals, manuscript sections (AI-assisted; ENGINEERING_ONLY / documents)

- New code (fixture-only tests): `r1/c3/ni_masking.py`, the results-masking test for (NI) of `proposals/T4_PROP10_REVISION_20261028.md` §6. It cross-fits A3 with and without the six direct outcome features. RPS is scored against the **evaluation-half** soft label (audit seeds 7006–7010). Fold modes: campaign, pair-grouped (with fold diagnostics) and LONO. The output flag is `results_add_predictive_value`, not evidence for or against NI by itself. Tests: `r1/tests/test_c3_ni_masking.py`, 15 cases. No table, label or evaluation seed was used.
- Proposals (author decides): `proposals/TABPFN_PIN_PROPOSAL_20261028.md` (`tabpfn==9.2.0`; v3.5 + v2 recommended; licence, gating and attribution steps for the author) and `proposals/A1_CTX_IMPLEMENTATION_NOTE_20261028.md` (A1-ctx model; shared `NO_RULE_ARMS` for `offline_eval.py:362` **and** `prior_model.py:120`; prompt-ablation options (a)/(b)).
- Manuscript sections problem, theory and setup, drafted on branch `docs/manuscript-28oct` (from `codex/r1-manuscript-28oct` `fb68ff3`). Theory is marked as pending the author's proof check; results remain `\TBD{}`.
- Independent review with re-review and final check: `reviews/MAC_LOCAL_DELIVERABLES_REVIEW_20261028.md`. All four deliverables ACCEPTED.
- Findings for the plan, from the review: the rule layer is chosen by arm name in two places; edit-hash grouping, cited in TECH_ROUTE, is not implemented in `offline_eval` folds; `offline_eval` scores C3 RPS/log scores against label-half soft labels; climate's descriptors are still PROVISIONAL in `features.py`; `serialize.POOL` still lists the Laya and StartLux tokenizers.
- Branches `docs/c3prep-28oct` (from `main` `a1ba5cf`) and `docs/manuscript-28oct`, both local; not pushed or merged — for the coordinator.

## 28 October 2026 — C3 decision-model pool narrowed; TabPFN added (AI-assisted; documents only)

- Author decisions recorded (PLAN §10): **R1-C3-POOL** (candidates Kev-0.8B and Kev-4B; StartLux 0.8B/2B/4B and Laya removed; Qwen3.5-0.8B/4B-Base kept as control), **R1-C3-POOL-EXAM** (P.3a on those four bases, a subset of the 27 Oct authorization; the architecture-class finalist rule no longer selects), **R1-TABPFN** (TabPFN rung: in-context, fine-tuned, R-A0, R-A1).
- RUNBOOK Track P and the Track P spec: one pointer line each to these rows. No code, registry, rule file or authorization changed; no run started or stopped.
- **Open:** TabPFN version (author); the Track P operator must apply R1-C3-POOL-EXAM before the P.3a DRYRUN/EVIDENCE launch.
- Also recorded: **R1-RB-GRPO** (R-B update rule: leave-one-out advantage without std normalisation, PPO clip ε = 0.2 with 2 epochs per batch, KL to the SFT warm-up checkpoint, β ∈ {0, 0.02}); spec §6.4 and the R-A1 estimator check amended. Aligning the R-A1 check code is for the Track P agent.
- Also recorded: **R1-CONTEXT-BASELINE** (context-only rung A1-ctx from node descriptors, fitted across training nodes per LONO fold; context-aware vs context-oblivious prompt ablation on Kev-0.8B at Stage S). No new labels.
- Also recorded: **R1-T4-DI-FIX** (combined route for T4 Proposition 10: one-step theorem; global optimality only under no-feedback and no-information; new Proposition 10(c)). Draft and independent review under `proposals/` and `reviews/`; theory files unchanged pending the author's proof check.
- Branch `docs/c3-pool-28oct` (local, from `main` `30303d8`); not pushed or merged — for the coordinator.

## 27 October 2026 — latest main update merged into local branch (AI-assisted)

- Incorporated the later `origin/main` commit `b5a5d38` after the initial merge. The [independent review](reviews/LOCAL_MAIN_UPDATE_REVIEW_20261027.md) accepts the status conflict resolution and verifies the incoming documents.

## 27 October 2026 — sweep launch stopped; provenance and local scratch repair (AI-assisted)

The author-approved launch batch `r1_c3_sweep_ENGINEERING_ONLY_20261027_LkGdPo` stopped during engineering liveness, before B.1, after discovering that native manifests did not contain the authorized paper launch pin and work scratch used Ceph. The author chose “停止后修复原生 manifest，再重新准备（推荐）”; the owned runner, liveness and model service were stopped and the partial batch is retained. The repair records initial launch provenance in the native liveness and sweep manifests, moves temporary work to verified local disk, and durably archives referenced work; see [coordinator review](reviews/DT_SWEEP_PROVENANCE_SCRATCH_REVIEW_20261027.md) and [independent review](reviews/DT_SWEEP_PROVENANCE_SCRATCH_INDEPENDENT_20261027.md). Linux scoped tests: 79 passed, 1 skipped; fake retry/permanent/interrupt/watchdog all passed under the author-approved R1-DT-TESTGATE longer-timeout exception. The 75-second timeout and earlier diagnostic failures remain recorded. This is engineering validation, not sweep evidence. A fresh batch must pass the unchanged full prepare gate and launch checks; the stopped batch must not be resumed.

## 27 October 2026 — Deepthought preparation test failures reviewed (AI-assisted)

Author-approved fresh preparation at paper `3c4651d` and harness `6adf385` stopped with `prepare.json` false: 553 paper tests passed, 38 skipped and 2 failed. The stopped batch `r1_c3_sweep_ENGINEERING_ONLY_20261027_18wc1y` and logs remain unchanged. Independent review accepted two test-only fixes; the author instructed “允许提交并重新准备”. Neither changes the experiment configuration, golden output or prepare acceptance gate. See [review](reviews/DT_SWEEP_PREP_TEST_FIXES_20261027.md). A new preparation is required; no sweep has started.

## 27 October 2026 — repository layout decision recorded (AI-assisted; documents only)

- Author decision recorded (PLAN §10): **R1-LAYOUT-FLATTEN**. R1 is confirmed as the only live route; the `r1` directory layer (`docs/r1/`, `results/r1/`, `papers/r1/`, the `r1/` package) is removed in one reviewed batch after the labels freeze (3 Nov), with all agents at a STOP. Harness `r1` branch, pin and `R1-*` IDs unchanged.
- RUNBOOK §5: one scheduling line added. No file moved; all current paths remain valid until the batch.
- Branch `docs/layout-flatten-27oct` (local, from `main` `3c4651d`); not pushed or merged — for the coordinator.

## 27 October 2026 — Deepthought preparation STOP and author-approved dependency fix (AI-assisted)

Two pre-launch STOPs are preserved: the first preparation session name collided by tmux prefix with the launcher's duplicate-session check; on explicit author permission the second preparation created batch `r1_c3_sweep_ENGINEERING_ONLY_20261027_QCMMIn`, but its `prepare.json` is `ok: false` because the harness-only venv has no torch and `test_trackp_e0_v2.py` imports it at collection. No evidence was launched and that batch is not modified. The author approved the independently reviewed optional dependency guard and a fresh preparation attempt. On hosts without torch the entire Track P test module is skipped, not passed; with dependencies present 24 tests are collected and two CPU-only checks passed on Mac. The three pilot regression tests identified in the author clarification are unchanged. Details: [review](reviews/DT_SWEEP_PREP_TORCH_GUARD_20261027.md).

## 27 October 2026 — D28 engineering readiness independently accepted (AI-assisted; STOP)

Independent review accepted the D28 repair and noise binding at paper branch `3892354` and harness `6adf3859de66c4814fcf376eed59880fbd8eeaf7`; see [independent review](reviews/DT_D28_REPAIR_REVIEW_20261027.md) and [merge review](reviews/DT_SWEEP1_MERGE_REVIEW_20261027.md). Mac CPU merge checks retain the pre-existing soft-label v1 hash failure; historical provenance and cross-platform floating-point limits remain recorded. Sweep 1 and B.2 remain unstarted and require explicit author authorization and launch-time pin verification.

## 27 October 2026 — repair noise-source binding prepared (AI-assisted; ENGINEERING_ONLY)

The D28 review found the sweep collector and later C3 build defaulted to the old common noise table, which lacks climate and predates the repaired configurations. An eight-node composite is pinned and linked through the runner, collector manifests, sweep index, table and offline evaluation; historical defaults remain. Composite SHA256 `3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310`; final deepthought config SHA256 `2fa891f43bf26e6ed2ac6c794696428a43568a69a850d6029e3bc8233616974b`. [Binding report](reports/DT_D28_NOISE_BINDING_20261027.md) records CPU tests and the legacy pilot fixture limitation. Independent re-review is pending; readiness STOP remains and no sweep or B.2 has started.

## 27 October 2026 — repair D28 complete; sweep-1 readiness STOP (AI-assisted; ENGINEERING_ONLY)

Three D21-qualified repaired nodes and the climate reserve passed D28, with full GPU offload before and after. Blood_transfusion failed D21 and is replaced by climate under R1-D28-REPAIR. Proposed eight-node config and harness pin are prepared on this branch; [readiness report](reports/DT_SWEEP1_READINESS_20261027.md), D28 raw records and archived temporary provenance are retained. Independent review is pending. **STOP:** sweep 1 and B.2 remain unstarted and require the author's authorization and a matching final pin set.

## 27 October 2026 — D28 reserve climate D21 passes (AI-assisted; PILOT)

The separate climate status check at harness `6adf385` completed 552 unique records with no failures or missing metrics; climate qualifies under D21 (3 material edits, mean P(wrong) 0.2907157594). Report: [DT_D28_CLIMATE_D21_20261027.md](reports/DT_D28_CLIMATE_D21_20261027.md). Climate remains a reserve until its own D28 passes; the original failed and completed climate attempts remain unchanged.

## 27 October 2026 — D28 repair D21 re-measurement (AI-assisted; PILOT)

Four repaired nodes measured at harness `6adf385` after predeclaration `b2f8b74`: 2,208 unique records, zero failures or missing metrics, 30 seeds per condition. Breast_w, sonar and wdbc qualify under the unchanged D21 rule; blood_transfusion does not (mean P(wrong) 0.07715375 < 0.10). Report: [DT_D28_D21_REPAIR_20261027.md](reports/DT_D28_D21_REPAIR_20261027.md). Preserve this finding; no re-run or threshold adjustment. The reserve climate D21 status check is running separately under the same harness pin; D28 and sweep 1 have not started.

## 27 October 2026 — coordination handed to a local operator agent (AI-assisted; documents only)

- `docs/r1/prompts/OPERATOR_HANDOVER_20261027.md`: state of the four agents, ground rules, immediate queue, monitoring, merge protocol, upcoming gates and open author decisions, for a Mac agent with SSH access that takes over coordination and monitoring.
- `docs/r1/prompts/DEEPTHOUGHT_NODE_REPAIR_PROMPT.md`: instruction for the deepthought agent under R1-D28-REPAIR.
- `docs/r1/proposals/AUTH_DRAFT_trackp_p3a_20261027.md`: draft P.3a authorization for the author (authorizes nothing until committed under `docs/r1/authorizations/`).

## 27 October 2026 — coordinator main merged into local branch (AI-assisted)

- Merged `origin/main` at `0a3f5c7` (includes coordinator commit `c5ea037`) after pushing the pilot clarification at `960a53c`. The [independent review](reviews/LOCAL_MAIN_MERGE_REVIEW_20261027.md) accepts the conflict resolutions, which retain incoming Track P and D28 decisions alongside the newer pilot clarification. The post-merge CPU regression rerun again reports 30 passed and one v1 byte-identity failure; see the [test report](reports/LOCAL_PILOT_REGRESSION_CLARIFICATION_20261027.md).

## 27 October 2026 — pilot regression clarification and failure (author; AI-assisted)

- The author clarified that the 19 Oct pilot restriction concerns Track P training data and evaluation evidence; the named existing engineering regression tests may use it as a read-only fixture. Unconditional skip markers were removed. CPU test run: 30 passed and the soft-label v1 byte-identity test failed; see the [report](reports/LOCAL_PILOT_REGRESSION_CLARIFICATION_20261027.md). The [independent review](reviews/LOCAL_PILOT_REGRESSION_CLARIFICATION_REVIEW_20261027.md) rejects overall acceptance while this regression fails. No threshold or reference was changed.

## 27 October 2026 — Track P and deepthought branches merged; sweep-1 node repair decided (AI-assisted)

- Coordinating session merged `trackp-20261026` (`a3cc81f`: author's 26 Oct decisions, E0 v2 and two-stage driver DRYRUNs, rule v2 `p3_rule_v2.yaml`, TASL-7 migration with host equivalence passed; all independently reviewed and accepted) and `dt-sweep1-20261026` (`cdeac81`: Phase 2 recheck, A.6 config, A.8 host smoke with the real server, A.7 D28 liveness 4 of 8 with read-only diagnosis; `serve.py` validates pins before importing torch; Track P test modules skip without torch). Conflicts in PLAN, STATUS and the Track P spec resolved by keeping both sides.
- Author decision R1-D28-REPAIR (PLAN §10): repair the four no-headroom nodes by a pre-declared start-configuration rule, re-measure their D21 noise floor, re-run D28, then one sweep-1 batch on all eight nodes; reserve `openml_climate` only if a repaired node still fails.

## 27 October 2026 — accepted local (Mac) work merged into `main` by the coordinating session (AI-assisted)

- Path-selective commit from `local-20261026` at `fa87d79` (158 paths): PLAN §10 rows of 26–27 Oct, route/spec/theory annotations, `TECH_ROUTE.md`, proposals, reports, reviews, theory audit and author packets, sweep-1 resume-stamp note, Track G runbook, pre-declaration template and tool (L4.4/L4.5). Review: `docs/r1/reviews/LOCAL_MERGE_REVIEW_20261027.md`.
- Not taken: the L6 manuscript and its Makefile/pyproject targets, the L4.3 renderer, and new skip markers on three existing regression tests (H.1/H.8 acceptance tests, soft-label v1 reproduction); clarification proposed to the author.

## 27 October 2026 — H.8 deferred; Track G scope clarified (author; AI-assisted)

- PLAN now records H.8 deferral until A7/C4 needs an environment, direct Track P label-table training, and the 19 Oct pilot as read-only test fixture only, never training or evaluation evidence. The rejected amendment is preserved at `origin/local-h8-20261027` (`f666a38`); the accepted bin-action environment and controller are restored. The unaccepted sidecar prompt follow-up is also deferred.
- Track G is autoresearch plus MLGym only if a container is available by 10 Nov; 1GC is removed from G.1. The [independent review](reviews/LOCAL_DEFER_H8_G1_REVIEW_20261027.md) accepts these scoped changes; a synthetic CPU environment fixture passed and five pilot-training test cases were skipped. This is not an exhaustive audit of all pilot references.

## 27 October 2026 — L4.3 fixture boundary reviewed (AI-assisted)

- The renderer now reads the 22 Oct C1 source only and writes a separate C1 directory; the 19 Oct pilot is a read-only test fixture only, never training data or evaluation evidence. Historical outputs are preserved. The [scoped review](reviews/LOCAL_L4_3_FIXTURE_SCOPE_REVIEW_20261027.md) accepts the boundary; five fixture tests passed independently and one committed-source render was deselected. Full L4.3 remains unaccepted, including provenance limitations.

## 27 October 2026 — citation follow-up independently reviewed (AI-assisted)

- The NeurIPS publication distinguishes the two authors named Yang Yue. The Jev essay signature and footer support, but do not directly establish, its full-name byline, which remains marked unverified. The [scoped review](reviews/LOCAL_L6_CITATION_FOLLOWUP_REVIEW_20261027.md) accepts these annotations. L6 remains unaccepted pending the author proof check and remaining citation gaps.

## 27 October 2026 — H.8 split mapping clarified (author)

- Author confirmed `train` and `val` use `z_train`; `test` uses `z_eval` (PLAN R1-H8-SPLIT-MAPPING). A split assignment for the older pilot is test-only. This supersedes the pending-mapping note in the prior entry, without accepting the rejected implementation or authorizing another attempt.

## 27 October 2026 — pilot noise transformation independently reviewed (AI-assisted)

- The partial L4.3 renderer at `5143b24` recomputes the displayed noise fields from captured historical pilot data and checks them against the stored summary. Independent [review](reviews/LOCAL_PILOT_NOISE_REVIEW_20261027.md) accepts this limited engineering transformation: all 30 displayed sigma values match, with 12 focused tests passing.
- This is not acceptance of the pilot as evidence or of the complete L4.3 pipeline. The source-hash limitation applies to both the renderer and its imported summarizer; working-tree committedness is not enforced at runtime.

## 27 October 2026 — pilot safeguard correction re-reviewed (AI-assisted)

- Independent [re-review](reviews/LOCAL_PILOT_GUARD_REVIEW_20261027.md) confirms the expected file sets, input-byte hashes and cooperative locking in `8a1ecf5`; 11 focused tests passed. The renderer hash is read near the end and cannot prove which source bytes Python loaded if it changed during execution. Full L4.3 remains unaccepted.

## 27 October 2026 — pilot metadata guard independently reviewed (AI-assisted)

- The partial L4.3 renderer input-status guard (`8b8b623`) is independently accepted for its limited metadata check ([review](reviews/LOCAL_PILOT_GUARD_REVIEW_20261027.md)); focused source and fixture checks: 7 passed. Full L4.3 remains unaccepted.
- On a failed guard, previous output files remain; their existence is not evidence of a successful current render. The existing provenance lacks a renderer revision. Both limits remain open and no pilot output is an accepted scientific result.

## 27 October 2026 — sweep-1 stamp note independently reviewed (AI-assisted)

- The one-paragraph [authorization note](reports/SWEEP1_RESUME_STAMP_NOTE_20261027.md) is independently accepted for scoped source accuracy ([review](reviews/LOCAL_SWEEP1_STAMP_NOTE_REVIEW_20261027.md)): interrupted sweep roots are rerun whole and C3 features do not read the stamp. The note preserves the separate live E2 verification caveat and does not assert a particular historical execution state. The author’s sweep-1 non-applicability ruling controls.

## 27 October 2026 — scoped citation checks independently reviewed (AI-assisted)

- The bibliography now records a documented DACBench publisher spelling conflict, with the spelling supported by the paper and project citation; a Bechhofer single-sample paper is added only as an explicitly unverified candidate for the underspecified reading-list entry. The [scoped review](reviews/LOCAL_CITATION_GAPS_REVIEW_20261027.md) accepts these draft corrections, not the bibliography as a whole.
- L6 remains unaccepted: author proof check, direct metadata/identity verification where marked and other citation gaps remain.

## 27 October 2026 — autoresearch fake CLI smoke independently reviewed (AI-assisted)

- Harness branch `r1-local-20261027-autoresearch` commit `d63cb91` contains an explicitly fake three-trial CLI smoke using the local worker and synthetic metrics. The [independent review](reviews/LOCAL_AUTORESEARCH_STUB_REVIEW_20261027.md) accepts this fixture-only subitem; one focused fixture passed independently. No real node training or scientific run is inferred.
- L4.1 overall remains unaccepted: the authoritative 1GC task source and its adapters are unavailable, other integration criteria and post-merge full-environment checks remain open.

## 27 October 2026 — final authorized H.8 attempt independently rejected (AI-assisted)

- Author authorized one further table-utility attempt; `d9a4338` computes through `labels.action_target` using a training-only A1 and table split. Fresh independent [review](reviews/LOCAL_L4_2_FINAL_REVIEW_20261027.md) **rejects** it: a mixed-split environment exposes test episodes during training, rule-equipped no-ops can execute, and a failed reset can leave stale state. Fifteen scoped fixture tests passed but did not catch these counterexamples. The train/val/test label-block mapping remains an assumption pending author confirmation.
- No further H.8 code attempt is authorized by the current one-more-attempt ruling. Preserve the branch for coordinator review; the earlier H.8 reviewer’s pilot-table fixture-scope incident remains in its review. No `r1/c3/train/` edits were made.

## 27 October 2026 — L4.5 harness audit independently accepted (AI-assisted)

- The [governance audit](proposals/HARNESS_GOVERNANCE_20261027.md) and its two added legacy-metric fixtures (`4e25521`) are accepted under the author's amended restricted Mac criterion: [review](reviews/LOCAL_L4_5_RULING_REVIEW_20261027.md); independent fixture run 2 passed. The known resume-stamp defect has a separate accepted `r1-local-20261027` repair gated until after sweep 1 and B.2.
- The restricted comparisons predate the new test file and intervening pilot-figure changes; no fresh whole-selection claim is made. Full-environment suite comparison remains after merge. Generic non-AUC metric behavior remains an audit question, not a proven deployed defect.

## 27 October 2026 — resume stamp repair independently reviewed (AI-assisted)

- Harness branch `r1-local-20261027` commit `7567215` is pushed and independently accepted for the scoped engineering fix ([review](reviews/LOCAL_RESUME_STAMP_FIX_REVIEW_20261027.md)). Fixture tests cover resumed E1 evaluated and skip plus E2 verify rescue/veto and live/resumed behavior; 3 passed. The fix recomputes the final count after a verify decision can change, while preserving the pre-verify snapshot view.
- The [sweep-1 note](reports/SWEEP1_RESUME_STAMP_NOTE_20261027.md) records the author's non-applicability ruling and source limits. `r1` remains pinned at `897d83c`; the coordinator may merge this as a new pin only after sweep 1 and B.2, before C.3 (R1-RESUME-STAMP). No historical impact or evidence readiness is inferred.

## 27 October 2026 01:30 — author rulings and L4.4 acceptance (AI-assisted)

- PLAN §10 records the authorized resume-stamp repair on `r1-local-*`, sweep-1 non-applicability note and post-sweep/B.2 merge timing; restricted comparison is the accepted Mac criterion for L4.4/L4.5 with full-suite comparison after merge; one more H.8 table-utility attempt is authorized, including read-only committed-table fixtures.
- Independent [L4.4 ruling review](reviews/LOCAL_L4_4_RULING_REVIEW_20261027.md) **accepts** the pre-declaration scaffold under the amended Mac criterion: all 581 common selected paper outcomes match and 13 new predeclaration cases pass; harness and tiny-model restricted comparisons match. The full environment suite remains a post-merge check. Implementation `9e4ca52`, comparison evidence `1c09b77`.
- The [L4.5 ruling review](reviews/LOCAL_L4_5_RULING_REVIEW_20261027.md) accepts the restricted comparisons but rejects item completion because the separate tests-added-and-passing requirement remains unestablished. H.8 and harness repair are in progress.

## 27 October 2026 — pre-scaffold restricted comparison independently reviewed (AI-assisted)

- The [pre-scaffold comparison](reports/LOCAL_BASELINE_CLARIFIED_20261027.md) was independently checked ([baseline review](reviews/LOCAL_BASELINE_CLARIFIED_REVIEW_20261027.md), [L4.4 review](reviews/LOCAL_L4_4_REVIEW_20261027.md); evidence `1c09b77`). Of the selected paper tests, 581 IDs common to `8ba81b6` and `d4c76d2` have matching outcomes; the 13 newly added predeclaration cases pass. The separate tiny-model selection matches across 48 IDs. Matching IDs do not imply identical test code.
- Both reviews retain the exclusions, skips and failures; this is restricted engineering documentation, not a full-suite pass or L4.4 acceptance.

## 27 October 2026 — H.8 implementation review remains open (AI-assisted; fixture tests)

- Author-authorized H.8 and sidecar edits were implemented and reviewed in three attempts (`089ed87`, `395aeff`, `d4c76d2`). The [independent review](reviews/LOCAL_L4_2_IMPLEMENTATION_REVIEW_20261027.md) remains **NOT ACCEPTED**: utility reference, price and split are caller assertions rather than a verified producer. The final scoped fixture check reports 27 passed; the reviewer confirms the `delta_hat` leak was removed.
- The first review also included a cached pilot-table test outside the H.8 fixture-only instruction; that separate incident is retained in the review. No model inference, weight download, GPU/MPS or remote operation was reported. Under the three-attempt limit the item is handed to the coordinator rather than silently accepted; Track P picks up only after an accepted coordinator merge to main.

## 27 October 2026 — clarified CPU baseline independently reviewed (AI-assisted; restricted)

- The corrected-environment [baseline](reports/LOCAL_BASELINE_CLARIFIED_20261027.md) and exact-ID harness comparison were accepted as restricted engineering documentation by [review](reviews/LOCAL_BASELINE_CLARIFIED_REVIEW_20261027.md): harness before/after 443 passed, 19 failed, one collection error, 55 subtests passed, same outcomes; paper baseline and separate tiny-model checks retain their recorded failures and skips.
- Eight dry-run test IDs and two individual cases were excluded from the paper selections; the original unrestricted full-suite criterion and L4.4/L4.5 acceptance remain unestablished. No failure was converted to an accepted exception and no scientific evidence is inferred.

## 27 October 2026 — L7 decision consistency pass independently accepted (AI-assisted)

- The [post-decision scan](reports/LOCAL_POST_DECISION_SCAN_20261027.md), updated [technical route](TECH_ROUTE.md), Track P specification, manuscript outline and handoff were independently reviewed after corrections: [review](reviews/LOCAL_L7_REVIEW_20261027.md), initial alignment `4f30ed2`, review corrections `fc439ad`. DAC framing, bin/RPS decisions, scope, H.8, C4 and Track G rulings are recorded in PLAN §10 and reconciled in the reviewed files.
- This is acceptance of the consistency pass, not acceptance of the separately unfinished L4.2 or L6 work, author proof checking, an evidence run or a merge.

## 27 October 2026 — theory proposal and pinned resume trace reviewed (AI-assisted)

- The [resume trace](reports/LOCAL_RESUME_STAMP_TRACE_20261027.md) is independently confirmed ([review](reviews/LOCAL_RESUME_STAMP_REVIEW_20261027.md), `a4bed47`): at `897d83c`, resumed E1/skip records omit cumulative `repeated_bad_count` stamping when the true count is positive. Historical impact and E2 verify semantics are not established; the sweep pin is unchanged.
- The [theory-correction proposal](proposals/THEORY_CORRECTIONS_20261027.md) was revised after review and accepted only as an aid for author proof check ([review](reviews/LOCAL_THEORY_CORRECTIONS_REVIEW_20261027.md), `183ebe9` / `395aeff`). No theory-file claim was changed, and no proof is marked author checked.

## 27 October 2026 — author rulings and Mac test-scope clarification (AI-assisted)

- Author rulings recorded in PLAN §10: noise-aware DAC headline; canonical bins and RPS; limited hard-label ablations; R-A0/R-A2 and C4 endpoint decisions; H.8 execute/skip amendment with legacy version; focused scope, internal freezes, Track P and Track G roles, theory correction proposals, and a post-sweep/B.2 harness pin.
- The author superseded the narrower test ruling: existing CPU tests, including sklearn fits and node subprocesses, are permitted subject to the stated exclusions. The [incident record](reports/LOCAL_TEST_SCOPE_INCIDENT_20261027.md) is closed **within scope after clarification**; previous observations and unknown subprocess outcomes remain intact. Re-run baselines and comparisons in a corrected subprocess environment; test outputs are not evidence.
- The pinned-harness read-only trace has identified a confirmed resumed E1/skip `repeated_bad_count` stamping defect; the trace and independent review are in progress. No pinned harness change is authorized before sweep 1 and B.2.

## 27 October 2026 — local test-scope inventory independently reviewed (AI-assisted; static only)

- The corrected [non-exhaustive static audit](reports/LOCAL_TEST_SELECTION_AUDIT_20261027.md) is accepted for its limited inventory purpose: [review](reviews/LOCAL_TEST_SELECTION_REVIEW_20261027.md), initial inventory `c0ffd1f`, correction `dfbfa96`. It identifies further node-training and LightGBM paths to exclude or inspect and a conservative matched-allowlist procedure.
- No actual allowlist, compliant broad run or full-suite baseline comparison has been certified. The L0 incident remains documented and L4 acceptance criteria remain unchanged.

## 27 October 2026 — local L5 feasibility proposal independently reviewed (AI-assisted; proposal only)

- Independent reviewer accepted the corrected [Track P feasibility proposal](proposals/TRACKP_FEASIBILITY_20261027.md): [review](reviews/LOCAL_L5_REVIEW_20261027.md); proposal `b070022`, corrections `96b0169`. Its pilot-based bootstrap is an illustrative proxy, not a determination of detectable finalist differences; stage costs are sourced projections or explicitly unknown.
- **STOP L5:** author decides which Track P stages to include and how to resolve the listed specification questions. This analysis authorizes no training or scope change.

## 27 October 2026 — local L0 scope re-review (AI-assisted)

- The independent [re-review](reviews/LOCAL_L0_REVIEW_20261027.md) accepts the fidelity of the documented baseline but rejects adherence to the test scope: synthetic node-model fits are confirmed, while the stopping points of other attempted subprocesses are unknown. See the [incident record](reports/LOCAL_TEST_SCOPE_INCIDENT_20261027.md); L4.4 remains unaccepted.

## 27 October 2026 — local test-scope incident (AI-assisted; review pending)

- The L0 and L4.4 harness suites included an in-process test that fitted existing node models on synthetic CPU data; additional node-training subprocesses were attempted with incompletely known outcomes. Two Track G subagents also ran tests outside their stub-only brief. The [incident record](reports/LOCAL_TEST_SCOPE_INCIDENT_20261027.md) separates confirmed fits from unknown subprocess outcomes and preserves available evidence.
- The operator stopped the L4.4 paper-suite repeat upon discovering the scope issue; it is incomplete. No further broad suite or node-training test has been launched since. L0 was independently rechecked with the new facts; L4.4 remains unaccepted. No scientific evidence or authorization is inferred.

## 27 October 2026 — local L2 theory support independently reviewed (AI-assisted; ENGINEERING_ONLY)

- Independent reviewer accepted [the proof audit](theory/T_AUDIT_20261027.md), ten author-check packets and [T3/T5 CPU reproduction](reports/LOCAL_T_SIMULATION_REPRO_20261027.md) after one numerical correction: [review](reviews/LOCAL_L2_REVIEW_20261027.md); commits `7429cb8`, `59527dd`, `99039a3`. The audit flags a zero-noise edge error, a diminishing-returns counterexample and decision-independence conditioning gaps, among other qualified findings. These are AI-assisted audit results, not author-checked propositions.
- Generated T3/T5 tables matched their committed tables byte for byte; the underlying numeric fields had the recorded floating-point differences. The simulations are model-only engineering outputs, not measurements. The author's T4 proof check remains outstanding; no claim or protocol was silently changed.

## 27 October 2026 — local L3 timeline proposal accepted for author review (AI-assisted)

- Independent reviewer accepted the [conditional planning proposal](proposals/ICML_REPLAN_20261027.md) after re-deriving the illustrative schedule and checking assumptions: [review](reviews/LOCAL_L3_REVIEW_20261027.md), proposal commits `d537578` / `be233a9`. The full-route scenario uses guessed windows; Track X completion, resource contention and actual host capacity remain unknown. Official ICML 2027 deadlines were not found on the checked official future-meetings page.
- **STOP L3:** author decides scope and dates, including quality-bar consequences and response windows; only then may the coordinator re-date RUNBOOK. Acceptance is neither adoption nor authorization. Independent L2/L4/L5 work continues.

## 27 October 2026 — local L1 route review accepted; author proposals pending (AI-assisted)

- Independent reviewer accepted the consistency scan, historical annotations and [technical route](TECH_ROUTE.md) after corrections to the dependency graph, references, gate and accounting: [review](reviews/LOCAL_L1_REVIEW_20261027.md). Scan and route commits `221d6d3` / `9a9f7e4`; review corrections `1954484` / `dc63abc` / `66b8079`.
- **STOP L1:** author decisions remain open in [route proposals](proposals/ROUTE_PROPOSALS_20261027.md), including DAC headline framing, bin edges, hard-label diagnostic exceptions, R-A0, score scaling, belief/action coupling, DI endpoint and H.8 coordination. No new PLAN decision or evidence authorization is inferred. L2, L3 and independent L4 work continue.

## 27 October 2026 — local L0 baseline independently reviewed (AI-assisted; engineering only)

- L0 is accepted as a documented baseline with limitations: [report](reports/LOCAL_BASELINE_20261027.md), [independent review](reviews/LOCAL_L0_REVIEW_20261027.md). Paper: 500 passed, 66 failed, 72 skipped, 1 deselected; harness: 433 passed, 27 failed, 3 errors, 55 subtests passed. Raw outcomes and exact IDs are committed with the report. The launch HEAD was not captured; conditions and commands are operator-reported. Failures include sandbox-restricted fake servers and two reproducibility tests; the reviewer reproduced a record-level E0 difference without assigning its cause.
- The author clarified that Mac scope permits read-only Track P proposals and CPU-only unit tests on tiny random-weight models under the stated restrictions; recorded as R1-TRACKP-RUNBOOK-SCOPE. No evidence run or real-model execution follows from this baseline.

## 26 October 2026 — Track P Mac scope clarified (AI-assisted)

- Author clarified R1-TRACKP-RUNBOOK: the Mac restriction covers execution, including Track P training, GPU jobs, API calls and edits to `r1/c3/train/`, while reading documents and writing analyses and proposals, including L5 without runs, are allowed. CPU unit tests using tiny random-weight models are permitted under the author's conditions; test results are test outcomes only. Recorded as R1-TRACKP-RUNBOOK-SCOPE in PLAN §10.

## 26 October 2026 — local (Mac) work runbook (AI-assisted; documents only)

- New agent runbook `docs/r1/prompts/MAC_LOCAL_RUNBOOK.md` for one Claude Code agent on the Mac: L0 baseline; L1 technical-route review and consolidation (`TECH_ROUTE.md`, consistency scan, route proposals — incl. the DAC-framing conflict with R1-ROUTE); L2 theory-check support for A.2; L3 feasibility and ICML 2027 re-plan (proposal); L4 framework code (Track G adapters G.1, Track H follow-ups, regenerate-all analysis pipeline, D.2 scaffold, harness audit — harness pin 897d83c untouched); L5 Track P feasibility review (proposal); L6 ICML LaTeX skeleton in `papers/r1/`; L7 final pass. Subagent use and acceptance criteria per task; independent review at every STOP.

## 26 October 2026 (night) — Track P migrated to TASL-7; host equivalence passed; STOP (AI-assisted; ENGINEERING_ONLY / DRYRUN; independently reviewed and accepted)

- Track P agent on TASL-7, branch `trackp-20261026`. Merged `origin/main` (STATUS conflict: both entries kept, unchanged), then the portal session's last commits.
- **Phase 0:** `docs/r1/reports/PORTAL_TRACKP_HOST_FACTS_TASL7_20261026.md`. RTX 4090, cc 8.9, driver 580 / CUDA 13.0, 965 G free. Work dir `/home/dowling/r1_trackp` (same paths as the portal). Reboot pending since 6 Oct; secrets file absent.
- **Phase 2, same pins:** `docs/r1/reports/TRACKP_PHASE2_ENV_PINS_TASL7_20261026.md`. The venv freeze is identical to the portal's (torch 2.6.0+cu124). The GPU smoke test matches the portal to ~1e-6. All 8 repos (112 files) were re-hashed against the committed `registry.yaml`, which is unchanged. The config is unchanged and `--check-config` is clean.
- **Host equivalence:** `docs/r1/reports/TRACKP_TASL7_EQUIVALENCE_20261026.md`. Kev-0.8B, fresh, soft, lr 1e-4, seed 0, 2,000-step caps, at `8e13e77`. Tolerance pre-declared and pushed first (`f3567e9`). **Equivalent:** Δ width slope −0.0095, Δ mean slope +0.0077, RPS −2.5 % (limits 0.05 / 0.05 / 10 %).
- Code: run manifests record the host and the GPU in use, by UUID (R1-ADA-OVERFLOW).
- Independent review: `docs/r1/reviews/TRACKP_TASL7_MIGRATION_REVIEW_20261026.md`. 5 minor findings fixed; **accepted**. 26.3 leased GPU-minutes on TASL-7.
- **STOP. Waiting for the author:** `trackp_p3a_<date>.md`, and the questions in `docs/r1/reports/TRACKP_TASL7_MIGRATION_20261026.md` (Track X STATUS guard on TASL-7, config label, reboot, other users). No P.3a run. Not merged; the coordinating session merges.

## 26 October 2026 (evening) — Track P: rule v2, two-stage E0 driver validated; portal work ends (AI-assisted)

- The author's evening decisions are recorded as PLAN §10 rows on `trackp-20261026`: R1-E0-THRESHOLDS, R1-E0-BUDGET, R1-E0-HEADFIT, R1-CONTROL-READOUT, R1-TRACKP-CHOICES, R1-EXAM-RULE-V2, R1-P3A-READY. Spec and runbooks are updated, and the agent's own readings are marked for confirmation.
- **Rule v2** is committed: `r1/c3/rules/p3_rule_v2.yaml`, sha256 `8c0ef908…`. `exam_analyze` accepts v2 only. Finalist 1 is the E3 point top; the tie-breaks pick only the second finalist. The rule holds the E0 thresholds (width slope vs label std ≥ 0.6 with bootstrap lower bound > 0, mean slope ≥ 0.8) and A4 ≥ 95 %.
- **Two-stage driver validated** with a short DRYRUN on kev-0.8b (`docs/r1/reports/TRACKP_E0V2_TWOSTAGE_DRYRUN_20261026.md`; clean `5538b79`).
  - The mechanics work. The shortened budget measures no E0.
  - Attempt 1 showed that starting LoRA from the L-BFGS head makes it diverge, then saturate. The head fit therefore stays descriptive, and LoRA starts from the fresh head.
  - ≈ 1.6 GPU-h.
- Independent review: `docs/r1/reviews/TRACKP_RULEV2_REVIEW_20261026.md` (4 minor + 1 on the DRYRUN record, fixed; **verdict: accepted**). The decisions review was accepted earlier.
- **Host change (R1-TASL7-TRACKP):** this is the last Track P GPU work on zhixu portal. The portal work dir, venvs and models are left untouched.
  - Host-equivalence check on TASL-7: reproduce the selected Kev-0.8B run of the portal E0 v2 DRYRUN (code `8e13e77`, `--variant fresh --lr 0.0001`, seed 0, 2,000-step caps). On the portal it gave width slope vs label std 0.923, mean slope 1.012 and RPS 1.99e-4, as pre-declared by the TASL-7 agent in `f3567e9`.
  - Optional: the short two-stage run at `5538b79`.
- **Waiting for the author:** `trackp_p3a_<date>.md`, and the marked readings (descriptive head fit means LoRA starts fresh; bootstrap bound; A4 not disqualifying; final budget for the hard/native runs). Not merged; the coordinating session merges.

## 26/27 October 2026 — Deepthought sweep 1: Phase 5 host smoke passes, Phase 6 D28 STOP (4 of 8 nodes) (AI-assisted; ENGINEERING_ONLY)

Implementation agent (Claude) on deepthought, branch `dt-sweep1-20261026`. Phases 2, 4 and 5 complete and passing; **Phase 6 is a STOP for the author**. Readiness report: [DT_SWEEP1_READINESS_20261026.md](reports/DT_SWEEP1_READINESS_20261026.md). Phase 7 has not started and needs `docs/r1/authorizations/c3_sweep1_<date>.md` from the author.

- **Phase 5 (A.8 host smoke) passes with the real `llama-server`, real GGUF and the schema on**, via the new `r1/scripts/c3_host_smoke.py` (the dry run's isolation, the host's own server, `nvidia-smi` and `ps`; no fault injected — it kills a real process by the pid the batch recorded after matching pid, process group and command line). Server killed mid-request → watchdog recorded the loss, restarted (generation 1) and re-ran both affected roots whole, batch completed (194.5 s); runner killed mid-campaign → completed root kept byte for byte, interrupted root re-run whole, orphan server stopped only on a full identity match (182.4 s). Report: [WATCHDOG_SMOKE_DT_20261026.md](reports/WATCHDOG_SMOKE_DT_20261026.md).
- **R1-SCHEMA verified end to end.** The pinned build enforces per-request `response_format: json_schema`: the same prose-inviting prompt returns Markdown prose without it and strict six-field all-string JSON with it. Across Phase 6's **161 trials there were 0 parse failures**, with `manager_proposal/v1` recorded per trial, in the run manifest and in the sweep index.
- **Phase 6 (A.7 D28 liveness, 8 nodes, 2 × W = 10, memory on, 1,592.8 s): 4 pass, 4 fail.** Pass: `digits_mlp`, `tabular_mlp`, `openml_credit_approval`, `openml_ionosphere`. Fail on `keep_after_trial_1`: `openml_breast_w`, `openml_sonar`, `openml_blood_transfusion`, `openml_wdbc` (also `invalid_rate` exactly 0.30). **No repair, no drop** — read-only diagnosis: [LIVENESS_LLAMACPP_20261026.md](reports/LIVENESS_LLAMACPP_20261026.md).
- **Diagnosis:** every node passes `active_novelty_fraction`, so the manager is not inert. On the four failing nodes **no proposal in 20 trials produced a positive delta**: `max_iter` edits are exactly inert on an already converged model (Δ = 0 in 10–12 of 20 trials) and `C` edits mostly hurt, with baseline `val_auc` 0.9971 (`wdbc`) and 0.9919 (`breast_w`) leaving no headroom; `blood_transfusion` has headroom but nothing helped. The two MLP nodes, with three real knobs, reach Δ +0.17 to +0.22 and 9–10 keeps. All 18 invalid trials are value errors R1-SCHEMA deliberately leaves to the model (`max_iter` beyond the allowed `[100, 3000]`, `class_weight` outside `{None, "balanced"}`), each caught by D25.
- **The 19 Oct risk did not materialise: `digits_mlp` is now the strongest node** (novelty 0.90, invalid rate 0.00, 10 keeps after trial 1).
- **Full GPU offload** proven at every load and after every collection, route (ii) against the pinned footprint; the server pid held **exactly 5253 MiB** on the card in every start measured.
- **Measured runtime basis:** mean LLM latency 7.46 s at a mean prompt of 827 tokens (max 1,232), worker runs 2.47 s per trial → sweep 1 on the pool of 8 (5,760 proposals) ≈ **14–20 h wall on one TITAN**; ≈ 7–10 h on the 4 passing nodes; Phase 8 audits ≈ 2–3 h wall on 16 workers.
- **Blocking for the author:** the node pool (`min_live_nodes` = 8 would STOP at the runner's own liveness phase; options and their costs are in the liveness report). Also open: the paper pin can only be "the `main` head at launch" because the runner refuses a checkout that is not at the remote head (`main` moved three times during this work); whether "one manager per TITAN" means one batch on one card (what is built, and what is pinned) or four concurrent batches (not built; four sweep indexes, which the A.4 table build rejects as one sweep); whether to pin a `footprint_mib` below the measured 5253.
- **Also fixed, so a real launch can pass the prepare gate:** `r1/c3/serve.py` validates a model pin before importing `torch`, and the four Track P test modules skip instead of failing collection where `torch` is absent (it is not in the harness lock). The accepted-failure list in `c3_prepare_check.py` was not changed.

## 26 October 2026 — Deepthought sweep-1 restart: Phase 2 recheck and Phase 4 config (AI-assisted; ENGINEERING_ONLY)

Implementation agent (Claude) on deepthought, branch `dt-sweep1-20261026` from `main` `7611338` (later merged `fc3e0da`); harness `r1` fast-forwarded to `897d83c` = `HARNESS_PIN_C3`. The six 25 Oct documentation commits were cherry-picked onto the new branch (report blobs byte-identical; STATUS conflicts resolved by keeping both sides). The old `dt-sweep1-20261025` is history. PLAN §10 records the author's R1-DT-RESTART / R1-DT-TESTGATE / R1-DT-SCRATCH / R1-DT-PIN.

- **Phase 2 (redone at the new pins):** all nine data caches `ok` (climate included; the two non-OpenML nodes checked separately with the network blocked). Harness suite **454 passed / 8 failed / 1 collection error**, exactly the accepted 26 Oct baseline for `897d83c`. Paper suite **528 passed / 6 failed / 25 skipped / 4 collection errors**. Report: [DT_PHASE2_RECHECK_20261026.md](reports/DT_PHASE2_RECHECK_20261026.md).
- **Two environment findings that change the launch.** (1) The `LocalWorker` runs bare `python3`, which on this host resolves to anaconda's **scikit-learn 1.5.1**, not the locked 1.8.0; three harness stage2 tests failed for that reason and pass with the venv `bin` first on `PATH`. The sweep must be launched with that `PATH`. (2) `narwhals` was missing (`lightgbm` had been installed `--no-deps`), which broke `r1/c3/arms.py`; `narwhals==2.27.1` installed `--no-deps`, metric libraries re-verified unchanged. `test_c3_control_dryrun` and `test_trackp_soft_label_v2` pass after it.
- **R1-DT-TESTGATE (a):** met. Standalone with `--deadline 300`: `retry` 93.1 s (ollama) / **107.3 s** (llamacpp, deepthought config), `permanent` 44.2 / 48.0 s, `watchdog` **101.1 s**, all **passed**. Only the hardcoded 75 s limit fails.
- **R1-DT-TESTGATE (b): resolved, one attempt.** The `interrupt` scenario **passes** on both backends, in the suite and standalone (123.5 s), archive assertion included. The 25 Oct failure was on pre-batch-B code; batch B deviation 5 documents that exact `openml_breast_w__s105` case and the assertion it changed, while keeping "a root with logged trials at the kill must still have its partial ledger archived". Nothing was relaxed here.
- **Phase 4 (A.6): config completed, `--check-config` passes, no placeholders.** `r1/scripts/configs/c3_sweep_deepthought.json` sha256 `85431afc…` before this commit; `proposal_schema = manager_proposal/v1` on (R1-SCHEMA); re-probed on the host with the sweep's own server settings (`-np 1 -c 8192`): build `version: 0.7.0-dev (build 1, commit 620d222)`, GGUF sha256 `509287f7…`, verdict **FULL_GPU_OFFLOAD** by route (ii) (no offload line at default verbosity; CPU control 4.192× slower), **`footprint_mib` = 5253**; `gpu_uuid` pins TITAN index 1; port 18083; `workers` 16 of 40. Two tests that asserted the file was still a draft were updated and a completed-config test added.
- **Host is not exclusive in practice.** Three other users held 5.3 GiB on TITAN index 0 and about 12.4 of 40 cores while this phase ran (co-tenancy is allowed and logged, PLAN §10 13 Oct). Ceph file-count headroom 45 % (275,839 of 500,000); `/ceph` 303 TiB free; scratch on local disk per R1-DT-SCRATCH.
- **Open for the author:** whether the "one manager per TITAN" GPU plan means one batch on one card (what is built, and what sweep 1 assumes) or four concurrent batches (not built; four sweep indexes, which the A.4 table build does not accept as one sweep); `workers` 16 rather than the runbook's starting 24; whether to pin a slightly lower `footprint_mib` than the measured 5253.

## 26 October 2026 — hosts: TASL-7 dedicated to Track P; Ada as overflow (AI-assisted; documents only)

- Author decisions recorded (PLAN §10): R1-ADA-OVERFLOW (zhixu experiment takes resumable overflow runs; one comparison table on one GPU type and one pinned environment unless declared) and R1-TASL7-TRACKP (second RTX 4090 node TASL-7, exclusive, dedicated to Track P; zhixu portal left to Track X).
- RUNBOOK §3 host table and Track P hardware note updated; `PORTAL_TRACK_P_RUNBOOK.md` gains a host-change header with the migration steps (TASL-7 host facts, same pinned environment and model revisions, host-equivalence E0 DRYRUN with a pre-declared tolerance, independent review, STOP).
- Needed from the author: SSH key and alias for TASL-7, GitHub authentication there, a reboot (the host reports "System restart required") before long runs, Claude Code on TASL-7, later `~/.config/r1/secrets.env`.

## 26 October 2026 — Track P: author's decisions implemented; E0 v2 DRYRUN on Kev-0.8B and Qwen-0.8B (AI-assisted)

- The author's 26 Oct decisions are recorded as PLAN §10 rows (R1-STARTLUX-TRAINABLE … R1-TRACKP-MERGE) on `trackp-20261026`, with the spec corrected to match. The agent's own implementation choices are listed under the rows for confirmation.
- Code: E0 protocol v2, the A3 pool budget, token rows (mean-embedding init, fp32, own lr), the lr grid, early stopping, temperature scaling, the Track X marker in the GPU lease, 10 Jev questions, environment pins checked and recorded in every manifest.
- Independent review: `docs/r1/reviews/TRACKP_DECISIONS_REVIEW_20261026.md` (1 blocking + 9 minor, then 3 minor on the DRYRUN report and 1 on the manifest dirty-file list; all fixed; **verdict: accepted**). The four Track H modules pass at harness `897d83c`: 29/29.
- **E0 v2 DRYRUN** (DRYRUN, code at `8e13e77`; the manifests' dirty flag comes from an uncommitted review-file edit, not code): `docs/r1/reports/TRACKP_E0V2_DRYRUN_20261026.md`.
  - Selected lr 1e-4 for both bases. Width slope vs the label's own std: 0.92 (Kev) and 0.97 (Qwen); mean slope 1.01. Label ceiling vs s: 0.925.
  - Within 2,000 steps the frozen-backbone head fit learns no width (it had not converged). Hard labels collapse the width (ratio 0.27 / 0.20).
  - A3 v2 is ≤ 3e-5 on both; A4 v2 is 1.00 on both; A5 fails on Qwen (TV 0.20).
  - The soft runs peak near the 2,000-step cap.
  - 3.7 GPU-h, plus ≈ 0.5 h for an aborted first attempt.
- **Waiting for the author:** the E0/A4 threshold row, the training budget, the head-fit and A5 readings, and the Phase 5 authorization. Not merged; the coordinating session merges.

## 26 October 2026 — Track P branch merged into `main` by the coordinating session (AI-assisted)

- `trackp-20261026` (`6f67717`, Phases 0–4 independently accepted on the portal, P.3a DRYRUN) merged into `main` after a merge review: `docs/r1/reviews/TRACKP_MERGE_REVIEW_20261026.md` (accepted; one STATUS conflict resolved by keeping both sides; v1 soft labels reproduce `main` exactly; two environment-pinned Track P tests fail off the portal, not code defects).
- R1-PORTAL-SCHEDULE amended (author): Track X evidence marker `~/r1_locks/trackx_evidence.active` during B1/B2, plus STATUS headings; both runbooks updated (separate commit).
- Open for the author (from the overnight summary): Phase 5 design (E0 training budget, head fit, learning-rate grid, A3 policy), spec readings, model-wrapper choices, environment pins, harness `6afdb0e` push, secrets before Phase 7.

## 26 October 2026 — exam Phase 1 merged into `main` / `r1` by the coordinating session

Harness `r1` fast-forwarded to `897d83c` (exam Phase 1; re-run in the coordinator's Linux VM env: 453 passed / 9 failed / 1 error, no failure outside the known environmental set). Paper `exam-x-20261026` (`ea6dd8c`, independently accepted at STOP 1) merged into `main`, which had meanwhile gained the Track P documents (`e09b399`, `b5a7aec`); PLAN §10 and STATUS conflicts resolved by keeping both sets of rows/entries. **Note for the author:** R1-EXAM-TRANSFER (no GitHub credentials on the portal; code via SSH bare repos) and R1-TRACKP-RUNBOOK (Track P agent clones from GitHub on the portal) differ on GitHub credentials on the portal; both agents must take the R1-PORTAL-SCHEDULE GPU lease. Not pushed (needs the author's credentials).

## 26 October 2026 — portal exam Phase 1 independently reviewed and accepted; STOP 1 (AI-assisted)

Completed runbook code gaps 1.1–1.10 on the Mac, with no LLM inference or model-weight downloads. Paper implementation `e6f42c0`, fixes `930687c` / `57f56e5` / `df1a6eb`, evidence `b3764a3`; harness `897d83c8efa364ec2fdd37288241cc42e01d7274`. Frozen rule bytes/hash committed at `4b9c656` before any B1 fixture data. Corrected storage remains `/home/dowling/exam-x/{models,work}`, with a 100 GB floor; no portal runtime install or code transfer occurred.

Fresh independent reviewer reran both full suites, the fake-server Stage A/B1 kill/resume pipeline and final focused checks; **ACCEPTED**, all three MAJOR and one MINOR findings resolved: [EXAM_1_REVIEW_20261026.md](reviews/EXAM_1_REVIEW_20261026.md). Broad checkpoint: paper 445 passed / 21 failed / 9 skipped (baseline 417 / 22 / 9); harness 454 passed / 8 failed / 1 collection error (baseline 448 / 8 / 1). Zero new failure/error IDs; one baseline paper watchdog failure passed in both after runs. Full suites launched at initial implementation; final fixes independently checked with 31 passing focused tests and counterexamples. Existing failures remain documented. All campaign outputs are synthetic DRYRUN fixtures.

Handoff: [EXAM_X_CODE_HANDOFF.md](overnight/EXAM_X_CODE_HANDOFF.md). Report and saved evidence: [PORTAL_EXAM_PHASE1_20261026.md](reports/PORTAL_EXAM_PHASE1_20261026.md). **STOP 1:** ready for author/coordinator merge; no protected branch merge/push, Phase 2 activity, scientific rule adoption or B1/B2 authorization inferred.

## 26 October 2026 — author STOP 0 decisions recorded; Phase 1 authorised (AI-assisted)

Recorded the author's direct STOP 0 decisions in PLAN §10 R1-EXAM-STORAGE / LICENCES / ORNITH / TRANSFER / USER-RUNTIME. Approved storage is `/home/dowling/exam-x/{models,work}` (author corrected the initial `/ceph` paths after a read-only portal check found `/ceph` absent); downloads/runs must stop below 100 GB available on that filesystem. Licences approved for research evaluation and publication, including Nemotron/Laguna OpenMDW-1.1 and LFM2.5 LFM 1.0. Ornith-31B is removed as not publicly released, no substitute; effective pool 21 candidates plus 3 anchors (OLMo Think remains a sensitivity). Ornith-35B maps to `ornith-ai/Ornith-1.0-35B`, with vendor GGUF Q4_K_M checked first in Phase 2. Code transfer uses Mac-to-portal SSH pushes to bare repositories under `/home/dowling/exam-x/work/`; no portal GitHub credentials. User-level uv/Python >=3.11 installation under `/home/dowling` is permitted, no sudo/system Python changes; installation not yet performed. Phase 1 is now authorised, with independent review at STOP 1; no later phase or evidence authorisation is inferred.

## 26 October 2026 — portal exam Phase 0 resumed, independently reviewed and accepted; STOP 0 (AI-assisted; ENGINEERING_ONLY)

The author restored Tailscale and authorised resuming Phase 0 only, with independent review and STOP 0 for disk/licence decisions. SSH to `portal_zhixu` succeeded. Inventory commits `57d8fc4` / `0791688`, formatting cleanup `d8d1035`; report: `reports/PORTAL_HOST_FACTS_20261026.md`, command transcripts and metadata under `reports/portal_host_facts_20261026/`. Same independent reviewer re-ran SSH checks and accepted the **read-only inventory and decision package**, with no remaining report corrections: `reviews/EXAM_0_REVIEW_20261026.md`, resumption acceptance. The initial failed attempt and blocked-record review remain preserved below/in Git history.

- **Host facts:** TASL-2, Ubuntu 22.04.5; RTX 4090, 24,564 MiB, driver 535.309.01, compute capability 8.9; 32 logical CPUs, about 62 GiB RAM. About 899 GB / 837 GiB available on the filesystem containing `/home/dowling`. No GPU compute applications at either sample; another user's desktop remains present. This establishes neither future reservation nor model fit.
- **Preparation gaps:** Python 3.10.12, no uv/HF CLI/visible llama-server in checked scope. CUDA toolkit 12.2 is installed outside PATH. Public GitHub works, but private paper repo HTTPS lacks credentials and SSH stops at an unknown host key. OpenML homepage HEAD 200, metadata API HEAD 412; cache-transfer plan unchanged.
- **HF/licence scope:** no token in the checked environment/cache scope. Twenty candidate base repositories plus OLMo Think and the 7B anchor report `gated=false`, with API/config HEAD 200; eventual GGUF weight access is not established. Custom terms are documented for Nemotron, LFM2.5 and Laguna. Ornith-31B remains unidentified; a vendor Ornith-35B repo is a documented possible mapping for the 35B-A3B label, not an adopted substitution.
- **Verification:** independent live host/network/per-repo rechecks; Python and shell syntax, all JSONL records and `git diff --check` passed. No installation, build, inference, worker run, weight download, credential/known_hosts change, merge or push was performed in this resumption.
- **STOP 0:** author to confirm proposed `/home/dowling/exam-x/{models,work}`, decide the licence package, and resolve Ornith identities/mapping. Paths were not created; no licence accepted. Phase 1 and all later phases remain unstarted.

## 26 October 2026 — portal exam Phase 0 blocked by local network access (AI-assisted; ENGINEERING_ONLY)

Updated `main` was verified at `fad6dfe` (R1-EXAM-HOST conflicts resolved). Created `exam-x-20261026` from paper `main` and harness `r1` (`6afdb0e`), preserving existing untracked files. Paper commit `39731ce` records the attempted host inventory in `reports/PORTAL_HOST_FACTS_20261026.md`. SSH to `portal_zhixu` (`dowling@100.120.160.70`) returned `Network is unreachable` outside the sandbox; local `tailscale status --json` reports `BackendState: Stopped`. No remote command ran; all host facts 0.1–0.9 remain uncollected. Phase 0 is incomplete, not accepted. Independent review (`reviews/EXAM_0_REVIEW_20261026.md`) reproduced the access blocker: ACCEPTED AS A BLOCKED EXECUTION RECORD ONLY; PHASE 0 NOT ACCEPTED / INCOMPLETE. One MAJOR completion blocker (missing host facts), no MINOR corrections; `git diff --check` passed. Restore the Mac's Tailscale connection before resuming the read-only inventory; the author storage/licence gate remains pending. No installation, inference, worker run, model download, Phase 1 implementation, merge, or push occurred.

## 26 October 2026 — Track P overnight summary (AI-assisted; ENGINEERING_ONLY / DRYRUN)

- Track P agent on zhixu portal, branch `trackp-20261026` (not merged). Phases 0–4 done and independently reviewed and accepted; Phase 5 (P.3a) not started (no authorization note); its one-model DRYRUN (kev-0.8b) ran: soft E0 mean slope 1.00 but width slope 0.11 (would fail E0), hard labels collapse width; A4 fails, A3 blocked by Kev's state limit — not evidence, nothing tuned.
- No stop condition hit; ≈ 57 leased GPU-minutes. Summary and the author's questions: `docs/r1/reports/TRACKP_OVERNIGHT_20261026.md` (StartLux rung; Phase 5 design; spec interpretations; harness pin `6afdb0e` to GitHub; merge).

## 26 October 2026 — Track P Phase 4: P.1/P.2 toy batch (AI-assisted; ENGINEERING_ONLY; independently reviewed and accepted)

- Same 64-example batch, 50 steps, both outputs, shared loop, all 8 families (StartLux included, rung pending the author): total, belief and action loss decrease on the whole batch in eval mode for every family; reload bit-identical. Laya needed one fix (its new heads now read the mean-pooled encoder output; the post-head [CLS] state is ~constant). Laya's belief still ends above the constant base rate (slow at lr 2e-5); the Qwen-0.8B control is unstable. Report `docs/r1/reports/TRACKP_P4_TOY_BATCH_20261026.md`, review `docs/r1/reviews/TRACKP_4_REVIEW_20261026.md` (accepted).
- Open for the author: Laya readout state; control learning rates before P.4. Phase 5 (P.3a) needs `trackp_p3a_<date>.md`; only its one-model DRYRUN runs tonight.

## 26 October 2026 — Track P Phase 3: P.0 spikes (AI-assisted; ENGINEERING_ONLY; independently reviewed and accepted)

- 8 bases (Kev 0.8B/4B, Qwen3.5-0.8B/4B-Base, Laya, StartLux Instant 0.8B/2B/4B) at commit `fcc7d7d`: load, 12-option forward, LoRA r = 16 (incl. DeltaNet), toy SFT on soft targets for both outputs, bit-identical save→reload, sha256, peak ≤ 13.7 GB at ~1,024 tokens × 8 with gradient checkpointing; packing off on all Qwen3.5-family bases (expected). StartLux trains with the prompt-bidirectional mask; our transformers-5.19 port matches StartLux's own 5.8 code at bf16 noise level (12–19 × below a mask error); vLLM path not run. Report `docs/r1/reports/TRACKP_P0_SPIKES_20261026.md`, review `docs/r1/reviews/TRACKP_3_REVIEW_20261026.md` (accepted).
- Six attempts recorded (OOM without gradient checkpointing; CPU-loading/composite-config/lr bugs; Laya head scale → LayerNorm before new heads; seeding). GPU: 33.8 leased minutes for Phases 2–3.
- **Author decides: StartLux rung (trainable candidate or inference-only zero-shot rung).** Also open: LayerNorm before new heads; Kev pointer-temperature policy; E0 head-fit design before Phase 5.

## 26 October 2026 — Track P Phase 2: environment, downloads, pins (AI-assisted; ENGINEERING_ONLY; independently reviewed and accepted)

- Branch `trackp-20261026` (Phases 2–4 on the reviewed branch per the author's overnight instruction). Report `docs/r1/reports/TRACKP_PHASE2_ENV_PINS_20261026.md`; review `docs/r1/reviews/TRACKP_2_REVIEW_20261026.md` (accepted).
- Run venv `~/r1_trackp/venvs/trackp-gpu`: torch 2.6.0+cu124 (2.5.1+cu121 fails under transformers 5.19), transformers 5.19.0, peft 0.21.2, flash-linear-attention 0.5.2, causal-conv1d 1.7.0 (built). GPU smoke test passes (bf16 matmul; Qwen3.5-0.8B DeltaNet forward on fla/causal-conv1d within TF32-level precision of the fp32 reference).
- 8 repos (26 GB) at pinned revisions, all 112 files verified against the Hub records (LFS sha256 / git blob sha1) and re-hashed by the reviewer; Kev adapters also match the GitHub `kev-1.0` release; `r1/c3/train/registry.yaml`; portal config filled (`--check-config` clean).
- GPU: < 10 minutes under the lease. Open for the author: torch 2.6/cu124 on driver 535; `jev.model = jev-1.14.0`; code pins (Kev code 23 commits after `kev-1.0`).

## 26 October 2026 — Track P Phase 1: code (AI-assisted; ENGINEERING_ONLY / DRYRUN; independently reviewed and accepted)

- Track P agent on zhixu portal, branch `trackp-20261026` (not merged). Items 1.1–1.11 on tiny models, CPU only; report `docs/r1/reports/TRACKP_PHASE1_CODE_20261026.md`, handoff `docs/r1/overnight/TRACKP_CODE_HANDOFF.md`, review `docs/r1/reviews/TRACKP_1_REVIEW_20261026.md` (3 blocking, 8 minor findings fixed; accepted).
- Tests: paper 407/1/11/4 → 559/1/11/4 (failing set unchanged, environmental: harness pin `6afdb0e` not on GitHub); harness unchanged.
- Open for the author: handoff questions 1–7.

## 26 October 2026 — Track P Phase 0: portal host facts (AI-assisted; ENGINEERING_ONLY; independently reviewed and accepted)

- Track P agent (Claude Code) on zhixu portal (`TASL-2`), work dir `/home/dowling/r1_trackp/`, branch `trackp-20261026` in both repos (paper from `main` `b5a7aec`; harness from `r1` `264011e`). Report `docs/r1/reports/PORTAL_TRACKP_HOST_FACTS_20261026.md` (commits `870e6de`, `f08e5e4`); review `docs/r1/reviews/TRACKP_0_REVIEW_20261026.md` (6 minor findings fixed; verdict accepted). Read-only apart from the clones; no installs, weights, GPU jobs or secrets.
- Findings: RTX 4090 sm_89, driver 535 / CUDA 12.2 (current torch wheels are cu126/cu130 → Phase 2 risk); Python 3.10 only, `uv` absent; all Track P Hub repos public and un-gated (StartLux CC BY-NC 4.0); Laya weights are `convaiinnovations/laya-typed-decisions`, Kev weights `jaredpalmer/kev-{0.8b,4b}` (RUNBOOK names are the GitHub code repos); `~/.config/r1/secrets.env` absent; **harness pin `6afdb0e` (`HARNESS_PIN_C3` on `main`) is not on GitHub**.
- Open for the author: the six questions at the end of the report.
## 26 October 2026 — Track P agent moved onto zhixu portal (AI-assisted; documents only)

- Author decision (R1-TRACKP-RUNBOOK revised): the Track P agent runs on zhixu portal itself, not on the Mac over SSH. `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md` updated: placement table, host and clone rules (own clone on the portal, `trackp-<date>` branches pushed with the portal's GitHub credentials), secrets on the same host (never read or passed on a command line), Phase 0 checks GitHub push and the agent's own endpoints, Phase 1 code and CPU-only tests on the portal, reviewers on the same host. RUNBOOK Track P execution line and hardware note aligned.
- Needed from the author before Phase 0: start Claude Code on the portal; GitHub authentication on the portal (clone of the private repo, push of `trackp-*`); `~/.config/r1/secrets.env`.

## 26 October 2026 — Track P revised and adopted; portal agent runbook for Track P (AI-assisted; documents only)

- Author decisions recorded (PLAN §10): R1-C3-POST (Track P revised: belief/action decoupling, decision-model exam P.3a/P.3b, reasoning arm P.6, bounded-score RL rewards), R1-C3-CONTROL (Qwen3.5-0.8B/4B-Base control), R1-SOFT-SIGMA (pooled σ̂ in the soft label), R1-PORTAL-SCHEDULE (Track X evidence first on the 4090; GPU lease), R1-JEV-RUNG (official TypeSafe API, version pinned and logged), R1-RB-TEACHER (DeepSeek-V4.1-Flash-1017 demonstrations), R1-TRACKP-RUNBOOK.
- RUNBOOK: Track P replaced; C.1 and B.5 rows aligned; host rule for the GPU lease added.
- New: technical specification `docs/r1/TRACK_P_POST_TRAINING.md`; reading list `docs/r1/references/` (Jev architecture reconstruction, calibration notebook notes; three paper PDFs still to be added by hand — arXiv/ACL are not reachable from the agents' sandboxes); agent runbook `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md` (Phase 0 host facts, Phase 1 code, Phase 2 pins, Phase 3 P.0 spikes, Phase 4 toy batch, Phase 5 P.3a, Phase 6 label gate, Phase 7 P.3b, Phase 8 A5, Phase 9 A6 and R-B).
- `PORTAL_EXAM_RUNBOOK.md` §0: one added line asking the Track X agent to take the same GPU lease.
- **Open for the author:** StartLux rung after P.0; Track H.8 `OfflineBanditEnv` action = bin must become execute/skip before P.5 uses it; place `~/.config/r1/secrets.env` (TYPESAFE_API_KEY, DEEPSEEK_API_KEY) on the portal; start Tailscale on the Mac (the Track X agent found it stopped).

## 26 October 2026 — exam execution decisions; portal agent runbook (AI-assisted; documents only)

- Author decisions recorded (PLAN §10): R1-EXAM-CTX (32k), R1-SCHEMA (structure-only `json_schema` in exam and sweeps, before sweep 1), R1-QUANT-SOURCE (vendor Q4_K_M, else bartowski; GSQ-RCO out), R1-EXAM-RUNBOOK.
- New agent runbook `docs/r1/prompts/PORTAL_EXAM_RUNBOOK.md`: Phase 0 host facts, Phase 1 code gaps (schema, thinking control, random-valid anchor, A4 observer, exam namespace guard, registry and fit estimator, ported Round-7 machinery, exam runner, analysis with a pre-committed rule, config), Phase 2 downloads and pins, Phase 3 Stage A, Phase 4 author gate, Phase 5 B1, Phase 6 B2.
- Later the same night: author adopted X.2–X.6 with the two amendments (R1-EXAM-PROTOCOL), required an independent review loop at every exam phase (R1-EXAM-REVIEW), and decided Q10 (R1-A1-VERIFY: A1 unchanged; non-firing verify reported as a confirmed prediction). Runbook updated accordingly.

## 25 October 2026 — Track H: DAC control interface, Mac steps H.1–H.9 (AI-assisted; ENGINEERING_ONLY / DRYRUN; reviewed and accepted 26 Oct)

Acceptance by the coordinating session (Claude), 26 Oct. Re-ran in the Linux VM: harness 446 passed / 10 failed / 1 error (the known environmental set, unchanged from the baseline); paper 439 passed / 1 skipped / 1 failed (known `test_real_runner_desktop_dryrun`) plus `test_c3_control_dryrun` (1 passed). Read the harness diff (defaults byte-identical: `detail`/`events` only when set, `skip_display` only when declared, re-screen only for controllers that opt in) and the RuleController, featurizer v2, KG-verify and AWR changes. Accepted. Author answers recorded: H.4 line keeps the trial id and summary prefix; D25 inactive-key skips keep their old line; "identical information set" means identical declared access. **Open for the author (Q10):** at the declared g = 0.1 σ_node and r = 2, KG verify can never pay (VoI < 0.4 σ_cmp ≤ 2rg), so A1's verify is vacuous on these nodes; the control dry run used r = 1, campaigns use the declared r. Merge order: harness `track-h-25oct` → `r1` first (pin `6afdb0e`), then this branch → `main`.


- **Review round (26 Oct; still pending review).** Coordinator review asked for six fixes, all done on the same branches: F1 AWR trains on the label half only (`bd45aea`); F2 control-plane skips no longer count in `invalid_so_far` (featurizer v2; tables byte-identical) (`fab1a9c`); F3 `RuleController` verifies at E2 with D23's KG rule and `posterior_mean/v1`, A1 equals the index-policy arm including verify (`7053f42`); F4 the hybrid re-screens its revision once (harness opt-in hook `6afdb0e`, paper `9aafb55`); F5 LLM self-control at E1/E2 by flag (`bdf1ce3`, test fix `6c7b19c`); F6 W and the LLM cap bind, the trial budget never does, `matching_report` flags violations (`4ae8a1b`). Pin → `6afdb0e` (`2523e0c`). New DRYRUN manifest `results/r1/engineering/c3_control_dryrun_20261025T231516Z` (`a19b447`), all 14 checks pass. Finding: at g = 0.1 σ_node with r = 2 KG verify can never fire (VoI < 0.4 σ_cmp ≤ 2rg); the dry run used r = 1 and still no verify fired. Tests: paper 446 / 1 skipped / 1 failed (known); harness 446 / 10 / 1 (same failing set).

Implementation agent (Claude) on branch `track-h-25oct` in both repositories (paper from `bf45424`, harness from `r1` `264011e`); not merged, not pushed. No LLM, GPU, SSH, real llama.cpp/Ollama or model weights; fake servers and fake sidecars only. Details, deviations and questions: `docs/r1/overnight/TRACK_H_25OCT_HANDOFF.md`.
- **Harness `2604a97`:** `ControlDecision.detail` and whitelisted controller events (`prior_unavailable`); R1-SKIP-DISPLAY `one_line/v1` in the memory summary, `campaign_started` and snapshots. Defaults unchanged.
- **H.2 (`ffac687`):** one featurizer `features_from_view` for the online controller and `dataset.build`; pilot table byte-identical; online features from real `ControlView`s hash-equal all 1,323 pilot rows; leak tests.
- **H.1 (`211552a`):** `PriorModel`/`Forecast`; wrapped A1–A3 reproduce `offline_eval` on the 19 Oct pilot table bit for bit; A4 typed questions. NGBoost variant not in the code base, not added.
- **H.3/H.6 (`5de18eb`):** `RuleController` for every arm (rule skips first, Prop. 8 skip, one cached forecast serves E2's Bayes keep, full decision records, A4 charged to the LLM cap); A1 equals the constant-prior index policy on a scripted campaign.
- **H.4 (`afda1ce`):** skipped proposals shown as one line without a metric; manifests record `skip_display`.
- **H.5 (`2046f97`):** stdlib sidecar with sha256 pin and `FakeLoader` (real loader = Track P.2); 1 s timeout → A1 fallback + `prior_unavailable`.
- **H.7 (`801f6e1`):** AWR direct arm, LLM self-control, hybrid (a proposal); `matching_report` checks instances, W, LLM cap, information set.
- **H.8 (`bc6fc10`):** `OfflineBanditEnv` (Gymnasium API, optional); reproduces `offline_eval` one-step values (rel. 1e-12).
- **H.9 (`7ada947`, `2647fab`):** desktop DRYRUN, 2 nodes × 10 arms, SIGKILL mid-campaign and resume, all checks pass: `results/r1/engineering/c3_control_dryrun_20261025T224515Z/summary.json`.
- **Pin (`8ef8f8f`):** `HARNESS_PIN_C3` → `2604a97`, which is not on harness `r1` yet: merge harness `track-h-25oct` into `r1` before this branch reaches `main`, or a sweep launch STOPs.
- **Tests:** paper 383 passed / 1 skipped / 1 failed → 435 / 1 / 1 (same known failure); harness 433 / 10 / 1 → 443 / 10 / 1 (same failing set).
- **Questions for the author:** H.4 line wording (trial id + summary prefix); which skips get the line; meaning of "identical information set"; hybrid definition; online trial budget vs W; `invalid_so_far` semantics; A4 calibration data; A6 τ_node; LLM self-control epochs.

## 25 October 2026 — exam located; Tracks X, H, P added to the RUNBOOK (AI-assisted; documents only)

- **Exam located.** The model "exam" is the Round-7 candidacy exam of the Paper A repo (`agent-checkpoint-intervention`, `paper/appendices/C_protocol.tex`; `round10/CANONICAL_EXAM_RESULTS.md`; evidence `evidence/round7-blackwell-grouped/run/`), completed 4 Sep 2026; a code copy is in `archive/old_b_2026-10-09/code/.../round5_titan_exam.py`. Assessment (coordinating session): sound machinery, but it measures a tool-using coding agent on a different task and hardware, is confounded by submission-format conformance, and is an eligibility screen only. Not evidence for R1; machinery to be ported (Track X.1).
- **Author decisions** R1-EXAM-POOL and R1-DAC-INTERFACE recorded (PLAN §10). RUNBOOK gains Track X (proposer exam on zhixu portal), Track H (DAC interface) and Track P (post-training); host rule on proposer size updated.
- **Finding for R1-C3-BASE:** StartLux-Decision publishes no training code and its Instant models use bidirectional prompt attention via a vLLM plugin, so "fits TRL GRPO directly" is unverified (P.0 spike decides). Kev's trainer takes hard labels only and has no RL code (soft-label patch needed).
- **Decisions needed:** adopt the Track X protocol (X.2–X.6); H.4 skip display in manager memory; P.1 Qwen3.5-Base control rung; Track P as a whole.
- Evening: author decided H.4 (R1-SKIP-DISPLAY) and the Q4_K_M basis of the fit estimate (R1-EXAM-FIT); Track X revised after an audit (B1 screen on audited proposal increments, B2 finalists, roles separated, A4 self-forecast, 32k context proposed; prompt lengths measured: max 1,345 tokens). Branch `track-h-25oct` (rebased on `main` `a8aa001`), not merged.
## 25 October 2026 — batch B: A.10, C3 label sweep ported to llama.cpp (AI-assisted; ENGINEERING_ONLY; reviewed and merged)

Review by the coordinating session (Claude), 25 Oct. Found before merge: the runner accepted GPU offload only from the `offloaded N/N layers` log line, which llama.cpp v0.7.0 does not print on deepthought (probe report on branch `dt-sweep1-20261025`); fixed in `8122600` with the author's two-route acceptance. Re-ran the offload/instance/probe tests (57 passed) and the three llama.cpp dry runs (3 passed). Fast-forward merged into main. Harness `batch-b-25oct` fast-forwarded into `r1` and pushed (`origin/r1` 4012897 → 264011e; this also published `7305434`, the `openml_climate` node, which had not been on origin). Deepthought agent runbook added as `docs/r1/prompts/DEEPTHOUGHT_SWEEP1_RUNBOOK.md`.

Implementation agent (Claude) on branch `batch-b-25oct` in both repositories (paper from `main` `3d3ec48`; harness from `r1` `7305434`); not merged, not pushed. No LLM, GPU, SSH, real llama.cpp or Ollama; fake servers only. Details, fail-before evidence, host checklists and build recipes: `docs/r1/overnight/BATCH_B_25OCT_HANDOFF.md`.
- **Runner (`d560490`):** config `backend` (`ollama` default, historical path unchanged; `llamacpp`): dedicated `llama-server` per batch (`r1/scripts/llama_server_instance.py`), GGUF sha256 and `llama-server --version` line pinned before every start, `/health`, `/v1/models`, `/props`, one-token probe, full GPU offload from the server log (CPU fallback or partial offload = STOP), census as before; watchdog via `/health` and `/v1/models`; orphans stopped only if pid, owner, process group and command line match; A.5 resume unchanged. Collectors/liveness take `--manager-model llamacpp/<alias>`. Fixed: a root failing with the OpenAI client's unpicklable exception broke the collector's process pool.
- **Fake server and dry runs:** `c3_fake_llama_server.py`; `c3_sweep_dryrun.py --backend llamacpp`. Passing on the llama.cpp path: the deepthought config (retry + permanent), kill-and-resume, watchdog (server SIGTERM).
- **Harness (`264011e`, pin updated in `HARNESS_PIN_C3`):** `llamacpp` base URL gets `/v1`; no API key needed; no hidden OpenAI-client retries (before: a dropped request was retried silently, outside the logged D26-seeded retry). Seed reaches the request and the `llm_call` record; connection errors classified like Ollama's.
- **Configs (`607f78e`):** deepthought on llama.cpp with nine `TODO_VERIFY_ON_HOST` values; new zhixu portal draft; author's answers applied (watchdog on, limits 5/3, `min_live_nodes` 8, Paper A check "not applicable" via `paper_a_status.py --not-applicable`, refused on `ucrtasl`). Ada config unchanged.
- **A.11 helper (`adab041`):** `python3 -m r1.scripts.llamacpp_probe` — one-token load probe with the runner's own checks; gives `build`, `model_sha256`, `footprint_mib`.
- **Review fix (`8122600`):** on deepthought, llama.cpp v0.7.0 (commit 620d222) printed no `offloaded N/N layers` line at default verbosity (report on `dt-sweep1-20261025`), so the log-only check would STOP every real start. Now full offload passes by route (i) the N/N line (partial N/M = STOP) or route (ii) the server pid on the configured GPU with ≥ the pinned `footprint_mib` (refused if unset); CPU fallback stops both; the route is recorded. The probe records loaded telemetry before any assertion, adds a `-ngl 0` CPU control (≥ 2× slower) for route (ii), exits 1 on STOP and reports the footprint to pin. No verbosity flag added (not verifiable offline). Build pin format `version: 0.7.0-dev (build 1, commit 620d222)`; the working deepthought build recipe is in the handoff.
- **Tests:** paper 327 passed / 1 failed → 359 passed / 1 failed → 384 passed / 1 failed after the review fix (same known `test_real_runner_desktop_dryrun`); harness 427 passed / 9 failed / 1 error → 434 / 9 / 1 (same failing set).
- **Questions for the author:** one manager per TITAN (open; options and their needs in the handoff); `ctx_size` 8192 is a proposal (prompt lengths unmeasured); bit-repeatable same-seed retries would need `cache_prompt: false`; which GGUF is pinned; build pin = the `version:` line (or also the full commit); harness `264011e` must reach `r1` before a launch.

## 25 October 2026 — climate reserve measured: qualifies (PILOT); stop before Phase 4

AI-assisted by GPT-6 (Codex). **PILOT, not evidence.** `openml_climate` (OpenML 1467) fresh complete attempt: **552 unique runs, 0 failures, 0 missing metrics**, 30 seeds per condition on all six configurations, all six default/repeat metrics identical. Adopted D21 rule: **qualifies**, 3 material edits, mean P(wrong) **0.2907157594**, σ_joint **0.0399363099**, δ_n **0.0050897867**. Independent raw-pair rule agrees; paired bootstrap P(qualifies)=0.9055 (reported, not decisive). Four CPU workers, no LLM/GPU, 228.4 s.

The first attempt STOPped at 348 records on Ceph file quota and lacks a manifest; it is preserved unchanged, excluded and never resumed or pooled. A fresh full attempt changed only output/scratch to local /tmp. Same paper `3d3ec48`, preparation harness `7305434`, locked metric libraries; Python 3.13.15 versus the unavailable reference patch 3.13.16 is explicitly recorded. Durable, hash-verified complete records: `results/r1/pilot/E1_CLIMATE_DT_20261025_ATTEMPT02/` on the author's Mac. Report: `reports/NOISE_FLOOR_CLIMATE_20261025.md`.

Final test coverage addendum: five LightGBM skips were a missing optional Narwhals helper. The isolated test copy with Narwhals 2.27.1 ran the full C3-arms module: **10 passed**; locked metric-library versions remained unchanged. This does not clear the unresolved retry/resume integration gate.

No Phase 4 configuration work, node substitution, final sweep-pin adoption, real D28 run, sweep, or authorization note. Batch B and the runner test gate remain unresolved. The requested stop before Phase 4 is reached.

## 25 October 2026 — independent Phase 2 preparation performed; runner test gate blocked

AI-assisted by GPT-6 (Codex); ENGINEERING_ONLY. Fresh paper main `3d3ec48`; preparation harness `7305434` from the Batch A handoff, imported as an exact committed bundle because it was not published. The final C3 sweep pin was not changed or accepted. Python 3.13.15 (3.13.16 unavailable through uv); locked sklearn 1.8.0 / numpy 2.4.4 / pandas 3.0.3 / scipy 1.17.1 verified. Seven OpenML caches pass network-disabled checks; the two bundled/generated nodes also load offline. Climate metadata matches; no code correction.

Initial paper suite: 317 passed / 5 failed / 6 skipped. Bounded unchanged-assertion integration retries: watchdog passed, retry still exceeds 75 s and interrupted-root archive assertion remains unresolved; no fourth retry of the exhausted item. Quota-induced live-golden failure passed in local scratch. Harness: 427 passed / 9 failed / 1 error, with an explicitly recorded difference in the artifact failure set. **No baseline acceptance or sweep readiness claimed.**

Ceph file-count quota interrupted temporary writes despite ample byte space. New scratch moved to local /tmp; only inventoried task-created package/bytecode caches were cleared, preserving source, environments and every run record. The independent climate PILOT continued separately. Report: `reports/DT_PREPARATION_20261025.md`. Batch B/source/pin/test recheck remains required; stop before Phase 4.

## 25 October 2026 — Deepthought Phase 1 retry passed (ENGINEERING_ONLY)

AI-assisted by GPT-6 (Codex). Author revised offload acceptance and explicitly authorized engineering retries. Same source/GGUF pins; added verbose logging and saved loaded GPU/PID telemetry before acceptance. GPU 0 and GPU 1 each logged **29/29 layers offloaded**, with 4,920 MiB held per server before acceptance. GPU 1 loaded while GPU 0 remained resident. Twenty synthetic manager requests averaged 7.2609 s, 91.65 output tokens, 250.73 prompt tokens/s and 24.87 generation tokens/s. Three seeded temperature-0.2 responses were identical. Two one-token probes completed. Projection: 11.70 hours for 5,800 calls, inference only; worker/audit costs excluded. Both owned servers exited cleanly; prior STOP preserved. Report updated: `reports/LLAMACPP_PROBE_DT_20261025.md`.

Phase 1 complete; no D28 or sweep evidence run. Current scope continues with Batch B–independent Phase 2 and climate Phase 3, then stops before Phase 4. Raw retry records stay on the host; only report/STATUS are pushed.

## 25 October 2026 — Deepthought Phase 1 STOP: build and GGUF verified, full offload unproven

AI-assisted by GPT-6 (Codex); ENGINEERING_ONLY, not evidence. Phase 0 complete (`7a8ee19`). Built unmodified llama.cpp `v0.7.0` @ `620d2225cc436ab0b001e3200e590e3b286ef9ab` for sm_52 with CUDA 11.8 and installed GCC 13 C++ compiler (CUDA host compiler GCC 8; explicit iomanip include flag). Both binaries build. Official Qwen2.5-Coder-7B-Instruct Q4_K_M GGUF SHA-256 `509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c` verified twice. Original GCC 8 server build failure preserved.

- STOP: GPU 0 server loaded and became healthy, but its log lacked the required full-offload line. The standalone probe recorded STOP before any completion request; no throughput, determinism or GPU 1 check. Loaded VRAM was not captured before the assertion (agent instrumentation error). No retry.
- Diagnosis without model load: all four CUDA devices enumerate and CUDA dependencies resolve. Missing log does not establish offload failure; its cause remains unconfirmed. Draft verbose probe prepared and syntax-checked, not executed.
- Cleanup: only owned PID/process group 3546902 signalled after command validation; exited cleanly. Final GPUs 0 MiB used and no compute processes; Ceph about 303 TiB free.
- Report: `reports/LLAMACPP_PROBE_DT_20261025.md`. Hashed raw logs/scripts remain local; automatic approval review rejected publishing the full bundle, so this push includes summary documentation only. Phase 1 incomplete, Phases 2–9 unstarted. Author continuation required for the proposed verbose load attempt. Batch B on origin/main remains a prerequisite for Phase 2.

## 25 October 2026 — Deepthought Phase 0 census complete

AI-assisted by GPT-6 (Codex); ENGINEERING_ONLY. Author continuation explicitly permits Phases 0–1 before Batch B is merged, superseding the orientation missing-handoff STOP for these phases only. Census: four idle TITAN X GPUs (5.2), driver 525.147.05, installed CUDA 11.8.89, 40 CPUs, 503 GiB RAM, about 303 TiB free on Ceph; GitHub/Hugging Face/PyPI/OpenML HTTP 200. No GPU/LLM run yet. Report: `reports/DT_HOST_CENSUS_20261025.md`. Next: Phase 1 build and probe; Phase 2 remains gated on Batch B on origin/main.

## 25 October 2026 — Deepthought execution STOP before host census

AI-assisted by GPT-6 (Codex); ENGINEERING_ONLY, not evidence. The author requested execution of the Deepthought llama.cpp/liveness/C3 runbook. Its required `overnight/BATCH_B_25OCT_HANDOFF.md` is absent, triggering its explicit missing-file STOP. Published `origin/main` was verified at `3d3ec488be5e1cdcb12ee66b8130305fc9c7db26`; no published `batch-b-25oct` ref was returned. The active local Batch B changes remain uncommitted and untouched.

- Report: `reports/DT_ORIENTATION_STOP_20261025.md`, on branch `dt-sweep1-20261025`.
- Checks: required reading and Git publication checks only. No SSH, host census, remote changes, GPU/LLM/worker run or evidence collection. No tests for this documentation-only STOP.
- Not done: Phases 0–9; the required handoff and merged backend are unavailable.
- Coordinator action: finish/review/publish Batch B with its handoff and merge it into main. Author continuation is needed after this STOP; sweep evidence still requires the separate author-committed authorization note.

## 24–25 October 2026 — Phase A coding batch: A.4, A.5, A.8, A.6 draft (AI-assisted; ENGINEERING_ONLY; reviewed and merged)

Review by the coordinating session (Claude), 25 Oct: re-ran the new table, deepthought-config and resume tests (12 passed + 1 skipped; 16 passed) and the three end-to-end dry runs including kill-and-resume and the watchdog (3 passed, 134 s; they need TMPDIR on a disk with free space). Read the orphan-stop code: a process is signalled only if pid, process group, port and models directory match the batch record; another user's process is never signalled. Fast-forward merged into main. The open questions in the handoff are for the author.

Implementation agent (Claude) on branch `batch-a-24oct` (paper repo, from `42c93f6`); not merged, not pushed; harness unchanged. No LLM, GPU, SSH or real Ollama. Details, fail-before evidence and the deepthought checklist: `docs/r1/overnight/BATCH_A_24OCT_HANDOFF.md`.
- **A.4 (`62571dc`):** `python -m r1.c3.dataset build-sweep --index <index or batch dir> --out DIR` builds the C3 table from a completed sweep. On fixture indexes over the 19 Oct pilot ledgers it reproduces `build()` byte for byte, and the 19 Oct split-recheck rows apart from the 22 Oct `noop_kind` field.
- **A.5 (`c560ef9`):** an interrupted sweep phase resumes on `--start <batch>`: completed roots kept, started roots re-run whole (partial attempts archived), each interruption logged (batch, step and runner logs, sweep directory). The orphaned Ollama of the batch is stopped only after pid, process group and environment match. Dry run: SIGKILL mid-campaign, then restart → batch completes, completed roots unchanged.
- **A.8 (`c560ef9`, opt-in):** watchdog for the dedicated Ollama (exit/signal, unresponsive, model unloaded): records the loss, restarts the instance, re-runs affected roots. Dry run: server SIGTERM mid-request → recorded and recovered. Deepthought smoke not done (needs the host).
- **A.6 draft (`8fe3416`):** `r1/scripts/configs/c3_sweep_deepthought.json` with seven `TODO_VERIFY_ON_DEEPTHOUGHT` values; the runner refuses such values at launch; `--check-config --allow-placeholders` passes locally.
- **Tests:** paper 296 passed / 1 failed → 327 passed / 1 failed (same known `test_real_runner_desktop_dryrun`); harness 427 passed / 9 failed / 1 error, unchanged.
- **Questions for the author:** which host is deepthought (RUNBOOK says deepthought2 with TITANs; STATUS 12 Oct says deepthought2 has L40S, deepthought has TITAN X); TITAN X on driver 525 has no demonstrated Ollama offload; one manager per TITAN needs four batches or a multi-instance runner; the Paper A check on deepthought; watchdog default; `min_live_nodes` 2 vs the planned eight nodes.

## 24 October 2026 — author decisions recorded; runbook rewritten

Recorded by an AI agent (Claude, coordinating session) at the author's request. No experiment ran.

- PLAN §10, new 24 Oct block: R1-C3-BASE (Kev and StartLux main, Laya rung, ≤ 4B), R1-HOSTS, R1-COMPUTE (revised: Mac as last resort only), R1-SWEEP-HOST (deepthought; no mixing hosts within one table), R1-C1-FLOOR (common 30-seed run accepted as the C1 table), R1-VENUE-3 (ICML 2027; only the venue changes), R1-BENCH-HARD (autoresearch, 1GC-7RC, MLGym added; role open), R1-PROPOSER-QUANT (Q4_K_M; ceiling ≈ 27B dense to 35B-A3B MoE).
- RUNBOOK.md rewritten for the post-18 Oct plan (route A ladder, C3 gate, D21 pool of eight): Phases A–E, Track G, host table, immediate queue. The 12 Oct L/E step lists are superseded; their completed work stays recorded below.
- C3_DESIGN §5 A5 row: base models per R1-C3-BASE. README venue line updated.
- Next (RUNBOOK §5 queue): coding batch A.4 / A.5 / A.8 on the Mac; A.1b climate fetch (author's terminal: the agent VM cannot reach OpenML); A.6 → A.7 → A.9 → sweep 1 (deepthought; the agent VM cannot reach it).


## 22–23 October 2026 — common 30-seed noise floor over ten nodes (accepted); D21 pool = 8

AI-assisted: run and report by a Claude subagent; verified, merged (`8aa9a5f`) and wired in by the coordinating session (Claude). PILOT pending the author's acceptance as the C1 noise-floor table (`reports/NOISE_FLOOR_COMMON_20261022.md`; `results/r1/pilot/E1_20261022T214606Z/`). No LLM, GPU or SSH.
- **Run:** 5,520 runs, 0 failures, 0 missing metrics; 30 seeds per condition on every node; 21.6 min on 4 workers. Environment: harness-locked venv (Python 3.13.16, scikit-learn 1.8.0, pandas 3.0.3, numpy 2.4.4), recorded in the manifest. Determinism re-check identical. The 12 Oct E1 runs reproduce bit-for-bit (1,152/1,152); the 22 Oct `credit_approval` re-measurement under scikit-learn 1.9.1 differs on tree models, verdict unchanged.
- **D21 rule applied as adopted** (≥ 2 material edits, mean P(wrong) ≥ 0.10, σ_joint > 0, 30 seeds; bootstrap reported only). Verdicts re-derived independently from the raw runs by the coordinating session: identical. `e1_report`'s extra label "more seeds needed" is not part of the rule; such nodes are reported as "does not qualify".
- **Qualify (8):** `digits_mlp` (mean P(wrong) 0.101; bootstrap 0.48), `tabular_mlp` (0.125), `openml_breast_w` (0.233), `openml_ionosphere` (0.195; δ_n 0.004), `openml_wdbc` (0.174), `openml_credit_approval` (0.229), `openml_sonar` (0.196; δ_n 0.0032), `openml_blood_transfusion` (0.103; bootstrap 0.48). **Do not qualify:** `openml_credit_g` (1 material edit; its C ×0.5 edit at Δ̂ = 0.00195 is just below 0.002), `openml_qsar_biodeg` (0). Pool = 8, exactly the PLAN target, no margin; two nodes are borderline.
- **Wired in (`main`):** `r1/c3/dataset.py` `E1_SUMMARY` → the common run (newly built C3 tables use its σ_node and δ_n; the 19 Oct pilot table keeps its build-time values, so the pilot gate numbers are unchanged); sweep `D21_NODES`, liveness `DEFAULT_RUN_NODES` and `r1/scripts/configs/c3_sweep_ada.json` → the eight nodes (`nodes_pending` emptied); `e1b_collect` now defaults to this run. Tests: 296 passed (tests pinned to the 12 Oct E1 now name it explicitly; a new test checks the default source).
- **Sweep size:** 8 nodes × 18 instances × 2 memory modes × W = 20 (was 5 nodes in the config) — about 5,800 manager proposals before liveness exclusions.

## 22 October 2026 — author adopts the D21 rule (30 seeds) and the pool extension

Recorded by an AI agent (Claude, coordinating session). No experiment ran. PLAN §10 rows "D21 rule", "D21 uniform application", "D21 pool" and "D21 common measurement" (22 Oct): 30 seeds for every node; ≥ 2 material edits with mean P(wrong) ≥ 0.10; bootstrap reported, not decisive; applied to all nodes including the original five; `credit_approval` added, `diabetes` dropped; candidates `credit_g`, `sonar`, `blood_transfusion`, `qsar_biodeg` (OpenML IDs verified). Next: build the three new harness nodes (subagent), author fetches four data caches on the Mac, then one 30-seed run over ten nodes.

## 22 October 2026 — C3 preparation batch and 30-seed noise re-measurement (accepted, merged)

AI-assisted: two Claude subagents in separate worktrees; reviewed, corrected and merged by the coordinating session (Claude). No LLM, Ollama, GPU or SSH. Merges `06f5faa` (code, ENGINEERING_ONLY) and `554ba3e` (noise, PILOT) on `main`. Tests: 290 passed (baseline 248), 1 deselected (known environmental dry-run test).
- **Gate at the declared g only.** `offline_eval` computes g ∈ {0.1 (primary), 0.05, 0.2} σ_node; `gate_verdict` is the only verdict (g = 0.1, primary run accounting, instance split). On the 19 Oct pilot it reproduces the old 0.1σ values exactly: digits +0.0051 [0.0018, 0.0086], tabular +0.0016 [−0.0008, 0.0037], breast-w −0.0006 → fail. Not a gate decision (tiny pilot).
- **Run accounting.** Primary as decided. Freed-run sensitivity: the subagent's uncapped variant scaled with 1/exec-rate (digits +0.039); replaced at acceptance by an LLM-call cap c × W (c = 1 = primary; c = 2 reported: digits +0.0103 [0.0037, 0.0172], tabular +0.0033 [−0.0017, 0.0073], breast-w −0.0012; c = ∞ upper bound). PLAN row wording corrected (literal replay impossible: one proposal per run in root ledgers).
- **C1 duplicate rate** (`r1/c3/duplicate_report.py`; `reports/DUPLICATE_RATE_PILOT_20261022.md`, PILOT): 841/1,323 rule-detectable; memory-on duplicates 51–66 % (9.7–12.5 wasted runs per 20); DT4 digits memory-off 77 %; all 114 no-ops are inactive-key edits on ionosphere.
- **DI audited mode** (`di_test.py --immediate audited`): default outputs byte-identical. PILOT: memory-on tabular residual −0.00122 → +0.00004 [−0.00120, 0.00093] with audits (13/13 points); memory-off digits +0.00051 → −0.00003. Both undetermined; audit noise is not in the CI.
- **Audits K = 10** (7001–7010, 5 label + 5 evaluation); K = 6 pilot audits still split 3 + 3.
- **Paper A coordination** (`r1/scripts/paper_a_status.py`): refuses unless evidence shows Paper A running on its card or finished; its Ada config has null entries that must be verified read-only on Ada first (handoff lists 7 checks).
- **Sweep config** `r1/scripts/configs/c3_sweep_ada.json`: 5 D21 nodes, 18 instances × W = 20 × both memory modes, own Ollama port 11481, K = 10; `--check-config` passes; desktop DRYRUN passed (`results/r1/engineering/c3_sweep_dryrun_20261022T103215Z/`). Ionosphere kept (passed D28 on 14 Oct; the 19 Oct exclusion concerns only the DI-test pool). A node that fails D28 is dropped from both memory modes; for digits the memory-off choice stays with the author.
- **Acceptance fix:** the C3 pipeline did not know `openml_wdbc` or `openml_credit_approval`; added, with the D25 projection read per node (imputer active on credit-approval) and checked against the harness configs; original node codes unchanged (rebuilt pilot table byte-identical).
- **Noise re-measurement** (`results/r1/pilot/E1_remeasure_20261022T100942Z/`, `reports/NOISE_REMEASURE_20261022.md`, PILOT): 1,104 runs, 0 failures, 300 s. Under E1's (still unadopted) D21 rule, `credit_approval` qualifies (mean P(wrong) 0.09 → 0.24; bootstrap 0.87); `diabetes` has no material edit (bootstrap 0.03). δ_n = 0.002 (floor) on both. Tree-model metrics differ from E1 under scikit-learn 1.9.1; logistic regression reproduces bit-for-bit. Acceptance fix: the comparison script wrote temporary paths; now byte-reproducible.
- **Post-merge fix (`4ae3b8a`):** `e1b_collect`'s default E1 glob also matched `E1_remeasure_*` (two nodes only), so `digits_mlp` lost its noise entry and 3 tests failed on `main`; it now matches full `E1_<timestamp>` runs only. After the fix: 290 passed on `main`.
- **Open for the author:** (1) add `credit_approval` to D21, drop `diabetes`; (2) pool is 6 of ≥ 8 — fetch `credit_g` on a networked machine and choose 2–3 further OpenML datasets; (3) re-measure the five D21 nodes at 30 seeds for a common footing (~15 CPU-min); (4) adopt or amend E1's D21 threshold (mean P(wrong) ≥ 0.10 over ≥ 2 material edits).
- **Still to do before the Ada sweep:** adapter from the sweep index to `dataset.build`; read-only Ada checks (Paper A config, seeded models path, port); `digits_mlp` repair and D28.

## 22 October 2026 — author decisions before the first C3 label sweep

Recorded by an AI agent (Claude, coordinating session). No experiment ran. All rows are in PLAN §10, dated 22 Oct.
- **Duplicates (option A):** confirms the 19 Oct duplicate ≠ no-op split; duplicates are excluded from learned-arm training and evaluation; new: C1 reports the duplicate rate as wasted runs.
- **g (option A):** g = 0.1 σ_node primary, {0.05, 0.2} σ_node declared sensitivity; the gate is judged at the primary value only. C3_DESIGN §1 updated.
- **Run accounting (option A):** skips credited at g; freed runs not re-spent in the primary analysis; replay as sensitivity.
- **Node pool:** credit_approval and diabetes after a 30-seed `"vary"` re-measurement; credit_g after fetching its cache; 2–3 more OpenML datasets if fewer than 8 qualify.
- **`digits_mlp`:** repair, do not exclude; out of memory-on collection until D28 passes.
- **Next:** implementation batch (classification of kinds through labels and arms, g and run accounting in the gate, audited-outcome mode for `di_test.py`, Paper A status command, sweep config) and the noise re-measurement, run by subagents and accepted by the coordinating session.

## 19 Oct 2026 — partial memory-on absolute-metric DI diagnostic

AI-assisted by Codex. **PILOT, PARTIAL, not evidence.** The authorised preserved arm snapshot is 11.99 MB, with lossless compressed ledgers and source SHA-256 manifests; two whole failed points are excluded. No experiment was resumed and no LLM, GPU or worker was run. Memory-on tabular has nine promotion points and four demotion points; its next-one absolute-metric contrast passes the combined diagnostic rule and the value residual is −0.00122155 [−0.00222152, −0.000257005]. Verdict: **violated in value terms**, limited to this exploratory partial diagnostic. Memory-off absolute-metric re-analysis: **undetermined at this sample size**, residual .000510569 [−.00258821, .00417810]. The shared ionosphere node has no changed points in either dataset. These results do not justify A7 training/deployment. See [report](reports/DI_TEST_MEMORY_ON_PARTIAL_20261019.md) and [tables](reports/DI_TEST_MEMORY_ON_PARTIAL_20261019_tables.md). The default legacy outputs remain byte-identical; focused file-only regression suite: 12 passed.

Newest entry first. Only this file says what is done.

## 19 Oct 2026 — rerun-2 diagnosis, digits liveness, and E1b DI diagnostic

AI-assisted by Codex; ENGINEERING_ONLY / PILOT; not evidence. Author-authorized file-only diagnosis in the fresh Ada clone, incorporating addendum `bf52f5c` and the later observed-record/revised-stop-rule instructions. No LLM, GPU, worker runs, retries or writes to preserved results.

- **Task 1 (ENGINEERING_ONLY):** all seven collection-failure leaves coincide with Ollama runner SIGTERM during proposal requests (five runner-unavailable errors, two unexpected EOFs). Signal sender/reason is not recorded. Failures occurred in branches, but shared-service loss can also affect root-only C3. Proposed lifetime/observability fixes and a mocked desktop fixture only; no fix implemented. Report: `reports/RERUN2_STOP_DIAGNOSIS_20261019.md`.
- **Task 2 (ENGINEERING_ONLY):** digits memory-on has no keep after trial 1; 10 later ties and 8 worse scores, with repeated edits. Keep the node as a candidate with proposer/liveness repair; retain its exclusion from memory-on collection until it passes the existing D28 gate. A lucky-incumbent or causal memory explanation is not identified. Same report, “digits_mlp liveness”.
- **Task 3 (PILOT):** observed decision changes are 12 promotions at six digits points, zero demotions; digits has 24 unchanged point-repetitions, ionosphere 36 unchanged. The next-three mean-delta distance exceeds paired null by 0.00495217 (95% cluster interval [0.00123811, 0.00968352]) and unchanged by 0.00607417 ([0.00227162, 0.0107627]); adjusted exploratory p=0.0006. The requested empirical DI criterion flags a memory-off deviation; conditional-law identification and A7 benefit remain undetermined. Ionosphere is excluded from the eligible pool. No scripted per-trial control exists; none was regenerated. Reports: `reports/DI_TEST_E1B_20261019.md`, `reports/DI_TEST_E1B_20261019_tables.md`.
- Deterministic committed-input CLI: `r1/diagnostics/di_test.py`; synthetic/integrity tests: `r1/tests/test_di_test.py` (5 passed). Full r1 suite not run: harness unavailable in the isolated analysis environment. Diagnostic artifacts remain ENGINEERING_ONLY / PILOT, not scientific acceptance, deployment approval or authorization for the proposed memory-on follow-up.







## 19 October 2026 — duplicate ≠ no-op split implemented

Recorded by an AI agent (Claude, coordinating session), at the author's decision (PLAN §10, 19 Oct). ENGINEERING_ONLY.
- **Theory:** T4 §1 now has separate no-op (I_n) and duplicate (D_n) events. Corollary 8a is revised, with a new part (iii): under ρ a duplicate can never be kept, because the record is monotone.
- **Code:** `r1/c3/` gains `noop`, `duplicate`, `rule_skip` and `known_metric` (`inert` remains the alias of `noop`). Duplicates are excluded from training and skipped by the rule layer. Offline evaluation charges an A1/A0 keep of a duplicate its audited Δ or the logged proxy, and counts such keeps. C3 tests: 39 passed, including a new duplicate test.
- **Pilot re-check** (`results/r1/engineering/c3_split_recheck_20261019/`; table rebuilt from the same ledgers, same audits).
  - 1,323 proposals: 727 duplicates, 114 no-ops, 482 other.
  - The maximum Δ̂ over the duplicates is exactly 0, as Corollary 8a(iii) predicts.
  - The gate quantity is unchanged in substance (not passed). At g = 0.1σ: digits +0.0051 [0.0018, 0.0086]; tabular +0.0016 [−0.0008, 0.0037]; breast-w −0.0006.
  - A1 (no rule layer) keeps up to 92 duplicates at g = 0, because a positive constant prior gives t* < 0. This is the failure the rule layer prevents.

## 19 October 2026 — overnight build merged (ENGINEERING_ONLY)

AI-assisted: four Claude subagents worked overnight, coordinated and merged by the coordinating session (Claude). Each worked in its own git worktree; the merges are `86380c2`, `e249a0f`, `d59d77b` and `3c84170` on `main`, and harness `r1` was fast-forwarded to `4d68c54`. No LLM, GPU, SSH or Ollama was used; workers ran on CPU only. Nothing here is evidence. After merging, the new C3/T5/DI/runner tests pass on `main` (113, with Python 3.13 in the VM).
- **C3 offline pipeline** (`r1/c3/`; handoff `docs/r1/overnight/C3_OFFLINE_HANDOFF.md`; report `docs/r1/reports/C3_OFFLINE_PILOT_20261019.md`).
  - Built: T4 rules; 12-bin soft labels; features with ledger replay; CPU audits; arms A1–A3; offline one-step evaluation; the C3 gate.
  - Pilot: 166 proposals audited (672 runs, 0 failures; ≈ 4.7 run-seconds per proposal).
  - Gate quantity on this tiny sample: not passed. Digits passes but has only 6 instances; tabular +0.0021 [−0.0002, 0.0040]; breast-w ≈ 0. Sharing audit seeds between labels and evaluation makes the gate pass spuriously, so separate seeds are required.
- **T5 simulation** (`docs/r1/theory/T5_SIMULATION.md`; `results/r1/engineering/T5_20261019T004918Z/`).
  - Propositions 7–9 are confirmed in the model (Proposition 7 realised/predicted ratio 0.98–1.02 under DI). Under DI, myopic acceptance is never beaten; under the modelled violations it loses ≤ 0.54 δ_n.
  - Only audited increments over each branch's own incumbent are a clean DI outcome.
  - C3 headroom in the model: memory-on oracle 1.35–2.4 δ_n; a calibrated predictor keeps 0.76–1.06 δ_n; an uncalibrated one is worse than the constant prior.
  - The sign of route D depends on whether the suppressed bold edits are good: it must be measured.
- **DI verdict revised:** the memory-on "violated in value terms" is withdrawn as proxy selection bias (addendum to `DI_TEST_MEMORY_ON_PARTIAL_20261019.md`). Both memory modes are undetermined.
- **Novelty full text** (`docs/r1/inputs/NOVELTY_FULLTEXT_20261019.md`): no threat to the core. Pre-execution skipping and re-proposal of rejected candidates are published, so those claims are narrowed (C3_DESIGN §10). Quotes were read via a summarising fetch tool and a mirror; check each against the PDF before the manuscript.
- **Harness and runner** (`docs/r1/overnight/HARNESS_AND_RUNNER_HANDOFF.md`).
  - Harness: D4 action versions (Bayes keep rule, posterior-mean verify, `verify_failed` keeps the original decision); `"vary"` default for new manifests; bounded transport retry. All are backward-compatible: legacy records are identical when the options are unset.
  - Paper: collector observability; dedicated Ollama instance per batch; the C3 label-sweep runner with a Paper A coordination gate (refuses unless Paper A is not waiting for a card); a desktop dry run with fault injection (retry and permanent-loss scenarios passed).
  - Tests: harness 421 passed, 10 pre-existing environmental failures; paper 193 passed, 1 pre-existing failure.
- **Open:**
  1. Author decision: duplicates of earlier non-incumbent configurations are not zero-increment (727 of 841 rule-inert proposals). The inert ⇒ Δ = 0 wording in T4 §1, the labels and the A0/A1 value levels must distinguish "duplicate (known result)" from "inactive edit (Δ = 0)".
  2. Declare g before the gate.
  3. Model the runs freed by skipping in the 20-run scaling.
  4. Add an audited-outcome mode to `di_test.py`.
  5. Before an Ada C3 sweep: write the real Paper A status command and the sweep config (pinned models dir, nodes, GPU); make sure the OpenML data caches exist in the batch harness; repair and re-check `digits_mlp` (D28). The SIGTERM source is still unknown.

## 19 October 2026 — DI review; memory-on partial-arm diagnostic authorised

Recorded by an AI agent (Claude, coordinating session).
- **Review of `DI_TEST_E1B_20261019` (Codex, `7b81e1c`).** The flagged memory-off contrast in next-3 mean Δ̂ (+0.0047 at the 12 changed point-repetitions, all promotions) is mainly a record-reference shift: the verify branch's record is 0.0051 lower after a promotion. In absolute metric the signed shift is +0.0016. Addendum and `r1/diagnostics/di_record_shift.py` committed in `1840efe`. Verdict: undetermined, not "violated".
- **Rerun-2 stop (Codex diagnosis):** the shared Ollama runner received SIGTERM (source unknown); 7 of 648 arm-A leaves failed. It can also affect root-only C3 sweeps. Proposed fixes before the C3 label sweep: a dedicated Ollama instance per batch (own port and model dir); bounded retries for transport-level LLM request failures, logged in the ledger; tracebacks and timestamps persisted by the collector.
- **`digits_mlp`:** keep conditionally; repair the proposer and re-run D28 before use.
- **Author rule (PLAN §10, R1-COMPUTE Paper A coordination):** no Paper B GPU launch on Ada while a Paper A live campaign there is waiting for an idle card. CPU-only and file-only work is unaffected; otherwise wait or use Deepthought.
- **Author authorisation (PLAN §10, 19 Oct):** snapshot and analyse the preserved partial arm A (memory on) as a PILOT DI diagnostic, using absolute metrics and a value-residual check. Prompt `docs/r1/prompts/ADA_DI_TEST_MEMORY_ON_PARTIAL_PROMPT.md`.

## 18 October 2026 — add-on placement: B joins C2, D becomes C4

Recorded by an AI agent (Claude, coordinating session). The author agreed that route B (the T4 theory of the gain) is part of C2, with its empirical checks reported alongside C3, and that route D becomes **C4 (secondary): proposer feedback** — the DI test on forced-decision branch pairs plus the debiased-memory A/B. PLAN §3 (current-contributions box) and §10 (R1-C4), `C3_DESIGN.md` §7 and the README were updated. No experiment ran.

## 18 October 2026 — author adopts the open Phase 0 decisions, the C3 ladder and the C3 gate

Recorded by an AI agent (Claude, coordinating session). The author adopted every recommendation put to them on 18 Oct (D4 amendment allowed; D21 node set plus pool extension to ≥ 8 nodes; `"vary"` split on every node; D18 δ_n; D23 constant-prior KG index policy as arm A1; R1-E1B-RERUN2 converted into the C3 label sweep), and fixed C3 as route A with the A0–A6 ladder and the C3 gate. All are PLAN §10 rows dated 18 Oct. No experiment ran.

- **Next actions:**
  1. read the rerun-2 collection-failure cause on Ada;
  2. implement the D4 action versions (Bayes threshold; posterior-mean verify response; `verify_failed` keeps the original decision) and the `"vary"` default on the harness branch `r1`;
  3. build the audit pipeline and the C3 label sweep;
  4. run the DI test on the existing E1b LLM branch pairs;
  5. extend the node pool (D21);
  6. diagnose `digits_mlp` liveness.

## 18 October 2026 — C3 route adopted; legacy code archived; T4 theory and C3 design drafted (ENGINEERING_ONLY)

AI-assisted by Claude (coordinating session) at the author's request. Nothing here is evidence. Uncommitted working-tree changes on the author's Mac; no commit or push was made.

- **Author decision R1-C3** recorded in PLAN §10: C3 is the learned per-proposal prior under the C2 rule. Design proposal `docs/r1/C3_DESIGN.md`.
- **RUNBOOK 0.1 legacy code:** moved with `git mv` to `archive/old_b_2026-10-09/code/` (list in PLAN §10). `r1/` imports none of it (checked by grep). Legacy suites before the move, from the root: 212 / 6 / 12 OK; after the move, via `make legacy-test`: 212 / 6 / 12 OK. Both runs used Python 3.13.15 in a scratch uv venv with `requirements.lock`, because the Mac's `.venv` is not usable from the Linux shell. The root `Makefile`, `README.md`, `pyproject.toml` (testpaths → `r1/tests`) and `.gitignore` paths were updated; `archive/old_b_2026-10-09/code/Makefile` keeps the test targets. The old `paper-b`, `smoke-b`, `release-b` and `check-release-b` targets were not carried over. `make r1-test` was not run: the harness checkout is not reachable from this session.
- **Theory T4** (`theory/T4_FEEDBACK_PROPOSER.md`, Propositions 6–10): per-proposal Bayes rule under a ledger-dependent proposer; exact gain of a per-proposal over a constant prior; screening under a run price; winner's curse for every adaptive proposer; decision independence ⇒ myopic optimality, with a counterexample. The closed forms of Propositions 7 and 9 were checked against Monte Carlo (agreement to MC error). The proofs are unchecked by the author.
- **Offline premise check for C3** (ENGINEERING_ONLY; script on the Mac VM at `~/scratch/offline_a.py`, not committed):
  - 39–77 % of LLM trials repeat an evaluated configuration; 9–14 % are bit-identical to the incumbent;
  - informative increments differ by edit type (`digits_mlp` `BATCH_SIZE` −0.012, n = 94; `HIDDEN_UNITS` +0.004, n = 181);
  - with memory on, 24 % of informative proposals improve.

  Small samples; single-campaign Δ̂.
- **Novelty sweep part 2** (`inputs/NOVELTY_SWEEP_PART2_20261018.md`, AI-assisted, abstract-level): no work combines an LLM proposer, noisy incumbent-relative acceptance and a learned per-proposal prior. The nearest 2026 works are SAGE (2609.36043), FOREAGENT (2601.05930) and Beneath the Diff (2609.00077). C2-i (Bayes threshold) and C2-ii/v (verify VoI) are classical and are to be presented as instantiations. C3_DESIGN §10 was revised accordingly.
- **Still open:** D18, D21, D23, the D4 amendment, the verify split policy, the C3 gate, and whether to re-run or redesign R1-E1B-RERUN2 (stopped 14 Oct on collection failures; cause not yet read from the Ada logs).

## 14 October 2026 — R1-E1B-RERUN2 (PILOT): stopped

AI-assisted execution by Codex (AI-assisted). All outputs are PILOT or ENGINEERING_ONLY; none is evidence.

- **Execution host:** `ucrtasl`. Logs and preserved runtime state: `/data1/dowling/tmp/r1_e1b_rerun2_ENGINEERING_ONLY_20261014_X7Qyse/`.
- **Harness:** `411c6054c8505f93a6429e2f9eed526952793882`; manager `qwen2.5-coder:7b`, pinned digest `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`.
- **GPU / offload:** `2, GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154, NVIDIA RTX 6000 Ada Generation, 48427`; `{"full_offload": true, "host": "ucrtasl", "keep_alive": -1, "probe_tokens_max": 1, "size": 5560907776, "size_vram": 5560907776}`.

- **preconditions:** `{"completed": true, "completed_utc": "20261014T140742Z", "started_utc": "20261014T140727Z"}`
- **liveness:** `{"commit": "b2e5cc3ce5570e9a0da9cec67f5da8b9c4795ab6", "completed": true, "completed_utc": "20261014T141051Z", "eligible_nodes": ["tabular_mlp", "openml_ionosphere", "openml_breast_w"], "excluded_nodes": ["digits_mlp"], "out": "/data1/dowling/tmp/r1_e1b_rerun2_ENGINEERING_ONLY_20261014_X7Qyse/agent_paper_B/results/r1/engineering/liveness_llm_20261014T140742Z", "started_utc": "20261014T140742Z", "verdicts": {"digits_mlp": {"active_novelty_fraction": {"equals_incumbent_trials": 0, "evaluated_trials": 20, "novel_trials": 12, "novelty_source": "events", "observed": 0.6, "required": ">= 0.5", "seen_before_trials": 8}, "invalid_rate": {"observed": 0.0, "required": "< 0.3"}, "keep_after_trial_1": {"observed": 0, "required": "at least 1 keep with budget_index > 1"}}, "openml_breast_w": {"active_novelty_fraction": {"equals_incumbent_trials": 1, "evaluated_trials": 20, "novel_trials": 13, "novelty_source": "events", "observed": 0.65, "required": ">= 0.5", "seen_before_trials": 7}, "invalid_rate": {"observed": 0.05, "required": "< 0.3"}, "keep_after_trial_1": {"observed": 1, "required": "at least 1 keep with budget_index > 1"}}, "openml_ionosphere": {"active_novelty_fraction": {"equals_incumbent_trials": 0, "evaluated_trials": 20, "novel_trials": 11, "novelty_source": "events", "observed": 0.55, "required": ">= 0.5", "seen_before_trials": 9}, "invalid_rate": {"observed": 0.0, "required": "< 0.3"}, "keep_after_trial_1": {"observed": 3, "required": "at least 1 keep with budget_index > 1"}}, "tabular_mlp": {"active_novelty_fraction": {"equals_incumbent_trials": 0, "evaluated_trials": 20, "novel_trials": 12, "novelty_source": "events", "observed": 0.6, "required": ">= 0.5", "seen_before_trials": 8}, "invalid_rate": {"observed": 0.0, "required": "< 0.3"}, "keep_after_trial_1": {"observed": 3, "required": "at least 1 keep with budget_index > 1"}}}}`
- **arm_A:** `{"completed": false, "started_utc": "20261014T141051Z"}`

**STOP:** RuntimeError: STOP: collection failures; no leaf retries permitted

E1b rerun-2 phases are accepted only where the phase entry explicitly records completion. Partial outputs are preserved; no completed phase was re-run and no interrupted phase was retried.

- **Author decisions remain open:** D18, D21, D23, the D4 amendment and any verify split-policy revision. Fixed split policy retained; L11 was not built.

## 14 October 2026 — batch 4c: launch repairs and real-runner desktop dry run (DRYRUN; review resolved)

AI-assisted implementation by Codex at the author's explicit request, including approval to execute the complete `BUILD_BATCH4C_PROMPT.md` and then start a fresh Ada batch. Production design, PLAN rows and harness pin remain unchanged. Base: paper `42f454c` (coordination documents; prior launch base `69b2bbd`); harness `411c6054c8505f93a6429e2f9eed526952793882`. Implementation/tests/evidence commit: `bb7a12c02717566ebe8338287f9f9b55afe97beb`, pushed. Independent review and its single correction round are complete; the new Ada batch has not yet been started.

- **X1:** The runner reads and validates `R1_OLLAMA_MODELS` before touching a GPU or starting a server; no missing directory or unset variable proceeds. A compiled merged-module global-name guard mirrors the exec loader and detects `MODELS` in the original `69b2bbd` sources and an injected missing global.
- **X2/X3/X5:** The launcher requires `R1_GIT_NAME` and `R1_GIT_EMAIL`, configures both fresh clones repository-locally, validates `GIT_COMMITTER_IDENT`, checks both branch pushes with `--dry-run`, installs `uv sync --extra dev`, records the pytest version and identity/setup checks in `prepare.json`, and rechecks identity/push permission at `--start`. It prints a self-check summary. It discovers Ada's already-installed `uv` in the prior batch toolchain when SSH PATH omits it; no manual package install is needed.
- **X4:** `rerun2_dryrun.py` launches the real launcher and real runner with a fake Ollama HTTP server, fake GPU census including a co-tenant, actual CPU workers, real fresh Git clones, real commits/pushes to temporary bare remotes, and an isolated tmux socket. DRYRUN requires `R1_DRYRUN=1`, a marked temporary root and local temporary remotes; it is refused on Ada and cannot push to `origin` in DRYRUN mode. The harness remains untouched.
- **Fail-before/pass-after:** Baseline paper tests: 144 passed. Five targeted regressions fail at `69b2bbd`; the before-fixes real entrypoint fixture stops on `MODELS` before inference (`results/r1/engineering/rerun2_dryrun_20261014T131354Z/`). Pre-review full `make r1-test`: **153 passed in 351.20 s**; final post-correction full suite: **158 passed in 399.89 s**; final nested clone suite: **157 passed, 1 skipped** (only recursive integration suppressed). Legacy suites with the harness interpreter: **212 / 6 / 12 passed**. Raw logs, including intermediate fixture failures and the initial wrong-interpreter legacy check, are preserved in `results/r1/engineering/batch4c_test_logs_20261014/`.
- **Passing end-to-end fixture:** `results/r1/engineering/rerun2_dryrun_20261014T135521Z/summary.json`, **DRYRUN**, elapsed **348.14 s** (pre-review passing fixture `...133616Z`, 319.61 s, also preserved). Preconditions, liveness, A, B, C, comparison and STATUS all completed. Six generated commits are present in the local bare remote; each arm's committed/regenerated analysis hashes match; fake chat calls carry integer D26 seeds; D25 inactive-key rejection occurred; restarting the completed batch refuses. No real model or GPU was used on the Mac.
- **Fixture deviations required by unchanged code:** two instances per node instead of one (`evaluate_arms` requires at least two for cross-fitting); W=6 rather than W=4, with E2 at 2 (`point_features` requires remaining budget `2*r=4` for verify). Two nodes (`digits_mlp`, `openml_breast_w`), one repetition, one audit seed. Liveness uses one instance and four worker runs only in guarded DRYRUN. An isolated loopback port replaces 11434 because the Mac's existing service already occupies 11434. Production stays at four prescribed nodes, 18 instances, W=20, E2 4/8/12, r=2, two repetitions and six audit seeds; production port remains 11434.
- **Unexercised production paths:** real Ollama inference/model files, real GPU offload/OOM/free-memory loss and wait-for-card, the two other production nodes, full scale/latency, real GitHub transport/authentication or non-fast-forward recovery, interrupted-phase recovery and long-duration monitor intervention. The one-repetition fixture cannot exercise leaf-split headroom; that calculation retains its existing unit coverage. Engineering checks do not establish node eligibility or scientific conclusions for the future Ada run.
- **Preservation:** Old Ada batch `..._20261014_nH08fo` was not resumed. Its STOP logs/state/census/env and staged STATUS patch were copied with a SHA-256 manifest into `stop_20261014T104505Z_preserved/`; the author's directly authorized repository-local Git identity repair was applied there, but its staged STOP entry was not committed or pushed. A fresh batch is required after this build/review.
- **Ada test portability:** Before fresh preparation, desktop integration was explicitly excluded on physical Ada (DRYRUN must be refused there), and pure guard fixtures were made host-independent. Simulated Ada test module: **13 passed, 1 skipped**; complete nonrecursive unit suite: **157 passed, 1 skipped**. Only tests changed; actual Ada preparation remains the host-specific gate.
- **Independent review:** `docs/r1/reviews/BUILD_REVIEW_20261014c.md` plus Resolution. One MAJOR (separate push URLs could bypass the local-only DRYRUN boundary) and two MINOR findings (module/class global-name coverage; direct liveness CLI output/work containment) were fixed in one correction round with negative regressions. No open MAJOR remains. Final full suite and DRYRUN passed after correction. Ada launch is the next authorized action; engineering success does not establish real-node eligibility.

## 14 October 2026 — rerun-2 first launch stopped before any inference (engineering defects)

Reported by the Ada operator agent (AI-assisted); recorded here by an AI agent (Claude, coordinating session). Not evidence; no experiment ran.

- Batch `/data1/dowling/tmp/r1_e1b_rerun2_ENGINEERING_ONLY_20261014_nH08fo/` on Ada.
  - `--prepare` passed its classification only after the operator installed `pytest` into the batch venv by hand: the launcher runs `uv sync` without `--extra dev`.
  - `r1-test`: 144 passed. Every harness failure was in the accepted set.
- **STOP** at `r1/scripts/ada_e1b_rerun2.py:156`: `NameError` on `MODELS`. The runner never reads `R1_OLLAMA_MODELS`, although `env.sh` exports it. In DT4 this name was defined inside `ada_rerun_dt4.py`, not in the shared helpers.
- `finish()` then could not commit its STATUS entry because the fresh Ada clone has no git author identity. The entry stays staged in that clone and was not pushed. This is the same gap the DT4 recovery hit (repository-local identity), and it was never added to the launcher.
- No Ollama server, liveness check or arm ran. Our tmux sessions are gone and the port is free. The batch directory stays as evidence; it is not resumed.
- Systemic cause: this is the third Ada stop caused by runner paths that the desktop stub tests did not execute (DT4 tables whitespace, `MODELS`, git identity). Fix batch: `docs/r1/prompts/BUILD_BATCH4C_PROMPT.md`, which adds an end-to-end desktop dry run of the real runner against a fake Ollama and a fake `nvidia-smi`. `ADA_E1B_RERUN2_PROMPT.md` is updated (git identity passed in; no manual environment changes on Ada).

## 14 October 2026 — batch 4b: second Ada accepted-failure ID in the rerun-2 launcher (ENGINEERING_ONLY)

AI-assisted execution by opencode (deepseek-v4.1-flash) per `docs/r1/prompts/BUILD_BATCH4B_PROMPT.md`; no LLM calls, no GPU, no Ada. Commit: paper `75d6911` → `f7879db` (branch `main`). One change: the rerun-2 launcher's accepted-failure set gains exactly `tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_checked_in_report_contains_all_plan_campaigns` (PLAN §10, row R1-COMPUTE (Ada environmental test exception 2)), beside the missing-`/bin/zsh` exception of 12 Oct. The launcher's Ada-only host guard scopes the set as before; every other failure still refuses `--start`, and no pattern/file/class matching was added. The harness is untouched, so `HARNESS_PIN_RERUN2` stays `411c6054c8505f93a6429e2f9eed526952793882`.

- **Tests.** Paper `r1/tests`: 141 → **144 passed**; `make test` 212 / 6 / 12 OK before and after. Fail-before: `test_ada_exceptions_are_accepted_and_start_proceeds` fails at head `7272d77` (`prepare.json.ok=False`); the patch makes it pass.
- **The four stub tests (all pass).** (a) `test_ada_exceptions_are_accepted_and_start_proceeds` — the zsh and fresh-checkout tests classified environmental on Ada, so `--prepare` records no unexpected failure and `--start` proceeds; (b) `test_ada_exceptions_are_refused_off_ada` — the same prepare.json off `ucrtasl` is refused; (c) `test_a_third_test_in_the_same_file_is_still_refused` — a sibling in the same `TestCompletenessCLI` class is refused; (d) `test_prepare_refuses_a_nonzero_exit_without_parsed_failures` — the F8 behaviour is kept.
- **Next:** `docs/r1/prompts/ADA_E1B_RERUN2_PROMPT.md` is ready to hand over; it can be run unchanged.

## 14 October 2026 — author approves a second Ada test exception before rerun-2

Planning only; recorded by an AI agent (Claude) at the author's request.

- Batch-4 review findings F7–F11 are already fixed (review Resolution). The one item still worth fixing before Ada is the launcher's accepted-failure set. The 12 Oct Ada DT0 run failed `tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_checked_in_report_contains_all_plan_campaigns` on a fresh checkout (it passes on the Mac), so `--start` would refuse.
- **Adopted** (PLAN §10): accept exactly that test ID as environmental on Ada, together with the missing-`/bin/zsh` exception. Patch prompt: `docs/r1/prompts/BUILD_BATCH4B_PROMPT.md`. Afterwards, `docs/r1/prompts/ADA_E1B_RERUN2_PROMPT.md` is handed over unchanged.

## 14 October 2026 — batch 4: D27 F3 fix, D28 revised criterion 2, R1-E1B-RERUN2 entrypoints (ENGINEERING_ONLY)

AI-assisted execution by opencode (deepseek-v4.1-flash) at the author's request per `docs/r1/prompts/BUILD_BATCH4_PROMPT.md`; no LLM calls, no GPU, no Ada batch created or launched. Commits: paper `5f650be` → `a8956ca` (branch `main`; P6 `271fc16`, P7 `9dd245c`, correction round `0cb76a3`, review `a8956ca`); harness `0f2d9e9` → `411c605` (branch `r1`; H6 `ed55297`, correction `411c605`). Independent fresh-context review: `docs/r1/reviews/BUILD_REVIEW_20261014b.md` (+ Resolution). `r1/scripts/HARNESS_PIN_RERUN2` = `411c6054c8505f93a6429e2f9eed526952793882`, on `origin/r1`.

- **Tests.** Harness: 380 passed / 8 failed / 1 error before → **389 passed / the same 8 failed / 1 error** after (the 9 IDs are the known environmental set; the launcher classifies exactly these plus the Ada `/bin/zsh` exception). Paper `r1/tests`: 109 → **141 passed**; `make test` 212 / 6 / 12 OK before and after. Fail-before shown in both repos: the new paper tests at base `5f650be` gave 5 failed / 3 collection errors, and at harness `0f2d9e9` the F3 scenario printed `config_seen_before: false` and the new D27 tests could not import the corrected helpers.
- **D27 (F3 fix).** `edit_novelty` gains `effective_config_sha256`, `active_config_sha256` (active-key projection; equal to the full configuration on undeclared nodes), `active_config_equals_incumbent` and `active_config_seen_before`. E2 snapshots store the full and active seen-hash sets at capture time and `resume_campaign` seeds them; an old-format snapshot resumes with `seen_before_resume: "unknown"` recorded on the first `edit_novelty` event, never a silent empty set. `TrialRecord` bytes unchanged (existing record test; review re-verified base-vs-head byte identity). The reviewer's lr_synthetic reproduction now yields `config_seen_before: true` and fails at `0f2d9e9`. Correction round: the configuration now covers **every editable symbol**, not only the narrow `build_effective_config` map (review F7); `HIDDEN_UNITS`/`ALPHA`/`LEARNING_RATE_INIT` edits on the MLP nodes are visible to the flags and hashes, and the E1-snapshot resume counts the replayed captured trial among the seen configurations (review F9).
- **D28 (revised criterion 2).** Criterion 2 is active-key novelty over evaluated trials (skipped trials, including `inactive_key` skips, are excluded; inactive-key rejections are a separate count); legacy ledgers without events are scored by replaying structured edits from the node's start configuration, projected with the node's current declaration; the report states `novelty_source: events | replayed`. The gate accepts only LLM-backed, memory-on liveness manifests; a memory-off `contrast` collection reuses the memory-on verdict and cannot bypass the gate with a scripted or memory-off manifest. The collector now persists root event streams (and the liveness runner archives them), so new runs are scored from events. **Offline DT4:** `openml_ionosphere` FAIL on criteria 1 and 2 (0 keeps after trial 1; novelty 0/120; invalid 0.0); `digits_mlp` FAIL on novelty only (32/120 novel; 11 keeps after trial 1; invalid 0.0), pinned after a raw-constants independent recomputation. **Scripted smoke** on the corrected harness, `results/r1/engineering/liveness_scripted_20261014T084101Z/` (ledgers force-added): digits_mlp PASS 20/20, tabular_mlp PASS 20/20, openml_breast_w PASS 19/20, openml_ionosphere PASS 18/20, **openml_wdbc PASS 19/20 (the old metric-difference criterion scored it FAIL at 7/18)**. The pre-correction smoke `...075806Z` is kept as the F7 evidence.
- **R1-E1B-RERUN2 entrypoints (built and tested, not run).** `r1/scripts/ada_e1b_rerun2.py`: six phases checkpointed in `batch_state.json` — preconditions (PLAN rows, both checkouts at origin heads, digest pin, co-tenancy card, `OLLAMA_KEEP_ALIVE=-1`, full offload with telemetry), LLM liveness (memory on, 2 instances, W=10; fewer than 2 eligible nodes is a STOP), arms A/B/C, per-arm analysis/commit/regeneration check, comparison, finish. A completed phase is skipped on restart; an interrupted phase is a STOP for the author and is never retried; a completed batch refuses to re-finish (review F10). Arm A is gated by the memory-on manifest; arm B is the declared memory-off contrast; arm C is scripted and ungated. `ada_e1b_rerun2_launch.sh`: `--prepare` (fresh paper clone at `origin/main`, fresh harness clone at `HARNESS_PIN_RERUN2`, `uv sync`, harness suite + `make r1-test`, `prepare.json` with per-failure acceptance classification incl. the Ada missing-`/bin/zsh` exception; a non-zero exit with no parsed failures is refused, review F8) and `--start` (refuses an existing `r1_e1b_rerun2` or any `r1_ollama_*` session, or unaccepted failures). `e1b_compare.py`: per arm and node/ALL ρ, `always_verify − ρ`, `kg_index − ρ`, `margin_threshold − ρ` with instance-cluster bootstrap CIs, best simple baseline, naive and leaf-split headroom, verify-changes-leaf share, mean verify − continue; the memory effect `(always_verify − ρ)_B − (always_verify − ρ)_A` as a shared-draw paired instance bootstrap; C1 waste counters (active novelty, inactive-key rejections, `config_seen_before` rate, LLM calls, parse failures); PILOT report with a Bonferroni readings template (m per-node memory-effect contrasts stated). Compute estimate printed before running: 72 roots and 864 leaves per arm; ~11,808 expected LLM calls per LLM arm (roots 20 each + branches' mean remaining budget 12).
- **Review.** One MAJOR (F7: novelty dropped real editable constants — `digits_mlp` was wrongly failed at 7/20 and the Ada gate could have excluded a live node) and four MINOR findings (F8 launcher exit codes, F9 E1-resume seen set, F10 finish checkpointing, F11 lexicographic manifest pick); all five fixed in one correction round (harness `411c605`, paper `0cb76a3`). The review re-derived the committed smoke, confirmed byte-identical records, the DT4 regeneration, the gate fail-before and the end-to-end commit check.
- **Deviations / open items.** (1) An untracked stray `uv.lock` at the paper repository root (and an empty partial `.venv`) was moved aside to the session temp directory; all suites ran with the harness venv interpreter and an absolute `AR_HARNESS_ROOT` (`make` does not expand `~`). (2) The launcher's batch-root/binary/pinned-batch/remote paths gained `R1_RERUN2_*` environment overrides (Ada defaults unchanged) so `--prepare`'s classification is testable off Ada. (3) The P6 commit message and the superseded smoke carry the pre-correction digits/tabular numbers; this entry and the review Resolution supersede them. (4) Ada remains unverified locally: if the 12 Oct extra harness failure (`TestCompletenessCLI::test_checked_in_report_contains_all_plan_campaigns`) still occurs at the pin, `--start` refuses by design and the operator reports. Open author decisions unchanged: the D4 amendment, D18, D21, D23 and the verify split policy.
- **Next:** hand over `docs/r1/prompts/ADA_E1B_RERUN2_PROMPT.md`; it starts `--prepare` from this prompt's entrypoints.

## 14 October 2026 — author decisions after the batch-3 review

Planning only; recorded by an AI agent (Claude) at the author's request. No code and no runs.

- **Adopted** (PLAN §10, 14 Oct, after the batch-3 review): the D27 F3 fix via config hashes in `edit_novelty` and in E2 snapshots (no `TrialRecord` change); D28 criterion 2 revised to active-key novelty, with the memory-off contrast arm exempt from the gate; R1-E1B-RERUN2 (4 nodes, 18 instances, arms A = LLM memory on, B = LLM memory off, C = scripted on the new harness).
- **Not decided**: the D4 amendment (run-free acceptance rules). It is not in the rerun. D18, D21, D23 and the verify split policy are also still open.
- Consequence of the batch-3 F1 fix, recorded here: the scripted proposal sequence is unchanged, but on declared nodes an inert draw is now skipped without a worker run, so the 12 Oct scripted E1b is not byte-reproducible on the new harness. That is why arm C reruns it.
- Next: `docs/r1/prompts/BUILD_BATCH4_PROMPT.md` (desktop: F3, D28 revision, rerun entrypoints), then `docs/r1/prompts/ADA_E1B_RERUN2_PROMPT.md`.

## 14 October 2026 — batch 3: D24–D28 desktop implementation, review and correction (ENGINEERING_ONLY)

AI-assisted execution by opencode (deepseek-v4.1-flash) at the author's request per `docs/r1/prompts/BUILD_BATCH3_PROMPT.md`; no LLM calls, no GPU, no Ada batch created or launched. Commits: paper `0a3f284` → `e4d31d5` (branch `main`); harness `9c4902d` → `0f2d9e9` (branch `r1`). Independent fresh-context review: `docs/r1/reviews/BUILD_REVIEW_20261014.md` (+ Resolution).

- **Built (harness).** D24 summary fixes (node `metric_name`, a metric of exactly 0.0 is shown, best-strategy respects `metric_direction`, a missing node metric never leaks another parsed metric). D25 node-declared active keys: optional `active_keys` on `NodeSpec` omitted from `to_dict()` when empty (undeclared hashes unchanged), all seven `openml_*` nodes declared (model_type-keyed; `class_weight` omitted under `gradient_boosting`; `imputer` excluded where the committed feature metadata shows no categorical columns), the LLM prompt lists only active keys, a proposal naming an inactive key is rejected before any worker run, revised at most 2 times (`MAX_INACTIVE_KEY_REVISIONS`, each charged to the LLM-call cap), else skipped with reason `inactive_key` (event `proposal_rejected_inactive_key`). D26 deterministic Ollama seed from (campaign, trial index, repetition, revision attempt), passed at model construction and recorded in `llm_call`; temperature stays 0.2. D27 record-only `edit_novelty` event (`config_equals_incumbent`, `config_seen_before`, `metric_identical_to_incumbent`); `TrialRecord` bytes unchanged. Post-review fix: `ManagerStatus` stays unfiltered — the D25 filter applies only to the prompt — so the scripted proposal law is untouched.
- **Built (paper).** `e1b_collect` takes `memory_mode` and the seed policy from the manifest (no literal; absent field = `none` for historical runs); branch continuations inherit the root's mode from the snapshot (verified); `scripted_manager` reads the node declaration (numeric pool = active ∩ allowed_ranges, order preserved) with two goldens generated from pre-change code (direct replay; live `run_real_campaign` path). `noop_skip` E1 controller (skips no-op/duplicate edits; marked as needing E1 branch data for offline scoring). `r1/liveness/`: D28 checker (`--offline`/`--run`, JSON + Markdown per node) and `require_live` gate wired into `deepthought_batch1_resume.collect` before any collector call; the gate accepts only an LLM-backed (`manager_kind: langgraph`) liveness manifest.
- **Tests.** Harness: **349 passed, 8 failed, 1 error** before → **380 passed, same 8 failed, 1 error** after (the failures/error are pre-existing environmental: generated paper assets absent; `harness/claw-code` submodule not initialised). Paper: `r1/tests` **75** → **109 passed**; `make test` **212 / 6 / 12 OK** before and after. Every behaviour change was shown to fail on the base code (harness base + new tests: 5 failed, 2 collection errors; paper base + new tests: 4 failed, 3 collection errors); the review independently re-ran these spot checks.
- **Liveness results.** Offline DT4 ledgers (`results/r1/pilot/E1b_20261013T151857Z/provenance/ledgers/roots`, committed): `openml_ionosphere` **FAILS** (0 keeps after trial 1; 0/114 trials metric-different; invalid 0.0) and `digits_mlp` **PASSES** (11 keeps; 92/114 = 0.807; invalid 0.0) — committed acceptance test. Scripted smoke on the five noise nodes (`results/r1/engineering/liveness_scripted_20261014T072114Z`; 2 instances, W = 10, no branching; re-run on the corrected harness): `openml_wdbc` **FAILS** `metric_diff_fraction` (7/18), `digits_mlp`, `tabular_mlp`, `openml_breast_w`, `openml_ionosphere` PASS. The scripted verdicts are not the D28 check for LLM collection; the gate rejects `manager_kind != langgraph`, so the Ada LLM liveness run must be performed before LLM-backed collection.
- **Audit headline.** `docs/r1/reports/NODE_KEY_AUDIT_20261014.md`: all 15 registered nodes audited. OpenML declarations match the template code; `imputer` is inert on ionosphere/wdbc/breast_w/diabetes (feature metadata), active on credit_approval; `class_weight` is inert under `gradient_boosting`. Flagged for the author: `imputer` on `openml_bank_marketing`/`openml_credit_g` (no in-repo metadata; declared active), `resnet_trigger` (fast-search env and MPS-cap inert keys, no declaration; not the same mechanism), `autoresearch_linux` (registered config, no node directory).
- **Review summary.** 1 MAJOR + 5 MINOR. Fixed: F1 (MAJOR: D25 filtering in the campaign status silently changed the scripted live proposal sequence for existing seeds; fixed by filtering only the LLM prompt, with a live-campaign golden that fails on the reviewed head `ff61911` and passes on `0f2d9e9`), F2 (unguarded `revision_attempt` kwarg), F5 (scripted smoke not re-derivable; gate could consume a scripted manifest), F6 (Anthropic-backed manager raised). Open: F3 (`config_seen_before` is blind to configs evaluated before a resume; a fix needs a record-level config hash and an author decision), F4 (dry campaigns emit no `edit_novelty`; no workspace to compare — would be vacuous).
- **Deviations.** (1) Environment: system `python3` is 3.14 without pytest/numpy; all suites ran with the harness venv interpreter (`make r1-test ... R1_PY=…`, `make test PYTHON=…`) and `make r1-test` needs an absolute `AR_HARNESS_ROOT` (make does not expand `~`). (2) The harness H2–H4 work is one commit, not three (the changes interleave in `campaign.py`/`langgraph_manager.py`). (3) D26 adds the revision attempt to the seed derivation (per the batch prompt) and skips seeding for providers without a seed API (Anthropic). (4) `edit_novelty` is the documented new event type; `llm_call` payloads additionally carry `seed` (required by D26). No item was fully stopped under rule 3; the two open review findings and the three audit flags are recorded above for the author.
- **Next.** Ready for the Ada step: the LLM liveness check (memory on) on the five noise nodes, then the LLM E1b rerun. The runner gate requires a `manager_kind: langgraph` liveness manifest (produced by `python -m r1.liveness --run --manager langgraph …`).












## 14 October 2026 — author adopted D24–D28 (proposer decisions)

Planning only; recorded by an AI agent (Claude) at the author's request. No code and no runs.

- Finding behind the decisions: memory was switched off by R1's own collector (`r1/headroom/e1b_collect.py`, `run_root`: `memory_mode="none"` as a literal), not by a harness default and not by any PLAN row. Under `none` the LangGraph prompt still prints the AVOIDANCE RULE over a history that does not exist. Details: `docs/r1/reports/PROPOSER_DECISIONS_20261014.md`.
- **Adopted** (PLAN §10, 14 Oct): D24 memory `append_only_summary` (primary; `none` as E1b contrast), D25 node-declared active keys, D26 seeded manager sampling, D27 no-op/duplicate flags plus an E1 skip arm, D28 node liveness check as a runner STOP.
- Next: desktop implementation per `docs/r1/prompts/BUILD_BATCH3_PROMPT.md` with an independent review; then the liveness check and the LLM E1b rerun on Ada (separate prompt).
- Still open: D18, D21, D23, the D4 amendment, the verify split policy, and the trial-1 unconditional-keep item.

## 14 October 2026 — ionosphere LLM diagnosis (read-only, ENGINEERING_ONLY)

AI-assisted diagnosis by opencode (deepseek-v4.1-flash) at the author's request; no LLM calls, no GPU, no worker runs, no code change to harness/manager/prompts/nodes/PLAN/RUNBOOK. PILOT data only; not evidence. No decision recorded.

- **Examined.** LLM run `results/r1/pilot/E1b_20261013T151857Z` (6 ionosphere roots, 72 branches, `provenance/ledgers/`, snapshots, `points.json`); scripted run `results/r1/pilot/E1b_20261012T161034Z`; harness `9c4902d` (node `benchmark.py`, `langgraph_manager.py`, `metric_parser.py`, `decision.py`, `summarizer.py`); Ada `r1_e1b_llm_work/` per-trial `patch.diff`/`run.log` (read-only).
- **Verdict: the working hypothesis is confirmed.** On ionosphere the LLM edits only `n_estimators` and `max_depth`, which `_build_model` ignores under `logistic_regression` (`benchmark.py:225-231`), so the metric is bit-identical to the incumbent on 114/114 root and 720/720 branch trials; the strict keep rule (`delta > 0`) never fires after trial 1. 840 trials, 6 keeps (first valid metric per root), 0 invalid, Δ̂ = 0. The scripted proposer edits only active keys and keeps 18/66 root trials (ρ = +0.0189 vs LLM 0). Decoding is not deterministic (temperature 0.2, no seed): 3/72 branch pairs agree across repetitions.
- **Ruled out:** metric-parsing default, incumbent read error, unapplied edit, cached worker result (see Q6).
- **Report:** `docs/r1/reports/IONOSPHERE_LLM_DIAGNOSIS_20261014.md`; reproducible tables `r1/diagnostics/ionosphere_llm_diag.py`. Fix options listed for the author (expose only active keys; annotate active keys; surface "metric unchanged"; set manager temperature/seed; or leave as is). **Decisions remain open.**

## 13 October 2026 — DT4 rerun: commit-only recovery

AI-assisted recovery by Codex, authorized by the author (PLAN §10, R1-COMPUTE DT4 commit-only recovery). PILOT; not evidence.

- Cause of the stop: generated tables ended with a blank line, failing `git diff --cached --check`. The runner stopped before committing anything. Fix: `0a7a8328eb219243ebb205c366a3e68e6b1733f8` (`e1b_analyze.markdown` emits one trailing newline through main; regression `r1/tests/test_e1b_markdown.py`).
- No re-collection or inference. Collection `results/r1/pilot/E1b_20261013T151857Z`: 144 leaves, 12 audits, 1,440 LLM calls, 0 collection and 0 parse failures; wall time 28.3 min; Ada GPU 1 (`GPU-aa340032-6f94-9783-8f3d-50a15da47a6f`), no co-tenants observed, minimum free memory 43,145 MiB; load offload `size_vram = size = 5,560,907,776` bytes.
- Regenerated `analysis.json` is byte-identical to the runner's: sha256 `d0d5979ac2cff458b95865fb27bd3c2ea973f215e59b15ea78a881ac9b84caca`. Tables differ only in trailing newline; report text unchanged. Artifacts committed/pushed `52894f32eacd900b51d53482efa131ac5b3d948e`.
- Committed-data regeneration: match; original, recovered and regenerated sha256 `d0d5979ac2cff458b95865fb27bd3c2ea973f215e59b15ea78a881ac9b84caca`. Record `/data1/dowling/tmp/r1_DT4_rerun_ENGINEERING_ONLY_20261013_PI3cZS/recovery/regeneration.json`.
- Gap: after-collection offload check passed, but telemetry was not saved; logging fixed for future runs in `0a7a832`. No telemetry recreated.
- Stopped-state provenance: `/data1/dowling/tmp/r1_DT4_rerun_ENGINEERING_ONLY_20261013_PI3cZS/recovery/`; runner's stopped STATUS entry retained below.
- Local validation: 75 R1, 212 control, 6 release and 12 standalone tests passed. Installed author-approved `hypothesis==6.112.1` in existing local test venv with dependencies attrs 26.1.0 and sortedcontainers 2.4.0; used that interpreter for make test after system Python lacked dependencies. Fresh Ada clone lacked Git identity; configured repository-local identity from the existing Mac author settings before committing. No rejected push, history rewrite, data change, GPU use or interference with other users.
- E2 decisions remain open. L11 is not built.

## 13 October 2026 — Remote batch 1: stopped

AI-assisted execution by Claude (runner) on Ada, started by the author. All outputs are PILOT or ENGINEERING_ONLY; none is evidence.

- **Execution host:** `ucrtasl`. Logs and preserved runtime state: `/data1/dowling/tmp/r1_DT4_rerun_ENGINEERING_ONLY_20261013_PI3cZS/`.
- **Harness:** `9c4902d0d8776f18a081e1ff2478d651fc7096c1`; manager `qwen2.5-coder:7b`, pinned digest `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`.
- **GPU / offload:** `1, GPU-aa340032-6f94-9783-8f3d-50a15da47a6f, NVIDIA RTX 6000 Ada Generation, 48427`; `{"full_offload": true, "host": "ucrtasl", "keep_alive": -1, "probe_tokens_max": 1, "size": 5560907776, "size_vram": 5560907776}`.

- **DT1:** `{"commit": "9c4902d0d8776f18a081e1ff2478d651fc7096c1", "completed": true, "latency": {"completion_tokens": {"max": 95, "mean": 90.4, "median": 90.5, "min": 85, "n": 10}, "event_files": ["/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/autoresearch_harness/experiments/r1/pilot/L4dt_20261013T011936Z/events.jsonl"], "label": "PILOT", "latency_ms": {"max": 848.0100480373949, "mean": 814.598328480497, "median": 820.8710500621237, "min": 773.399808909744, "n": 10}, "n_calls": 10, "n_parse_failures": 0, "parse_failure_rate": 0.0, "prompt_tokens": {"max": 622, "mean": 619.2, "median": 620.0, "min": 611, "n": 10}, "tokens_reported": true}, "out": "/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/autoresearch_harness/experiments/r1/pilot/L4dt_20261013T011936Z", "size_vram": 5560907776}`
- **DT2:** `{"commit": "7f8128312f70d8b20e9dd7613c8ee7ba27e73392", "completed": true, "out": "/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/agent_paper_B/results/r1/engineering/L12_live_20261013T090417Z", "summary": {"accepted": true, "actual_worker_runs": 10, "call_errors": 0, "caps": {"llm_calls": 12, "worker_runs": 10}, "charged_llm_calls": 4, "control_events": 6, "decision_action_distribution": {"continue": 4, "verify": 2}, "digest": "dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364", "disallowed_actions": 0, "event_llm_calls_sum": 4, "harness": {"branch": "r1", "commit": "9c4902d0d8776f18a081e1ff2478d651fc7096c1", "dirty": false}, "host": "ucrtasl", "label": "ENGINEERING_ONLY", "missing_llm_calls": 0, "model": "qwen2.5-coder:7b", "parse_failures": 0, "queried_action_distribution": {"continue": 2, "verify": 2}, "side_queries": 4, "utc": "20261013T090418Z"}}`
- **DT3:** `{"checks": {"collection_failures": 0, "label": "ENGINEERING_ONLY", "leaves": 2, "llm_calls": 8, "manager_kind": "langgraph", "parse_failures": 0, "proposal_examples": ["increase-hidden-units-64", "increase-batch-size-128", "increase-hidden-units-128", "increase-batch-size-128", "increase-hidden-units-128"]}, "commit": "48f8d8900bf688f8f4beec126cc6b9df408a075b", "completed": true, "out": "/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/agent_paper_B/results/r1/engineering/E1b_llm_smoke_20261013T090434Z"}`
- **DT4:** `{"checks": {"collection_failures": 0, "label": "PILOT", "leaves": 144, "llm_calls": 1440, "manager_kind": "langgraph", "parse_failures": 0, "proposal_examples": ["increase-hidden-units-64", "increase-hidden-units-128", "increase-hidden-units-256", "increase-batch-size-128", "increase-batch-size-128"]}, "completed": false, "headroom": {"ALL": {"best_simple": "always_verify", "contrast_ci": {"always_verify - rho": [-0.00012251157407406135, 0.0014056759259259604], "awr_mlp - rho": [-1.934027777777958e-05, 0.0013154027777778077], "harness_heuristic - rho": [-0.00012251157407406135, 0.0014056759259259604], "kg_index - rho": [-0.00017409722222220224, 0.0013154027777778077], "margin_threshold - rho": [-0.00017409722222220137, 0.00027081944444445893], "oracle_leafsplit - always_verify": [-1.934027777777958e-05, 0.0001740972222222018], "oracle_leafsplit - rho": [-2.578703703703944e-05, 0.0014066434027778078], "oracle_naive - always_verify": [0.0, 0.0001805439814814621], "oracle_naive - rho": [0.0, 0.0014079327546296528], "random_matched - rho": [-0.00017409722222220224, 0.0006963888888889174], "ridge_advantage - rho": [-0.00017409722222220224, 0.0013154027777778077]}, "headroom_leafsplit": 5.1585648148140886e-05, "headroom_naive": 6.44791666666606e-05}, "digits_mlp": {"best_simple": "always_verify", "contrast_ci": {"always_verify - rho": [-0.0002579166666666424, 0.002695287037037121], "awr_mlp - rho": [-3.868055555555916e-05, 0.0026308055555556153], "harness_heuristic - rho": [-0.0002579166666666424, 0.002695287037037121], "kg_index - rho": [-0.0003481944444444045, 0.0026179120370370956], "margin_threshold - rho": [-0.00034819444444440274, 0.0005416388888889179], "oracle_leafsplit - always_verify": [-3.868055555555916e-05, 0.00034819444444440274], "oracle_leafsplit - rho": [-5.157407407407888e-05, 0.002785564814814883], "oracle_naive - always_verify": [0.0, 0.00036108796296292246], "oracle_naive - rho": [0.0, 0.0028113518518519207], "random_matched - rho": [-0.0001547499999999813, 0.001379884259259315], "ridge_advantage - rho": [0.0, 0.0012380277777777806]}, "headroom_leafsplit": 0.00010317129629628177, "headroom_naive": 0.0001289583333333212}, "openml_ionosphere": {"best_simple": "rho", "contrast_ci": {"always_verify - rho": [0.0, 0.0], "awr_mlp - rho": [0.0, 0.0], "harness_heuristic - rho": [0.0, 0.0], "kg_index - rho": [0.0, 0.0], "margin_threshold - rho": [0.0, 0.0], "oracle_leafsplit - rho": [0.0, 0.0], "oracle_naive - rho": [0.0, 0.0], "random_matched - rho": [0.0, 0.0], "ridge_advantage - rho": [0.0, 0.0]}, "headroom_leafsplit": 0.0, "headroom_naive": 0.0}}, "out": "/data1/dowling/tmp/r1_DT4_rerun_ENGINEERING_ONLY_20261013_PI3cZS/agent_paper_B/results/r1/pilot/E1b_20261013T151857Z", "report": "/data1/dowling/tmp/r1_DT4_rerun_ENGINEERING_ONLY_20261013_PI3cZS/agent_paper_B/docs/r1/reports/HEADROOM_PILOT_20261013_llm.md"}`

**STOP:** CalledProcessError: Command '['git', 'diff', '--cached', '--check', '--', '.', ':!results/r1/**', ':!experiments/r1/**']' returned non-zero exit status 2.

DT1–DT4 are accepted only where the step entry explicitly records completion. Partial outputs are preserved; no failed model or collection run was retried.

- **Author decisions remain open:** D18, D21, D23, the D4 amendment and any verify split-policy revision. Fixed split policy retained; L11 was not built.

## 13 October 2026 — launcher updated for GPU co-tenancy; DT4 rerun prepared

AI-assisted ENGINEERING_ONLY code change by Claude at the author's request; no runs. The author authorized a fresh DT4 attempt on Ada (PLAN §10, R1-COMPUTE DT4 rerun).

- `r1/scripts/deepthought_batch1_resume.py`:
  - card selection (`gpu_rows`) is now by free memory: footprint 5,304 MiB (DT1 `size_vram`) + 2,048 MiB margin;
  - `check_gpu` logs a census of every card (free memory, process owners) to `gpu_census.jsonl` and STOPs only when free memory is below the margin (footprint + margin before loading, margin alone after); other users' processes no longer cause a STOP;
  - new `assert_full_offload`: STOP unless `size_vram = size`;
  - a memory check before every collection session;
  - DT4 moved unchanged into `run_dt4(meta, version)`, plus a full-offload check after collection; the report's deviation note now describes co-tenancy;
  - executor label and commit co-author are configurable (`R1_EXECUTOR`, `R1_COAUTHOR`; defaults unchanged).
- New `r1/scripts/ada_rerun_dt4.py` (Ada-only; preconditions: DT1–DT3 complete and the interrupted DT4 preserved in the previous batch, duplicate-launch hold confirmed, both PLAN rows present, checkout at origin/main, a permanent `dt4_rerun_claim`) and `r1/scripts/ada_dt4_rerun_launch.sh` (fresh clone in a new batch directory, reuses the DT1 harness venv and pinned model files, tmux `r1_dt4_rerun`). Ollama runs with `OLLAMA_KEEP_ALIVE=-1`, so the model is never unloaded and reloaded onto a fuller card mid-run.
- `r1/tests/test_gpu_process_census.py` rewritten for the new rule (7 tests). The test "other user on card is rejected" is replaced by "allowed and logged".
- Checks (device VM, Python 3.13.15): `r1/tests` without the three harness-dependent files **58 passed**; `make test` control 212, release 6, standalone 12, all OK. The three harness-dependent R1 test files were not run here (no harness checkout in this environment); they do not import the changed scripts.
- `docs/r1/prompts/DEEPTHOUGHT_BATCH1_PROMPT.md` hard rule 1 now states the co-tenancy rule.
- **Not run yet.** The launch needs the author's Ada login: `bash r1/scripts/ada_dt4_rerun_launch.sh` on `ucrtasl` after these commits are on origin/main.

## 13 October 2026 — author decision: GPU co-tenancy allowed; latency descriptive

Planning only; no code and no runs. Recorded by an AI agent (Claude) at the author's request.

- **Author decision** (PLAN §10, R1-COMPUTE GPU co-tenancy): a card may be shared with other users when its free memory is enough; LLM latency is descriptive only. This replaces the idle-card / no-other-user condition of the earlier R1-COMPUTE rows. The other rules stay: pinned model, verified GPU offload with CPU fallback a STOP, no disturbance of other users, duplicate-launch prevention, no Mac LLM.
- **Agent-proposed default, for the author to confirm or change:** "enough" = free memory ≥ measured footprint + 2 GiB (≈ 7.2 GiB for the pinned 7B), checked at selection and before each step.
- RUNBOOK §3 (compute map, Ada bullet, new GPU-sharing bullet) and 0.4 (latency is descriptive, logged with a GPU census) updated to match.
- **Consequences.** The DT2/DT3 note that no exclusive-use claim is made needs no further action. The DT4 STOP was triggered only by the old ownership rule, so the decision removes that cause. A DT4 rerun still needs an explicit go from the author, as the DT4 entry says.
- The launcher and the batch prompt were updated afterwards (next entry).

## 13 October 2026 — old manuscript archived (RUNBOOK 0.1, legacy item)

AI-assisted housekeeping by Claude at the author's request; no runs, no evidence.

- Moved `papers/paper_b/` unchanged (sources, build products, `legacy/`, `archive/B1_20260927/`) to `archive/old_b_2026-10-09/paper_b_manuscript/`. `papers/` is now empty; the R1 manuscript goes in `papers/r1/` (RUNBOOK Phase 4).
- Repointed `make paper-b` (root `Makefile`) and the paths in `README.md`; documented the move and the remaining dangling `papers/paper_b/...` names (release scripts, `release/paper_b_manifest.json`, `PROVENANCE.md`, PLAN §8) in `archive/old_b_2026-10-09/README.md`. PLAN was not edited.
- No kept test reads the manuscript: `tests/release/test_provenance.py` builds its own fixture repo, and `scripts/release_provenance.py` reads `main.tex` from a historical source commit. `make test` after the move (Python 3.13.15): control 212, release 6, standalone 12 — all OK.
- The old release tooling (`make release-b`, `check-release-b`) still points at the old path and stays unmaintained, as before.

## 13 October 2026 — DT2/DT3 complete; DT4 stopped on GPU ownership conflict

AI-assisted ENGINEERING_ONLY smoke checks and interrupted PILOT; not evidence.

- Continuation selected Ada GPU 0 after its free-card census at 09:03:58 UTC. Exact pinned 7B digest verified; offload probe records size_vram 5560907776 and owned Ollama with 29 GPU layers. DT1 was not repeated. Deepthought permanent migration holds remain.
- DT2 committed/pushed `7f81283`: four side queries (two continue, two verify), zero parse/disallowed/call errors. Independently read six control events: every event has llm_calls and sum 4 reconciles with accounting/controller log. Ten worker runs, four LLM calls within caps 10/12. Output `results/r1/engineering/L12_live_20261013T090417Z/`.
- DT3 committed/pushed `48f8d89`: independently verified continue/verify leaves, zero collection failures, langgraph manager, eight LLM calls with zero parse failures and LLM proposal summaries. Output `results/r1/engineering/E1b_llm_smoke_20261013T090434Z/`.
- DT4 started at 09:05:10 UTC. Independent monitoring subsequently found root-owned PID 1625292 on selected GPU 0 alongside our Ollama. Its process start time precedes our Ollama start; the saved free-card census does not establish when it allocated GPU memory. GPU ownership during DT2/DT3 therefore has a limitation; no exclusive-use claim is made.
- Hard STOP enforced at 09:17:35 UTC: stopped only our continuation process tree and dedicated Ollama; NVIDIA census confirms our model process absent and the root-owned job untouched. Claims/results retained. Partial DT4 `results/r1/pilot/E1b_20261013T090510Z/` and interrupted work/log/state/offload/census bytes archived in `interrupted_provenance/`. No DT4 headroom bracket is accepted or analyzed. Monitoring paused; no failed/interrupted campaign retry.
- Author input needed for any further DT4 execution; a new attempt would require an explicit decision and reliable exclusive GPU allocation. E2 decisions remain open, fixed splits retained, no L11.

## 13 October 2026 — Any-idle-Ada continuation authorized

AI-assisted ENGINEERING_ONLY setup; DT1 remains the accepted PILOT.

- Author now permits **one idle Ada GPU for unstarted DT2–DT4**, instead of waiting for GPU 0. Recorded in PLAN §10, pushed `05af1c1`; selector implementation pushed `fded5fe`. No model, node, seed, budget or analysis design changed.
- Census: Ada GPU 2 (`GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154`) had no compute or graphics processes; the other seven cards were occupied. Selection is rechecked immediately before serving, and the chosen UUID stays fixed for the continuation.
- The old GPU-0-only waiting checkpoint had no campaign steps or claim. It now has a permanent migration hold, and only our waiting tmux session `r1_ada_DT2_DT4_census_20261013` was stopped. All earlier claims, stopped states and results remain intact; Deepthought launchers remain disabled.
- Fresh continuation path: `/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_DT2_DT4_idle_20261013_khbc3ro5/`. It may execute only unstarted DT2–DT4 after pin and actual GPU offload checks on the selected card. DT1's ten calls are never repeated. Same exact pinned 7B model, one card, no other users disturbed, no API/larger model/Mac inference, PILOT/ENGINEERING_ONLY only; no E2 decisions or L11.
- **Post-launch census:** GPU 2 became occupied (PID 1445397) before allocation; all eight cards now have processes. The current continuation is alive, scans all cards every 60 seconds, has no claim and has not loaded a model or started DT2–DT4. It will select and pin one genuinely idle card when available. Census JSON is preserved in the new checkpoint.

## 13 October 2026 — Ownership-census race repaired; DT2–DT4 still unstarted

AI-assisted ENGINEERING_ONLY launcher repair; harness defaults unchanged.

- After DT1 staging recovery, the separate checkpoint successfully loaded the pinned model and generated only its one-token offload probe. Before DT2 it stopped when a GPU PID exited between `nvidia-smi` and `ps`. No DT2–DT4 campaign or collection had started; no failed model/collection is retried.
- Launcher repair (`beb62b2`, fixture `d255907`, merged/pushed `fb10c1f`) accepts a disappeared PID only after a fresh census proves it absent, then rechecks all remaining process owners. Unknown live owners and other users remain STOP conditions. CPU mocks: 2 failed/1 passed before repair; **all 68 R1 tests passed after**. Logs: `results/r1/engineering/GPU_census_regression_20261013/`.
- Both prior stopped states and permanent claims are retained. A fresh checkpoint for only the unstarted DT2–DT4 phases is `/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_DT2_DT4_census_20261013_ly8t2_9l/`; same node/seed/budget/model design and Ada GPU 0 only. DT1's original 10 calls are not repeated. Model pin and actual offload are revalidated before campaigns.
- DT1 remains accepted and committed in harness `9c4902d`. No E2 decision, L11, API/larger model or Mac inference. PILOT/ENGINEERING_ONLY only.

## 13 October 2026 — Remote batch 1: stopped

AI-assisted execution by Codex. All outputs are PILOT or ENGINEERING_ONLY; none is evidence.

- **Execution host:** `ucrtasl`. Logs and preserved runtime state: `/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_DT2_DT4_20261013_pqaq4qvv/`.
- **Harness:** `9c4902d0d8776f18a081e1ff2478d651fc7096c1`; manager `qwen2.5-coder:7b`, pinned digest `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`.
- **GPU / offload:** `0, GPU-9be33fd1-8eeb-497d-772a-87362d6720be, NVIDIA RTX 6000 Ada Generation, 48427`; `{}`.

- **DT0_ADA:** `{"acceptance": "Known environment failures plus author-approved missing-zsh exception", "completed": true, "tests": {"accepted": false, "deepthought_shutdown": "Unconfirmed: direct and portal SSH timeouts on both hosts", "duplicate_launch_prevented": false, "finished_utc": "2026-10-12T19:47:51.375022+00:00", "gpu_offload_verified": false, "harness_failures": ["FAILED tests/stage2/test_stage2_control_plane.py::TestClawWorkerExtraction::test_claw_worker_deterministic_constant_patch_runs_without_llm", "FAILED tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_checked_in_report_contains_all_plan_campaigns", "FAILED tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_cli_passes_on_real_campaigns", "FAILED tests/test_artifact_completeness_and_manifest.py::TestBuildManifest::test_all_referenced_files_exist", "FAILED tests/test_artifact_completeness_and_manifest.py::TestGenerateManifestCLI::test_cli_reports_all_files_exist", "FAILED tests/test_kdd_paper_sections.py::test_chunk_4_1_related_work_acceptance", "FAILED tests/test_kdd_paper_sections.py::test_chunk_4_2_system_design_acceptance", "FAILED tests/test_kdd_paper_sections.py::test_chunk_4_3_experiments_acceptance", "FAILED tests/test_kdd_paper_sections.py::test_chunk_4_4_results_order_and_artifact_links", "FAILED tests/test_kdd_paper_sections.py::test_chunk_4_5_discussion_acceptance", "ERROR tests/test_legacy_noop_skip.py"], "harness_head": "cbbd5fb2421ea65ccda8a0da2bd7340533488b36", "harness_summary": "10 failed, 347 passed, 1 warning, 1 error, 4 subtests passed in 33.58s", "harness_tests_exit": 1, "host": "ucrtasl", "inference_started": false, "label": "ENGINEERING_ONLY", "model_loaded": false, "paper_failures": [], "paper_head": "b246a4fd3d63c4b70b153995ad793abbf71d8a15", "paper_summary": "65 passed in 3.83s", "paper_tests_exit": 0, "prepared": true, "python": "Python 3.11.17", "started_utc": "2026-10-12T19:46:59.335607+00:00", "stop_reason": "Previously passing ClawWorker deterministic extraction test fails on Ada because /bin/zsh is absent", "uv_sync_exit": 0}}`
- **AUTHOR_EXCEPTION:** `{"commit": "0f25a18", "completed": true, "model_unchanged": true}`
- **DT1:** `{"commit": "9c4902d0d8776f18a081e1ff2478d651fc7096c1", "completed": true, "latency": {"completion_tokens": {"max": 95, "mean": 90.4, "median": 90.5, "min": 85, "n": 10}, "event_files": ["/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/autoresearch_harness/experiments/r1/pilot/L4dt_20261013T011936Z/events.jsonl"], "label": "PILOT", "latency_ms": {"max": 848.0100480373949, "mean": 814.598328480497, "median": 820.8710500621237, "min": 773.399808909744, "n": 10}, "n_calls": 10, "n_parse_failures": 0, "parse_failure_rate": 0.0, "prompt_tokens": {"max": 622, "mean": 619.2, "median": 620.0, "min": 611, "n": 10}, "tokens_reported": true}, "out": "/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/autoresearch_harness/experiments/r1/pilot/L4dt_20261013T011936Z", "size_vram": 5560907776}`

**STOP:** CalledProcessError: Command '['ps', '-o', 'user=', '-p', '762418']' returned non-zero exit status 1.

DT1–DT4 are accepted only where the step entry explicitly records completion. Partial outputs are preserved; no failed model or collection run was retried.

- **Author decisions remain open:** D18, D21, D23, the D4 amendment and any verify split-policy revision. Fixed split policy retained; L11 was not built.

## 13 October 2026 — DT1 verified and committed; unstarted DT2–DT4 checkpoint

AI-assisted PILOT/ENGINEERING_ONLY execution; not evidence.

- **DT1 accepted:** Ada GPU 0 became unoccupied and the guarded runner started once. Ollama 0.9.2 served the exact pinned `qwen2.5-coder:7b` digest `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`. GPU offload verified before latency: `size_vram = 5560907776`, an owned process on the selected card, and server log confirms **29/29 layers offloaded**.
- **Latency:** 10 calls, 0 parse failures; median **820.871 ms**, mean **814.598 ms**, range **773.400–848.010 ms**. Independently checked event count, parse flags, CSV row count, pin and offload records. Harness commit `9c4902d` pushed and remote HEAD verified; data `experiments/r1/pilot/L4dt_20261013T011936Z/`.
- Original runner stopped during artifact staging (`git diff --cached --check`), before DT2. Raw generated CSV/log/patch whitespace caused the failure, not a model or collection failure. Every original artifact byte was preserved and hash-checked; only source changes are subject to whitespace checks. No extra DT1 call or harness behavior change occurred.
- The original stopped attempt, its state and permanent claim remain intact. Checkpoint scripts (`6826979`, `27184cc`, pushed) may continue **only unstarted DT2–DT4**, after rechecking GPU 0, the existing duplicate-prevention record and model pin/offload. They cannot rerun DT1 or any started DT2/DT3/DT4 step.
- New checkpoint logs: `/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_DT2_DT4_20261013_pqaq4qvv/`; original provenance remains `/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/`. No claim is cleared. Same planned nodes, seeds, budgets and manager; one GPU and no API/larger model. The known missing-zsh exception remains; E2 decisions remain open and L11 is unbuilt.

## 13 October 2026 — Remote batch 1: stopped

AI-assisted execution by Codex. All outputs are PILOT or ENGINEERING_ONLY; none is evidence.

- **Execution host:** `ucrtasl`. Logs and preserved runtime state: `/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/`.
- **Harness:** `cbbd5fb2421ea65ccda8a0da2bd7340533488b36`; manager `qwen2.5-coder:7b`, pinned digest `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`.
- **GPU / offload:** `0, GPU-9be33fd1-8eeb-497d-772a-87362d6720be, NVIDIA RTX 6000 Ada Generation, 48424`; `{"host": "ucrtasl", "probe_tokens_max": 1, "size_vram": 5560907776, "verified_before_DT1": true}`.

- **DT0_ADA:** `{"acceptance": "Known environment failures plus author-approved missing-zsh exception", "completed": true, "tests": {"accepted": false, "deepthought_shutdown": "Unconfirmed: direct and portal SSH timeouts on both hosts", "duplicate_launch_prevented": false, "finished_utc": "2026-10-12T19:47:51.375022+00:00", "gpu_offload_verified": false, "harness_failures": ["FAILED tests/stage2/test_stage2_control_plane.py::TestClawWorkerExtraction::test_claw_worker_deterministic_constant_patch_runs_without_llm", "FAILED tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_checked_in_report_contains_all_plan_campaigns", "FAILED tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_cli_passes_on_real_campaigns", "FAILED tests/test_artifact_completeness_and_manifest.py::TestBuildManifest::test_all_referenced_files_exist", "FAILED tests/test_artifact_completeness_and_manifest.py::TestGenerateManifestCLI::test_cli_reports_all_files_exist", "FAILED tests/test_kdd_paper_sections.py::test_chunk_4_1_related_work_acceptance", "FAILED tests/test_kdd_paper_sections.py::test_chunk_4_2_system_design_acceptance", "FAILED tests/test_kdd_paper_sections.py::test_chunk_4_3_experiments_acceptance", "FAILED tests/test_kdd_paper_sections.py::test_chunk_4_4_results_order_and_artifact_links", "FAILED tests/test_kdd_paper_sections.py::test_chunk_4_5_discussion_acceptance", "ERROR tests/test_legacy_noop_skip.py"], "harness_head": "cbbd5fb2421ea65ccda8a0da2bd7340533488b36", "harness_summary": "10 failed, 347 passed, 1 warning, 1 error, 4 subtests passed in 33.58s", "harness_tests_exit": 1, "host": "ucrtasl", "inference_started": false, "label": "ENGINEERING_ONLY", "model_loaded": false, "paper_failures": [], "paper_head": "b246a4fd3d63c4b70b153995ad793abbf71d8a15", "paper_summary": "65 passed in 3.83s", "paper_tests_exit": 0, "prepared": true, "python": "Python 3.11.17", "started_utc": "2026-10-12T19:46:59.335607+00:00", "stop_reason": "Previously passing ClawWorker deterministic extraction test fails on Ada because /bin/zsh is absent", "uv_sync_exit": 0}}`
- **AUTHOR_EXCEPTION:** `{"commit": "0f25a18", "completed": true, "model_unchanged": true}`
- **DT1:** `{"completed": true, "latency": {"completion_tokens": {"max": 95, "mean": 90.4, "median": 90.5, "min": 85, "n": 10}, "event_files": ["/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/autoresearch_harness/experiments/r1/pilot/L4dt_20261013T011936Z/events.jsonl"], "label": "PILOT", "latency_ms": {"max": 848.0100480373949, "mean": 814.598328480497, "median": 820.8710500621237, "min": 773.399808909744, "n": 10}, "n_calls": 10, "n_parse_failures": 0, "parse_failure_rate": 0.0, "prompt_tokens": {"max": 622, "mean": 619.2, "median": 620.0, "min": 611, "n": 10}, "tokens_reported": true}, "out": "/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/autoresearch_harness/experiments/r1/pilot/L4dt_20261013T011936Z", "size_vram": 5560907776}`

**STOP:** CalledProcessError: Command '['git', 'diff', '--cached', '--check']' returned non-zero exit status 2.

DT1–DT4 are accepted only where the step entry explicitly records completion. Partial outputs are preserved; no failed model or collection run was retried.

- **Author decisions remain open:** D18, D21, D23, the D4 amendment and any verify split-policy revision. Fixed split policy retained; L11 was not built.

## 12 October 2026 — Deepthought duplicate-launch prevention confirmed

AI-assisted ENGINEERING_ONLY shutdown; no inference or evidence.

- SSH to both Deepthought hosts recovered. The old shared batch had no `runner_claim` and no `batch_state.json` on either host; no old runner had launched.
- Atomically created a permanent migration hold in `/ceph/dwong/r1_batch1_ENGINEERING_ONLY_resume_20261012T191238Z/runner_claim/`, with ENGINEERING_ONLY ownership provenance for Ada migration. The claim is retained and must never be cleared.
- Stopped only our dedicated `r1_auto_resume_20261012` launch-watcher session on each host. Both stop commands returned zero; the sessions are absent. Other users' jobs and other tmux sessions were untouched.
- Provenance and the confirmed `duplicate_launch_prevented: true` marker are committed in `results/r1/engineering/Deepthought_shutdown_20261012T200109Z/`. The marker is copied to the fresh Ada batch after syncing this commit, allowing its existing GPU-0-only watcher to proceed when that card has no process.
- This completes the duplicate-prevention prerequisite. Ada must still wait for unoccupied GPU 0, verify the exact pinned 7B model and demonstrate actual GPU offload before DT1 latency and DT2–DT4. The missing-zsh environmental exception remains in force; all other rules and open E2 decisions remain unchanged.

## 12 October 2026 — Ada continuation authorized; waiting on both launch prerequisites

AI-assisted ENGINEERING_ONLY setup; no inference or evidence.

- The author explicitly accepted the Ada missing `/bin/zsh` deterministic-extraction failure as environmental; recorded in PLAN §10 at pushed commit `0f25a18`. The recorded suite remains Paper B **65 passed**, harness **347 passed, 10 failed, 1 error**. Only the recorded environment failure set is accepted; all other STOP rules remain.
- Pushed `ef34671`: Ada-only watcher, fixed to GPU 0 UUID `GPU-9be33fd1-8eeb-497d-772a-87362d6720be`; host/path guards and actual runtime provenance. New scripts compile; no harness behavior was changed. The private fresh checkouts and environment remain under `/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/`.
- Dedicated Ada tmux `r1_ada_wait_20261012` checks every 60 seconds. It must observe both an unoccupied GPU 0 and a verified `deepthought_disabled.json` before creating one permanent `ada_runner_claim` and invoking DT1–DT4. It never selects another card or clears a claim.
- **GPU 0 became occupied:** user `vla-reasoning` now holds the selected card (PIDs 116617, 117775, 117778, 117779, 117780 at census). Their jobs were untouched.
- **Duplicate prevention is still pending:** direct IPv4 SSH to both Deepthought hosts timed out again. No claim was cleared or overwritten and no Ada model was loaded. Shutdown-only monitoring continues for the old shared claim/launchers; the separate Ada experiment monitor has been re-enabled under the author's exception.
- **DT1–DT4 remain unstarted.** Once both waiting gates pass, the runner must verify `qwen2.5-coder:7b` digest `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`, then demonstrate Ollama `size_vram > 0` and an owned process on selected GPU before the latency campaign or later steps. GPU offload has not yet been tested.
- No additional author decision is needed for the known missing-zsh failure. Other test regressions, model digest changes, CPU fallback or unrecorded experiment decisions remain STOP conditions. E2 decisions remain open; L11 is unbuilt. All outputs remain PILOT or ENGINEERING_ONLY.

## 12 October 2026 — Ada migration preparation: hard STOP before inference

AI-assisted ENGINEERING_ONLY preparation; no empirical evidence.

- Author authorized Ada GPU 0 for DT1–DT4, fresh checkouts and tests, pinned-model GPU offload, and prevention of duplicate Deepthought runs. Recorded in PLAN §10, commit `b246a4f` (pushed). Ada path/host guards and the duplicate-launch prerequisite were committed as `0d9874b` (pushed); harness code was unchanged.
- Fresh checkouts and private uv/Python environment: `/data1/dowling/tmp/r1_batch1_ENGINEERING_ONLY_ada_20261012_DcmRNh/`. Paper B test HEAD `b246a4f`; harness HEAD `cbbd5fb`. uv 0.13.0, managed Python 3.11.17. Existing Ada checkouts were preserved.
- Ada GPU 0: NVIDIA RTX 6000 Ada, UUID `GPU-9be33fd1-8eeb-497d-772a-87362d6720be`, no processes at census, about 47 GiB free. Seven other cards were occupied. No GPU process or Ollama server was started by this preparation.
- Tests: Paper B **65 passed**. Harness **347 passed, 10 failed, 1 error**, four subtests passed. Nine failures and the collection error are the recorded missing paper/artifact/submodule set. The artifact-report existence test returns to its initial failure on a fresh checkout; the prior passing result was already documented as a generated-report flake.
- **New failure / hard STOP:** `tests/stage2/test_stage2_control_plane.py::TestClawWorkerExtraction::test_claw_worker_deterministic_constant_patch_runs_without_llm`, previously passing on Deepthought, raises `FileNotFoundError: [Errno 2] No such file or directory: /bin/zsh` on Ada. Under batch hard rule 5, this stops DT1–DT4 before inference. No harness fix, shell substitution, submodule initialization or test retry was attempted.
- Preserved logs and exact test identities: `results/r1/engineering/DT0_Ada_20261012T194751Z/`. Copies remain in the remote engineering scratch directory.
- **Duplicate prevention remains unconfirmed:** direct IPv4/default SSH to both Deepthought hosts and the existing portal jump routes timed out. Their prior shared claim and tmux launchers could not be inspected or disabled. Ada inference was therefore withheld; there is no Ada/Deepthought duplicate launch by this preparation.
- **DT1–DT4:** unstarted on Ada; model digest has not been checked through a serving instance, and actual GPU offload has not been demonstrated. The pinned 7B model and all other rules remain unchanged. No headroom bracket is available. No E2 decision was recorded; L11 remains unbuilt.
- **Needs author / infrastructure:** disposition of the missing-zsh environmental failure under the hard STOP rule, and working SSH access to reserve the old shared claim and stop the old launch watchers before any Ada inference.

## 12 October 2026 — Deepthought batch 1 automatic resumption armed

AI-assisted ENGINEERING_ONLY preparation; model workloads remain PILOT or ENGINEERING_ONLY.

- Author amendment in PLAN §10 (`12db087`): monitor both authorized hosts without the previous one-hour deadline, and resume DT1–DT4 on an unoccupied GPU. The previous stopped attempt and all results are preserved.
- Both hosts are checked every 60 seconds from dedicated tmux watchers. A shared atomic claim permits one runner only. No other user's session or process is changed.
- Fresh logs and runtime state: `/ceph/dwong/r1_batch1_ENGINEERING_ONLY_resume_20261012T191238Z/`. The pinned `qwen2.5-coder:7b` digest stays `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`; no API or larger model.
- The runner first loads at most one probe token and requires Ollama `size_vram > 0` plus a process on the selected card before DT1 latency or DT2–DT4. GPU ownership is rechecked before every step. The older host's CUDA compatibility remains unqualified until that check passes.
- Latest census: Deepthought has another user's PID 1674140 on all four cards despite 0 percent utilization; Deepthought2 has other users' processes on both cards. No model has been started by this resumption at the time of this entry.
- DT0 and its regression baselines remain as recorded below. DT1–DT4 completion requires the runner's acceptance checks and subsequent status entry; no headroom bracket is available yet. E2 decisions remain open; L11 is not built.

## 12 October 2026 — Deepthought batch 1: stopped

AI-assisted execution by Codex. All outputs are PILOT or ENGINEERING_ONLY; none is evidence.

- **DT0:** deepthought2; Paper B `d55043c`, harness baseline `4e8fd69`; uv environment installed. Harness: 9 failed, 347 passed, 1 warning, 1 error, 4 subtests passed in 52.87s. Paper B: 64 passed. OpenML credit-g cache filled successfully.
- **DT0 environment:** Deepthought2 has 128 logical CPUs, about 1 TiB RAM, two NVIDIA L40S GPUs (46,068 MiB each), driver 570.211.01; nvidia-smi reports CUDA capability 12.8. Docker daemon access is denied; no Podman is installed.
- **Authorized fallback:** `deepthought.etp.kit.edu` (PLAN §10 author follow-up, commit `ae14877`); 40 CPUs, 503 GiB RAM, four GTX TITAN X GPUs (12,288 MiB each), driver 525.147.05. The fallback was checked without disturbing its occupied GPUs.
- **Fallback CUDA compatibility is unqualified:** current [Ollama hardware documentation](https://docs.ollama.com/gpu) requires driver 570+ for compute capability 5.0–6.2; GTX TITAN X is 5.2. The installed runtime must demonstrate actual GPU offload before DT1 is accepted; no driver upgrade was attempted.
- **Harness repair:** `0e8a817` (pushed): explicit zero `llm_calls` in emitted control decisions. Regression: failed before, 9 targeted tests passed after; full suite: 8 failed, 349 passed, 1 warning, 1 error, 4 subtests passed in 34.21s. No newly failing tests; the artifact-report existence flake accounts for one prior failure becoming a pass.
- **Preserved engineering logs:** `/ceph/dwong/r1_batch1_ENGINEERING_ONLY_20261012_E4cC3e/` (environment JSON, suite logs, OpenML log, GPU census/wait, official standalone Ollama runtime).
- **Model manifest preflight:** registry manifest SHA256 matches the author pin `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`. No inference is implied by this check.

- **COLLECTOR_REPAIR:** `{"commit": "63778d35c1a4aecf91ceb10514e8ae7e333112b7", "completed": true, "reason": "Retain branch directories and ledgers after auditing", "regression": "new test failed before; all 65 R1 tests passed after"}`
- **HOST_AUTHORIZATION:** `{"commit": "ae1487788c5e93bf007629accfdfdc1403b799fb", "completed": true, "decision": "Author permits deepthought.etp.kit.edu if a GPU is idle"}`
- **DT5_FEASIBILITY_PRECHECK:** `{"commit": "cbbd5fb2421ea65ccda8a0da2bd7340533488b36", "completed": true, "out": "/ceph/dwong/autoresearch_harness/experiments/r1/pilot/MLGym_dt_20261012T183511Z", "reason": "Deepthought2: Docker daemon permission denied. Deepthought: Docker daemon cannot be reached. Neither host exposes Podman in PATH.", "status": "blocked", "task_runs": 0}`
- **DT2_SCRIPT_PREPARATION:** `{"checks": "Compilation and ChatOllama/LLMSelfController constructor preflight passed; no invoke, zero model calls", "commit": "ee6eab2d4ef4cd2a7df52cf8515ff60605b2324b", "completed": true, "live_run_completed": false, "script": "r1/scripts/l12_live_smoke.py"}`

**STOP:** RuntimeError: No GPU became idle within the one-hour availability window; other users were undisturbed

DT1–DT4 are accepted only where the step entry above explicitly records completion. Uncompleted steps produced no accepted LLM headroom bracket. L12 smoke script preparation is not a live run.

- **DT5 task runs not performed:** Deepthought2 denies access to its Docker daemon; Deepthought cannot reach its Docker daemon. Podman is absent from PATH on both hosts. The PILOT precheck JSON and its commit are listed above. No MLGym clone or adapter was created.
- **Author decisions remain open:** D18, D21, D23, the D4 amendment and any verify split-policy revision. The existing fixed split policy was retained. L11 was not built.

## 12 October 2026 (evening) — steps 1–6 of the revised order; E2 STOP prepared

Executed by an AI agent (Claude) at the author's request. Outputs are PILOT or ENGINEERING_ONLY: no evidence. The work ran in the Linux VM on the Mac (4 cores, 3 GiB, Python 3.11, environment outside the repos). That VM cannot reach Ollama, so no LLM call was made anywhere.

### Harness (`autoresearch_harness`, branch `r1`; not pushed)

| Commit | What |
|---|---|
| `423addd` | **L8b:** noisy CPU nodes `digits_mlp` and `tabular_mlp` (sklearn MLP; training and split seeds injected independently); `mlp_synthetic` seed injection with unchanged defaults. 5 tests. |
| `f0dcd6a` | **L7 fix, found while debugging E1b.** A resumed E2 trial did not restore the incumbent after a discard, dropped verify's evidence, did not charge verify's re-runs, and did not push keeps onto the stack. Every branch dataset collected with earlier code is invalid. 2 tests. |
| `c686517` | **L12:** `ControlDecision.llm_calls`; controller LLM calls are charged to the LLM-call cap. Default records and events are unchanged. 3 tests. |
| `4e8fd69` | **L14 review fixes:** resumed E1 charges its run and the revise call; the resume mask respects compute headroom; the new nodes no longer print `test_score`, which the worker would have parsed into the ledger. 2 tests. |

Suite (Linux VM): **347 passed, 9 failed, 1 error**. The failures and the error are the pre-existing environmental set.

### Paper B (`r1/` package; this repo)

- **E1 (step 1):** `r1/noise/`. 1,952 runs over 11 nodes. Report `reports/NOISE_FLOOR_20261012.md`, tables `reports/NOISE_FLOOR_20261012_tables.md`, data `results/r1/pilot/E1_20261012T145353Z/`.
  - Five nodes qualify under the proposed D21 rule.
  - The OpenML logistic-regression nodes have zero training-seed noise.
  - `openml_credit_g` was not measured: there is no data cache and OpenML is blocked from the VM.
- **T1 (step 1′):** `theory/T1_MODEL.md` (model and literature map; 11 citations checked against their sources).
- **L8b (step 2):** see the harness table.
- **L9 (step 3):** `r1/branch/` (r1_branch_v1 schema, sibling table, instance-cluster bootstrap, `matching_report`).
- **T2 (step 3):** `theory/T2_DERIVATIONS.md` and `r1/theory/acceptance.py` (Propositions 1–5, Monte-Carlo-checked). D23 proposal in §7.
- **L10 (step 4):** `r1/baselines/` (ρ, always, random-matched, margin threshold, harness heuristic, KG index, ridge advantage, AWR-MLP, naive and leaf-split oracles; PACE-style and racing responses implemented but not scored).
- **E1b (step 5):**
  - Main run `results/r1/pilot/E1b_20261012T161034Z/` and sensitivity run `results/r1/pilot/E1b_vary_ionosphere_20261012/`.
  - Report `reports/HEADROOM_PILOT_20261012.md`.
  - The first E1b run is kept in `results/r1/pilot/invalid/` and was never analysed (L7 defect).
  - Headroom ceiling: +0.0006 (`"fixed"`, both nodes) and +0.0025 (`"vary"`, ionosphere). The scripted proposer stood in for the LLM.
- **L12:** `r1/llm_control.py` (forked side query; stub-LLM tests only).
- **L13:** `r1/controllers.py`, `r1/e2e.py`, `make r1-e2e`. One run in `results/r1/engineering/E2E_20261012T163133Z/` (produced before the L14 label fix, so its manifest still says PILOT).
- **T3 (step 6):** `theory/T3_SIMULATION.md`, `r1/theory/simulate.py`, data `results/r1/engineering/T3_20261012T161444Z/`.
- **L14 (step 6):** `reviews/BUILD_REVIEW_20261012.md`. A fresh-session AI review found 6 MAJOR and 14 MINOR findings. One correction round followed; the items still open are listed in the review.
- **Tests:** `make r1-test` → 64 passed.
- **E2 STOP (step 7):** `reports/E2_STOP_MEMO_20261012.md`. **The author decides.** The memo proposes:
  - the premise C1 holds;
  - verify-based C3 fails the pre-check;
  - L11 is not built yet;
  - next: an overnight LLM rerun of E1b on the Mac, a D4 amendment for run-free acceptance rules, then Phase 1 or the fallback paper.

### Not done, and why

- No LLM ran: the VM cannot reach Ollama. The E1b LLM rerun is a Mac command in the headroom report.
- Not pushed: neither repo.
- PACE was not scored: it needs its own `verify:pace` action version (D4).
- The E1 skip/revise and E0 stop/demote branches were not collected.

## 12 October 2026 — plan revised: R1-REFRAME, R1-INDEX, R1-GATE-FIRST

Planning only; no code and no runs. Author decisions of 12 Oct recorded in PLAN §1 and §10; PLAN §2, §3, §5, §6, §7, §9 and RUNBOOK §3 updated to match. Drafted by an AI agent (Claude) at the author's request.

- **R1-REFRAME.** The headline is incremental acceptance under noise. C2 is now B's own theory: the value of verify and of a raised threshold as functions of |Δ̂|/σ_n, ϱ and remaining budget; the winner's-curse bias of `current_best` and the stagnation it causes; built on ranking & selection, knowledge gradient, racing and best-arm identification. New theory track T1–T3 in the RUNBOOK.
- **R1-INDEX.** The primary contrasts are learned arms vs the C2 index policy (KG-style or PACE-style, D23). LLM self-control stays, with a stronger manager at least as a deployment check (D22). Baselines split into required and secondary.
- **R1-GATE-FIRST.** Before any model is built: E1 (noise per training seed and split seed, node selection D21) and a new E1b / 0.4b pilot headroom pre-check. D16 and L11 are deferred until the gate passes. Fallback = C1 + C2.
- **Compute map** added to RUNBOOK §3: the Mac, deepthought (many CPU cores, 4 × TITAN 12 GB) and Ada (shared 8 × RTX 6000 Ada).
- **Not committed.** The edits are in the working tree only.
- **New open decisions:** D21 (noise nodes), D22 (stronger manager), D23 (index policy).
- **Still open from 9 Oct:** the four batch-2 questions (Docker for MLGym, held-out OpenML nodes, the `lr_synthetic` split policy, `mlagentbench_vectorization`).

## 9 October 2026 — build batch 2: L4, L7, L8

All output is ENGINEERING_ONLY or PILOT: no evidence. Harness work is on
branch `r1` (now pushed), three commits on top of `3c80b53`:
`3a9f203` (L4), `1a2983b` (L7), `b55209f` (L8). Paper B: `9ff6f2a` (batch-2
prompt + PLAN §10 rows).

### Machine and baseline

- Apple M1 Pro, 16 GiB RAM, macOS 26.6.2 (build 25G83).
- Ollama 0.40.2 running locally. D15 model `qwen2.5-coder:7b` already present
  (no download): digest
  `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`,
  Q4_K_M, 7.6B params, Apache-2.0.
- Step-0 baseline (`uv run python -m pytest --continue-on-collection-errors
  -p no:cacheprovider -q`): **321 passed, 8 failed, 1 error, 4 subtests**. The
  8 failures are the same environmental set as Linux (3 artifact-manifest,
  5 KDD paper-section) and the error is the `src.autoresearch_worker`
  collection error. Linux batch 1 reported 9 failures; on macOS the
  artifact-report existence test passes because the report is already on disk.

### L4 — pinned local manager model (`3a9f203`)

- Files: `manager/langgraph_manager.py` (per-call latency/usage telemetry in
  `proposal.extra["llm_call"]`), `control_plane/campaign.py` (emits an
  `llm_call` event; default controllers emit nothing new),
  `scripts/run_campaign.py` (`--worker claw|local`, default claw),
  `scripts/r1_llm_latency.py` (new), `tests/stage2/test_r1_l4.py` (4 tests).
- Smoke tests, both on `lr_synthetic`:
  - dry-run with `--llm-stub`: 3 trials, no Ollama, no `llm_call` telemetry.
  - real `--budget 5` with the pinned model and `LocalWorker` (on a copied
    node): 5 trials, 3 kept, `net_gain` ~0.00085.
- PILOT latency (5 real calls, `PILOT` table; output in
  `experiments/r1/pilot/L4_20261009T151754Z/`):

  | metric | min | median | mean | max |
  |---|---|---|---|---|
  | latency (ms) | 5943 | 6203 | 7296 | 12003 |
  | prompt tokens | 611 | 620 | 618 | 620 |
  | completion tokens | 83 | 88 | 86.6 | 88 |

  Parse failures: 0/5. Side note: the model is deterministic only in
  structure; sampling at temperature 0.2 varied the proposals.

### L7 — restore and branching (`1a2983b`)

- Files: new `control_plane/snapshot.py` (`CampaignSnapshot`, capture, write/
  read, `restore_snapshot`, `SnapshotRecorder`, `FirstActionThenPolicy`,
  `resume_campaign`, `run_restore_audit`); `control_plane/campaign.py` gains
  an optional `snapshot_hook` (None by default) invoked at E0/E1/E2 and
  `initial_current_best` / `initial_incumbent_stack`; `nodes/spec.py` gains
  `branch_state_paths` (declared per node, defaults in the module);
  new `scripts/r1_branch.py`; `tests/stage2/test_r1_l7.py` (7 tests).
- Snapshot contents: editable bytes, the declared non-editable node-state
  paths (`artifacts`, `results.tsv`, `experiment_memory.jsonl`,
  `.autoresearch_artifacts`, `run.log`, node-declared caches), ledger prefix,
  explicit `current_best` and incumbent stack (verified flags), budget and
  compute-budget states, train/split seeds, manager config, controller
  identity, and the epoch-local proposal (E1) / provisional record and worker
  result (E2). Every layer has a SHA-256 hash in `manifest.json`.
- Restore copytree's into a fresh isolated dir with its own ledger and events;
  E1/E2 resume uses the captured proposal and does **not** re-call the manager.
  Forced first actions are honoured; infeasible ones are rejected to
  `continue` (F6 semantics), which the branch CLI showed for
  revise/verify/demote/stop at E1.
- **Restore audit** (exact equality, never a tolerance). Output in
  `experiments/r1/pilot/L7_20261009T152619Z/`:

  | node | epoch | original metric | replayed metric | reproduced | editable/node_state/ledger hashes match |
  |---|---|---|---|---|---|
  | lr_synthetic | E1 | 0.922558 | 0.922558 | yes | yes/yes/yes |
  | openml_breast_w | E1 | 0.990338 | 0.990338 | yes | yes/yes/yes |

- Branch CLI smoke (`scripts/r1_branch.py`, snapshot at lr_synthetic E1,
  h=1) wrote `branch_manifest.json`; siblings are isolated (test writes in one
  branch, checks the other).

### L8 — benchmark adapters (`b55209f`)

- Files: new `nodes/openml_template/` and five node dirs
  (`openml_breast_w`, `openml_credit_approval`, `openml_diabetes`,
  `openml_ionosphere`, `openml_wdbc`); five `configs/nodes/openml_*.yaml`;
  `nodes/registry.py` registers them; `nodes/spec.py` gains `held_out`;
  `nodes/mlagentbench_vectorization/train.py` reads `AR_SPLIT_SEED` for the
  random problem; `tests/stage2/test_r1_l8.py` (4 tests).
- Adapter table (PILOT output in
  `experiments/r1/pilot/L8_20261009T152916Z/L8_adapters.json`):

  | node | OpenML id | rows | feats | licence | determinism | 3-trial smoke | blocker |
  |---|---|---|---|---|---|---|---|
  | openml_breast_w | 15 | 699 | 9 | Public | deterministic (0.993156) | kept/discarded/discarded | — |
  | openml_credit_approval | 29 | 690 | 15 | Public | deterministic (0.909670) | kept/discarded/discarded | — |
  | openml_diabetes | 37 | 768 | 8 | Public | deterministic (0.829667) | kept/kept/discarded | — |
  | openml_ionosphere | 59 | 351 | 34 | Public | deterministic (0.984520) | kept/discarded/discarded | — |
  | openml_wdbc | 1510 | 569 | 30 | Public | deterministic (0.997642) | kept/discarded/discarded | — |
  | mlagentbench_vectorization | — | — | — | MIT | **not** deterministic: `speed_score = 1/runtime` is timing-based (24.61 vs 23.85) | kept/discarded/discarded | none; seed injection added for the random problem |

- Held-out marking: `held_out` is a `NodeSpec` field (default false) and is
  serialised; no node is marked held out yet (MLAgentBench stays a dev node,
  as the author noted; the MLE-bench Lite subset is not added in this batch).
- **MLGym feasibility** (`experiments/r1/pilot/L8_20261009T152916Z/mlgym_feasibility.json`):
  cloned `facebookresearch/MLGym` to
  `~/Documents/third_party/MLGym` (CC-BY-NC-4.0; 20 task configs). Every task
  runs inside a Docker/Podman container (`dockerfiles/mlgym.dockerfile`,
  per-task conda). **Blocker: neither Docker nor Podman is installed or
  running on this Mac.** No adapter written. Removing the blocker needs
  Docker Desktop (or Podman + a Linux VM); then light CPU tasks
  (`titanicSurvival`, `3SATTime`, game-theory tasks) could be attempted,
  subject to dataset downloads and agent/model configuration.

### Checks

- Full suite after batch 2: **336 passed, 8 failed, 1 error, 4 subtests** =
  the Step-0 baseline + 15 new tests (L4 4, L7 7, L8 4), with the identical
  8-failure / 1-error set. The L5 golden regression and every batch-1 test
  stay green.
- Default behaviour: `snapshot_hook` is None by default, `initial_*` default to
  the previous derivation, and no new event is emitted for deterministic
  managers.

### Not done, and why

- The `SnapshotRecorder` snapshots only the first matching epoch by default;
  E0 snapshots store no proposal (there is none at E0).
- `resume_campaign` rebuilds `LocalWorker` and deterministic / LangGraph
  managers from the manifest; a manager with an injected stub LLM must be
  passed back in (tests do this).
- The openml nodes need a one-time OpenML fetch (network); the pilot copies
  carry `data_cache`, so re-runs are offline.

### Open questions for the author

1. MLGym needs Docker or Podman; installing one is a system change. Proceed?
2. Should any of the five OpenML nodes be held out, or is the whole OpenML pool
   training/dev (per PLAN §6, the held-out benchmarks are MLAgentBench and the
   MLE-bench Lite subset)?
3. `lr_synthetic` verify: the pilot shows training-seed noise ≤ 1e-4 while
   split-seed noise is ~0.01. Under the default `"fixed"` split policy,
   lr_synthetic verify will mostly measure the candidate difference. Confirm
   `"fixed"` remains the choice for this node.
4. `mlagentbench_vectorization`'s `speed_score` is timing-based. Keep it as a
   dev node, or exclude it from branch/label collection where determinism is
   required?

## 9 October 2026 — batch 1 review and fixes

All ENGINEERING_ONLY. Seven review findings on harness branch `r1` (at
`201e025`) fixed, one commit each, then `r1` merged into harness `main`.
Tests ran in a Linux VM (Python 3.11.16, env built outside the repo; the
macOS `.venv` was not touched).

### Findings and commits (harness)

- **F1 (MAJOR) revise ignored its feedback — `8086f97`.** E1 `revise` now
  calls `propose_next_trial(..., revision_feedback=feedback)`.
  `LangGraphManager` adds a REVISION REQUEST block to the prompt and records
  `extra.revision_feedback` only when feedback is given; the default prompt is
  byte-identical (golden sha256 test). `revise` is also masked out for
  managers whose `propose_next_trial` lacks the keyword, so it cannot fall
  back to a plain resample. This answers open question 4 of the previous
  entry: the feedback channel is the `revision_feedback` keyword.
- **F2 (MAJOR) verify could run unseeded — `5ec9e9d`.** The E2 mask uses
  `hasattr(worker, "run_trial_at_seed")` (real and dry loops), and
  `_run_worker_at_seed` raises `SeedInjectionUnsupportedError` instead of
  falling back to `run_trial`.
- **F3 (MAJOR) demote could revert verified keeps — `ddba025`.** The mask
  input is now `top_of_stack_unverified`; `_perform_demote` pops exactly the
  top entry and refuses an empty stack or a verified top.
- **F4 (MAJOR) coupled seeds — `81c5bd5`.** `lr_synthetic` builds its dataset
  from `AR_SPLIT_SEED` and trains with `AR_TRAIN_SEED` (both default 42);
  `openml_*` `SPLIT_SEED` defaults to 42 independently. `_run_verify` and
  `run_real_campaign` take `verify_split_policy` (`"fixed"` default, or
  `"vary"`), recorded as `extra.control.verify.split_policy`.
  `LocalWorker.run_trial_at_seed(split_seed=None)` now keeps the worker's
  configured split seed, so "fixed" really re-runs on the campaign's split.
- **F5 (MINOR) LLM calls counted for deterministic managers — `04ba041`.**
  Proposals count against `max_llm_calls` only when
  `not getattr(manager, "deterministic", False)`, in both campaign loops.
- **F6 (MINOR) infeasible choice crashed the campaign — `6756d68`.**
  `_require_feasible` is gone. A masked-out or epoch-unsupported action emits
  `control_decision_rejected` `{epoch, action, mask}` and the trial continues.
- **F7 (MINOR) docs — `d9b4401`.** Docstrings (`run_real_campaign`,
  `run_dry_campaign`, controller module, `ComputeBudget`, `seeds`), the README
  R1 section and `CLAUDE.md` updated. `run_dry_campaign` is documented as
  continue-only; its `NotImplementedError` message now says so.

New tests: `tests/stage2/test_r1_review_fixes.py` (21 tests). Every finding
has at least one test that failed on the pre-fix code and passes after it. A
few companion tests guard behaviour that was already right and pass on both:
the F1 golden default prompt, the F2 mask with a seeded worker, the F3
single-top demote, and F5 counting for an LLM manager. Two existing tests
were adapted:
- `test_r1_l6.py`: the mask test uses the renamed keyword. The six-trial
  scripted run now demotes at trial 4 and verifies at trial 5, because a
  demote right after a verified keep is no longer feasible.
- `test_r1_defects.py` L3.4: with the dataset now fixed, train seeds 7 and 8
  give the same `lr_synthetic` val_score (0.921357). The different-seed check
  uses train seed 100 and tests the split seed separately.

### Checks (Linux VM)

| Run | Passed | Failed | Errors |
|---|---|---|---|
| Baseline, `r1` at `201e025` | 299 | 9 | 1 |
| After fixes, `r1` at `d9b4401` | 320 | 9 | 1 |
| `main` after merge (`3c80b53`) | 320 | 9 | 1 |

- The failures and the error are identical across all three runs and are
  environmental: the 9 failures are the same set as the macOS baseline (missing
  untracked ledgers, figures and paper sections; `/bin/zsh`), and the error is
  the `src.autoresearch_worker` collection error.
- **The L5 golden-fixture regression (`test_r1_l5.py`) passes on Linux**, at
  baseline and after every fix. The fixture was not edited.
- The tree of `main` after the merge is identical to `r1`.

### Merge and push

- Harness merge commit on `main`: **`3c80b53`** ("Merge r1: R1 build batch 1
  (L3, L5, L6) with review fixes"); `r1` is checked out again.
- `git push origin main r1` **failed**: `fatal: could not read Username for
  'https://github.com': terminal prompts disabled`. The VM has no GitHub
  credentials, and none were configured. Push both branches from the Mac.
- This STATUS commit's own push is attempted right after it is made; the
  result is in the session reply. It is expected to fail the same way.

### Observation for the author

- On `lr_synthetic` the training seed now barely moves the metric (≤ 1e-4 on
  val_score, often 0 at 6 dp), while the split seed moves it by about 0.01.
  Under the default `"fixed"` policy, verify's paired deltas on this node
  will therefore be almost entirely the candidate-versus-incumbent difference,
  with little seed noise. Choose whether `lr_synthetic` verify should use
  `"vary"`.

## 9 October 2026 (night) — build batch 1: L3, L5, L6

All ENGINEERING_ONLY: no evidence. Harness work is on branch `r1` of
`~/Documents/autoresearch_harness`, based on `da8dcbd` (7 commits, not pushed).

### L3 — the four harness defects (one commit each)

- **c4efce7** `prompt_manager`: added `deterministic = True` and a docstring
  stating it makes no LLM call; corrected `CLAUDE.md` and the `README.md`
  layout comment. Test: `TestPromptManagerIsDeterministic` (2 tests).
- **6e670dc** `ClawWorker`: the legacy path no longer stores `1 - val_bpb`
  under a `val_bpb` node's metric name (minimise nodes keep the raw sign;
  AUC-style nodes still convert). Test: `TestClawWorkerMetricSign`.
- **f446429** `_current_best`: now respects `metric_direction` and counts only
  `KEPT` records. Tests: `TestCurrentBestOnResume` (minimise resume; invalid
  high metric ignored).
- **bf3df0d** Seed injection: new `worker/seeds.py`; `LocalWorker` and
  `ClawWorker` pass `AR_TRAIN_SEED` / `AR_SPLIT_SEED` to node subprocesses;
  `nodes/lr_synthetic/train.py` and both `nodes/openml_*/benchmark.py` read
  them with 42 as the default. Tests: `TestSeedInjection` (same seed
  reproduces, different seed changes the metric; seed vars are not editable
  symbols).

Files changed: `src/autoresearch/manager/prompt_manager.py`,
`src/autoresearch/worker/{claw_worker,local_worker,seeds}.py`,
`src/autoresearch/control_plane/campaign.py`, `nodes/lr_synthetic/train.py`,
`nodes/openml_credit_g/benchmark.py`, `nodes/openml_bank_marketing/benchmark.py`,
`CLAUDE.md`, `README.md`, `tests/stage2/test_r1_defects.py`.

### L5 — decision hooks and budgets (bb15e01)

- New `control_plane/controller.py`: `ControlView`, `ControlDecision`,
  `Controller` protocol, default `ContinueController`, `build_control_view`
  (leak-refusing) and `compute_mask`.
- E0/E1/E2 hooks in `run_real_campaign` (and E0/E1/E2 in `run_dry_campaign`),
  with the E2 evaluate/commit split before the single immutable append.
- New `control_decision` event; the default controller emits nothing.
- New `ComputeBudget(max_worker_runs, max_worker_seconds, max_llm_calls)` next
  to `BudgetState`; with only `--budget N` behaviour is unchanged.
- CLI: `--controller`, `--max-worker-runs`, `--max-worker-seconds`,
  `--max-llm-calls` (documented in `README.md`).
- Tests (written first, against the unmodified code):
  `test_r1_l5.py::TestDefaultControllerRegression::test_dry_and_local_default_records_match_fixture`
  compares every non-excluded `TrialRecord` field against a golden fixture
  (`tests/stage2/fixtures/l5_default_records.json`) captured from the
  unmodified harness, for a dry campaign and a fixed-seed `LocalWorker`
  campaign; `TestControlViewLeak` (4 tests) rejects audit metrics, future
  records and sibling outcomes.

### L6 — actions (efca691, 201e025)

- `TrialDecision.SKIPPED` + `TrialState.SKIPPED` (PROPOSED → SKIPPED) with
  `TrialRecord` validation for skipped records (no metric, execution FAILED,
  validity VALID, no failure category, `extra.control`).
- `skip`, `revise`, `verify` (paired fresh-seed re-runs, frozen response rule,
  veto/rescue, hash-checked swaps), `demote` (incumbent stack) and `stop`;
  masks per problem spec §2.1.
- Skipped counted separately in `evaluation/metrics.py`, `memory/similarity.py`
  and `reporting/export_figures.py`; `summarizer.py` handles it via
  `decision.value`.
- Tests: `test_r1_l6.py` (10 tests) — one per action, the masks, the
  `TrialRecord.from_mapping` round-trip for skipped records, and a scripted
  controller issuing each action once across a 6-trial `lr_synthetic`
  campaign (with `LangGraphManager` + an injected stub LLM, no Ollama).

### Checks

- **Full harness suite** (`uv run python -m pytest --continue-on-collection-errors
  -p no:cacheprovider -q`): **299 passed, 9 failed, 1 error, 2 subtests
  passed**. L1 baseline was 277/9/1, so +22 new tests and **the same 9 failed
  and 1 error**. The failures are the pre-existing ones listed in the L1 entry
  below.
- **Default behaviour.** The L5 regression is green after every commit; the
  default `ContinueController` adds no record fields and no events.
- **New tests by name:** `test_r1_defects.py` (7), `test_r1_l5.py` (5),
  `test_r1_l6.py` (10). Full list in the session reply.
- **README dry-run:** `scripts/run_campaign.py --node lr_synthetic
  --campaign-id smoke --budget 3 --dry-run` runs cleanly. The `smoke` ledger
  already holds the 3 records from the L1 baseline check, so it resumes
  (`records_written=0`); a fresh id (`r1_check`) writes 3. A fresh run with
  `--max-worker-runs 2` stops after 2, confirming the compute cap.

### Not done, and why

- The `r1` harness branch is **not pushed**. Only the Paper B repo push was
  requested (L1). Say the word and I will push it.
- `run_dry_campaign` still raises for non-`continue` actions; the actions are
  implemented in `run_real_campaign`, which the L6 tests exercise. The runbook
  only asks for the dry path to carry the E0/E1/E2 hooks.
- `verify` re-runs use a synthetic (non-ledger) budget index and a no-edit
  proposal; the incumbent is restored from the pre-trial editable snapshot.
  The verify budget is measured but the per-run wall time is passed as 0.
- There is a pre-existing test-order flake: `test_artifact_completeness...`
  writes `paper/tables/artifact_completeness_report.txt`, and once that file
  exists one pre-existing failure flips to a pass (8 vs 9 failures). It is not
  caused by R1 code; I report the clean-tree count (`9 failed`).

### Open questions for the author

1. Push the harness `r1` branch to `origin`?
2. The runbook's verify rule sets `current_best` to the candidate's original
   single-run metric on a rescue or keep. On a rescue this can *lower*
   `current_best` (a rescued discard had a worse metric than the incumbent).
   Confirm that is intended, or change the rule.
3. `t_min` (stop threshold, default 3) and `verify_runs` (default 2) are
   function parameters only. Add `--t-min` / `--verify-runs` CLI flags?
4. `revise` records a fixed structured feedback string; the manager interface
   (`propose_next_trial(status, memory_context, node_spec)`) has no feedback
   argument, so the manager does not yet consume it. Confirm the intended
   feedback channel for L12.

## 9 October 2026 (evening) — build batch 1: L1

**L1 — Housekeeping.**
- **Paper B commit.** One commit, "Archive old Paper B plans; adopt route R1 canonical plan": the deletion of `docs/paper_split/`, the new `archive/old_b_2026-10-09/` and `docs/r1/`, the `README.md` banner, and the dated author decisions in PLAN §10 (D1, D3, D4, D14, D19, D20 — "decided 9 Oct 2026 by the author"). Pushed.
- **Harness.** Branch `r1` created from `main` at `da8dcbd` (the base commit). `uv sync --extra dev` succeeded. The `harness/claw-code` submodule is **not** initialised (D19).
- **Baseline test result** (`uv run python -m pytest --continue-on-collection-errors -p no:cacheprovider -q`): **277 passed, 9 failed, 1 error, 2 subtests passed**. Pre-existing, recorded not fixed:
  - `tests/test_artifact_completeness_and_manifest.py` ×4 (missing checked-in campaign report / manifest entries);
  - `tests/test_kdd_paper_sections.py` ×5 (the `paper/kdd_aae_2026/sections/*.md` files are absent);
  - `tests/test_legacy_noop_skip.py` error (imports `src.autoresearch_worker` from the uninitialised `harness/claw-code` submodule).

## 9 October 2026 (15:45) — build runbook and first prompt

Added `docs/r1/BUILD_RUNBOOK.md`, a per-step specification for L1–L14 written against the harness at `da8dcbd`, and `docs/r1/prompts/BUILD_BATCH1_PROMPT.md`, which covers L1, L3, L5 and L6 with the L2 defaults in an editable block. Nothing has been implemented yet.

## 9 October 2026 (15:30) — execution order adopted

RUNBOOK §3 gains the local-first order: build steps L1–L14 on the Mac, then experiments E1–E8. The next step is L1.

## 9 October 2026 (15:20) — configurator: encoder proposal

PLAN §7 is revised. The proposed primary is now a ModernBERT-family encoder decision model (Laya checkpoint vs plain ModernBERT-large), with late fusion of numeric features. Training is supervised, then an RL step with an RLCR-style bounded proper-score reward. Kev moves to the decoder comparison. D16 stays open.

## 9 October 2026 (afternoon) — format, benchmarks, configurator proposal

- **Author decisions:**
  - No manuscript format is fixed yet (R1-FORMAT).
  - ResNet-trigger is removed; experiments and configurator training use agent benchmarks across the board (R1-BENCH).
- **New open decision D20:** the benchmark set and scope. The proposal is in PLAN §6.
- **PLAN §7 gains** a verified candidate table and a proposed primary: Kev typed decision model; CLM, generative LLM and tabular as ablations. D16 stays open for discussion.

## 9 October 2026 (later) — venue, ledgers, harness clone

- **Author decisions:**
  - TMLR is the primary venue, with an ICML main-track quality bar (PLAN §9; D17 closed).
  - The original 1,355-trial ledgers are lost (D12 closed). Only aggregate tables survive, in the workshop-paper repo.
- **Harness clone.** `dowlingwong/autoresearch_harness` was cloned to `~/Documents/autoresearch_harness` at `da8dcbd`. The folder the author connected, `~/Documents/A-Governed-Harness-for-Auditable-LLM-Driven-ML-Experimentation`, is the workshop-paper repo (camera-ready; also the harness's submodule), not the harness code.
- **Note for the author.** Because the ledgers are lost, the `ClawWorker` `1 − val_bpb` sign issue cannot be checked for the workshop paper's autoresearch trials.
- **New default D14:** harness work on branch `r1` of that clone (confirm).
- **New open decision D19:** worker backend.

## 9 October 2026 — route R1 adopted; old plans archived; canonical plan written

- **Author decisions** (PLAN §1):
  - R1-ROUTE
  - R1-VENUE: rolling journal; TMLR recommended, to be confirmed as D17
  - R1-CARRY
  - R1-ARCHIVE
  - R1-PLAN
- **Archive.** All of the old `docs/paper_split/` moved to `archive/old_b_2026-10-09/docs_paper_split/`. The move includes the uncommitted §19 and §20 additions of 9 Oct and the 9 Oct prompt pack. Legacy code and the old manuscript stay in place for now (PLAN §8; RUNBOOK 0.1 decides).
- **New files:**
  - `docs/r1/PLAN.md`
  - `docs/r1/RUNBOOK.md`
  - this STATUS
  - `docs/r1/inputs/PROBLEM_SPEC_DRAFT_20261009.md`
  - `docs/r1/inputs/NOVELTY_SWEEP_20261009.md`

  The two inputs are AI-assisted subagent outputs and were not independently reviewed. In the sweep, three arXiv entries were spot-checked against their abstract pages (2607.05458, 2603.24647, 2608.21027). COTA's "0.5B" size is not stated on its arXiv page.
- **Not committed.** The file moves were made in the working tree with `mv`; nothing is committed yet. The first Phase 0 session commits them as one change: "Archive old Paper B plans; adopt route R1 canonical plan".
- **Next:** Phase 0 (RUNBOOK §3). The first prompt covers 0.1–0.3.
- **Open:**
  - D1–D12 and D14–D18 (PLAN §10);
  - the configurator architecture discussion (D16);
  - venue confirmation (D17).
