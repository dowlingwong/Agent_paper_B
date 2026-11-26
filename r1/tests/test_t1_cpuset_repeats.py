"""local/20261126-01: the R1-TASL2-CPU check's three sealed attempts are producible by ``dry_run_node.py``.

G.1b's ``next_attempt`` allows one complete attempt per node per run; the check needs three in its one derived run.
``dry_run_node.py`` installs ``check_next_attempt`` for the check's derived spec only; every other spec keeps G.1b's
rule, and G.1b's runner is unchanged.
"""
from __future__ import annotations

import copy
import functools
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sweep2" / "t1_tasl"))
sys.path.insert(0, str(ROOT / "sweep2" / "g1b"))
import dry_run_node as D  # noqa: E402
import g1b_lib as lib  # noqa: E402
import g1b_tasl as T  # noqa: E402
import g5_tasl as G5  # noqa: E402
from test_t1_tasl_g1b import _attempt, job, launch_spec  # noqa: E402,F401  (job: the fake-host fixture)

HP = "mlgym_houseprice"
G5_SPEC = json.loads((ROOT / "sweep2" / "t1_tasl" / "g5_tasl_spec.json").read_text())
RUN = f"tasl2-cpuset-{HP}-20261127"


def _record(attempt_dir: Path, stop_class=None) -> None:
    (attempt_dir / "job_record.json").write_text(json.dumps({"stop_class": stop_class,
                                                             "stop": None if stop_class is None else "STOP: x"}))


def test_constants_are_g5_tasl_values():
    assert D.CHECK_RULE == G5.TASL2_CPU_ROW and D.CHECK_REPEATS == G5.CPUSET_REPEATS == 3
    assert D.CHECK_RUN.pattern == G5.CPUSET_RUN.pattern


def test_the_check_spec_is_recognised_and_nothing_else():
    derived = G5.cpuset_spec(copy.deepcopy(G5_SPEC), HP, RUN)
    assert D.is_cpuset_check(derived, HP) is True
    signed = json.loads((ROOT / G5.FAMILY_SPECS["G5-7"]).read_text())
    assert "cpuset_check" not in signed and D.is_cpuset_check(signed, HP) is False
    assert D.is_cpuset_check(launch_spec(Path("/nonexistent")), HP) is False
    for bad in ({"run_id": "g1b-tasl-20261121-b"}, {"run_id": f"tasl2-cpuset-mlab_imdb-20261127"},
                {"run_id": f"tasl2-cpuset-{HP}-2026112"}, {"cpuset_check": {**derived["cpuset_check"], "rule": "x"}},
                {"cpuset_check": {**derived["cpuset_check"], "node": "mlab_imdb"}}, {"cpuset_check": "R1-TASL2-CPU"}):
        with pytest.raises(T.Stop, match="not mlgym_houseprice's R1-TASL2-CPU check spec"):
            D.is_cpuset_check({**derived, **bad}, HP)
    with pytest.raises(T.Stop, match="check spec"):              # the block names another node
        D.is_cpuset_check(derived, "mlab_imdb")


def test_check_attempts_three_complete_then_refused(tmp_path):
    root = tmp_path / HP
    for n in (1, 2, 3):
        got, d = D.check_next_attempt(root)
        assert got == n and d == root / f"attempt-{n}" and (d / "attempt.json").is_file()
        _record(d)
    with pytest.raises(T.Stop, match="holds 3 complete attempts"):
        D.check_next_attempt(root)
    assert sorted(p.name for p in root.iterdir()) == ["attempt-1", "attempt-2", "attempt-3"]   # nothing created
    ref_root = tmp_path / "g1b"                                   # attempt.json as G.1b writes it
    _, g = T.next_attempt(ref_root)
    assert set(json.loads((g / "attempt.json").read_text())) == \
        set(json.loads((root / "attempt-1" / "attempt.json").read_text()))


