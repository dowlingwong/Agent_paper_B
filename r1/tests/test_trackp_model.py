"""Track P.1.1 / P.1.5: decision-model wrappers and tree packing on tiny random-weight models (CPU only).

Tiny backbones are built from small configs (random weights); the real tokenizers of the pool are read from the
local Hugging Face cache (tokenizer files only, never weights) and the tests skip when they are absent.
ENGINEERING_ONLY; AI-assisted (Claude).
"""
from __future__ import annotations

import json
import os

import pytest
import torch

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
transformers = pytest.importorskip("transformers")
pytest.importorskip("peft")

from r1.c3.labels import N_BINS  # noqa: E402
from r1.c3.train import model as M  # noqa: E402
from r1.c3.train import packing as P  # noqa: E402
from r1.c3.train.types import DecisionPrompt  # noqa: E402

QWEN = ("Qwen/Qwen3.5-0.8B-Base", "dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68")
STARTLUX = ("startlux-models/StartLux-Decision-v1.1-0.8B-Instant", "6496ae641cc71b149ce9dad69bd97f2a44e7bf11")
LAYA = ("convaiinnovations/laya-typed-decisions", "e929ae5cf69bc34259cd2f95c9e91145b818b1f0")


def _tok(repo, rev, subfolder=None):
    from huggingface_hub import hf_hub_download
    from transformers import AutoTokenizer
    try:
        if subfolder:  # a tokenizer folder without its own config.json: load it as a local directory
            path = hf_hub_download(repo, f"{subfolder}/tokenizer.json", revision=rev, local_files_only=True)
            hf_hub_download(repo, f"{subfolder}/tokenizer_config.json", revision=rev, local_files_only=True)
            return AutoTokenizer.from_pretrained(os.path.dirname(path))
        return AutoTokenizer.from_pretrained(repo, revision=rev, local_files_only=True)
    except OSError:
        pytest.skip(f"tokenizer of {repo} not in the local HF cache")


def _qwen35_config(hybrid=True, vocab=248320):
    from transformers import Qwen3_5TextConfig
    types = ["linear_attention", "full_attention", "linear_attention", "full_attention"] if hybrid \
        else ["full_attention"] * 3
    return Qwen3_5TextConfig(vocab_size=vocab, hidden_size=64, intermediate_size=128, num_hidden_layers=len(types),
                             num_attention_heads=4, num_key_value_heads=2, head_dim=16, linear_num_key_heads=2,
                             linear_num_value_heads=4, linear_key_head_dim=16, linear_value_head_dim=16,
                             layer_types=types, tie_word_embeddings=True)


def _causal_lm(hybrid=True, seed=0):
    from transformers import AutoModelForCausalLM
    torch.manual_seed(seed)
    return AutoModelForCausalLM.from_config(_qwen35_config(hybrid), attn_implementation="sdpa").float()


@pytest.fixture(scope="module")
def qwen_tok():
    return _tok(*QWEN)


@pytest.fixture(scope="module")
def tiny_dirs(tmp_path_factory, qwen_tok):
    """Saved tiny Qwen3.5 causal LMs (hybrid and attention-only) with the real Qwen3.5 tokenizer, for kev's loader."""
    out = {}
    for name, hybrid in (("hybrid", True), ("full", False)):
        d = tmp_path_factory.mktemp(f"qwen35_{name}")
        _causal_lm(hybrid).save_pretrained(d)
        qwen_tok.save_pretrained(d)
        out[name] = str(d)
    return out


def prompts(n=3, group="g1"):
    st = "node digits_mlp; budget 4 of 20 used; incumbent lr=0.01, hidden=64; history: t2 lr 0.1->0.01 kept (+0.6)"
    return [DecisionPrompt(state=st, proposal=f"set hidden_units from 64 to {32 * (i + 1)}", group=group,
                           meta={"proposal_id": f"p{i}"}) for i in range(n)]


