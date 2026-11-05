# M11 sidecar reader guard — independent review

AI-assisted (Codex), 5 November 2026. **Verdict: ACCEPTED for the scoped pin-file, hash-input, fake-JSON and ready-file path checks only**, at `d298b3294de81aa91c4ed2e7e5ac866d84507512` (diff against `41eed4e`). This is not an acceptance of universal sealed-input protection or authorization to run a sidecar. No network, real service, model, GPU or experiment was used.

`r1/c3/serve.py:58–60` checks paths before hashing/opening; `:76–78` checks the pin before reading it; `:285–287` checks all named CLI paths before loading the fake JSON. `analysis_guard.refuse_sealed` examines lexical and resolved path components, so a symlink target in `r1_sealed/` is refused. `Pin.verify` calls the guarded hashing helper for referenced files. Normal synthetic pin load, verification and hashing still work. The check of `ready_file` is an intentional additional sealed-path refusal, rather than unchanged behaviour for sealed output.

Independent focused suite on the clone with the local harness Python: `r1/tests/test_c3_analysis_guard.py`, **17 passed**. Additional temporary synthetic checks exercised lexical and symlinked pin/hash/fake inputs, a pin referencing a sealed adapter, and ordinary pin/hash reads; **5 checks passed** without starting a server or model. There is no claim of protection against concurrent path replacement by a hostile process.

## Remaining separate limitation

`TorchLoraLoader.load` (`r1/c3/serve.py:139–151`) passes `pin.model['base_path']` to `_build`, while `Pin.verify` checks only `pin.files`. A base path that resolves under `r1_sealed/` can therefore reach model loading; this review does not cover or waive that path. The implementer should apply `refuse_sealed` to the resolved base path before any model build and have that fix separately reviewed. Other generic train/serve paths were not exhaustively audited here. The previously accepted D8 table gates and author-held files remain separate.
