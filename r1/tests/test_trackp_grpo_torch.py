"""Track P Stage R-B (GRPO): torch path and a tiny end-to-end run with LoRA (skips without torch)."""
import math

import numpy as np
import pytest

from r1.c3.train import grpo as G

torch = pytest.importorskip("torch")
if not torch.cuda.is_available() and hasattr(torch, "accelerator"):
    # Test-environment shim, CPU only: transformers 5.19 calls torch.accelerator.current_accelerator() at import,
    # which torch 2.6 answers with an error instead of None when no accelerator exists.
    torch.accelerator.current_accelerator = lambda *args, **kwargs: None


def test_torch_surrogate_and_kl_equal_the_numpy_reference():
    rng = np.random.default_rng(0)
    ln, lo, lr = (np.log(rng.uniform(0.05, 0.95, (4, 5))) for _ in range(3))
    mask = (rng.random((4, 5)) > 0.2).astype(float); adv = rng.normal(0, 1, 4)
    t = lambda a: torch.tensor(a, dtype=torch.float64)
    loss, clip = G.clipped_surrogate(t(ln), t(lo), t(adv), t(mask))
    ref_loss, ref_clip = G.np_clipped_surrogate(ln, lo, adv, mask)
    assert float(loss) == pytest.approx(ref_loss) and clip == pytest.approx(ref_clip)
    kl, mean = G.k3_kl(t(ln), t(lr), t(mask))
    ref_kl, ref_mean = G.np_k3(ln, lr, mask)
    assert float(kl) == pytest.approx(ref_kl) and mean == pytest.approx(ref_mean)
    with pytest.raises(ValueError, match="beta"):
        G.grpo_loss(t(ln), t(lo), t(lr), t(adv), t(mask), beta=0.1)


def test_estimator_check_through_autograd():
    """The same §6.3 check with torch autograd of the clipped surrogate at rho = 1 (first epoch)."""
    rng = np.random.default_rng(5)
    z = torch.tensor(rng.normal(0, 1.5, 256), requires_grad=True)
    u = torch.tensor(rng.normal(0, 1, 256))
    exact = torch.autograd.grad((-(torch.sigmoid(z) * u)).sum(), z)[0]
    gen = np.random.default_rng(9)
    acc = torch.zeros(256, dtype=torch.float64)
    for _ in range(64):
        pi = torch.sigmoid(z)
        a = torch.tensor((gen.random((256, 8)) < pi.detach().numpy()[:, None]).astype(float))
        adv = torch.tensor(G.loo_advantages((u[:, None] * a).numpy()))
        logp = (a * torch.log(pi)[:, None] + (1 - a) * torch.log1p(-pi)[:, None]).reshape(-1, 1)
        loss, _ = G.clipped_surrogate(logp, logp.detach(), adv.reshape(-1), torch.ones_like(logp))
        acc += torch.autograd.grad(loss, z)[0] / 8   # loss averages over 256*8 completions; rescale to per-prompt group means x 256
    cos = torch.nn.functional.cosine_similarity(acc, exact, dim=0)
    assert float(cos) >= 0.95


def test_tiny_end_to_end_grpo_with_lora_raises_the_target_probability():
    """A tiny random GPT-2 (built from a config, no download) with a rank-16 LoRA learns, under GRPO with the
    leave-one-out advantage, the clipped surrogate (2 epochs) and the k3 KL (beta 0.02), to emit a target token."""
    transformers = pytest.importorskip("transformers")
    peft = pytest.importorskip("peft")
    torch.manual_seed(0)
    cfg = transformers.GPT2Config(vocab_size=8, n_positions=16, n_embd=32, n_layer=1, n_head=2, bos_token_id=0,
                                  eos_token_id=0, resid_pdrop=0.0, embd_pdrop=0.0, attn_pdrop=0.0)
    base = transformers.GPT2LMHeadModel(cfg)
    ref = transformers.GPT2LMHeadModel(cfg); ref.load_state_dict(base.state_dict())
    model = peft.get_peft_model(base, peft.LoraConfig(r=G.LORA_RANK, lora_alpha=32,
                                                      target_modules=["c_attn", "c_proj", "c_fc"], lora_dropout=0.0))
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.Adam(params, lr=1e-2)
    target, contexts, length = 5, torch.tensor([[1, 2], [3, 4]]), 3

    def logp_fn(ctx, toks, m=model):
        full = torch.cat([ctx, toks], dim=1)
        logits = m(full).logits[:, ctx.shape[1] - 1:-1]
        return torch.log_softmax(logits, -1).gather(-1, toks[..., None])[..., 0]

    def p_target():
        with torch.no_grad():
            return float(torch.softmax(model(contexts).logits[:, -1], -1)[:, target].mean())

    before = p_target()
    rewards = []
    for step in range(30):
        ctx = contexts.repeat_interleave(G.GROUP_SIZE, dim=0)
        with torch.no_grad():
            out = model.generate(ctx, max_new_tokens=length, min_new_tokens=length, do_sample=True,
                                 pad_token_id=0, eos_token_id=None)
        toks = out[:, ctx.shape[1]:]
        r = (toks == target).float().mean(dim=1).numpy().reshape(len(contexts), G.GROUP_SIZE)
        with torch.no_grad():
            lref = logp_fn(ctx, toks, ref)
        batch = G.SampledBatch(ctx, toks, torch.ones_like(toks, dtype=torch.float32), r, lref)
        mons = G.ppo_update(logp_fn, params, opt, batch, beta=0.02)
        assert len(mons) == 2 and all(set(m) >= {"clip_share", "mean_kl", "zero_advantage_share"} for m in mons)
        rewards.append(float(r.mean()))
    assert p_target() > before + 0.05
    assert np.mean(rewards[-5:]) > np.mean(rewards[:5])