def check_out(out, n, action=True):
    assert out["belief_logits"].shape == (n, N_BINS)
    p = torch.softmax(out["belief_logits"], -1)
    assert torch.allclose(p.sum(-1), torch.ones(n), atol=1e-5)
    assert torch.isfinite(out["belief_logits"]).all()
    if action:
        assert out["action_logit"].shape == (n,)
    else:
        assert out["action_logit"] is None


def roundtrip(wrapper, make, batch, tmp_path, **fw):
    wrapper.eval()
    with torch.no_grad():
        ref = wrapper(batch, **fw)
    rec = wrapper.save(tmp_path / "ckpt")
    assert rec["files"] and all(len(v) == 64 for v in rec["files"].values())
    assert "adapter/adapter_model.safetensors" in rec["files"] and "heads.safetensors" in rec["files"]
    fresh = make()
    fresh.load(tmp_path / "ckpt")
    fresh.eval()
    with torch.no_grad():
        got = fresh(batch, **fw)
    assert torch.equal(ref["belief_logits"], got["belief_logits"])
    if ref["action_logit"] is not None:
        assert torch.equal(ref["action_logit"], got["action_logit"])
    # a manifest that drops a loaded file, or an adapter missing keys, is refused (STOP 1 review #8)
    man_path = tmp_path / "ckpt" / M.MANIFEST
    man = json.loads(man_path.read_text())
    dropped = dict(man, files={k: v for k, v in man["files"].items() if k != M.HEADS_FILE})
    man_path.write_text(json.dumps(dropped))
    with pytest.raises(M.IntegrityError, match="not recorded"):
        make().load(tmp_path / "ckpt")
    man_path.write_text(json.dumps(man))
    from safetensors.torch import load_file, save_file
    ad_path = tmp_path / "ckpt" / M.ADAPTER_FILE
    full = ad_path.read_bytes()
    ad = load_file(str(ad_path))
    save_file(dict(list(ad.items())[1:]), str(ad_path))
    partial = dict(man, files={**man["files"], M.ADAPTER_FILE: M.sha256_file(ad_path)})
    man_path.write_text(json.dumps(partial))
    with pytest.raises(M.IntegrityError, match="lacks"):
        make().load(tmp_path / "ckpt")
    ad_path.write_bytes(full)
    man_path.write_text(json.dumps(man))
    # tampering with any recorded file is refused
    heads = tmp_path / "ckpt" / "heads.safetensors"
    heads.write_bytes(heads.read_bytes()[:-1] + bytes([heads.read_bytes()[-1] ^ 1]))
    with pytest.raises(M.IntegrityError):
        make().load(tmp_path / "ckpt")
    return ref


def _perturb(wrapper):
    """Make adapter and heads non-trivial (LoRA B starts at zero), so a round trip that drops them would show."""
    g = torch.Generator().manual_seed(7)
    with torch.no_grad():
        for p in wrapper.trainable_parameters():
            p.add_(0.05 * torch.randn(p.shape, generator=g))


# ---------------------------------------------------------------- belief head forms

def test_cumulative_head_is_a_monotone_distribution():
    torch.manual_seed(0)
    raw = torch.randn(64, M.N_CUM) * 3
    p = M.cumulative_probs(raw)
    assert p.shape == (64, N_BINS) and (p > 0).all()          # every bin keeps mass (monotone by construction)
    assert torch.allclose(p.sum(-1), torch.ones(64), atol=1e-6)
    assert torch.allclose(p[:, 0], torch.sigmoid(raw[:, 0]))
    # the parametrisation reproduces any strictly decreasing threshold sequence P(z > e_k), differenced into bins
    s = torch.sigmoid(torch.linspace(3, -3, M.N_EDGES))[None]
    l = torch.logit(s)
    inv_softplus = lambda y: y + torch.log(-torch.expm1(-y))  # noqa: E731
    raw2 = torch.cat([torch.full((1, 1), -50.0), l[:, :1], inv_softplus(l[:, :-1] - l[:, 1:])], 1)
    q = M.cumulative_probs(raw2)[0, 1:]
    expect = torch.cat([1 - s[0, :1], s[0, :-1] - s[0, 1:], s[0, -1:]])
    assert torch.allclose(q, expect, atol=1e-6)


