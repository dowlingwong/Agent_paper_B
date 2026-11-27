# G.5 addendum note — audit hosts beyond the TASL pair (DRAFT, 27 Nov 2026)

approved: false

**Status.** Draft for the author. Not signed, not published; nothing in it starts a job. It is the template of the
note that admits a card as a G.5 audit host under R1-HOST-FREE (3) ("the G.5 note is signed as drafted for the TASL
pair so that it can start, and further hosts join it through an addendum note") and R1-G5-SIGNATURE (3). When signed
it is published as `docs/r1/authorizations/c3_t1_labels_audit_hosts_<YYYYMMDD>.md`, next to the signed G.5 note, and
`g5_tasl.py check-addendum-note` checks it (strict mode after publication). AI-assisted (Claude), local worker, unit
`mac-g5-audit-hosts-20261127` (card local/20261126-06 unit 2).

**What it does not change.** The signed G.5 note (revision 13) and its spec are not edited: their bytes, their key
lines, the switch on TASL-2 and TASL-7, the cap (425 GPU-h, a reporting threshold under R1-NO-TIMEOUT (3)), K, the
thresholds and the schedule stay as signed. The addendum is a separate spec file bound to the signed spec by its
sha256 and to the signed note by its path.

## 1. What may move to an addendum host, and what may not

| Work | On an addendum host? | Why |
|---|---|---|
| Campaign waves (proposer on TASL-7, worker slot on TASL-2) | **never** | G5-SLOT A as amended by R1-G5-AUDIT-TWO-CARDS; R1-HOST-FREE (2)(c): a campaign keeps its proposer on one GPU model |
| A wave's plan (its first audit chunk) and its last chunk (E5) | **never** | made on TASL-2 by the code (`next_chunk`, `claim_chunk` refuses the last chunk) |
| Autoresearch's audits | **never** | `ar-cond7a` exists only on TASL-2; the addendum admits the G5-7 family only |
| Noise floors (G.1b, G.4b) | **never re-measured** | a node's floor is used on a second host only with its cross-host PASS (R1-HOST-FREE (2)(b)) |
| Other audit chunks of a G5-7 node, on a card of the table's GPU model (RTX 4090) | **yes**, after the node's cross-host PASS on that card's host | the class TASL-2 and TASL-7 already form; the TASL-7 rules apply |
| Other audit chunks of a G5-7 node, on a card of **another GPU model** (Ada's RTX 6000 Ada) | **only with the author's row R1-G5-AUDIT-HOST-CLASS** on main naming that model, and the node's cross-host PASS | see §5: an audit chunk is a slice of (code state × seed) runs, so a proposal's candidate runs and its parent's runs can land on different cards; R1-HOST-FREE (2)(a) keeps "the candidate and incumbent audits of one proposal" on one hardware class |
| The short cross-check of the eight nodes on an Ada card (ENGINEERING_ONLY) | yes, under its own note (later unit) | it is how (2)(b) is met and what the class decision would rest on; spec `sweep2/t1_tasl/g5_audit_host_xc_ada_spec.json` (draft, not launched) |

Without the row, the code refuses every claim and every job start of a G.5 audit chunk on a card of another GPU model
(`g5_audit_hosts.hardware_class`), whatever the addendum says. Fail closed.

## 2. What the addendum names per card

One entry per card (Ada's eight cards are eight entries on hostname `ucrtasl`), in the addendum spec
(`g5_audit_hosts_addendum/1`, validated by `g5_tasl.py addendum-lines <spec> --addendum <file> [--launch]`):

- **identity**: entry name (`Ada-g0` …), hostname, GPU UUID, GPU model (the nvidia-smi name), driver — checked at
  every job start (`g5_audit_hosts.gpu_check`);
- **its own GPU lease** (`~/r1_locks/…`; one lease per card; no two of our G.5 jobs on one card) and the
  **free-memory floor** of R1-CARD-SHARE (proposed 24 576 MiB, the memory of the 4090 the G.5 jobs were sized on): a
  job starts beside other compute processes when the card has that much free memory, and each check records the
  count and memory of the card's other compute processes (never owners or commands);
- **the harness-isolation host check record** of that host (items 1–7 of `reports/HARNESS_ISOLATION_20261117.md` §3
  at the seven nodes' G.1b pin `c025f89a…`, `host_check_host: <hostname>`), on main at its sha256;
- **paths**: the G5-7 checkout at `/home/dowling/r1_tracks/t1_tasl/harness_g5` and the runs tree at
  `/home/dowling/r1_tracks/t1_tasl/runs` (the table's layout, as TASL-7: claims, plans and attempts copy by relative
  path; on `ucrtasl` these may be links into `/data1/dowling`), the environments `torch312` and `jax312` (freeze-checked
  at every job start), the extra environment, and for `mlgym_houseprice` its CPU set on that host (same size as its
  G.1b set);
- **its C12 record** under `cuda_ipc: c12`, or under the acceptance mode the `addendum_cuda_ipc` acceptance line
  below, signed with this note;
- **the cross-check spec** it was checked under (path, sha256, host name) and, **per G5-7 node, the short cross-check
  PASS record** `docs/r1/reports/<dir>/G5_AUDIT_HOST_XC_VERDICT_<host>_<node>_<YYYYMMDD>.json` with its sha256, or
  `PENDING short cross-check: <node>` (the node then runs on the TASL pair only, R1-XC3-FAIL-READING).

At each claim (on TASL-2) and job start (on the card) the node's admission is read on main
(`g5_audit_hosts.check_admission`; at the registration on TASL-2 it is re-read for information only and never blocks
the accounting, as TASL-7's cross-host PASS): the G5-7 family, G5-TASL-GPUH A, environment filled, host check, C12 where
required, hardware class, the cross-check spec in the checkout at its sha256, the PASS on main at its sha256 (this node,
mode short, complete, PASS, both sides deterministic, the TASL-2 side the node's declared sealed attempt, the host side
`<run>-<host>` on the card UUID and driver the cross-check spec names), and that file the one such verdict of the node
and host on main. The PASS is measured on one card of the host under one driver: an entry is admitted under it only
with that driver, on that host and GPU model; the key line names the card it was measured on, so the coverage of the
host's other cards is stated in the note. A new driver needs a new cross-check.

## 3. Procedure on the TASL-2 runs tree (unchanged for TASL-7)

A chunk is claimed on TASL-2 for one host (`g5_tasl.py claim-chunk <spec> --node … --wave … --chunk … --host Ada-g0
--addendum <file>`), one open claim per host; the operator copies the claim and the wave's plan to the card's runs
tree; the job runs there (`g5_tasl.py run … --host Ada-g0 --chunk … --addendum <file> --addendum-note <note>`, behind
the signed G.5 note, both keys, and this note); every attempt is registered on TASL-2 in order (`register-chunk …
--addendum <file>`) before it counts for the meter, the STOP records, E5 and the seal; a claim the card cannot finish
is handed back by `abandon-claim`. After the card's last job its access log is registered a last time
(`finalize-remote --host Ada-g0`, a host some claim names); `seal-run` requires every host's final registration. The
card is sampled for other compute processes at three points (before the job, before the engine, after the engine; a
process that comes and goes between two samples is not seen): no job or engine starts beside one, and an attempt
during which one was seen is an infrastructure failure and is repeated, whatever it ended in (a baseline failure
included), except an isolation-gate STOP 2, a seed STOP 10 and the left-processes STOP 9 (R1-NO-TIMEOUT (2): a run's
budget decides a proposal only on an attempt that had its card to itself; the audit rows are sealed, so the whole
attempt is repeated; R1-CARD-SHARE (3)). The hours of every attempt count inside `cap_gpu_hours`.

## 4. Key lines (rendered from the addendum spec by `g5_tasl.py addendum-lines`)

The note carries `g5_note: docs/r1/authorizations/<the signed G.5 note>.md`, `addendum_spec_sha256: <sha256>` and the
lines below verbatim. Rendered here from a draft entry for one Ada card on the current (unsigned) G.5 spec, all
placeholders open; the published note is rendered again from the filled addendum spec.

```
g5_note: docs/r1/authorizations/c3_t1_labels_<YYYYMMDD>.md
g5_run_id: PENDING: c3_t1_labels_YYYYMMDD (the signed note's date)
g5_spec_sha256: 16b39b475e5ccccd9143de06b0a69996e5274d73033521d5cac8c1db0470627f
addendum_spec: sweep2/t1_tasl/g5_audit_hosts_addendum_<YYYYMMDD>.json
audit_hosts: TASL-7 (the signed note's tasl7_audits, unchanged); Ada-g0 (NVIDIA RTX 6000 Ada Generation)
audit_host_Ada_g0: ucrtasl PENDING: the card's nvidia-smi UUID NVIDIA RTX 6000 Ada Generation driver PENDING: driver_version; lease ~/r1_locks/ada_gpu0.lock (its own; free memory at least 24576 MiB, the card's other compute processes recorded, R1-CARD-SHARE); host check PENDING: docs/r1/reports/<dir>/ADA_ISOLATION_HOST_CHECK_<date>.md sha256 PENDING; G5-7 checkout /home/dowling/r1_tracks/t1_tasl/harness_g5; hardware class: another GPU model than the table's NVIDIA GeForce RTX 4090; no audit chunk runs here unless R1-G5-AUDIT-HOST-CLASS is on main naming NVIDIA RTX 6000 Ada Generation (R1-HOST-FREE (2)(a)); per node the short cross-check PASS against its sealed TASL-2 attempt under sweep2/t1_tasl/g5_audit_host_xc_ada_spec.json sha256 8470694f42c49ff3d0e0068da2f9ffeed86517689c47290822e2434f6cf8daf7 (measured on Ada's card PENDING: the card's nvidia-smi UUID (compute agent survey) and covering this card of the same host, GPU model and driver, driver PENDING: nvidia-smi driver_version (compute agent survey)): mlab_cifar10: PENDING (runs on the TASL pair only); mlab_imdb: PENDING (runs on the TASL pair only); mlab_ogbn_arxiv: PENDING (runs on the TASL pair only); mlgym_breakout_minatar: PENDING (runs on the TASL pair only); mlgym_cifar10: PENDING (runs on the TASL pair only); mlgym_fmnist: PENDING (runs on the TASL pair only); mlgym_houseprice: PENDING (runs on the TASL pair only)
addendum_cuda_ipc: The author accepts, for the G.5 audit chunks on Ada-g0 admitted by this addendum, the residual risk that harness-isolation host-check item 7 (CUDA IPC across the isolation boundary, reports/HARNESS_ISOLATION_20261117.md §3) is untested on these hosts, as for TASL-2 and TASL-7 in the signed note's cuda_ipc_acceptance line. Disclosed in the T1 report.
addendum_scope: G.5 audit chunks of the G5-7 family only (autoresearch_fixedtokens's audits stay on TASL-2); campaign waves, a wave's plan and its last chunk (E5) stay on TASL-2; a chunk is claimed on TASL-2 for one host, one open claim per host, and every attempt is registered on TASL-2 before it counts; its hours count inside cap_gpu_hours (R1-NO-TIMEOUT (3)); the card is sampled for other compute processes before the job, before the engine and after the engine: no job or engine starts beside one, and an attempt during which one was seen is an infrastructure failure and is repeated (R1-NO-TIMEOUT (2), R1-CARD-SHARE (3)); a process between two samples is not seen; a node without its PASS on main runs on the TASL pair only (R1-XC3-FAIL-READING)
addendum_spec_sha256: <the addendum spec's sha256>
```

Rows the strict check reads on main: R1-HOST-FREE, R1-G5-SIGNATURE, R1-CARD-SHARE; for a card of another GPU model also
R1-G5-AUDIT-HOST-CLASS at every admission, which must open with the lead sentence of the draft row in §5 naming that
GPU model.

## 5. The author's decision (AH-CLASS)

The candidate and the parent of one proposal are separate units of the wave's plan, and the plan's (unit × seed) runs
are cut into chunks without regard to proposals (`g5_job.chunk_plan`; under `reuse_parent_runs` a code state's runs
serve every role across the node's waves). A chunk on an Ada card therefore holds candidate runs whose parent runs ran
on a 4090, and the reverse. R1-HOST-FREE (2)(a) keeps "the candidate and incumbent audits of one proposal" on one
hardware class, and R1-G5-AUDIT-TWO-CARDS reads "one table, one GPU model (both RTX 4090)".

- **A (recommended): same GPU model only.** Addendum hosts are admitted for G.5 audit chunks only if they are RTX
  4090 cards; Ada is not a G.5 audit host. Built (the default: no row, no Ada chunk). Cost: none now; G.5 runs on the
  TASL pair (and any further 4090 lease). Why recommended: a node's short cross-check shows that its *default part*
  (the baseline and its n_edits declared edits) is bit-identical on the two models; the G.5 audits run arbitrary
  proposed diffs, and a diff that changes a tensor shape or a batch size can lead cuBLAS/cuDNN to pick a different
  kernel on a card with another SM count (RTX 6000 Ada: 142 SMs; RTX 4090: 128), so candidate and parent could differ
  in numerics exactly where (2)(a) asks them not to.
- **B: one hardware class per node by its cross-host PASS.** The row R1-G5-AUDIT-HOST-CLASS (text below) lets an Ada
  card take a node's audit chunks once that node's short cross-check PASS is on main. Built (the row switches it on;
  nothing else changes). Cost: the Ada cross-check run (≈ 2.9 GPU-h, 3.5 at the sensitivity ratio, cap 4.0) and its
  runner unit; the T1 report states per node which audit runs ran on which GPU model.
- **C: whole proposals on one class.** Plan chunks so that a proposal's candidate and parent runs (and every reuse of
  them) stay on one host. Not built: it changes the plan bytes and the chunking of the TASL pair, so it needs a
  re-issued G.5 note and a re-review of the plan code.

Draft row text (B):

> | R1-G5-AUDIT-HOST-CLASS | **For the G.5 audit chunks of a G5-7 node, a card of NVIDIA RTX 6000 Ada Generation is
> one hardware class with the RTX 4090 pair once the node has a cross-host PASS** (author, <date>). Reads R1-HOST-FREE
> (2)(a) for T1 G.5 audit chunks and amends R1-G5-AUDIT-TWO-CARDS's "one table, one GPU model" for them: the candidate
> and incumbent audits of one proposal may run on the two GPU models when the node's short cross-check (the default
> part, bit-identical to its sealed TASL-2 attempt, `g5_audit_host_xc_ada_spec.json`) is a cross-host PASS on main and
> an addendum note lists it. Campaign waves, plans, E5 chunks and autoresearch's audits stay on TASL-2. For the
> CPU-only mlgym_houseprice no GPU model enters: its audits on such a host run on that host's CPUs, and the row covers
> them on the same terms (its cross-host PASS on that host's CPU set). The T1 report states per node which audit runs
> ran on which GPU model or CPU (R1-HOST-FREE (4)); no analysis by GPU model is added. |

Draft row text (A):

> | R1-G5-AUDIT-HOSTS | **G.5 audit hosts beyond the TASL pair: RTX 4090 cards only** (author, <date>). The
> audit-hosts addendum of the G.5 note (`g5_audit_hosts.py`, reviewed unit `mac-g5-audit-hosts-20261127`) is adopted
> for cards of the table's GPU model; R1-G5-AUDIT-TWO-CARDS's "one table, one GPU model" stands; Ada's cards are not G.5
> audit hosts and the Ada short cross-check spec stays a draft. |
