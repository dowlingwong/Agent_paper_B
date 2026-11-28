# compute/20261128-22 — D.3a production route records (for the launch binding before the author's P9)

From local's handoff (`coord/local` `47bdb458`): the P7 receipt used work-root locks; the D.3a production route on the TASL-2 RTX 4090 needs, on `main` `c3a48405`
and frozen rev 5 (`700d93ca…`):
1. the reviewed **launch manifest** for the production route (driver, chunk runner, server command exactly as rev 5 §2: `-c 32768 -ngl 999 -np 1`, `--jinja`,
   `enable_thinking:false`, q8_0 K/V, `cache_prompt` false; GGUF `2959c1b0…`, llama-server `646caa00…`);
2. the **campaign environment / image disposition** against rev 5 §§2 and 7.2 (what runs the campaigns on TASL-2, its Python and package set, how it
   relates to the pinned image; the deepthought audit side is P8, already accepted);
3. **canonical endpoint-to-lease UUID proof** across the server and every chunk (the leased card's UUID is the one serving the endpoint the chunk calls),
   using the canonical leases (`~/r1_locks/`), not work-root locks;
4. the **resource basis** (VRAM/RAM/scratch from P7 at the exact runtime), and a **fresh evidence run ID** reconciled with your ledger (unused).
ENGINEERING checks only, no campaign. Record + review. Local then binds `paper_commit`/`run_id` in the D.3a note, rechecks P10/P11 at that SHA, and the note
comes to the author for P9. Priority: first (you are idle; G.5 waits for the author).