@pytest.mark.parametrize("form", M.HEAD_FORMS)
def test_head_forms_can_learn_from_free_logits(form):
    """Learnability (STOP 1 review): free per-row raw outputs fitted to one-bin-heavy soft targets reach the target;
    no bin carrying label mass stays at zero."""
    torch.manual_seed(0)
    n = 64
    y = torch.full((n, N_BINS), 0.01)
    y[torch.arange(n), 1 + torch.arange(n) % 11] += 1 - 0.01 * N_BINS
    raw = torch.zeros(n, N_BINS if form == "softmax12" else M.N_CUM).normal_(0, 2).requires_grad_(True)
    opt = torch.optim.Adam([raw], lr=0.05)
    lin = torch.nn.Identity()
    for _ in range(400):
        lg = raw if form == "softmax12" else M.belief_logits_from(form, None, lin, raw)
        loss = -(y * torch.log_softmax(lg, -1)).sum(-1).mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
    lg = raw if form == "softmax12" else M.belief_logits_from(form, None, lin, raw)
    p = torch.softmax(lg, -1).detach()
    entropy = -(y * torch.log(y)).sum(-1).mean()
    assert float(loss) < float(entropy) + 0.05
    assert (p[y > 0.05] > 0.5).all()


# ---------------------------------------------------------------- Kev

@pytest.mark.parametrize("form", M.HEAD_FORMS)
def test_pointer_wrapper_shapes_and_roundtrip(tiny_dirs, qwen_tok, tmp_path, form):
    make = lambda: M.build_model("kev", tiny_dirs["hybrid"], qwen_tok, head_form=form)  # noqa: E731
    torch.manual_seed(0)
    w = make()
    assert w.kev.hybrid and not w.packing
    _perturb(w)
    batch = prompts(3) + [DecisionPrompt(state="another state", proposal="set lr from 0.01 to 0.02")]
    check_out(w(batch), 4)
    roundtrip(w, make, batch, tmp_path)


def test_pointer_wrapper_grouping_changes_no_logit(tiny_dirs, qwen_tok):
    torch.manual_seed(0)
    w = M.build_model("kev", tiny_dirs["hybrid"], qwen_tok)
    _perturb(w)
    w.eval()
    grouped = prompts(3, group="g")
    alone = prompts(3, group="")
    recs, _ = w.records(grouped)
    assert len(recs) == 1 and len(recs[0]["questions"]) == 3
    with torch.no_grad():
        a, b = w(grouped), w(alone)
    assert torch.allclose(a["belief_logits"], b["belief_logits"], atol=1e-5)


def test_pointer_wrapper_trains_lora_and_heads_only(tiny_dirs, qwen_tok):
    w = M.build_model("kev", tiny_dirs["hybrid"], qwen_tok)
    names = [n for n, p in w.named_parameters() if p.requires_grad]
    assert names and all("lora_" in n or n.startswith("heads.") or ".head." in n or n.startswith("kev.head")
                         for n in names)
    adapter = {n for n in names if "lora_" in n}
    assert any("in_proj_qkv" in n for n in adapter) and any("q_proj" in n for n in adapter)  # DeltaNet + attention
    out = w(prompts(2))
    (out["belief_logits"].logsumexp(-1).sum() + out["action_logit"].sum()).backward()
    assert all(p.grad is not None for n, p in w.named_parameters() if p.requires_grad and "lora_B" in n)


def test_pointer_wrapper_warm_start_from_a_kev_checkpoint(tiny_dirs, qwen_tok, tmp_path):
    """A Kev-format run directory (adapter + head.pt, kev.checkpoint's layout) loads through Checkpoint.warm_start."""
    from kev.checkpoint import Meta, write_meta
    torch.manual_seed(0)
    src = M.build_model("kev", tiny_dirs["hybrid"], qwen_tok, action_head=False)
    _perturb(src)
    run = tmp_path / "kevrun"
    src.kev.lm.save_pretrained(str(run))
    write_meta(str(run), Meta(base="tiny/qwen35", head=src.kev.head.state_dict(), lora=M.LORA_R, head_dim=256))
    torch.manual_seed(1)
    dst = M.build_model("kev", tiny_dirs["hybrid"], qwen_tok, action_head=False, base_name="tiny/qwen35",
                        init_from=str(run))
    assert dst.provenance["init_from"] == str(run)
    src.eval(), dst.eval()
    with torch.no_grad():
        assert torch.allclose(src(prompts(2))["belief_logits"], dst(prompts(2))["belief_logits"], atol=1e-6)
    with pytest.raises(ValueError):  # base mismatch is refused before anything loads
        M.build_model("kev", tiny_dirs["hybrid"], qwen_tok, base_name="other/base", init_from=str(run))


