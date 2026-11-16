"""Offline guard tests: no real Slurm commands are run."""
import datetime as dt
import hashlib
import io
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
        self.plan.write_text("## 10. Decisions\n### 4 November 2026 — author\n| ID | Author decision |\n|---|---|\n| R1-HOREKA-AGENT-SUBMIT | approved |\n| R1-HOREKA-UNIFIED-SUBMISSION | approved |\n")
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

    def test_dated_unique_nonempty_plan_row_only(self):
        row = 'R1-HOREKA-AGENT-SUBMIT'
        prefix = '## 10. Decisions\n### 4 November 2026 — author\n'
        table = '| ID | Author decision |\n|---|---|\n'
        decision = '| ' + row + ' | yes |\n'
        bad = [
            '## 10. Decisions\n### Undated\n' + table + decision,
            '## 11. Other\n### 4 November 2026\n' + table + decision,
            prefix + 'Mention ' + row + ' in prose.\n',
            prefix + decision,
            prefix + table + '| ' + row + ' | |\n',
            prefix + table + decision + decision,
            prefix + table + '| ' + row + '-FAKE | yes |\n',
            prefix + '```markdown\n' + table + decision + '```\n',
            prefix + '~~~\n' + table + decision + '~~~\n',
            prefix + '<!--\n' + table + decision + '-->\n',
            prefix + '<div>\n' + table + decision + '</div>\n',
            prefix + '    ' + table.replace('\n', '\n    ') + decision,
            prefix + '| ID | Proposed option |\n|---|---|\n' + decision,
            '## 10. Decisions\n### 31 February 2026 — author\n' + table + decision,
        ]
        for content in bad:
            with self.subTest(content=content):
                self.plan.write_text(content)
                self.assertFalse(c.plan_has_row(self.plan, row)[0])
        self.plan.write_text(prefix + table + decision)
        self.assertTrue(c.plan_has_row(self.plan, row)[0])
        for row_id in ('R1-HOREKA-AGENT-SUBMIT', 'R1-HOREKA-UNIFIED-SUBMISSION'):
            self.assertTrue(c.plan_has_row(c.DEFAULT_PLAN, row_id)[0])

    def test_invalid_thresholds_and_configuration_roots_fail_closed(self):
        original = json.loads(c.DEFAULT_CONFIG.read_text())
        path = Path(self.tmp.name) / 'config.json'
        for value in (float('nan'), float('inf'), -1, 0, '300', True):
            payload = json.loads(json.dumps(original))
            payload['budget_stop_gpu_h']['value'] = value
            path.write_text(json.dumps(payload))
            with self.assertRaises(c.Hk2Error): c.load_config(path)
        for key, value in [('t_max_hours', float('inf')), ('query_min_interval_s', 59),
                           ('max_outstanding', 91), ('max_outstanding', True)]:
            payload = json.loads(json.dumps(original))
            payload[key]['value'] = value
            path.write_text(json.dumps(payload))
            with self.assertRaises(c.Hk2Error): c.load_config(path)
        payload = json.loads(json.dumps(original))
        payload['results_root']['value'] = self.tmp.name
        path.write_text(json.dumps(payload))
        with self.assertRaisesRegex(c.Hk2Error, 'canonical shared project state root'):
            c.load_config(path)

    def test_same_root_across_different_config_files(self):
        original = json.loads(c.DEFAULT_CONFIG.read_text())
        first, second = Path(self.tmp.name) / 'a.json', Path(self.tmp.name) / 'b.json'
        first.write_text(json.dumps(original))
        second.write_text(json.dumps(original))
        one, two = c.load_config(first), c.load_config(second)
        self.assertEqual(c.records_dir(one) / 'query.lock', c.records_dir(two) / 'query.lock')
        self.assertEqual(c.records_dir(one) / 'observed_jobs.json', c.records_dir(two) / 'observed_jobs.json')

    def test_status_observation_survives_delayed_accounting(self):
        live = [{'job_id': '27', 'partition': 'cpu', 'state': 'RUNNING', 'time_limit_s': 3600,
                 'gpus': 0, 'qos': 'normal', 'name': 'external'}]
        with patch.object(c, 'load_config', return_value=self.config), \
             patch.object(c, 'query_snapshot', return_value=(live, [])):
            self.assertEqual(status.main([]), 0)
        with self.assertRaises(c.AccountingPending):
            self.guard()
        self.guard(accounted=[{'job_id': '27', 'state': 'COMPLETED', 'elapsed_s': 100, 'gpus': 0}])

    def test_squeue_observation_survives_sacct_failure(self):
        def fake_query(argv):
            if argv[0] == 'squeue':
                return subprocess.CompletedProcess(argv, 0, '28|cpu|RUNNING|01:00:00||normal|job\n', '')
            return subprocess.CompletedProcess(argv, 1, '', 'temporarily unavailable')
        with patch.object(c, 'current_user', return_value='fixture'):
            with self.assertRaisesRegex(c.Hk2Error, 'sacct failed'):
                c.query_snapshot(self.config, runner=fake_query)
        with self.assertRaises(c.AccountingPending):
            self.guard()
        self.guard(accounted=[{'job_id': '28', 'state': 'COMPLETED', 'elapsed_s': 100, 'gpus': 0}])

    def test_copyback_deadline_order_and_status(self):
        payload = json.loads(c.DEFAULT_CONFIG.read_text())
        payload['copyback_D']['value'] = '2026-11-20T19:00:00+01:00'
        path = Path(self.tmp.name) / 'bad-order.json'
        path.write_text(json.dumps(payload))
        with self.assertRaisesRegex(c.Hk2Error, 'must be in order'):
            c.load_config(path)
        self.assertEqual(status.copyback_state(self.config, dt.datetime(2026, 11, 19, tzinfo=dt.timezone.utc)), 'not_due')
        self.assertEqual(status.copyback_state(self.config, dt.datetime(2026, 11, 20, 20, tzinfo=dt.timezone.utc)), 'due')
        self.assertEqual(status.copyback_state(self.config, dt.datetime(2026, 11, 21, 18, tzinfo=dt.timezone.utc)), 'overdue')
        output = io.StringIO()
        with patch.object(c, 'load_config', return_value=self.config), \
             patch.object(c, 'query_snapshot', return_value=([], [])), \
             patch.object(c, 'utc_now', return_value=dt.datetime(2026, 11, 21, 18, tzinfo=dt.timezone.utc)), \
             patch('sys.stdout', output):
            self.assertEqual(status.main([]), 0)
        self.assertIn('copyback_deadline=2026-11-21T18:00:00+01:00', output.getvalue())
        self.assertIn('copyback_state=overdue', output.getvalue())

    def test_dev_rejects_known_production_phases(self):
        for phase in ('HK3', 'HK4', 'HK4b', 'HK5'):
            with self.subTest(phase=phase):
                with self.assertRaisesRegex(c.Hk2Error, 'production job on dev'):
                    self.guard(dict(self.job, phase=phase, partition='dev-gpu-h100', production=False))
        for phase in ('HK1', 'HK2'):
            with self.subTest(phase=phase):
                self.guard(dict(self.job, phase=phase, partition='dev-gpu-h100', production=False))

    def test_plan_row_and_dev_continuation(self):
        self.guard(inside={"SLURM_JOB_ID": "9", "SLURM_JOB_PARTITION": "cpu"})
        self.plan.write_text("## 10. Decisions\n### 4 November 2026 — author\nThe R1-HOREKA-AGENT-SUBMIT is proposed.\n| ID | Author decision |\n|---|---|\n| R1-HOREKA-UNIFIED-SUBMISSION | approved |\n")
        with self.assertRaises(c.Hk2Error):
            self.guard()
        self.guard(author=True)
        with self.assertRaises(c.Hk2Error):
            self.guard(author=True, inside={"SLURM_JOB_ID": "9", "SLURM_JOB_PARTITION": "cpu"})
        self.plan.write_text("## 10. Decisions\n### 4 November 2026 — author\n| ID | Author decision |\n|---|---|\n| R1-HOREKA-AGENT-SUBMIT | approved |\n| R1-HOREKA-UNIFIED-SUBMISSION | approved |\n")
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

    def test_deadline_blocks_exact_submitted_manifest_and_persists(self):
        directory = c.records_dir(self.config)
        directory.mkdir(parents=True)
        digest = 'a' * 64
        (directory / 'submissions.jsonl').write_text(json.dumps({
            'event': 'submit', 'job_id': '25', 'manifest_sha256': digest, 'phase': 'HK1'}) + '\n')
        deadline = [{'job_id': '25', 'state': 'DEADLINE', 'elapsed_s': 3600, 'gpus': 1}]
        with self.assertRaisesRegex(c.Hk2Error, 'DEADLINE job'):
            c.refuse_deadline_resubmission(self.config, digest, deadline)
        with self.assertRaisesRegex(c.Hk2Error, 'DEADLINE job'):
            c.refuse_deadline_resubmission(self.config, digest, [])
        c.refuse_deadline_resubmission(self.config, 'b' * 64, [])

    def test_deadline_guard_refuses_corrupt_or_conflicting_mapping(self):
        directory = c.records_dir(self.config)
        directory.mkdir(parents=True)
        records = directory / 'submissions.jsonl'
        for content in ('{broken\n', json.dumps({'job_id': '25', 'phase': 'HK1'}) + '\n',
                        '\n'.join(json.dumps({'job_id': '25', 'manifest_sha256': char * 64})
                                  for char in ('a', 'b'))):
            records.write_text(content)
            with self.assertRaises(c.Hk2Error):
                c.refuse_deadline_resubmission(self.config, 'a' * 64, [])

    def test_status_remembers_deadline_even_when_later_snapshot_changes(self):
        record = {'job_id': '25', 'state': 'DEADLINE', 'elapsed_s': 3600, 'gpus': 1}
        c.record_deadline_jobs(self.config, [record])
        c.record_deadline_jobs(self.config, [])
        self.assertEqual(json.loads((c.records_dir(self.config) / 'deadline_jobs.json').read_text()), ['25'])

    def test_enabled_submit_refuses_deadline_before_fake_sbatch(self):
        manifest = Path(self.tmp.name) / 'job.json'
        manifest.write_text(json.dumps(self.job))
        digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
        directory = c.records_dir(self.config)
        directory.mkdir(parents=True)
        (directory / 'submissions.jsonl').write_text(json.dumps({
            'event': 'submit', 'job_id': '25', 'manifest_sha256': digest, 'phase': 'HK1'}) + '\n')
        deadline = [{'job_id': '25', 'state': 'DEADLINE', 'elapsed_s': 10, 'gpus': 1}]
        with patch.object(c, 'load_config', return_value=self.config), \
             patch.object(c, 'query_snapshot', return_value=([], deadline)), \
             patch.object(c, 'utc_now', return_value=self.now), \
             patch.object(submit, 'require_submission_readiness'), \
             patch.object(submit.subprocess, 'run') as sbatch:
            self.assertEqual(submit.main([str(manifest), '--plan', str(self.plan), '--submit']), 2)
            sbatch.assert_not_called()

    def test_deadline_persists_when_earlier_guard_stops(self):
        manifest = Path(self.tmp.name) / 'job.json'
        manifest.write_text(json.dumps(self.job))
        digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
        directory = c.records_dir(self.config)
        directory.mkdir(parents=True)
        (directory / 'submissions.jsonl').write_text(json.dumps({
            'event': 'submit', 'job_id': '25', 'manifest_sha256': digest, 'phase': 'HK1'}) + '\n')
        snapshots = [([], [{'job_id': '25', 'state': 'DEADLINE', 'elapsed_s': 10, 'gpus': 1}]),
                     ([], [{'job_id': '25', 'state': 'COMPLETED', 'elapsed_s': 10, 'gpus': 1}])]
        times = [dt.datetime(2026, 11, 20, 12, tzinfo=dt.timezone.utc), self.now]
        with patch.object(c, 'load_config', return_value=self.config), \
             patch.object(c, 'query_snapshot', side_effect=snapshots), \
             patch.object(c, 'utc_now', side_effect=times), \
             patch.object(submit, 'require_submission_readiness'), \
             patch.object(submit.subprocess, 'run') as sbatch:
            self.assertEqual(submit.main([str(manifest), '--plan', str(self.plan), '--submit']), 2)
            self.assertEqual(submit.main([str(manifest), '--plan', str(self.plan), '--submit']), 2)
            sbatch.assert_not_called()

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

    def test_enabled_submit_executes_test_only_and_records_fake_job(self):
        self.v['real_submission_enabled'] = True
        manifest = Path(self.tmp.name) / 'enabled.json'
        manifest.write_text(json.dumps(self.job))
        calls = []
        def fake_sbatch(argv, **kwargs):
            calls.append((argv, kwargs['env']))
            return subprocess.CompletedProcess(argv, 0,
                'estimate' if '--test-only' in argv else '551;cluster\n', '')
        with patch.object(c, 'load_config', return_value=self.config), \
             patch.object(c, 'query_snapshot', return_value=([], [])), \
             patch.object(c, 'utc_now', return_value=self.now), \
             patch.object(submit.subprocess, 'run', side_effect=fake_sbatch), \
             patch.dict(os.environ, {'SBATCH_BAD': 'x', 'SLURM_BAD': 'x', 'TOKEN': 'x'}):
            self.assertEqual(submit.main([str(manifest), '--plan', str(self.plan), '--submit']), 0)
        self.assertEqual(len(calls), 2)
        self.assertIn('--test-only', calls[0][0])
        self.assertIn('--parsable', calls[1][0])
        for _, env in calls:
            self.assertNotIn('SBATCH_BAD', env)
            self.assertNotIn('SLURM_BAD', env)
            self.assertNotIn('TOKEN', env)
        directory = c.records_dir(self.config)
        events = [json.loads(line) for line in (directory / 'submissions.jsonl').read_text().splitlines()]
        self.assertEqual([x['event'] for x in events], ['test-only', 'submit'])
        self.assertEqual(events[-1]['job_id'], '551')
        self.assertFalse((directory / 'SUBMISSION_UNCERTAIN').exists())
        self.assertEqual(len(list((directory / '_to_delete').glob('submitted-551-*'))), 1)

    def test_wait_for_accounting_of_previously_observed_user_job(self):
        running = [{'job_id': '22', 'partition': 'cpu', 'state': 'RUNNING', 'time_limit_s': 3600,
                    'gpus': 0, 'qos': 'normal'}]
        self.guard(outstanding=running)
        with self.assertRaisesRegex(c.Hk2Error, 'waiting for terminal accounting'):
            self.guard(accounted=[{'job_id': '22', 'state': 'RUNNING', 'elapsed_s': 100, 'gpus': 0}])
        with self.assertRaisesRegex(c.Hk2Error, 'waiting for terminal accounting'):
            self.guard()
        self.guard(accounted=[{'job_id': '22', 'state': 'COMPLETED', 'elapsed_s': 100, 'gpus': 0}])

    def test_enabled_wait_does_not_call_sbatch(self):
        self.v['real_submission_enabled'] = True
        directory = c.records_dir(self.config)
        directory.mkdir(parents=True)
        (directory / 'observed_jobs.json').write_text('["22"]')
        manifest = Path(self.tmp.name) / 'waiting.json'
        manifest.write_text(json.dumps(self.job))
        with patch.object(c, 'load_config', return_value=self.config), \
             patch.object(c, 'query_snapshot', return_value=([], [])), \
             patch.object(c, 'utc_now', return_value=self.now), \
             patch.object(submit.subprocess, 'run') as runner:
            self.assertEqual(submit.main([str(manifest), '--plan', str(self.plan), '--submit']), 75)
        runner.assert_not_called()

    def test_enabled_submission_queries_fake_user_slurm_and_accounts_budget(self):
        self.v['real_submission_enabled'] = True
        manifest = Path(self.tmp.name) / 'query.json'
        manifest.write_text(json.dumps(self.job))
        query_calls, submit_calls = [], []
        def fake_query(argv):
            query_calls.append(argv)
            if argv[0] == 'squeue':
                return subprocess.CompletedProcess(argv, 0,
                    '88|gpu-h100|RUNNING|01:00:00|gpu:1|normal|other-user-job\n', '')
            return subprocess.CompletedProcess(argv, 0,
                '88|other-user-job|gpu-h100|RUNNING|1800|gres/gpu=1|x|Unknown|60\n', '')
        real_snapshot = c.query_snapshot
        def snapshot(config):
            return real_snapshot(config, runner=fake_query)
        def fake_sbatch(argv, **kwargs):
            submit_calls.append(argv)
            return subprocess.CompletedProcess(argv, 0,
                'estimate' if '--test-only' in argv else '552\n', '')
        with patch.object(c, 'load_config', return_value=self.config), \
             patch.object(c, 'query_snapshot', side_effect=snapshot), \
             patch.object(c, 'utc_now', return_value=self.now), \
             patch.object(submit.subprocess, 'run', side_effect=fake_sbatch), \
             patch.dict(os.environ, {'USER': 'fixture'}, clear=False):
            self.assertEqual(submit.main([str(manifest), '--plan', str(self.plan), '--submit']), 0)
        self.assertEqual([x[0] for x in query_calls], ['squeue', 'sacct'])
        self.assertTrue(all(x[1:3] == ['-u', 'fixture'] or x[1:4] == ['-X', '-u', 'fixture'] for x in query_calls))
        self.assertEqual(len(submit_calls), 2)
        entry = json.loads((c.records_dir(self.config) / 'submissions.jsonl').read_text().splitlines()[0])
        self.assertEqual(entry['budget']['used_gpu_h'], .5)
        self.assertEqual(entry['budget']['reserved_gpu_h'], 1)
        self.assertEqual(entry['budget']['new_gpu_h'], 1)

    def test_unified_submission_decision_does_not_enable_unqualified_submission(self):
        """STOP precedes row parsing; this fixture does not validate PLAN authority."""
        self.plan.write_text(
            '## 10. Decisions\n'
            '| R1-HOREKA-AGENT-SUBMIT | approved |\n'
            '| R1-HOREKA-UNIFIED-SUBMISSION | adopted |\n'
        )
        manifest = Path(self.tmp.name) / 'job.json'
        manifest.write_text(json.dumps(self.job))
        # Neither an author invocation nor a continuation changes readiness.
        for flags, job_env in [([], {}), (['--author'], {}),
                               ([], {'SLURM_JOB_ID': '42', 'SLURM_JOB_PARTITION': 'cpu'})]:
            with self.subTest(flags=flags, job_env=job_env), \
                 patch.object(c, 'load_config', return_value=self.config), \
                 patch.object(c, 'query_snapshot') as query, \
                 patch.object(submit.subprocess, 'run') as runner, \
                 patch.dict(os.environ, job_env, clear=True):
                self.assertEqual(submit.main([str(manifest), '--plan', str(self.plan), '--submit'] + flags), 2)
                query.assert_not_called()
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
