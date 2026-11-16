# Independent review: Stage A footprint capture (7 November 2026)

**Verdict: ACCEPTED for the captured Stage A footprint and model/build bindings at Paper commit `92fb405732ccd8a58165ab0171a848f5cad5111b`; not a host preflight, actual model-load test, author gate or B1 launch acceptance.** No host access, GPU, model, or evaluation audit data was used during this review.

The retained `/private/tmp/paper-b-stagea-footprints-20261107.6NfPwZgJ/fields.jsonl` SHA-256 is `b29bc5ac87ea91145d970cfdeddca23ccd57f675c5fc160bc30aa32c67ee8a8f`; stderr is empty and exit file contains `0`. The capture reports t7h8 table SHA `00ab143dc0742b24034e653bfa15acff5183538f85a1179cdbc7802cac22975c` and 24 rows, and t7j10 SHA `71525124fcf973ef7465fee9b0ff99c27b3f21b68f3a0ca55fcb9f7357992103` and 10 rows. These agree with the committed B1 config and O1 receipt. There are 11 emitted t7h8 PASS rows and 10 t7j10 PASS rows, without duplicate candidate IDs within either table. The independently reviewed probe reads and hashes complete tables before emitting PASS fields; the capture reports their hashes, but the raw remote table bytes are not in this reviewer’s local evidence and the capture alone does not independently rehash them.

I reconstructed the frozen `stage_a_pass_set` selection from the captured PASS rows and the committed registry, including the rule’s thinking-off eligibility. The selected set contains the two software anchors `random_valid` and `scripted`, which have no model footprint, plus the following **16 model-backed entries**. Every entry has a positive finite footprint, PASS qualification, model SHA equal to its committed registry entry, and build equal to the config's `version: 0.7.0-dev (build 1, commit 620d222)`:

| Model | Selected Stage A table | Footprint MiB |
|---|---|---:|
| qwen25_coder_7b | t7h8 | 5734 |
| qwen38_27b | t7h8 | 17682 |
| qwen36_27b | t7h8 | 17998 |
| gemma4_31b | t7j10 | 21534 |
| olmo31_32b | t7j10 | 20542 |
| devstral_small2_24b | t7j10 | 16750 |
| qwen36_35b_a3b | t7h8 | 21132 |
| gemma4_26b_a4b | t7j10 | 17424 |
| glm47_flash | t7h8 | 18972 |
| laguna_xs21 | t7j10 | 20626 |
| ornith10_35b | t7h8 | 20922 |
| qwen3_coder_30b_a3b | t7h8 | 19772 |
| qwen35_9b | t7h8 | 6360 |
| gemma4_12b | t7j10 | 8434 |
| ornith10_9b | t7h8 | 6078 |
| ministral3_14b | t7j10 | 10886 |

The committed registry SHA-256 is `2c6ef6b329694536df6a23345e4313d0cb2dcbf447113023e18f60fcb608e723`; B1 config SHA-256 is `6b6a851e4f4a4d1b6bfa02199da69fdad51935586c775d8f685bf484306adcb6`. The t7h8 qwen anchor takes precedence over its duplicated t7j10 row; only candidate rows from t7j10 are added. These footprint values are previously recorded Stage A qualifications, not current GPU memory/capacity observations. The capture does not establish actual current model files, server state, host headroom, the approved note, exact final checkout, author gate or any other B1 launch prerequisite. No audit evaluation values were read.
