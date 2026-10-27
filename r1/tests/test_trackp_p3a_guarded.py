"""CPU-only safety checks for the P.3a supervisor."""
import json
import math

import pytest

from r1.scripts import trackp_p3a_guarded as G


def test_finite_json_refuses_nan_and_infinity(tmp_path):
    f = tmp_path / "report.json"
    f.write_text('{"metric": [1.0, NaN]}')
    with pytest.raises(ValueError, match="non-finite"):
        G.read_json_finite(f)
    f.write_text('{"metric": 1e999}')
    with pytest.raises(ValueError, match="non-finite"):
        G.read_json_finite(f)
    f.write_text('{"metric": [0, 1.5], "optional": null}')
    assert G.read_json_finite(f)["metric"][1] == 1.5


def test_unit_refuses_existing_partial_and_expired_budget(tmp_path, monkeypatch):
    monkeypatch.setattr(G.R, "tasl7_driver_snapshot", lambda: {"boot_id": "boot"})
    monkeypatch.setattr(G.time, "monotonic", lambda: 10)
    root = tmp_path / "campaign"
    (root / "DRYRUN" / "kev" / "screen").mkdir(parents=True)
    journal = root / "journal.jsonl"
    with pytest.raises(G.R.TrackPStop, match="already exists"):
        G.run_unit(root, journal, "boot", G.GPUBudget(lease_log=tmp_path/"lease"), "DRYRUN", "kev", "screen", [])
    with pytest.raises(G.R.TrackPStop, match="45 GPU-hour"):
        G.run_unit(root, journal, "boot", G.GPUBudget(limit=0, lease_log=tmp_path/"lease"), "DRYRUN", "kev", "other", [])
    assert not journal.exists()


def test_unit_refuses_reboot_before_start(tmp_path, monkeypatch):
    monkeypatch.setattr(G.R, "tasl7_driver_snapshot", lambda: {"boot_id": "other"})
    monkeypatch.setattr(G.time, "monotonic", lambda: 10)
    with pytest.raises(G.R.TrackPStop, match="reboot"):
        G.run_unit(tmp_path, tmp_path / "journal", "original", G.GPUBudget(lease_log=tmp_path/"lease"), "DRYRUN", "kev", "screen", [])


def test_real_subprocess_accepts_only_complete_unit(tmp_path, monkeypatch):
    import sys
    import time
    fake = tmp_path / "fake.py"
    fake.write_text("""
import json, pathlib, sys
args=sys.argv
out=pathlib.Path(args[args.index('--run-dir')+1]); out.mkdir()
label=args[args.index('--evidence')+1]
(out/'report.json').write_text(json.dumps({'score':0.5}))
(out/'manifest.json').write_text(json.dumps({'evidence_label':label,'tasl7_driver':{'boot_id':'boot'}}))
""")
    monkeypatch.setattr(G, "SCRIPT", fake)
    monkeypatch.setattr(G, "verify_live_pins", lambda journal: None)
    monkeypatch.setattr(G.R, "tasl7_driver_snapshot", lambda: {"boot_id": "boot"})
    root = tmp_path / "campaign"; root.mkdir()
    result = G.run_unit(root, root / "journal", "boot", G.GPUBudget(lease_log=tmp_path/"lease"),
                        "DRYRUN", "kev", "select", ["e0-select"], gpu=False)
    assert result == {"score": 0.5}
    events = [json.loads(x)["event"] for x in (root / "journal").read_text().splitlines()]
    assert events == ["unit_start", "unit_complete"]


def test_partial_report_without_manifest_is_not_complete(tmp_path, monkeypatch):
    import time
    fake=tmp_path / "fake.py"
    fake.write_text("""
import pathlib, sys
out=pathlib.Path(sys.argv[sys.argv.index('--run-dir')+1]); out.mkdir()
(out/'report.json').write_text('{"score":0.5}')
""")
    monkeypatch.setattr(G, "SCRIPT", fake)
    monkeypatch.setattr(G, "verify_live_pins", lambda journal: None)
    monkeypatch.setattr(G.R, "tasl7_driver_snapshot", lambda: {"boot_id": "boot"})
    root=tmp_path / "campaign"; root.mkdir()
    with pytest.raises(FileNotFoundError):
        G.run_unit(root, root/"journal", "boot", G.GPUBudget(lease_log=tmp_path/"lease"),
                   "DRYRUN", "kev", "partial", ["e0"], gpu=False)
    assert (root/"DRYRUN"/"kev"/"partial"/"report.json").exists()
    with pytest.raises(G.R.TrackPStop, match="already exists"):
        G.run_unit(root, root/"journal", "boot", G.GPUBudget(lease_log=tmp_path/"lease"),
                   "DRYRUN", "kev", "partial", ["e0"], gpu=False)


