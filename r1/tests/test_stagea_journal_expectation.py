"""In-memory regression for Stage A journal expectation binding; no host I/O."""
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from r1.exam import stage_a
from r1.exam import cache_runtime, cache_order, cache_proc, cache_false, cache_nongen, fit
from r1.exam import campaign, runtime
from r1.scripts import llama_server_instance
from autoresearch.llm import providers


class JournalExpectationTest(unittest.TestCase):
    def _check(self, dryrun):
        expected = [('/apply-template', {'kind': 'fixed'}),
                    ('/apply-template', {'kind': 'frozen'})]
        job = {'config': {'dryrun': dryrun, 'server': {'binary': '/synthetic/server'},
                          'prompts': '/synthetic/prompts', 'prompts_sha256': 'hash'},
               'candidate': {'id': 'synthetic', 'runtime': {'model_path': '/synthetic/model',
                             'model_config_path': '/synthetic/config', 'model_config_sha256': 'hash'},
                             'quant_source': {'size_bytes': 1},
                             'thinking_policy': {'mode': 'off'}},
               'out': '/synthetic/out', 'ctx': 32768, 'port': 1,
               'cache_identity': {'synthetic': True}}
        result = {'nongen_expected': expected, 'failure_classes': [], 'passed': True}
        def read_text(path, *args, **kwargs):
            if str(path) == '/synthetic/job':
                return json.dumps(job)
            if str(path) == '/synthetic/config':
                return '{}'
            return ''  # The validator itself is stubbed: journal bytes are not exercised here.
        recorder = SimpleNamespace(close=lambda: None)
        with patch.object(stage_a, 'require_d3_evidence'), \
             patch.object(Path, 'read_text', read_text), \
             patch.object(cache_runtime, 'authorize_cooperative_stagea'), \
             patch.object(cache_runtime, 'reject_unverified_cold'), \
             patch.object(cache_runtime, 'validate_worker_binding'), \
             patch.object(llama_server_instance, 'LlamaServerInstance', return_value=SimpleNamespace(url='fake', alias='synthetic')), \
             patch.object(stage_a, 'load_prompts', return_value=[{'synthetic': True}]), \
             patch.object(stage_a, 'run_stage_a', return_value=result), \
             patch.object(cache_proc, 'sample_llama_server_processes'), \
             patch.object(cache_false, 'FalseCallRecorder', return_value=recorder), \
             patch.object(cache_nongen, 'NonGenerationRecorder', return_value=recorder), \
             patch.object(providers, 'manager_response_format', return_value={'synthetic': True}), \
             patch.object(runtime, 'gpu_sample'), \
             patch.object(cache_order, 'validate_local_order', return_value={'passed': True}) as validator, \
             patch.object(campaign, 'write_json') as writer, \
             patch.object(stage_a, 'digest_file', return_value='hash'), \
             patch.object(fit, 'estimate', return_value={'estimated_admissible': True}):
            stage_a.main(['--job', '/synthetic/job'])
        self.assertIs(validator.call_args.kwargs['nongen_expected'], expected)
        self.assertIs(writer.call_args.args[1], result)

    def test_dryrun_uses_actual_expectation(self):
        self._check(True)

    def test_nondryrun_keeps_actual_expectation(self):
        self._check(False)


if __name__ == '__main__':
    unittest.main()
