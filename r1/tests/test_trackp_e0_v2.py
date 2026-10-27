"""Track P decisions of 26 Oct (PLAN §10): E0 protocol v2, A3 budget, A4 label reference, linear12 head, token-row
init / fp32 / lr, early stopping, temperature scaling, Track X marker. Tiny random-weight models, CPU only.
ENGINEERING_ONLY; AI-assisted (Claude).
"""
from __future__ import annotations

import json
import os

import numpy as np
import pytest
import torch

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
pytest.importorskip("transformers")
pytest.importorskip("peft")

from r1.c3.labels import N_BINS  # noqa: E402
from r1.c3.train import exam_run as X  # noqa: E402
from r1.c3.train import exam_synthetic as E  # noqa: E402
from r1.c3.train import metrics as MT  # noqa: E402
from r1.c3.train import model as M  # noqa: E402
from r1.c3.train import run as R  # noqa: E402
from r1.c3.train import tiny  # noqa: E402
from r1.c3.train.trainer import Trainer, TrainConfig  # noqa: E402


def _tiny(family, tmp_path, **kw):
    try:
        return tiny.build_tiny(family, tmp_path, **kw)
    except OSError:
        pytest.skip("pool tokenizers not in the local HF cache")


@pytest.fixture(scope="module")
def items():
    return E.load()


# ---------------------------------------------------------------- linear12 head (R1-E0-PROTOCOL c)

@pytest.mark.parametrize("family", ["kev", "laya", "startlux", "qwen_control"])
def test_linear12_head_reads_the_returned_state_and_reloads(family, tmp_path, items):
    w = _tiny(family, tmp_path, head_form="linear12")
    assert "belief" in w.heads and isinstance(w.heads["belief"][0], torch.nn.LayerNorm)
    prompts = [E.prompt_from_dict(it["prompt"]) for it in items[:3]]
    w.eval()
    with torch.no_grad():
        out = w(prompts, return_state=True)
        assert out["belief_logits"].shape == (3, N_BINS) and out["state"].dtype == torch.float32
        assert torch.allclose(out["belief_logits"], w.heads["belief"](out["state"]), atol=1e-5)
        assert "state" not in w(prompts)
    ids = {id(p) for p in M.new_head_parameters(w)}
    assert all(id(p) in ids for p in w.heads["belief"].parameters())
    w.save(tmp_path / "saved")
    w2 = _tiny(family, tmp_path, head_form="linear12")       # same random backbone (it is not saved)
    with torch.no_grad():
        for p in w2.heads["belief"].parameters():
            p.zero_()
    w2.load(tmp_path / "saved")
    w2.eval()
    with torch.no_grad():
        assert torch.equal(w2(prompts)["belief_logits"], out["belief_logits"])


# ---------------------------------------------------------------- token rows (R1-TOKEN-INIT)

def test_new_token_rows_start_at_the_mean_embedding_in_fp32_with_their_own_lr(tmp_path):
    from r1.c3.train.tiny import causal_lm, tokenizer, QWEN
    try:
        tok = tokenizer(*QWEN)
    except OSError:
        pytest.skip("Qwen tokenizer not in the local HF cache")
    lm = causal_lm(True, 0)
    n_vocab = len(tok)
    w0 = lm.get_input_embeddings().weight.detach().clone()
    w = M.build_model("qwen_control", lm, tok)
    new = sorted(w.token_ids.values())
    mean = w0[:n_vocab][[i for i in range(n_vocab) if i not in set(new)]].float().mean(0)
    rows = w._token_rows(torch.tensor(new))
    assert rows.dtype == torch.float32 and torch.allclose(rows, mean.expand_as(rows), atol=1e-6)
    tp = M.token_row_parameters(w)
    assert tp and all(p.dtype == torch.float32 for p in tp)
    assert not {id(p) for p in tp} & {id(p) for p in M.new_head_parameters(w)}
    # a uniform belief at init (identical rows)
    with torch.no_grad():
        p = torch.softmax(w([E.prompt_from_dict(E.load()[0]["prompt"])])["belief_logits"], -1)
    assert torch.allclose(p, torch.full_like(p, 1 / N_BINS), atol=1e-5)
    rows_ = [{"prompt": E.prompt_from_dict(E.load()[0]["prompt"]), "y": torch.full((N_BINS,), 1 / N_BINS)}]
    tr = Trainer(w, rows_, X.belief_loss, TrainConfig(max_steps=1, grad_accum=1, lr=3e-5, head_lr=1e-3, token_lr=1e-4),
                 tmp_path / "t", head_params=M.new_head_parameters(w), token_params=tp)
    lrs = {g["lr"] for g in tr.opt.param_groups}
    assert lrs == {3e-5, 1e-4}                         # no new heads on the control's native readout


