# G.5 audit hosts beyond the TASL pair — unit report (27 Nov 2026)

Card `local/20261126-06` unit 2, tier E. Branch `mac-g5-audit-hosts-20261127` from `origin/main` @ `6684e840`.
Code commit `540eefd7`; this report is the commit after it (the branch tip is given in the coordinator report, read
from git). AI-assisted (Claude), local worker. Supersedes nothing. Review: pending (a fresh reviewer, not this agent).

## 1. Content

The signed G.5 note (revision 13) keeps TASL-7 as its one extra audit host, read from the spec's `tasl7_audits` block
exactly as before. Further cards join through **a separate addendum spec** (`g5_audit_hosts_addendum/1`) bound to the
signed spec by its sha256, and **an addendum note** `docs/r1/authorizations/c3_t1_labels_audit_hosts_<YYYYMMDD>.md`
bound to the signed G.5 note by its path. The list of audit hosts (`g5_audit_hosts.audit_hosts`) is TASL-7 followed
by the addendum's cards (one entry per card: Ada's eight cards are eight entries on `ucrtasl`). Each card carries its
identity (hostname, GPU UUID, GPU model, driver), its own GPU lease, the R1-CARD-SHARE free-memory floor, the G5-7
checkout and the table's runs-tree layout, environments, its harness-isolation host check record, its C12 record (or
the addendum's own CUDA-IPC acceptance line), the cross-check spec it was checked under, and per G5-7 node the short
cross-check PASS record against the node's sealed TASL-2 attempt (or `PENDING short cross-check: <node>`). A node is
admitted on a card at each claim and job start (`check_admission`; at the registration it is re-read for information
only); any failure refuses that node on that card only. A card of **another GPU model** than the table's RTX 4090 is refused for every G.5 audit chunk unless
the author's row `R1-G5-AUDIT-HOST-CLASS` is on main naming that model (R1-HOST-FREE (2)(a), §3). The job side reuses
TASL-7's claim → run → register path with the host named in the claim: one open claim per host, the card's own lease,
its GPU model and driver checked, its free memory checked and its other compute processes recorded (count and memory)
at the start, before the engine and after the engine; an attempt that saw another compute process is an
infrastructure failure and is repeated (R1-NO-TIMEOUT (2)); each host's access log is registered under
`_remote/<host>/` with its own final registration, and `seal_run` requires each. The **Ada cross-check spec** for
the eight nodes (`sweep2/t1_tasl/g5_audit_host_xc_ada_spec.json`, sha256
`8470694f42c49ff3d0e0068da2f9ffeed86517689c47290822e2434f6cf8daf7`, ENGINEERING_ONLY, draft, not launched) names each
node's sealed TASL-2 reference attempt and checks it against the record on main that holds it; its projection is
2.94 GPU-h (3.535 at the sensitivity ratio 1.5; cap 4.0). The **addendum note draft** is
`docs/r1/proposals/G5_ADDENDUM_AUDIT_HOSTS_DRAFT_20261127.md` (`approved: false`).

Files: `sweep2/t1_tasl/g5_audit_hosts.py` (new), `sweep2/t1_tasl/g5_audit_host_xc_ada_spec.json` (new),
`sweep2/t1_tasl/g5_tasl.py` (switch, CLI, docstring, import-source list), `sweep2/t1_tasl/g5_job.py` (claim, run,
registration, abandonment, final registration per host), `sweep2/t1_tasl/g5_seal.py` (final registration per host),
`r1/tests/test_t1_g5_audit_hosts.py` (new), the draft note. Not changed: `g5_tasl_spec.json`, `g1b_crosscheck.py`, the
xc3 spec and `build_xc3_launch.py`.

## 2. Backward compatibility (the signed configuration)

- `g5_tasl_spec.json` is byte-identical to `main` (sha256 `16b39b47…`); `note_lines` renders the same key lines for it
  (sha256 of the sorted key-line JSON `74f93fa5…`, and `1c892d6e…` under G5-TASL-GPUH B, both computed on the base and
  pinned in the test). The addendum never enters `note_lines` or `check_note`.
- `launch` on TASL-2 and TASL-7 runs the same checks in the same order; it refuses an addendum argument; a host outside
  the pair without an addendum gets the same "host must be one of" STOP.
