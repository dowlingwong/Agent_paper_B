# Proposed HoreKa EVIDENCE note binding — open, not authorization

AI-assisted (Codex). This is one concrete format option for discussion, **not an author decision** and not a submit-tool implementation. The current tool continues to refuse EVIDENCE and late phases. The single default-off real-submission switch remains off.

The runbook requires the author's committed G.5 authorization note for EVIDENCE and, after HK5 projection, the author's decisions on the number of task nodes, K and budget (HoreKa runbook §0.2, §0.4, HK5–HK7). It does not specify machine-readable note bytes or manifest binding. One narrowly scoped option is a committed JSON note such as:

```json
{
  "schema": "hk2_evidence_authorization/v1",
  "author": "Dowling Wong",
  "approved": false,
  "phase": "HK6",
  "manifest_sha256": "<SHA256 of exact committed job manifest bytes>",
  "node_count": "<author-chosen positive integer after HK5>",
  "audit_k": "<author-chosen integer in force after HK5>",
  "budget_gpu_hours": "<author-chosen finite positive number after HK5>"
}
```

The placeholders and `approved: false` deliberately prevent use. If adopted, the author's final committed note would contain typed numeric values, the specific phase, and the exact manifest hash; the verifier would require committed, clean checkout bytes and check the selected manifest against them. One note per exact manifest is conservative but can be burdensome for many jobs; the author may instead choose a reviewed, bounded manifest-set format. The authorization and the recorded count, K and budget do not by themselves prove that the generated command does what the manifest claims. Independent review must classify the actual argv, phase and input/output paths, verify every manifest against the authorized task set and limits, and check other runbook phase gates. The budget guard and site accounting checks remain separate. A changed manifest needs a new valid binding. These are proposed minimum semantics, not a claim that source authentication is cryptographic.

**Author options:** adopt this per-manifest format; choose a reviewed manifest-set binding; or specify another format. **Recommendation:** choose a manifest-set format only after its membership and per-job limits can be checked without ambiguity; use the per-manifest format for the smallest initial scope. **Paste-ready answer:** `For HoreKa EVIDENCE, use <per-manifest / reviewed manifest-set / other specified> committed author-note format; the post-HK5 node count, K and budget still require my decision.` No choice permits a job by itself.
