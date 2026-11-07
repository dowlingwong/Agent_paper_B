import hashlib
import io
import tarfile
import pytest
from r1.scripts.b1_safe_extract import extract


def archive(path, name, kind=tarfile.REGTYPE):
    with tarfile.open(path, 'w') as tar:
        entry=tarfile.TarInfo(name); entry.type=kind
        if kind == tarfile.REGTYPE:
            entry.size=5; tar.addfile(entry, io.BytesIO(b'hello'))
        else:
            entry.linkname='../outside'; tar.addfile(entry)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_correct_digest_and_no_overwrite(tmp_path):
    tar=tmp_path/'a.tar'; digest=archive(tar, 'd/f')
    dest=tmp_path/'dest'; dest.mkdir()
    extract(tar,dest,digest)
    assert (dest/'d'/'f').read_bytes()==b'hello'
    with pytest.raises(ValueError): extract(tar,dest,digest)


@pytest.mark.parametrize('name,kind', [('../outside',tarfile.REGTYPE),('/outside',tarfile.REGTYPE),('link',tarfile.SYMTYPE),('link',tarfile.LNKTYPE)])
def test_reject_unsafe_archive_before_writing(tmp_path,name,kind):
    tar=tmp_path/'a.tar'; digest=archive(tar,name,kind)
    dest=tmp_path/'dest'; dest.mkdir()
    with pytest.raises(ValueError): extract(tar,dest,digest)
    assert list(dest.iterdir())==[]


def test_bad_hash_does_not_extract(tmp_path):
    tar=tmp_path/'a.tar'; archive(tar,'ok')
    dest=tmp_path/'dest'; dest.mkdir()
    with pytest.raises(ValueError, match='sha256'): extract(tar,dest,'0'*64)
    assert list(dest.iterdir())==[]
