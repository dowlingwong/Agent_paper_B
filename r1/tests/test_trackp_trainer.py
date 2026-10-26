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


def test_manifest_records_commits_and_hashes():
    m = R.run_manifest(subcommand="spike", evidence="ENGINEERING_ONLY", cfg={"a": 1}, seed=0,
                       base={"repo": "x", "revision": "y"}, model_files={"heads.pt": "0" * 64},
                       data_hash=R.data_manifest_hash(rows(3)), lease_log=[])
    assert len(m["git"]["paper"]["commit"]) == 40 and m["evidence_label"] == "ENGINEERING_ONLY"
    with pytest.raises(ValueError):
        R.run_manifest(subcommand="spike", evidence="PILOT", cfg={}, seed=0, base={}, model_files={}, data_hash="",
                       lease_log=[])
