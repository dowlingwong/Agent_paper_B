Reviewed base: origin/main `cdb8be91d` (rounds 1–2 on `f1f1b6511`); accepted at `8cc72969` (branch `mac-g1b-expansion-20261126c`; launch commit `7d0279d8a677582f4f6e5892461bf7138e78fd66`)

# Independent review record — the expansion G.1b (R1-T1-NODE-EXPANSION): spec, note draft and launch commit for mlgym_titanic, mlgym_metamaze, gc7rc_etth1 and gc7rc_forestcover

**Unit.** `sweep2/t1_tasl/g1b_tasl.py` (spec kind `g1b_tasl_x_job/v1`, `check-note-x`, `check_gate_x`, `check_review_record`, CPU-set
leases, `cpu_busy_check`, `max_attempts` on CPUs 8-11, `X_ENGINE_OVERRIDE`), the spec `sweep2/t1_tasl/g1b_tasl_x_spec.json` (run
`g1b-x-tasl-20261126-a`), `sweep2/g1b/env/venv_jax.freeze.txt`, the builder `sweep2/t1_tasl/build_g1bx_launch.py` and its config, the note
draft `docs/r1/proposals/G1B_X_T1_TASL_NOTE_DRAFT_20261126.md` (`approved: false`), tests `r1/tests/test_t1_tasl_g1b_x.py` and
`r1/tests/test_t1_tasl_g1bx_launch.py`, and the report `docs/r1/reports/tasl_chain_20261122/G1B_EXPANSION_PREP_20261126.md`. Authority:
R1-T1-NODE-EXPANSION (the coordinating chat publishes once reviewed and the launch checks pass), R1-G5-EXPANSION-JOIN, R1-T1-D21-SCOPE,
R1-T1-TASL-ENV; the queue of 26 Nov 2026 (02:26), item 1.

**Process.** One independent reviewer for both rounds, read-only, no label, evaluation, sealed or secrets file opened, no U2 metric value
copied (39 values searched in all added text, 0 matches). Round 1 found three majors (review gates that only checked a file existed; CPU-set
contention with G.5 not fail-closed and the note overstating R1-G5-EXPANSION-JOIN; no contingency for native crashes on CPUs 8-11, the
critical path). The author rebuilt the unit on `mac-g1b-expansion-20261126b` (the first branch, `ad4e95fb`, is superseded); round 2 accepted
it. After R1-TASL2-CPU (main `cdb8be91`: no R1 job on TASL-2 uses CPUs 8-11) the author rebuilt it again on
`mac-g1b-expansion-20261126c` (branch `…b`, READY 110, is superseded): Titanic on CPUs 12-15, Forest Cover on 4-7, each gated by a
node-specific fixed-seed determinism check (`cpu_determinism`); round 3 accepted it, reproducing the launch commit in a scratch clone.

**Disposition of kit-review items c2/c4 (ETTh1, Forest Cover).** The reviewer accepts each node's CPU census as the census of a CPU G.1b,
c2 and c4 disposed of for device cpu, on the conditions written into the spec and note: both nodes stay on CPU on their sets for
G.1b and any G.5 addendum (ETTh1 its census set 16-31; Forest Cover 4-7, the R1-TASL2-CPU replacement, under its `cpu_determinism` gate) (a GPU run needs c2/c4 and a re-issued spec); the funnel discloses CPU-measured noise floors; c1 is still to be
recorded (P2).

