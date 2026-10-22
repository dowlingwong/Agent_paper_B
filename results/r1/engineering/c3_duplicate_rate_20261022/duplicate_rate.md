PILOT. AI-assisted (Claude). Table: `results/r1/engineering/c3_duplicate_rate_20261022`.

| Source | Node | Memory | Campaigns | Proposals | No-op: inactive edit | No-op: incumbent repeat | Duplicate | Other | No-ops | Duplicates | Wasted runs under ρ (per campaign) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| dt4 | digits_mlp | none | 6 | 114 | 0 | 0 | 88 | 26 | 0.0 % | 77.2 % | 88 = 77.2 % (14.7) |
| dt4 | openml_ionosphere | none | 6 | 114 | 114 | 0 | 0 | 0 | 100.0 % | 0.0 % | 114 = 100.0 % (19.0) |
| liveness | digits_mlp | append_only_summary | 2 | 18 | 0 | 0 | 8 | 10 | 0.0 % | 44.4 % | 8 = 44.4 % (4.0) |
| liveness | openml_breast_w | append_only_summary | 2 | 17 | 0 | 0 | 6 | 11 | 0.0 % | 35.3 % | 6 = 35.3 % (3.0) |
| liveness | openml_ionosphere | append_only_summary | 2 | 18 | 0 | 0 | 9 | 9 | 0.0 % | 50.0 % | 9 = 50.0 % (4.5) |
| liveness | tabular_mlp | append_only_summary | 2 | 18 | 0 | 0 | 8 | 10 | 0.0 % | 44.4 % | 8 = 44.4 % (4.0) |
| rerun2A | openml_breast_w | append_only_summary | 18 | 340 | 0 | 0 | 209 | 131 | 0.0 % | 61.5 % | 209 = 61.5 % (11.6) |
| rerun2A | openml_ionosphere | append_only_summary | 18 | 342 | 0 | 0 | 225 | 117 | 0.0 % | 65.8 % | 225 = 65.8 % (12.5) |
| rerun2A | tabular_mlp | append_only_summary | 18 | 342 | 0 | 0 | 174 | 168 | 0.0 % | 50.9 % | 174 = 50.9 % (9.7) |
| **all** | **all** | **append_only_summary** | 62 | 1095 | 0 | 0 | 639 | 456 | 0.0 % | 58.4 % | 639 = 58.4 % (10.3) |
| **all** | **all** | **none** | 12 | 228 | 114 | 0 | 88 | 26 | 50.0 % | 38.6 % | 202 = 88.6 % (16.8) |
| **all** | **all** | **all** | 74 | 1323 | 114 | 0 | 727 | 482 | 8.6 % | 55.0 % | 841 = 63.6 % (11.4) |
