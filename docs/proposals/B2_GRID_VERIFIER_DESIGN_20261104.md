# Proposed B2 grid verifier

**Status: proposed, AI-assisted. This document is not an authorization, an
author decision, or an acceptance of B2 evidence.** The B2 instance count and
power plan remain open. The current unconditional v2 ranking STOP remains in
force until the verifier is implemented and independently accepted and its
required author decisions and evidence exist.

## Purpose and current boundary

The x5_rule/v2 B2 summary must not rank candidates from an incomplete or
unequal set of node/instance results. The verifier should establish the
expected grid from the author-bound power plan and require each B1 finalist's
primary thinking-off results to cover exactly that grid. It must fail closed
on missing, extra, duplicated, inconsistent, or unverified evidence. Only
after verification may the existing final-Y ranking and GPU-hours tie-break
run. This is a proposed design, not a decision about a count or node list.

At `5fcea745d2d31716a1e016153008465a2cb83442`, `b2_summary` dispatches v2
manifests to `_b2_summary_v2`, which currently raises an unconditional STOP.
`runtime.author_gate` verifies the committed authorization note, rule hash,
nodes and B2 instance count against the launch configuration, and binds the
B1 analysis hash; it does not by itself prove the complete grid received by
the summary. The verifier must not replace this STOP with a permissive path.

## Inputs and authority

Require explicit, verifiable inputs: the author-committed B2 authorization
note, the applicable dated author PLAN power-plan row, the frozen B1 analysis,
the pinned rule, the candidate manifests, and their root-level evidence and
receiving checks. Verify actual bytes against their expected SHA-256 values;
verify the authorization note against the bytes at its committed repository
revision. Match its author, approval, phase, rule hash, node list, instance
count and B1 analysis hash against the applicable author decision and launch
configuration. The PLAN row must record the power-plan decision; the note
must authorize this B2 and bind the exact values. A caller-supplied JSON
object, hash or `approved: true` is not by itself proof of author authority.

### Proposed authority anchor

The verifier needs a separately authenticated instruction from the author,
received through an author-verified channel outside the evidence bundle, that
designates an exact full commit ID published on an author-controlled repository
and ref as the authority snapshot, with the repository identity, immutable
commit ID and exact PLAN and B2 note paths and SHA-256 values. The commit's
existence or author-name metadata alone does not authenticate that instruction.
The verifier must obtain the snapshot from that designated publication and
compare the Git commit and file bytes to the separately authenticated pins;
local `HEAD`, a working-tree PLAN, an arbitrary caller-supplied ref, or a
locally fabricated commit bearing the author's name is insufficient. This is a
proposed future trust mechanism; no such designation is asserted here.

At that snapshot, parse the dated tables in PLAN §10 structurally and select
the exact author decision row identifiers specified by the author-designated
authority record. Read the decision cell, not a substring in other columns or
nearby prose. The decision cell must contain the author's decision binding the
rule, B1 analysis, nodes, count and note, either directly or by an unambiguous
explicit reference to the note and its digest. Validate the note's structured
fields against those bindings. A dated later decision or revocation that
supersedes the selected row must be resolved from a newer author-designated
snapshot; do not pick a convenient older row. Refuse ambiguous duplicates,
conflicting or insufficient rows, unrecognized formats, missing authoritative
snapshot, inability to establish its current applicability, or any mismatch.
Report STOP and the missing decision or authority input. This design does not
presume that today a power-plan row or designated snapshot exists.

The count must come from that decision, not from an observed result count or
an implementation default. Reject a missing, inconsistent, non-integer, or
Boolean count, and enforce the runner's present `1 <= N <= 89` limit for the
fresh 9011–9099 namespace. Do not invent an instance count in code or tests
that is represented as the actual author decision. Tests may use synthetic
counts in explicitly synthetic author records.

