# MLGym data-manifest comparison (fmnist, cifar10)

Census host `experiment_zhixu` `/home/dowling/r1_trackg_20261117/data/` vs TASL production
(TASL-2 fmnist, TASL-7 cifar10). The only difference in each JSON is `source.datasets`:
census `5.0.1`, TASL `3.6.0`; the census `torch312` freeze is `datasets==3.6.0`. All four `.npy`
sha256 and byte sizes are identical.

fmnist `.npy`: test_x `fa687ea6e35cd511e68bc9cd5049edbadf6eb7dfde574e880a3325309e5aadfd` (7840128 B),
test_y `33e7c41e1d27e7ea46528a86fd6d54e0eb0d60f705e95ae5e9c956635f269cbc` (80128), train_x
`fa55843a054d8d313e1599d2541666e5febd6f186948f84db90dd89f854fa02e` (47040128), train_y
`eb6efccc70db136ce327076edeadbbcba39b38ab16fd8f89b0625f62fc605f24` (480128).

cifar10 `.npy`: test_x `b57763d00c64…`, test_y `fc48d9ecfdbe…`, train_x `9a8bd8090cac…`, train_y
`9e2ee9261f6a…` (same on both hosts; full hashes in the JSON files beside this note).

Whole-manifest sha256: census fmnist `8d28287b…` vs produced `24cb3448…`; census cifar10 `c0ef1168…`
vs produced `54d3a74d…`. This is metadata/provenance, not data bytes; no data was fabricated.
