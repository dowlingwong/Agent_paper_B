# Attempt 2 design — streaming classification with a deployment-contract audit

Status: **PROPOSED, UNSEALED, NOT IMPLEMENTED OR RUN**. Prepared 8 October
2026 for D-ATT2. This is the second and last bounded task attempt under P-B1.
D-ATT2 is NOT APPROVED as a complete design. The author adopted the end-of-run R4, behaviour changes, never-as-control (144 leaves), symmetry-aware metric, information surfaces and CPU caps, subject to the revisions below and another pre-seal inspection. The supplied 7/8 reach is a recorded pre-seal fact; no utility or RNG-stream outcome has been produced. Mechanisms and constants are specified for review;
no generator, seed search, candidate run or outcome-producing code has run.

## 📋 Question, unit and unchanged science

Can a competent executor benefit from auditing its candidate's deployed input
contract, and does auditing early versus after a new batch offer a genuine
information-versus-delay tradeoff? Each original root has one shared prefix,
then paired now/later/never tails in each of two repetitions. Families, not roots or
repetitions, are the independent units. U remains final valid-candidate
hidden-test accuracy in [0,1]; invalid/no candidate is 0 with a reason, and
collection failure is an integrity status. q=.25, the existing controllers,
shared allocator, estimands, replay sensitivity and 512-leaf evidence cap remain
unchanged. This document proposes a new task law and bounded task horizon;
D-ATT2 must adopt those before any implementation. It does not bind a contract
or authorize an Ada/model/evidence run.

This is an explicitly constructed integration task, not an organic production
workload. Passing CPU realism would qualify only this task/verifier setup;
it would not establish the paper's hypothesis or general application realism.

## 🔍 Diagnosis from attempt 1, without rerunning it

The retained report says: "R1 and R4 fail for the *typical* behaviour"
(`docs/paper_split/TASK_REALISM_REPORT.md`, Verdict and Run 2). Its recorded
now/later/never counts are 0/5/3 and best verification gain is −0.04 U.

`cc_live_candidate.py:66–69` fits another stump on the diagnostic part and
replaces the original only on strict visible improvement. This diagnostic
uses ordinary visible rows: `cc_live_realism.py:94–103` re-splits those same
rows, while `:121–128` compares against an ordinary refit on all dev1 rows.
Thus the verifier adds a different finite-sample split/search, not a new
information source unavailable to a competent refit. That interpretation
explains a redundancy mechanism; it does not infer unobserved outcomes.

`cc_live_task.py:57–59` delivers dev2 on continuing. New data can improve a
late fit; the old code does not establish a separately measured deadline cost
of postponing the diagnostic. `cc_live_generator.py:33–34` alternates two
bundled tables; distinct family IDs do not establish independent underlying
tasks or near-duplicate separation. These facts motivate new information and
an actual shared work horizon, not tuning old parameters or adding winner
families. Attempt 1's code/results stay unchanged from the post-D-INFRA-RB
baseline `b09c85a`; that prior author-approved docstring change is not a
mechanism change.

## ⚙️ Diagnostic mechanism and ordinary-refit control

An executor fits a binary linear classifier on labeled tabular batches. The
candidate consists of an executable feature decoder, weights and intercept.
The deployment service has a versioned signed feature-permutation map. Mismatch and migration classes are assigned before generation for the balanced development-screen law; the separate pilot law is an explicitly artificial independent random mixture. Neither assignment uses behaviour, policy or utility. Ordinary
refitting can learn a classifier from the visible data, including fitting on
the latest raw batch alone; the task is therefore solvable without verification.

The verifier runs **input-contract probes** in a separate deployment sandbox:
paired canonical/serialized inputs with known feature semantics, plus a
separate labeled diagnostic split. Neither is the hidden test. Its output is
current feature-map correspondence, current-versus-reconciled diagnostic
accuracy and an executable reconciled candidate. It never returns the teacher,
family parameters, future schema version, hidden rows/labels or hidden U.
The paired correspondence cannot be recovered just by rerunning a fit on
unpaired visible training batches. Visible labels and a latest-raw fit may allow useful adaptation;
that possibility is part of the never/refit control, not forbidden.

