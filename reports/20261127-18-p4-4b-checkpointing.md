# local/20261127-18 — P.4 4B activation checkpointing

for: compute

- Published code base `840ad01df1c517f023c3dc14c32ec7ae2429a109`. Reviewed and tested implementation
  `5b43cb221f28950be76d3fc81ef0cac7fec1bf55`. Delivery `mac-p4-4b-checkpointing-20261127`
  @ `585ed0d04bebfe1d6235d69b4bfe18207250ac39`.
- Independent implementation review **ACCEPTED** at the exact code commit. It confirmed both 0.8B
  configurations are byte-identical (SHA-256 `4f1345e72359e9c00b3d014f258aa5e2e64664513e8557b5115c4057c162e8dc`).
  Both 4B arms call the real checkpointing method before training. The review combines the archived
  0.8B results with fabricated 4B results and charges both roots plus T1 once. Review SHA-256
  `c2e5a9a58fccf7d0c4ebe26fe01bc008bfeac3e85b6d4615d8321b171b2ff83d`.
- R1-P4-4B-CHECKPOINT is limited to `kev-4b` and `qwen3.5-4b-base` on the P.4 route.
  Stage S and job records attest the setting. The synthetic probe retains micro-batch 8,
  effective batch 16, the original data and the 50-step limit. The original 0.8B seals and
  all older charges remain in the record.

## Tests

Python 3.12.8 and torch 2.15.0, LightGBM off the path, serial runs with fresh
temporary directories. `python -m pytest -q -p no:cacheprovider -rfE r1/tests`.

| Checkout | Failed | Passed | Skipped | Errors |
|---|---:|---:|---:|---:|
| Base `840ad01d` | 210 | 4,954 | 170 | 6 |
| Implementation `5b43cb22` | 210 | 4,963 | 170 | 6 |

The [216 failing/error IDs](20261127-18-p4-fullsuite-failure-ids.txt) are identical.
Sorted list SHA-256 `425dbc169a2937688ef5e11ddf7a836511d673f3c8a9ace00d8aebb603389f2c`.
The new targeted checks plus the grid/learning-curve comparison passed 10/10.
The runner and direct-launcher torch files passed all 213 tests on the candidate.
Both checkouts initially lacked the optional Kev package for its model checkpoint
test. Repeating the two model checkpoint tests with the published Kev package
pin `2074cc44256200bb37540103fa4572901faa10f3` gave 2/2 passes on each checkout.
The broader full-suite failures remain visible and were compared by ID.

## Exact probe inputs

- SFT config SHA-256 `093fffd71c9fa8b99a47a9a7bef908f6c66ff2c1e77663213ea15d0ef0f9f118`.
- Probe template `21a2ad9c34104c9a35b33891cd4ef030966aa9702301f096161f86e839e77022`.
  Phase-1 template `70ac8954f3a7f7d6f28420cdd47bd6b91c48820235f016c8c3139255c0377493`.
  Original sealed Ada spec `540bd9798017260ca391612351706189712221c269482a7d47385695160a50a2`.
  The filled spec below has SHA-256 `670330c12d0d8d7a6bd7a207e0018db66ae4285eb2111090fee6c9e254bc92d1`
  with jq's default formatting and passed the probe validator.

## Compute handoff

After the coordinator publishes the reviewed branch and confirms the Compute queue priority,
use the existing authorized Ada direct-launch account and pinned runtime. Use published main
with this exact implementation and compare its transferred files against the declared commit.
Check the active jobs, staging ledger and sealed tree before making a new stage. The fresh
run ID is `trackp-p4-probe-20261127-b`. Each arm uses a unique stage and one empty leased Ada.
The two 0.8B PASS results stay under the prior run. Follow the normal stage transfer and seal
process from the previous accepted Ada report.

```sh
code=5b43cb221f28950be76d3fc81ef0cac7fec1bf55
pkg=r1/scripts/htcondor/trackp_p4
prior=docs/r1/reports/trackp_p4_probe_ada_20261127/p4_probe_spec_ada.json
SEALED_ROOT=/ceph/srv/dwong/paperb/trackp_p4
PINNED_TABLE=/work/dwong/htcondor_prep_20261114/w2_3_rebuild_20261115/tables/c3_features_v3_20261115T232007Z
jq --arg code "$code" --slurpfile prior "$prior" \
  '.paper.commit=$code | .run_id=.ada_4b_reprobe.run_id | .host_class=$prior[0].host_class |
   .image.versions_sha256=$prior[0].image.versions_sha256 |
   .hosts.ada_rtx6000.host_config.sha256=$prior[0].hosts.ada_rtx6000.host_config.sha256' \
  "$pkg/p4_probe_spec.json" > "$NEW_SPEC"
python3 "$pkg/p4_lib.py" validate "$NEW_SPEC" --probe
first="$SEALED_ROOT/trackp-p4-probe-20261125-a/kev-0.8b/attempt-4/job_record.json"
python3 "$pkg/p4_render_jdl.py" "$NEW_SPEC" "$NEW_KEV_STAGE" --probe \
  --arm kev-4b --table "$PINNED_TABLE" --first-record "$first"
python3 "$pkg/p4_render_jdl.py" "$NEW_SPEC" "$NEW_QWEN_STAGE" --probe \
  --arm qwen3.5-4b-base --table "$PINNED_TABLE" --first-record "$first"
```

On Ada from each corresponding transferred stage, inspect `python3 p4_direct.py cards`,
then use `python3 p4_direct.py launch --stage "$REMOTE_STAGE" --arm "$ARM" --gpu "$EMPTY_CARD"`.
Seal with the exact filled spec, then report peak memory, timings, charged GPU-hours and
outcome. A repeat OOM on an empty card is an author STOP on that arm. For a combined
`probe-record`, use the previously sealed Kev 0.8B attempt 4 and Qwen 0.8B attempt 2,
the first verified STOP-free attempt of each new 4B arm, and the T1 history if T1
has yet to be charged in a base charge file. Keep all eight old attempts and all
new attempts in the charge accounting. The phase-1 note waits for the reviewed probe record.

Decided alone: used the existing Stage S checkpointing implementation, selected a new
run ID and kept the original first-arm seal as the staging gate. The local desk ran
synthetic checks only. No compute job was submitted.
