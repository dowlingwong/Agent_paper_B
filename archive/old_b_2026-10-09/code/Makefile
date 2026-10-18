# Legacy Paper B code (old route), moved here from the repository root on
# 18 Oct 2026 (RUNBOOK 0.1). Read-only history: route R1 (r1/) imports none of it.
# Only the test targets are kept runnable. The old manuscript, smoke, release
# and launch-validator targets are not maintained; see the root Makefile in git
# history (before 18 Oct 2026) for them.
#
#   make -C archive/old_b_2026-10-09/code test PYTHON=/path/to/python3.13
#
# Needs Python 3.11+ (StrEnum) and the pins in requirements.lock.

PYTHON ?= python3
SCAFFOLD_SRC := experiment_scaffold/src

.PHONY: test test-control test-release test-standalone

test: test-control test-release test-standalone

test-control:
	PYTHONPATH=$(SCAFFOLD_SRC) $(PYTHON) -m unittest discover -s tests/control -p 'test_*.py'

test-release:
	$(PYTHON) -m unittest discover -s tests/release -p 'test_*.py'

test-standalone:
	$(PYTHON) -m unittest discover -s tests/standalone -p 'test_*.py'