Response is frozen for both checkpoints: evaluate current candidate and one
reconciled alternative; accept the alternative only if its diagnostic accuracy
is strictly higher; otherwise retain the current candidate. The reconciled
alternative first converts weights from their recorded fitting schema to canonical order, then sets the decoder to the inverse current map and performs one
bounded optimizer update using visible fitting rows only. Verifier-owned
labeled diagnostics are used for selection, never gradient fitting. The tool
returns the exact executable candidate it evaluated. The task does not reuse
attempt 1's stump implementation or assert that its response mechanism passed.

The R4 ordinary-refit control gets the same candidate class, total work slots,
all visible rows and ordinary development diagnostics; it may choose either
pooled batches using its available decoder or the latest batch alone, using
visible diagnostic accuracy only. It receives no deployment sandbox probes.
No intentionally crippled fitter is used as the competent control. R4 compares
this control with the otherwise identical candidate plus verification at c1,
including verification's work debit, graded on the same held-out rows.

## ⏱️ Waiting information and an actual deadline

After c1 every tail has **eight work slots** until one fixed release deadline.
One ordinary action evaluates one updated alternative and uses one slot; it does not fit two alternatives for one slot. Verification plus its frozen response
uses two slots, early or late; the fit portion of the response is included,
not free extra training. All tool work is separately counted. The first four
slots precede c2, and the final four follow c2. No utility penalty is subtracted
for time: the final candidate is actually the one reached within these slots.

At c2 a new labeled batch arrives in the current deployment schema. A possible
schema migration happens at that boundary, independently of the initial
mismatch. Verification at c1 describes only the version current then; its
cached map is not magically updated. Verification at c2 can learn the current
map and test the inherited candidate in the new deployment schema; the response can train one alternative on the newly visible batch before selection. Early verification can
prevent fitting later batches with a wrong decoder; late verification can
catch a migration absent at c1, but has fewer remaining updates to recover
from earlier post-c1 fitting on mismatched pooled coordinates. An independent raw dev1 arrives at c1 after a canonical dev0 prefix, so such gradients can occur before c2. When there is no
integration problem, spending two slots on an audit can waste optimization
work and diagnostic selection can overfit. These are mechanisms allowing
possible now/later/never winners, **not guarantees or family assignments**.

The eight-slot clock is identical across tails. The checkpoint trigger is
completion of slot four, without looking at outcomes. Reaching c2 uses the
same outcome-blind hash gate as attempt 1 (nominal .70). The author reports that fixed IDs a2-r0…a2-r7 reach in 7/8 cases (.875); this fact is recorded in the pre-seal package without choosing new IDs. Unreached roots
remain under their registered fallback. For such roots, no new batch/migration
is revealed; the final four slots continue on the original visible batch.
The supplied .875 reach lies within R7’s [.5,.9] interval; this is a known pre-seal property, not evidence from the realism run. Execution still records reach and early termination, and never resamples IDs.

## 🧮 Fully specified pre-run law and behaviours

The implementation must follow this law exactly; any unresolved ambiguity is
reported before the author approves/seals it. No outcome-based choices remain.

| Component | Proposed fixed law |
|---|---|
| RNG | NumPy PCG64; SeedSequence entropy `[20261008, partition_index, family_index, root_index, stream_index]`; indices stored in a manifest, never outcome-selected |
| Dimensions | 8 continuous features; no reused public dataset or shared rows |
| Family covariance | Draw an 8×8 standard-normal matrix, QR with positive diagonal convention; eigenvalues drawn independently Uniform(.5,1.5); covariance Q diag(eigenvalues) Qᵀ |
| Teacher | Independent standard-normal coefficient vector normalized to unit length; intercept 0; binary label is sign(wᵀx), flipped independently with probability .20 |
| Rows | Each root: dev0 80, dev1 80, dev2 80, audit1 80, audit2 80, hidden 500; independent draws within its family; fixed row IDs identify every split |
| Feature names | Eight neutral field names; numerical family descriptor and data define distinctness, not cosmetic renaming |
| Initial map | Screen: class from fixed family-index rule; pilot: identity with probability .65, otherwise uniform nonidentity signed permutation. Realism balancing choice remains pending. Final law frozen separately before any final test generation/outcome |
| Migration | Screen: fixed family class; pilot: independent Bernoulli(.35). When migration is present draw a new signed permutation, rejecting only equality to old map; final law remains a separate freeze |
| Training coordinates | dev0 canonical; dev1 serialized using the initial map, revealed at c1 after prefix; dev2 serialized using the current map; audit inputs serialize using their checkpoint's map; hidden serializes using the final actual map |
| Candidate initial state | weight_schema_version=canonical, identity decoder, zero weights/intercept; prefix uses four ordinary updates on canonical dev0; all tails inherit this exact candidate/workspace/session prefix |
| Optimizer | Logistic cross-entropy SGD, learning rate .10, L2 penalty .001, batch size 16, no momentum; sigmoid inputs clipped to [-30,30]; float64; per-action keyed minibatch selection |
| Ordinary fit selection | Alternate one pooled and one latest-only alternative, one gradient/evaluation per slot; exact transforms, incumbent selection and minibatch keys are specified below |
| Verifier probes | 16 probes, +e_j and −e_j for j=1…8, encoded by current map; return correspondence, not teacher or future state; audit uses the separate 80-row checkpoint diagnostic split |
| Checkpoint reach | `_reached(root_id,.70)` as in attempt 1; root IDs `a2-r0`…`a2-r7` for the eight CPU-realism roots; no changed IDs after observing reach |
| Response acceptance | Strict diagnostic improvement; tie retains incumbent; exactly one verifier invocation per verified tail |
| Grading | Round-trip executable candidate JSON, then final deployment-map predictions on 500 hidden rows; mean accuracy; collection failure kept distinct |