Read the expected finalists from the digest-verified frozen B1 analysis.
Reject an empty list, duplicate IDs, and IDs inconsistent with the applicable
registry and eligibility evidence. Require exactly one complete, primary,
thinking-off v2 B2 manifest for each finalist and no other primary candidate.
Check phase, rule, B1 analysis and candidate identity consistently throughout.
The runner currently skips specs absent from its Stage A eligible set, so the
analysis must detect a missing finalist rather than silently rank a subset.

## Grid and numerical validation

Build the expected Cartesian product from the author-bound unique node list
and the seed sequence `range(9011, 9011 + N)`. Every finalist must have the
same complete unique set of `(node, instance seed)` pairs. Reject duplicate
node names, canonical-ID collisions, missing or extra pairs, and duplicates,
even when the overall number of records is correct. Each final audit must have
exactly the ordered seeds 9201–9210 and ten finite numerical metrics; verify a
finite `final_y` against their mean with `math.isclose(reported, mean,
rel_tol=0.0, abs_tol=1e-12)`. This explicit absolute-only tolerance is a
proposed v2 validation rule and must be reviewed; the current call uses
Python's default relative tolerance as well. Accept actual finite numeric
values only, rejecting booleans and strings rather than coercing them. Audit
seeds must be exact integers, not booleans, in the specified order.

The actual B2 `final_audits` records produced by `campaign.py` have `node`,
`instance_id` of the form `<node>__s<seed>`, `seeds`, `metrics` and `final_y`;
the seed is not a separate field in each final audit. Generate a map from the
authorized expected pairs to exact canonical IDs, reject collisions, and match
records against that map. This avoids parsing a seed by splitting a node name
that itself may contain delimiters. Root campaign manifests also provide
`node`, `instance_seed`, `candidate`, `phase` and `mode`; use these to check
identity and ensure the aggregate audit matches its verified root.

Finalists must be registry candidates eligible under the frozen B1 analysis
and Stage A/D28 gates, rather than software anchors or sensitivity-only roles.
The three required CPU nodes follow the applicable author decisions. Track G
is an optional additional node only when the author explicitly adds the
specific node and the governing X.6 prerequisites, including G.1/G.3 and the
applicable same-host fit requirement, are evidenced. Resolve host conditions
against the latest integrated PLAN, including later amendments, rather than
hard-coding superseded host wording. A caller-supplied fourth node or config
list alone cannot establish that authorization. With no such decision, reject
an additional Track G node.

## Evidence and separation

Candidate-level `status`, hashes and flattened audits alone are not a
receiving check. Verify the digest-bound root manifests and their job and
post-check/evidence hashes using the applicable `runtime.verify_campaign`
contract and expected run binding. Cross-check every root's candidate, phase,
mode, node and seed, and require exactly one corresponding final audit whose
content matches the aggregate record. Bind the relevant authorization, B1,
rule and configuration identities across launch and analysis. Reject reused
root paths, swapped roots, modified jobs, checks or audit contents, and roots
from a different candidate, phase or mode. A hash demonstrates identity only
relative to a trusted, independently established binding; it does not by
itself prove who authorized a plan or that the measurement is valid.

### Proposed independent receiving commitment

Before B2 starts, the author must designate an independent receiving process,
its responsible identity and publication channel, the exact run and launch
config/rule/registry/B1/authorization pins it will receive, and the applicable
acceptance procedure. After the run, and before analysis or selection, that
receiver must independently obtain and validate the run artifacts and publish
an immutable receiving record at the designated channel. The author separately
authenticates the published record's repository, full commit ID, path and
SHA-256 to the verifier. The receiver's record binds the capture time and run
identity, full config and run-binding digests, authority snapshot and note,
rule and B1 analysis hashes, and a complete inventory of candidate aggregate
digests plus every root's path and digest, `job.json` digest and
`post_check.json` digest; it also binds the referenced evidence hashes and
server-interval records used for GPU-hours. The verifier compares all bytes
and expected identities against that externally authenticated inventory before
calling `verify_campaign` and validating the grid. The receiving record must
itself state the checks actually performed and their result; unexplained gaps,
false or absent evidence labels, non-acceptance, duplicate paths, missing
roots, digest mismatch or an untrusted or modified record cause STOP.

