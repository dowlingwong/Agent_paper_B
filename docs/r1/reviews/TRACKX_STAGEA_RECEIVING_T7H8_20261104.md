# Track X Stage A — receiving review of attempt `r1_stagea_20261103_t7h8` (TASL-7)

Reviewer: the independent reviewer (not the implementer). Review time: 2026-11-04 (Europe/Berlin);
read-only host observations timestamped UTC. No process was signalled, no lock acquired, no server started,
no GPU/model job launched. TASL-7 access read-only (`ls`/`cat`/`stat`/`sha256sum`/`git`/`/proc`/
`nvidia-smi`).

**Verdict: `ACCEPT` (with conditions).** `t7h8` is the Stage A evidence set: the batch ran to COMPLETE (24
rows), the guardian validated the completion over **43/43** server records and released the lease
(`released:true`, `reason:validated_completion`), the preflight (M1) and the 187-file Stage A manifest are
consistent, the STOP-6/7/8 fixes are validated in the real run, and all 20 replay offload records are
`full:true, route:log_line` with no CPU fallback. The 8 PASS candidates plus the three anchors are the Stage A
PASS evidence; the 12 template/grammar exclusion rows and the one offload row are recorded candidate-level
failures. Under the author's stated template policy (exclusion rows now; targeted byte-equal repairs after
completion; build-pin only after a diagnostic) the evidence is acceptable, subject to the conditions in §6.

---

## 1. Run identity (verified)

| Item | Value |
|---|---|
| Attempt | `r1_stagea_20261103_t7h8`, host TASL-7 |
| Code / binding | `3b3283f` (bounded GPU-quiescence wait) + config binding `19b8f33` (`paper_commit=3b3283f`); clone HEAD `19b8f33`, clean |
| Manifest | Stage A `95bfc8b6197127b726ee135cf6e2882570a0d9e4bffc324d2442bdccde98f7ab` (187 pinned files); preflight `5f44064313283ac489593102a35a5f263808166b1ee1276d6d5b792bff57b10d` |
| Start / release | `2026-11-03T20:25:49Z` → `2026-11-04T12:44:31Z` (16 h 18 m 42 s), single continuous guardian lock |
| Preflight (M1) | `checkpoint.json`: checkpoint `19b8f33`, `clean:true`, host TASL-7, code-file hashes (launcher `1bfb30c8…`, guardian `ebdfcf40…`, config `1153a848…`, exam_runner `eeec5e9a…` = v15, llama_server_instance `b697fc44…` = v14b, runtime `67978bb9…`, qualify `496097c1…`, cooperative_lease `989d4f1b…`, cache_runtime `12b56012…`), manifest `5f440643…`, binary `b70f488248…`, prompts `70872a77…`; preflight release `released:true, validated_completion`, records_verified 1 |
| Post-release | no guardian, LOCK-FREE (`gpu0.lock` dev 66306, inode 56251186, size 0, nlink 1), GPU idle (236 MiB, 0 %), 22/22 models `.verified` |

## 2. Batch / table / lease evidence (verified hashes and content)

- `batch_state.json` `ae6adef583cf25782db2ead73b0a0275b949a0beca31fdc1e261d191e17ab596` — **status COMPLETE,
  24 rows, no stop_reason/interruptions**.
- `stage_a_table.json` `00ab143dc0742b24034e653bfa15acff5183538f85a1179cdbc7802cac22975c` — **24 rows**:
  11 PASS (8 candidates + `random_valid`/`scripted`/`qwen25_coder_7b` anchors), 7 `template`, 2
  `grammar+template`, 3 `grammar`, 1 `offload`. The 50-prompt rows have `prompts:50`, `cache_prompt_planned:
  false`, schema/free parse evidence, `seed_reproducible:true`, the D3 `descriptive_cache_true` event, and the
  sample rows show `first_call:true, prompt_tokens_cached:0` at sequence 1 (cold true-first). `qwen25_coder_7b`
  and a sample of PASS rows' template checks are `[true,…]`; the template-failure rows' checks are
  `[false,…]`; `olmo31_32b` has no replay (`template_checks:null`, qualification parser failure).
- Lease: `start.json a6f54d3d…`, `lease_inheritance.json 2e1a90d9…`, `lease_completion.json 5836c654…`,
  `lease_release.json 415eb713…` — all match. `lease_completion` has **43 servers** (`runner_start_ticks`
  285228860, batch_state digest `ae6adef5…`); `lease_release` `released:true`,
  `reason:"validated_completion"`, `records_verified:43`, `completion_sha256 5836c654…`, guardian 3896322,
  method `close_fd_after_validated_completion`, kcmp direction guardian→runner, utc 2026-11-04T12:44:31Z.
- **43/43 records verified:** 43 `llama_server_*.json` files under the run root; 43 in the completion;
  **0 uncovered, 0 extra, 0 digest mismatches**; 0 records lacking `stopped_utc` or `lease_inheritance`.
  The three failed-start probes (`olmo31_32b` template; `nemotron35_30b_a3b` 32k and 16k OOM) carry
  `stopped_utc`, `returncode 1`, and SAME-OFD `lease_inheritance` (`kcmp_same_ofd:true`) — the STOP-7 fix is
  validated in the real run, and the guardian's completion validation accepted them.
- The 20 replay `servers/*/exam_offload.json`: **20/20** `full:true`, `route:log_line`, no CPU fallback; the
  nemotron/olmo candidates have no replay server (qualification failures) — consistent with the table.