# ---------------------------------------------------------------- early stopping

class _Lin(torch.nn.Module):
    """A tiny DecisionModel stand-in: belief = Linear(one-hot of the prompt group)."""
    family = ""

    def __init__(self):
        super().__init__()
        self.heads = torch.nn.ModuleDict({"belief": torch.nn.Linear(4, N_BINS)})

    def trainable_parameters(self):
        return (p for p in self.parameters() if p.requires_grad)

    def forward(self, batch, return_state=False):
        x = torch.stack([torch.nn.functional.one_hot(torch.tensor(int(p) % 4), 4).float() for p in batch])
        return {"belief_logits": self.heads["belief"](x), "action_logit": None}

    def save(self, path):
        path.mkdir(parents=True, exist_ok=True)
        torch.save(self.state_dict(), path / "w.pt")
        return {"files": {}}

    def load(self, path):
        self.load_state_dict(torch.load(path / "w.pt"))
        return {}


def test_early_stopping_restores_the_best_and_does_not_resume_past_it(tmp_path):
    torch.manual_seed(0)
    m = _Lin()
    rows = [{"prompt": str(i), "y": torch.full((N_BINS,), 1 / N_BINS)} for i in range(8)]
    vals = iter([0.6, 0.5, 0.4, 0.45, 0.46, 0.47, 0.1])     # step 0 (the start), then every 2 steps
    snap = {}

    def evaluate(model):
        v = next(vals)
        snap[v] = {k: t.clone() for k, t in model.state_dict().items()}
        return {"val_rps": v}
    cfg = TrainConfig(max_steps=100, epochs=1e9, batch_size=8, grad_accum=1, lr=1e-2, eval_every_steps=2,
                      early_stop_patience=3, keep_checkpoints=1)
    res = Trainer(m, rows, X.belief_loss, cfg, tmp_path / "r", evaluate=evaluate).train()
    assert res["early_stopped"] and res["best_step"] == 4 and res["stopped_at"] == 10
    assert all(torch.equal(t, snap[0.4][k]) for k, t in m.state_dict().items())
    assert len(list((tmp_path / "r" / "ckpt").glob("step_*"))) == 1
    evals = [json.loads(ln) for ln in (tmp_path / "r" / "metrics.jsonl").read_text().splitlines()]
    assert [e["step"] for e in evals if e["kind"] == "eval"] == [0, 2, 4, 6, 8, 10]
    assert json.loads((tmp_path / "r" / "best.json").read_text())["step"] == 4
    res2 = Trainer(m, rows, X.belief_loss, cfg, tmp_path / "r", evaluate=evaluate).train()   # resume: exhausted
    assert res2["stopped_at"] == 10 and res2["best_step"] == 4


# ---------------------------------------------------------------- E0 v2 data and metrics (R1-E0-PROTOCOL a, b)

def test_validation_cells_are_held_out_of_training_and_disjoint_from_test(items):
    tr, va = E.e0_split(items)
    assert va and tr and len(tr) + len(va) == sum(it["split"] == "train" for it in items)
    assert {tuple(it["cell"]) for it in va} == set(E.VAL_CELLS)
    assert not {tuple(it["cell"]) for it in tr} & set(E.VAL_CELLS)
    assert not set(E.VAL_CELLS) & set(E.HELDOUT)


def test_width_slope_against_the_labels_own_std_is_one_for_the_labels(items):
    test = [it for it in items if it["split"] == "test"]
    m = E.e0_metrics_v2(np.array([it["y_soft"] for it in test]), test)
    assert abs(m["width_slope_vs_label"] - 1) < 1e-9 and abs(m["mean_slope_vs_label"] - 1) < 1e-9
    assert m["primary_width"] == "width_slope_vs_label"
    assert m["label_width_slope_vs_s"] == pytest.approx(m["width_slope"])   # the ceiling = the labels' own slope
    assert m["width_slope_vs_label_lb95"] == pytest.approx(1.0) and E.e0_pass_v2(m) is True
    # R1-E0-THRESHOLDS: >= 0.6 (inclusive), lower bound > 0 (strict), mean >= 0.8
    t = E.E0_V2_THRESHOLDS
    assert t == {"width_slope_vs_label_min": 0.6, "width_slope_vs_label_lb95_gt": 0.0, "mean_slope_min": 0.8}
    from r1.c3.train import exam_analyze as A
    rule = A.load_rule()[0]                          # one source of truth: the frozen rule agrees with the code
    assert rule["e0_pass"] == t and rule["e0_bootstrap"] == E.E0_BOOT
    assert rule["e6"]["a4_min_frac_monotone_vs_label"] == E.A4_V2_MIN_FRAC
    ok = {"width_slope_vs_label": 0.6, "width_slope_vs_label_lb95": 1e-6, "mean_slope": 0.8}
    assert E.e0_pass_v2(ok) is True
    assert E.e0_pass_v2({**ok, "width_slope_vs_label": 0.599}) is False
    assert E.e0_pass_v2({**ok, "width_slope_vs_label_lb95": 0.0}) is False
    assert E.e0_pass_v2({**ok, "mean_slope": 0.799}) is False


