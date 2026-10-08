# Root Makefile — Paper B repository entry points.
#
# The manuscript build lives in papers/paper_b/Makefile and is delegated with
# `-C papers/paper_b`.  Repo-level concerns (control tests, the import
# allowlist, the release package) live here.  Never invoke a bare `python3`:
# the scaffold needs 3.11+ (StrEnum).

PYTHON ?= $(shell test -x .venv/bin/python && echo .venv/bin/python || echo python3)
SCAFFOLD_SRC := experiment_scaffold/src

.PHONY: paper-b smoke-b release-b check-release-b test test-control test-release test-standalone

# Build the manuscript, run the verify pass and the anonymity audit.
paper-b:
	$(MAKE) -C papers/paper_b pdf verify anonymity-check PYTHON=$(PYTHON)

# Engineering-only smoke path: closed synthetic workload through the B schema,
# learner and evaluator.  Never a pilot and never a real-agent result.  The
# tracked smoke_latest directory is rewritten; restore it with
# `git checkout -- results/paper_b/smoke_latest`.
smoke-b:
	rm -rf results/paper_b/smoke_latest
	PYTHONPATH=$(SCAFFOLD_SRC) $(PYTHON) experiments/paper_b/smoke_b.py --output results/paper_b/smoke_latest

# Build the B release package from the allowlist.  Requires a clean tree.
release-b:
	$(PYTHON) scripts/make_release.py

# Verify the built package in a clean directory: manifest provenance, no Paper A
# or measurement-core paths, PDF build, smoke and the control tests.  A host
# without latexmk fails the check unless ALLOW_NO_PDF=1 is given.
check-release-b:
	$(PYTHON) scripts/check_release_independence.py $(if $(ALLOW_NO_PDF),--allow-no-pdf,)

test: test-control test-release test-standalone

test-control:
	PYTHONPATH=$(SCAFFOLD_SRC) $(PYTHON) -m unittest discover -s tests/control -p 'test_*.py'

test-release:
	$(PYTHON) -m unittest discover -s tests/release -p 'test_*.py'

test-standalone:
	$(PYTHON) -m unittest discover -s tests/standalone -p 'test_*.py'