def test_deadline_stops_real_fake_process(tmp_path, monkeypatch):
    import time
    fake=tmp_path/"sleep.py"
    fake.write_text("import os,time,json,pathlib,sys\np=pathlib.Path(sys.argv[sys.argv.index('--lease')+1])\np.open('a').write(json.dumps({'pid':os.getpid(),'event':'start','monotonic_s':time.monotonic()})+'\\n')\ntime.sleep(20)\n")
    monkeypatch.setattr(G, "SCRIPT", fake)
    monkeypatch.setattr(G, "verify_live_pins", lambda journal: None)
    monkeypatch.setattr(G.R, "tasl7_driver_snapshot", lambda: {"boot_id": "boot"})
    root=tmp_path/"campaign"; root.mkdir()
    with pytest.raises(G.R.TrackPStop, match="45 GPU-hour|process group|watchdog STOP rc=3"):
        G.run_unit(root, root/"journal", "boot", G.GPUBudget(limit=0.3, lease_log=tmp_path/"lease"),
                   "DRYRUN", "kev", "timeout", ["--lease", str(tmp_path/"lease")])
    assert "unit_complete" not in (root/"journal").read_text()


def test_base_uses_original_driver_sequence_for_dryrun_and_evidence(tmp_path, monkeypatch):
    from r1.c3.train import registry
    monkeypatch.setattr(registry, "reverify", lambda path: [])
    calls=[]
    def fake(root, journal, boot, deadline, label, base, name, arguments, gpu=True):
        calls.append((label, base, name, arguments, gpu))
        return {"selected": {"lr": 0.0001}} if name == "select" else {}
    monkeypatch.setattr(G, "run_unit", fake)
    import time
    G.run_base(tmp_path, tmp_path/"journal", "boot", G.GPUBudget(lease_log=tmp_path/"lease"), "DRYRUN", "kev-0.8b", True)
    assert [v[2] for v in calls] == ["screen_lr1e-05", "screen_lr3e-05", "screen_lr0.0001",
                                     "select", "final", "hard", "native", "probes"]
    assert all("--steps" in v[3] for v in calls[:3])
    assert "--hard" in calls[5][3] and calls[3][4] is False
    assert calls[-1][3][calls[-1][3].index("--n-probe")+1] == "32"
    calls.clear()
    G.run_base(tmp_path, tmp_path/"journal", "boot", G.GPUBudget(lease_log=tmp_path/"lease"), "EVIDENCE", "kev-0.8b", False)
    assert all("--steps" not in v[3] for v in calls)
    assert calls[-1][3][calls[-1][3].index("--n-probe")+1] == "100"


def test_live_pin_change_is_a_stop(tmp_path, monkeypatch):
    journal=tmp_path/"journal"
    journal.write_text(json.dumps({"pins":{"paper":{"commit":"original"},"harness":{"commit":"expected"}}})+"\n")
    monkeypatch.setattr(G.R, "git_commit", lambda path: {"commit":"changed","dirty":False})
    with pytest.raises(G.R.TrackPStop, match="pin changed"):
        G.verify_live_pins(journal)


def test_timeout_terminates_fake_descendant(tmp_path, monkeypatch):
    import os
    import time
    fake=tmp_path/"parent.py"; child_pid=tmp_path/"child.pid"
    fake.write_text(r"""
import pathlib, subprocess, sys, time
p=subprocess.Popen([sys.executable,'-c','import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(60)'])
pathlib.Path(sys.argv[sys.argv.index('--pid-file')+1]).write_text(str(p.pid))
lease=pathlib.Path(sys.argv[sys.argv.index('--lease')+1])
lease.open('a').write(__import__('json').dumps({'pid':__import__('os').getpid(),'event':'start','monotonic_s':time.monotonic()})+'\n')
time.sleep(60)
""")
    monkeypatch.setattr(G, "SCRIPT", fake)
    monkeypatch.setattr(G, "verify_live_pins", lambda journal: None)
    monkeypatch.setattr(G.R, "tasl7_driver_snapshot", lambda: {"boot_id":"boot"})
    root=tmp_path/"campaign"; root.mkdir()
    with pytest.raises(G.R.TrackPStop):
        G.run_unit(root, root/"journal", "boot", G.GPUBudget(limit=1, lease_log=tmp_path/"lease"), "DRYRUN", "kev", "timeout",
                   ["--pid-file",str(child_pid), "--lease", str(tmp_path/"lease")])
    pid=int(child_pid.read_text())
    proc=G.Path(f"/proc/{pid}/stat")
    if proc.exists():
        assert proc.read_text().split()[2] == "Z"
