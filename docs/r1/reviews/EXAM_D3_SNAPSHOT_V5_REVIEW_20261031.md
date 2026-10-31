# Independent review: Track X D3 engineering snapshot v5 — 31 October 2026

**BLOCK.** Stage A production entry remains unconditionally stopped. Snapshot `SHA256SUMS` SHA-256 `c6cad2312ae9f201c043951ea458759918391f56a41b3f7482ade96d33f0a7b1`; all 31 listed files passed hash checks. The snapshot was copied to the local operations archive for preservation. The reviewer compiled 27 Python files in memory, but could not run pytest because it was not installed in the review environment. No model or GPU was used.

Findings requiring repair and re-review:

1. `cache_io.py` fails to journal `http.client.IncompleteRead.partial` bytes; a 16-byte synthetic partial produced no journal entry.
2. `runtime.py` does not reject an existing STOPPED batch state and can call `stop_orphan` after the current gate is removed. Both conflict with STOP preservation.
3. Stage A qualification calls the old `llamacpp_probe`, where a generation request does not explicitly set `cache_prompt=false` and exception cleanup can signal the service; CPU qualification also has the cleanup path.
4. The observer stores response chunks only in memory before returning, so a process interruption can lose already received bytes.
5. True-first on a genuinely cold service, single-server lifetime and identity, request isolation, deployed binary field semantics and end-to-end Linux behavior remain unverified.

The reviewer inadvertently generated one bytecode file during a CPU fake-stream test; it was moved to `/private/tmp/_to_delete/d3-v5-review-bytecode-20261031/`. Listed snapshot files were rehashed and remained unchanged. None of these findings represent a live-run result.