def test_pointer_wrapper_refuses_a_checkpoint_of_another_base_revision(tiny_dirs, qwen_tok, tmp_path):
    """The pinned base revision (config ``base_revision``) is compared with the checkpoint's (STOP 1 review #7)."""
    from kev.checkpoint import Meta, write_meta
    src = M.build_model("kev", tiny_dirs["hybrid"], qwen_tok, action_head=False)
    run = tmp_path / "kevrun"
    src.kev.lm.save_pretrained(str(run))
    write_meta(str(run), Meta(base="tiny/qwen35", base_revision="a" * 40, head=src.kev.head.state_dict(),
                              lora=M.LORA_R, head_dim=256))
    ok = M.build_model("kev", tiny_dirs["hybrid"], qwen_tok, action_head=False, base_name="tiny/qwen35",
                       base_revision="a" * 40, init_from=str(run))
    assert ok.provenance["init_from"] == str(run)
    with pytest.raises(ValueError):
        M.build_model("kev", tiny_dirs["hybrid"], qwen_tok, action_head=False, base_name="tiny/qwen35",
                      base_revision="b" * 40, init_from=str(run))


def test_pointer_wrapper_packs_on_attention_only_bases(tiny_dirs, qwen_tok):
    torch.manual_seed(0)
    w = M.build_model("kev", tiny_dirs["full"], qwen_tok)
    assert w.packing and not w.kev.hybrid
    _perturb(w)
    w.eval()
    with torch.no_grad():
        packed, alone = w(prompts(3, group="g")), w(prompts(3, group=""))
    assert torch.allclose(packed["belief_logits"], alone["belief_logits"], atol=1e-5)


# ---------------------------------------------------------------- Qwen control (bin tokens) and P.6

@pytest.mark.parametrize("form", M.HEAD_FORMS)
def test_bin_token_wrapper_shapes_and_roundtrip(qwen_tok, tmp_path, form):
    def make():
        torch.manual_seed(0)
        return M.build_model("qwen_control", _causal_lm(), _tok(*QWEN), head_form=form)
    w = make()
    ids = w.token_ids
    assert len(set(ids.values())) == N_BINS + 2
    _perturb(w)
    batch = prompts(3)
    check_out(w(batch), 3)
    roundtrip(w, make, batch, tmp_path)


def test_bin_token_belief_is_the_lm_head_restricted_to_bin_tokens(qwen_tok):
    torch.manual_seed(0)
    w = M.build_model("qwen_control", _causal_lm(), _tok(*QWEN))
    _perturb(w)
    w.eval()
    p = prompts(1)[0]
    ids, bpos, apos, _ = w.segments(p)
    with torch.no_grad():
        out = w([p])
        full = w.lm(input_ids=torch.tensor([ids])).logits[0]
    assert torch.allclose(out["belief_logits"][0], full[bpos, w.bin_ids], atol=1e-4)
    assert torch.allclose(out["action_logit"][0], full[apos, w.act_ids[0]] - full[apos, w.act_ids[1]], atol=1e-4)
    # the action position comes after the belief position and never changes it
    assert apos > bpos


def test_bin_token_rows_are_trainable_and_saved(qwen_tok, tmp_path):
    torch.manual_seed(0)
    w = M.build_model("qwen_control", _causal_lm(), _tok(*QWEN))
    out = w(prompts(2))
    out["belief_logits"].logsumexp(-1).sum().backward()
    tt = [n for n, p in w.named_parameters() if p.requires_grad and "trainable_tokens" in n]
    assert tt, "the reserved token rows must train"


