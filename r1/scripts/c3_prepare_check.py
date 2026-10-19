"""Write prepare.json for the C3 sweep launcher (accepted environmental failures only).

Usage: c3_prepare_check.py BATCH HARNESS_RC PAPER_RC PAPER_HEAD HARNESS_PIN SKIPPED
AI-assisted (Claude); ENGINEERING_ONLY.
"""
import json
import re
import sys
from pathlib import Path

# Same environmental set as the rerun-2 launcher (PLAN §10 exceptions of 12 and 14 Oct
# and the generated-report / unvendored claw-code tests documented in STATUS).
ACCEPTED = [
    "tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_cli_passes_on_real_campaigns",
    "tests/test_artifact_completeness_and_manifest.py::TestBuildManifest::test_all_referenced_files_exist",
    "tests/test_artifact_completeness_and_manifest.py::TestGenerateManifestCLI::test_cli_reports_all_files_exist",
    "tests/test_kdd_paper_sections.py::test_chunk_4_1_related_work_acceptance",
    "tests/test_kdd_paper_sections.py::test_chunk_4_2_system_design_acceptance",
    "tests/test_kdd_paper_sections.py::test_chunk_4_3_experiments_acceptance",
    "tests/test_kdd_paper_sections.py::test_chunk_4_4_results_order_and_artifact_links",
    "tests/test_kdd_paper_sections.py::test_chunk_4_5_discussion_acceptance",
    "tests/test_legacy_noop_skip.py",
    "tests/stage2/test_stage2_control_plane.py::TestClawWorkerExtraction::test_claw_worker_deterministic_constant_patch_runs_without_llm",
    "tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_checked_in_report_contains_all_plan_campaigns",
]


def failures(log):
    return [m.group(1) for m in (re.match(r"^(?:FAILED|ERROR)\s+(\S+)", l.strip()) for l in log.splitlines()) if m]


def summary(log):
    for line in reversed(log.splitlines()):
        if re.search(r"\d+ (passed|failed|error)", line):
            return line.strip()
    return "(no summary line)"


def main():
    batch, harness_rc, paper_rc, paper_head, pin, skipped = sys.argv[1:7]
    batch = Path(batch)
    harness_log = (batch / "harness_tests.log").read_text(errors="replace")
    paper_log = (batch / "paper_tests.log").read_text(errors="replace")
    h_fail = failures(harness_log)
    unexpected = [f for f in h_fail if f not in ACCEPTED]
    if int(harness_rc) != 0 and not h_fail:
        unexpected.append(f"harness suite exited {harness_rc} with no parsed failures")
    if int(paper_rc) != 0:
        unexpected += [f"r1-test: {f}" for f in (failures(paper_log) or [f"exited {paper_rc}"])]
    payload = {"batch": str(batch), "paper_head": paper_head, "harness_head": pin,
               "suites_skipped_dryrun": skipped == "1",
               "harness_tests": {"returncode": int(harness_rc), "summary": summary(harness_log),
                                 "failures": h_fail, "unexpected": unexpected},
               "r1_tests": {"returncode": int(paper_rc), "summary": summary(paper_log)},
               "accepted_failures": ACCEPTED, "unexpected": unexpected, "ok": not unexpected}
    (batch / "prepare.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"ok": payload["ok"], "unexpected": unexpected}))


if __name__ == "__main__":
    main()
