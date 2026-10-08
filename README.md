# Paper B — when should an executor agent spend its one verification

This is the standalone repository for Paper B (ICML 2027 target). It was copied
from the joint Paper A/B repository `agent-checkpoint-intervention` at snapshot
`S = 4154f153` (7 October 2026); see [PROVENANCE.md](PROVENANCE.md) for the path
map, the files that differ from S and the licences.

The paper is a **research draft**. There is no real-agent experimental result in
this repository. The analysis side runs on CPU; the live Pi-backed lane is not
built yet (see [docs/paper_split/OPEN_ITEMS.md](docs/paper_split/OPEN_ITEMS.md)).

## Layout

- `papers/paper_b/` — manuscript (ICML 2026 development kit).
- `protocols/paper_b/` — contract v1/v2/v3, launch validator, design decisions.
- `experiments/paper_b/` — engineering smoke and CPU fixtures.
- `experiment_scaffold/src/causal_branch/control/` — B's controller, allocator,
  evaluator, configurator scaffold and governance ledger.
- `tests/control/`, `tests/release/`, `tests/standalone/` — the test suites.
- `third_party/pi/` — the vendored Pi source tree (MIT; see PROVENANCE).

## Environment

Python 3.11+ (the repository pins 3.13.4 in `.python-version`). The locked test
dependencies are in `requirements.lock`. A virtual environment outside the
repository is recommended:

```sh
uv venv --python 3.13 .venv
uv pip sync --python .venv/bin/python requirements.lock
```

## Checks

```sh
make test              # tests/control, tests/release, tests/standalone
make smoke-b           # 11/11 engineering checks (ENGINEERING_ONLY)
make paper-b           # build the manuscript, verify, anonymity check
make release-b         # build the allowlisted release package
make check-release-b   # verify the package in a clean directory
```

The launch validator refuses a draft contract:

```sh
python protocols/paper_b/launch_validator.py --contract protocols/paper_b/contract_v3.yaml \
  --phase qualification --lane one_step --for-launch
```

## Rewriting tracked files

`make check-release-b`, `make paper-b` and `make smoke-b` write into paths that
are tracked at S: `release/check_release_b.json`, the manuscript build products
and `results/paper_b/smoke_latest/`. Until the targets write elsewhere, restore
the inherited bytes afterwards:

```sh
git checkout -- release/check_release_b.json results/paper_b/smoke_latest papers/paper_b/main.pdf
```

`make release-b` requires a clean tree and writes `release/paper_b/`, which is
ignored and not tracked.