def test_reason_then_bin_generates_and_scores_analyses(qwen_tok):
    torch.manual_seed(0)
    w = M.build_model("qwen_reason", _causal_lm(), _tok(*QWEN))
    w.eval()
    batch = prompts(2)
    texts = w.generate(batch, seed=3)
    assert len(texts) == 2 and all(0 < n <= M.ANALYSIS_MAX_TOKENS for n in w.last_generated_tokens)
    with torch.no_grad():
        out = w(batch, analyses=["the edit halves the width", "no change expected"])
    check_out(out, 2)
    assert out["analysis_logprob"].shape == (2,) and (out["analysis_logprob"] < 0).all()
    with pytest.raises(ValueError):
        w(batch)


# ---------------------------------------------------------------- StartLux

@pytest.fixture(scope="module")
def startlux_tok():
    return _tok(*STARTLUX)


def test_startlux_bidirectional_self_checks_and_mask():
    m = _causal_lm()
    bd = M.StartLuxBidirectional(m.model)
    rep = bd.check()
    assert rep["causal_max_diff"] <= 1e-5 and rep["late_token_reach"] > 0
    with pytest.raises(ValueError):  # left padding refused
        ids = torch.tensor([[1, 2, 3]])
        bd.hidden(ids, torch.tensor([[0, 1, 1]]))


@pytest.mark.parametrize("form", M.HEAD_FORMS)
def test_startlux_wrapper_shapes_and_roundtrip(startlux_tok, tmp_path, form):
    def make():
        torch.manual_seed(0)
        return M.build_model("startlux", _causal_lm(), startlux_tok, head_form=form)
    w = make()
    assert w.check_report["late_token_reach"] > 0
    _perturb(w)
    batch = prompts(3)
    text = w.prompt_text(batch[0])
    assert text.endswith("<think>\n\n</think>\n\n") and "L) standardised change z in (3,inf]" in text
    check_out(w(batch), 3)
    roundtrip(w, make, batch, tmp_path)


def test_startlux_readout_is_letter_logits_at_the_last_token(startlux_tok):
    torch.manual_seed(0)
    w = M.build_model("startlux", _causal_lm(), startlux_tok)
    w.eval()
    p = prompts(1)[0]
    ids = torch.tensor([startlux_tok.encode(w.prompt_text(p), add_special_tokens=False)])
    with torch.no_grad():
        h = w.bidir.hidden(ids)[0, -1]
        expect = w.model.lm_head(h)[w.letter_ids]
        got = w([p])["belief_logits"][0]
    assert torch.allclose(got, expect.float(), atol=1e-4)


# ---------------------------------------------------------------- Laya

@pytest.fixture(scope="module")
def laya_parts():
    from transformers import ModernBertConfig
    tok = _tok(*LAYA, subfolder="tokenizer")
    from huggingface_hub import hf_hub_download
    cfg = json.loads(open(hf_hub_download(LAYA[0], "rl_agent_config.json", revision=LAYA[1],
                                          local_files_only=True)).read())
    cfg["head_layers"] = 1
    enc = ModernBertConfig(vocab_size=len(tok), hidden_size=64, intermediate_size=128, num_hidden_layers=3,
                           num_attention_heads=4, global_attn_every_n_layers=3, local_attention=16,
                           max_position_embeddings=1024, pad_token_id=tok.pad_token_id,
                           cls_token_id=tok.cls_token_id, sep_token_id=tok.sep_token_id)
    return cfg, enc, tok


@pytest.mark.parametrize("form", M.HEAD_FORMS)
def test_laya_wrapper_shapes_and_roundtrip(laya_parts, tmp_path, form):
    cfg, enc, tok = laya_parts

    def make():
        torch.manual_seed(0)
        return M.build_model("laya", (cfg, enc), tok, head_form=form)
    w = make()
    _perturb(w)
    batch = prompts(3)
    out = w(batch)
    check_out(out, 3)
    assert out["truncated"] == [False] * 3
    roundtrip(w, make, batch, tmp_path)


