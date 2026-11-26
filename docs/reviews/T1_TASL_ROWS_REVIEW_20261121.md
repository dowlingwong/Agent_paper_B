Reviewed base: `021dbc260d87c900e6afe18a8a712e72c04693d1` (the accepted T1 TASL code unit; round 1 was on `f4180237` over `eae2db87`, rebased unchanged to `53618888`); accepted at `33d0eb78fdc5ee712da7d6e9a4a0099ab3545fcd`

# Independent review record — drafts of R1-G1B-EDITS, R1-G1B-TIMEOUT and R1-T1-TASL-ENV for the TASL pair (approved: false)

**Unit.** `docs/r1/proposals/T1_TASL_ROWS_DRAFT_20261121.md` on `mac-t1-rows-20261121`: three PLAN rows the T1 jobs on the TASL
pair need, each with facts, options, a recommendation and a proposed row text, for the author to sign (the queue of 21 Nov
2026, item 2). It decides nothing.

**Process.** One independent reviewer for all four rounds, read-only, scratch under `/tmp/rev_rows/` moved to its
`_to_delete/`. Between rounds 1 and 2 the branch was rebased onto the accepted code unit (the draft unchanged). Rounds 3
and 4 confirm small fixes after the round-2 acceptance. The round texts are reproduced below as delivered.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `f4180237 (rev 1)` | CHANGES REQUESTED (4 major, 8 minor) |
| 2 | `9c95e5ef (rev 2)` | ACCEPTED (3 minor) |
| 3 | `b0fa255a` | ACCEPTED (confirmation; 1 nit) |
| 4 | `33d0eb78` | ACCEPTED (confirmation) |

**Open for the author.** The three rows (R1-G1B-EDITS A/B; R1-G1B-TIMEOUT A–D; R1-T1-TASL-ENV A–C with §3a A–C).
Under §3a A, the cross-host default check and the per-job driver STOP are a small reviewed code addition, not built.

## Round 1 (`f4180237 (rev 1)`)

