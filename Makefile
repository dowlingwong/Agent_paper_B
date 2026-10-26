# Root Makefile — Paper B, route R1 (docs/r1/PLAN.md).
#
# The old-route code, its tests, the vendored Pi tree and the release tooling were
# moved to archive/old_b_2026-10-09/code/ on 18 Oct 2026 (RUNBOOK 0.1); r1/ imports
# none of it. `make legacy-test` still runs those suites from their new location.

# R1 code runs against the harness checkout in $(AR_HARNESS_ROOT) (default: ../autoresearch_harness).
R1_PY ?= python3
LEGACY_PY ?= $(shell test -x .venv/bin/python && echo $(CURDIR)/.venv/bin/python || echo python3)

.PHONY: r1-test r1-e2e legacy-test

r1-test:
	$(R1_PY) -m pytest -q -p no:cacheprovider r1/tests

r1-e2e:
	$(R1_PY) -m r1.e2e

# Legacy suites (old route): 212 control / 6 release / 12 standalone tests. Needs Python 3.11+.
legacy-test:
	$(MAKE) -C archive/old_b_2026-10-09/code test PYTHON=$(LEGACY_PY)

# L6 manuscript: draft builds display placeholders; final builds reject them.
.PHONY: paper paper-final
paper:
	cd papers/r1 && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

paper-final:
	cd papers/r1 && latexmk -pdf -interaction=nonstopmode -halt-on-error -jobname=final -pdflatex='pdflatex %O "\\def\\FinalPaper{1}\\input{%S}"' main.tex
