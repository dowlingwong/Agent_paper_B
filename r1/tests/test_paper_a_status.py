"""Paper A coordination check with fake directories and fake tmux / nvidia-smi / ps. AI-assisted (Claude)."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "paper_a_status.py"
sys.path.insert(0, str(SCRIPT.parent))
import paper_a_status as PA  # noqa: E402

KEY = "paper_a_live_waiting_for_card"


def _exe(path: Path, text: str) -> str:
    path.write_text(text)
    path.chmod(0o755)
    return str(path)


def setup(tmp_path, *, state=None, session=False, gpu=(), markers=(), branch="paper-a-v4-ada", ps_fail=False,
          smi_rc=0, tmux_rc=None):
    co = tmp_path / "agent-checkpoint-intervention"
    run = co / "results/paper_a/replay_panel_v4/live_20261018T234416Z"
    run.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", branch, str(co)], check=True)
    if state is not None:
        (run / "state.json").write_text(json.dumps({"campaign": {"status": state}}))
    for m in markers:
        (run / m).write_text("done\n")
    bins = tmp_path / "bin"
    bins.mkdir()
    rc = tmux_rc if tmux_rc is not None else (0 if session else 1)
    err = "" if rc == 0 else 'echo "can\'t find session: paper_a_v4" >&2\n'
    tmux = _exe(bins / "tmux", f"#!/bin/sh\n{err}exit {rc}\n")
    lines = "".join(f"{pid}, GPU-{pid}, 5000\\n" for pid, _ in gpu) or "No running processes found\\n"
    smi = _exe(bins / "nvidia-smi", f"#!/bin/sh\nprintf '{lines}'\nexit {smi_rc}\n")
    cases = "".join(f'  *" {pid}") echo "{args}";;\n' for pid, args in gpu)
    ps = _exe(bins / "ps", "#!/bin/sh\n" + ("exit 1\n" if ps_fail else f'case "$*" in\n{cases}  *) exit 1;;\nesac\n'))
    cfg = {"expected_host": "ucrtasl", "paper_a_checkout": str(co), "expected_branch": "paper-a-v4-ada",
           "run_dir": "results/paper_a/replay_panel_v4/live_20261018T234416Z",
           "state_file": "state.json", "state_key": "campaign.status",
           "running_values": ["running"], "finished_values": ["finished", "stopped"],
           "waiting_values": ["waiting_for_gpu"], "finished_markers": ["DONE"],
           "tmux_session": "paper_a_v4", "tmux_binary": tmux, "nvidia_smi_binary": smi, "ps_binary": ps,
           "process_patterns": ["live_20261018T234416Z"]}
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps(cfg))
    return path, cfg


def run_cli(cfg_path, host="ucrtasl"):
    done = subprocess.run([sys.executable, str(SCRIPT), "--config", str(cfg_path), "--host", host],
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout.strip().splitlines()[-1])


PAPER_A_PROC = (4242, "python -m paper_a.live --run results/paper_a/replay_panel_v4/live_20261018T234416Z")
OTHER_PROC = (777, "python train_someone_else.py")


def test_running_with_card_clears(tmp_path):
    cfg, _ = setup(tmp_path, state="running", session=True, gpu=[OTHER_PROC, PAPER_A_PROC])
    rep = run_cli(cfg)
    assert rep[KEY] is False and rep["verdict"] == "clear_running"
    assert [p["pid"] for p in rep["evidence"]["gpu"]["paper_a_processes"]] == [4242]


def test_finished_clears_only_without_live_signals(tmp_path):
    cfg, _ = setup(tmp_path, state="finished", gpu=[OTHER_PROC])
    rep = run_cli(cfg)
    assert rep[KEY] is False and rep["verdict"] == "clear_finished"


def test_finished_marker_clears(tmp_path):
    cfg, _ = setup(tmp_path, state="other_value", markers=["DONE"])
    assert run_cli(cfg)["verdict"] == "clear_finished"


@pytest.mark.parametrize("kw,verdict", [
    (dict(state="waiting_for_gpu", session=True), "waiting"),
    (dict(state="something_else", session=True), "waiting"),           # live session, no Paper A GPU process
])
def test_waiting_prints_true(tmp_path, kw, verdict):
    cfg, _ = setup(tmp_path, **kw)
    rep = run_cli(cfg)
    assert rep[KEY] is True and rep["verdict"] == verdict


@pytest.mark.parametrize("kw", [
    dict(state="finished", session=True),                       # finished but session alive
    dict(state="finished", gpu=[PAPER_A_PROC]),                 # finished but a Paper A GPU process
    dict(state="running", session=True),                        # running state but no GPU process
    dict(state="running", gpu=[PAPER_A_PROC]),                  # running state but no session
    dict(state="something_else"),                               # nothing alive, no finished evidence
    dict(state="something_else", session=True, gpu=[PAPER_A_PROC]),  # no running state value
    dict(state="finished", branch="main"),                      # wrong branch
    dict(state="finished", smi_rc=9),                           # nvidia-smi fails
    dict(state="finished", gpu=[OTHER_PROC], ps_fail=True),     # unidentifiable GPU process
    dict(state="finished", tmux_rc=2),                          # tmux error
    dict(state=None, markers=()),                               # state file missing
])
def test_unknown_omits_key(tmp_path, kw):
    cfg, _ = setup(tmp_path, **kw)
    rep = run_cli(cfg)
    assert KEY not in rep and rep["verdict"] == "unknown" and rep["reasons"]


def test_wrong_host_and_unconfigured_refuse(tmp_path):
    cfg, raw = setup(tmp_path, state="finished")
    assert KEY not in run_cli(cfg, host="deepthought")
    for drop in ("paper_a_checkout", "run_dir", "tmux_session", "process_patterns"):
        c = dict(raw)
        c.pop(drop)
        p = tmp_path / f"cfg_{drop}.json"
        p.write_text(json.dumps(c))
        rep = run_cli(p)
        assert KEY not in rep, drop
    c = dict(raw, typo_key=1)
    p = tmp_path / "cfg_typo.json"
    p.write_text(json.dumps(c))
    assert KEY not in run_cli(p)
    assert KEY not in run_cli(tmp_path / "missing.json")


def test_allow_running_without_state(tmp_path):
    cfg, raw = setup(tmp_path, state="something_else", session=True, gpu=[PAPER_A_PROC])
    raw["allow_running_without_state"] = True
    cfg.write_text(json.dumps(raw))
    assert run_cli(cfg)["verdict"] == "clear_running"


def test_stale_running_state_is_unknown(tmp_path):
    cfg, raw = setup(tmp_path, state="running", session=True, gpu=[PAPER_A_PROC])
    raw["state_max_age_seconds"] = 0
    cfg.write_text(json.dumps(raw))
    assert run_cli(cfg)["verdict"] == "unknown"


def test_runner_accepts_only_clear(tmp_path):
    """End to end with the sweep runner's paper_a_check: clear -> record; waiting/unknown -> STOP."""
    sys.path.insert(0, str(SCRIPT.parents[2]))
    from r1.scripts import c3_label_sweep as sweep
    cfg, _ = setup(tmp_path, state="running", session=True, gpu=[PAPER_A_PROC])
    cmd = [sys.executable, str(SCRIPT), "--config", str(cfg), "--host", "ucrtasl"]
    assert sweep.paper_a_check({"command": cmd}, "ucrtasl")["verdict"] == "clear"
    with pytest.raises(sweep.Stop):
        sweep.paper_a_check({"command": [sys.executable, str(SCRIPT), "--config", str(cfg), "--host", "x"]}, "x")


def test_ada_config_refuses_until_verified():
    """The committed Ada config has unverified (null) entries: the check must refuse, never clear."""
    path = SCRIPT.parent / "configs" / "paper_a_status_ada.json"
    raw = json.loads(path.read_text())
    assert raw["expected_host"] == "ucrtasl" and raw["expected_branch"] == "paper-a-v4-ada"
    assert raw["verify_before_first_use"]
    rep = run_cli(path)
    assert KEY not in rep and rep["verdict"] == "unknown"
