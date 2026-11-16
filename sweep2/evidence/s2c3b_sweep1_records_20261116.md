# S2-C3b sweep-1 liveness / prompt-length records — read-only location record (16 Nov 2026)

**ENGINEERING_ONLY.** Read-only check for the S2-C3b prompt-length re-measurement. Two sources were inspected:
the pinned paper checkout (`9ae6d87783f53f9da27200869085c9ed0e7697e2`) and the deepthought ETP batch tree that
produced sweep 1. No file was written on deepthought for this check (the only remote writes were the local
`/tmp/s2c3b_dryrun_20261116T1109Z/` staging dir for the reviewed `condor_submit -dry-run`; nothing was queued).

## 1. Sweep-1 D28 liveness record (the liveness baseline)

- Repository path: `results/r1/engineering/liveness_c3_20261027T152425Z/`
- Deepthought path (same content; SHA-256 compared):
  `/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/agent_paper_B/results/r1/engineering/liveness_c3_20261027T152425Z/`
- SHA-256 (identical in both places):
  - `liveness.json` `3f64604e925082e8d639c0f95a9955ebf825cbd7be2f70fbb2aebbf4ab14b6f5`
  - `manifest.json` `154f5f4832eaf2b673f475baa931f62b03ef37e330b0707013666d50ab76bd15`
  - `ledgers/digits_mlp__s104/root_trials.jsonl` `ed3b55eee0a24130526651feedbef2069322452ad009cb37cfba0f08eca5d61d`
- Content: 8 nodes, 2 instances each (16 campaigns), W = 10, memory `append_only_summary`, manager `langgraph`
  (`llamacpp/r1-manager`), label `ENGINEERING_ONLY`; `liveness.json` says all eight nodes PASS.
- The manifest's `campaigns` list is the sweep-1 D28 seed record: per node the seeds are the pinned
  `_instance_seed(node, k = 0,1)` values (digits_mlp s104/s114, tabular_mlp s102/s112, openml_breast_w s105/s115,
  openml_ionosphere s103/s113, openml_wdbc s100/s110, openml_credit_approval s100/s110, openml_sonar s105/s115,
  openml_climate s104/s114).

## 2. Sweep-1 prompt-length record

There is **no separate prompt-length file** in the batch tree or the repository (a `find` over
`.../2YSBbw/results` for `*prompt*` returned nothing). The recorded prompt lengths are:

1. **Per-call `usage.prompt_tokens` in the sweep-1 D28 liveness ledgers** (16 ledgers under
   `results/r1/engineering/liveness_c3_20261027T152425Z/ledgers/`), together with the exact prompt text hash
   `extra.manager.context_sha256`. The two instances of every node recorded the same trial-1 prompt tokens
   (514, 520, 482, 481, 484, 489, 497, 513 for the eight nodes) — the trial-1 prompt is seed-independent.
2. **The recorded 1,345-token maximum** ("manager prompts are ... at most 1,345 tokens (memory on, W = 20,
   rerun-2)", `docs/r1/RUNBOOK.md` "Context" note, counted with the 7B tokenizer). The number itself is the
   `proposal.extra.llm_call.prompt_tokens` / `provisional.extra.manager.llm_call.prompt_tokens` value in
   `results/r1/pilot/E1b_rerun2_A_PARTIAL_memory_on_20261014/provenance/snapshots/tabular_mlp__s142/E2_b012/manifest.json`
   (SHA-256 `5e269d4cee24e263ee36f25cd087df6f489bbec5b8a5db51f5236b438310e605`; the same file exists under the
   deepthought batch tree at the same relative path with the same SHA-256).

## 3. Seed-set sources (used by the disjointness check)

- `results/r1/pilot/C3_sweep_index_20261028T033315Z.json` (SHA-256
  `812468e26c0901a6cb5b3241f44a46fd4d1d2e498d172b76d63b1e91f6d835ab`): `instances: 18`, the eight nodes, the
  sweep-1 liveness path, and the audit seeds 7001-7010.
- `r1/headroom/e1b_collect.py` (SHA-256 `0001260442f9647461fd867a53fb74867a2b0e65810d9547eeb093a39e4b3271`):
  `_instance_seed(node, k) = 100 + 10*k + sum(ord(node)) % 7`; `run_root` uses k = 0 .. instances-1.
- The full sweep-2 instance-seed list is **derived, not stored as a list**: R1-MAIN-PROPOSER (b) fixes sweep 2 to
  sweep 1's instance seeds, so it is `{_instance_seed(node, k)}` over 8 nodes × 18 k = 90 distinct seeds
  (SHA-256 of the sorted compact JSON `0d7f0e599ecc88f1da6c3724067e319f5714df4d2b0f415833a2b8fafaa7843d`).
  The S2-C4 pilot roots `digits_mlp__s104` / `digits_mlp__s114` are the k = 0,1 members of that list.

## 4. Verification commands (read-only)

```
ssh deepthought.etp.kit.edu 'sha256sum <batch-tree>/.../liveness.json .../manifest.json .../<ledger>'
# -> the three digests above, byte-identical to the repository copies
ssh deepthought.etp.kit.edu 'sha256sum <batch-tree>/.../E2_b012/manifest.json'
# -> 5e269d4cee24e263ee36f25cd087df6f489bbec5b8a5db51f5236b438310e605
```

No job was submitted; no HTCondor state was changed; nothing on deepthought was modified.
