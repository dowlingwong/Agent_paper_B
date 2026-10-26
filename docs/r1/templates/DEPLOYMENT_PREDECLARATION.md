# Deployment pre-declaration template

AI-assisted scaffold. **Not a pre-declaration, authorization, or PLAN decision.** The author fills, commits and adopts the actual declaration and its hash before deployment. See RUNBOOK D.2 and PLAN §9.

## Contrasts and outcomes

For each H1–H5, specify the exact arms, estimand, outcome, direction and primary or secondary status. Include the three-way comparison of LLM self-control, trained configurator and hybrid. Cite the governing PLAN rows and resolve any outstanding arm-definition questions before declaring them.

| Contrast | Exact comparison and outcome | Status and PLAN reference |
|---|---|---|
| H1 | AUTHOR TO FILL | AUTHOR TO FILL |
| H2 | AUTHOR TO FILL | AUTHOR TO FILL |
| H3 | AUTHOR TO FILL | AUTHOR TO FILL |
| H4 | AUTHOR TO FILL | AUTHOR TO FILL |
| H5 | AUTHOR TO FILL | AUTHOR TO FILL |
| Three-way comparison | AUTHOR TO FILL | AUTHOR TO FILL |

## Instances and budgets

- Nodes, inclusion criteria, instance identities and seeds: AUTHOR TO FILL.
- Sample sizes, repetitions and justification: AUTHOR TO FILL.
- Matched worker-run budget W, LLM-call cap, information and tuning budgets: AUTHOR TO FILL.
- Audit seeds, exclusions, missingness and integrity handling: AUTHOR TO FILL.

## Analysis and provenance

- Analysis script path, immutable revision and SHA-256: AUTHOR TO FILL.
- Statistical method, clustering, uncertainty, multiplicity and sensitivity analyses: AUTHOR TO FILL.
- Code, configuration, model, data and environment pins: AUTHOR TO FILL.
- Author, date and adopted PLAN row: AUTHOR TO FILL.

After the author has finalized the declaration, calculate its exact byte-level SHA-256 with `python -m r1.predeclaration hash PATH`; verify a saved digest with `python -m r1.predeclaration verify PATH SHA256`. A hash alone does not adopt the declaration or authorize a run. Record the declaration hash separately to avoid self-reference.
