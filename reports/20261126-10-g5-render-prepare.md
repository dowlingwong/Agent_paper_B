# local/20261126-10 → local/20261126-08 "prepare now": G.5 signature fills, dry run

Task: `local/20261126-10` (first input of `local/20261126-08`), the "prepare now" part of -08. Level 0, no spec change pushed.
Base: `main` `54082a05` (contains `ef06a65c`, R1-G5-SIGNATURE). Spec `sweep2/t1_tasl/g5_tasl_spec.json` sha256
`16b39b475e5ccccd9143de06b0a69996e5274d73033521d5cac8c1db0470627f` (unchanged on `main`).

## Result in five lines

1. The signature's choices fill four field groups now (8 × `decisions.<id>.signed`, `decisions_row`, `e4_amendment_row`,
   `key_values.freeze_wait_release_date`, `key_values.cuda_ipc.mode`); every other choice S1–S14 equals the spec's value already.
2. In a scratch copy with those fills, `validate_spec` (draft) passes with no unsigned decision and no launch blocker.
3. `key-lines` on the scratch copy: rc 0, 57 lines, the same keys as on `main`. Four lines change: `freeze_wait` (2027-12-31),
   `decisions` (row R1-G5-DECISIONS-2), `e4_amendment_row` (R1-G5-MEM-E4) and `spec_sha256`. `cuda_ipc` renders the acceptance line both before and after.
4. `validate_spec --launch` refuses only on the inputs still to come, in this order: `run_id`, then `tails` (P10), then
   `noise_floor.seven.*` (the copy). With dummy values for those three, launch validation passes. **No refusal comes from a signed value.**
5. The final render waits for `compute/20261126-05` (the reviewed REL-T1-G1B copy) on `main`, as the card says.

## Fields the signature fills, with the source of each value

| Spec field | Value | Source |
|---|---|---|
| `decisions.{G5-W, G5-TEMP, G5-MEM, G5-AUDIT, G5-DIV, G5-TASL-GPUH, G5-SLOT, G5-ARPEND}.signed` | `true` (each `option` is already `A`) | R1-G5-DECISIONS-2 items 1–8; R1-G5-SIGNATURE (1) S10 |
| `decisions_row` | `R1-G5-DECISIONS-2` | R1-G5-SIGNATURE (1) S10 |
| `e4_amendment_row` | `R1-G5-MEM-E4` | R1-G5-SIGNATURE (1) S10 |
| `key_values.freeze_wait_release_date` | `2027-12-31` (no "moved by author row" suffix) | S6 (c); task `local/20261126-10` |
| `key_values.cuda_ipc.mode` | `acceptance`; the six `c12_*` fields stay `null` (the validator requires null outside `c12`) | S4 (a) |
| `key_values.cap_gpu_hours`, `liveness_floor`, `invalid_share_stop`, `infrastructure_stop_share`, `audited_band`, `seal_mode`, `t1_table_readings`, `server_log` | unchanged: 425, 0.25, 0.2, 0.05, [100, 200], procedural, `refuse`, `a` | S1 A, S7, S8 (spec already holds them) |
| `key_values.status` | not read by the code; free text. Proposed: `"signed (R1-G5-SIGNATURE, 26 Nov 2026)"` | cosmetic; it changes only `spec_sha256` |
| `tasl2_cpus`, the CPU-set check, `audit_K`, the seeds, environments, `tasl7_audits` | unchanged | S13 A, S14 A, S11 K = 10, S12, S5 A |
| `noise_floor.seven.{copy, sha256, review, sealed_path, gate_copy, gate_sha256, assembly_copy, assembly_sha256, runs_copy, runs_sha256}` | from the reviewed copy | `compute/20261126-05` on `main` (**not yet**) |
| `nodes[*].tails` (seven nodes) | `gaussian` or `student_t` per node | P10 declarations from the copied seven-node summary (E5): after the copy |
| autoresearch: `noise_floor.ar.*`, `nodes[autoresearch].env`, `.tails`, `harness_families.G5-AR.isolation_host_check` | stay PENDING | G5-ARPEND A (completion record later; validated as PENDING) |
| `run_id` | `c3_t1_labels_<YYYYMMDD>` | the note's date, at render |
| `paper.commit` | the publishing commit | at publication (coordinator) |
| `spec_sha256` | printed by `key-lines` from the filled file | mechanical |

## Commands (scratch copy only; nothing pushed)

```
python <scratch>/g5fill.py sweep2/t1_tasl/g5_tasl_spec.json <scratch>/spec_signed.json   # the fills in rows 1-5 above
python -c 'validate_spec(spec)'            -> OK, unsigned [], launch_blockers []
python -c 'validate_spec(spec, launch=True)'-> STOP: run_id must be c3_t1_labels_<YYYYMMDD>
  + run_id, paper.commit dummies           -> STOP: mlab_cifar10.tails must be gaussian or student_t (P10)
  + tails dummies                          -> STOP: noise_floor.seven.assembly_sha256 must be a sha256 (64 hex)
  + noise_floor.seven dummies              -> launch: OK
python sweep2/t1_tasl/g5_tasl.py key-lines <scratch>/spec_signed.json  -> rc 0, 57 lines
```
Scratch spec sha256 (fills only, no dummies) `7ab3c35362522bca9c310a40226869dc32ae3c63005ed85591bc3872764d224f`, for comparison only.
`check-note --draft` cannot run before a note exists. It runs at render time.

## Decided alone

The fill set and the dry-run method (iterating launch validation with dummy values only to reach refusals after the first). No spec change pushed.

## Needs

Nothing from the author. For the final render (-08): a task file naming the merge commit of `compute/20261126-05`.
The render then fills the copy fields, fills `tails` from the seven P10 declarations (from the copied summary; who records P10 to be confirmed in that task), sets `run_id` and
renders. A render that changes any choice above goes back to the author (R1-G5-SIGNATURE (2)). None is expected.
