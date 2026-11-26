"""Synthetic procfs fixtures; no OS process or model is started."""
from pathlib import Path
import pytest
from r1.exam.cache_proc import process_start_ticks, sample_llama_server_processes


def proc(root,pid,name,start):
    p=root/str(pid);p.mkdir()
    (p/'exe').symlink_to('/fixture/'+name)
    fields=['S']+['0']*18+[str(start)]
    (p/'stat').write_text(f'{pid} (name with ) parens) '+ ' '.join(fields))


def test_start_identity_and_actual_snapshot(tmp_path):
    proc(tmp_path,123,'llama-server',987)
    proc(tmp_path,124,'other',555)
    identity={'pid':123,'process_start_ticks':987}
    assert process_start_ticks(123,proc_root=tmp_path)==987
    s=sample_llama_server_processes(identity,proc_root=tmp_path)
    assert s['count']==1 and s['observed'][0]['pid']==123
    assert 'cooperative same-UID assumption' in s['scope']
    assert s['host_global_single_server']=='NOT_CHECKABLE'


def test_extra_server_and_pid_reuse(tmp_path):
    proc(tmp_path,123,'llama-server',987);proc(tmp_path,125,'llama-server',111)
    with pytest.raises(RuntimeError,match='server count or identity mismatch'):
        sample_llama_server_processes({'pid':123,'process_start_ticks':987},proc_root=tmp_path)
    with pytest.raises(RuntimeError,match='identity changed'):
        sample_llama_server_processes({'pid':123,'process_start_ticks':999},proc_root=tmp_path)


def test_missing_executable_link_is_reported_not_claimed_absent(tmp_path):
    proc(tmp_path,123,'llama-server',987);(tmp_path/'126').mkdir()
    result=sample_llama_server_processes({'pid':123,'process_start_ticks':987},proc_root=tmp_path)
    assert result['missing_executable_links']==1
    assert result['host_global_single_server']=='NOT_CHECKABLE'


def test_other_process_cannot_impersonate_owned_server(tmp_path):
    proc(tmp_path,123,'other',987);proc(tmp_path,125,'llama-server',111)
    with pytest.raises(RuntimeError,match='server count or identity mismatch'):
        sample_llama_server_processes({'pid':123,'process_start_ticks':987},proc_root=tmp_path)


def test_inaccessible_links_are_counted_and_not_claimed_absent(tmp_path,monkeypatch):
    import os
    proc(tmp_path,123,'llama-server',987);proc(tmp_path,126,'hidden',1)
    real=os.readlink
    def readlink(path):
        if path.parent.name=='126': raise PermissionError('redacted')
        return real(path)
    monkeypatch.setattr(os,'readlink',readlink)
    result=sample_llama_server_processes({'pid':123,'process_start_ticks':987},proc_root=tmp_path)
    assert result['inaccessible_executable_links']==1
    assert result['host_global_single_server']=='NOT_CHECKABLE'


def test_transient_unreadable_link_is_a_recorded_gap_not_a_stop(tmp_path,monkeypatch):
    import errno, os
    from r1.exam import cache_proc
    proc(tmp_path,123,'llama-server',987);proc(tmp_path,126,'gone',1)
    real=os.readlink
    def readlink(path):
        if path.parent.name=='126': raise OSError(errno.ESRCH,'no such process')
        return real(path)
    monkeypatch.setattr(os,'readlink',readlink)
    result=sample_llama_server_processes({'pid':123,'process_start_ticks':987},proc_root=tmp_path)
    assert result['unreadable_executable_links']==1
    assert result['unreadable_executable_errnos']==['ESRCH']
    assert result['unreadable_executable_samples'][0]['pid']==126
    cache_proc.validate_census_snapshot(result,{'pid':123,'process_start_ticks':987,
                                                'binary':'/fixture/llama-server'})
    assert result['host_global_single_server']=='NOT_CHECKABLE'


def test_unexpected_census_errno_still_stops_with_the_errno(tmp_path,monkeypatch):
    import errno, os
    proc(tmp_path,123,'llama-server',987);proc(tmp_path,126,'weird',1)
    real=os.readlink
    def readlink(path):
        if path.parent.name=='126': raise OSError(errno.EIO,'i/o error')
        return real(path)
    monkeypatch.setattr(os,'readlink',readlink)
    with pytest.raises(RuntimeError,match='unexpected executable census error.*EIO'):
        sample_llama_server_processes({'pid':123,'process_start_ticks':987},proc_root=tmp_path)


def test_census_validation_requires_the_gap_fields(tmp_path):
    from r1.exam import cache_proc
    proc(tmp_path,123,'llama-server',987)
    result=sample_llama_server_processes({'pid':123,'process_start_ticks':987},proc_root=tmp_path)
    result.pop('unreadable_executable_links')
    result['snapshot_sha256']=cache_proc.census_digest(result)
    with pytest.raises(RuntimeError,match='server census or identity mismatch'):
        cache_proc.validate_census_snapshot(result,{'pid':123,'process_start_ticks':987,
                                                    'binary':'/fixture/llama-server'})
