# T3/T5 CPU reproduction — 27 October 2026

AI-assisted independent reproduction; **ENGINEERING_ONLY, model output, not harness measurements or author proof approval**. The simulation agent used a Git archive of paper commit `29bd16a4e4ae3479c1f142887b93b580caec95f6` in a fresh `/private/tmp` directory. Both full runs exited zero. The archive contains no `.git`, so the regenerated T5 manifest has no Git HEAD; the source identity comes from the archive operation. The scratch directory and original outputs remain at `/private/tmp/paper-b-l2-repro-Zyu8jA`.

The source archive and the committed T5 manifest's two source hashes matched. The original T5 record reports Linux/aarch64, Python 3.13.15 and NumPy 2.5.4; this run used macOS/arm64, Python 3.13.4 and NumPy 2.4.4. This is a cross-environment comparison, not an assertion of bit identity.

```sh
env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /private/tmp/paper-b-local-20261026-venv/bin/python -m r1.theory.t3_report --out /private/tmp/paper-b-l2-repro-Zyu8jA/output-t3
env CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /private/tmp/paper-b-local-20261026-venv/bin/python -m r1.theory.t5_report --out /private/tmp/paper-b-l2-repro-Zyu8jA/output-t5
```

| Check | Result | Scope |
|---|---|---|
| T3 | Table bytes match the committed table; `results.json` has 20 numeric differences, maximum absolute difference `6.938893903907228e-18`; no other field differences | Seed 7, 3,000 campaigns, W=40. Displayed numbers agree with T3 note; typographic notation differs. |
| T5 | Table bytes match; all 84 part JSON files compared, excluding `_seconds`; 7 numeric differences, maximum absolute difference `2.220446049250313e-16`; no other field differences | Full defaults: base seed 20261019, M_test=20000, M_big=40000, M_dev=4000, n_branch=30000. Per-part seeds match. |

The [comparison output](local_theory_repro_20261027/comparison-all.txt) lists every differing numeric field; [comparison code](local_theory_repro_20261027/compare.py), [regenerated outputs](local_theory_repro_20261027/regenerated.tar.gz), manifests, logs and exit files are retained alongside it. The table byte checks used `cmp`; the recursive comparator excludes elapsed-time fields only. The T5 narrative was not independently checked against every table cell. The result demonstrates reproduction at the displayed precision, with the explicitly recorded floating-point and provenance differences; it does not establish record-level byte identity, empirical validity or proof correctness.