**Full suite** (author, default options, lightgbm absent, one run at a time): base `cdb8be91` 59 failed, 4123 passed, 197 skipped, 3 errors;
build tip `732baed9` 59 failed, 4272 passed, 197 skipped, 3 errors; `FULLSUITE_G1BX_BASE_cdb8be91.txt` = `FULLSUITE_G1BX_TIP.txt` (62
entries; main's extra failure since f1f1b651 is `test_t1_tasl_xc3.py::test_note_draft_renders_the_spec_and_passes_the_checks`, unrelated).

**Dispositive lines** (read by `check_review_record`; each appears exactly once in this record):

spec_sha256: d0dce0584b5c1c446e989bd7f8981242b36e30f6008f0c38eb43428524cfd238
verdict: ACCEPTED
cpu_census_disposition: gc7rc_etth1 ACCEPTED
cpu_census_disposition: gc7rc_forestcover ACCEPTED

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `ad4e95fb` | NOT ACCEPTED (MAJOR-1 gates; MAJOR-2 CPU contention; MAJOR-3 8-11 contingency; m1–m6) |
| 2 | `52b2cb49` | ACCEPTED (minors m7–m9, one nit; branch …b, superseded) |
| 3 | `8cc72969` | ACCEPTED (R1-TASL2-CPU rebuild; schedule risk for the chat; two minors, one nit) |

**Open items.** Before any node launches: (1) one TASL-2 host check per kit pin (report §9, one session, a separate clone, every step off CPUs
8-11); (2) the `cpu_determinism` records for Titanic (12-15) and Forest Cover (4-7) per report §9 step 7, each showing the adapted driver's
diff against the stability driver (review round 3, minor 3); (3) EXP-ENV, the one author decision (MetaMaze's venv_jax; proposed row text in
report §10); (4) kit c1 recorded (P2); (5) this record on main (P4 and the ETTh1 and Forest Cover gates read it). Schedule (review round 3,
finding 1): G.5's TASL-2 jobs use CPUs 0-7 and take no CPU-set lease; unless the G.5 note's schedule holds them off 0-7 until MetaMaze and
Forest Cover seal (or those start first), the two likely miss the cutoff. G.5 joining needs a separate G.5 code unit and an author decision on
the frozen eight-node split file (PRE-SPLIT A).

## Round 1 (`ad4e95fb`)

> ## Round 1, `ad4e95fb`: NOT ACCEPTED
>
> 3 MAJOR, no BLOCKING. Pins, spec, timeouts, D21 structure, schedule arithmetic and launch-commit reproduction check out.
>
> ### Verified
> - **Pins and inputs** (scripted against the captures on main): node_spec, committed pin, edits manifest, data manifest, spec_path (pins.json); harness pins (git_head.txt); census times B1 = `s000_baseline`, B2, E1–E4 against `elapsed_seconds_info_only` (3 decimals); sha256 of each census record, SHA256SUMS, kit record and kit review; freezes (`venv_jax.freeze.txt` = census and kit capture `630ed6e1`; torch312 `d2e70fe4`). CPU sets from preflight affinity: Titanic retry 8-11, MetaMaze 0-3, ETTh1 16-31, Forest Cover 8-11. Titanic's earlier 8-11 STOP ran beside a sibling smoke (load ≈5.6); the retry ran alone (<1). The `measurement` block is byte-identical to the seven-node spec's: (4+1)×(3×30+2) = 460. Timeouts raw slowest × 3 as in existing specs; all under the 300 s ceiling.
> - **Code:** seven-node, AR, crosscheck, xc3, G.5, G.4b specs byte-identical; `validate` output for seven-node and AR byte-identical between base and tip; non-x paths unchanged. `X_ENGINE_OVERRIDE` (`g1b_tasl.py:173`) run against the real engine at `c025f89a`: plain engine refuses `mlgym_metamaze`; with the override it passes the guard. `CPU_ONLY_NODES` is used only in `validate_chunk` (`noise_floor.py:177`), so nothing measured changes; scoped to one process and chunk; disclosed. `check_publication_row` matches the row text exactly.
> - **Note:** `check-note-x --draft` passes with all gates PENDING; rendered lines equal the builder render; `approved: false`; covers STOPs, cutoff, funnel, D21, crashes, publication; no result claimed.
> - **Launch commit:** rebuilt in a scratch clone: `1c889771`, `ef3bce62`, `883f535d` exactly (holder `b66790e9`). Only the spec outside docs/; `paper.commit` = parent `858aa2e6`, whose parent `f1f1b651` is on main (publish by merge). Tails add code outside docs/, so hosts must launch from `1c889771` or a docs-only descendant.
> - **Tests:** g1b_x 81, g1bx_launch 3, g1b 45, g1b_ar 69, chain 16, crosscheck 79 passed. Full-suite lists identical (62). The extra failure on main is `test_t1_tasl_xc3.py::test_note_draft_renders_the_spec_and_passes_the_checks` (draft xc3_fail B vs the new row A), unrelated.
> - **Data access:** 39 metric values from the U2 capture JSONs searched in all added text: 0 matches.
> - **Schedule:** 18.378, 16.400, 7.131, 1.675 h; 43.584 h serial (64.878 at 1.5×); 8-11 chain 34.778 (51.918); 0 GPU-h correct.
>
> ### MAJOR
> - **MAJOR-1.** The "review" gate only checks the cited file exists on main (`g1b_tasl.py:1523`): citing the kit review that asked for the GPU census passes. P4 is a substring check (`:1418`); `env_row` (`:1515`) accepts any row mentioning venv_jax and mlgym_metamaze, even a refusal. Fix: require a disposition line (`cpu_census_disposition: <node> ACCEPTED` and `spec_sha256: <sha>`) with an ACCEPTED verdict; check P4's file on main; rebuild the launch commit.
> - **MAJOR-2.** CPU-set contention with G.5 is not fail-closed: leases are per exact set (`:205`), G.5 takes no CPU lease and runs on 0-7 and 8-15 (`g5_tasl_spec.json:67,595`); R1-G5-EXPANSION-JOIN gives precedence only "on the TASL cards", but note line 41 and report line 196 read it as CPU reservation. A shared-CPU timeout is a timing STOP with no retry. Fix: reword; fail-closed `/proc/stat` utilisation preflight on the node's set, recorded; the coordinating chat puts the reservation into the G.5 note's schedule, or the expansion starts before G.5 uses TASL-2 CPUs; better, per-CPU locks adopted by G.5.
> - **MAJOR-3.** No contingency for native crashes on 8-11 (the "favoured P-cores", the census record's leading explanation for SIGSEGV/SIGILL), which carry the 34.8 h critical path; a late crash pushes Titanic and Forest Cover past 2 Dec; the fallback order leaves the cheapest nodes last. Fix (docs): run 0-3 and 16-31 beside the 8-11 chain; at most one retry on 8-11 after a native-signal STOP; prepare a contingency census for Titanic and Forest Cover on a non-favoured set (e.g. 4-7) with a re-issued spec; latest starts at 1.5× (cutoff 2 Dec 00:00 CET): 8-11 chain 29 Nov 20:05; Titanic 30 Nov 20:33; Forest Cover 30 Nov 23:31; MetaMaze 1 Dec 13:26; ETTh1 1 Dec 21:37; all four serial 29 Nov 07:07.
>
> ### minor
> m1 override wording (censuses patched `port_smoke_gpu.CPU_ONLY_NODES`, G.1b patches `noise_floor.CPU_ONLY_NODES`); m2 add a `disclosure_data` line (Titanic provenance c6(i), ETTh1 licence, 1GC-7RC is not a suite); m3 option A row text should record venv_jax's interpreter symlink target and sha256 and that nothing modifies it; m4 state the cutoff instant and time zone; m5 later gate notes are independently reviewed; m6 one host-check procedure for a single TASL-2 session (four checkouts, four records, C4 with venv_jax, GPU smoke with torch312 before G.5 takes the card).
>
> ### nit
> CPU-lease refusal reuses the GPU message; timing messages say "4090"; add `--disable-pip-version-check`; fill the stability record path at publication if it exists.
>
> ### Open questions
> - **(a)** Disposition: accept the CPU census as the census of a CPU G.1b for ETTh1 and Forest Cover, c2 and c4 disposed of for device cpu. The CPU census met c2's operative parts (standard smoke at full budget on TASL-2, CPU list, 8G, swap-0, torch312, all run records, isolation, fixed-seed repeat, 3×-slowest basis); GPU-only items do not apply to device:cpu; c4's purpose is met by B2 = B1 on the measuring device, and G.1b re-checks determinism; Forest Cover's baseline is under c2's 120 s cap. Conditions: both nodes stay on CPU on their census sets for G.1b and any G.5 addendum (a GPU run needs c2/c4 and a re-issued spec); the funnel discloses CPU-measured floors; c1 still needs recording (P2).
> - **(b)** EXP-ENV is genuinely an author decision (R1-T1-TASL-ENV names torch312 and jax312; R1-G1B-AR-ENV covers only ar-cond7a).
> - **(c)** New host-check records are needed at each pin (`check_host_record` binds the pin; the reviewed AR procedure says the `c025f89a` record does not serve another pin; Titanic's kit changes `noise_floor.py`).
> - Outside the unit: G.5's code admits exactly eight nodes and two harness pins (`g5_tasl.py:118,786`); joining needs a G.5 code unit.

## Round 2 (`52b2cb49`)

> ## Round 2, branch `mac-g1b-expansion-20261126b` @ `52b2cb49`: ACCEPTED
>
> All three round-1 MAJOR findings and m1–m6 are fixed; nothing new above minor. The whole rebuilt branch was re-reviewed.
>
> ### Checks repeated (all passed)
> - Pins, manifests, census times, census-record and capture sha256s, freezes and CPU sets match the captures on main (Titanic 8-11 retry, MetaMaze 0-3, ETTh1 16-31, Forest Cover 8-11); timeouts 3 × raw slowest (467.895, 163.878, 34.518, 767.169 s); `measurement` block unchanged (460 runs per node).
> - The 39 U2 metric values: no matches in any added text.
> - Launch commit rebuilt in a scratch clone from holder `wip-g1bx-tail-b` (`ea46b071`): `db5c6944`, `54c8303d`, `310d3645` exactly; only the spec outside docs/; `paper.commit` = parent `d26a2147`, directly on `f1f1b651`; launch from `db5c6944` or a docs-only descendant, never from the tip.
> - Seven-node, AR, crosscheck, xc3, G.4, G.4b, G.5 specs byte-identical; seven-node and AR `validate` output byte-identical.
> - Note: `check-note-x --draft` passes with all gates PENDING; rendered lines equal `render` (incl. `cpu_preflight`); `approved: false`; cutoff 2026-12-01T23:00:00Z; latest starts correct (three rounded down a minute, safe side); data, licence and suite disclosures present; override wording corrected.
> - Tests: g1b_x 99, g1bx_launch 3, g1b 45, g1b_ar 69, chain 16, crosscheck 79 passed; full-suite lists identical (62).
>
> ### New code
> - `check_review_record` fails closed: refuses any other path (incl. the Forest Cover kit review), a record missing from main, a wrong sha, an extra sha line, a column-0 NOT ACCEPTED verdict line, a trailing space, a NOT ACCEPTED or duplicated disposition line, and a quoted template line; P4 checked on main in strict mode.
> - `env_row` requires the exact sentence inside the one PLAN line.
> - `cpu_busy_check` (synthetic /proc/stat): idle iowait not busy, guest not double-counted, zero interval reads busy, missing CPU stops; 25 % refused, exactly 20 % passes, load outside the set ignored, two threads over 0-7 at 25 % refused; the job's own engine is not running between parts; refusal before the attempt uses nothing, before a later part is an infrastructure STOP.
> - `max_attempts: 2` enforced for nodes touching 8-11, refused for others, the extra attempt refused before creation.
>
> ### Findings (none blocking)
> - **m7** a busy reading before a later part uses up one of the two 8-11 attempts; only if the chat cannot reserve 0-3 and 8-11 against G.5: bounded wait and re-sample, and/or do not count busy-CPU STOPs toward `max_attempts`.
> - **m8** verdict lines with other casing or markup are not detected (optional: refuse `^\W*verdict\s*:` case-insensitive other than the canonical line).
> - **m9** report §9 step 1 adds host-check worktrees to Track P's `/home/dowling/r1_trackp/autoresearch_harness`; use a separate clone as the AR procedure did.
> - **nit** the proposed EXP-ENV row says a different interpreter target or sha256 "is a STOP", but jobs check only the Python version and the freeze.
>
> ### Record format
> The checker counts only lines beginning exactly with `verdict:` or `spec_sha256:` at column 0; headings, table rows and bold prose do not count. The four dispositive lines must appear exactly once in the whole record (fenced blocks count).

## Round 3 (`8cc72969`)

> ## Round 3 (R1-TASL2-CPU rebuild), branch `mac-g1b-expansion-20261126c` @ `8cc72969`: ACCEPTED
>
> The unit meets R1-TASL2-CPU and its new launch checks fail closed. The Forest Cover c2/c4 disposition still holds. One schedule risk is for the coordinating chat.
>
> ### Checks repeated
> - Launch commit rebuilt in a scratch clone from holder `wip-g1bx-tail-c` (`6992a205`): `7d0279d8`, `1d6c2191`, `732baed9` exactly; spec `d0dce058…`; only the spec outside docs/; `paper.commit` = parent `e81e0a34`, whose parent is `cdb8be91` = origin/main; launch from `7d0279d8` or a docs-only descendant.
> - Existing specs byte-identical to `cdb8be91`; seven-node and AR `validate` output byte-identical.
> - Pins unchanged apart from CPU sets; census-baseline result-channel sha256s (Titanic `77a834ec…`, Forest Cover `bcfc9b5d…`) equal the census `s000_baseline` and `B2` channel files on main. No U2 value copied.
> - Note: `check-note-x --draft` passes with all gates PENDING; rendered lines equal `render` incl. the two `determinism_check_<node>` lines; `approved: false`; no 8-11 rule left.
> - Tests: g1b_x 146, g1bx_launch 3, g1b 45, g1b_ar 69, chain 16, crosscheck 79 passed; full-suite lists identical (62).
>
> ### R1-TASL2-CPU
> - Reading correct and strict: any node or host set with 8-11 refused; a replacement must be census-sized, one of 0-3 / 4-7 / 12-15, cite the stability record by sha256, carry a `cpu_determinism` gate. Refusals tested (Titanic on 8-11, a 3-CPU set, E-cores 16-19, missing gate, stray `max_attempts`, MetaMaze with CPU 8 added). Option (ii) is the conservative reading (the stability record ran MetaMaze/JAX only).
> - The check satisfies the row; comparing with the census baseline sha256 is valid on another set (same P-core microarchitecture, threads fixed at 4, census channel deterministic B2 = B1, MetaMaze reproduced its census bytes on all three sets; a mismatch fails closed).
> - `check_determinism_record` refuses a wrong path or sha, verdict FAIL, another channel sha, CPUs 8-11, a wrong pin, a second or other-cased verdict line, one wall time, NaN, or a time above 1.5× B1; accepts exactly 1.5×.
> - Timing: 6.1/5.8 GHz = 1.052×; measured < 1.072×; 2.80× margin; Forest Cover E4 × 1.072 = 274 s < 300 s; the gate measures timing transfer.
> - 8-11 rules removed; `next_attempt` back to main's signature. Schedule correct: four disjoint sets in parallel; Titanic latest start 30 Nov 20:33 CET (27.443 h at 1.5×).
> - Forest Cover disposition holds on 4-7: the question was device (GPU vs CPU), unchanged; the condition's purpose is enforced by the `cpu_determinism` gate.
>
> ### Findings (none blocking)
> 1. Schedule risk for the coordinating chat: G.5's TASL-2 jobs (0-7, per the G.5 amendment) collide with MetaMaze (0-3) and Forest Cover (4-7); G.5 takes no `cpus-*.lock`; R1-G5-EXPANSION-JOIN covers cards only. Make report §5.5's recommendation part of the G.5 note's schedule (hold G.5 TASL-2 jobs off 0-7 until MetaMaze and Forest Cover seal, about 16.4 h / 24.5 h at 1.5×, or start those two first), or a G.5 code change refusing while `cpus-0-3.lock`/`cpus-4-7.lock` is held; otherwise those two likely miss the cutoff (an author trade-off).
> 2. minor: the determinism record has one `result_channel_sha256` line for both runs and no isolation line; optionally require two shas and a `determinism_check_isolation` line (code change, rebuilds the launch commit).
> 3. minor: the adapted driver is unreviewed; its diff against the stability driver must be shown in each determinism record, reviewed with the later gate note.
> 4. nit: the census set is bound only by tests (spec pinned by sha256; not a gap in practice).

---

Code-Commit: e81e0a34 (code, templates; launch commit 7d0279d8)
Verdict: ACCEPTED

Accepted 26 Nov 2026.