Behaviour names and qualitative coverage remain careless / typical / careful.
Each uses the same task law, slot clock, class and verifier. Careless updates
only the first four model-coordinate positions and uses the first .60 of each
batch for fitting; typical uses all eight and .80; careful uses all eight and
.90. These fractions/feature restrictions preserve attempt 1's documented
behaviour distinctions. Candidate-search counts 2/16/32 from stump fitting
are not carried to SGD: the declared eight post-c1 slots replace that
candidate-search control, with no mechanism-specific hand-authored strategy.
Each verifies when the regime requires it and submits its retained visible candidate at the fixed deadline. Repetition seeds differ only within-root
optimizer row order. The author adopted this behavioural-interface change as a D-ATT2 subitem; complete design approval and contract binding remain pending.

The competent R4 control uses all eight features and .80 fitting fraction,
identical fitting alternatives and slot budget to typical. It can select
latest-only rather than blindly pooling incompatible batches. Its permitted
input information is fixed here and cannot be weakened to make R4 pass.

## 🗂️ Families, partitions and leakage audit

Reserve exactly **88 disjoint family IDs**: 48 development, 32 test,
8 posttrain. The development cohorts are disjoint: **0–7 realism, 8–15 screen,
16–47 pilot**. Screen uses eight families × two roots × two repetitions ×
three regimes = 96 leaves; pilot uses 32 families with the same per-family
counts = 384 leaves. Neither consumes test families. Test families 0–31 are
held out for final collection; its complete final law must be frozen and
committed before any final test family generation, fitting or final outcome.
Posttrain remains separately authorized and does not consume either cohort.

The screen is balanced over four initial-mismatch × migration classes,
**two families per class**. For development family f in 8…15 let k=(f−8) mod 4:
0=(no mismatch,no migration), 1=(no mismatch,migration),
2=(mismatch,no migration), 3=(mismatch,migration). All roots in a screen family
inherit its class. For mismatch=false use identity; for mismatch=true draw
nonidentity M1 from stream 21. For migration=false use M2=M1; for migration=true
draw M2 unequal to M1 from stream 23. No Bernoulli gates 20/22 are drawn for
screen. Assignment precedes generation and does not guarantee regime winners.
Screen reports conditional operability/cost by class; it does not estimate
the prevalence or value of the pilot mixture.

The pilot keeps the original independent random mixture: initial mismatch
Bernoulli(.35), migration Bernoulli(.35), per root, with no class balancing,
selection or redraw. Label this **artificial mixture**, not naturally observed
class prevalence. Realism families 0–7: **balanced/random choice pending the
author’s bracketed adopt/decline answer**. If balanced is adopted, use k=f mod 4
with the same mapping (two families each); if declined, retain the pilot’s
random artificial mixture. No law is silently chosen while this answer is open.

After the eventual seal, generate development families under the approved
cohort laws once. Do not evaluate RNG streams **20–23 before the seal**, for
any cohort or purpose. Final test and posttrain data remain ungenerated until
their respective approved freezes. Apply distinctness/leakage audits to each
new cohort and all previously generated cohorts; a failure stops without
redrawing. Development fitting uses only the development cohorts permitted
by the phase protocol; test/posttrain families and descendants stay excluded.
The final law is an explicit later author freeze, not an implementer choice
made after seeing final outcomes.

