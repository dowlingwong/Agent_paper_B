import json
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from r1.scripts.hk2.hk2_interrupt_checkpoint import CheckpointError, InterruptCheckpoint


class CheckpointTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='hk2-synthetic-checkpoint-')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.unit = self.base / 'unit'; self.unit.mkdir()
        (self.unit / 'partial').write_bytes(b'synthetic partial')
        self.archive = self.base / '_interrupted'; self.archive.mkdir()

    def test_no_signal_does_not_touch_unit_and_restores_handler(self):
        old = signal.getsignal(signal.SIGUSR1)
        with InterruptCheckpoint() as cp:
            self.assertIsNone(cp.checkpoint(self.unit, self.archive, '123'))
        self.assertEqual(signal.getsignal(signal.SIGUSR1), old)
        self.assertEqual((self.unit / 'partial').read_bytes(), b'synthetic partial')
        self.assertEqual(list(self.archive.iterdir()), [])

    def test_collision_and_symlink_refuse_without_overwrite(self):
        existing = self.archive / '123'; existing.mkdir(); (existing / 'prior').write_bytes(b'prior')
        with InterruptCheckpoint() as cp:
            cp.requested = True
            with self.assertRaises(CheckpointError): cp.checkpoint(self.unit, self.archive, '123')
        self.assertEqual((existing / 'prior').read_bytes(), b'prior')
        self.assertEqual((self.unit / 'partial').read_bytes(), b'synthetic partial')
        link = self.base / 'alias'; link.symlink_to(self.unit, target_is_directory=True)
        with InterruptCheckpoint() as cp:
            cp.requested = True
            with self.assertRaises(CheckpointError): cp.checkpoint(link, self.archive, '124')
        self.assertFalse((self.archive / '124').exists())

    def test_failed_move_keeps_both_source_and_partial_archive_directory(self):
        with InterruptCheckpoint() as cp:
            cp.requested = True
            with patch('r1.scripts.hk2.hk2_interrupt_checkpoint.os.rename', side_effect=OSError('synthetic failure')):
                with self.assertRaises(CheckpointError): cp.checkpoint(self.unit, self.archive, '125')
            with self.assertRaisesRegex(CheckpointError, 'already attempted'):
                cp.checkpoint(self.unit, self.archive, '127')
        self.assertEqual((self.unit / 'partial').read_bytes(), b'synthetic partial')
        self.assertTrue((self.archive / '125').is_dir())

    def test_real_owned_subprocess_receives_usr1_and_archives_once(self):
        code = '''import json,signal,sys,time\nfrom r1.scripts.hk2.hk2_interrupt_checkpoint import InterruptCheckpoint\nwith InterruptCheckpoint() as cp:\n print("READY",flush=True)\n end=time.monotonic()+8\n while not cp.requested and time.monotonic()<end: time.sleep(.02)\n if not cp.requested: raise SystemExit(3)\n result=cp.checkpoint(sys.argv[1],sys.argv[2],"126")\n print(json.dumps(result),flush=True)\n'''
        child = subprocess.Popen([sys.executable, '-c', code, str(self.unit), str(self.archive)],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            self.assertEqual(child.stdout.readline().strip(), 'READY')
            child.send_signal(signal.SIGUSR1)
            stdout, stderr = child.communicate(timeout=10)
            self.assertEqual(child.returncode, 0, stderr)
            receipt = json.loads(stdout)
            archived = Path(receipt['archive'])
            self.assertEqual((archived / 'partial').read_bytes(), b'synthetic partial')
            self.assertFalse(self.unit.exists())
            self.assertEqual(archived.stat().st_ino, receipt['unit_ino'])
        finally:
            if child.poll() is None:
                child.kill()
                child.communicate(timeout=5)


if __name__ == '__main__': unittest.main()
