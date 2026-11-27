# local/20261127-29 — G.5 expansion addendum drafts and switch STOP

for: coordinator

**Result.** Four addendum drafts prepared with `approved: false` from the four published expansion G.1b PASS
records. The launch switch and completed addenda remain pending. Base `cbc86fc5b628ed328b1889f42e7b4e0235c004f3`.
Draft branch `mac-g5-expansion-addenda-20261127` @ `cc4da5b2ebdddd48168684840699869b5af32cb4`, reviewed drafts
`e18106d881ec172daae8dde49ce5bf2eae8910ec`. This advances the draft portion of `local/20261126-12`.

| Draft under `docs/r1/proposals/` | SHA-256 |
|---|---|
| `G5_EXPANSION_ADDENDUM_GC7RC_ETTH1_DRAFT_20261127.md` | `870057740e56b6bcd866b37690352f30ad527be73b9206b85dce170ab9d03176` |
| `G5_EXPANSION_ADDENDUM_GC7RC_FORESTCOVER_DRAFT_20261127.md` | `0cc3e5690540e79505032ac36cb116935443b2ce7118f174794fb24c20580165` |
| `G5_EXPANSION_ADDENDUM_MLGYM_METAMAZE_DRAFT_20261127.md` | `7e5fd728082dee9347da0985dffbe72664616afda2c82435536e125a40dc8f12` |
| `G5_EXPANSION_ADDENDUM_MLGYM_TITANIC_DRAFT_20261127.md` | `494cc7c05f353487ca26233264a5a6cb95a8e4f62032ee6b2302b9ea64ac7577` |

**Checks.** 4/4 committed draft checks passed for exact published citation bytes, the node and run in each sealed
receipt, determinism, G.1b layout, pending bindings and S9 split routing. `git diff --check` passed. Four scratch
harness merges of the reviewed G5-7 implementation `cbf7a0030d73fbc73e2735a6b0e33f25ddf04a98` onto the four
G.1b kit pins passed the existing `measurement_path_check` and `check_engines` on each merge. These checks do not
exercise the CPU-only launcher. The branch changes Markdown only, so no full-suite comparator was run for this
packet. Independent tier-E re-check **ACCEPTED for draft handoff**. Review `docs/r1/reviews/G5_EXPANSION_ADDENDA_DRAFT_REVIEW_20261127.md`
SHA-256 `892a159eadc3990e3ac9a7ca9648f0d6d68b09f8bec4de5592171fdb8bd8d182`.

**STOP at launch and release binding.** The existing switch validates a fixed eight-node spec with split v1 and
its G5-7/G5-AR families. The release check refuses a v2 evidence binding until the PRE-SPLIT amendment is published.
The main G.5 render still needs its `paper.commit`, combined accepted P11 and final checks. Its exact shared
launch-code binding with the addenda must be settled before it pins the code. A second spec introduced after
that pin must satisfy the reviewed `verify_launch_tasl` tree comparison as well as its own note's digest.

The four candidate engine merges pass desk P5. At the kit pins, the G.5 engine's existing CPU allowlist admits
Titanic and refuses MetaMaze, ETTh1 and Forest Cover without the separately reviewed census-override handling
their G.1b used. Each spec entry also needs a dedicated reviewed G.5 deployment and placement covering the CPU set,
its lease and its census environment. `g5_job` and `g5_seal` bind server records and receipts to an exact spec/run,
and the assembly reads the seven-node or autoresearch noise binding. The integration needs an explicit reviewed
spec/run binding for the added jobs and receipts, MLGym release integration under split v2, and separate 1GC
outputs. Preserve the same K, campaign settings, run budget, host checks and release locks. A complete code unit
needs end-to-end synthetic refusals and routing checks, the full-suite comparison and independent tier-E acceptance.

**Next.** Coordinator routes the shared launch binding with the main G.5 render and publishes the exact PRE-SPLIT
amendment after its checks. Compute supplies the D6 noise-floor copy in the separate `for: compute` handoff.
Then finish and review the switch, four per-node entries and P10 tail-law bindings before any G.5 label assembly.
Each final addendum needs its own accepted fill and strict check after the main G.5 note is published. The S9 eligibility
of all four nodes is already established by the accepted and published expansion G.1b result.

Decided alone: filled only the published G.1b and split citations and tested four scratch harness merges. The
assigned worktree was used to write the drafts. Temporary writable Git metadata was used for the branch and fetch
because the linked worktree's Git metadata is read-only. No label or evaluation partition was opened. No host job
was submitted.

## Queue and recorded jobs

After refetching `coord/coordinator` at `287c7c0367c114d50fc3ab85706952ae548bb6f1` and `coord/compute` at
`17a20d28dc2e2b2857fbb634b42f54bbfd417ae8`, Local is idle. No further Local card is runnable. The statuses
below come from the published job receipts and queue.

- **G.1b complete elsewhere.** `compute/20261126-10`, run `g1b-x-tasl-20261126-a`. Titanic PID `106578`
  finished and sealed at 18:31:03 UTC. All four seals and determinism PASS are on `main` `cbc86fc5`.
  The D6 copy handoff uses this finished run.
- **Screening retry pending on Compute.** `compute/20261127-35` preserves `SMEAS_EVIDENCE_20261127T1550Z`
  (186/10,164 written, zero failed, tmux `smeas_reissue2`) and requires a fresh stamp under the same signed note
  and strict 10-free-core preflight. The old manifest is SHA-256
  `39575f58bf0a2d824b6f2e75bab2075230b03e653396bd0e9c73d5dada05c2c9`. Check for the fresh receipt. D.3 step (8)
  and campaigns wait for the screening disposition.
- **Houseprice and Ada P5 queued after screening.** `compute/20261127-33` uses the exact command in
  [the `for: compute` handoff](20261127-27-houseprice-two-attempts.md#compute-handoff), delivered in `63cd96e1`.
  The accepted code and full-suite comparison are recorded there. S14 still requires three sealed attempts on
  CPUs 0-7, bit-identical to the reference and within 9.486 s per run. The preserved old run is
  `tasl2-cpuset-mlgym_houseprice-20261127`, with two seals. Check for new houseprice and Ada P5 job IDs and leases.
  The prior Ada P5 refusal happened before GPU work. P.4 phase 1 awaits accepted P5 records and the published note.
- **D.3 G6 under coordinator test.** `compute/20261127-31` source `345f4c97`, review `6eadf655`, ACCEPTED.
  The remaining G.5 P11 TASL-2 items are `compute/20261127-32`. Base G.5 render `local/20261126-08` waits for
  combined P11, exact `paper.commit`, draft check and final independent review. The addenda and shared-card
  repeat and extra audit-host work wait on their recorded dependencies.
- **Idle or blocked on Compute.** D.3 batch preflight IDs `760148`, `760149` and `760152` and old P.4 H200 ID
  `760065` were removed unmatched. Check for a newly eligible D.3 L40S or A100. Paper C E-INT `compute/20261127-28`
  needs Ada staging and a separate eligible-card smoke under Paper B priority. No E-INT job ID is recorded.
  The Paper C CPU measurements await operator pins and signed notes.