Family law descriptors comprise normalized teacher coefficients and covariance.
For two families define distance as the maximum of teacher Euclidean distance
(divided by 2) and covariance Frobenius distance (divided by the larger
Frobenius norm). **Near duplicate: distance < .10**, ignoring IDs/seeds/names.
Compare every pair, including within partitions; no redraws to cure a failure.
The row audit additionally rejects any repeated numeric row+label digest across
partitions. Histories are checked for duplicate content after removing IDs,
paths and the invariant task/tool boilerplate; tokenize numbers to their
recorded 6-decimal representation and nonnumeric text to lowercase words,
then use 5-token-shingle Jaccard ≥ .90 as the near-duplicate threshold. Report
same-partition and cross-partition matches separately; a cross-partition match
stops the leakage audit and does not trigger another family draw. This history
audit uses recorded visible content, not hidden outcomes or family names.

Potentially symmetric laws are not made distinct just by random seeds: the
numerical distance is only a proposed observable-law screen, not a proof of
independence or semantic diversity. The single independent challenge identified a symmetry defect in this raw metric. The symmetry-aware replacement below controls the final draft; the raw distance is reported only as an ancillary diagnostic.
The executor/controller/recorder allowlists below govern visibility. H₂ keeps H₁; host teacher, future maps and hidden outcomes never enter decision inputs.

## 🧾 Ground truth and restoration surface

Record per root: family law digest, split-row digests, initial/final map digests,
initial-mismatch flag, migration flag, seeded reach flag, slots used, verifier
calls, candidate before/after digests, response decision, session/workspace
lineage, repetition seed and invalid/integrity reasons. These state fields are
sealed recorder metadata, not decision-visible features. No posttraining state
labels are used in this attempt; adding a label map is a later author decision.

The task object keeps all hidden rows, teacher and future-map draws outside
agent workspaces. Verifier-owned probes/diagnostics live in a different object
and never import/access the hidden test. Forks restore candidate/optimizer
state, visible batches, clock, decoder cache and per-root tool counters exactly.
The raw task seed and future map never appear in the system prompt or visible history. Current correspondence is permitted in executor history only after an audit, as specified below. The evaluator grades only after a terminal candidate is frozen.

## ✅ R1–R9, unchanged thresholds and real caps

| Check | Frozen pass rule / implementation |
|---|---|
| R1 | Each now/later/never best in ≥1 family for each behaviour; use attempt-1 tie convention verbatim, report tie counts alongside winners; no winner-conditioned sampling |
| R2 | Between-family SD(later−never) > .02 for each behaviour |
| R3 | Row partitions disjoint, hidden rows absent from all workspaces/probes/tool outputs; audit actual files/objects, not a constant True |
| R4 | Typical verify at c1 exceeds the competent ordinary-refit control by > .02 U in ≥1 family; also report all behavioural controls and paired differences, no selected-only mean |
| R5 | Verification lowers U in ≥1 family for each behaviour |
| R6 | Typical never mean in [.2,.8], root SD > .05 (population SD, as attempt 1) |
| R7 | Typical c2 reach in [.5,.9], early termination < .5; measured over all original roots |
| R8 | 512 leaves × 1350 tokens = 691200 ≤ 2M; 512 × 12 s = 6144 s ≤ 10 h, retained planning arithmetic only. CPU-realism must also fit the CPU caps below; real GPU/model costs remain unmeasured and must be qualified before launch |
| R9 | Fit/verifier return the exact executable candidate; submit round-trip and rejection tests, no candidate description substituted for execution |

R4's new sandbox information and SGD candidate differ from attempt 1; the
**.02 threshold is not changed**. R3/R9 are now executed integrity tests rather
than assumed booleans. R8 retains the old token/time planning assumptions,
explicitly labeled as such; it cannot certify live model cost. A proposal to
change any threshold requires an author amendment before the seal, justified
from its purpose, never from the failed attempt's numbers.

## 🔒 Budget, one run and failure disposition

CPU realism: eight families × one root × two repetitions × three regimes ×
three behaviours = at most **144 terminal leaves**, with the existing never tails reused as all three behavioural ordinary-refit controls = **144**, below 512. No model/token/GPU call. Stop at
30 minutes aggregate CPU-run wall time, 1 GiB retained outputs, or an integrity
failure, whichever comes first. Use one process, at most four CPU threads.
A interrupted/partial run remains recorded; no scientific second run is started.
Execution-bug corrections preserve partial evidence and resume only unfinished
immutable units after a recorded explanation; no repaired unit replaces a
scientific failure or already completed leaf.

