# Independent review — B1 read-only inventory (4 November 2026)

**Verdict: NOT ACCEPTED pending correction of the evidence-file format label.** This review did not contact TASL-2, read GGUF files there, launch a job or download anything; host readings and individual file hashes are the operator's observations. I examined the report, retained output and script, the pinned registry and the two Stage A tables.

## Finding

`OPS_B1_INVENTORY_20261104.jsonl` begins with a plain text `utc ...` line, which is not JSON. Thus the retained raw output is not a valid JSON Lines file. Preserve the output bytes as a text file and update its report reference, or preserve the raw text and create a valid JSONL derivative with clear provenance. Do not present a transformed derivative as the original stdout.

## Independent checks

- The source registry YAML SHA-256 is `2c6ef6b329694536df6a23345e4313d0cb2dcbf447113023e18f60fcb608e723`. I parsed the YAML independently and verified that the supplied JSON parsing matches it.
- Re-derived the selected set from the stored Stage A tables: exactly 8 `t7h8` candidates plus 7 distinct `t7j10` candidates and the model anchor `qwen25_coder_7b`. The other anchors, `random_valid` and `scripted`, are registered as software and have no GGUF. The retained output has exactly one entry for every one of the 16 required files.
- All 16 recorded filenames, byte sizes, observed digests, and expected digests match the registry; the script's embedded entries also match the independently parsed registry. The table's sizes reproduce the output at three decimal GB. Total is 239,018,738,080 bytes. This compares the reported readings against the pins; I did not independently re-hash the 239 GB of files on the host.
- The recorded 183,290,667,008 bytes available is above the PLAN's 100,000,000,000-byte floor, and equals approximately 170.7 GiB; disk observation itself was not independently reproduced. A fresh preflight is required at use time.
- The Stage A table hashes match the previously recorded receiving evidence. This inventory does not satisfy or waive the future B1 rule, authorization, host preflight, Stage A author acceptance, or other gates.

## Re-check

**Verdict: ACCEPTED for the documented read-only inventory.** The operator renamed the retained stdout to `OPS_B1_INVENTORY_20261104.txt` and corrected the report reference. The bytes remain unchanged: SHA-256 `b43d297730a02d467faf46f520fb661fce1ea78330a482b5960ac1b5e6d64d24`. The prior format-label finding is resolved. The observed file hashes and disk reading remain operator-reported rather than independently remeasured on the host; the report correctly requires a fresh preflight before use. No download or B1 run is authorized by this review.
