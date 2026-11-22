# Harness-defaults check for sweep 2 (R1-MAIN-PROPOSER (c), v6 precondition 9)

20 November 2026. ENGINEERING_ONLY. Read-only check that the harness defaults the sweep relies on are unchanged by
pin `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2` from the previously used sweep-1 pin
`6adf3859de66c4814fcf376eed59880fbd8eeaf7`. No worker ran and no label was read.

- new pin: `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`; previous pin: `6adf3859de66c4814fcf376eed59880fbd8eeaf7`
- 47 tracked `nodes/*/config.yaml` and `configs/` files at the new pin; combined config digest `e8d8b8e0c1e29d6ed1df30bfe9daed04e4de3d6e8b162849992a7057cc6766dd`
- `git diff --stat 6adf385 a3fedbb -- configs nodes harness`: **(empty)**
- commits between the pins:
  - `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2 llm: record cache_prompt on the failed-call event too (review R9)`
  - `382cbab66b208457f8beefe94eabc837b1808fbf llm: omit cache_prompt when the backend does not carry it; cover the event and the schema variant`
  - `987fb2623b1907e93fd4e87e03d5dffdaf630161 llm: send cache_prompt explicitly on every llamacpp request (default false)`
  - `115df37d2b4581487eb2d911dc4d6a903afcc76a Track S: optional seed_key for the LangGraph manager's D26 seed`
  - `f8bc22270015744ddbb3f7c5bed187477fb4fc9d Track S: fork-arm overrides in resume_campaign, controller ledger view, skip displays hidden/v1 and reason/v1`
- the only default-affecting change is the accepted `cache_prompt` fix (explicit `cache_prompt: false` on every
  request; R1-CACHEPROMPT-FALSE), which is the reason for the new pin; the LLM/manager/snapshot code changes do not
  alter node configs, the split/seed defaults, or the server/collector defaults used by the sweep.

Method: `git clone --filter=blob:none https://github.com/dowlingwong/autoresearch_harness.git`, fetch both commits,
`git diff --stat <old> <new> -- configs nodes harness`, and SHA-256 of every tracked node/config file at the new pin.
Artifacts retained in `/tmp/harness_check` during the check; command reproduced above.
