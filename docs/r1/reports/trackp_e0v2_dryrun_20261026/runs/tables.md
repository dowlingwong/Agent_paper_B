| run | stage | RPS | width slope vs label std | (v1: vs s) | mean slope | width ratio | steps |
|---|---|---|---|---|---|---|---|
| kev-0.8b fresh_hard | head fit (frozen) | 0.0799 | **-0.003** | -0.003 | 0.160 | 1.85 | best 1900 / stop 2000 |
| kev-0.8b fresh_hard | + LoRA | 0.0373 | **0.055** | 0.041 | 0.808 | 0.27 | best 100 / stop 600 |
| kev-0.8b fresh_soft_lr0.0001 | head fit (frozen) | 0.0430 | **-0.001** | -0.002 | 0.122 | 2.09 | best 1600 / stop 2000 |
| kev-0.8b fresh_soft_lr0.0001 | + LoRA | 0.0002 | **0.923** | 0.862 | 1.012 | 1.08 | best 1700 / stop 2000 |
| kev-0.8b fresh_soft_lr1e-05 | head fit (frozen) | 0.0430 | **-0.001** | -0.002 | 0.122 | 2.09 | best 1600 / stop 2000 |
| kev-0.8b fresh_soft_lr1e-05 | + LoRA | 0.0006 | **0.783** | 0.724 | 1.017 | 1.15 | best 2000 / stop 2000 |
| kev-0.8b fresh_soft_lr3e-05 | head fit (frozen) | 0.0430 | **-0.001** | -0.002 | 0.122 | 2.09 | best 1600 / stop 2000 |
| kev-0.8b fresh_soft_lr3e-05 | + LoRA | 0.0003 | **0.853** | 0.797 | 1.024 | 1.12 | best 1900 / stop 2000 |
| kev-0.8b native_soft | zero-shot (native) | 0.0778 | **-0.029** | -0.026 | 0.035 | 2.08 | 0 |
| kev-0.8b native_soft | + LoRA | 0.0000 | **0.943** | 0.878 | 1.023 | 1.04 | best 1800 / stop 2000 |
| qwen3.5-0.8b-base fresh_hard | head fit (frozen) | 0.0627 | **0.003** | 0.003 | 0.304 | 1.70 | best 1900 / stop 2000 |
| qwen3.5-0.8b-base fresh_hard | + LoRA | 0.0383 | **0.023** | 0.016 | 0.831 | 0.20 | best 100 / stop 600 |
| qwen3.5-0.8b-base fresh_soft_lr0.0001 | head fit (frozen) | 0.0340 | **0.003** | 0.004 | 0.228 | 1.93 | best 2000 / stop 2000 |
| qwen3.5-0.8b-base fresh_soft_lr0.0001 | + LoRA | 0.0002 | **0.971** | 0.910 | 1.009 | 1.11 | best 1900 / stop 2000 |
| qwen3.5-0.8b-base fresh_soft_lr1e-05 | head fit (frozen) | 0.0340 | **0.003** | 0.004 | 0.228 | 1.93 | best 2000 / stop 2000 |
| qwen3.5-0.8b-base fresh_soft_lr1e-05 | + LoRA | 0.0014 | **0.646** | 0.599 | 0.955 | 1.11 | best 1800 / stop 2000 |
| qwen3.5-0.8b-base fresh_soft_lr3e-05 | head fit (frozen) | 0.0340 | **0.003** | 0.004 | 0.228 | 1.93 | best 2000 / stop 2000 |
| qwen3.5-0.8b-base fresh_soft_lr3e-05 | + LoRA | 0.0004 | **0.863** | 0.810 | 1.011 | 1.14 | best 1800 / stop 2000 |
| qwen3.5-0.8b-base native_soft | zero-shot (native) | 0.0585 | **-0.000** | -0.000 | 0.000 | 2.63 | 0 |
| qwen3.5-0.8b-base native_soft | + LoRA | 0.0002 | **0.813** | 0.758 | 1.026 | 1.11 | best 1700 / stop 2000 |
