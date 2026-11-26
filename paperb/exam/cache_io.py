"""Persist each received chunk before reading the next; no claim about delivery."""
import base64
import hashlib
from http.client import IncompleteRead


def read_chunks(stream,write,*,sequence=None):
    chunks=[];index=0
    def preserve(chunk,*,from_incomplete_read=False):
        nonlocal index
        if not isinstance(chunk,bytes):
            raise TypeError('STOP: response stream did not return bytes')
        if not chunk:return
        index+=1
        write({'event':'response_chunk','sequence':sequence,'chunk_index':index,
               'chunk_b64':base64.b64encode(chunk).decode('ascii'),
               'chunk_sha256':hashlib.sha256(chunk).hexdigest(),'chunk_bytes':len(chunk),
               'from_incomplete_read':from_incomplete_read})
        chunks.append(chunk)
    while True:
        try:
            chunk=stream.read(65536)
        except IncompleteRead as exc:
            # http.client supplies newly read bytes on the exception itself.
            # Persist them before re-raising; do not treat them as a full body.
            preserve(exc.partial,from_incomplete_read=True)
            raise
        if not chunk: break
        preserve(chunk)
    return b''.join(chunks)
