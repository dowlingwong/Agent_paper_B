# G.5 code and draft revision 11: R1-T1-D21-SCOPE and R1-G5-AUDIT-TWO-CARDS (25 Nov 2026)

ENGINEERING_ONLY report. AI-assisted (Mac-desk agent, Claude). Branch `mac-g5-scope-twocards-20261125`, from
`3e429275` (READY 104: the G.5 draft revision 10, on READY 103 (D7-DIFF B), on READY 100), with published `main`
`5d4f1b09` merged in first (merge commit `9a58bbad`, no conflict). After the code and docs commits, `main` moved to
`912a7e02` (the READY 99–106 batch, which puts READY 100, 103 and 104 on `main`, the signed G.4b note, and two author
rows that do not bear on this unit); it was merged too (merge commit `d95c9e51`, no conflict; the rendered key-lines
block is byte-identical before and after; the targeted tests were rerun after it).
- Authority: the PLAN rows **R1-T1-D21-SCOPE** and **R1-G5-AUDIT-TWO-CARDS** on `main` `5d4f1b09`, read there.
- Files changed: `sweep2/t1_tasl/g5_tasl.py`, `g5_tasl_spec.json`, `g5_job.py`, `g5_assemble.py`, `g5_noise.py`
  (docstring), `g5_seal.py`, `t1_tasl_node.sh`; the tests `r1/tests/test_t1_g5_tasl.py`, `test_t1_g5_job.py`,
  `test_t1_g5_seal.py`, `test_t1_features.py` (fixture only); `docs/r1/proposals/T1_G5_AUTHORIZATION_DRAFT_20261120.md`
  (revision 11, `approved: false`); `docs/r1/proposals/T1_RELEASE_ROWS_DRAFT_20261123.md` (`approved: false`, row
  texts unchanged). This report and the full-suite lists beside it are new.
- Not changed: `gate.py`, `gate_input_builder.py`, `release.py`, the preregistration, `g1b_crosscheck.py`,
  `g5_relcopy.py`, the G.1b code. The spec's `harness_families.*.g5_commit` stay PENDING (the later fill with the
  reviewed recount tips G5-7 `cbf7a003`, G5-AR `ccdb3774`).
- Nothing ran on a host. No label, evaluation value, sealed file or receipt partition was read. The xc2 verdict files
  on `main` were read for their sha256 and their non-value fields only (schema, node, mode, verdict, sides'
  determinism, run ids, pins); the two excluded evidence files were not opened.

## 0. Review round 1 (NOT ACCEPTED at `e7ab0c36`; fixed on top)

§9 maps every finding to its change. Where §1–§6 below differ from §9, §9 holds; the stale statements in them were
corrected in place.

## 1. Reading of the task, and the placeholders

**R1-T1-D21-SCOPE.** Read as written: D21 stops selecting. What still STOPs a node: G.1b fixed-seed determinism; the
G.1b cross-host gate, where it ran (the three TASL-7 nodes); and a node without a usable σ̂_node or δ_n. No other
threshold.

**R1-G5-AUDIT-TWO-CARDS, the four nodes without a cross-host PASS** (`mlab_imdb`, `mlab_ogbn_arxiv`, `mlgym_fmnist`,
`mlgym_houseprice`). The reading in the task is confirmed: the spec carries the exact marker
`PENDING short cross-check: <node>`; until the node has a PASS record it may not run on TASL-7 but runs on TASL-2;
the launch is not blocked; only that node's TASL-7 chunks are. **One addition, chosen for a reason:** the spec is
bound by the note's `spec_sha256` and must not change on `main` from the launch to the T1 test release (the release
integrity check, draft §6). A PASS that arrives after the launch could then never be written into the spec. So the
switch accepts a pending node's PASS in two ways:
1. filled in the spec before the signature (a record list, as for the three xc2 nodes); or
2. without a spec change, from `main` by file pattern, as G5-ARPEND A's completion record works: exactly one
   `docs/r1/reports/<dir>/G1B_XC3_SHORT_VERDICT_<node>_<YYYYMMDD>.json`.

