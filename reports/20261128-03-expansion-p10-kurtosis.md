# local/20261128-03 — P10 basis for the four expansion nodes

for: coordinator

- **Result:** Ready for the author's P10 sheet. The original seven-node script reproduces
  the prior result and gives the following paired G2 values for expansion. Each edit has
  30 joint pairs and normal-reference SE 0.833.

| Node | Scope | c1 − c0 | c2 − c0 | c3 − c0 | c4 − c0 |
|---|---|---:|---:|---:|---:|
| gc7rc_etth1 | Scoped 1GC | −0.21 | +3.63 | +0.49 | −0.65 |
| gc7rc_forestcover | Scoped 1GC | +0.73 | −0.23 | −0.08 | −0.83 |
| mlgym_metamaze | Main table | −0.18 | +6.51 | +3.54 | −1.08 |
| mlgym_titanic | Main table | −0.78 | −0.58 | +0.78 | +1.42 |

- **Base and tip:** `7716cfced1a30105f38590114c2b2d200b6b417d`.
  Branch `local-20261128-03-expansion-p10` @ `8962135cdd2d64eedfad936391da94a5919f354d`.
  Reviewed content `2e6fba7d71dc44147b97dec389f01fe79474602a`.
- **Tests and review:** Original script run on both published copies. Independently verified
  with SciPy, explicit paired seeds and the finite-sample SE. **ACCEPTED** with no findings.
  Review SHA-256 `cf2fdb40c0fe7816bec3c5053a3117e2240a17d587e921b0af6b381a77c21e1a`.
  Report SHA-256 `b89b452e59caa88f1dcf2105fcf20c672f4a83f2c698e43dc6db2615c36a4533`.
- **Inputs:** Archived `g5r_kurt.py` SHA-256 `1fdc798927c5e714c39111b9f33fafb0de1828038b45e2e95c3ddd54244f313a`.
  D6 runs SHA-256 `c23dec91a97cc04f3fb51e15d6248833dfa536a56cf7fda7d75713d82d6808a7`.
  The report includes summary, assembly, copy-record and PRE-SPLIT v2 hashes.
- **Next:** Coordinator puts the table on the author's P10 sheet. Per-node tail laws
  are declared by the author before the expansion addenda and labels proceed.

Decided alone to archive the identical original script with the report and reproduce the
seven-node table as a control. The expansion has the complete joint seed block
3001–3030, while the earlier mlab_cifar10 c4 pair count was 29. This is a report with its
original analysis script. No assembly, Compute submission, sealed data or label read.
