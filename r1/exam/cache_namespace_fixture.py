"""Synthetic namespace-fixture report validator; never authorizes a real job.

Values are caller-supplied fixtures, not observed host facts. A real evidence
collector, executable fixture, host capability checks and review are pending.
"""


def validate_namespace_fixture(report):
    def stop(reason):raise ValueError('STOP: namespace fixture '+reason)
    if not isinstance(report,dict) or report.get('schema')!='D3_NAMESPACE_SYNTHETIC_FIXTURE_ONLY/v1':
        stop('wrong or missing synthetic-only label')
    if report.get('synthetic_only') is not True or report.get('real_models') is not False or report.get('gpu_used') is not False:
        stop('scope is not CPU synthetic-only')
    ns=report.get('namespaces')
    if not isinstance(ns,dict):stop('missing namespace evidence')
    roles=('supervisor','worker','server')
    for key in ('user','net','pid','proc_mount'):
        outer=ns.get('outer_'+key)
        if type(outer) is not int or outer<=0:stop('invalid outer '+key+' inode')
        inner=[(ns.get(role) or {}).get(key) for role in roles]
        if any(type(value) is not int or value<=0 for value in inner) or len(set(inner))!=1 or inner[0]==outer:
            stop('inner '+key+' namespace not jointly isolated')
    if report.get('inner_loopback_works') is not True or report.get('outer_same_uid_connect_blocked') is not True:
        stop('network isolation missing')
    if report.get('outer_same_uid_nsenter_blocked') is not True:
        stop('same-UID namespace entry not excluded')
    if report.get('fixture_server_count')!=1 or type(report.get('fixture_server_count')) is not int:
        stop('fixture server count invalid')
    lease=report.get('fixture_lease')
    if not isinstance(lease,dict):stop('missing synthetic lease evidence')
    if (type(lease.get('holder_pid')) is not int or lease['holder_pid']<=0 or
        type(lease.get('holder_start_ticks')) is not int or lease['holder_start_ticks']<=0 or
        type(lease.get('lock_inode')) is not int or lease['lock_inode']<=0 or
        lease.get('contender_blocked_before') is not True or
        lease.get('synthetic_supervisor_exit_observed') is not True or
        lease.get('same_holder_alive_after') is not True or
        lease.get('contender_blocked_after') is not True):
        stop('fixture flock continuity unproven')
    if report.get('event_gaps')!=0 or type(report.get('event_gaps')) is not int:
        stop('fixture event loss or gap')
    return {'verdict':'SYNTHETIC_STRUCTURE_ONLY',
            'scope':'caller-supplied fixture fields only; no host, GPU, service or coldness verified',
            'real_launch_authorized':False}