**The xc3 format** (from the coordinator, 25 Nov, while the xc3 unit is under review: "names stable but not yet
final"): `docs/r1/reports/tasl_chain_20261122/G1B_XC3_SHORT_VERDICT_<node>_20261125.json`, schema
`g1b_tasl_crosscheck_verdict/1`, `mode: "short"`, `rule: "R1-G5-AUDIT-TWO-CARDS"`, fields `node`, `mode`, `verdict`,
`reason`, `crosscheck_run_id`, `g1b_run_id`, `g1b_spec_sha256`, `harness_commit`, and `sides.TASL-7`/`sides.TASL-2`
each with `run_id`, `spec_sha256`, `job_record_sha256`, `attempt`. After review round 1 (m3, m8; §9) the consumer
checks: mode, rule, node, PASS with no reason, `label` ENGINEERING_ONLY and `complete: true` (required), the pin,
the signed G.1b spec and run, both sides with their four fields, the TASL-2 side's `run_id` the G.1b run and the
TASL-7 side's `<xc3 run>-TASL-7`, and the xc3 run id (the xc3 spec's on `main`, else the signed note's, else the
prefix `g1b-tasl-20261121-b-xc3-`). Only a `.json` named exactly so directly under `docs/r1/reports/<dir>/` counts;
copies in `*_captures/` are ignored. It does not pin the xc3 spec sha256. It fails closed. A first version of this
unit used an invented name and required a separate review file; both were replaced when the xc3 names arrived. For
round 1 the xc3 branch `mac-xc3-short-crosscheck-20261125b` was read with `git show` (note draft, spec, writer).

**XC3-FAIL is an open author decision** (written up by the xc3 unit; signed in the xc3 note's `xc3_fail` line and the
PLAN row R1-XC3-FAIL-READING). *(Round 1, M3:)* the switch reads the value from `main` and **both options are built**
behind it (§9): **A**, a failed or missing short check keeps only that node's audits off TASL-7; **B**, a node whose
short check was run and did not PASS leaves G.5 (STOP 5 at every job of that node, TASL-2 included). The code does not
choose between them.

## 2. Design: R1-G5-AUDIT-TWO-CARDS (amends G5-SLOT A)

**Spec** (`g5_tasl_spec.json`). New block `tasl7_audits`; `slots` gains `worker_host` `TASL-2` and `audit_hosts`
`[TASL-2, TASL-7]` (bound to G5-SLOT A by `required_settings`). G5-SLOT B stays refused. The validator
(`_check_tasl7`) requires:
- identity, environments (`torch312`, `jax312`), extra environment (`XLA_FLAGS`), base, `uv` and the isolation host
  check record equal to the TASL-7 host of the signed G.1b spec (`g1b_tasl_spec.json`, sha256 `7ff3c95b…`): the host,
  card and environments on which G.1b measured the three TASL-7 nodes;
