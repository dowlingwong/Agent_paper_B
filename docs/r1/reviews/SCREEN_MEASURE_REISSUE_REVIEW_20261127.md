# Independent screening authorization re-issue review

AI-assisted (Codex, independent screening reviewer, 27 Nov 2026). I reviewed
`local/20261127-21` against published main `e92f3c7389e06347a0ff78f5f68971024133c670`
and the author-signed R1-SCREEN-MEASURE-REISSUE row. The candidate is
`f8a1c3ef02a9c90c5883d034f055ebf72e743def`. I did not prepare the candidate.

The candidate adds exactly `docs/r1/authorizations/screen_measure_20261127_reissue.md`.
The original signed note is byte-identical on both trees. The candidate's command
names `python3`, points `--note` to the new file, and uses a fresh UTC stamp for
the evidence and scratch folders. The same stamp is used for analysis and outputs.
One sentence cites the author row and the worker-runtime STOP and excludes the stopped
stamp `20261127T1032Z`. The STOP records the literal interpreter alias mismatch and
zero of 10,164 runs written. Reversing these textual edits recovers the signed
original byte-for-byte. `git diff --check` passed.

All 33 parsed key-block fields are identical, including `approved: true`, the
scientific run ID, the 3301–3420 seeds, the six code hashes, harness commit, the
cache tree pin and all P1–P8 lines. At the exact pinned code commit I recomputed
the six code hashes and canonical design, reproduced the 10,164-run plan, and
checked the companion's byte hash and the published independent code review.

I ran the pinned `preflight_evidence` for the new repository-relative note path.
It refused before publication as expected. With only the new note supplied as a
published-byte fixture, it passed the real field, design, seed, companion,
published PLAN, code provenance and scratch path checks. I stubbed the host environment,
harness-equivalence and co-tenancy probes. The live strict preflight still belongs
to Compute after coordinator publication. The focused synthetic screening suite
passed 82 tests at the exact code pin. The candidate is documentation-only.
I accessed neither hosts nor sealed data and launched no evidence run.

| Binding | SHA-256 |
|---|---|
| Original signed note | `96188e7c8d0ff92990f8ac821ad3608838cbb59226096064072a627061cd88e0` |
| Re-issued note | `7c3c8313e90016fa1ff6773bd678e95e5c6ed9457b14d01631897499ee0fdeb0` |
| Companion pre-declaration | `a380dbf122f17705f29ae0d056a8eafeebe67f2718a6fca09616994c09362585` |
| Published exact-code review | `ee0b83776b822026a06e378506d09fa6b0520047e42af9a4d3404f035a65b814` |
| STOP report | `1edf4b30c87417063714cccb48465994a0370cff5621e9367ca1cb1e01910169` |
| Canonical design | `bbc98b87d2170ad89ff17a92303ffb440583b74b035d2690a6a2ababeb8d8ec8` |
| Data-cache tree pin | `c0c2a3645f3fbcbeed6374e7f1a1b717421ec39985cb875bdc1e4a44f6a9781b` |

Code-Commit: e153df24ee3435bbe0b2fa994297b15250550c30
Verdict: ACCEPTED