RNG law, parameters, draw order, family/row manifests, behaviours, slot costs,
thresholds, grading, command and failure policy are sealed before outcome code.
Any structural/leakage preflight failure after the seal stops for the author;
no generator rejection/resampling is added except the explicitly declared
identity/equality rejection for signed permutations. One independent challenge
is used before sealing. No substantive mechanism or threshold repair is allowed
after outcomes: **execution-bug fixes only**, adopted by the author. An
execution bug is a **test-demonstrable mismatch between code and sealed text**.
Every fix must cite the exact sealed provision and a failing-before/passing-after
test, preserve completed evidence and receive a dated record. Disappointing
outcomes, low power or a mechanism working as specified are not execution bugs.
The general one-repair field never permits substantive tuning of this attempt.

P-B1, verbatim from OPEN_ITEMS §B1:

> failure disposition (adopted P-B1): if attempt 2 fails substantive
> realism criteria, stop this task/verifier setup and drop its ICML 2027
> route. Execution bugs may be fixed transparently; mechanisms and thresholds
> are not tuned against the result.

## Pre-seal resolution of the single challenge (binding proposed details)

This revision answers B1–B3, M1–M2 and N1–N2 in
`docs/paper_split/ATTEMPT2_CHALLENGE_20261008.md`. The original challenge verdict
is preserved. These details supersede any shorter table wording above. The author’s revision decisions below supersede the earlier proposals. The complete design remains unapproved and unsealed; adopted subitems do not authorize implementation or execution.

### B1/B2: coordinates, executable response and slot schedule

For canonical column x, schema v serializes z=M_v x. A candidate stores
`weight_schema_version` B, decoder D, weights w and intercept b; deployment
prediction is `1{wᵀDz+b >= 0}`. B is the coefficient coordinate basis:
canonical has M_B=I, raw schema v has M_B=M_v. Each fit also records its batch
schema versions and conversion assumptions. This separates the coefficient
basis from possibly incorrect ordinary conversion guesses; mixed provenance
is not silently labelled an audited fit.

Candidates begin in canonical basis. A latest-raw fit records the **actual
visible batch version v** as B=v, even if the executor does not know M_v.
The candidate does not contain the protected true map. The independent audit
sandbox can resolve a recorded historical schema version from its versioned
registry for conversion; this is internal audit input, never ordinary-fit input
or an extra visible disclosure. Future maps and hidden outcomes remain forbidden.

For canonical dev0, fitting in basis B uses `estimated_M_B x`; for raw batch
version v it uses `estimated_M_B estimated_M_vᵀ z`. Before any audit, estimates are identity. After an audit, use a version’s disclosed cached map when available; for an unprobed version use the most recently disclosed map as an explicitly stale guess. No true registry lookup is allowed to ordinary fitting. Both ordinary control and verified executor have the same conversion
code; only authorized audit information differs. Visible checks follow the
same batch conversion. The coefficient-basis tag remains B on pooled updates,
even if a recorded conversion guess is wrong. The tag records the intended
feature basis, not a claim that all gradients were in true canonical order.

The prefix fits canonical dev0. After the shared prefix is frozen, independent
raw dev1 is released at c1. This addition is proposed to resolve the challenge's
correct observation that canonical-only pre-c2 gradients cannot be corrupted
by a deployment mismatch. At c2 reached roots receive raw dev2 and the new
map becomes active before the decision; the inherited candidate is not claimed
to have trained on dev2. Unreached roots receive no dev2 and retain M1.