class FakeReasoner(torch.nn.Module):
    """Stand-in with ReasonThenBinWrapper's interface: generate() samples word analyses; forward(batch, analyses)
    returns belief logits, an action logit, and per-token analysis log-probabilities with a mask."""
    WORDS = ("up", "down", "same")

    def __init__(self, cap_every=None):
        super().__init__()
        self.belief = torch.nn.Parameter(torch.zeros(12))
        self.action = torch.nn.Parameter(torch.zeros(1))
        self.word = torch.nn.Parameter(torch.zeros(len(self.WORDS)))
        self.cap_every = cap_every
        self.last_generated_tokens, self.last_generated_closed = [], []

    def generate(self, batch, *, temperature=1.0, seed=0):
        g = torch.Generator().manual_seed(seed)
        out, self.last_generated_tokens, self.last_generated_closed = [], [], []
        p = torch.softmax(self.word.detach() / temperature, 0)
        for i, _ in enumerate(batch):
            n = 3
            idx = torch.multinomial(p, n, replacement=True, generator=g).tolist()
            out.append(" ".join(self.WORDS[j] for j in idx))
            capped = self.cap_every is not None and (seed + i) % self.cap_every == 0
            self.last_generated_tokens.append(G.ANALYSIS_MAX_TOKENS if capped else n)
            self.last_generated_closed.append(not capped)     # an unclosed span (cap or EOS) is a format violation
        return out

    def forward(self, batch, analyses):
        lp_words = torch.log_softmax(self.word, 0)
        # each analysis is its word tokens plus one appended closing-tag token (log-prob log 0.5), as ``segments``
        rows = [torch.cat([torch.stack([lp_words[self.WORDS.index(w)] for w in a.split()]),
                           torch.tensor([math.log(0.5)])]) for a in analyses]
        width = max(len(r) for r in rows)
        lp = torch.zeros(len(rows), width); mask = torch.zeros(len(rows), width)
        for i, r in enumerate(rows):
            lp[i, :len(r)] = r; mask[i, :len(r)] = 1.0
        n = len(batch)
        return {"belief_logits": self.belief.expand(n, 12), "action_logit": self.action.expand(n),
                "analysis_token_logprob": lp, "analysis_token_mask": mask,
                "analysis_text_tokens": torch.tensor([len(a.split()) for a in analyses]),
                "analysis_close_tokens": torch.ones(len(analyses), dtype=torch.long)}


def test_rb_group_step_on_the_wrapper_interface():
    import copy
    from r1.c3.train.types import DecisionPrompt
    torch.manual_seed(0)
    policy = FakeReasoner(cap_every=5)
    ref = copy.deepcopy(policy)
    opt = torch.optim.Adam(policy.parameters(), lr=0.05)
    prompts = [DecisionPrompt(state=f"s{i}", proposal=f"p{i}", meta={"proposal_id": f"p{i}"}) for i in range(4)]
    y = np.zeros((4, 12)); y[:, 3] = 1.0                       # label distribution: all mass on bin 3
    u = np.array([1.0, 1.0, 1.0, 1.0])                        # executing pays
    first = None
    for step in range(15):
        out = G.rb_group_step(policy, ref, prompts, y, u, opt, u_max=2.0, lambda_a=0.5, beta=0.02, seed=step)
        assert out["rewards"].shape == (4, G.GROUP_SIZE) and len(out["updates"]) == 2
        assert out["format_violations"] > 0                     # capped analyses are penalised
        first = out["updates"][0]["belief_rps"] if first is None else first
    assert out["updates"][-1]["belief_rps"] < first             # the exact RPS gradient reaches the belief
    assert float(torch.sigmoid(policy.action)) > 0.5            # the decision reward pushes towards executing
    with pytest.raises(ValueError, match="last_generated_closed"):
        class NoCounts(FakeReasoner):
            def generate(self, batch, **kw):
                out = super().generate(batch, **kw); self.last_generated_closed = []; return out
        G.rb_group_step(NoCounts(), ref, prompts, y, u, opt, u_max=2.0, lambda_a=0.5, beta=0.0)


