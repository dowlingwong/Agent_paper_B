# Independent review of the H200 Track P E0 submission

_18 November 2026 · Paper B R1 · Static pre-submission review · DRYRUN / ENGINEERING_ONLY_

---

## Verdict

**ACCEPTED on revision, subject to the published execution gates below.** The revised handback preserves the per-prompt predictions and identifies both hosts. The historical workload, pinned image, reference selection and tolerance arithmetic are acceptable. E0 submission requires completed and accepted v2 I2/I3 and H200 smoke records.

The reviewed unit is `trackp_stage/e0_h200` at the following hashes. The `origin/main` snapshot supplied for review was `50176481cbc85fb9e5b5dd97887043dea6e528fb`. This review used local objects and staged files.

| File | Accepted SHA-256 |
|---|---|
| `probe.sh` | `24688a109787d15be1718eb695167529ee615f72e32c41770f09be0cf04c148b` |
| `probe.jdl` | `eeb4606b38ea73b361f019836e9aedd689ec604426b8bf4fd8eb02780db7282e` |
| `nvidia-smi-scoped` | `ec88ddfe03eab01d7b7762ea726f2879921de782a7083ec73097ba751ded5af1` |
| `compare.py` | `bd957c0d3e984b4ec9e27ef090d29580654cfef91d73174bf05a615cd4bf6084` |

## Findings

1. **Resolved — prediction and training artifacts.** The first version copied only aggregates and the manifest. The accepted `probe.sh:80–83` saves `pred_test_lora.npy`, `pred_test_head_fit.npy`, `head_fit/curve.jsonl`, `lora/metrics.jsonl` and `lora/best.json` in the transferred handback, ahead of the numerical STOP. The new files support the runbook's independent recomputation and review of early stopping.
2. **Resolved — comparison identity.** The historical comparator's `portal` key represents the TASL-7 reference in this job and its `tasl7` key represents H200. The accepted `probe.sh:92–93` puts the explicit mapping in `handback/comparison_identity.txt` before invoking the byte-identical comparator. TASL-7 remains the baseline denominator.

## Reference and numerical rule

Mission 3 of `CLUSTER_AGENT_PROMPT_20261118.md` and published PLAN §10 `R1-HTC-QTORCH` / `R1-QTORCH-AMEND` govern the relocation. The Track P runbook's host-migration rule supplies the E0 v2 procedure and tolerance. The v2 proposal at `cbd0238e` explicitly identifies the TASL-7 equivalence record as the reference for HTCondor. The historical `PREDECLARATION.md` specifies how TASL-7 was compared to the portal and fixes the same three criteria. Both staged references are byte-identical to the TASL-7 `run/report.json` and `run/manifest.json` at published `main`. The old portal comparison also reproduced exactly when evaluated using the staged comparator and the historical portal and TASL-7 reports.

| `lora.test` metric | TASL-7 reference | H200 tolerance |
|---|---:|---|
| `width_slope_vs_label` | 0.9134840344314319 | Absolute difference ≤ 0.05 |
| `mean_slope` | 1.019259573471914 | Absolute difference ≤ 0.05 |
| `rps` | 0.00019400102792893227 | Absolute difference divided by absolute TASL-7 RPS ≤ 0.10 |

All three criteria must pass. I independently exercised one synthetic miss for each criterion and verified exit status 1 and the corresponding failed row. A numerical miss is a STOP for the author. The historical descriptive fields include head fit, early stopping, interpolation and extrapolation RPS, width ratio and slopes.

## Workload and host compatibility

- The detached paper checkout is pinned to `8e13e77cd49532c7ac2e78ad8e5c1ee45401b286` and the harness to `897d83c8efa364ec2fdd37288241cc42e01d7274`, matching both reference manifests. The script checks full SHAs and clean trees after fetching. The historical harness object was absent from the local review clones, so I checked its identity against the two manifests and statically inspected the runtime fetch and SHA check. Execute-node checkout success remains to be verified at runtime.
- The equivalent E0 command uses `kev-0.8b`, `DRYRUN`, `fresh`, adapter LR `0.0001`, and seed 0. It uses the soft target and fresh LayerNorm plus linear head through the historical CLI defaults. The source config digest independently recomputed to `588869fa8e721eec2005607dc25f6f46229aa0960bd3f64dbf5155323094f4b9`. The relocation changes the host label, GPU identity and paths. The source settings retain bf16, gradient checkpointing, head LR `0.001`, token LR `0.0001`, two stages capped at 2,000 steps each, evaluation every 100 steps, patience 5, and batch size 8. The staging shell sets offline Transformers and scratch HF cache. The revision removes the initial staging CPU thread overrides. Config comments still describe the historical environment where applicable. The installed CUDA extension architecture is established by the image build record.
- The pinned synthetic dataset's compressed bytes hash to `4f4db29b6a4c0ca0181825e5c2c0fb031521e034a006990b93686cd5fffc8290`. Together with the six validation cells, it reproduces manifest digest `b963be2dd378241e0b0689907d4051bfa62922a8e4968aa40061ed7ef275bfef`. The historical loader verifies those data bytes and the wrapper rejects a differing post-run manifest. The reference split contains 2,714 train, 286 validation and 1,000 test prompts.
- The staged registry is byte-identical to the historical checkout's registry. `stage_models.py` fetches the 12 registered files for each of `Qwen/Qwen3.5-0.8B-Base` @ `dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68` and `jaredpalmer/kev-0.8b` @ `788ddbdd65715bb03a56788c822f6c632c9a551d`, and checks size and SHA-256 for each. This preserves the starting weights and tokenizer. The run manifests' trained adapter/head hashes report the result of each bf16 training run.
- The JDL requests one NEMO2 H200 and pins the v2 GPU digest `sha256:b1144ecec7ffe07642ff108fb9624aa34775cb873ed17f835ea3e3c87bc024fd`. The digest matches `R1-QTORCH-AMEND` and v2 CI build run `43775496127` recorded at `cbd0238e`. The image's env3 freeze input is byte-identical to the published Track P freeze (`50238e5a07ca259c0dede08adfc42cc3473d29c222157994b6f284dabe0b9a08`). The recipe checks the installed sorted freeze, uses Python 3.12.15 and torch 2.6.0+cu124, and builds causal-conv1d for SM 8.0, 8.9 and 9.0. The job checks the visible device count, name and SM 9.0 at runtime, and records UUID, driver and HTCondor allocation metadata. Its job scratch lock and scheduler allocation provide the relocated lease context. The added shell wrapper accepts only the historical `nvidia-smi --query-compute-apps` argument pair, calls the real utility with the UUID of the sole CUDA-visible GPU, and propagates failures and output. The historical live `origin/main` STATUS check and Track X marker check are still active. The H200 smoke exercises the scoped query and live STATUS dependency before this job. Both revised shell files pass `bash -n`.

## Submission and receiving gates

Recheck the current published PLAN, the accepted v2 I2/I3 results, and the independent review accepting the H200 smoke at code D `8662e359` before submitting this one E0 job. Record the actual job ID, host, GPU and driver, scheduler walltime, E0 lease duration, full handback hashes and the independent result review. The Q-TORCH gate concerns H200 compatibility. Mission 3 restricts this unit to engineering.
