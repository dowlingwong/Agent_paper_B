"""Offline guard tests: no real Slurm commands are run."""
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "hk2"))
import hk2_common as c
import hk2_submit as submit
import hk2_status as status


class ToolsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = c.load_config()
        self.v = self.config["values"]
        self.v["results_root"] = self.tmp.name
        self.v["stop_marker"] = str(Path(self.tmp.name) / "STOP")
        self.plan = Path(self.tmp.name) / "PLAN.md"
        self.plan.write_text("## 10. Decisions\n| R1-HOREKA-AGENT-SUBMIT | approved |\n")
        self.now = dt.datetime(2026, 11, 5, tzinfo=dt.timezone.utc)
        self.job = {"schema": "hk2_job/v1", "account": self.v["account"], "partition": "gpu-h100",
                    "time": "01:00:00", "mem": "10G", "cpus": 8, "gpus": 1,
                    "phase": "HK1", "kind": "engineering", "production": False,
                    "argv": ["python3", "run.py", "hello world"]}

    def guard(self, job=None, outstanding=None, accounted=None, author=False, inside=None, now=None):
        return submit.check_guards(job or self.job, self.config, self.plan, outstanding or [], accounted or [],
                                   now or self.now, author, {} if inside is None else inside)

    def test_typed_and_generic_tres(self):
        self.assertEqual(c.gpus_from_tres("gres/gpu:h100=2"), 2)
        self.assertEqual(c.gpus_from_tres("gres/gpu=2,gres/gpu:h100=2"), 2)
        with self.assertRaises(c.Hk2Error):
            c.gpus_from_tres("gres/gpu=1,gres/gpu:h100=2")
        with self.assertRaises(c.Hk2Error):
            c.gpus_from_tres("gres/gpu:h100=unknown")

    def test_plan_row_and_dev_continuation(self):
        self.guard(inside={"SLURM_JOB_ID": "9", "SLURM_JOB_PARTITION": "cpu"})
        self.plan.write_text("## 10. Decisions\nThe R1-HOREKA-AGENT-SUBMIT is proposed.\n")
        with self.assertRaises(c.Hk2Error):
            self.guard()
        self.guard(author=True)
        with self.assertRaises(c.Hk2Error):
            self.guard(author=True, inside={"SLURM_JOB_ID": "9", "SLURM_JOB_PARTITION": "cpu"})
        self.plan.write_text("## 10. Decisions\n| R1-HOREKA-AGENT-SUBMIT | approved |\n")
        with self.assertRaises(c.Hk2Error):
            self.guard(inside={"SLURM_JOB_ID": "9", "SLURM_JOB_PARTITION": "dev-cpu"})

    def test_budget_and_clock(self):
        self.v["budget_stop_gpu_h"] = 1
        self.assertEqual(self.guard()["total_gpu_h"], 1)
        self.v["budget_stop_gpu_h"] = .99999
        with self.assertRaises(c.Hk2Error): self.guard()
        self.v["budget_stop_gpu_h"] = 300
        with self.assertRaises(c.Hk2Error): self.guard(now=dt.datetime(2026, 11, 20, 12, tzinfo=dt.timezone.utc))
        with self.assertRaises(c.Hk2Error): self.guard(now=dt.datetime(2026, 11, 20, 18, 30, tzinfo=dt.timezone.utc))
        running = [{"job_id":"3", "time_limit_s":14400, "gpus":1}]
        accounted = [{"job_id":"3", "elapsed_s":7200, "gpus":1}]
        self.assertEqual(c.budget_state(running, accounted), {"used_gpu_h":2, "reserved_gpu_h":4})

    def test_dev_shape_and_missing_parameters(self):
        job = dict(self.job, partition="dev-gpu-h100", production=True)
        with self.assertRaises(c.Hk2Error): self.guard(job)
        job = dict(self.job, kind="evidence")
        with self.assertRaises(c.Hk2Error): self.guard(job)
        job = dict(self.job, phase="HK6")
        with self.assertRaises(c.Hk2Error): self.guard(job)
        job = dict(self.job, cpus=33)
        with self.assertRaises(c.Hk2Error): self.guard(job)
        job = dict(self.job); del job["mem"]
        with self.assertRaises(c.Hk2Error): self.guard(job)
        job = dict(self.job, partition="dev-gpu-h100")
        live = [{"partition":"dev-cpu", "qos":"dev"}]
        with self.assertRaises(c.Hk2Error): self.guard(job, outstanding=live)

    def test_manifest_script_quoting_and_controls(self):
        submit.validate_manifest(self.job, self.config)
        script = submit.render_script(self.job, "a" * 64, self.config)
        for text in ("manifest_sha256=" + "a" * 64, "--deadline=", "--signal=B:USR1@600", "'hello world'", "--mem=10G"):
            self.assertIn(text, script)
        with patch.dict(os.environ, {"SBATCH_TEST": "a", "SLURM_JOB_ID": "123", "TOKEN": "secret"}):
            env = submit.scrubbed_environment()
            self.assertNotIn("SBATCH_TEST", env)
            self.assertNotIn("SLURM_JOB_ID", env)
            self.assertNotIn("TOKEN", env)

    def test_uncertain_submission_blocks_new_attempts(self):
        directory = c.records_dir(self.config)
        directory.mkdir(parents=True)
        (directory / "SUBMISSION_UNCERTAIN").write_text("{}")
        with self.assertRaises(c.Hk2Error): self.guard()

    def test_timeout_persists_uncertain_marker(self):
        manifest = Path(self.tmp.name) / "job.json"
        manifest.write_text(json.dumps(self.job))
        calls = []
        def fake_sbatch(argv, **kwargs):
            calls.append(argv)
            self.assertNotIn("SLURM_JOB_ID", kwargs["env"])
            if "--test-only" in argv:
                return subprocess.CompletedProcess(argv, 0, "estimate", "")
            raise subprocess.TimeoutExpired(argv, 1)
        with patch.object(c, "load_config", return_value=self.config), \
             patch.object(c, "query_snapshot", return_value=([], [])), \
             patch.object(c, "utc_now", return_value=self.now), \
             patch.object(submit, "require_submission_readiness"), \
             patch.object(submit.subprocess, "run", side_effect=fake_sbatch):
            self.assertEqual(submit.main([str(manifest), "--plan", str(self.plan), "--submit"]), 2)
        self.assertTrue((c.records_dir(self.config) / "SUBMISSION_UNCERTAIN").exists())
        with self.assertRaises(c.Hk2Error): self.guard()
        self.assertEqual(len(calls), 2)

    def test_ledger_deadline(self):
        record = {"job_id":"25", "name":"x", "partition":"gpu-h100", "state":"DEADLINE", "elapsed_s":3600, "gpus":1}
        path, rows = status.update_ledger(self.config, [], [record])
        self.assertTrue(path.exists())
        self.assertEqual(rows["25"]["resubmit"], "never")
        self.assertEqual(rows["25"]["expected_end"], "yes")
        self.assertEqual(rows["25"]["allocation_gpu_h"], "1.00000000")

    def test_throttle_before_any_query_on_error(self):
        calls = []
        def runner(argv):
            calls.append(argv)
            class Result:
                returncode = 1
                stdout = ""
                stderr = "failed"
            return Result()
        with patch.dict(os.environ, {"USER": "test"}):
            with self.assertRaises(c.Hk2Error): c.query_snapshot(self.config, runner)
            with self.assertRaises(c.Hk2Error): c.query_snapshot(self.config, runner)
        self.assertEqual(len(calls), 1)

    def test_corrupt_throttle_fails_closed(self):
        directory = c.records_dir(self.config)
        directory.mkdir(parents=True)
        (directory / "query_state.json").write_text("not json")
        with self.assertRaises(c.Hk2Error): c.query_snapshot(self.config, lambda _: None)

    def test_missing_accounting_stops_budget_guard(self):
        directory = c.records_dir(self.config)
        directory.mkdir(parents=True)
        (directory / "submissions.jsonl").write_text(json.dumps({"job_id":"44", "phase":"HK1"}) + "\n")
        with self.assertRaises(c.Hk2Error): self.guard()

    def test_cutoff_rechecked_after_test_only(self):
        manifest = Path(self.tmp.name) / "job.json"
        manifest.write_text(json.dumps(self.job))
        calls = []
        def fake_sbatch(argv, **kwargs):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 0, "estimate", "")
        with patch.object(c, "load_config", return_value=self.config), \
             patch.object(c, "query_snapshot", return_value=([], [])), \
             patch.object(c, "utc_now", side_effect=[self.now, self.now, dt.datetime(2026, 11, 20, 12, tzinfo=dt.timezone.utc)]), \
             patch.object(submit, "require_submission_readiness"), \
             patch.object(submit.subprocess, "run", side_effect=fake_sbatch):
            self.assertEqual(submit.main([str(manifest), "--plan", str(self.plan), "--submit"]), 2)
        self.assertEqual(len(calls), 1)

    def test_real_submit_is_disabled_without_even_calling_slurm(self):
        manifest = Path(self.tmp.name) / "job.json"
        manifest.write_text(json.dumps(self.job))
        with patch.object(c, "load_config", return_value=self.config), \
             patch.object(submit.subprocess, "run") as runner:
            self.assertEqual(submit.main([str(manifest), "--plan", str(self.plan), "--submit"]), 2)
        runner.assert_not_called()

    def test_corrupt_submission_journal_fails_closed(self):
        directory = c.records_dir(self.config)
        directory.mkdir(parents=True)
        (directory / "submissions.jsonl").write_text("{broken\n")
        with self.assertRaises(c.Hk2Error): self.guard()

    def test_cutoff_crosses_during_test_only_before_freeze(self):
        self.v["cutoff_C"] = "2026-11-20T13:00:00+01:00"
        self.job["time"] = "02:00:00"
        manifest = Path(self.tmp.name) / "job.json"
        manifest.write_text(json.dumps(self.job))
        before = dt.datetime(2026, 11, 20, 9, 59, 59, tzinfo=dt.timezone.utc)
        after = dt.datetime(2026, 11, 20, 10, 0, 1, tzinfo=dt.timezone.utc)
        calls = []
        def fake_sbatch(argv, **kwargs):
            calls.append(argv)
            return subprocess.CompletedProcess(argv, 0, "estimate", "")
        with patch.object(c, "load_config", return_value=self.config), \
             patch.object(c, "query_snapshot", return_value=([], [])), \
             patch.object(c, "utc_now", side_effect=[before, before, after]), \
             patch.object(submit, "require_submission_readiness"), \
             patch.object(submit.subprocess, "run", side_effect=fake_sbatch):
            self.assertEqual(submit.main([str(manifest), "--plan", str(self.plan), "--submit"]), 2)
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