def test_width_slope_bootstrap_interval_brackets_the_estimate(items):
    test = [it for it in items if it["split"] == "test"]
    rng = np.random.default_rng(0)
    y = np.array([it["y_soft"] for it in test])
    p = 0.5 * y + 0.5 * rng.dirichlet(np.ones(12), size=len(y))        # a noisy predictor
    p[:, 0] = 0
    p /= p.sum(1, keepdims=True)
    m = E.e0_metrics_v2(p, test)
    assert m["width_slope_vs_label_lb95"] < m["width_slope_vs_label"] < m["width_slope_vs_label_ub95"]
    assert E.width_slope_bootstrap(p, test) == E.width_slope_bootstrap(p, test)    # seeded


def test_a4_label_reference(items):
    lab = E.a4_label_std(n=20)
    assert lab.shape == (20, E.A4_STEPS)
    r = E.a4_pass_v2(lab, lab)
    assert r["frac_monotone_vs_label"] == 1.0 and r["median_slope_vs_label"] == pytest.approx(1.0) and r["pass"] is True
    flat = np.repeat(lab[:, :1], E.A4_STEPS, axis=1)
    assert E.a4_pass_v2(flat, lab)["median_slope_vs_label"] == pytest.approx(0.0)
    dec = lab[:, ::-1]
    assert E.a4_pass_v2(dec, lab)["frac_monotone_vs_label"] < 0.5 and not E.a4_pass_v2(dec, lab)["pass"]
    bad = lab.copy()
    bad[:2, -1] = bad[:2, 0] - 1                       # 2 of 20 prompts decrease: 90 % < 95 %
    assert E.a4_pass_v2(bad, lab)["frac_monotone_vs_label"] == 0.9 and E.a4_pass_v2(bad, lab)["pass"] is False


# ---------------------------------------------------------------- A3 budget (R1-A3-BUDGET)

def _word_counter(k):
    return lambda p: k * len(f"{p.state}\n{p.proposal}\n{p.question}\n{' '.join(p.options)}".split())


def test_a3_levels_fill_the_pool_budget_and_fit_every_family():
    counters = {"a": _word_counter(1), "b": _word_counter(2)}    # "b" is the token-hungriest family
    lim = 1024
    a3 = E.a3_probe_budget(counters, n=6, limit=lim)
    assert list(a3["prompts"]) == list(E.A3_FRACS)
    for i, budget in enumerate(a3["budget"]):
        base = a3["tokens"][0.0][i]["b"]
        assert budget == lim - base and a3["prompts"][0.0][i].meta["extra_history_words"] == 0
        prev = -1
        for f in E.A3_FRACS:
            t = a3["tokens"][f][i]
            assert max(t.values()) <= base + f * budget <= lim
            n = a3["prompts"][f][i].meta["extra_history_words"]
            assert f - a3["reached"][f][i] < 0.02          # word-level fill: within ~a word of the target
            assert n >= prev
            prev = n
        assert a3["tokens"][1.0][i]["b"] >= lim - 2           # the maximum level fills the budget


@pytest.mark.parametrize("family", ["kev", "qwen_control", "startlux", "laya"])
def test_budget_counters_match_what_each_wrapper_feeds_the_model(family, tmp_path, items):
    from r1.c3.train import budget as B
    w = _tiny(family, tmp_path)
    if family == "kev":
        c = B.kev_counter(w.tok)
    elif family == "qwen_control":
        c = B.qwen_control_counter(tiny.tokenizer(*tiny.QWEN))
    elif family == "startlux":
        c = B.startlux_counter(w.tok)
    else:
        from laya import common as lc
        shell = M.LayaWrapper.__new__(M.LayaWrapper)
        shell.lc, shell.cfg, shell.tok, shell.max_len, shell.head_max_len = lc, w.cfg, w.tok, 10 ** 9, w.head_max_len
        c = lambda p: len(shell.encode(p)["ids"])  # noqa: E731  (laya_counter reads a checkpoint directory)
    for it in items[:3]:
        p = E.prompt_from_dict(it["prompt"])
        if family == "kev":
            from kev import model as km
            recs, _ = w.records([p])
            want = len(km.encode(w.tok, recs[0], max_state=w.ctx["max_state"], max_branch=w.ctx["max_branch"],
                                 strict=True)["ids"])
        elif family == "qwen_control":
            want = len(w.segments(p)[0])
        elif family == "startlux":
            want = len(w.tok.encode(w.prompt_text(p), add_special_tokens=False))
        else:
            want = len(w.encode(p)["ids"])
        assert c(p) == want


