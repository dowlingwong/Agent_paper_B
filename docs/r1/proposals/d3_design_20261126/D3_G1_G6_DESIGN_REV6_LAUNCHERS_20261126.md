# D.3 G1/G6 launcher revision (revision 6b) — one chunk script, HTCondor or direct SSH

**Status:** DESIGN ONLY, revision 6b (27 November 2026). No code, no job, no campaign, no audit, no data read.
This is the short design revision required by `compute/20261126-02` (with `cluster/20261126-02`) before G1/G6
code. It changes only the launcher, hardware-record and walltime parts of
`docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_20261126.md` revision 5b
(sha256 `4b95798659c13feeef02af02504d68f138e40cdaf056ded0b89a09fbcc4e3a23`, ACCEPTED FOR CODE by
`docs/r1/reviews/D3_G1_G6_DESIGN_REVIEW_R6_20261126.md`). Revision 6b answers the independent review
`docs/r1/reviews/D3_G1_G6_LAUNCHER_REV6_REVIEW_20261126.md` (CHANGES REQUIRED): the model refusal, the independent
model source, the shared-card walltime reconciliation and the "both stages" sentence are corrected. All scientific
choices — arms, budgets, seeds, snapshots, Y/Y(w), analysis, STOP classes otherwise — are unchanged.

## 1. Authority and scope

- R1-HOST-FREE (2)(c): all arms of one closed-loop instance are served by one GPU model; a campaign keeps its
  proposer on one GPU model from start to end. R1-HOST-FREE (2)(a) also keeps a paired/differenced comparison on
  one hardware class.
- R1-CARD-SHARE: an empty card first; a shared card when the job's memory fits; an attempt lost to the card/host is
  sealed and repeated, never an outcome and never a STOP.
- R1-NO-TIMEOUT: no wall-clock limit decides a check or an outcome; a job that shows no progress is ended and
  issued again as an infrastructure failure by its operator.
- `compute/20261126-02`: the campaign chunk logic lives in one script; HTCondor is one of two launchers, the other
  starts the same script over SSH under a lease on the host. The runner records host, GPU model and driver per
  chunk and refuses a chunk that would break either one-model rule.

**Explicit amendments to D5b.** This revision replaces D5b:13 ("One GPU model for both stages") with the two
R1-HOST-FREE (2)(c) rules and the paired-comparison rule below; it amends D5b:29's "One HTCondor job" to the
launcher-neutral sentence in §2; it withdraws the `chunk walltime` STOP of D5b §2.3/§3.3 for shared-card attempts
and makes the 1.5× time a descriptive planning value (see §4). No other line of D5b changes.

**The "both stages" question.** D.3a and D.3b for one instance are a paired comparison (D.3b's A3/A5 are compared
with D.3a's A2 on the same instances), so they use **one `instance_model` for that instance across both stages**;
this is R1-HOST-FREE (2)(a)/(c) applied, not a second hardware rule. Different instances may use different
campaign blocks only as the reviewed note declares; an arm's own campaign keeps its proposer model for its whole
life. This replaces D5b:13 rather than standing beside it.

## 2. One chunk script, two launchers

**One script.** `r1/c3/d3/campaign_chunk.py` (name for review; the G1 unit fixes it) is the only implementation of
the chunk: it validates pins and seeds, runs the 18-instance campaign, writes `chunk.json`, `campaigns/`,
`snapshots/`, `summary.json` and the SHA256SUMS tree, and applies the STOP/recovery rules. It takes a
`launch.json` and a new output directory; it knows nothing about HTCondor or SSH.

**Two launchers, same arguments.** D5b §2.1's replacement sentence is: *one chunk per launch; when HTCondor is the
launcher, one HTCondor job per `(stage, node, arm, repetition)` chunk; when SSH is the launcher, one process per
chunk on the leased host.*
1. **HTCondor launcher** — `r1/c3/d3/launch_htcondor.py` generates the job; `Cmd`/`Args` invoke the same
   `campaign_chunk.py` with the same `launch.json`. The scheduler request is the reviewed one; no request is edited
   to get a slot.
2. **Direct SSH launcher** — `r1/c3/d3/launch_ssh.py` starts the same `campaign_chunk.py` on a host that has the
   card (or CPU set) and a free lease, under a delegated user scope (`systemd-run --user --scope`) or an
   equivalent `nohup`/`setsid` wrapper. It takes the lease, checks free memory rather than requiring an empty card
   (R1-CARD-SHARE), records the other compute processes at start and end (count and memory only), and writes the
   same `launch.json`/`chunk.json`.

The launcher choice is recorded, not inferred: `chunk.json.launcher ∈ {htcondor, ssh, direct}` (`direct` is the
G6 deepthought CPU default; G1 uses `htcondor` or `ssh`). The two G1 launchers emit the same fields and invoke
the same argv; only `launcher`, `request`/`scope` and `lease_path` differ, and each launcher emits the
inapplicable field as `null`, never omitting it. The scientific record is `chunk.json`; the pinned analysis path
is unchanged: `chunk.json.launcher` is provenance only, the G7 builder may read the chunk records, and
`d3_analysis.py` still reads the `r1_d3_outcome/v1` table exactly as D5b §3.2 says.

## 3. Hardware record and refusal rules

The hardware fields below are **in addition to** D5b §2.1's `chunk.json` (pins, image, model sha, server flags,
walltime, status); nothing is replaced. Every chunk's `launch.json` and `chunk.json` carry:

- `stage`, `arm`, `instance_id`, `repetition`; `launcher`, `host`, `host_class`, `lease_path`;
- `campaign_model`, `campaign_model_source` (path + sha256 of the reviewed stage note/PD pin, or the campaign spec
  before the note), and `campaign_manifest_sha256` (the independent per-instance/campaign declaration below);