def test_check_attempts_retry_infrastructure_and_refuse_the_rest(tmp_path):
    root = tmp_path / HP
    _, d = D.check_next_attempt(root)
    _record(d, "infrastructure")
    for n in (2, 3, 4):                                          # the infra STOP does not count
        got, d = D.check_next_attempt(root)
        assert got == n
        _record(d)
    with pytest.raises(T.Stop, match="holds 3 complete"):
        D.check_next_attempt(root)
    for cls in ("node", "timing", "refused_before_run", "other"):
        r = tmp_path / cls / HP
        _, d = D.check_next_attempt(r)
        _record(d)
        _, d = D.check_next_attempt(r)
        _record(d, cls)
        with pytest.raises(T.Stop, match=f"stop_class '{cls}'; no new attempt of this check"):
            D.check_next_attempt(r)
    r = tmp_path / "norecord" / HP
    D.check_next_attempt(r)                                       # left without a job record
    with pytest.raises(T.Stop, match="has no job record"):
        D.check_next_attempt(r)
    (tmp_path / "odd" / HP / "junk").mkdir(parents=True)
    with pytest.raises(T.Stop, match="unexpected entry"):
        D.check_next_attempt(tmp_path / "odd" / HP)


def _derived_job_spec(spec: dict) -> dict:
    """The fixture's launch spec as cpuset-spec shapes a check spec: its own run id and the cpuset_check block."""
    s = copy.deepcopy(spec)
    s["run_id"] = RUN
    s["cpuset_check"] = {"rule": "R1-TASL2-CPU", "node": HP, "cpus": "0-7", "g1b_cpus": "8-15"}
    return s


def _main(monkeypatch, spec_path, node, engine, smi, setup):
    """dry_run_node.main as the host runs it, the runner taking the fixture's fake host."""
    monkeypatch.setattr(T, "next_attempt", T.next_attempt)       # restored after the test (main replaces it)
    monkeypatch.setattr(lib, "PARTS", lib.PARTS)
    monkeypatch.setattr(lib, "merge_parts", lib.merge_parts)
    real = T.run_node_job
    monkeypatch.setattr(T, "run_node_job", functools.partial(real, smi=smi, engine=engine, setup=setup))
    monkeypatch.setattr(sys, "argv", ["dry_run_node.py", str(spec_path), node])
    return D.main()


def test_dry_run_gives_the_check_three_attempts_end_to_end(job, tmp_path, monkeypatch, capsys):
    """Through the real run_node_job on the fake host: the check spec gets attempts 1-3 of the default part, each
    complete, then a refusal (recorded under _refusals/, no attempt-4)."""
    spec, spec_path, calls, state, engine, smi, setup = job
    s = _derived_job_spec(spec)
    T.validate_spec(copy.deepcopy(s), launch=True)
    spec_path.write_text(json.dumps(s))
    for n in (1, 2, 3):
        assert _main(monkeypatch, spec_path, HP, engine, smi, setup) == 0
        rec = json.loads((_attempt(s, HP, n) / "job_record.json").read_text())
        assert (rec["attempt"], rec["stop_class"], rec["run_id"], rec["runs"]["written"]) == (n, None, RUN, 10)
    with pytest.raises(T.Stop, match="holds 3 complete attempts"):
        _main(monkeypatch, spec_path, HP, engine, smi, setup)
    assert not _attempt(s, HP, 4).exists()
    runs = Path(s["hosts"]["TASL-2"]["runs_root"]) / RUN
    assert len(list((runs / "_refusals").iterdir())) == 1


def test_dry_run_keeps_g1b_one_attempt_rule_for_other_specs(job, monkeypatch):
    spec, spec_path, calls, state, engine, smi, setup = job
    assert _main(monkeypatch, spec_path, HP, engine, smi, setup) == 0
    assert T.next_attempt is not D.check_next_attempt
    with pytest.raises(T.Stop, match="no new attempt of this node"):
        _main(monkeypatch, spec_path, HP, engine, smi, setup)
    s = _derived_job_spec(spec)                                   # a block for another node: refused before any run
    s["cpuset_check"]["node"] = "mlab_imdb"
    spec_path.write_text(json.dumps(s))
    with pytest.raises(T.Stop, match="check spec"):
        _main(monkeypatch, spec_path, HP, engine, smi, setup)