# ---------------------------------------------------------------- E0 v2 end to end (tiny)

@pytest.mark.parametrize("variant", ["fresh", "native"])
def test_e0_v2_runs_both_stages_with_early_stopping(variant, tmp_path):
    w = _tiny("qwen_control", tmp_path, head_form="linear12" if variant == "fresh" else "softmax12")
    rep = X.e0_v2(w, tmp_path / "run", variant=variant, lr=1e-4, token_lr=1e-4, max_steps=4, eval_every=2,
                  patience=1, batch_size=4, n_train=8, n_val=4, n_test=6, stage="final")
    assert rep["protocol"] == "trackp_e0/v2" and rep["n_val"] == 4 and rep["stage"] == "final"
    if variant == "fresh":
        hf = rep["head_fit"]
        assert hf["descriptive"] and hf["method"].startswith("full-batch L-BFGS") and hf["converged"]
        assert hf["lora_starts_from"].startswith("the fresh head")
    assert ("head_fit" in rep) == (variant == "fresh") and ("zero_shot" in rep) == (variant == "native")
    assert rep["lora"]["best_step"] in (0, 2, 4) and "width_slope_vs_label" in rep["lora"]["test"]
    assert (rep["pass"] in (True, False)) == (variant == "fresh")     # the E0 result: soft, final, fresh head
    with pytest.raises(ValueError):
        X.e0_v2(w, tmp_path / "bad2", variant=variant, lr=1e-4, stage="other")
    with pytest.raises(ValueError):
        X.e0_v2(w, tmp_path / "bad", variant="fresh" if variant == "native" else "native", lr=1e-4)


# ---------------------------------------------------------------- temperature scaling (R1-TEMPERATURE)

def test_temperature_scaling_recovers_the_generating_temperature():
    rng = np.random.default_rng(0)
    z = rng.normal(0, 3, (4000, N_BINS))
    y = MT.apply_temperature(z, 2.5)
    assert MT.fit_temperature(z, y) == pytest.approx(2.5, rel=1e-3)
    assert np.allclose(MT.apply_temperature(z, 1.0).sum(-1), 1)


# ---------------------------------------------------------------- Track X marker (R1-TRACKX-MARKER)

def test_gpu_lease_refuses_while_the_track_x_marker_exists(tmp_path):
    marker = tmp_path / "trackx_evidence.active"
    kw = dict(lock_path=tmp_path / "gpu0.lock", log_path=tmp_path / "lease.jsonl", status_text="## Track P",
              check_processes=False, marker_path=marker)
    with R.gpu_lease("ok", **kw) as lease:
        assert lease["job"] == "ok"
    marker.write_text("B1")
    with pytest.raises(R.TrackPStop, match="marker"):
        with R.gpu_lease("refused", **kw):
            pass
    assert "trackx_marker" in json.loads((tmp_path / "lease.jsonl").read_text().splitlines()[0])


def test_a_run_that_never_improves_on_its_start_returns_the_start(tmp_path):
    torch.manual_seed(0)
    m = _Lin()
    start = {k: t.clone() for k, t in m.state_dict().items()}
    rows = [{"prompt": str(i), "y": torch.full((N_BINS,), 1 / N_BINS)} for i in range(8)]
    vals = iter([0.1, 0.2, 0.3, 0.4])
    cfg = TrainConfig(max_steps=100, epochs=1e9, batch_size=8, grad_accum=1, lr=1e-1, eval_every_steps=2,
                      early_stop_patience=3)
    res = Trainer(m, rows, X.belief_loss, cfg, tmp_path / "r", evaluate=lambda _: {"val_rps": next(vals)}).train()
    assert res["best_step"] == 0 and res["stopped_at"] == 6
    assert all(torch.equal(t, start[k]) for k, t in m.state_dict().items())


# ---------------------------------------------------------------- environment pins (R1-ENV-PIN)