> **Verdict: CHANGES REQUESTED**
>
> I checked the draft at f4180237 (docs/r1/proposals/T1_TASL_ROWS_DRAFT_20261121.md) against every source listed and found four Major problems. Most numbers are right. The worst issue is a misattributed binary hash in §3. I edited nothing in the repo. My scratch files are in /tmp/rev_rows/_to_delete/.
>
> **What matches the sources**
> - **Projections:** the 4-edit validate gives 28.262 GPU-h (41.644 at ratio 1.5), 14.06 / 14.20 h per host, and houseprice 0.896 h. A 5-edit copy of the spec gives 33.614 (49.672), 16.72 / 16.89 h, and 1.026 h. All match the §1 table.
> - **Census:** the report's sha256 is 146b1114…92d7. All seven B1 times match. Every U2 record's E1–E4 manifest has four edits, and each manifest sha matches the spec's edits_manifest_sha256 (houseprice f26332ff ✓). The autoresearch cond7a smoke also has E1–E4.
> - **Timeouts:** the slowest declared record per node is cifar E2 13.347, imdb E1 65.156, ogbn E4 21.8, mlgym_cifar E3 35.948, fmnist E3 40.795, breakout B2 61.781 and houseprice E4 6.794. All 14 timeout values and the 1.29× figure check out.
> - **PLAN rows:** quotes of R1-G1B-CAP ("552 runs") and R1-TRACKG-PORT-DECISIONS (4) are correct. R1-T1-HOST-TASL is on e5e452a0 ✓.
> - **Exam server:** the exam binary b70f4882… with "version: 0.7.0-dev (build 1, commit 620d222)" and the GGUF 2959c1b0… are correct.
> - **Launch checks:** the three spec authority checks and the timing STOP (`stop_class: timing`) match the code.
>
> **Blocking:** none.
>
> **Major**
>
> - **M1 — §3 Facts and option B: wrong binary attributed to image v2.** `f8d35fd3…` (build 11669) is the llama-server of image **v1** (`69b06b35…`), which is the sweep-2 pin (S2_M1_AUTH_DRAFT_REVIEW l.197; sweep2/spec*.json). Image v2's llama-server sha256 has never been verified: the H200 G.4 spec still has it as `TODO_VERIFY_ON_HOST`, with only an expected build line. "Image v2's binary … f8d35fd3 … the H200 G.4 and sweep-2 pin" is therefore wrong.
>   - Fix: say v1's binary is f8d35fd3 (the sweep-2 pin) and v2's sha is unverified (expected build 11669, same commit). Restate option B as "v1's binary f8d35fd3" or "v2's binary once hashed".
>
> - **M2 — §3 option A and the R1-T1-TASL-ENV row: the proposer pin covers less than the image did.**
>   - Only the `llama-server` executable is pinned. A llama.cpp build at this commit uses shared libraries by default (the image's I3 review lists `/opt/r1/llama/bin/libggml-cuda.so*`). So the CUDA kernels in libggml-cuda.so, plus libggml/libllama/libmtmd, and the host CUDA toolkit libraries the build links against, are not covered by the binary's sha256. The image fixed all of these.
>   - The g4 spec also runs a different path (`/home/dowling/r1_t1_tasl/llama/bin/llama-server`, GGUF under `r1_t1_tasl/models/`) from the exam path the draft cites.
>   - Fix: pin the whole `build-exam/bin` set by a sha256 manifest, record `ldd` resolution of the CUDA libraries, and state whether the binary is used in place or as a byte-identical copy of the bin directory.
>
> - **M3 — §3 Facts: the two hosts run different drivers, and the draft doesn't say so.** TASL-2 runs driver 535.309.01 and TASL-7 runs 580.178.04 (R1-TRACKP-D2, R1-TASL7-TRACKP). G.1b measures mlab_cifar10, mlgym_cifar10 and breakout on TASL-7, but G.4/G.5 run their workers on TASL-2. So those nodes would get their noise floor on one driver stack and their labels on another. R1-S2C3-ACCEPT shows that cross-host numeric differences are real.
>   - Fix: state both drivers, and add an option with a recommendation. Either measure G.1b for each node on its label host (TASL-2), or allow both hosts with disclosure. Rewrite "driver recorded, not pinned" to match the choice.
>
> - **M4 — §2 row and §1: autoresearch_fixedtokens is not covered.** The code allows it as a later T1 node (`T1_NODES_LATER`), and it is the G.4 pilot's third node. Under R1-TRACKG-AR-U2-TASL2 its census U2 runs on TASL-2, an RTX 4090. The R1-G1B-TIMEOUT row ("U4 census, RTX 6000 Ada") and the 4090/Ada estimate wording don't fit it.
>   - Fix: add a clause that for a node whose census record is on a 4090, the basis is its own census record on that host, with no ratio applied. In R1-G1B-EDITS, note that autoresearch also declares four edits.
>
> **Minor**
>
> - **m1 — §2 table header and row text: the basis definition is ambiguous.** "Slowest executed census record" literally includes the s002/s003 smoke records. Breakout's s003 took 62.848 s (rc 0), which would give a 188.54 s timeout instead of 185.34 s. Fix: write "the slowest of B1, B2 and E1–E4", which excludes the s00x smoke records.
> - **m2 — R1-G1B-TIMEOUT row: G.4 timing STOP missing.** `g4_tasl.py` also STOPs (timing) when the pilot run median exceeds 1× the basis. Add this to the row.
> - **m3 — R1-G1B-TIMEOUT row: wrong scope note.** "T0 is unchanged" doesn't apply, because PORT-DECISIONS (4) governs the ported Track G nodes. Write "T2 and later tables are unchanged".
> - **m4 — R1-G1B-TIMEOUT row: CPU node not covered.** "On the RTX 4090 the census times are an estimate" leaves out mlgym_houseprice, which runs on a different CPU but gets the same timing STOP. Say "on the TASL hosts".
> - **m5 — R1-T1-TASL-ENV row: isolation precondition missing.** The row doesn't mention the harness-isolation host checks, which must **pass** under R1-T1-HOST-TASL ("recorded" in option A is too weak). Add "READY 60 §3 host checks passed on each host that runs workers, report sha in the spec".
> - **m6 — R1-T1-TASL-ENV row: harness pin unnamed.** "Harness at the reviewed pin" doesn't say which pin. Name `af480809…` or "the commit in the signed note". Also, the uv version and the source of the Python 3.12.16 interpreter (which the image fixed) are neither recorded nor pinned. Record them.
> - **m7 — §1 option B understates its cost.** It needs eight new edits (autoresearch included), and the re-smokes can't run on Ada (R1-TRACKG-AR-U2-TASL2), so they would move the census host.
> - **m8 — R1-G1B-EDITS row: two wording issues.**
>   - The basis cites the U4 report for "four declared edits", but the report doesn't state that. Cite the U2 records' manifests (the spec's edits_manifest_sha256).
>   - Drop "on the TASL pair": the edit count shouldn't depend on which host runs it.
>
> Nothing new worth saving to memory came up. The fact that TASL-2 is the zhixu portal and has no root on TASL-7 was already in memory and matches the draft.

## Round 2 (`9c95e5ef (rev 2)`)

> **Verdict: ACCEPTED**
>
> Revision 9c95e5ef fixes all four Major and all eight Minor findings from round 1. I found no new Blocking or Major issues, only three Minor points. I edited nothing in the repo, and this round wrote nothing new under /tmp/rev_rows.
>
> **How the round-1 findings were handled**
> - **M1 (binary hashes):** fixed. `f8d35fd3…` is now named as the image v1 binary and the sweep-2 pin. v2's binary is described as never hashed (it is a placeholder in the H200 G.4 spec). Option B is restated to match.
> - **M2 (proposer pin):** fixed, and the code matches the draft.
>   - `g4_tasl_spec.json` points `binary` and `model_path` at the exam paths, so the exam server is used in place.
>   - `serve` checks a manifest of every file and symlink in the build directory against `bin_dir_manifest_sha256`. It STOPs if `ldd` reports "not found", or if any `libllama*`/`libggml*`/`libmtmd*` resolves outside that directory.
>   - It unsets `LD_LIBRARY_PATH` and `LD_PRELOAD`, and records the full `ldd` output.
>   - The worker's `/props` check expects `b1-620d222`, derived from the `--version` line.
> - **M3 (drivers):** fixed. Both drivers are stated and match R1-TRACKP-D2 (TASL-2 535.309.01, TASL-7 580.178.04).
>   - The new §3a has three real options. Its recommendation is justified, and its TASL-7 node list matches the spec (mlab_cifar10, mlgym_cifar10, breakout).
>   - Option B's cost holds up: about 28.3 GPU-h, and T1_TASL_PLAN gives "1 day slack".
>   - The two parts that are not built yet are flagged in §4: the cross-host check, and the STOP when a driver changes. The driver itself is already recorded per job (`gpu_check` reads `driver_version`).
> - **M4 (autoresearch):** fixed. Its basis is now its own TASL-2 census record. I confirmed that the cond7a kit declares E1–E4.
> - **m1–m8:** all fixed as described. Specifically:
>   - The basis is the slowest of B1, B2 and E1–E4 everywhere, including the `g1b_tasl.py` docstring.
>   - The draft says the first timeout stops the run. The code does this: `chunk["stop_on_timeout"] = True`, and harness `c025f89a` `noise_floor.py:349` stops on the first `divergent:timeout` row.
>   - The G.4 STOP when the run median exceeds the 1× basis is now in the row.
>   - "T2 and later tables" and "on the TASL hosts" are fixed.
>   - Host checks are verified at launch: the report must be on published main with the declared sha256 and contain the `host_check_*` PASS lines (`check_host_record`).
>   - The harness commit is "the one the signed note names (today c025f89a)", and both specs pin c025f89a.
>   - uv and the Python interpreter are now recorded.
>   - Option B of §1 now counts eight edits and says the re-smokes can't run on Ada.
>   - The edit-count basis cites the U2 manifests, and "on the TASL pair" is gone.
>
> **Minor**
> - **m1 — §3a option A: breakout may fail the bit-for-bit check.** The census `jax312` environment had `nvidia-cuda-nvcc-cu12` removed, so XLA has no `ptxas`. It then falls back to the driver's own PTX compiler. With drivers 535 and 580, Breakout's default parts may well not be bit-identical, so the check is likely to STOP on that node.
>   - Fix: name this risk in §3a. Optionally pre-state what happens if it STOPs, e.g. "Breakout moves to TASL-2 (option B for that node)".
>   - Also, `g1b_tasl_spec.json`'s TASL-2 host has no `jax312` in `env_python` (only the G.4 worker spec does). The future `crosscheck` addition needs it there.
> - **m2 — §3a option A: the cost is understated.** The draft says "under 15 min per node", but setup is estimated at 900 s per node before any runs. Breakout's 10 default runs take about 10 min (10 × ~61 s) on top. Fix: say "about 15–30 min per node, including setup".
> - **m3 — R1-G1B-TIMEOUT row wording.** "On the TASL hosts the census times are an estimate" doesn't apply to autoresearch_fixedtokens, whose census runs on TASL-2 itself. Fix: add "(except a node censused on its TASL host)".

## Round 3 (`b0fa255a`)

> **Verdict: ACCEPTED**
>
> Commit b0fa255a fixes all three round-2 Minor findings, and the change touches nothing else. I edited nothing and wrote no scratch files this round.
>
> - **m1 (Breakout's cross-driver risk):** fixed. §3a A now names the risk: the census jax312 environment has no `ptxas`, so XLA compiles with the driver's own compiler, and Breakout's results may differ between drivers 535 and 580. It also proposes what happens if the check fails: that node is re-measured on TASL-2. And it notes the crosscheck needs jax312 on TASL-2 in the G.1b spec.
> - **m2 (check cost):** fixed. The cost now reads "about 15–30 min per node, including the node setup", with Breakout's roughly 10 min of runs called out.
> - **m3 (TIMEOUT row):** fixed. The row now reads "(except for a node censused on its TASL host)", which matches the autoresearch clause earlier in the same row.
>
> **One small nit, not a finding:** two sentences in §3a A now pull in different directions. One says "otherwise STOP and the author chooses between B and disclosure". The new proposed default says a failing node is re-measured on TASL-2 rather than disclosed. The R1-T1-TASL-ENV row text still says only "else STOP". If the author adopts the proposed default, it should go into the row text, for example "else STOP; that node's G.1b is re-measured on TASL-2". The earlier "author chooses" sentence should then drop "disclosure". Since the default is clearly marked "(proposed)", this does not affect acceptance.

## Round 4 (`33d0eb78`)

> **Verdict: ACCEPTED**
>
> Commit 33d0eb78 fixes the §3a nit, and I have no remaining findings. I only read the diff; I edited nothing and wrote no scratch files.
>
> - **One outcome now:** §3a option A and the R1-T1-TASL-ENV row text now say the same thing. If the cross-host check fails, the job STOPs and that node's G.1b is re-measured on TASL-2. §3a marks this as *(proposed)*.
> - **No leftover alternative:** the "author chooses between B and disclosure" wording is gone from option A. Disclosure is still mentioned only as option C ("split as queued, disclosed only"), which is the right place for it.
> - **Breakout risk tied in:** the known-risk note now ends with "then Breakout is re-measured on TASL-2 as above", so it points back to the same outcome.
> - **Nothing else changed:** the commit touches only those lines in §3a and the row text.

---

Code-Commit: 33d0eb78fdc5ee712da7d6e9a4a0099ab3545fcd
Verdict: ACCEPTED

Accepted commit: `33d0eb78fdc5ee712da7d6e9a4a0099ab3545fcd` (round 4).
