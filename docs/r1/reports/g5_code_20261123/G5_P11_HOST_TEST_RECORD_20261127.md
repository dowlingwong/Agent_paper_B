# G.5 P11 host-test record — existing evidence for C1–C16

**Prepared 27 November 2026 by the compute agent (AI-assisted, DeepSeek). Tier D: it prepares a reading, decides
nothing.** Task `compute/20261127-03` item 2. Base `origin/main` `47df6f55`. The first version made no test, job,
GPU lease, label or evaluation read; every row cited a record already on published `main`. It answers the
coordinator's sheet `sheets/G5_P10_P11_S9_SHEET_20261127.md` option (b): what is already covered before publication,
and what remains for a task file after the author's P11 decision.

**Update, 27 November 2026 01:30 UTC (`compute/20261127-05`).** A TASL-7 ENGINEERING host run now adds the
evidence in `P11_HOST_TEST_RUN_20261127/P11_HOST_TEST_RUN_20261127.md`: two clean resident-GGUF server spans, the
identity re-check, the Tailscale-only listener and latency, and the lease refusal while the server held it. No G.5
label, evidence row, sealed file or evaluation value was read; the G.5 note-dependent paths still refuse and are
named below. Rows C7, C10 and C11 carry the new evidence.

**Status vocabulary.** `COVERED` — the record exercises the item as worded at the code it names.
`PARTIAL` — the record exercises part of the item, or a predecessor engine/run, and the remainder is named.
`NOT COVERED` — no record on `main`. `REPLACED` — the signed acceptance line replaces the test (P1/S4 (a)).
Where a record predates current `main`, it is cited for the mechanism it exercised, **not** as a PASS at current
code; a host-test task after the author's decision must re-run the uncovered parts at the published code.

Code and plan read at this base:

| File | sha256 |
|---|---|
| `sweep2/t1_tasl/T1_TASL_PLAN.md` | `fc5606ae75fa486a45af98d1ec848c0ae4ee342d55359024a5184046f0f2867c` |
| `sweep2/t1_tasl/g5_tasl_spec.json` (rev 13) | `16b39b475e5ccccd9143de06b0a69996e5274d73033521d5cac8c1db0470627f` |
| `docs/r1/PLAN.md` (`R1-G5-SIGNATURE` row) | `4f476a8246c0442a8d02a8f63fdf71e961e46ec0e07a070b2f81114950e67c80` |

## Table