def test_environment_check_refuses_other_torch_or_code_commits():
    cfg = {"venv": {"torch": "2.6.0+cu124"}, "code_pins": {"kev": "jaredpalmer/kev@abc"}}
    good = {"torch": "2.6.0+cu124", "packages": {"kev": {"pip_commit": "abc", "path": "/x"}}}
    assert R.check_environment(cfg, good) is good
    with pytest.raises(R.TrackPStop, match="torch"):
        R.check_environment(cfg, {**good, "torch": "2.5.1+cu121"})
    with pytest.raises(R.TrackPStop, match="pinned abc"):
        R.check_environment(cfg, {**good, "packages": {"kev": {"pip_commit": "def", "path": "/x"}}})
    dirty = {"pip_commit": "abc", "path": "/x", "git": {"commit": "abc", "dirty": True}}
    with pytest.raises(R.TrackPStop, match="dirty=True"):
        R.check_environment(cfg, {**good, "packages": {"kev": dirty}})
    assert set(R.environment_record()) >= {"torch", "transformers", "peft", "packages"}


def test_git_commit_lists_dirty_files_with_full_names(tmp_path):
    import subprocess
    run = lambda *a: subprocess.run(["git", "-C", str(tmp_path), *a], check=True, capture_output=True)  # noqa: E731
    run("init", "-q")
    run("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "0")
    for f in ("abc.txt", "def.txt"):
        (tmp_path / f).write_text("1")
    run("add", "abc.txt", "def.txt")
    run("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "1")
    for f in ("abc.txt", "def.txt"):
        (tmp_path / f).write_text("2")          # unstaged changes: porcelain lines start with a space
    rec = R.git_commit(tmp_path)
    assert rec["dirty"] and rec["dirty_files"] == ["abc.txt", "def.txt"]
    run("checkout", "-q", "--", ".")
    assert R.git_commit(tmp_path)["dirty_files"] == [] and not R.git_commit(tmp_path)["dirty"]



def test_lbfgs_head_fit_converges_to_a_stationary_point():
    """R1-E0-HEADFIT: full-batch L-BFGS runs to convergence. LayerNorm's affine times the linear layer makes the fit
    non-convex, so the check is stationarity: Adam started from the L-BFGS solution cannot improve it materially."""
    from r1.c3.train import losses as L
    torch.manual_seed(0)
    X_ = torch.randn(200, 16)
    Y = torch.softmax(X_ @ torch.randn(16, N_BINS), -1)
    head = torch.nn.Sequential(torch.nn.LayerNorm(16), torch.nn.Linear(16, N_BINS))
    fit = X.fit_head_lbfgs(head, X_, Y, X_[:50], Y[:50])
    assert fit["converged"] and fit["outer_iterations"] < 500 and fit["grad_norm"] < 1e-4
    with torch.no_grad():                            # the fitted weights are back in the caller's head
        assert float(L.rps(torch.softmax(head(X_), -1), Y).mean()) == pytest.approx(fit["train_rps"], rel=1e-4)
    w = head.double()
    opt = torch.optim.Adam(w.parameters(), lr=1e-3)
    for _ in range(2000):
        opt.zero_grad()
        loss = L.rps(torch.softmax(w(X_.double()), -1), Y.double()).mean()
        loss.backward()
        opt.step()
    assert float(loss) > fit["train_rps"] * (1 - 1e-3)



def test_head_fit_is_descriptive_and_lora_starts_from_the_fresh_head(tmp_path):
    w = _tiny("qwen_control", tmp_path, head_form="linear12")
    init = {k: t.clone() for k, t in w.heads["belief"].state_dict().items()}
    seen = {}
    orig = X.fit_head_lbfgs

    def spy(head, *a, **k):
        r = orig(head, *a, **k)
        seen["fitted"] = {k_: t.clone() for k_, t in head.state_dict().items()}
        return r
    X.fit_head_lbfgs = spy
    try:
        X.e0_v2(w, tmp_path / "r", variant="fresh", lr=1e-4, max_steps=0, eval_every=1, patience=1, batch_size=4,
                n_train=8, n_val=4, n_test=4, stage="final")
    finally:
        X.fit_head_lbfgs = orig
    assert any(not torch.equal(seen["fitted"][k], init[k]) for k in init)          # the fit moved the head ...
    assert all(torch.equal(w.heads["belief"].state_dict()[k].cpu(), init[k].cpu()) for k in init)  # ... LoRA got the fresh one
    rep = X.e0_v2(_tiny("qwen_control", tmp_path / "b", head_form="linear12"), tmp_path / "s", variant="fresh",
                  lr=1e-4, max_steps=2, eval_every=1, patience=1, batch_size=4, n_train=8, n_val=4, n_test=4,
                  stage="screen", head_fit=False)
    assert "head_fit" not in rep and rep["pass"] is None                          # screen: no head fit, no pass
