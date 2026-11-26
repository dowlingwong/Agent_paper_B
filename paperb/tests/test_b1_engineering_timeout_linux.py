"""Linux only: own synthetic process groups, no model, GPU or external process."""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(not sys.platform.startswith('linux'), reason='Linux waitid / proc only')
WRAPPER = Path(__file__).resolve().parents[1] / 'scripts' / 'b1_engineering_timeout.py'


def live(pid):
    try:
        text = Path(f'/proc/{pid}/stat').read_text()
    except FileNotFoundError:
        return False
    return text.rsplit(')', 1)[1].split()[0] != 'Z'


@pytest.mark.parametrize('case', ['early_exit', 'deadline', 'interruption'])
def test_owned_group_is_stopped_and_unrelated_session_is_not(tmp_path, case):
    root = tmp_path / 'root.py'
    root.write_text('''import os, signal, subprocess, sys, time\nfrom pathlib import Path\nout=Path(sys.argv[1]); case=sys.argv[2]\nchild=subprocess.Popen([sys.executable,"-c", "import os,signal,sys,time; from pathlib import Path; signal.signal(signal.SIGTERM, signal.SIG_IGN); Path(sys.argv[1]).write_text(str(os.getpid())); time.sleep(12)",str(out/'child')])\nwhile not (out/'child').exists(): time.sleep(.01)\n(out/'ready').write_text(str(os.getpid()))\nif case=='early_exit': raise SystemExit(7)\ntime.sleep(12)\n''')
    unrelated=subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(12)'], start_new_session=True)
    outlog=(tmp_path/'wrapper.stdout').open('x')
    errlog=(tmp_path/'wrapper.stderr').open('x')
    wrapper=subprocess.Popen([sys.executable, str(WRAPPER), '--seconds', '4',
                              sys.executable, str(root), str(tmp_path), case],
                             stdout=outlog, stderr=errlog, text=True,
                             start_new_session=True)
    try:
        deadline=time.monotonic()+3
        while not (tmp_path/'ready').exists() and time.monotonic()<deadline:
            time.sleep(.01)
        assert (tmp_path/'ready').exists(), 'synthetic root was not ready'
        if case=='interruption': os.kill(wrapper.pid, signal.SIGTERM)
        wrapper.wait(timeout=7)
        outlog.flush(); errlog.flush()
        stdout=(tmp_path/'wrapper.stdout').read_text()
        stderr=(tmp_path/'wrapper.stderr').read_text()
        expected={'early_exit':7, 'deadline':124, 'interruption':128+signal.SIGTERM}[case]
        assert wrapper.returncode == expected, (wrapper.returncode, stdout, stderr)
        root_pid=int((tmp_path/'ready').read_text())
        assert f'ENGINEERING_TEST_ROOT pid={root_pid} pgid={root_pid} start_ticks=' in stderr
        assert not live(int((tmp_path/'child').read_text())), stderr
        assert unrelated.poll() is None
    finally:
        outlog.close(); errlog.close()
        child_file=tmp_path/'child'
        child_pid=int(child_file.read_text()) if child_file.exists() else None
        observation={'case':case, 'wrapper_pid':wrapper.pid, 'wrapper_returncode':wrapper.poll(),
                     'child_pid':child_pid, 'child_live':live(child_pid) if child_pid else None,
                     'unrelated_pid':unrelated.pid, 'unrelated_live':unrelated.poll() is None}
        with (tmp_path/'observation.json').open('x') as record:
            json.dump(observation,record,sort_keys=True);record.write('\n')
        # This test created the unrelated control process itself and owns its handle.
        if unrelated.poll() is None: unrelated.terminate()
        unrelated.wait(timeout=3)
        # On a wrapper failure do not blindly signal process IDs; the synthetic
        # commands have an twelve-second self-expiry and the site is STOP.
