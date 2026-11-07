"""Parse job-visible GPU selectors for a future J3 runner.

This is an offline environment helper, not device enumeration, occupancy
checking, a slot-allocation policy, an execution-identity verifier, or an
EVIDENCE authorization.  In particular SLURM_JOB_GPUS is recorded as supplied
and never used as an index into CUDA_VISIBLE_DEVICES.
"""


import re


class AllocationError(ValueError):
    pass


def job_visible_gpu(environment, local_index):
    """Select one job-visible CUDA selector and retain the original Slurm value.

    ``local_index`` is a zero-based index within the job-visible selector list,
    supplied by the future scheduler. No placement policy or multiplicity is
    chosen here. Physical device identity must be verified separately in the
    actual job; the values returned here are only environment claims.
    """
    if not isinstance(environment, dict):
        raise AllocationError('environment must be a mapping')
    visible = environment.get('CUDA_VISIBLE_DEVICES')
    slurm = environment.get('SLURM_JOB_GPUS')
    if not isinstance(visible, str) or not visible or any(c in visible for c in '\x00\r\n'):
        raise AllocationError('CUDA_VISIBLE_DEVICES is missing or invalid')
    if not isinstance(slurm, str) or not slurm.strip() or any(c in slurm for c in '\x00\r\n'):
        raise AllocationError('SLURM_JOB_GPUS is missing or invalid')
    selectors = visible.split(',')
    if any(not re.fullmatch(r'(?:[0-9]{1,20}|GPU-[A-Za-z0-9-]+|MIG-[A-Za-z0-9/-]+)', item)
           for item in selectors):
        raise AllocationError('invalid CUDA-visible selector list')
    canonical = [str(int(item)) if item.isascii() and item.isdecimal() else item for item in selectors]
    if len(set(canonical)) != len(canonical):
        raise AllocationError('duplicate CUDA-visible selectors')
    if type(local_index) is not int or not 0 <= local_index < len(selectors):
        raise AllocationError('local visible GPU index is out of range')
    return {'cuda_visible_devices': visible,
            'slurm_job_gpus': slurm,
            'local_visible_index': local_index,
            'selected_cuda_visible_device': selectors[local_index],
            'device_identity_verified': False}
