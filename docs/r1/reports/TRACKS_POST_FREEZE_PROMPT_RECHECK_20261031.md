# Post-freeze Track S CPU prompt regeneration — 31 October 2026

For author decision D2 (12:00), after freeze commit `323ddf2`, an independent worker regenerated the Track S fixed prompts on TASL-2 and TASL-7 using CPU only. No LLM, model, server request, or GPU was used; socket connection methods were disabled. The frozen prompt file was not changed.

Both hosts reported paper HEAD `9bb64ba6712668c4bab4a66720cf7f2645e1c672`, harness HEAD `115df37d2b4581487eb2d911dc4d6a903afcc76a`, tracked-clean paper and harness trees, and `determinism.py` SHA-256 `081adb63aa59b93c4b7f94cbf0b74c8ace94f30b03e7f6e141c8fd26dffb715f`. Untracked files were not assessed. The source prompt bundle SHA was `70872a7702a36dc13b5612abd7a8580414f01c43bb8e19179942ca70a2ed510a`.

The worker generated 200 digits prompts and 200 tabular prompts with `fixed_prompts(200)`. Before comparing the frozen set, the worker checked the prompt UTF-8 bytes and seeds of the four retained serial, concurrent, F1 and F2 `request_example` fields on each host: **8/8 matched**. All 400 generated prompt SHA-256 values were then compared with the 50 frozen context SHA-256 values: **zero matches**.

Each host's four examples represent the same first prompt. They validate the regeneration against the examples, not the historical bytes of every request. The original reports do not retain every request, and this retrospective reconstruction cannot prove all actual call inputs. The original computation and result were transmitted via SSH/stdout; no original execution transcript was retained. A later `/private/tmp/track_s_prompt_recheck_20261031.py` restates the logic but was created after that execution and was not itself executed. Python bytecode creation was disabled; no full filesystem before/after snapshot was taken.
