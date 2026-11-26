| run | stage | RPS | width slope vs label std | (v1: vs s) | mean slope | width ratio | steps |
|---|---|---|---|---|---|---|---|
| kev-0.8b final | head fit (frozen) | 0.0166 | **0.007** | 0.011 | 0.870 | 0.78 | L-BFGS 390 outer, converged True |
| kev-0.8b final | + LoRA | 0.0025 | **-0.021** | -0.018 | 1.028 | 1.28 | best 400 / stop 400 |
| kev-0.8b hard | + LoRA | 0.0344 | **0.003** | 0.003 | 0.835 | 0.66 | best 100 / stop 400 |
| kev-0.8b native | zero-shot (native) | 0.0778 | **-0.029** | -0.026 | 0.035 | 2.08 | 0 |
| kev-0.8b native | + LoRA | 0.0002 | **0.862** | 0.804 | 1.019 | 1.12 | best 400 / stop 400 |
| kev-0.8b screen_lr0.0001 | + LoRA | 0.0028 | **-0.012** | -0.012 | 0.968 | 1.26 | best 200 / stop 200 |
| kev-0.8b screen_lr1e-05 | + LoRA | 0.0062 | **-0.010** | -0.015 | 0.848 | 1.26 | best 200 / stop 200 |
| kev-0.8b screen_lr3e-05 | + LoRA | 0.0037 | **-0.013** | -0.013 | 0.925 | 1.31 | best 200 / stop 200 |
