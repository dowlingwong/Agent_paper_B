# G.1b seven-node official assembly on the TASL pair (25 November 2026)

**Status: PASS — R1-G1B-JOIN A official assembly and floor-by-node completed.** ENGINEERING_ONLY; no label read.
Inputs: main `5d4f1b09` code (g1b_tasl_join.py, g1b_tasl.py, cross-check spec a9e6b463…), predecessor spec
`985dd45d:sweep2/t1_tasl/g1b_tasl_spec.json` (060aac91…, first note), re-issued spec 7ff3c95b…, harness c025f89a.
Three step-2 preassembly verdicts on main (9403653f…/fea9ca97…/503fc731…), all PASS. Seven sealed attempts: TASL-2
`mlab_ogbn_arxiv`, `mlab_imdb`, `mlgym_houseprice` (first spec), `mlgym_fmnist` attempt-3 (re-issued spec); TASL-7
`mlab_cifar10`, `mlgym_cifar10`, `mlgym_breakout_minatar` (re-issued spec). Unsealed fmnist attempts 1–2 recorded as
not used.

Command (on TASL-2, main 5d4f1b09 checkout):
`g1b_tasl_join.py assemble <crosscheck spec> --dest … --predecessor-spec <985 spec> --sealed <7> --verdict <3 step-2> --xc-tasl2 <3 xc2 TASL-2 attempts> --unsealed <fmnist a1,a2>`
→ rc 0; then `g1b_tasl.py summarise <dest> <re-issued spec> --paper-root <main checkout>` → rc 0; then
`g1b_tasl_join.py floor-by-node <dest>/summary.json <AR summary>` → rc 0.

## Official D21 (matches the provisional table exactly; no STOP)

| node | qualifies_D21 | mean_p_wrong | sigma_joint | determinism | GPU-h |
|---|---|---|---|---|---|
| mlab_cifar10 | false | 0.010050537868361728 | 0.018578266872881336 | true | 0.7819 |
| mlgym_cifar10 | false | 7.2686301422209e-13 | 0.01037016941969144 | true | 1.5031 |
| mlgym_breakout_minatar | true | 0.17969980001800998 | 7.7516153743556515 | true | 4.7000 |
| mlab_imdb | false | 0.045823359403353664 | 0.0064248941133544036 | true | 4.6114 |
| mlab_ogbn_arxiv | false | 0.0044048932945487534 | 0.06196111851205978 | true | 0.9264 |
| mlgym_fmnist | false | 0.0 | 0.0040357128669948296 | true | 1.5106 |
| mlgym_houseprice | true | 0.31458651509587915 | 12042.88012945658 | true | 0.6436 CPU core-h |

Seven-node GPU total 14.0334 GPU-h / 100 cap; AR summary joins by node at `g1b_tasl_floor_by_node/1` (8 nodes),
AR qualifies_D21 false / 0.057985 / sigma 0.00679369389686993 / 29.1178 GPU-h / 100 cap.

## Records (this directory)
- `ASSEMBLY.json` sha256 e4056710beff92b4e0628372831632c9a54d070be1c41497e990eb45924236dd
- `crosscheck_gate.json` sha256 00ee68c28aa2f9fcebd0b858d85df21a1baa3175b492eb5bfef0b074b073c8e2
- `summary.json` sha256 945abc0a7ced28a7ffa27905c3282b7ad4b25ed6f9c49de01ca7c595491e7a67
- `floor_by_node.json` sha256 6fb8f9908b54ba9804eebcd7d6a5fb2b264155de1ecd8e9c520066ea1db6667d
- `SHA256SUMS` covers the four and verifies.

The official and provisional assemblies differ only in `ASSEMBLY.json` (join/gate/summary records vs provisional
ungated run); all seven per-node D21/mean_p_wrong/sigma/determinism values are byte-identical, so no author STOP.