def test_laya_loads_a_checkpoint_directory_with_the_shipped_loader_rule(laya_parts, tmp_path):
    """build_model("laya", <dir>) reads rl_agent_config.json, encoder/, tokenizer/ and model.safetensors (strict)."""
    from safetensors.torch import save_file
    cfg, enc, tok = laya_parts
    torch.manual_seed(3)
    core = M._laya_core(cfg, enc, None)
    d = tmp_path / "laya_ckpt"
    (d / "encoder").mkdir(parents=True)
    enc.save_pretrained(str(d / "encoder"))
    tok.save_pretrained(str(d / "tokenizer"))
    (d / "rl_agent_config.json").write_text(json.dumps(cfg))
    save_file({k: v.contiguous() for k, v in core.state_dict().items()}, str(d / "model.safetensors"))
    w = M.build_model("laya", str(d))
    base = w.core.encoder.get_base_model().state_dict()
    for k, v in core.encoder.state_dict().items():  # peft keeps LoRA-wrapped weights under .base_layer
        got = base.get(k)
        if got is None:
            head, _, leaf = k.rpartition(".")
            got = base[f"{head}.base_layer.{leaf}"]
        assert torch.equal(got, v), k
    for name in ("head", "scorer"):
        for k, v in getattr(core, name).state_dict().items():
            assert torch.equal(getattr(w.core, name).state_dict()[k], v)
    check_out(w(prompts(2)), 2)
    with pytest.raises(ValueError, match="encoder/ directory"):
        M._laya_core(cfg, enc, str(d / "model.safetensors"))


def test_laya_long_state_is_cut_but_never_the_edit(laya_parts):
    cfg, enc, tok = laya_parts
    torch.manual_seed(0)
    w = M.build_model("laya", (cfg, enc), tok)
    p = DecisionPrompt(state="history line\n" * 2000, proposal="set lr from 0.01 to 0.02")
    e = w.encode(p)
    assert e["truncated"] and len(e["ids"]) <= w.max_len
    assert "set lr from 0.01 to 0.02" in tok.decode(e["ids"])


# ---------------------------------------------------------------- tree packing (spec §2.4)

def test_tree_mask_matches_the_spec_formula_and_kev():
    from kev.model import branch_mask
    lay = P.tree_layout([1, 2, 3], [[4, 5], [6], [7, 8, 9]])
    assert lay.pos == [0, 1, 2, 3, 4, 3, 3, 4, 5] and lay.last == [4, 5, 8]
    allow = P.tree_mask([lay.seg])[0, 0] == 0
    g = lay.seg
    for i in range(len(g)):
        for j in range(len(g)):
            assert bool(allow[i, j]) == (j <= i and (g[j] == 0 or g[j] == g[i]))
    assert torch.equal(P.tree_mask([lay.seg]), branch_mask(lay.seg, "cpu"))


def test_packed_equals_unpacked_on_a_full_attention_model():
    torch.manual_seed(0)
    backbone = _causal_lm(hybrid=False).model.eval()
    g = torch.Generator().manual_seed(1)
    rnd = lambda n: torch.randint(0, 1000, (n,), generator=g).tolist()  # noqa: E731
    layouts, refs = [], []
    for nb in (2, 4):
        state, branches = rnd(11), [rnd(3 + k) for k in range(nb)]
        layouts.append(P.tree_layout(state, branches))
        refs.append(P.unpacked_hidden(backbone, state, branches))
    with torch.no_grad():
        packed = P.packed_hidden(backbone, layouts)  # two right-padded sequences in one batch
    for a, b in zip(packed, refs):
        assert float((a - b).abs().max()) <= P.TOL_FP32
    # branch order does not matter with tree-depth positions
    state, branches = rnd(8), [rnd(4), rnd(6), rnd(2)]
    with torch.no_grad():
        fwd = P.packed_hidden(backbone, [P.tree_layout(state, branches)])[0]
        rev = P.packed_hidden(backbone, [P.tree_layout(state, branches[::-1])])[0]
    assert float((fwd - rev.flip(0)).abs().max()) <= P.TOL_FP32
    assert P.supports_packing(backbone) == (True, "")