- `gpu` (if any): `model`, `uuid`, `driver_version`, `memory_total_mib`, `memory_free_mib_at_start`,
  `required_memory_mib`, `memory_check`, and the other compute processes at start and end (count, memory; no other
  user's command line or identity beyond the count/memory rule);
- `proposer_model_expected`, `proposer_model_observed` and `proposer_check`;
- `request` for the HTCondor launcher (exact scheduler request) and `scope` for the SSH launcher;
- `environment_freeze` (the pinned image digest/venv freeze and its preflight check; both launchers run the same
  check);
- `chunk_start_utc`, `chunk_end_utc`, `status`, `model_check`.

**Independent model source and the instance claim.** The authority is the reviewed stage note/PD pin (or, before
the note, the campaign spec), recorded as `campaign_model_source`; `launch.json` may not self-declare a different
model. Before the first chunk, the G1 unit writes one `campaign_manifest.json` under the run root with, per
instance, `instance_model` and the campaign's `proposer_model`, plus `campaign_model_source` sha256. It is written
once, locked, and its sha256 is in every `chunk.json`. The chunk compares the observed card with that manifest,
not with a value the chunk chose.

**Refusal before execution (a placement refusal, not a §10 STOP):**
- a chunk whose detected GPU `model` (the model identifier, e.g. "NVIDIA RTX 6000 Ada Generation") differs from
  the `campaign_model` in `campaign_model_source`/`campaign_manifest.json`;
- a chunk for an arm whose `instance_model` in the campaign manifest differs from the observed model (all arms of
  one instance share one model; the manifest is the race-free claim);
- a chunk whose observed `proposer_model` differs from the campaign manifest's `proposer_model` (the proposer is
  fixed for the campaign's whole life);
- a launcher/host/lease mismatch, a missing lease, or insufficient free memory (`memory_check` fail: wait or
  re-place; not a STOP).

**UUID, driver and host are recorded and disclosed, never compared to the model.** The same GPU model on a second
host, with another UUID or driver, is allowed for a chunk that fits; a different model is refused. If the reviewed
note fixes a driver family, that check is separate from the model check and is named by the note; otherwise a
driver change is disclosed only. A chunk refused for a model mismatch is re-placed; if the campaign has already
moved model (the instance claim no longer matches the declared source), that is a campaign-level STOP and no
outcome table is built from the partial design. A **lease held by another of our jobs** is waited out or re-placed
(an exclusive own-job lease, as the existing G1b/G.5 code uses); foreign processes may share the card when the
memory fits (R1-CARD-SHARE). The lease is per card actually used (`gpu<index>.lock` or a per-UUID lease; never a
fixed `gpu0.lock` on a multi-GPU host), and the UUID is recorded beside it.

## 4. Wall time, shared cards and the 1.5× value

D5b's `chunk walltime` STOP is **withdrawn** under R1-NO-TIMEOUT (1). The smoke's measured chunk time and its
1.5× are descriptive planning values used for scheduling and reporting, not a pass/fail line. An attempt that
shows no progress is ended by its operator and issued again as an infrastructure failure; an attempt lost to the
card or host (including a slow shared-card attempt, OOM or a kill) is sealed, recorded with the other compute
processes and their memory, and repeated in a new directory. No shared-card attempt and no wall-clock value
decides a result. This amends D5b §2.3's STOP list and §3.3's 1.5× sentence; the other §10 STOP classes are
unchanged.

## 5. G6 audit jobs

The G6 audit jobs are CPU-only on deepthought, after campaign seal, 16 workers, ≥10 of 40 cores free
(co-tenancy sampled), under the existing §3.1 conditions. They use the same one-script pattern:
`audit_chunk.py` (or the G6 unit's script) validates the sealed snapshots and writes `audit/…` and
`Y_final.jsonl`/`Y_w.jsonl`; the launcher is `direct` on deepthought (the default) or an HTCondor CPU job. A direct
process is attempt-recorded and sealed like a job (its stdout/stderr, host, start/end and exit are kept). The
deepthought record carries `host`, `workers: 16`, `cores_free_at_start` and `lease_path: null`; deepthought has no
TASL-style CPU lock file and none is invented. No GPU model rule applies to a CPU audit, and no audit value enters
a campaign run or controller.

## 6. Testing and review (before code)

- Unit tests: the hardware record and `model_check`; the refusal cases (detected model vs independent source;
  instance claim across arms; proposer model; lease/memory); launcher parity (both G1 launchers produce the same
  `launch.json`/`chunk.json` fields, the same `campaign_chunk.py` argv, and contain no duplicated chunk logic); the
  HTCondor request is not rewritten; the other-process record contains count/memory only; the G6 `direct` launcher
  record.
- A CPU-only ENGINEERING dry run, clearly labelled `ENGINEERING_ONLY`, with no GPU job and no evidence run.
- The G1 and G6 units each get their own tier-E review; the full `r1/tests` suite runs on base and tip with zero
  new failures (listed by test id). No campaign, audit, label or evaluation is run by this revision.

## 7. What this revision does not decide

The exact script names, the `launch.json` schema version, the HTCondor request values and the direct-launcher
wrapper are implementation details for the G1/G6 unit review, provided they keep the one-script/two-launchers
property, the independent model source and the refusal rules above. The measured model used for D.3 remains the
reviewed note's model; this revision does not choose a GPU model and does not make the H200 a prerequisite. The R6R
non-blocking notes on §3.2 refusal wording and revision labels remain unit-level/editorial and are not settled here.