def test_span_token_logprobs_sum_to_the_span_logprob():
    """model.py: the per-token analysis log-probabilities (new) sum to the existing per-span value."""
    from types import SimpleNamespace
    from r1.c3.train.model import BinTokenWrapper
    torch.manual_seed(1)
    head = torch.nn.Linear(6, 11, bias=False)
    fake = SimpleNamespace(lm=SimpleNamespace(get_output_embeddings=lambda: head))
    h = torch.randn(2, 9, 6)
    ids = torch.randint(0, 11, (2, 9))
    spans = [(2, 6), (3, 9)]
    total = BinTokenWrapper._span_logprob(fake, h, ids, spans)
    per_token, mask = BinTokenWrapper._span_token_logprobs(fake, h, ids, spans)
    assert mask.sum(dim=1).tolist() == [4.0, 6.0]
    assert torch.allclose((per_token * mask).sum(dim=1), total, atol=1e-6)


def test_sampled_mask_scores_the_closing_tag_only_when_the_policy_sampled_it():
    out = {"analysis_token_logprob": torch.zeros(3, 5),
           "analysis_token_mask": torch.tensor([[1., 1, 1, 1, 0], [1, 1, 1, 1, 1], [1, 1, 0, 0, 0]]),
           "analysis_text_tokens": torch.tensor([2, 3, 1]), "analysis_close_tokens": torch.tensor([1, 2, 0])}
    m = G.sampled_analysis_mask(out, [True, False, True])
    assert m.tolist() == [[1, 1, 1, 0, 0], [1, 1, 1, 0, 0], [1, 0, 0, 0, 0]]
    with pytest.raises(ValueError, match="analysis_text_tokens"):
        G.sampled_analysis_mask({"analysis_token_mask": out["analysis_token_mask"]}, [True] * 3)


def test_unclosed_analysis_is_a_violation_and_its_forced_tag_is_not_scored():
    """EOS before ``</analysis>`` (short, not capped) is a format violation, like the cap; the PPO mask never includes
    the closing tag ``segments`` appends to an unclosed span."""
    import copy
    from r1.c3.train.types import DecisionPrompt

    class EOSEarly(FakeReasoner):
        def generate(self, batch, **kw):
            out = super().generate(batch, **kw)
            self.last_generated_closed = [False] * len(batch)   # stopped at EOS, 3 tokens, never closed
            return out

    policy = EOSEarly()
    seen = []
    orig = G.grpo_loss

    def spy(lp_new, lp_old, lp_ref, adv, mask, **kw):
        seen.append(mask.clone())
        return orig(lp_new, lp_old, lp_ref, adv, mask, **kw)

    G.grpo_loss = spy
    try:
        prompts = [DecisionPrompt(state="s", proposal="p", meta={"proposal_id": "p"})]
        y = np.zeros((1, 12)); y[0, 2] = 1.0
        out = G.rb_group_step(policy, copy.deepcopy(policy), prompts, y, np.array([1.0]),
                              torch.optim.SGD(policy.parameters(), lr=0.0), u_max=1.0, lambda_a=0.0, beta=0.0)
    finally:
        G.grpo_loss = orig
    assert out["format_violations"] == G.GROUP_SIZE
    assert np.allclose(out["rewards"], out["rewards"][0, 0])    # all penalised alike
    # 3 word tokens scored, the appended tag (column 3) not, then the action token
    assert seen[0][:, :4].tolist() == [[1.0, 1.0, 1.0, 0.0]] * G.GROUP_SIZE and bool((seen[0][:, -1] == 1).all())


def test_rb_group_step_runs_in_eval_mode_and_restores_train_mode():
    import copy
    from r1.c3.train.types import DecisionPrompt
    modes = []

    class Watch(FakeReasoner):
        def generate(self, batch, **kw):
            modes.append(self.training)
            return super().generate(batch, **kw)

    policy = Watch(); policy.train()
    prompts = [DecisionPrompt(state="s", proposal="p", meta={"proposal_id": "p"})]
    G.rb_group_step(policy, copy.deepcopy(policy), prompts, np.eye(12)[:1], np.array([0.5]),
                    torch.optim.SGD(policy.parameters(), lr=0.0), u_max=1.0, lambda_a=0.5, beta=0.0)
    assert modes and not any(modes) and policy.training
