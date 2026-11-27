# Independent screening authorization review (local/20261127-12)

AI-assisted (Codex, independent tier-E reviewer, 27 Nov 2026). I did not write the authorization or the code.
I reviewed the documentation diff from published base `98c571d22251a9d57a6d157950bd5ac8c340e17b` at
`6da4e63021b9f127452300284c6ec89f7b7595b7`. The review covers handoff of the unsigned authorization to the
author and the exact screening code pin. The author signature, publication and live strict preflight are pending.

## Exact bindings

| Record | SHA-256 |
|---|---|
| `docs/r1/authorizations/screen_measure_20261127.md` | `c622ccb5c7781b18639edfbb23ad299820b04e996d95487e73ef8d3da2bd8831` |
| `docs/r1/authorizations/SCREEN_MEASURE_PREDECLARATION_20261127.md` | `a380dbf122f17705f29ae0d056a8eafeebe67f2718a6fca09616994c09362585` |
| Smoke report | `09621f0539f8136ce28010059894cabbb1b2600a3f9eff4771e0ed581538fcfa` |
| Smoke manifest | `20748f42e5792a78d49abb8249c9a8f85c37116067169031c01be99b9b14ddc7` |
| Data-cache manifest | `74e688e754346d177cbafbe7e19b4bd984839d37c7808600f20c011602bcbd62` |
| Data-cache tree | `c0c2a3645f3fbcbeed6374e7f1a1b717421ec39985cb875bdc1e4a44f6a9781b` |

The pre-declaration copy equals the reviewed draft byte for byte. I verified the eight populated P fields, cited
artifact hashes, canonical design hash and the 10,164-run plan. P7 correctly uses R1-SCREEN-MEASURE-CHOICES
option (a), the both-links rule, and run ID `smeas-20261123-a`. The original review and cache re-check cover the
companion text. The first authorization candidate omitted the P1–P8 field names. The reviewed revision restores
the eight names, and the actual `key_block()` parses it. Using the candidate bytes as the published-note fixture,
`preflight_evidence()` rejected the unsigned note for the `approved` field. The runtime environment and lease
were not simulated as live checks.

The exact code pin is the published smoke checkout and descends from the merged ARFF fix. I compared the six
screening files, their focused test, and relevant paper helpers, 19 paths in total, across the previous ARFF re-check
target `e5227c0c`, the merged fix `03a352d9` and the exact code commit below. All 19 paths were byte-identical.
Changes from the merged fix to the launch pin are confined to D.3 implementation and its tests. The six code hashes
match the note and the smoke manifest. On a temporary export of the exact code commit I ran
`python -m pytest -q -p no:cacheprovider r1/tests/test_screen_measure.py` with isolated Git metadata,
a fresh temporary directory and Python 3.11.5. All 82 synthetic tests passed in 9.64 seconds.
The authorization diff is documentation-only.

## Smoke and flag reading

The published captures verify against their checksums. The cache trees recompute for all six OpenML nodes and
their aggregate matches the smoke manifest. Each has one ARFF, and the four recorded pilot ARFF pins match the
decompressed content hashes in the manifest. The smoke records seed 999, 168/168 runs, zero failures, no STOP,
the clean pinned harness, equal edit sets on eight nodes, and an adequate co-tenancy margin. Compute reports
`failed_runs.jsonl` absent, consistent with the recorded counters and the log creation path.

I checked all 37 configuration pairs in the note against the manifest and the design. On digits, discrete-metric
ties are plausible given the 2–4 ties per 30 joint E1 seeds for each single edit and verified edit application in
the smoke. The child rates are unmeasured. The breast-w, credit, ionosphere and sonar comparisons are consistent
with their single-seed tie context and near-duplicate links. On WDBC nine flags involve C or class weight. The
remaining random-forest comparison c3 versus c0 tied at 2 of 30 repaired E1 pilot joint seeds, which I
recomputed. The tabular flags involve ALPHA edits, with observed 5/30 and 11/30 single-edit ties and nonzero
E1 mean changes. Climate has no flags, including the decisive c35 versus c3 check. No flag meets the return
condition in pre-declaration §8.4. The evidence analysis retains the global refusal for bit-identical vectors.

The seed check ran locally over 3301–3420. The cited all-refs review is historical and the current strict
preflight repeats the registered static check. P5 and P8 cite recorded conditions and still require the live
environment, worker-runtime and co-tenancy gates. The older screening and D.3 order rows place the screening
reading before the D.3 signature. The author has since signed the rev 4 text and its binding freeze remains
pending. The coordinator should reconcile the ordering before freezing D.3 and retain the declared SHARED
handoff for author disposition if it occurs.

I used published engineering artifacts and the designated E1 pilot records. I did not access sealed data,
release partitions, credentials or hosts. No smoke replay, evidence job or launch took place in this review.

Code-Commit: e153df24ee3435bbe0b2fa994297b15250550c30
Verdict: ACCEPTED