def test_packing_is_refused_on_a_qwen35_hybrid():
    backbone = _causal_lm(hybrid=True).model
    ok, reason = P.supports_packing(backbone)
    assert not ok and "linear-attention" in reason


def test_laya_lora_targets_and_trainable_head(laya_parts):
    cfg, enc, tok = laya_parts
    w = M.build_model("laya", (cfg, enc), tok)
    names = [n for n, p in w.named_parameters() if p.requires_grad]
    lora = [n for n in names if "lora_" in n]
    assert any(".attn.Wqkv." in n for n in lora) and any(".attn.Wo." in n for n in lora)
    assert any(".mlp.Wi." in n for n in lora) and any(".mlp.Wo." in n for n in lora)
    assert any(n.startswith("heads.laya_scorer") for n in names)
    assert not any("act_head" in n for n in names)  # Laya's own escalate head is not used


@pytest.mark.parametrize("family", ["kev", "qwen_control"])
def test_gradient_checkpointing_trains(family, tiny_dirs, qwen_tok):
    torch.manual_seed(0)
    w = M.build_model("kev", tiny_dirs["hybrid"], qwen_tok) if family == "kev" else \
        M.build_model("qwen_control", _causal_lm(), _tok(*QWEN))
    w.enable_gradient_checkpointing()
    w.train()
    out = w(prompts(2))
    (out["belief_logits"].logsumexp(-1).sum() + out["action_logit"].sum()).backward()
    assert any(p.grad is not None and float(p.grad.abs().sum()) > 0 for n, p in w.named_parameters() if "lora_B" in n)


@pytest.mark.parametrize("form", M.HEAD_FORMS)
@pytest.mark.parametrize("family", ["kev", "laya", "startlux", "qwen_control"])
def test_every_family_and_head_form_learns_a_fixed_batch(family, form, tmp_path):
    """STOP 1 review: a fixed-batch overfit from random init reduces the soft CE, and every bin keeps mass."""
    from r1.c3.train import losses as L
    from r1.c3.train import spike as S
    from r1.c3.train import tiny
    try:
        m = tiny.build_tiny(family, tmp_path, head_form=form)
    except OSError:
        pytest.skip("pool tokenizer not in the local HF cache")
    rows = S.toy_rows(4)
    y = torch.stack([r["y"] for r in rows])
    opt = torch.optim.Adam(list(m.trainable_parameters()), lr=1e-2)
    m.train()
    losses = []
    for _ in range(40):
        p = L.softmax_probs(m([r["prompt"] for r in rows])["belief_logits"])
        loss = L.soft_ce(p, y).mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
        losses.append(float(loss.detach()))
    assert losses[-1] < losses[0] - 0.05 and losses[-1] < 3.0, losses[::10]
    assert (p.detach() > 0).all()


def test_laya_native_readout_equals_layas_own_forward(laya_parts):
    """STOP 1 review #9: ``LayaWrapper._core_forward`` reproduces ``laya.common.DecisionModel.forward``'s logits."""
    cfg, enc, tok = laya_parts
    torch.manual_seed(0)
    w = M.build_model("laya", (cfg, enc), tok)
    _perturb(w)
    w.eval()
    batch = prompts(3)
    encs = [w.encode(p) for p in batch]
    L = max(len(e["ids"]) for e in encs)
    ids = torch.full((3, L), tok.pad_token_id, dtype=torch.long)
    att = torch.zeros((3, L), dtype=torch.long)
    for i, e in enumerate(encs):
        ids[i, :len(e["ids"])] = torch.tensor(e["ids"])
        att[i, :len(e["ids"])] = 1
    marker_pos = torch.tensor([e["markers"] for e in encs])
    marker_mask = torch.ones_like(marker_pos, dtype=torch.bool)
    qtype = torch.full((3,), w.lc.QTYPES["choice"])
    with torch.no_grad():
        theirs = w.core(ids, att, marker_pos, marker_mask, qtype)[0]
        ours = w(batch)["belief_logits"]
    assert torch.allclose(ours, theirs.float(), atol=1e-5)
