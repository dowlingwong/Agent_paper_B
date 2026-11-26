"""Partial exception bytes are retained before STOP, never marked complete."""
import base64
import hashlib
from http.client import IncompleteRead
import pytest
from r1.exam.cache_io import read_chunks


@pytest.mark.parametrize('prior',[b'',b'earlier'])
def test_incomplete_read_exception_partial_is_persisted(prior):
    class Stream:
        def __init__(self):self.calls=0
        def read(self,size):
            self.calls+=1
            if prior and self.calls==1:return prior
            raise IncompleteRead(b'partial\xffbytes',100)
    saved=[]
    with pytest.raises(IncompleteRead):read_chunks(Stream(),saved.append,sequence=9)
    assert b''.join(base64.b64decode(x['chunk_b64']) for x in saved)==prior+b'partial\xffbytes'
    assert saved[-1]['from_incomplete_read'] is True
    assert saved[-1]['chunk_sha256']==hashlib.sha256(b'partial\xffbytes').hexdigest()
    assert all(x['event']=='response_chunk' for x in saved)