| Item | Status | Existing evidence on `main` (path, sha256) | What remains |
|---|---|---|---|
| **C1** everything in `T1_TASL_PLAN.md` §6 | `NOT COVERED` as a whole | Plan: `sweep2/t1_tasl/T1_TASL_PLAN.md`, `fc5606ae75fa486a45af98d1ec848c0ae4ee342d55359024a5184046f0f2867c`. Its components are the rows below. | No single record covers every §6 item; use the C2–C16 rows. |
| **C2** audit runner on the TASL-2 4090: re-materialisation, isolated joint-seed runs, fixed-seed determinism, E5 per seed block | `NOT COVERED` | No G.5 audit-runner record on `main`. The G.4b re-pilot (`docs/r1/reports/tasl_chain_20261122/G4B_TASL_PILOT_RESULT_20261125.md`, `af74c536211815c58b8c0d3c3ec14246ecbdb64a6026b49eea842c447be6bbcb`) exercised the G.4 audit path, not the G.5 engine's re-materialisation/E5 checks. | A G.5 audit run on a non-evidence smoke chunk, with the four checks named. |
| **C3** run time on the TASL-2 4090 against the timeout basis | `COVERED` (predecessor run) | G.4b result §4: per-node spans and no `timing` STOP (`af74c536211815c58b8c0d3c3ec14246ecbdb64a6026b49eea842c447be6bbcb`, review `a04b490e445cce5b313e624a5c45656055ee9d39b15c5b5a3af4b42d3831f3ad`). G.5 prep re-computes the basis on TASL-2: `docs/r1/reports/tasl_chain_20261122/G5_TASL_PREP_20261126.md`, `e38b4d1eff3658cb2b98a3759e24fe503656d8422a7b345fa30400d2800c8701`; unit record `docs/r1/reports/g5_code_20261123/G5_PILOT_BASIS_HARNESS_20261126.md`, `123dce809b5a6c5c137dee83f0d99f91cee8f4e356d1ecc22b9f6cb057574799`. | Re-check on the published G.5 code at the first job start (the switch's timing check). |
| **C4** diagnostics out per wave and per audit chunk, so STOPs act early | `NOT COVERED` | The engine smoke exercised job-side diagnostics on synthetic chunks (`469cdac87aa9506f142a961051170b74d63df1e4c3d5716664108adab772997f`, items 5–9), not per-wave G.5 diagnostics. | A smoke campaign plus audit chunk with the diagnostics files inspected. |
| **C5** audit-chunk deadlines for the K = 10 imdb and Breakout audits | `NOT COVERED` | No K = 10 audit-chunk deadline record. | A short smoke chunk on both node families at the declared W/K. |
| **C6** seal end to end (procedural receipt/access log, or encryption) | `PARTIAL` | G.4b §7: three attempts sealed, receipts and `SHA256SUMS` verified (`af74c536211815c58b8c0d3c3ec14246ecbdb64a6026b49eea842c447be6bbcb`); REL copy step ran rc 0 with a copy record (`docs/r1/reports/g5_rel_t1_g1b_20261126/seven/COPY_RECORD.json`, `343a1004c68244fbaba6f98f582ace93adada13422a2f7fb200bf0ca2fa3dbb6`). | The G.5 `seal-attempt`/`seal-node`/`seal-run` path on a smoke attempt; the encryption alternative is not built and is not the signed route. |
| **C7** resident GGUF on TASL-7, one worker slot; server stopped/restarted around audit phases with identity re-checked | `PARTIAL` (restart + identity PASS, 27 Nov) | G.4b §6: resident server on TASL-7 for the 1.43 h pilot span, 180 slot launches, `SIGTERM` stop, identity recorded (`af74c536211815c58b8c0d3c3ec14246ecbdb64a6026b49eea842c447be6bbcb`). 27 Nov ENGINEERING run: two clean starts (`01:25:10Z`–`01:27:26Z`, `01:27:30Z`–`01:30:09Z`), identical `/props`, `SIGTERM` rc 0 and bound `server_end.json` both times (`P11_HOST_TEST_RUN_20261127/P11_HOST_TEST_RUN_20261127.md`). | The "around an audit phase" context; the restart and identity re-check themselves now pass. |
| **C8** cross-instance identical-proposal rate at the chosen temperature, from G.4b | `COVERED` | G.4b §3: applied 138 / duplicate 12 / context-mismatch 5, dup factor 3/180 (`af74c536211815c58b8c0d3c3ec14246ecbdb64a6026b49eea842c447be6bbcb`); independent result review `a04b490e445cce5b313e624a5c45656055ee9d39b15c5b5a3af4b42d3831f3ad`. | Confirm the same factor is the one the filled spec uses at publication. |
| **C9** worker GPU-hour meter against the cap under W, MEM, K, closed attempts; proposer card hours beside it | `PARTIAL` | G.4b §4: both-card GPU-hour accounting (0.6333 + 0.7178 + 1.1122 worker; 0.5918 other card; server span 1.4339 h) (`af74c536211815c58b8c0d3c3ec14246ecbdb64a6026b49eea842c447be6bbcb`). | The G.5 meter at the signed W/MEM/K and the 425 GPU-h threshold, including a closed attempt. |
| **C10** proposer link over Tailscale for a multi-day span; reachability, latency, restart as infrastructure STOP | `PARTIAL` (short span, 27 Nov) | G.4b §6: 1.43 h short span over Tailscale with 180 served slots (`af74c536211815c58b8c0d3c3ec14246ecbdb64a6026b49eea842c447be6bbcb`). 27 Nov: two spans of 2 min 16 s and 2 min 39 s; five `/health` probes from TASL-2 at 0.029–0.126 s; `/props` identical on both starts (`P11_HOST_TEST_RUN_20261127`). | The hours-long short span and a server restart handled as an infrastructure STOP; both belong to the table itself (STOP 12), per the sheet. |
| **C11** TASL-7 lease: server holds it; G.1b TASL-7 finished; audit chunk takes the same lease, mutual refusal | `PARTIAL` (server-holds-lease refusal PASS, 27 Nov) | G.5 prep: TASL-2 `gpu0.lock` + CPU-set leases held 10:06:34–10:07:05Z and released (`e38b4d1eff3658cb2b98a3759e24fe503656d8422a7b345fa30400d2800c8701`); G.4b used the TASL-7 lease and stopped the server (`af74c536211815c58b8c0d3c3ec14246ecbdb64a6026b49eea842c447be6bbcb`). 27 Nov: while the server held `gpu0.lock`, a second `flock -n` returned rc 1; it returned 0 after the stop (`P11_HOST_TEST_RUN_20261127`). | The audit-chunk side of the mutual refusal (the G.5 switch needs the signed note). |
| **C12** host-check item 7, CUDA IPC, on TASL-2 and TASL-7 | `REPLACED` | P1/S4 (a): the signed CUDA-IPC acceptance line, `R1-G5-SIGNATURE` in `docs/r1/PLAN.md` (`4f476a8246c0442a8d02a8f63fdf71e961e46ec0e07a070b2f81114950e67c80`), as extended to TASL-7's audit chunks; the coordinator's sheet `sheets/G5_P10_P11_S9_SHEET_20261127.md` option (b). | No test; the note must carry the signed line verbatim. |
| **C13** G5-PIN B: two harness checkouts, both G.5 commits, `g5_pin_check.py` rc 0, wrong-family checkout refused | `COVERED` | G.5 prep §2: TASL-2 `harness_g5` @ `cbf7a003` and `harness_g5_ar` @ `ccdb3774`, both clean, both carrying both commits; `g5_pin_check` rc 0 on both (`e38b4d1eff3658cb2b98a3759e24fe503656d8422a7b345fa30400d2800c8701`). Capture `…_captures/tasl2/g5_pin_check.rc.txt`, `ff0d2ba0c625151bec94661d5205921bb6f2312a00bb6bc043bb10cb43f8e2fa`. | Re-run at publication if either checkout moves; the wrong-family refusal is a code check, covered by the unit tests. |
| **C14** harness unit smoke on TASL-2: out trees, binaries unread, isolation STOP 7, `code_state_sha256`, finite `outcome.value`, `g5` wrapper in a real delegated scope | `PARTIAL` | Engine smoke: 13 PASS, 2 NOT-EXERCISED, with real delegated scopes and the real job path, fake engines (`docs/r1/reports/tasl_chain_20261122/G5_TASL2_ENGINE_SMOKE_20261123.md`, `469cdac87aa9506f142a961051170b74d63df1e4c3d5716664108adab772997f`). Its item 4 (real normalised `code_state_sha256`) and item 13 (real-server truncation) are NOT-EXERCISED. | A real-engine smoke once the signed note and real spec exist; the literal `t1_tasl_node.sh g5` path is fail-closed without them. |
| **C15** seal, assembly and release on real outputs; `seal-attempt`/`seal-node`/`seal-run`; TASL-7 `seal-server`/`close-server`/`server-span`; joined-gated G.1b dir and `rel-copy`; noise pre-check; both assembly stages with the signed note; release `--source g5` | `PARTIAL` | `rel-copy` on the real sealed seven-node run: `docs/r1/reports/g5_rel_t1_g1b_20261126/seven/COPY_RECORD.json`, `343a1004c68244fbaba6f98f582ace93adada13422a2f7fb200bf0ca2fa3dbb6`, review `docs/r1/reviews/REL_T1_G1B_COPY_REVIEW_20261126.md`, `0939aee57dce8d57081b7b5948a684d1ddfb0925c1785ae01e941ee8c591885e`; G.4b sealed three attempts (`af74c536211815c58b8c0d3c3ec14246ecbdb64a6026b49eea842c447be6bbcb`). | `seal-attempt` (disk check, tar failure, closed attempt), `seal-node`, `seal-run` on a smoke attempt; TASL-7 `seal-server`/`close-server`/`server-span`; the noise pre-check at a job start; both assembly stages and the release step, which need the signed note and real ledgers. |
| **C16** before each claim and each TASL-7 job: `git fetch origin`; TASL-7 checkout/pins; one audit chunk end to end with the server stopped and the attempt sealed on TASL-2 | `NOT COVERED` | No TASL-7 G.5 audit chunk has run. | The C16 checklist and one end-to-end TASL-7 chunk after the note is published. |

## Reading

- Covered now: C3, C8, C13. Replaced: C12. Partial: C6, C7, C9, C10, C11, C14, C15. Not covered: C1 as a whole,
  C2, C4, C5, C16.
- Under the coordinator's option (b), a reviewed host-test record before publication covers C1–C9, C11, C13, C14 and
  the pre-run parts of C15; C10 is a short span (hours) with the multi-day part a STOP during the table; C15's
  assembly/release parts are checked before their first use; C16 before the first TASL-7 chunk. This table shows
  which of those still need a run: **C2, C4, C5, C6 (G.5 seal), C9, C10 (hours-long span), C11 (audit-chunk side),
  C14 (real engine), C15 (pre-run seal parts), C16.** C7's restart and identity re-check and the server-holds-lease
  side of C11 now pass; see `P11_HOST_TEST_RUN_20261127/`.
- The author's decision on P11 (option (b)) is on `main` (`e9c29a16`). The 27 Nov run is ENGINEERING only. The
  remaining items need either the signed G.5 note or a purpose-built synthetic smoke spec; no note was created.

**Decided alone:** the conservative statuses above (a predecessor record is `PARTIAL`/`COVERED` only for the
mechanism it actually exercised), and citing only files already on published `main`. No pin, spec, note or evidence
file was changed.
