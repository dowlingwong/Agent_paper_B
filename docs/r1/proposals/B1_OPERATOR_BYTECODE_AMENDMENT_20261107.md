# B1 operator message v3 — Python startup amendment, 7 November 2026

AI-assisted (Codex). **Draft for independent review; not authorization to launch.** This amendment specifies the direct production supervisor invocation required by the source-level bytecode review `docs/r1/reviews/B1_BYTECODE_SUPPRESSION_REVIEW_20261107.md`. The B1 note, exact integrated checkout and protected-code pin, full test requirements, author gate, host preflight, site qualification and reviewed TASL-7 handover remain prerequisites; the present draft establishes none of them. It does not approve a harness pin change, B2, X.7 or sweep 2.

When all prerequisites have independently passed, from the root of the exact reviewed and clean TASL-7 checkout, the operator must start the supervisor directly with the site-qualified Python interpreter and `-B` **at interpreter startup**, not by importing its `main()` into an already running interpreter. The reviewed supervisor CLI accepts `--config` and `--out`. Using the site-qualified executable resolved as `python3`, the command template is:

```bash
python3 -B r1/scripts/b1_supervisor.py \
  --config r1/scripts/configs/exam_b1_v2.json \
  --out "$B1_NEW_BATCH_PATH"
```

Before invocation, the operator supplies `B1_NEW_BATCH_PATH` as a fresh, absolute, unaliased, nonexisting direct child of the final committed config's `work_dir` (`/home/dowling/exam-x/work` in the current draft config). The example is a template, not a previously inspected or reserved path. Check that the chosen final config and `python3` executable are the reviewed and site-qualified ones; a later config change needs its own final review. The supervisor validates the path and committed configuration, but that check is not a substitute for the handover, no-deletion qualification or the remaining gates.

`-B` must be passed when Python starts because interpreter and `site` initialization occur before the supervisor script's own guard. The controlled child launch and environment also suppress ordinary Python bytecode writes, as described in the independent source review. This does not prove that external libraries, site initialization, subprocesses or node code cannot create other caches or perform deletion. Site qualification must verify the actual interpreter and child binding without violating the author's strict preservation rule. Do not treat an absent launch path or an unverified capability as permission to retry a STOP.

On any runner, guardian, author-gate or anchor-gate STOP, stop, preserve the scene, publish STATUS and report as required by the existing v3 message and the author's 7 November prompt. Never automatically retry, change the checkout or pin after launch, delete files, preempt another job, or start a later phase. The exact launch command and this amendment require a fresh independent review against the final integrated checkout before use.