- A TASL-7 claim has exactly its former fields (tested); the TASL-7 job, registration, abandonment, final
  registration and `check_remote_final` keep their paths, records and messages (the existing TASL-7 tests pass
  unchanged); the empty-card check stays for the TASL pair (R1-CARD-SHARE (5)).
- `dates --tasl7-audits` counts the TASL pair only (decided alone; the addendum hosts' hours are counted by the meter).

## 3. Which audit work may move to Ada (R1-HOST-FREE (2)(a)/(b))

| Work | Ada? |
|---|---|
| campaign waves (proposer, worker slot) | never (G5-SLOT A amended; (2)(c)) |
| a wave's plan and its last chunk (E5) | never (TASL-2 by the code) |
| autoresearch's audits | never (`ar-cond7a` only on TASL-2; the addendum admits the G5-7 family only) |
| noise floors | never re-measured; used on a second host only with the node's cross-host PASS ((2)(b)) |
| other audit chunks of a G5-7 node | **only with `R1-G5-AUDIT-HOST-CLASS` on main and the node's Ada PASS** |
| the Ada short cross-check (ENGINEERING_ONLY) | yes, under its own note, by a later runner unit |

Why the row is needed: the candidate and the parent of a proposal are separate units of the wave's plan, and
`g5_job.chunk_plan` cuts the plan's (unit × seed) runs into chunks without regard to proposals (and under
`reuse_parent_runs` a code state's runs serve every role across waves). A chunk on an Ada card therefore holds
candidate runs whose parent ran on a 4090, and the reverse — the comparison (2)(a) keeps on one hardware class.
Whole-proposal chunks would change the plan bytes of the TASL pair (a re-issued note), so the conservative form was
built instead: Ada admitted per node only after its cross-host PASS **and** the author's class row. Cards of the
table's GPU model (any further RTX 4090) need no row.

## 4. Decided alone

- The addendum is a separate spec file plus a note, not a field of the signed spec (its sha256 is bound by the note).
- One entry per card; one lease per card; one open claim per host; each host's own access-log copies and final
  registration under `_remote/<host>/`.
- Free-memory floor 24 576 MiB (the RTX 4090's memory, which the G.5 jobs fit); the floor is enforced before the job and
  before the engine, recorded only after the engine.
- An attempt on an addendum card that saw another compute process at any check, ending complete, in a timing STOP or a
  STOP 9, is classed infrastructure and repeated; other node-class STOPs keep their class (not budget-related).
- The Ada cross-check spec's reference attempts: the four xc3 nodes' sealed G.1b TASL-2 attempts (as the xc3 spec
  declares), the three TASL-7 G.1b nodes' xc2 TASL-2 attempts (bit-identical to their G.1b TASL-7 attempts by the xc2
  step-2 PASS), autoresearch's sealed G.1b-AR TASL-2 attempt (`AR_G1B_TASL2_RESULT_20261122.md`). The spec includes
  autoresearch (eight nodes as the card asks) although no addendum admits it.
- The spec's verdict paths are labels dated 20261127 under `docs/r1/reports/g5_audit_hosts_20261127/`.
- The `cpus`/`logdir` queries take `--addendum` for an addendum card; claim-side CLI commands take `--host` and
  `--addendum`; new commands `addendum-lines`, `check-addendum-note`, `host-xc-spec`.
- The claim on TASL-2 checks the addendum spec and the node's admission; the addendum note itself is checked by the
  switch at the job start (where the signed G.5 note is checked).

## 5. For the author (level 2) — AH-CLASS

**Options.** A: G.5 audit hosts beyond the pair are RTX 4090 cards only; Ada is no G.5 audit host (built: the
default). B: a node's short cross-check PASS on an Ada card makes that card one hardware class with the 4090 pair for
that node's G.5 audit chunks (built: the row switches it on). C: whole proposals on one class (not built: needs a
re-issued G.5 note and a plan-code re-review).

**Recommendation: A.** A node's short cross-check shows its default part (baseline and declared edits) bit-identical
on the two models; G.5 audits run arbitrary proposed diffs, and a diff that changes a shape or batch size can make
cuBLAS/cuDNN choose another kernel on a card with another SM count (142 vs 128), so candidate and parent could differ
numerically exactly where (2)(a) forbids it. G.5 starts on the TASL pair now; a spare 4090 lease can join under A
without a row. **Cost:** none (A); for B the Ada cross-check run (≈ 2.9–3.5 GPU-h, cap 4.0) plus its runner unit.
**Blocks:** nothing of G.5 on the TASL pair. Under A, the Ada cross-check spec stays a draft.

