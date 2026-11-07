"""Pure fake-environment tests: no Slurm, process, file, model or GPU work."""
import unittest

from r1.scripts.hk2.hk2_slurm_allocation import AllocationError, job_visible_gpu


class TestJobVisibleGPU(unittest.TestCase):
    def test_slurm_global_id_is_not_visible_index(self):
        got = job_visible_gpu({'CUDA_VISIBLE_DEVICES': '0', 'SLURM_JOB_GPUS': '3'}, 0)
        self.assertEqual(got['selected_cuda_visible_device'], '0')
        self.assertEqual(got['slurm_job_gpus'], '3')
        self.assertFalse(got['device_identity_verified'])

    def test_second_visible_selector_is_used_unchanged(self):
        env = {'CUDA_VISIBLE_DEVICES': 'GPU-abc,MIG-def', 'SLURM_JOB_GPUS': '3,7'}
        got = job_visible_gpu(env, 1)
        self.assertEqual(got['selected_cuda_visible_device'], 'MIG-def')
        self.assertEqual(got['cuda_visible_devices'], env['CUDA_VISIBLE_DEVICES'])

    def test_bad_environment_and_index_are_refused(self):
        valid = {'CUDA_VISIBLE_DEVICES': '0,1', 'SLURM_JOB_GPUS': '3,7'}
        for bad in (None, {}, {'CUDA_VISIBLE_DEVICES': '', 'SLURM_JOB_GPUS': '3'},
                    {'CUDA_VISIBLE_DEVICES': '0', 'SLURM_JOB_GPUS': ''},
                    {'CUDA_VISIBLE_DEVICES': '0,0', 'SLURM_JOB_GPUS': '3,7'},
                    {'CUDA_VISIBLE_DEVICES': '0,00', 'SLURM_JOB_GPUS': '3,7'},
                    {'CUDA_VISIBLE_DEVICES': '0,1 2', 'SLURM_JOB_GPUS': '3,7'},
                    {'CUDA_VISIBLE_DEVICES': '0, 1', 'SLURM_JOB_GPUS': '3,7'},
                    {'CUDA_VISIBLE_DEVICES': '-1', 'SLURM_JOB_GPUS': '3'},
                    {'CUDA_VISIBLE_DEVICES': '-2', 'SLURM_JOB_GPUS': '3'},
                    {'CUDA_VISIBLE_DEVICES': '0\n1', 'SLURM_JOB_GPUS': '3'},
                    {'CUDA_VISIBLE_DEVICES': '0', 'SLURM_JOB_GPUS': '3\n7'}):
            with self.subTest(environment=bad), self.assertRaises(AllocationError):
                job_visible_gpu(bad, 0)
        for index in (-1, 2, True, '0'):
            with self.subTest(index=index), self.assertRaises(AllocationError):
                job_visible_gpu(valid, index)


if __name__ == '__main__':
    unittest.main()
