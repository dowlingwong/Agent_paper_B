"""Synthetic census used only in isolated tests; does not inspect /proc."""
import time
from r1.exam.cache_proc import CENSUS_METHOD,CENSUS_SCOPE,census_digest


def fake_census(identity):
    sample={'method':CENSUS_METHOD,'scope':CENSUS_SCOPE,'count':1,'pid':identity['pid'],
            'process_start_ticks':identity['process_start_ticks'],
            'observed':[{'pid':identity['pid'],'process_start_ticks':identity['process_start_ticks'],
                         'executable':identity['binary']}], 'monotonic_ns':time.monotonic_ns(),
            'inaccessible_executable_links':0,'missing_executable_links':0,
            'unreadable_executable_links':0,'unreadable_executable_errnos':[],'unreadable_executable_samples':[],
            'unobserved_same_uid_calls':'assumed absent by author decision, not measured',
            'host_global_single_server':'NOT_CHECKABLE'}
    sample['snapshot_sha256']=census_digest(sample)
    return sample