Draft row (B):

> | R1-G5-AUDIT-HOST-CLASS | **For the G.5 audit chunks of a G5-7 node, a card of NVIDIA RTX 6000 Ada Generation is
> one hardware class with the RTX 4090 pair once the node has a cross-host PASS** (author, <date>). Reads R1-HOST-FREE
> (2)(a) for T1 G.5 audit chunks and amends R1-G5-AUDIT-TWO-CARDS's "one table, one GPU model" for them: the candidate
> and incumbent audits of one proposal may run on the two GPU models when the node's short cross-check (the default
> part, bit-identical to its sealed TASL-2 attempt, `g5_audit_host_xc_ada_spec.json`) is a cross-host PASS on main and
> an addendum note lists it. Campaign waves, plans, E5 chunks and autoresearch's audits stay on TASL-2. For the
> CPU-only mlgym_houseprice no GPU model enters: its audits on such a host run on that host's CPUs, and the row covers
> them on the same terms (its cross-host PASS on that host's CPU set). The T1 report states per node which audit runs
> ran on which GPU model or CPU (R1-HOST-FREE (4)); no analysis by GPU model is added. |

Draft row (A):

> | R1-G5-AUDIT-HOSTS | **G.5 audit hosts beyond the TASL pair: RTX 4090 cards only** (author, <date>). The
> audit-hosts addendum of the G.5 note (`g5_audit_hosts.py`, reviewed unit `mac-g5-audit-hosts-20261127`) is adopted
> for cards of the table's GPU model; R1-G5-AUDIT-TWO-CARDS's "one table, one GPU model" stands; Ada's cards are not G.5
> audit hosts and the Ada short cross-check spec stays a draft. |

## 6. For the coordinator (level 1)

- Merge after an accepted review; the code changes no signed file and no evidence path of the TASL pair.
- Under B only: a runner unit (local) for the Ada cross-check — the short kind of `g1b_crosscheck.py` for a host
  outside the signed G.1b spec, with an RTX 6000 Ada GPU check (today `g1b_tasl.gpu_check` refuses any model but the
  4090); then its note, the compute agent's host fill (UUIDs; driver 545.23.08 and CUDA 12.4 per the 26 Nov survey;
  the `torch312`/`jax312` environments, which the survey says are not on Ada; the house-prices input; the isolation
  host check at `c025f89a`), the runs at the declared paths, the addendum spec and note.
- Ada's cards 1 and 3–7 carried another user's processes in the 26 Nov snapshot: under the shared-attempt rule only an
  empty card (0 or 2 then) yields countable G.5 attempts.
- The G5-7 checkout and the runs tree must be at `/home/dowling/r1_tracks/t1_tasl/{harness_g5,runs}` on `ucrtasl` (as
  on TASL-7; links into `/data1/dowling` are fine).

## 6a. Review round 1 (fresh tier-E review of `473b17bb`: ACCEPTED WITH MINORS) — corrections

- **m1** (fixed): on a shared addendum card every outcome becomes an infrastructure failure except an infrastructure
  STOP already, STOP 2 (isolation gate), STOP 10 (seed) and the left-processes STOP 9 (`reclassify_shared`); STOP 6
  `baseline_failed` is included (the audit engine can emit it: `engine_stop` maps any engine's `stop_kind`). Tests: the
  rule table and an end-to-end shared baseline_failed attempt (infrastructure) beside an unshared one (node).
- **m2** (fixed): the cross-check spec's host must name the card (`gpu_uuid`) and `driver` its PASS was measured on
  (filled at launch); an entry's driver must equal it; the verdict's host side must carry that `gpu_uuid` and `driver`
  (the later runner unit writes them); the key line names the measured card and states the coverage of the host's
  other cards. Tests: driver mismatch, unfilled spec host at launch, verdict without or with another driver/card, the
  coverage wording.
- **m3** (fixed): the class row must open with the lead sentence of the draft row B naming the GPU model. Test: a row
  naming every term but not as its lead is refused.
- **m4** (fixed): no job and no engine starts on an addendum card beside another compute process (a refusal, no
  attempt burnt at the job start); the note's scope line discloses the three sampling points. Tests updated (a process
  arriving during the engine; a card shared at the start).
