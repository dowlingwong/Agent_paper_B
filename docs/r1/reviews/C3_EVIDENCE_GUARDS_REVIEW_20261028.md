# C3 evidence guards: independent review, 28 October 2026

AI-assisted review (OpenAI Codex). Code-Commit: `9bab3d6f6681c9f0dcc2594ef42933cbc2eb93e9`. Verdict: **BLOCK / NOT ACCEPTED FOR B.2 LAUNCH**.

The independent reviewers inspected runner authorization and batch identity, sidecar/path mapping, original Git blob verification, published author-decision checks, audit population and cache isolation, environment and code provenance, first-failure STOP, seed journals, scratch preservation, running resource checks, and evidence training boundaries. The operator's combined relevant test run passed 81 tests with one skipped; the independent audit review passed 40 with two skipped. Runner isolated checks passed, but two process-identification tests also fail on the unmodified Mac baseline; Linux validation remains open.

The original preparation record does not bind a complete historical runtime freeze. It records Python 3.13.15, NumPy 2.4.4, pandas 3.0.3 and scikit-learn 1.8.0, and refers to a shared venv. Full same-environment verification is NOT CHECKABLE; a present-day freeze is not proof of launch-time versions. The evidence guard is designed to STOP in that situation. The author has been asked whether to continue searching for historical records or consider a separately reviewed exception.

The joint-seed protocol uses seeds 7006–7010 for the audited task's model fitting and split as well as evaluation. The author has been asked whether that task-level use is compatible with the prohibition on evidence training and selection. Neither the seed set nor joint-seed semantics were changed.

Unlabelled or stripped ordinary dictionaries cannot be reliably identified as evidence by a marker-based downstream boundary. Thus global training/selection isolation is NOT CHECKABLE without a trusted, provenance-bound label-only input boundary. The guards conservatively reject identifiable evidence rows at currently unsupported training entrances. They must not be represented as a proof of global isolation or as acceptance of subsequent training.

The classification and pure-move commits are currently local: an automatic approval review rejected the attempted push to main, stating that the specific push was not explicitly authorized and code repair/review should be completed first. Until an authorized push and fresh remote verification, published-decision guards correctly reject B.2. No B.2 audit was launched; preserved source records were not edited.
