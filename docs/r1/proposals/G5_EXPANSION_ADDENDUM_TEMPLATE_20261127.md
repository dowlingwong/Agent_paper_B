# G.5 expansion addendum template

Draft under R1-G5-EXPANSION-JOIN, R1-STEP-ORDER (2)(a) and R1-G5-S9. Prepare a separate
spec, run and note for each eligible node. The coordinator publishes each approved note after
the main G.5 note. The main eight-node run has its own launch pin.

## Note fields

Publish under `docs/r1/authorizations/c3_t1_labels_<YYYYMMDD>_addendum_<N>.md`. Use the exact
values and digests of the filled spec and the accepted review.

```text
approved: false
run_id: <the note basename without .md>
node: <one expansion node>
paper_commit: <this addendum's paper code commit>
spec_sha256: <this addendum's spec SHA-256>
base_g5_note: <published path> sha256 <digest>
base_g5_spec: <published path> sha256 <digest>
instance_split: r1/c3/splits/c3_p3_split_v2.json sha256 4dd46796e50ec188b5f89ebc8f4c04e6ab60a5056f124538936dd1bb5d6ae53a
pre_split_amendment: <published path> sha256 <digest>
supply: <g5_addendum_mlgym or g5_addendum_extra_task>
review: <published independent review path> sha256 <digest>
```

The review cites the run ID, the code commit and the spec digest. Cite the G.1b seal and
D6 copy, the G.5 host and harness check, the author P10 declaration, and the projection
and applicable reporting threshold in the body.

## Spec

Use `schema: g5_tasl_addendum/v1` in a JSON file under `sweep2/t1_tasl/`. The fields below
name the deployment and the published records. Every citation is a string of the form
`<repo-relative path> sha256 <digest>`.

| Spec field | Value |
|---|---|
| `run_id`, `node`, `supply` | The same values as the note |
| `paper` | `{"repo": "<base G.5 repository>", "commit": "<addendum code commit>"}` |
| `base_g5_note`, `base_g5_spec` | The note's two citations |
| `g1b_note`, `g1b_spec`, `g1b_receipt` | The signed expansion note, expansion spec and that node's successful G.1b receipt |
| `g1b_copy` | Reviewed REL-T1-G1B copy fields `copy`, `sha256`, `sealed_path`, `review`, `assembly_copy`, `assembly_sha256`, `runs_copy`, `runs_sha256` |
| `pre_split_amendment` | The note's citation |
| `instance_split` | Object with `path` and `sha256` for the exact v2 file |
| `tail` | `tails`, `authority` (the published author row naming the node and law), and `tails_nu` for Student-t |
| `harness` | `g1b_pin`, `g5_commit`, `harness_dir`, and `isolation_host_check` with `record` and `sha256` for TASL-2 at the G.5 harness pin |

Make the filled spec the only non-document change after its paper code commit. The
launch checkout and note pass `verify_launch_tasl` against that commit and spec. The
strict `g5_tasl.py check-note SPEC --note NOTE` runs after publication. The command
also supports `--draft` with an unsigned filled addendum and its prerequisite records
already published.

## Worker deployments

The switch takes the census interpreter and freeze from the published G.1b spec.
TASL-2 runs both campaign and audit waves. The runner takes the main worker slot lease,
the two S13 CPU-set leases and the node's own CPU-set lease when it differs from those two.
Wait for the leases to clear before retrying a refusal. TASL-7 runs the proposer with
the addendum's run ID and spec digest.

| Node | TASL-2 CPUs | Lease under `~/r1_locks/` | Environment | CPU admission | Release route |
|---|---|---|---|---|---|
| `mlgym_titanic` | 12–15 | `cpus-12-15.lock` | `torch312` | Harness list | MLGym |
| `mlgym_metamaze` | 0–3 | `cpus-0-3.lock` | `venv_jax` | Census override | MLGym |
| `gc7rc_etth1` | 16–31 | `cpus-16-31.lock` | `torch312` | Census override | Separate extra task |
| `gc7rc_forestcover` | 4–7 | `cpus-4-7.lock` | `torch312` | Census override | Separate extra task |

The addenda use the main note's K, campaign settings, seed blocks, STOP rules and release
order. Each worker uses three times its own slowest census record as its proposal run budget.
The Student-t assembly uses the signed standard-deviation matching rule.

Under the signed v2 release rows, pass the published expansion specs to the main
`g5_tasl.py assemble` command with a separate `--addendum-spec SPEC` for each node cited
by the release row. MLGym enters the main T1 output. Each 1GC node has separate
`extra_tasks/<node>/` outputs under both assembly roots.

For the D6 gate-noise record, call `g5_noise.derive` with the exact main spec,
the signed train/dev row and the same `addendum_paths`. The record includes the
MLGym expansion nodes. The two 1GC nodes stay in their separate assembly outputs.