Each ordinary action creates one alternative from the incumbent. Odd actions
use pooled mode: keep B,w,b and fit one minibatch from all visible fitting
rows with the conversions above. Even actions use latest mode: for latest
raw version v set B'=v, D'=I and w'=Dᵀw, b'=b; these weights are now explicitly
in that raw version’s basis. This preserves current deployment predictions for
typical/careful. Careless truncates model coordinates 4–7 to zero after the
rebase and uses the same restriction in fitting and selection. Prefix latest
mode uses canonical dev0 and leaves B=canonical, D=I. The pooled/latest counter
counts ordinary actions only, continues across c2 and is restored at forks.
After each action compare alternative and incumbent on the fixed held-out
fraction of the newest visible batch; strict improvement adopts, ties retain.
On a pooled action set D to estimated_M_B estimated_M_currentᵀ, using the same recorded guesses as its current raw-batch conversion; a new unaudited version uses the explicitly stale guess, never a hidden map. Every adopted alternative retains its B, D, cached map versions, fit-provenance
record and batch version. No fitting on check rows or hidden selection occurs.
At an unaudited migration the incumbent D remains stale; a latest-mode raw fit
can adapt in the new raw basis without recovering canonical correspondence.

One work slot is one minibatch gradient plus selection on the latest visible
check rows. It is a constructed action-cost unit, not a measured elapsed time.
A minibatch contains 16 fitting rows, selected without replacement if at least
16 exist; otherwise all rows are used, with average gradient. For logit
v=wᵀu+b, gradient is `(sigmoid(clip(v,-30,30))-y)u + .001w` and the intercept
uses the corresponding mean residual without L2. Every ordinary action costs
one slot even on rejection; all its fitting/selection work is recorded.

The verifier first obtains 16 basis probes and the checkpoint audit split.
It constructs exactly one alternative by first resolving the candidate’s
recorded basis B and converting **w_canonical=M_Bᵀw**, b unchanged. For B=canonical
this is the identity conversion. Only then set B'=canonical and
**D'=M_currentᵀ**, and perform the declared one pooled minibatch update in
canonical order using visible fitting rows only. The source schema tag, internal
registry lookup version and conversion digest are recorded host-side. Unknown
or inconsistent schema tags are an integrity refusal, not a guess.

Without the gradient, the conversion preserves the semantic canonical
classifier `wᵀM_B x`, then evaluates it in the current deployment schema;
it does not reinterpret raw-trained weights as canonical weights. This works
both for an unchanged schema and migration from the weights’ fitting version
to the current version. The ordinary candidate remains untouched if selection
rejects the response. Compare alternative and incumbent on the 80 current
audit rows; strict improvement adopts, ties retain the exact incumbent with
its original tag/decoder. Careless’s four-coordinate restriction applies after
canonical conversion and is recorded; typical/careful use all eight. Response
conversion and schema metadata must round-trip with the executable candidate.

The full probe/diagnostic response occupies two slots including its one
gradient. The same two-slot tariff holds even if the response is rejected.

| Tail | Prefix/c1 | Slots 1–4 | c2 boundary | Slots 5–8 |
|---|---|---|---|---|
| now | Four ordinary dev0 actions; release dev1; audit starts | Audit occupies 1–2; ordinary actions occupy 3–4 | Release dev2/current map iff reached; no second audit | Four ordinary actions |
| reached later | Same prefix and dev1 | Four ordinary actions | Release dev2/current map; audit starts on inherited candidate | Audit occupies 5–6; ordinary actions occupy 7–8 |
| unreached later | Same prefix and dev1 | Four ordinary actions | No dev2/migration/audit, calls=0 | Four ordinary actions on existing batches |
| never/control | Same prefix and dev1 | Four ordinary actions | Release dev2/current map iff reached | Four ordinary actions, calls=0 |

Every tail submits only at slot eight. No scripted behaviour terminates early;
early termination means a recorded terminal event before the c2 boundary,
not the outcome-blind nonreach gate. Invalid/no executable candidates receive
U=0 with reason; integrity failures abort and do not supply a numerical leaf.
Now can prevent incompatible raw dev1 gradients; later observes schema
migration but follows four ordinary actions with its old decoder. This is a
mechanistic work-budget tradeoff; it does not guarantee a winner or a PASS.
Never and the competent R4 control are the **same leaf**, with the same rows,
optimizer/action stream and candidate class. All behavioural controls reuse
their already collected never leaves. No additional control collection exists.

### B3: sampling namespace, pairing and invocation

All features follow x=Q diag(sqrt(lambda))g, g~N(0,I8), float64; mean is zero.
Q comes from NumPy QR of independent standard normals with its columns
multiplied by sign(diag(R)), sign(0)=+1. Draw covariance before the independent
normalized teacher w; labels are `1{wᵀx >= 0}`, followed by independent .20
Bernoulli flips. Zero teacher norm is an integrity stop, never a redraw.

