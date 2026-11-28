# G.5 P10 for the four expansion nodes: tails declaration (level 2, for the author)

Coordinator, 28 Nov 2026. Basis on `main` `9e3426ef`: `docs/r1/reports/g5_p10_expansion_20261128/P10_EXPANSION_KURTOSIS_20261128.md` (local worker; the
original seven-node script `g5r_kurt.py`, sha256 `1fdc7989…`; review ACCEPTED, no findings), from the reviewed expansion D6 copy (runs `c23dec91…`).
Paired excess kurtosis G2 of edit − baseline over the 30 joint seeds 3001–3030 (normal-reference SE 0.833). No label read, nothing assembled.

| Node | Scope | c1 − c0 | c2 − c0 | c3 − c0 | c4 − c0 | edits with G2 > 3 |
|---|---|---:|---:|---:|---:|---:|
| `mlgym_metamaze` | main table | −0.18 | **+6.51** | **+3.54** | −1.08 | 2 |
| `gc7rc_etth1` | scoped 1GC | −0.21 | **+3.63** | +0.49 | −0.65 | 1 |
| `gc7rc_forestcover` | scoped 1GC | +0.73 | −0.23 | −0.08 | −0.83 | 0 |
| `mlgym_titanic` | main table | −0.78 | −0.58 | +0.78 | +1.42 | 0 |

**Precedent (R1-G5-TAILS, seven nodes):** Student-t for `mlab_ogbn_arxiv` (paired 7.5–8.7, all four edits) and `mlgym_breakout_minatar` (1.4–4.9, all edits
elevated); Gaussian for `mlgym_houseprice` although one edit had paired G2 **6.01**, and for the rest. The seven-node report's descriptive comparison was
"G2 above 3 on at least two edits".

| Option | Content |
|---|---|
| **A (recommended)** | Student-t, ν = 5, for `mlgym_metamaze`; Gaussian for `gc7rc_etth1`, `gc7rc_forestcover`, `mlgym_titanic` |
| B | As A, plus Student-t ν = 5 for `gc7rc_etth1` (more cautious on its one heavy edit) |
| C | Per-node choice by the author |

Why A: it applies the same reading as the signed seven-node declaration. MetaMaze is heavy on two edits, one at 7.8 SE, the pattern that made
breakout Student-t. ETTh1 has one heavy edit (3.63), weaker than houseprice's single 6.01, which was declared Gaussian; declaring ETTh1 Student-t would
treat the two nodes differently on weaker evidence. Forest Cover and Titanic stay within 1.7 SE on every edit. No code change: the Student-t path and the
ν field exist (R1-G5-TAILS, R1-G5-TAILS-CONSUMERS); each addendum fills its node's law before any label is assembled (E5), and it does not change after.

Draft row: `R1-G5-TAILS-EXPANSION` — P10 for the expansion addenda: `mlgym_metamaze` Student-t ν = 5; `gc7rc_etth1`, `gc7rc_forestcover`, `mlgym_titanic`
Gaussian; declared from the reviewed expansion copy (`main` `9e3426ef`) before any label is assembled.

Reply: **"签 P10 扩展 A"** (or "P10 扩展 B" / name per node).
