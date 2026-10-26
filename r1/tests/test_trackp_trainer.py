"""Track P 1.6: shared loop resume, run plumbing (config, seed guard, GPU lease, manifest). ENGINEERING_ONLY; AI-assisted (Claude)."""
from __future__ import annotations

import hashlib
import json

import pytest
import torch

from r1.c3.train import run as R
from r1.c3.train.trainer import Trainer, TrainConfig, epoch_order, sha256_file, seed_everything
from r1.c3.train.types import DecisionPrompt


class TinyModel(torch.nn.Module):
    """Hash-bag text model with the DecisionModel contract (tests only)."""

    family = "tiny"

    def __init__(self, dim=8):
        super().__init__()
        self.emb = torch.nn.EmbeddingBag(97, dim)
        self.belief = torch.nn.Linear(dim, 12)
        self.action = torch.nn.Linear(dim, 1)

    def forward(self, batch):
        ids = [torch.tensor([int(hashlib.md5(w.encode()).hexdigest(), 16) % 97 for w in (p.state + " " + p.proposal).split()])
               for p in batch]
        offsets = torch.tensor([0] + [len(x) for x in ids[:-1]]).cumsum(0)
        h = self.emb(torch.cat(ids), offsets)
        return {"belief_logits": self.belief(h), "action_logit": self.action(h).squeeze(-1)}

    def trainable_parameters(self):
        return self.parameters()

    def save(self, path):
        path.mkdir(parents=True, exist_ok=True)
        torch.save(self.state_dict(), path / "heads.pt")
        rec = {"files": {"heads.pt": sha256_file(path / "heads.pt")}}
        (path / "record.json").write_text(json.dumps(rec))
        return rec

    def load(self, path):
        rec = json.loads((path / "record.json").read_text())
        if sha256_file(path / "heads.pt") != rec["files"]["heads.pt"]:
            raise RuntimeError("sha256 mismatch")
        self.load_state_dict(torch.load(path / "heads.pt"))
        return rec


def rows(n=40):
    out = []
    for i in range(n):
        y = torch.zeros(12)
        y[1 + i % 11] = 1.0
        out.append({"prompt": DecisionPrompt(state=f"node n{i % 3} budget {i % 5}", proposal=f"edit lr x{i % 7}"),
                    "y": y})
    return out


def loss_fn(out, batch):
    y = torch.stack([r["y"] for r in batch])
    return -(y * torch.log_softmax(out["belief_logits"], -1)).sum(-1).mean()


def make(tmp, cfg):
    seed_everything(cfg.seed)
    return Trainer(TinyModel(), rows(), loss_fn, cfg, tmp)


def params(m):
    return torch.cat([p.detach().flatten() for p in m.parameters()])


def test_epoch_order_is_a_function_of_seed_and_epoch():
    assert (epoch_order(10, 3, 1) == epoch_order(10, 3, 1)).all()
    assert not (epoch_order(10, 3, 1) == epoch_order(10, 3, 2)).all()


def test_kill_and_resume_matches_an_uninterrupted_run(tmp_path):
    cfg = TrainConfig(seed=7, epochs=2, batch_size=4, grad_accum=2, lr=1e-2, head_lr=1e-2)
    full = make(tmp_path / "full", cfg)
    res = full.train()
    assert res["completed"] and full.step == full.total_steps == 10
    # interrupted: stop after 4 steps (last checkpoint at step 3 = every round(5 * 0.25) = 1 step -> step 4)
    part = make(tmp_path / "part", cfg)
    assert part.train(stop_after=4) == {"stopped_at": 4, "completed": False}
    resumed = make(tmp_path / "part", cfg)         # fresh process state, same run dir
    assert resumed.resume() == 4
    resumed.train()
    assert torch.equal(params(full.model), params(resumed.model))
    steps = [json.loads(l)["step"] for l in (tmp_path / "part" / "metrics.jsonl").read_text().splitlines()
             if json.loads(l)["kind"] == "step"]
    assert steps == list(range(1, 11))             # no completed step repeated


def test_steps_after_the_checkpoint_are_logged_once_after_resume(tmp_path):
    cfg = TrainConfig(seed=3, epochs=2, batch_size=4, grad_accum=2, checkpoint_every_frac=0.5)  # ckpt every 2 steps
    t = make(tmp_path, cfg)
    t.train(stop_after=3)                          # steps 1-3 logged, last checkpoint at step 2
    make(tmp_path, cfg).train()
    steps = [json.loads(l)["step"] for l in (tmp_path / "metrics.jsonl").read_text().splitlines()
             if json.loads(l)["kind"] == "step"]
    assert steps == list(range(1, 11))


def test_trainer_refuses_evaluation_seed_fields():
    bad = rows(4)
    bad[1]["y_eval"] = bad[1]["y"]
    with pytest.raises(R.TrackPStop, match="7006-7010"):
        make_rows(bad)
    meta = rows(4)
    meta[2]["prompt"] = DecisionPrompt(state="s", proposal="p", meta={"audit": {"delta_7008": 0.1}})
    with pytest.raises(R.TrackPStop):
        make_rows(meta)


def make_rows(rs):
    return Trainer(TinyModel(), rs, loss_fn, TrainConfig(), "/nonexistent")


def test_incomplete_checkpoint_is_ignored_and_tampered_state_refused(tmp_path):
    cfg = TrainConfig(seed=1, epochs=1, batch_size=8, grad_accum=1)
    t = make(tmp_path, cfg)
    t.train()
    last = t.latest_checkpoint()
    (last.parent / "step_9999999").mkdir()        # no COMPLETE marker
    assert make(tmp_path, cfg).latest_checkpoint() == last
    with open(last / "trainer_state.pt", "ab") as fh:
        fh.write(b"x")
    with pytest.raises(RuntimeError, match="sha256"):
        make(tmp_path, cfg).resume()


