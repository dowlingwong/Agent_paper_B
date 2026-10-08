LATEXMK := latexmk
TARGET  := main

PYTHON  ?= $(shell test -x ../../.venv/bin/python && echo ../../.venv/bin/python || echo python3)

.PHONY: pdf verify anonymity-check smoke clean

pdf:
	$(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error -file-line-error $(TARGET).tex

verify: pdf
	@! grep -E "LaTeX Error|Undefined control sequence|Citation .* undefined|Reference .* undefined|There were undefined references|multiply.defined|Cref reference format|No file .*\.bbl" $(TARGET).log
	@echo "verify: clean"

# B is a research draft; the anonymity audit uses the ICML-aware script copied
# into this repository from Paper A at the split snapshot.
anonymity-check:
	sh scripts/check_anonymity.sh --mode submission

# Engineering-only smoke path: closed test workload through the B schema,
# learner and evaluator.  It never touches real-agent data or credentials and
# reports ENGINEERING_ONLY.
smoke: python-check
	$(PYTHON) ../../experiments/paper_b/smoke_b.py --output ../../results/paper_b/smoke_latest

.PHONY: python-check
python-check:
	@$(PYTHON) -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' \
	  || { echo "this target requires Python 3.11+"; exit 1; }

clean:
	$(LATEXMK) -C