Partition indices are development=0, test=1, posttrain=2; family indices start
at zero within each partition. Family streams use root_index=0: covariance
matrix stream=0, eigenvalues=1, teacher=2. Root streams start at 10: dev0=10,
dev1=11, dev2=12, audit1=13, audit2=14, hidden=15. Each row stream draws its
complete row-normal matrix first, then its label-flip vector in row order.
Initial-map gate=20, initial permutation=21, migration gate=22, migration
permutation=23. Permutations use rng.permutation(8), then eight independent
rng.integers(0,2) signs; reject only the specified identity/equal-map event,
using the next draw in that same stream. Screen uses its fixed classes instead of streams 20/22; the pilot uses all four streams under its random artificial mixture. No map rejection reads a candidate. **Nobody evaluates streams 20–23 before the seal**, including exploratory class counts, manifest generation or smoke probes.

PCG64 SeedSequence entropy remains `[20261008, partition, family, root, stream]`.
Two roots, indexed 0/1, are specified per generated family; CPU realism uses
only root 0 of development families 0–7. Family parameters are shared within family; rows are independent across roots. Screen class indicators are fixed per family, but conditional map permutations are root-specific. Pilot indicators and maps are independent across roots. Realism law awaits the explicit balancing answer. All three
behaviours and regimes share each root's task rows/maps/labels/reach. Repetitions
0/1 change optimization samples only, using stream index
`1000 + 100*repetition + 10*phase + action_index`, phase prefix=0,
pre-c2=1, post-c2=2, and action_index=0…3 for ordinary actions in its phase;
audits use action_index=8. No RNG state is advanced by another branch's action.
Fitting-row indices are the first floor(fraction*80) rows of each batch in
original row order, check rows its complement. Within each action, sample
indices with its keyed rng.choice without replacement. Pooled rows concatenate
by dev0/dev1/dev2 order. These samples are identical for behaviours whenever
their permitted fitting populations coincide.

Each (root, behaviour, repetition) has one prefix and c1 fork shared across
now/continue. Reached later/never fork at the same c2 state. Prefixes across
behaviours or repetitions need not match; restoration digests are compared
only for the forks actually sharing them. CPU root IDs remain a2-r0…a2-r7;
other IDs are `a2-{partition}-f{family}-r{root}`. Reach is the unchanged attempt-1 hash predicate, independent of maps and labels. The author-provided 7/8 reach for the eight realism IDs is recorded in ATTEMPT2_PRESEAL_RECORD.md and must be included in the later seal package; no IDs are searched or changed. No reach computation is needed to implement this document revision.

The sealed implementation constructs a canonical JSON manifest, UTF-8 with
sorted keys and compact separators plus newline, containing namespace,
family/root/split IDs, seed keys, row and parameter SHA-256 digests. Arrays
are encoded little-endian float64 in C row order; labels uint8; no outcome
field affects manifest generation. Generate each approved cohort once after its freeze, audit it against already generated cohorts, and use its fixed IDs without replacements. No held-out final-test generation occurs before the final-law freeze. The eventual
command is `python -m experiments.paper_b.task_cc_v2.realism --output
results/paper_b/task_realism_v2_<UTC> --design
experiments/paper_b/task_cc_v2/ATTEMPT2_DESIGN.sha256`; existing output refuses.
There are no tunable command-line mechanisms, family counts, seeds or thresholds.

### M1: exact R summaries and denominators

Let U[f,b,r,a] denote terminal accuracy for family f=0…7, behaviour b,
repetition r=0/1 and regime a. Define u[f,b,a] as the arithmetic mean of both
repetitions. No selected repetition enters any criterion. All SDs below use
ddof=0. R1 applies the original literal rule to these family means: now wins
if now>=later and now>=never; later wins if later>now and later>=never;
never wins if never>now and never>later. Report exact equality counts too.
R2 is SD over eight families of u[later]-u[never], >.02 for each behaviour.
R4 is max over eight families of u[now]-u[never], >.02 for typical; the author adopted this terminal, budget-matched comparison in place of attempt 1’s isolated c1 refit diagnostic, accounting for the work debit; show every
family gain and corresponding careless/careful controls descriptively.
R5 requires at least one family with u[now]<u[never] or u[later]<u[never],
for each behaviour. R6 uses mean and SD of eight typical-never family means,
with the unchanged [.2,.8] and >.05 thresholds. R7 reach and early-termination
fractions use eight original roots, counted once each, not leaves/repetitions;
nonreach is not termination. R3/R9 must pass their declared integrity tests
for all families and every produced leaf. R8 reports planning arithmetic and
checks the actual CPU wall/storage limits. Any collection-integrity failure
makes the whole attempt incomplete; it cannot yield a PASS from remaining rows.

