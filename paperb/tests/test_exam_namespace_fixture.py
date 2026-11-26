"""Logic-only synthetic inputs; these tests do not create Linux namespaces."""
import pytest
from r1.exam.cache_namespace_fixture import validate_namespace_fixture


def fixture():
    inner={'user':11,'net':12,'pid':13,'proc_mount':14}
    return {'schema':'D3_NAMESPACE_SYNTHETIC_FIXTURE_ONLY/v1','synthetic_only':True,'real_models':False,'gpu_used':False,
            'namespaces':{'outer_user':1,'outer_net':2,'outer_pid':3,'outer_proc_mount':4,
                          'supervisor':dict(inner),'worker':dict(inner),'server':dict(inner)},
            'inner_loopback_works':True,'outer_same_uid_connect_blocked':True,'outer_same_uid_nsenter_blocked':True,
            'fixture_server_count':1,'event_gaps':0,
            'fixture_lease':{'holder_pid':3,'holder_start_ticks':4,'lock_inode':5,
                             'contender_blocked_before':True,'synthetic_supervisor_exit_observed':True,
                             'same_holder_alive_after':True,'contender_blocked_after':True}}


def test_fixture_never_authorizes_real_launch():
    result=validate_namespace_fixture(fixture())
    assert result['real_launch_authorized'] is False and result['verdict']=='SYNTHETIC_STRUCTURE_ONLY'


@pytest.mark.parametrize('change',[
    lambda x:x.update(gpu_used=True),
    lambda x:x['namespaces']['worker'].update(net=99),
    lambda x:x['namespaces'].update(outer_net=12),
    lambda x:x.update(outer_same_uid_nsenter_blocked=False),
    lambda x:x.update(fixture_server_count=True),
    lambda x:x['fixture_lease'].update(contender_blocked_after=False),
    lambda x:x.update(event_gaps=1),
])
def test_failed_scope_or_lease_is_not_accepted(change):
    value=fixture();change(value)
    with pytest.raises(ValueError,match='STOP'):validate_namespace_fixture(value)