- The failed-start probes are the only server records with `exited_early`; the 20 replay servers and the
  other qualification probes carry `stopped_utc` + inheritance. No survivor record exists.

## 3. Candidate outcomes (per table; verified)

- **PASS 8:** `glm47_flash` (p50 0.84 s), `ornith10_35b` (0.85), `ornith10_9b` (0.98), `qwen35_9b` (0.98),
  `qwen36_27b` (3.04), `qwen36_35b_a3b` (0.89), `qwen38_27b` (3.09), `qwen3_coder_30b_a3b` (0.63); plus the
  anchors `random_valid`/`scripted`/`qwen25_coder_7b` PASS.
- **`template` 7:** `devstral_small2_24b`, `gemma4_12b`, `gemma4_26b_a4b`, `gemma4_31b`, `laguna_xs21`,
  `ministral3_14b`, `olmo31_32b` (parser startup; prompts 0).
- **`grammar+template` 2:** `lfm25_24b_a2b`, `muse_glimmer_30b`. **`grammar` 3:** `gpt_oss_20b`,
  `rico03_qwen36_27b`, `olmo31_32b_think` (sensitivity). **`offload` 1:** `nemotron35_30b_a3b` (32k OOM
  mechanical failure + 16k retry; prompts 0).
- The 8 PASS rows are the Stage A PASS evidence (50 prompts, seed reproducible, explicit `cache_prompt:false`,
  cold first call, offload route (i) `log_line`); the failure rows are candidate-level exclusions; the
  `olmo31_32b_think` row is the sensitivity (grammar), not a candidate PASS.

## 4. Evidence-set classification

`t7h8` is the **only** Stage A evidence set: COMPLETE batch + guardian-validated release + preflight M1 +
187-file manifest. The earlier attempts are **not** Stage A evidence:
- `t7c3` (STOP-4 template STOP), `t7d4` (STOP-5 census), `t7e5` (STOP-6 OOM), `t7g7` (STOP-8 quiescence) —
  STOPPED; `t7f6` batch COMPLETE but the completion validation STOPped (STOP-7), so its rows are engineering
  evidence only and it has no validated release. None are reused.

## 5. Fix validations in this run

- STOP-6 (real-shape 32k OOM → mechanical failure + 16k retry) — nemotron rows present.
- STOP-7 (failed-start records carry `stopped_utc`/`returncode`/SAME-OFD `lease_inheritance`; the guardian
  validated all 43 and released) — validated for the olmo and both nemotron probes.
- STOP-8 (bounded quiescence wait; the 16k retry proceeded) — the t7h8 run completed the 16k retry without a
  transient GPU-unavailable STOP.
- The STOP1–8 reports are on the docs branch; the template failure map + 5/50-prompt render-diff analysis
  starts per the author's policy.

## 6. Conditions for the next phase

1. **Stage A evidence acceptance:** the 8 PASS candidates + `random_valid`/`scripted`/`qwen25_coder_7b`
   anchors are the Stage A PASS evidence; the 7 `template` + 2 `grammar+template` + 3 `grammar` rows are
   candidate-level exclusions and the 1 `offload` (nemotron) row is the recorded offload failure — all under
   the author's template policy (exclusion rows now; targeted byte-equal repairs after completion; build-pin
   only after a diagnostic). The `olmo31_32b_think` grammar row is a sensitivity result, not a candidate PASS.
2. **Template map / render-diff:** produce the template failure map + the 5/50-prompt render-diff analysis;
   the targeted byte-equal repairs and any build-pin decision remain separate author decisions (the build pin
   only after a diagnostic). No template/build change is authorized by this review.
3. **B1/B2 remain STOP** (and P.3a/B.2): no B1/B2 run is authorized by this receiving review; the B1 gate
   needs the author's separate authorization, the eligible-candidate set, and the template-policy decision.
4. **Evidence retention:** keep the `t7h8` batch/table/lease/manifest/preflight evidence (hashes above) and the
   STOP1–8 reports; do not reuse or relabel any STOPped batch; the t7h8 only is Stage A evidence.
5. **M3/environment:** record the environment (the manifest argv venv, the batch `template_reference_versions`
   transformers 5.20.2 / jinja2 3.1.6 / tokenizers 0.23.3, the HF cache) with the completion report.
6. Commit the Stage A completion report on the coordinator docs branch; keep the author's template policy
   (exclusion / byte-equal repair / build-pin-after-diagnostic) recorded in PLAN.

## 7. NOT CHECKABLE in this review

- The B1/B2 phases (STOP; not run).
- The template byte-equal repairs and any build-pin (future, separate author decisions; the render-diff
  analysis is starting).
- Host-global single-server / same-UID non-interference (carry over, NOT_CHECKABLE).
- The long-run host-global claims beyond the validated lease/completion evidence.

## 8. Final verdict

**`ACCEPT`** of the Stage A evidence set `t7h8`, with the §6 conditions. The batch is COMPLETE (24 rows), the
guardian validated the completion over 43/43 server records and released the lease, the preflight/M1 and the
187-file manifest are consistent, the STOP-6/7/8 fixes are validated in the real run, the 20 replay offload
records are `full`/`log_line` with no fallback, and the 8 PASS candidates + 3 anchors form the Stage A PASS
evidence with the 12 template/grammar exclusions and the 1 offload failure recorded as candidate-level rows.
The 8 PASS candidates and the recorded failure classes are acceptable under the author's template policy,
subject to the template map/render-diff, the targeted repairs (or build-pin after a diagnostic), and the
B1/B2 remaining STOP.