An independently authenticated record captured after receipt supports an
integrity claim from that capture onward; it does not alone prove the raw
artifacts were untampered before receipt, when a run happened, or that an
author authorized it. Those depend on the pre-designated procedure and its
independently verified provenance. A self-generated seal over arbitrary files
after inspection, or a mutually consistent replacement of a root, job and
post-check, is not prior provenance. If the designated receiver, authenticated
publication, required independent attestations or trusted record is missing,
keep STOP. This is a proposed prerequisite, not a claim that such a record
already exists or that any actual run was altered.

## GPU-hours and tie-break

The rule's tie-break depends on GPU-hours, so verify each primary candidate's
value against the externally committed server-interval records for that run,
candidate, phase and primary mode. Recompute the sum of non-overlapping,
completed dedicated-server wall intervals, including the applicable load and
audit time, using the runner's declared method and reviewed time units. Reject
missing or untrusted interval records, identity mismatches, open or interrupted
intervals that yield only an upper bound, overlap or contradictory timestamps,
and `None`, booleans, strings, negative or non-finite values. Proposed v2
validation compares reported and recomputed finite hours with `rel_tol=0.0`,
`abs_tol=1e-12` hours. This threshold and the fail-closed treatment of
interrupted intervals need independent review before implementation; any
different substantive policy needs the author's decision. No tie ranking may
use a merely self-reported or unknown cost.

Keep schema-free sensitivity and thinking-on descriptive results separate.
They cannot fill missing primary records, introduce a finalist or change the
primary ranking. Validate their own evidence and reported audit quantities
under their applicable scope, without imposing the primary grid where the
protocol specifies a different sensitivity design. Preserve them as
descriptive outputs only after the primary ranking gate has passed.

## Proposed tests and review

Use synthetic records and fake evidence only. A positive fixture can use two
synthetic finalists, three nodes and a synthetic author-bound `N=2`, with the
actual runner-shaped final-audit records and verified root bindings. Exercise
an independently authorized fourth Track G node as a separate positive case.

Individually test missing, extra and duplicate finalists, manifests, nodes,
instances and root paths; noncanonical or colliding IDs; unexpected 9001 or
9100 instances; an incomplete grid with the correct overall row count;
incorrect, duplicate or reordered audit seeds; non-finite metrics or means;
and mismatched `final_y`, including absolute-versus-relative tolerance edge
cases and boolean or string numbers. Test missing, modified or uncommitted notes,
inconsistent plan/count/rule/B1 hashes, an unauthorized Track G node or absent
prerequisites, and altered, replayed or swapped root/job/post-check evidence.
Tests must also change the root, job and post-check together and recompute all
their internal hashes while leaving the external receiving commitment fixed;
that must fail. Test changed/untrusted seals, fabricated same-author commits,
worktree-only PLAN edits, a superseding row and altered decision context. The
synthetic positive trust anchor must model both independently authenticated
authority and independently authenticated receiving commitments, not just a
fixture flag saying trusted. Test missing, manipulated, non-finite, boolean,
negative and interrupted costs, plus equal-Y ties with verified costs.
Every invalid case must raise before any ranked rows are returned. Verify
ranking and GPU-hours ties only on a verified complete grid, and show that
descriptive and schema sensitivity records do not affect it. Include direct
and CLI entry points. Compare v1 behavior to the actual `5fcea74` baseline:
the no-rule API accepts historical unstamped v1 manifests, while the default
CLI passes v1 explicitly and refuses unstamped manifests under the earlier
M2 rule-hash check. Do not silently broaden either route or remove the v2
safety check. Any proposed compatibility change requires separate review.

Run appropriate local CPU tests and compare full-suite results with the
baseline under the same environment. A fresh independent reviewer must assess
the implementation, authority binding, threat limits and tests before the
existing v2 ranking STOP is removed. Passing tests or adopting this proposal
does not authorize B2 execution, establish its power plan, or accept evidence.
