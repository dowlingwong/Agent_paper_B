# D.3 G1/G6 launcher revision (revision 6) — one chunk script, HTCondor or direct SSH

**Status:** DESIGN ONLY, revision 6 (26 November 2026). No code, no job, no campaign, no audit, no data read.
This is the short design revision required by `compute/20261126-02` (with `cluster/20261126-02`) before G1/G6 code.
It changes only the launcher and hardware-record parts of
`docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_20261126.md` revision 5b
(sha256 `4b95798659c13feeef02af02504d68f138e40cdaf056ded0b89a09fbcc4e3a23`, ACCEPTED FOR CODE by
`docs/r1/reviews/D3_G1_G6_DESIGN_REVIEW_R6_20261126.md`). All scientific choices — arms, budgets, seeds,
snapshots, Y/Y(w), analysis, STOP classes — are unchanged.

## 1. Authority and scope

- R1-HOST-FREE (2)(c): all arms of one closed-loop instance are served by one GPU model; a campaign keeps its
  proposer on one GPU model from start to end.
- R1-CARD-SHARE: an empty card first; a shared card when the job's memory fits; an attempt lost to the card/host is
  sealed and repeated, never an outcome.
- `compute/20261126-02`: the campaign chunk logic lives in one script; HTCondor is one of two launchers, the other
  starts the same script over SSH under a lease on the host. The runner records host, GPU model and driver per
  chunk and refuses a chunk that would break either one-model rule.
- This revision does **not** change the G1/G6 design's pins, controller behaviour, snapshots, audit or analysis.
  It changes §2.1's "One HTCondor job" sentence and §2.1's per-chunk record; G6's CPU audit jobs use the same
  launcher-neutral manifest (with a CPU-set lease instead of a GPU lease).

## 2. One chunk script, two launchers

**One script.** `r1/c3/d3/campaign_chunk.py` (name for review; the G1 unit fixes it) is the only implementation of
the chunk: it validates pins and seeds, runs the 18-instance campaign, writes `chunk.json`, `campaigns/`,
`snapshots/`, `summary.json` and the SHA256SUMS tree, and applies the STOP/recovery rules. It takes a
`launch.json` and a new output directory; it knows nothing about HTCondor or SSH.

**Two launchers, same arguments.**
1. **HTCondor launcher** — `r1/c3/d3/launch_htcondor.py` generates one job per `(stage, node, arm, repetition)`
   chunk; `Cmd`/`Args` invoke the same `campaign_chunk.py` with the same `launch.json`. The scheduler request is
   the reviewed one for the measured pool model; no request is edited to get a slot.
2. **Direct SSH launcher** — `r1/c3/d3/launch_ssh.py` starts the same `campaign_chunk.py` on a host that has the
   card (or CPU set) and a free lease, under a delegated user scope (`systemd-run --user --scope`) or an
   equivalent `nohup`/`setsid` wrapper. It takes the lease (`~/r1_locks/gpu0.lock` on a GPU host; the host's
   CPU-set file on a CPU host), checks free memory rather than requiring an empty card (R1-CARD-SHARE), records
   the other compute processes at start and end (count and memory only), and writes the same
   `launch.json`/`chunk.json`.

The launcher choice is recorded, not inferred: `chunk.json.launcher ∈ {htcondor, ssh}`; the scientific record and
the analysis read the chunk files, not the launcher.

## 3. Hardware record and refusal rules

Every chunk's `launch.json` and `chunk.json` carry:

- `launcher`, `host` (hostname), `host_class` (the declared GPU/CPU class), `lease_path`;
- `gpu` (if any): `model`, `uuid`, `driver_version`, `memory_total_mib`, `memory_free_mib_at_start`, and the
  other compute processes at start and end (count, memory; no other user's command line or identity beyond the
  count/memory rule);
- `request` for the HTCondor launcher (exact scheduler request) and `scope` for the SSH launcher;
- `campaign_model` (the model declared for the instance/arm) and `model_check: PASS`;
- `chunk_start_utc`, `chunk_end_utc`, `status`.

**Refusal before execution (a STOP, no output directory):**
- a chunk whose detected GPU `model`/`uuid`/driver family is not the `campaign_model` declared for that instance;
- a chunk for another arm of an instance whose `campaign_model` differs (all arms of one instance share one model);
- a chunk whose proposer server record names another model than the campaign's `proposer_model` (the proposer is
  fixed for the campaign's whole life);
- a `launcher` that does not match the host/lease it claims, or a missing lease / a lease held by another job.

The same GPU model on a second host is allowed; the driver and host are recorded and disclosed. A different GPU
model is **not** a fallback: it is a refusal. Moving a campaign to another model needs a re-issued design/note
(R1-HOST-FREE (3)), not a launcher choice.

## 4. G6 audit jobs

The G6 audit jobs are CPU-only on deepthought under the existing §3.1 conditions. They use the same one-script
pattern: `audit_chunk.py` (or the G6 unit's script) validates the sealed snapshots and writes `audit/…` and
`Y_final.jsonl`/`Y_w.jsonl`; the launcher is either a direct deepthought process (the default) or an HTCondor CPU
job. The CPU-set/co-tenancy lease is recorded in the same `launch.json` fields; no GPU model rule applies to a CPU
audit, and no audit value enters a campaign run or controller.

## 5. Testing and review (before code)

- Unit tests: the hardware record and `model_check`; the four refusal cases; launcher parity (both launchers
  produce the same `launch.json`/`chunk.json` fields and the same `campaign_chunk.py` argv); a CPU-only
  ENGINEERING dry run with no GPU job and no evidence run.
- The G1 and G6 units each get their own tier-E review; the full `r1/tests` suite runs on base and tip with zero
  new failures. No campaign, audit, label or evaluation is run by this revision.

## 6. What this revision does not decide

The exact script names, the `launch.json` schema version, the HTCondor request values and the direct-launcher
wrapper are implementation details for the G1/G6 unit review, provided they keep the one-script/two-launchers
property and the refusal rules above. The measured model used for D.3 remains the reviewed note's model; this
revision does not choose a GPU model and does not make the H200 a prerequisite.
