# Mac retained DRYRUN FixtureWorker probe — draft, 7 November 2026

AI-assisted (Codex). **DRAFT; not run or independently reviewed.** This is a one-shot local ENGINEERING_ONLY probe of the actual `FixtureWorker.run_trial` and actual DRYRUN fixture snapshot publisher, using only synthetic text and a fake result object. It is not a model, scientific experiment, full campaign, host access, or B1 launch. Exact script `mac_fixture_worker_probe_20261107/probe.py` SHA-256 `eaacf1e09fd6d3ba71853136404898a2e4283a9e33db5e6b5fe5e88b9e66b33e`.

The script verifies and loads three committed sources: `r1/exam/campaign.py` SHA-256 `36258a4335d8fb437fae463c31f18acf65b762a87bee87c5ea5d2042299f5b38`, `r1/c3/features.py` SHA-256 `08822bc9c1f7c846b26a449e891a7f48049e2b1a5b74a134ad3cf677d9885579`, and `r1/exam/b1_state_preserve.py` SHA-256 `c1deccb0795d5b30643a7b50b62fceed7eecb2ca440cb22005c7491d9d03942c`. It AST-extracts the unchanged actual `FixtureWorker`, `DryrunFixturePreservationStop`, `fixture_metric`, `_pattern`, `_loose` and `apply_edit` definitions, and executes the actual publisher module bytes under stub package bindings. `WorkerResult` is an inert fake container. This deliberately excludes unrelated real campaign imports, parent/guardian, harness and server behavior.

The probe creates a new exclusive private `/private/tmp/paper_b_mac_fixture_probe_20261107_2d823ecb5a174b5d` directory and `fixture.py`, then calls the extracted worker twice for `RATE = 1`→`2`→`3`. It checks the actual synthetic metrics, three distinct inode/content identities, and both old versions retained under `_to_delete`; all files and directories are retained. It calls the publisher's Darwin EXCL/SWAP and fsync code. It never intentionally unlinks or truncates an existing file. A partial write or failure after rename may leave a partially completed but retained scene; report STOP, do not retry, remove or signal. Closing failures can mask earlier errors; inspect complete output. This is a cooperative stable-path, single-writer test, not crash, concurrency or STOP qualification.

Before execution, require a fresh independent review of the exact script, source hashes, Python import/AST binding, capture command, all filesystem operations and errors. The operator must use a clean committed checkout, verify all four SHA values, check `/private` and `/private/tmp` owner/type/sticky, disk availability, intended `python3`, and verify the fixed root and capture are absent (including symlinks). Any unexpected state is STOP and no execution. Use this exact single invocation from the reviewed checkout under `/bin/bash`, with no terminal:

```bash
set -C
capture=/private/tmp/paper_b_mac_fixture_capture_20261107_2d823ecb5a174b5d.txt
if exec 3>"$capture"; then :; else
  printf '%s\n' 'STOP: capture exists or cannot be created' >&2
  exit 1
fi
if python3 -I -S -B docs/r1/proposals/mac_fixture_worker_probe_20261107/probe.py >&3 2>&1; then
  task_probe_status=0
else
  task_probe_status=$?
fi
if printf '\nPROBE_EXIT_STATUS=%s\n' "$task_probe_status" >&3; then :; else
  printf '%s\n' 'STOP: cannot record probe status; retain scene' >&2
  exit 1
fi
if exec 3>&-; then :; else
  printf '%s\n' 'STOP: capture close failed; retain scene' >&2
  exit 1
fi
if shasum -a 256 "$capture"; then :; else
  printf '%s\n' 'STOP: capture hash failed; retain scene' >&2
  exit 1
fi
exit "$task_probe_status"
```

Record UTC, exact HEAD, interpreter, source/script/capture hashes and complete output. Independent result review must confirm the version identities and bytes before reliance. Any collision, nonzero status, incomplete output, signal, capture failure or ambiguity is STOP; retain the scene and do not retry. The result would not establish a complete B1 campaign, true harness guard/restore, `WorkerResult` semantics, model/worker determinism, real Linux behavior, async STOP, crash durability, full test-suite preservation, or author approval. Local code and AST syntax were checked; this script and actual publisher were **not executed**.
