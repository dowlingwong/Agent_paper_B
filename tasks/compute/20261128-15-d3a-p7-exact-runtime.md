# compute/20261128-15 — D.3a P7 again at the frozen runtime settings (-c 32768, q8_0 K/V)

Local's note fill (`main` `52006470`, `coord/local` `e7eccf51`) found that the accepted P7 smoke ran the proposer server at `-c 8192` with no q8_0 K/V
settings, while frozen rev 4 §2 (line 80) fixes: `-c 32768 -ngl 999 -np 1`, `--jinja`, `--chat-template-kwargs` exactly `{"enable_thinking":false}`,
**q8_0 K/V**, `cache_prompt` false on every call. The P7 record therefore does not certify the signed runtime. My P7 card did not state the server line;
that omission is mine.
Rerun the full P7 on the TASL-2 RTX 4090 with exactly those settings (fresh run IDs; the earlier runs stay as records): seven arms × `openml_climate`
6301/6302, replicate seeds as declared, harness `9bb41680`, no G6 audit. Record: the exact server command line and its capture, GGUF and llama-server
binary digests, code and input pins, endpoint-to-leased-device UUID proof, CPU affinity, peak VRAM, host RAM and scratch, per arm/seed time, the
worker gate with the corrected classification (charged = worker ran). Fresh review. **If the model does not fit at 32768 with q8_0 K/V on 24 GB**, STOP
and report the measured failure: do not lower the context or change the cache type (that is the frozen declaration, the author's). Priority: first;
TASL-2 is free.
