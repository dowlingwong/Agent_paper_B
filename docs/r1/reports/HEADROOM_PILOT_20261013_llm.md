# E1b LLM pilot headroom pre-check — 20261013

**PILOT. AI-assisted execution and report by Claude (runner) on Ada, started by the author. Not evidence; no human review.**

## What ran

Run `results/r1/pilot/E1b_20261013T151857Z` on `ucrtasl`; harness `9c4902d0d8776f18a081e1ff2478d651fc7096c1`; manager LangGraph/Ollama `qwen2.5-coder:7b`, digest `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`; GPU `1, GPU-aa340032-6f94-9783-8f3d-50a15da47a6f, NVIDIA RTX 6000 Ada Generation, 48427`; Ollama `{'version': '0.9.2'}`.

Six instances per node, digits_mlp and openml_ionosphere; W=20 worker runs; E2 points 4, 8, 12; continue and verify, r=2, two repetitions; six common fresh joint audit seeds 5001–5006. Verify split policy fixed. Every branch continues under the default rule at matched worker budget.

Collection checks: `{"label": "PILOT", "leaves": 144, "collection_failures": 0, "manager_kind": "langgraph", "llm_calls": 1440, "parse_failures": 0, "proposal_examples": ["increase-hidden-units-64", "increase-hidden-units-128", "increase-hidden-units-256", "increase-batch-size-128", "increase-batch-size-128"]}`.

## Headroom bracket and scripted comparison

Naive oracle is biased upward; its upper confidence bound is a conservative ceiling. Leaf-split oracle is biased downward with two repetitions. These are pilot inputs for this proposal law, nodes and budget.

| Node | Proposer | Best simple | Naive headroom (95% CI) | Leaf-split headroom (95% CI) |
|---|---|---|---|---|
| digits_mlp | LLM | always_verify | +0.0001 [+0.0000, +0.0004] | +0.0001 [-0.0000, +0.0003] |
| digits_mlp | scripted | rho | +0.0002 [+0.0000, +0.0003] | -0.0002 [-0.0013, +0.0007] |
| openml_ionosphere | LLM | rho | +0.0000 [+0.0000, +0.0000] | +0.0000 [+0.0000, +0.0000] |
| openml_ionosphere | scripted | rho | +0.0004 [+0.0000, +0.0009] | -0.0046 [-0.0107, +0.0010] |
| ALL | LLM | always_verify | +0.0001 [+0.0000, +0.0002] | +0.0001 [-0.0000, +0.0002] |
| ALL | scripted | rho | +0.0003 [+0.0001, +0.0006] | -0.0024 [-0.0058, +0.0005] |

## Deviations

The initial named host Deepthought2 has two L40S cards, while the author-approved fallback Deepthought has four TITAN X cards. The execution host was ucrtasl; one card was used. Under the author’s 13 Oct co-tenancy decision (PLAN §10) the card could be shared with other users’ processes when its free memory was at least the model footprint plus 2 GiB; the per-step GPU census is in the batch log `gpu_census.jsonl`, and latency is descriptive only. Scratch paths are unique under the batch log directory to preserve pre-existing directories. No second Ollama instance was started; Ollama serializes inference, and OMP/OpenBLAS/MKL are capped at one thread per worker. Archived snapshot/noise paths were made repository-relative, with original paths recorded; proposal ledgers and snapshot bytes are included for regeneration. As in the scripted pilot, only E2 continue/verify is branched; E1 skip/revise and run-free rules are not evaluated, PACE is not scored, and this is not a stronger-manager deployment check.

## What this changes for the E2 STOP

The table adds headroom under the pinned LLM proposal law alongside the scripted proposal law. It is input to the author’s E2 STOP, not a go/no-go decision: D18, D21, D23, the D4 amendment and any split-policy revision remain open. The two-repetition oracle bracket is noisy and the pilot does not establish a learning gain. L11 remains unbuilt.