- `lease` equal to `proposer.lease` (the server's lease), `gpu_uuid` and `hostname` equal to the proposer's;
- `families` exactly `["G5-7"]`; `harness_dir` equal to the G5-7 family's path and so not a G.1b or G.4 checkout;
  `runs_root` equal to the worker's (the same layout on both hosts);
- `crosshost_pass` naming exactly the seven nodes (autoresearch absent): for `mlab_cifar10`, `mlgym_cifar10`,
  `mlgym_breakout_minatar` exactly their step-1 (`xc`) and step-2 (`preassembly`) xc2 verdicts of run
  `g1b-tasl-20261121-b-xc2`, each with its sha256; for the other four the PENDING marker or a record list with at
  least one `xc` record;
- `node_extra_env`: a node with a placeholder here is refused on TASL-7. *(Round 1, n1:)* `mlgym_houseprice`'s
  `AR_HOUSEPRICE_TRAIN_CSV` on TASL-7 is filled with `/home/dowling/r1_inputs/house-prices/train.csv`, the xc3 spec's
  `extra_env_additions.TASL-7` value.

**Which xc2 verdicts, and why both.** Step 1 (`G1B_XC2_STEP1_VERDICT_<node>_20261122.json`) compares the two hosts'
cross-check runs: the same code and environment give the same outcomes on both cards. Step 2
(`G1B_XC2_STEP2_PREASSEMBLY_VERDICT_<node>_20261124.json`) compares the node's own G.1b TASL-7 attempt with the
TASL-2 cross-check attempt: the row's literal comparison, and the one the G.1b assembly gate binds. TASL-7 audits
must reproduce TASL-2's measurements, so both are required; both are PASS on `main`. sha256s bound in the spec:

| Node | Step 1 (`xc`) | Step 2 (`preassembly`) |
|---|---|---|
| `mlab_cifar10` | `e5264c0b…` | `9403653f…` |
| `mlgym_breakout_minatar` | `29fe460e…` | `503fc731…` |
| `mlgym_cifar10` | `cbd4b05f…` | `fea9ca97…` |

At each TASL-7 job start `check_crosshost_pass` reads each record from `main`, checks the sha256 and the verdict
(schema `g1b_tasl_crosscheck_verdict/1`, this node, PASS with no reason, complete, the mode, R1-T1-TASL-ENV, the
seven nodes' pin `c025f89a`, the signed G.1b spec sha256 and run id, both hosts present and each side deterministic,
and the cross-check run id).

**Leases and "no campaign wave holds the server".** A TASL-7 chunk takes TASL-7's `~/r1_locks/gpu0.lock`, the lease
`g4_tasl.serve_spec` holds for the server's life. A running server therefore keeps every TASL-7 chunk out, and a chunk
keeps a server from starting. After the lease, `server_down` requires the server's `/health` not to answer; a campaign
wave needs that server. TASL-2's lease is unchanged. TASL-7 chunks are refused under G5-TASL-GPUH B (its meter counts
the proposer card from TASL-2's server spans; not worked out for two cards).

**One table, one GPU model.** `g1b_tasl.gpu_check` (already: the card's model must be the RTX 4090) and, in addition,
the job record's `gpu.name` against the spec's `gpu_model`, on both hosts.

**TASL-7 harness checkout and environment.** The audit engine `trackg/audit_g5.py` at the reviewed G5-7 tip `cbf7a003`
(read with `git show` only) binds no host: it takes the leased card's UUID with `--gpu-uuid`; its docstring names
TASL-2 only. TASL-7 needs a new G5-7 checkout at `/home/dowling/r1_tracks/t1_tasl/harness_g5` (G.1b's TASL-7 checkout
`.../harness` stays at its pin) holding both G.5 commits for `g5_pin_check.py`, and a G.5 paper checkout for the
launch binding (cluster test C16). Autoresearch's audits stay on TASL-2: `ar-cond7a` exists only there, and the switch,
`claim_chunk` and `worker_shim` each refuse it on TASL-7.

**The TASL-7 host check record.** `reports/trackg_g0_20261117/TASL7_ISOLATION_HOST_CHECK_BINDING_20261121.md`,
sha256 `09945c15df67b2627a97e6cc59239744738aecb14e522f7c52d1f390be4576a4` (`host_check_items: 1-7 PASS`,
`host_check_verdict: PASS` at `c025f89a`; item 7, CUDA IPC, untested). Checked on `main` at each TASL-7 job start
(`tasl7_host_check`), named in the `tasl7_audits` note line, and required in the note's P1 (`check_note`).

**State and order** (the TASL-2 runs tree stays the table's tree; `g5_job.py`):
1. A wave's plan is made on TASL-2 by its first audit chunk, as before.
2. `claim_chunk` (TASL-2; CLI `claim-chunk`): refuses autoresearch, a wave without a plan, the wave's last chunk (it
   computes E5 over all chunks), a chunk TASL-2 started, a chunk already claimed, a second open claim, and TASL-2's
   order checks (STOP 11 over the access log, a STOP on record, the meter above the cap). It writes
   `<run_id>/_remote/claims/<node>/audits-wave<w>/chunk-<i>.json` once, with the plan's sha256s, K and the meter.
3. The operator copies the claim and the wave's `plan_index.json` and `plan.tar` to TASL-7 (same paths) and runs
   `t1_tasl_node.sh g5t7 <spec> <node> <note> audits-wave<w> <i> --enable`, i.e. `g5_tasl.py run ... --host TASL-7
   --chunk <i>`. The switch adds the TASL-7 checks; `run_job` checks the claim against the job, the plan index against
   the claim, and the meter (the claim's TASL-2 reading plus the TASL-7 records the claim does not list as registered;
   round 1, m5); it reads the plan with an access-log line on TASL-7, runs exactly the claimed chunk, and writes
   no plan, no K lock and no wave checks. Its record carries `worker_host`, `claim_sha256` and `crosshost_pass` (the PASS
   records the switch checked).
4. `register_attempt` (TASL-2; CLI `register-chunk`): the attempt directory and TASL-7's `_access_log.jsonl`, copied
   back. It requires the claim, an attempt of exactly that chunk, spec and plan from TASL-7 (record `worker_host` and
   claim sha256; a closed attempt by its `attempt.json` host), the sums (a closed attempt has none and no `out.tar`),
   only attempt files, no overwrite, and only registered attempts in that chunk. The access log passes STOP 11 and must
   extend the copy registered before (kept as `_remote/TASL-7/access_log-<n>.jsonl`). The copy is verified file by
   file, and a registration record is written. Only then does the chunk count for the meter, the STOP records, E5,
   the wave checks and the seal.
5. `next_chunk` on TASL-2 skips claimed chunks; the wave's last chunk waits ("STOP (not yet)") until every claimed
   chunk of the wave is registered complete. A claim closes when a registered attempt is complete or ended in an
   author STOP; an infrastructure STOP leaves it open for a new TASL-7 attempt.
6. `seal_run` also tars `_remote` (claims, registrations, the TASL-7 access-log copies). Registered attempts lie in
   their chunk directories and are sealed as attempts. The assembly and the release step read one sealed tree, as
   before.

**Note lines** (re-rendered, §4): `hosts`, `gpu_model` and `job_layout` changed; `tasl7_audits` and `t1_node_scope`
are new.

**The switch** requires the rows R1-T1-D21-SCOPE (terms "D21 does not select T1 nodes for C3", "no other threshold is
introduced") and R1-G5-AUDIT-TWO-CARDS ("Amends G5-SLOT A", "while no campaign wave holds the server", "cross-host
check PASS") on `main` for every job, and adds both to the launch binding's rows. Both pass on `5d4f1b09`'s PLAN (the
tests read this checkout's PLAN lines).

## 3. Design: R1-T1-D21-SCOPE

Every place where D21 STOPped or excluded a node, and what it does now:

| Place | Before | Now |
|---|---|---|
| Switch, STOP 5 (`g5_tasl.launch`) | `qualifies_D21` false → node STOP | determinism: `g1b_verdict_scope(...)["deterministic"]` false → node STOP 5; the D21 value goes to `context["d21"]` |
| `check_g1b_copy` | returned `qualifies_D21` per node | also `scope` per node (determinism and the D21 record) |
| `check_ar_record` | `d21_verdict` must equal the copy's verdict; returned `qualifies_D21` | unchanged consistency check (a record, not a gate); also returns `scope` |
| `g5_assemble.noise_by_node` | cited node without `qualifies_D21` → STOP 5 | `require_deterministic` (STOP 5 on determinism); each node's entry gains `d21`, so `build.json` and the noise record carry it |
| `g5_noise.derive` | values from `noise_by_node` | unchanged code; the record's node entries now carry `d21` (docstring) |
| `noise_precheck`, `check_usable` | σ̂_node and δ_n finite and > 0 | unchanged (kept) |
| `g5_relcopy` | counts checked for qualifying or counted verdicts; a verdict without counts passed through | unchanged: a non-qualifying deterministic verdict carries counts and is checked; a determinism-failed one is passed through and STOPs later |
| Release checks (`r1/c3/release_checks.py`) | no D21 test | unchanged |
| Note | — | new line `t1_node_scope` |
| T1 release rows draft | "D21 verdict must be `qualifies_D21: true`; otherwise STOP 5" | determinism PASS; D21 recorded; the pre-release one-liner prints the determinism result per node |

**Determinism** is read from the verdict `g1b_lib.summarise` writes: a PASS needs `determinism.deterministic: true`
and not the "fixed-seed determinism failed" verdict. A verdict without a determinism result is not a PASS
(conservative; the real summaries carry it for every node). The test fixtures that lacked the field gained it.

**The cross-host gate** stays structural: the seven-node copy must carry `crosscheck_gate.json` naming the three TASL-7
nodes and binding the summary's assembly (`check_g1b_copy`), or every job STOPs; the switch also puts the gate's entry
for a TASL-7 node into the context.

**σ̂_node for a non-qualifying node.** T0's definition: the median sd over material edits, or over all edits with an
sd if none is material. A non-qualifying node may have one material edit (σ̂_node is that edit's sd) or none (the
fallback). **Decision: the fallback must still be finite and > 0, and δ_n too; the existing STOP is kept unchanged.**
σ̂_node divides the soft-label width and the gain z-scores, so 0 or a non-finite value cannot make labels; flat paired
differences (sd 0) or no edit with three paired seeds still STOP. D21's own `σ_joint > 0` test is not applied to
σ̂_node. No new threshold.

**Where the funnel reads the D21 value** (R1-BX-D12): `d21` in each node's entry of the T1 noise record
(`g5_noise.derive`, committed and reviewed) and of `build.json`: `qualifies_D21`, `n_material`,
`mean_p_wrong_material` (null if not finite), the rule's `checks`, `reason`, `selects: false`, `rule:
R1-T1-D21-SCOPE`. The REL-T1-G1B copy record's `d21_verdict` and the launch context carry it too. `build.json` is
table bytes: adding the key changes the table's bytes, not its schema name; `serialize_t1` reads only named keys.

**The READY 97 / READY 103 code and "qualifying".** The only "qualifying" test in the table and noise code was
`noise_by_node`'s (above). `g5_features`, `serialize_t1` and the D7-DIFF B code have none.

## 4. The §5 block

`key-lines` on this branch prints 55 lines (spec sha256 `a80b16e2d912c1853236de09df1b4ae3735f3b27636cab39b26366f4e9d0029d`
after review round 1; `eef8f5eb…` before, when the round-1 fill of `mlgym_houseprice`'s TASL-7 path had not been made
and the `tasl7_audits` line named XC3-FAIL A only).
Against revision 10's 53: `hosts`, `gpu_model`, `job_layout`, `spec_sha256` changed; `tasl7_audits` and
`t1_node_scope` added; 49 unchanged. The draft's block was replaced by this render (only the first line reads
`approved: false`), checked byte for byte. The harness commits stay PENDING, so one more render follows that fill.

## 5. What the note must fix

- **The schedule** (the row says the note fixes it): the phases in which the server is stopped for TASL-7 audit chunks
  (between campaign waves; each restart is a new server record, checked by the campaign jobs as before, and sealed with
  `seal-server`), which nodes' chunks are claimed for TASL-7 and in which order, and that a claimed chunk runs only on
  TASL-7. The code enforces the rules, not a timetable.
- P1 citing the TASL-7 host check record (enforced by `check_note`).
- The rendered lines `hosts`, `gpu_model`, `job_layout`, `tasl7_audits`, `t1_node_scope`.
- C16 (TASL-7 checkout, environments, one chunk end to end) before the first TASL-7 chunk; the TASL-2-only table does
  not wait for it.

## 6. Open items and author decisions

1. **XC3-FAIL (author decision, open):** both options are built behind the value the switch reads from `main` (the
   signed xc3 note's `xc3_fail` and R1-XC3-FAIL-READING, which must agree). The xc3 names may still change slightly
   (rebuild on `mac-xc3-short-crosscheck-20261125c`, "format stays the same"); a change of names or fields needs a
   reviewed code change here; until then those nodes stay TASL-2 only (fail closed).
2. **The xc3 unit's own note check** (`g1b_crosscheck.check_xc_note`, `short_decisions`) is not in this branch's
   `g1b_crosscheck.py`; the switch applies the same key-line rules itself (`xc3_reading`). Switching to the xc3
   functions once that unit is on `main` is a reviewed follow-up (both live in `sweep2/t1_tasl`, which is frozen from
   the G.5 launch, so it must happen before).
3. **The CUDA-IPC acceptance line** names TASL-2 only. If the author signs it instead of C12, its wording should cover
   TASL-7's audit chunks (item 7 is untested on TASL-7 too). The code renders the line unchanged (an author wording
   decision; changing it is a code change to `CUDA_IPC_ACCEPTANCE`).
4. **The meter reading** counts registered TASL-7 chunks as worker-card hours against the 425 GPU-h cap (G5-TASL-GPUH A
   counts "the worker card"; with two cards doing worker runs, both cards' worker runs count). This is the conservative
   reading; the alternative (TASL-7 audit hours outside the cap) needs an author row.
5. **Abandoning a claim** (round 1): `abandon-claim` relies on the operator's confirmation that every TASL-7 attempt of
   the chunk is registered (the code cannot see TASL-7's tree). An unregistered attempt found later cannot be
   registered (the claim is abandoned) and is reported to the author.
6. TASL-7's `_refusals/` stay on TASL-7 and are not sealed (refusal texts only, before any attempt; disclosed). The
   node wrapper log of each registered attempt is registered with it (round 1, m7). `close-attempt` on TASL-7 works
   unchanged (same lease string and layout).
7. Not worked in: R1-T1-NODE-EXPANSION. A candidate that enters G.5 by 2 Dec needs its own spec entry, split-file
   entry and a code change (`T1_NODES`, the split file is frozen with eight nodes), which this unit does not make.

## 7. Tests

Targeted, one file at a time (`/tmp/tgport312/bin/python -m pytest -q -p no:cacheprovider`, `AR_HARNESS_ROOT=/tmp/pb/wt/t1h`):

| File | Result |
|---|---|
| `test_t1_g5_tasl.py` | 138 passed after review round 1 (115 before this unit; 135 at `e7ab0c36`) |
| `test_t1_g5_job.py` | 50 passed after round 1 (37 before this unit; 42 at `e7ab0c36`) |
| `test_t1_g5_seal.py` | 38 passed (2 new) |
| `test_t1_features.py` | 30 passed, 1 skipped (fixture gains the determinism field) |
| `test_t1_tasl_g1b.py` | 45 passed |
| `test_t1_tasl_crosscheck.py` | 30 passed |

Also run: `test_t1_tasl_g4b` 5 (after the second merge), `test_t1_d7_diff_b` 19, `test_t1_tasl_chain` 16, `test_t1_tasl_g1b_ar` 69, `test_t1_tasl_g4` 47 (30 before the second merge),
`test_t1_tasl_g5_ar_projection` 6, `test_t1_tasl_g5_pin_check` 7, `test_trackp_t1_prompt` 17, all passed.

New tests, by rule:
- non-qualifying node recorded, not STOPped: `test_switch_rel_t1_g1b_copy_checks_and_stop_5` (seven-node),
  `test_stop_5_for_autoresearch_from_its_record` (autoresearch), `test_d21_scope_noise_by_node_records_d21_and_stops_on_determinism`
  (assembly), `test_d21_scope_verdict_record_and_determinism` (the helper, JSON-safe record);
- determinism and cross-host failures still STOP: `test_d21_scope_determinism_and_cross_host_still_stop`,
  `test_d21_scope_verdict_record_and_determinism`, the assembly test above;
- no usable σ̂_node still STOPs for a non-qualifying node: `test_d21_scope_non_qualifying_node_without_usable_sigma_still_stops`;
- both rows required on `main`: `test_d21_scope_rows_are_required_on_main`;
- TASL-7 audit refused without a PASS record: `test_two_cards_tasl7_audit_launch_needs_the_cross_host_pass` (changed
  record, missing host check), `test_two_cards_pending_node_runs_on_tasl2_not_on_tasl7_until_its_pass` (fail closed without
  a file; accepted from `main` in the xc3 shape without a spec change; a STOP verdict, wrong mode, rule, node or spec,
  missing side or side field, `complete: false`, another label: each refused on TASL-7 only, as a refusal and not a
  node STOP, while the node still runs on TASL-2 (XC3-FAIL A); two verdicts and a near-miss name refused);
- TASL-7 audit refused while a campaign wave holds the server, and while the server's lease is held:
  `test_two_cards_tasl7_chunk_refusals`;
- refused on a GPU model mismatch: `test_two_cards_tasl7_chunk_refusals`;
- autoresearch refused on TASL-7: switch, `claim_chunk` and `worker_shim` (three tests);
- spec and slot binding: `test_two_cards_spec_block_and_pending_markers`, `test_two_cards_spec_tampering_stops` (11
  cases), `test_two_cards_slot_amendment_is_bound`;
- claims, order, registration and E5 end to end: `test_two_cards_claims_on_tasl2`,
  `test_two_cards_claim_run_register_end_to_end`, `test_two_cards_register_refuses_a_tampered_or_foreign_attempt`;
- the TASL-7 job record carries the PASS records it ran under (`crosshost_pass`):
  `test_two_cards_claim_run_register_end_to_end`;
- the seal and the wrapper: `test_two_cards_seal_run_takes_the_remote_records`, `test_two_cards_node_wrapper_kind`.

## 8. Full suite

`/tmp/tgport312/bin/python -m pytest -q -p no:cacheprovider -rfE r1/tests`, LightGBM not importable (it is not on
that interpreter's path), `PYTHONPATH` unset, a fresh `TMPDIR` per run, `AR_HARNESS_ROOT=/tmp/pb/wt/t1h`, each run
started only when no other `pytest ... r1/tests` process was running.

| Run | Checkout | Result | List |
|---|---|---|---|
| base 1 | clean detached `origin/main` `912a7e02` | 58 failed, 3972 passed, 197 skipped, 3 errors | `FULLSUITE_BASE_912a7e02_DEFAULT_RETENTION_FAILED.txt` (61) |
| tip 1 | this branch at `430b0018` (before the xc3 adaptation) | 58 failed, 3998 passed, 197 skipped, 4 errors | (identical to base 2; superseded by tip 2) |
| tip 2 | this branch at `209b2db4` (the xc3 consumer and XC3-FAIL A; code final) | 58 failed, 3998 passed, 197 skipped, 4 errors | `FULLSUITE_TIP_SCOPE_TWOCARDS_FAILED.txt` (62) |
| base 2 | the same base checkout | 58 failed, 3972 passed, 197 skipped, 4 errors | `FULLSUITE_BASE_912a7e02_FAILED.txt` (62) |

Base 1 filled the disk with retained pytest temporary directories (5.2 GB under its `TMPDIR`), so the tip run used
`-o tmp_path_retention_policy=failed`. Under that option one teardown error appears that base 1 does not have:
`test_c3_mount_inode_candidate.py::test_bind_and_raw_mount_always_stop_before_io`, pytest's own cleanup of that test's
temporary directory (a `TypeError` inside `shutil.rmtree`; the test touches no file of this unit). Base 2 reran the
base with the same option and shows the same error. **Both tip lists are byte-identical to base 2's: zero new
failures.** Only this report and the lists changed after tip 2.

**After review round 1** (default options, as the coordinator asked, comparable to the standard 61-line baseline): the
tip `f8da2c5b` (the round-1 code; only docs and lists changed after it) gives 58 failed, 4009 passed, 197 skipped, 3
errors; its sorted list `FULLSUITE_TIP_SCOPE_TWOCARDS_R1_DEFAULT_FAILED.txt` (61 entries) is byte-identical to the
default-option base list on `912a7e02` (`FULLSUITE_BASE_912a7e02_DEFAULT_RETENTION_FAILED.txt`, base 1 above): zero
new failures. The TMPDIR was deleted right after the run. Base 1's list equals both minus that one entry. The 26 extra passes at the tip are this unit's new tests.

## 9. Review round 1: findings and changes

Round 1 at `e7ab0c36` (scope `git diff 912a7e02 e7ab0c36`): NOT ACCEPTED, 3 MAJOR, 8 minor, 6 nits; part (a) accepted
as is. Main had not moved (`912a7e02`). Changes on top of `e7ab0c36`:

| Finding | Change | Tests |
|---|---|---|
| **M1** a claim for a node that cannot run on TASL-7 deadlocks the wave | `claim_chunk` first runs `tasl7_eligible`: G5-7 family, G5-TASL-GPUH A, no placeholder in `node_extra_env` (factored out of `worker_shim` as `tasl7_env_open`), `S.tasl7_host_check`, `S.check_crosshost_pass` (with XC3-FAIL and `skip_nodes`). New `abandon_claim` (CLI `abandon-claim`, TASL-2): only while the claim is open (no registered attempt complete or in an author STOP), a reason of ≥ 10 characters, TASL-7's access log registered in the same call; effect stated in its record (the chunk returns to TASL-2; nothing more is registered into the claim); the record lies under `_remote/abandoned/` and is sealed with `_remote` | `test_two_cards_m1_claims_only_for_a_node_that_can_run_on_tasl7`, `test_two_cards_m1_abandon_claim_returns_the_chunk_to_tasl2` |
| **M2 (a)** registration out of order | attempt N requires N = 1 + the highest registered attempt of the chunk | `test_two_cards_m2_every_tasl7_attempt_is_registered_in_order` (reviewer's scenario 1: an infrastructure-STOP attempt 1 cannot be skipped; both reach the meter) |
| **M2 (b)** registration into a closed claim (and m1) | refused into a closed or abandoned claim (`g5_seal.claim_state`) | `test_two_cards_m2_no_registration_after_a_node_stop` (reviewer's scenario 2), the end-to-end test (a second registration after a complete one) |
| **M2 (c)** seal with an open claim | `seal_node` refuses with an open claim on the node; `seal_run` refuses (first thing) with any open claim; `node_finished` returns None while the node has one | scenario-1 test |
| **M2 (d)** no final access-log registration | new `finalize_remote` (CLI `finalize-remote`): no open claim; afterwards no claim, registration or abandonment; `seal_run` requires it, later than every registration and abandonment and naming the last log copy, whenever TASL-7 had claims (`check_remote_final`) | end-to-end and scenario-1 tests |
| M2 draft wording | draft §2.10 step 4 "Every TASL-7 attempt must be registered", steps 5–6, §4 item 16 | — |
| **M3** XC3-FAIL in two places, only A enforced | `g5_tasl.xc3_reading` reads, from published `main`, the signed xc3 note (exactly one `g1b_xc_short_t1_tasl_<YYYYMMDD>.md`; `approved: true`; one `xc3_fail` A/B; `skip_nodes`; where the xc3 spec is on `main`, its `run_id` and `xc_spec_sha256`) and R1-XC3-FAIL-READING (at most once, exactly one of `xc3_fail: A`/`B`); they must agree. **B is built** behind that value (`xc3_b_check`, at every job start of a short-check node, TASL-2 included): a committed STOP short verdict is STOP 5; a PASS or no verdict goes on; a skipped node is untouched; an unreadable verdict file refuses. Chosen over "STOP the launch under B" because it is small, applies only to the nodes B names, and leaves the other six nodes and the launch alone. `skip_nodes`: the TASL-7 gate refuses a skipped node (no short check). With no note and no row on `main`: "A pending" (the TASL-7 gate refuses the short-check nodes; B never applies). The xc3 unit's `check_xc_note`/`short_decisions` are not in this branch's `g1b_crosscheck.py`, so the same key-line rules are applied here (§6 item 2). Draft §2.10 and §11 item 21 name the coupling | `test_two_cards_xc3_reading_from_main`, `test_two_cards_xc3_fail_b_removes_a_failed_node_from_g5`, `test_two_cards_xc3_note_binds_the_xc3_spec_on_main` |
| m2 | `register_attempt` requires the record's `crosshost_pass` non-null and equal to a fresh `check_crosshost_pass` on `main` | `test_two_cards_m2_registration_rechecks_the_cross_host_pass` |
| m3 | short reader: `crosscheck_run_id` the xc3 spec's run id on `main` (else the note's, else the prefix `g1b-tasl-20261121-b-xc3-`); TASL-2 side `run_id` = `g1b_run_id`; TASL-7 side `<xc3 run>-TASL-7`; `label` and `complete: true` required | the pending-node test (wrong run id, wrong side run ids, missing label/complete) |
| m4 | flock `_remote/claims.lock` (`claims_lock`), held by `claim_chunk`, `abandon_claim` and around TASL-2's `next_chunk` … `next_attempt` | `test_two_cards_m4_tasl2_takes_the_claims_lock_around_its_chunk_pick` |
| m5 | the claim lists `registered_attempts_at_claim`; `check_order_tasl7` adds only TASL-7 records not in that list | `test_two_cards_m5_tasl7_meter_does_not_double_count` |
| m6 | draft §2.10 "Mixed-host labels" and §3 (funnel discloses per node whether chunks ran on TASL-7) | — |
| m7 | `register_attempt` requires the node wrapper log the record names (`--node-log`) and files it under `_remote/TASL-7/logs/` (sealed with `_remote`); TASL-7 refusals stay unsealed, disclosed | `test_two_cards_m7_node_wrapper_log_is_registered` |
| m8 | only `.json` named exactly `G1B_XC3_SHORT_VERDICT_<node>_<YYYYMMDD>.json` directly under `docs/r1/reports/<dir>/`; `*_captures/` copies ignored; other `.json` naming the token refused; non-`.json` ignored | pending-node test |
| n1 | `mlgym_houseprice`'s TASL-7 `AR_HOUSEPRICE_TRAIN_CSV` filled from the xc3 spec's `extra_env_additions.TASL-7` (spec sha256 now `a80b16e2…`; §5 re-rendered: `tasl7_audits` and `spec_sha256` changed) | `test_two_cards_tasl7_chunk_refusals` |
| n2 | `cpus`/`logdir` take `--host`; the wrapper's `g5t7` kind passes `--host TASL-7` | `test_two_cards_node_wrapper_kind` |
| n3 | a missing `job_record.json` in a staged attempt is a STOP, not a raw error; a missing access-log copy too | tamper test, abandon test |
| n4 | draft §11: XC3-FAIL is item 21 (after 20), the D21 item 22; release rows draft: "the item of the STOPped node is then removed", a non-qualifying node's item stays | — |
| n5 | §5 lead: the render is of this branch (which contains `main` `912a7e02`), not of `main` | — |
| n6 | operator `git fetch origin` before each claim and TASL-7 job: draft §2.10 step 2 and C16 | — |