- **m5** (fixed): registration re-reads the admission for information only (module docstring, note draft §2, §1 here).
- **m6** (fixed): `finalize-remote --host` must be TASL-7 or a host some claim names (test). Points noted, not built:
  (a) two addenda could name the same card under two entry names; each addendum is validated alone, so the
  coordinator publishes at most one live addendum per card (a later addendum supersedes by naming the same entries);
  (b) the per-host meter at a remote job start counts the claim's TASL-2 reading plus that host's own unregistered
  records, so two remote hosts running at once can each miss the other's in-flight attempt; the cap is a reporting
  threshold under R1-NO-TIMEOUT (3), and every attempt reaches the TASL-2 meter at its registration.
- **m7** (fixed): row B states that it covers the CPU-only `mlgym_houseprice` on the host's CPUs on the same terms.

## 7. Tests

`r1/tests/test_t1_g5_audit_hosts.py`, 17 tests (14 + 3 added in review round 1), synthetic (no GPU, no host, no label):
signed spec bytes and key lines pinned to the base; the switch on the TASL pair refuses an addendum and is unchanged;
a TASL-7 claim keeps its fields; the addendum validator (≈ 25 refusals incl. the TASL pair's hosts, families, hardware
class, paths, card share, CPU sets, environments, placeholders at launch, admission records, cross-check spec binding,
duplicate UUID and lease); the addendum note (draft/strict, on main, `g5_note`, every key line, rows, name); admission
(cross-model needs the row naming the model; same-model needs none; PENDING; verdict content, reference side, sha256,
second file; host check; environment; GPUH B; C12); the Ada spec (validity, projection, tampered references, nodes,
verdict paths, cap, binding); the card-share check (count and memory only, free-memory floor); end to end on an Ada
card with the row: claim, run, registration, a concurrent TASL-7 claim, E5 over both, both final registrations and the
seal check; refusals on the card (GPU model, driver, free memory, campaigns, held lease, autoresearch, houseprice CPU
set and input); a shared attempt classed infrastructure, registered, and repeated; registration under another addendum
refused; the switch on an addendum card (context, refusals, row, addendum note on main, spec binding).

Module tests (`test_t1_g5_job.py`, `test_t1_g5_seal.py`, `test_t1_g5_tasl.py`, `test_t1_tasl_xc3.py`,
`test_t1_tasl_crosscheck.py`): base 20 failed / 377 passed, tip 20 failed / 377 passed, the same failing ids (macOS
tar/sha256sum environment failures of the seal tests, as on the base).

After review round 1, run with `COPYFILE_DISABLE=1` (macOS tar otherwise adds AppleDouble members that break the seal
tests): base `6684e840` 1 failed / 396 passed (a first base run showed 2 failed / 395 passed: one flaky base test); tip
(the correction commit) the five module files plus `test_t1_g5_audit_hosts.py`: 1 failed / 413 passed (396 + 17 new).
The one failing id is the same on base and tip: `test_t1_g5_tasl.py::test_two_cards_xc3_fail_b_removes_a_failed_node_from_g5`.

## 8. Full suite

`TMPDIR=<fresh> PYTHONDONTWRITEBYTECODE=1 AR_HARNESS_ROOT=… python -m pytest -q -p no:cacheprovider -rfE
--continue-on-collection-errors r1/tests`, one run at a time, fresh TMPDIRs; base in a detached worktree at `6684e840`
(removed after), tip at the code commit `540eefd7`.

| | failed | errors | passed | skipped |
|---|---|---|---|---|
| base `6684e840` | 181 | 3 | 4247 | 161 |
| tip `540eefd7` | 181 | 3 | 4261 | 161 |

Failing ids (FAILED + ERROR, 184 each): identical sets — **zero new failing ids**, none gone. The 14 extra passes are
the new tests.

## 9. Open questions

1. AH-CLASS (§5): A, B or C.
2. Under B, whether a per-node PASS on one Ada card covers the other seven cards of `ucrtasl` (built: the PASS is per
   host name in the cross-check spec, so one run serves all eight entries; a per-card run would need eight specs).
3. Whether the shared-attempt rule should be narrowed (today every complete attempt on a card shared at any check is
   repeated; a row-level reading would need the engine to mark timeouts per row).