def test_resume_with_another_config_is_refused(tmp_path):
    make(tmp_path, TrainConfig(seed=1, epochs=1, batch_size=8, grad_accum=1)).train()
    with pytest.raises(RuntimeError, match="different training config"):
        make(tmp_path, TrainConfig(seed=2, epochs=1, batch_size=8, grad_accum=1)).resume()


def test_config_placeholders_are_refused(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"comment": "TODO_VERIFY_ON_HOST is fine here", "a": {"b": ["x", "TODO_VERIFY_ON_HOST"]}}))
    with pytest.raises(R.TrackPStop, match=r"a\.b\[1\]"):
        R.load_config(p)
    assert R.load_config(p, allow_placeholders=True)["a"]["b"][0] == "x"


def test_evaluation_seed_columns_are_refused_before_p4(tmp_path, monkeypatch):
    table = [{"y_train": [0.1] * 12, "y_eval": [0.1] * 12, "u_eval": 0.0, "mu_eval": 0.1, "z_eval": [0] * 5}]
    with pytest.raises(R.TrackPStop, match="7006-7010"):
        R.guard_rows(table, purpose="sft")
    monkeypatch.setattr(R, "AUTH_DIR", tmp_path)
    with pytest.raises(R.TrackPStop, match="authorizations"):
        R.guard_rows(table, purpose="p4_final_eval")
    (tmp_path / "trackp_p4_20261201.md").write_text("note")
    assert R.guard_rows(table, purpose="p4_final_eval") == table
    assert R.strip_eval_columns(table) == [{"y_train": [0.1] * 12}]
    assert R.guard_rows(R.strip_eval_columns(table), purpose="sft")


def test_gpu_lease_logs_and_refuses_when_held_or_track_x_runs(tmp_path):
    lock, log, run_log = tmp_path / "gpu0.lock", tmp_path / "lease.jsonl", []
    kw = dict(lock_path=lock, log_path=log, status_text="## 26 Oct — Track P Phase 0", check_processes=False)
    with R.gpu_lease("job1", run_log=run_log, **kw):
        with pytest.raises(R.TrackPStop, match="held"):
            with R.gpu_lease("job2", **kw):
                pass
    assert [e["event"] for e in run_log] == ["start", "end"]
    assert len(log.read_text().splitlines()) == 2
    with pytest.raises(R.TrackPStop, match="Track X"):
        with R.gpu_lease("job3", **{**kw, "status_text": "## 3 Nov 2026 — Track X B1 running on the portal"}):
            pass


def test_track_x_status_reading_uses_the_newest_b1_b2_heading():
    run = "## 4 Nov — Track X B2 started\n\n## 3 Nov — Track X B1 done\n"
    done = "## 5 Nov — Track X B2 done (accepted)\n\n" + run
    assert R.track_x_running(run) and not R.track_x_running(done)
    assert not R.track_x_running("## 26 Oct — Track P Phase 0\n## 25 Oct — exam runbook adopted\n")
    assert R.track_x_running("## 6 Nov — exam B1 in progress on the portal\n")


def test_manifest_records_commits_and_hashes():
    m = R.run_manifest(subcommand="spike", evidence="ENGINEERING_ONLY", cfg={"a": 1}, seed=0,
                       base={"repo": "x", "revision": "y"}, model_files={"heads.pt": "0" * 64},
                       data_hash=R.data_manifest_hash(rows(3)), lease_log=[])
    assert len(m["git"]["paper"]["commit"]) == 40 and m["evidence_label"] == "ENGINEERING_ONLY"
    assert m["host"]["hostname"] and "gpus" in m["host"]


def test_host_record_names_the_device_in_use():
    import torch
    h = R.host_record()
    if not torch.cuda.is_available():
        assert h["device"] is None
        return
    assert h["device"]["name"] == torch.cuda.get_device_name(torch.cuda.current_device())
    if h["gpus"]:   # the device's UUID is one of the cards nvidia-smi lists
        assert h["device"]["uuid"] in {g["uuid"] for g in h["gpus"]}
    with pytest.raises(ValueError):
        R.run_manifest(subcommand="spike", evidence="PILOT", cfg={}, seed=0, base={}, model_files={}, data_hash="",
                       lease_log=[])


def _trackp_cli():
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location("trackp_cli", Path(R.REPO) / "r1/scripts/trackp.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("cmd,phase", [("e0", "p3a"), ("probes", "p3a"), ("exam", "p3b"), ("sft", "p4"),
                                       ("a6", "p5"), ("rb", "p6")])
def test_authorization_gate_for_every_non_dryrun_label(cmd, phase, tmp_path, monkeypatch):
    import types
    cli = _trackp_cli()
    monkeypatch.setattr(R, "AUTH_DIR", tmp_path)
    for label in ("ENGINEERING_ONLY", "EVIDENCE"):
        args = types.SimpleNamespace(cmd=cmd, tiny=False, evidence=label)
        with pytest.raises(R.TrackPStop, match=f"trackp_{phase}_"):
            cli._require_authorization(args)
    cli._require_authorization(types.SimpleNamespace(cmd=cmd, tiny=False, evidence="DRYRUN"))
    cli._require_authorization(types.SimpleNamespace(cmd=cmd, tiny=True, evidence="ENGINEERING_ONLY"))
    (tmp_path / f"trackp_{phase}_20261201.md").write_text("note")
    for label in ("ENGINEERING_ONLY", "EVIDENCE"):
        cli._require_authorization(types.SimpleNamespace(cmd=cmd, tiny=False, evidence=label))
    cli._require_authorization(types.SimpleNamespace(cmd="spike", tiny=False, evidence="ENGINEERING_ONLY"))