### M2: signed-coordinate copies and history scope

Replace raw descriptor distance for acceptance with a canonical orbit metric.
Let S_i=diag(sign(w_i)), canonical teacher a_i=abs(w_i), canonical covariance
C_i=S_i Sigma_i S_i. Sort coordinates by increasing a_i and apply that same
permutation to C_i. Then compute the previously declared max distance on these
canonical (a_i,C_i) pairs, with the same .10 near-duplicate threshold. This is
invariant to simultaneous signed coordinate permutations; coordinate copies
have zero distance. If any teacher coordinate is exactly zero or abs-values
are exactly tied, preflight stops for the author rather than choosing a
symmetry convention or redrawing. Treating all signed coordinate copies as
near duplicates is deliberately conservative for careless's first-four mask;
it does not imply rotational equivalence or diverse application domains.

History comparison uses one representative never tail, typical, repetition 0,
root 0 per family. Exclude known paired-prefix copies from this comparison,
but test those separately for exact restoration. Compare only serialized
visible numeric table rows and candidate predictions; remove row IDs, file
paths, system/task/tool instruction blocks entirely. Render numbers to six
fixed decimals; tokens are numeric literals, labels and neutral field names.
Use 5-token shingles and Jaccard >=.90; empty or <5-token history is an
integrity failure. Report within/cross-partition matches, and stop on any
cross-partition match. This supplements the invariant law and row audits;
it cannot establish natural-workload generality.

### N1: information surfaces

Executor sees dev0 at prefix, raw dev1 at c1, raw dev2 iff reached, their
provenance and intentionally visible labels, candidate, slot clock and tool
outputs. Only an invoked audit reveals **current** map correspondence,
current/alternative diagnostic accuracies and selected executable candidate;
audit rows, teacher, seed, future maps and hidden test remain host-only.
The proposed controller sees numeric histories consisting only of visible
batch count/row count, fitting fraction, feature count, visible check accuracy,
ordinary-action count, consumed slots, verifier-used flag and (at c2) its
reached flag. H2 retains H1 and current values with checkpoint-prefixed keys.
It does not consume raw seed/IDs/paths, map matrices, candidate coefficient
vectors, protected diagnostics or host truth. Recorder alone receives the
listed ground-truth metadata. The author adopted these information surfaces;
configurator feature-map changes remain governed by their separate decisions.

## 📋 Approval and implementation boundary

Independent challenger reviews this document before it is sealed. Resolve each
finding with a written disposition; no outcome-producing probe is permitted.
**STOP (D-ATT2):** author approves this complete task law, behaviour change,
work horizon, integrity definitions and execution-bug-only repair policy.
Only then write `ATTEMPT2_DESIGN.sha256`, commit and push the approved design
and hash, and implement new files under this directory. No baseline task,
fixture, contract value or claim is silently changed by approval of a draft.

Before sealing, the author must inspect this revision/diff and resolve the pending realism balancing choice. No RNG streams 20–23, outcome-producing code or design hash may be generated beforehand. The seal package must include this design and ATTEMPT2_PRESEAL_RECORD.md.

Implementation files (after seal): generator, executable candidate, task tools,
prompts and realism runner. Tests cover family distinctness, partition separation,
hidden-test isolation, forked clock/optimizer restoration and executable candidate
round-trip. After one realism run, record the full R1–R9 table and all outcomes,
PASS or FAIL. Passing is never presumed from this mechanistic argument.

## Author D-ATT2 revision disposition — 8 October 2026

Complete approval: **withheld**. Adopted subitems: terminal R4; behaviour changes;
never-as-control, 144 leaves; symmetry-aware metric; information surfaces; CPU
caps; execution-bug-only repairs defined by test-demonstrable code/sealed-text
mismatch. Required revisions incorporated: disjoint development phase cohorts;
balanced screen, separate artificial-mixture pilot; recorded fitting schema and
canonical weight conversion before decoder replacement; supplied 7/8 reach
in the pre-seal package; no evaluation of RNG streams 20–23 before seal.
Balanced realism: **pending explicit adopt/decline**. No scientific or runtime
record is authorized by these partial decisions.
