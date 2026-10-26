"""Decision-model wrappers (RUNBOOK Track P.1.1; spec §2, §2.3, §2.5, §4). ENGINEERING_ONLY; AI-assisted (Claude).

Every wrapper takes a list of ``DecisionPrompt`` (``types.py``), renders it in its family's native format and
returns ``{"belief_logits": [N, 12], "action_logit": [N] | None}``; ``softmax(belief_logits)`` is the belief in the
fixed ``BIN_OPTIONS`` order. ``save``/``load`` write and read the adapter and heads only (never the base), with a
manifest of sha256 digests that ``load`` verifies before anything is parsed.

Families (spec §2.2):

* ``PointerWrapper`` (Kev): ``kev.model`` @ the pinned commit does the encoding, special tokens, Kev's pointer head
  and the row form on hybrid (Gated DeltaNet) bases. Mapping: Kev's *state* = ``prompt.state`` (the loop state shared
  by every proposal on it); each proposal is one Kev *question* whose instruction is ``proposal + question`` and whose
  options are the 12 bins. Prompts with the same non-empty ``group`` and identical state share one Kev record (Kev's
  own branch packing); on hybrid bases every question runs as its own causal row, so grouping changes no logit.
  A released checkpoint (``init_from``) is warm-started with ``kev.checkpoint.Checkpoint.warm_start``, which checks
  base, revision, LoRA rank and head size before loading. Action head: Linear(hidden -> 1) on the ``<decide>`` state.
* ``HeadWrapper`` (Laya, StartLux): the family's own 12-option readout. Laya: ``laya.common.build_sequence`` (choice
  question, our 12 options) and its typed-decision head (head layers + scorer at the ``[MASK]`` markers); LoRA on the
  ModernBERT encoder, the decision head trains in full; action head on the ``[CLS]`` state after the head layers.
  StartLux Instant: the trained prompt (``startlux_decide.prompt``: system line, Evidence / Question / lettered
  Options, thinking-off suffix), option-letter logits at the last token from the tied output embeddings, with
  prompt-bidirectional attention in the full-attention layers (see ``StartLuxBidirectional``); action head on the
  last token.
* ``BinTokenWrapper`` (Qwen3.5 control): reserved tokens ``<b0>…<b11>``, ``<exec>``, ``<skip>``; belief = LM-head
  logits restricted to the bin tokens at the belief position; action = logit(<exec>) - logit(<skip>) at the action
  position, both read in one causal pass (the action position comes after the belief position, so it never changes
  the belief). The new token rows train through peft ``trainable_token_indices`` (tied embeddings: the LM head reads
  the same rows).
* ``ReasonThenBinWrapper`` (P.6): ``BinTokenWrapper`` with an ``<analysis>…</analysis>`` span (≤ 256 tokens) before the
  belief position: ``generate`` samples analyses, ``forward(batch, analyses=...)`` scores given ones teacher-forced
  and also returns their token log-probabilities. The Kev (pointer) variant needs Kev's base LM head, which
  ``kev.model`` drops; not built (raises).

Belief head forms (spec §2.3): ``softmax12`` (the family's native 12 logits) and ``cumulative11`` (a Linear(hidden ->
11) on the readout state: one no-op Bernoulli plus one threshold sigmoid P(z > e_k) per finite bin edge — 10 with
``labels.EDGES`` — made monotone by a cumulative max from the right and differenced into bins 1..11).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterator, Sequence

import numpy as np
import torch
import torch.nn as nn

from r1.c3.labels import EDGES, N_BINS
from r1.c3.train.types import DecisionPrompt

MODEL_VERSION = "trackp_model/v1"
FAMILIES = ("kev", "laya", "startlux", "qwen_control", "qwen_reason")
HEAD_FORMS = ("softmax12", "cumulative11")
N_EDGES = int(np.isfinite(EDGES).sum())  # 10 finite edges between bins 1..11
N_CUM = 1 + N_EDGES                        # cumulative-11: no-op Bernoulli + one sigmoid per finite edge
assert N_CUM == 11

# spec §4: LoRA r = 16, alpha = 32, dropout 0.05; attention q/k/v/o + MLP up/down/gate (+ DeltaNet on Qwen3.5 hybrids)
LORA_R, LORA_ALPHA, LORA_DROPOUT = 16, 32, 0.05
ATTN_MLP = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
DELTANET = ["in_proj_qkv", "in_proj_z", "in_proj_a", "in_proj_b", "out_proj"]  # names as in Kev's adapter_config
MODERNBERT = ["Wqkv", "Wo", "Wi"]  # ModernBERT attention Wqkv/Wo and MLP Wi/Wo
ANALYSIS_MAX_TOKENS = 256
BIN_TOKENS = tuple(f"<b{k}>" for k in range(N_BINS))
EXEC_TOKEN, SKIP_TOKEN = "<exec>", "<skip>"
MANIFEST = "manifest.json"
ADAPTER_FILE = "adapter/adapter_model.safetensors"
HEADS_FILE = "heads.safetensors"
EPS = 1e-6
LOG_EPS = 1e-12


class IntegrityError(RuntimeError):
    """A saved file does not match the sha256 recorded in its manifest."""


def sha256_file(path: Path | str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_hybrid(config) -> bool:
    """Gated DeltaNet (linear-attention) layers present: no custom attention mask, no tree packing (spec §2.4)."""
    return "linear_attention" in set(getattr(config, "layer_types", None) or [])


def lora_targets(config, family: str) -> list[str]:
    if family == "laya":
        return list(MODERNBERT)
    return ATTN_MLP + (DELTANET if is_hybrid(config) else [])


def lora_config(targets, **extra):
    from peft import LoraConfig
    return LoraConfig(task_type="FEATURE_EXTRACTION", r=LORA_R, lora_alpha=LORA_ALPHA, lora_dropout=LORA_DROPOUT,
                      target_modules=list(targets), **extra)


# ---------------------------------------------------------------- belief head forms (spec §2.3)

def cumulative_probs(raw: torch.Tensor) -> torch.Tensor:
    """[N, 11] raw outputs -> [N, 12] probabilities. raw[:, 0]: logit of the no-op bin (Bernoulli). The 10 threshold
    sigmoids S_k = P(z > e_k) over the finite edges (ascending) are monotone *by construction*: logit S_1 = raw[:, 1],
    logit S_{k+1} = logit S_k - softplus(raw[:, k+1]), so every bin keeps positive mass and a gradient (a hard
    cumulative max over free sigmoids leaves bins at exactly zero with no gradient to reopen them — STOP 1 review).
    The spec's cumulative max (non-increasing from the left) is kept as a guard; it is the identity here.
    Bins: 1 = 1 - S_1, k+1 = S_k - S_{k+1}, 11 = S_last."""
    pi = torch.sigmoid(raw[:, 0])
    steps = torch.nn.functional.softplus(raw[:, 2:])
    logit_s = torch.cat([raw[:, 1:2], raw[:, 1:2] - torch.cumsum(steps, dim=1)], dim=1)
    s = torch.sigmoid(logit_s)
    s = torch.flip(torch.cummax(torch.flip(s, [1]), dim=1).values, [1])   # guard; identity for this parametrisation
    ones, zeros = torch.ones_like(s[:, :1]), torch.zeros_like(s[:, :1])
    cdf_gt = torch.cat([ones, s, zeros], dim=1)        # P(z > e) at e = -inf, e_1..e_10, +inf
    q = cdf_gt[:, :-1] - cdf_gt[:, 1:]                  # bins 1..11
    return torch.cat([pi[:, None], (1 - pi)[:, None] * q], dim=1)


def belief_logits_from(form: str, native: torch.Tensor | None, cum: nn.Module | None, h: torch.Tensor) -> torch.Tensor:
    if form == "softmax12":
        if native is None or native.shape[-1] != N_BINS:
            raise ValueError("softmax12 needs the family's 12 native option logits")
        return native.float()
    p = cumulative_probs(cum(h.float()))
    return torch.log(p + LOG_EPS)   # softmax(log(p + eps)) = (p + eps) / sum: no clamp, the gradient never vanishes


# ---------------------------------------------------------------- shared base

class _Wrapper(nn.Module):
    family = ""
    packing = False

    def __init__(self, head_form: str = "softmax12", action_head: bool = True):
        super().__init__()
        if head_form not in HEAD_FORMS:
            raise ValueError(f"head_form must be one of {HEAD_FORMS}")
        self.head_form, self.with_action = head_form, action_head
        self.heads = nn.ModuleDict()  # everything here is saved with the adapter

    def _add_heads(self, d: int, linear_action: bool = True) -> None:
        if self.head_form == "cumulative11":
            self.heads["cumulative"] = nn.Linear(d, N_CUM)
        if self.with_action and linear_action:
            self.heads["action"] = nn.Linear(d, 1)

    @property
    def device(self):
        return next(self.parameters()).device

    def trainable_parameters(self) -> Iterator[nn.Parameter]:
        return (p for p in self.parameters() if p.requires_grad)

    def enable_gradient_checkpointing(self) -> None:
        self._peft().base_model.model.gradient_checkpointing_enable(
            gradient_checkpointing_kwargs={"use_reentrant": False})

    def _peft(self):
        raise NotImplementedError

    def _heads_state(self) -> dict:
        return {k: v.detach().cpu().contiguous() for k, v in self.heads.state_dict().items()}

    def describe(self) -> dict:
        return {"family": self.family, "head_form": self.head_form, "action_head": self.with_action,
                "model_version": MODEL_VERSION}

    def save(self, path) -> dict:
        """Adapter (peft) + heads (safetensors) + manifest with sha256 of every file."""
        from safetensors.torch import save_file
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        self._peft().save_pretrained(str(path / "adapter"))
        save_file(self._heads_state(), str(path / "heads.safetensors"))
        files = sorted(str(p.relative_to(path)) for p in path.rglob("*") if p.is_file() and p.name != MANIFEST)
        record = {**self.describe(), "files": {f: sha256_file(path / f) for f in files}}
        (path / MANIFEST).write_text(json.dumps(record, indent=2, sort_keys=True))
        return record

    def load(self, path) -> dict:
        """Verify every recorded sha256, then load adapter and heads into this (identically built) wrapper."""
        from peft import get_peft_model_state_dict, set_peft_model_state_dict
        from safetensors.torch import load_file
        path = Path(path)
        record = json.loads((path / MANIFEST).read_text())
        for key in ("family", "head_form", "action_head"):
            if record.get(key) != self.describe()[key]:
                raise ValueError(f"{path}: {key} is {record.get(key)!r} there and {self.describe()[key]!r} here")
        for required in (ADAPTER_FILE, HEADS_FILE):   # what is loaded must be what is pinned
            if required not in record["files"]:
                raise IntegrityError(f"{path}: {required} is not recorded in the manifest")
        for f, digest in record["files"].items():
            if sha256_file(path / f) != digest:
                raise IntegrityError(f"{path / f}: sha256 does not match the manifest")
        adapter = load_file(str(path / ADAPTER_FILE))
        expected = {k for k in get_peft_model_state_dict(self._peft())}
        missing = sorted(expected - set(adapter))
        if missing:  # a partial adapter would otherwise load silently with LoRA at its initial values
            raise IntegrityError(f"{path}: adapter lacks {len(missing)} keys, e.g. {missing[:3]}")
        res = set_peft_model_state_dict(self._peft(), adapter)
        if getattr(res, "unexpected_keys", None):
            raise ValueError(f"unexpected adapter keys: {res.unexpected_keys[:5]}")
        self.heads.load_state_dict(load_file(str(path / HEADS_FILE)), strict=True)
        return record

    def _out(self, belief: torch.Tensor, action: torch.Tensor | None, **extra) -> dict:
        return {"belief_logits": belief, "action_logit": action if self.with_action else None, **extra}


# ---------------------------------------------------------------- Kev

class PointerWrapper(_Wrapper):
    """Kev: Qwen3.5 base + LoRA + pointer head (``kev.model``); see the module docstring for the record mapping."""

    family = "kev"

    def __init__(self, base: str, tokenizer=None, *, base_name: str | None = None, revision: str | None = None,
                 base_revision: str | None = None, init_from: str | None = None, head_form: str = "softmax12",
                 action_head: bool = True, dtype=torch.float32, device="cpu", max_state: int = 1024,
                 attn: str | None = None):
        """``revision``: Hub revision to download ``base`` at (moot for a local directory); ``base_revision``: the
        pinned base revision checked against a warm-start checkpoint's ``head.pt`` (defaults to ``revision``)."""
        super().__init__(head_form, action_head)
        from kev import model as km
        self.km_mod = km
        self.tok = tokenizer or km.load_tokenizer(base, revision=revision)
        self.kev = km.DecisionModel(base, self.tok, device, lora=LORA_R, revision=revision, dtype=dtype, attn=attn)
        self.provenance = None
        if init_from:
            from kev.checkpoint import Checkpoint, Meta
            ours = Meta(base=base_name or base, base_revision=base_revision or revision, lora=LORA_R, head_dim=256)
            self.provenance = Checkpoint(init_from).warm_start(self.kev, ours)
        self.ctx = km.training_context(max_state)
        self.packing = not self.kev.hybrid  # attention-only backbones run Kev's packed tree form (= spec §2.4 mask)
        self.heads["pointer"] = self.kev.head
        self._add_heads(self.kev.lm.config.hidden_size)
        self.to(device)

    def _peft(self):
        return self.kev.lm

    def describe(self) -> dict:
        return {**super().describe(), "kev_hybrid": self.kev.hybrid}

    def records(self, batch: Sequence[DecisionPrompt]) -> tuple[list[dict], list[tuple[int, int]]]:
        """Kev records and, per prompt, (record index, question index)."""
        recs, where, index = [], [], {}
        for p in batch:
            key = (p.group, p.state) if p.group else None
            if key is not None and key in index:
                r = index[key]
            else:
                recs.append({"state": p.state, "questions": []})
                r = len(recs) - 1
                if key is not None:
                    index[key] = r
            q = {"instr": f"{p.proposal}\n\n{p.question}", "options": list(p.options), "label": 0}
            recs[r]["questions"].append(q)
            where.append((r, len(recs[r]["questions"]) - 1))
        return recs, where

    def forward(self, batch: Sequence[DecisionPrompt]) -> dict:
        km = self.km_mod
        recs, where = self.records(batch)
        encs = [km.encode(self.tok, r, max_state=self.ctx["max_state"], max_branch=self.ctx["max_branch"],
                          strict=True) for r in recs]
        per = [[None] * len(r["questions"]) for r in recs]  # (option logits [12], decide hidden [d])
        if self.kev.rows_form(encs):
            rows, readouts = [], []
            for b, e in enumerate(encs):
                S, Sp, brs = km.rows_of(e)
                for k, r in enumerate(brs):
                    rows.append((S + r["ids"], Sp + r["pos"]))
                    readouts.append((b, k, len(S) + r["decide"], [len(S) + o for o in r["opts"]]))
            for h, (b, k, d, oi) in zip(self.kev._rows_hidden(rows), readouts):
                per[b][k] = (self.kev.head(h[d], h[torch.tensor(oi, device=h.device)]), h[d])
        else:
            hs = self.kev.hidden_batch(encs)
            for b, e in enumerate(encs):
                for k, (d, oi) in enumerate(zip(e["decide_idx"], e["opt_idx"])):
                    h = hs[b]
                    per[b][k] = (self.kev.head(h[d], h[torch.tensor(oi, device=h.device)]), h[d])
        native = torch.stack([per[r][k][0] for r, k in where])
        hd = torch.stack([per[r][k][1] for r, k in where])
        belief = belief_logits_from(self.head_form, native, self.heads["cumulative"] if "cumulative" in self.heads
                                    else None, hd)
        action = self.heads["action"](hd).squeeze(-1) if self.with_action else None
        return self._out(belief, action)


# ---------------------------------------------------------------- Laya

def _laya_core(config: dict, encoder_config, weights: str | None):
    """Laya's ``DecisionModel`` (encoder + typed-decision head). ``weights``: a checkpoint's model.safetensors (the
    shipped loader rule: strict load); without it a randomly initialised model (tests)."""
    from laya import common as lc
    from transformers import AutoModel
    if weights:
        from safetensors.torch import load_file
        if not (isinstance(encoder_config, (str, Path)) and Path(encoder_config).is_dir()):
            raise ValueError("loading Laya weights needs the checkpoint's encoder/ directory as encoder_config")
        core = lc.build_model(config, encoder_dir=str(encoder_config), pretrained=False)
        core.load_state_dict(load_file(weights), strict=True)
        return core
    enc = AutoModel.from_config(encoder_config, attn_implementation="sdpa")
    return lc.DecisionModel(enc, config.get("head_layers", 2), len(config.get("act_costs", {})) + 1)


class HeadWrapper(_Wrapper):
    """Spec §2.2 ``HeadWrapper``: the family's own 12-option readout (Laya, StartLux)."""


class LayaWrapper(HeadWrapper):
    """Laya typed-decisions checkpoint: one choice question with the 12 bin options (``HeadWrapper`` family)."""

    family = "laya"

    def __init__(self, config: dict, tokenizer, *, encoder_config=None, weights: str | None = None,
                 head_form: str = "softmax12", action_head: bool = True, device="cpu"):
        super().__init__(head_form, action_head)
        from laya import common as lc
        from peft import get_peft_model
        self.lc, self.cfg, self.tok = lc, dict(config), tokenizer
        if lc.uses_parallel_layout(self.cfg):
            raise NotImplementedError("Laya option_layout='parallel' is not wrapped (published checkpoints are sequential)")
        self.max_len = int(self.cfg.get("max_len", 1024))
        self.head_max_len = int(self.cfg.get("head_max_len", 256))
        core = _laya_core(self.cfg, encoder_config, weights)
        core.requires_grad_(False)
        core.encoder = get_peft_model(core.encoder, lora_config(MODERNBERT))
        for name in ("head", "type_emb", "scorer"):  # the decision head trains in full
            mod = getattr(core, name)
            if mod is not None:
                mod.requires_grad_(True)
                self.heads[f"laya_{name}"] = mod
        self.core = core
        self._add_heads(core.encoder.config.hidden_size)
        self.to(device)

    def _peft(self):
        return self.core.encoder

    def question(self, p: DecisionPrompt) -> dict:
        return {"t": "choice", "ins": p.question, "crit": {o: None for o in p.options}}

    def state_text(self, p: DecisionPrompt) -> str:
        # the proposal first: Laya cuts an over-long state at its end, which must never be the edit
        return f"Proposed edit:\n{p.proposal}\n\nLoop state:\n{p.state}"

    def encode(self, p: DecisionPrompt) -> dict:
        ids, markers, stats, trunc = self.lc.build_sequence(
            self.tok, self.state_text(p), self.question(p), self.max_len, self.head_max_len,
            return_stats=True, return_truncation_stats=True)
        if len(markers) != N_BINS or stats["options_distinct"] != N_BINS:
            raise ValueError(f"Laya head lost options: {len(markers)} markers, {stats['options_distinct']} distinct")
        return {"ids": ids, "markers": markers, "truncated": trunc["truncated"]}

    def forward(self, batch: Sequence[DecisionPrompt]) -> dict:
        encs = [self.encode(p) for p in batch]
        L = max(len(e["ids"]) for e in encs)
        dev = self.device
        pad = self.tok.pad_token_id
        ids = torch.full((len(encs), L), pad, dtype=torch.long, device=dev)
        att = torch.zeros((len(encs), L), dtype=torch.long, device=dev)
        for i, e in enumerate(encs):
            ids[i, :len(e["ids"])] = torch.tensor(e["ids"], device=dev)
            att[i, :len(e["ids"])] = 1
        marker_pos = torch.tensor([e["markers"] for e in encs], device=dev)
        marker_mask = torch.ones_like(marker_pos, dtype=torch.bool)
        qtype = torch.full((len(encs),), self.lc.QTYPES["choice"], device=dev)
        native, h_cls = self._core_forward(ids, att, marker_pos, marker_mask, qtype)
        belief = belief_logits_from(self.head_form, native, self.heads["cumulative"] if "cumulative" in self.heads
                                    else None, h_cls)
        action = self.heads["action"](h_cls.float()).squeeze(-1) if self.with_action else None
        return self._out(belief, action, truncated=[e["truncated"] for e in encs])

    def _core_forward(self, ids, att, marker_pos, marker_mask, qtype):
        """Laya's ``DecisionModel.forward`` up to the scorer, also returning the [CLS] state after the head layers."""
        core = self.core
        h = core.encoder(input_ids=ids, attention_mask=att).last_hidden_state
        h = h + core.type_emb(qtype)[:, None, :]
        if core.head is not None:
            padm = ~att.bool()
            for layer in core.head.layers:
                h = layer(h, src_key_padding_mask=padm)
        idx = marker_pos[:, :, None].expand(-1, -1, h.size(-1))
        logits = core.scorer(torch.gather(h, 1, idx)).squeeze(-1).float()
        return logits.masked_fill(~marker_mask, -1e4), h[:, 0].float()


# ---------------------------------------------------------------- StartLux

class StartLuxBidirectional:
    """Prompt-bidirectional attention of StartLux Instant models on the installed transformers (5.19).

    The released implementation (``startlux_decide.backends.bidirectional``) is written against transformers 5.8.x and
    refuses other versions. The trained behaviour it reproduces: full-attention layers attend over every token of the
    row (no causal term); Gated DeltaNet layers and their causal convolution are unchanged. transformers 5.19's
    ``Qwen3_5TextModel.forward`` accepts a per-layer-type mask mapping, so this port passes a non-causal key mask to
    the full-attention layers and the stock recurrent mask to the linear layers, without replacing any module.
    ``check`` runs the released module's three self-checks on the model itself: (1) the causal mapping reproduces the
    stock forward; (2) padding tokens change no other token's state; (3) a late token reaches the first position.
    Agreement with the 5.8 reference on real weights is a Phase 3 (P.0) item, not shown here.
    """

    def __init__(self, body):
        cfg = body.config
        types = list(cfg.layer_types[:cfg.num_hidden_layers])
        if "full_attention" not in types or set(types) - {"full_attention", "linear_attention"}:
            raise ValueError(f"not the Qwen3.5 hybrid decoder: layer types {sorted(set(types))}")
        if cfg._attn_implementation != "sdpa":
            raise ValueError(f"bidirectional prompt attention needs sdpa, not {cfg._attn_implementation!r}")
        self.body = body

    def masks(self, embeds: torch.Tensor, valid: torch.Tensor | None, causal: bool) -> dict:
        from transformers.masking_utils import create_causal_mask, create_recurrent_attention_mask
        kw = {"config": self.body.config, "inputs_embeds": embeds, "attention_mask": valid, "past_key_values": None,
              "position_ids": None}
        lin = create_recurrent_attention_mask(**kw)
        if causal:
            return {"full_attention": create_causal_mask(**kw), "linear_attention": lin}
        B, L = embeds.shape[:2]
        if valid is None:
            keys = torch.ones((B, L), dtype=torch.bool, device=embeds.device)
        else:
            keys = valid.bool()
            n = keys.sum(-1)
            if not bool((keys == (torch.arange(L, device=keys.device)[None] < n[:, None])).all()):
                raise ValueError("bidirectional rows must be right-padded")
        full = keys[:, None, None, :].expand(B, 1, L, L)
        return {"full_attention": full, "linear_attention": lin}

    def hidden(self, input_ids, valid=None, causal: bool = False) -> torch.Tensor:
        embeds = self.body.embed_tokens(input_ids)
        return self.body(inputs_embeds=embeds, attention_mask=self.masks(embeds, valid, causal),
                         use_cache=False).last_hidden_state

    @torch.no_grad()
    def check(self, tokens: int = 24) -> dict:
        body = self.body
        dev = body.embed_tokens.weight.device
        vocab = min(1000, body.config.vocab_size)
        g = torch.Generator().manual_seed(1234)
        ids = torch.randint(0, vocab, (2, tokens), generator=g).to(dev)
        am = torch.ones_like(ids)
        am[1, tokens * 2 // 3:] = 0
        tol = lambda a, b: float((a.float() - b.float()).abs().max()) <= 1e-3 * (1.0 + float(a.float().abs().max()))  # noqa: E731
        worst = 0.0
        for m in (None, am):
            ref = body(input_ids=ids, attention_mask=m, use_cache=False).last_hidden_state
            got = self.hidden(ids, m, causal=True)
            if not tol(ref, got):
                raise RuntimeError("bidirectional check (1) failed: the causal mapping does not reproduce the stock forward")
            worst = max(worst, float((ref - got).abs().max()))
        n = int(am[1].sum())
        both = self.hidden(ids, am)
        alt = ids.clone()
        alt[1, n:] = (alt[1, n:] + 7) % vocab
        both2 = self.hidden(alt, am)
        if not (tol(both[0], both2[0]) and tol(both[1, :n], both2[1, :n])):
            raise RuntimeError("bidirectional check (2) failed: padding reaches a token")
        late = ids.clone()
        late[0, -1] = (late[0, -1] + 1) % vocab
        reach = float((self.hidden(late, am)[0, 0] - both[0, 0]).abs().max())
        if not reach > 0:
            raise RuntimeError("bidirectional check (3) failed: a late token does not reach the first position")
        return {"impl": "trackp_startlux_bidirectional/v1", "causal_max_diff": worst, "late_token_reach": reach}


class StartLuxWrapper(HeadWrapper):
    """StartLux-Decision v1.1 Instant (``HeadWrapper`` family): option-letter readout with bidirectional prompt."""

    family = "startlux"

    def __init__(self, model, tokenizer, *, head_form: str = "softmax12", action_head: bool = True, device="cpu"):
        super().__init__(head_form, action_head)
        from peft import get_peft_model
        from startlux_decide import prompt as sp
        self.sp, self.tok = sp, tokenizer
        self.letter_ids = sp.check_tokenizer(tokenizer)[:N_BINS]
        inner = model.model
        body = getattr(inner, "language_model", inner)
        if not model.config.get_text_config().tie_word_embeddings:
            raise ValueError("StartLux readout assumes tied output embeddings")
        model.requires_grad_(False)
        self.bidir = StartLuxBidirectional(body)
        self.check_report = self.bidir.check()
        self.body = get_peft_model(body, lora_config(lora_targets(body.config, "startlux")))
        self.bidir.body = body          # peft injects LoRA in place; the same module tree runs
        self.model = model
        self._add_heads(body.config.hidden_size)
        self.to(device)

    def _peft(self):
        return self.body

    def describe(self) -> dict:
        return {**super().describe(), "prompt_attention": "bidirectional"}

    def prompt_text(self, p: DecisionPrompt) -> str:
        row = self.sp.from_systemone(f"{p.state}\n\nProposed edit:\n{p.proposal}",
                                     {"type": "choice", "instructions": p.question,
                                      "criteria": {o: None for o in p.options}})
        return self.sp.plain_prompt(self.tok, self.sp.messages(row))

    def forward(self, batch: Sequence[DecisionPrompt]) -> dict:
        rows = [self.tok.encode(self.prompt_text(p), add_special_tokens=False) for p in batch]
        L = max(len(r) for r in rows)
        dev = self.device
        ids = torch.full((len(rows), L), self.tok.pad_token_id or 0, dtype=torch.long, device=dev)
        valid = torch.zeros((len(rows), L), dtype=torch.long, device=dev)
        for i, r in enumerate(rows):
            ids[i, :len(r)] = torch.tensor(r, device=dev)
            valid[i, :len(r)] = 1
        h = self.bidir.hidden(ids, valid)
        last = h[torch.arange(len(rows), device=dev), valid.sum(-1) - 1].float()
        letters = self.body.get_input_embeddings()(torch.tensor(self.letter_ids, device=dev)).float()
        native = last @ letters.T
        belief = belief_logits_from(self.head_form, native, self.heads["cumulative"] if "cumulative" in self.heads
                                    else None, last)
        action = self.heads["action"](last).squeeze(-1) if self.with_action else None
        return self._out(belief, action)


# ---------------------------------------------------------------- Qwen control

def add_reserved_tokens(tokenizer) -> dict:
    """Add ``<b0>…<b11>``, ``<exec>``, ``<skip>`` as special tokens; returns their ids (each must be one token)."""
    names = list(BIN_TOKENS) + [EXEC_TOKEN, SKIP_TOKEN]
    tokenizer.add_tokens(names, special_tokens=True)
    ids = {n: tokenizer.convert_tokens_to_ids(n) for n in names}
    for n, i in ids.items():
        if tokenizer.encode(n, add_special_tokens=False) != [i]:
            raise ValueError(f"{n} is not a single token")
    return ids


class BinTokenWrapper(_Wrapper):
    """Qwen3.5 base + LoRA with reserved bin/action tokens read from the (tied) LM head."""

    family = "qwen_control"

    def __init__(self, model, tokenizer, *, head_form: str = "softmax12", action_head: bool = True,
                 list_bins: bool = True, bin_order: Sequence[int] | None = None, device="cpu"):
        super().__init__(head_form, action_head)
        from peft import get_peft_model
        self.tok = tokenizer
        self.token_ids = add_reserved_tokens(tokenizer)
        emb = model.get_input_embeddings()
        if max(self.token_ids.values()) >= emb.weight.shape[0]:
            model.resize_token_embeddings(len(tokenizer))
            emb = model.get_input_embeddings()
        if not model.config.get_text_config().tie_word_embeddings:
            raise ValueError("BinTokenWrapper assumes tied embeddings (the Qwen3.5 bases tie them)")
        self._init_token_rows(model, tokenizer)
        self.list_bins = list_bins
        self.bin_order = list(bin_order) if bin_order is not None else list(range(N_BINS))
        if sorted(self.bin_order) != list(range(N_BINS)):
            raise ValueError("bin_order must permute 0..11")
        cfg = lora_config(lora_targets(model.config.get_text_config(), "qwen_control"),
                          trainable_token_indices={"embed_tokens": sorted(self.token_ids.values())})
        model.requires_grad_(False)
        self.lm = get_peft_model(model, cfg)
        self.bin_ids = torch.tensor([self.token_ids[t] for t in BIN_TOKENS])
        self.act_ids = torch.tensor([self.token_ids[EXEC_TOKEN], self.token_ids[SKIP_TOKEN]])
        self._add_heads(model.config.get_text_config().hidden_size, linear_action=False)
        self.to(device)

    @torch.no_grad()
    def _init_token_rows(self, model, tok) -> None:
        """Deterministic init: each new row = mean embedding of its description's tokens."""
        from r1.c3.train.types import BIN_OPTIONS
        w = model.get_input_embeddings().weight
        texts = list(BIN_OPTIONS) + ["execute the proposal", "skip the proposal"]
        for name, text in zip(list(BIN_TOKENS) + [EXEC_TOKEN, SKIP_TOKEN], texts):
            ids = tok.encode(text, add_special_tokens=False)
            w[self.token_ids[name]] = w[ids].mean(0)

    def _peft(self):
        return self.lm

    def describe(self) -> dict:
        return {**super().describe(), "list_bins": self.list_bins, "bin_order": self.bin_order}

    def prefix(self, p: DecisionPrompt) -> str:
        lines = [p.state, "", "Proposed edit:", p.proposal, "", f"Question: {p.question}"]
        if self.list_bins:
            lines.append("Bins:")
            lines += [f"{BIN_TOKENS[k]} {p.options[k]}" for k in self.bin_order]
        return "\n".join(lines) + "\n"

    def segments(self, p: DecisionPrompt, analysis: str | None = None) -> tuple[list[int], int, int, tuple]:
        """Token ids, belief position, action position, analysis token span (start, end) or ()."""
        enc = lambda s: self.tok.encode(s, add_special_tokens=False)  # noqa: E731
        ids = enc(self.prefix(p))
        span = ()
        if analysis is not None:
            ids += enc("<analysis>")
            a = enc(analysis)[:ANALYSIS_MAX_TOKENS] + enc("</analysis>\n")
            span = (len(ids), len(ids) + len(a))
            ids += a
        ids += enc("Belief:")
        belief_pos = len(ids) - 1
        ids += enc("\nAction:")
        return ids, belief_pos, len(ids) - 1, span

    def _forward_ids(self, rows) -> tuple[torch.Tensor, torch.Tensor]:
        L = max(len(r) for r in rows)
        dev = self.device
        ids = torch.full((len(rows), L), self.tok.pad_token_id or 0, dtype=torch.long, device=dev)
        att = torch.zeros((len(rows), L), dtype=torch.long, device=dev)
        for i, r in enumerate(rows):
            ids[i, :len(r)] = torch.tensor(r, device=dev)
            att[i, :len(r)] = 1
        out = self.lm(input_ids=ids, attention_mask=att, output_hidden_states=True, logits_to_keep=1)
        return out.hidden_states[-1].float(), ids

    def _token_rows(self, ids: torch.Tensor) -> torch.Tensor:
        return self.lm.get_input_embeddings()(ids.to(self.device)).float()  # tied: = LM-head rows (trained values)

    def forward(self, batch: Sequence[DecisionPrompt], analyses: Sequence[str] | None = None) -> dict:
        segs = [self.segments(p, None if analyses is None else analyses[i]) for i, p in enumerate(batch)]
        h, ids = self._forward_ids([s[0] for s in segs])
        n = torch.arange(len(segs), device=h.device)
        hb = h[n, torch.tensor([s[1] for s in segs], device=h.device)]
        ha = h[n, torch.tensor([s[2] for s in segs], device=h.device)]
        native = hb @ self._token_rows(self.bin_ids).T
        belief = belief_logits_from(self.head_form, native, self.heads["cumulative"] if "cumulative" in self.heads
                                    else None, hb)
        action = None
        if self.with_action:
            a = ha @ self._token_rows(self.act_ids).T
            action = a[:, 0] - a[:, 1]
        extra = {}
        if analyses is not None:
            extra["analysis_logprob"] = self._span_logprob(h, ids, [s[3] for s in segs])
        return self._out(belief, action, **extra)

    def _span_logprob(self, h, ids, spans) -> torch.Tensor:
        """Sum of log p(token) over each analysis span (closing tag included), teacher-forced."""
        head = self.lm.get_output_embeddings()
        out = []
        for i, (a, b) in enumerate(spans):
            logits = head(h[i, a - 1:b - 1].to(head.weight.dtype)).float()
            out.append(torch.log_softmax(logits, -1).gather(-1, ids[i, a:b, None]).sum())
        return torch.stack(out)


class ReasonThenBinWrapper(BinTokenWrapper):
    """P.6 (spec §6.4): sampled ``<analysis>`` (≤ 256 tokens), then the bin-token belief and the action."""

    family = "qwen_reason"

    @torch.no_grad()
    def generate(self, batch: Sequence[DecisionPrompt], *, temperature: float = 1.0, top_p: float = 1.0,
                 seed: int = 0) -> list[str]:
        torch.manual_seed(seed)
        out, self.last_generated_tokens = [], []
        stop = self.tok.encode("</analysis>", add_special_tokens=False)
        for p in batch:
            ids = torch.tensor([self.tok.encode(self.prefix(p) + "<analysis>", add_special_tokens=False)],
                               device=self.device)
            gen = self.lm.generate(input_ids=ids, attention_mask=torch.ones_like(ids), do_sample=True,
                                   temperature=temperature, top_p=top_p, max_new_tokens=ANALYSIS_MAX_TOKENS,
                                   pad_token_id=self.tok.pad_token_id or 0)
            new = gen[0, ids.shape[1]:].tolist()
            for j in range(len(new) - len(stop) + 1):
                if new[j:j + len(stop)] == stop:
                    new = new[:j]
                    break
            self.last_generated_tokens.append(len(new))
            out.append(self.tok.decode(new, skip_special_tokens=False))
        return out

    def forward(self, batch: Sequence[DecisionPrompt], analyses: Sequence[str] | None = None) -> dict:
        if analyses is None:
            raise ValueError("ReasonThenBinWrapper.forward scores given analyses; sample them with generate()")
        return super().forward(batch, analyses)


# ---------------------------------------------------------------- factory

def build_model(family: str, base, tokenizer=None, **kw):
    """``family`` in FAMILIES. ``base``: a model path / Hub id (kev: the base path; laya: the checkpoint directory or
    an ``(rl_agent_config dict, encoder config)`` pair for tests; startlux / qwen_*: a path or an already built
    transformers model)."""
    if family == "kev":
        return PointerWrapper(base, tokenizer, **kw)
    if family == "laya":
        if isinstance(base, (str, Path)):
            base = Path(base)
            from transformers import AutoConfig, AutoTokenizer
            cfg = json.loads((base / "rl_agent_config.json").read_text())
            tok = tokenizer or AutoTokenizer.from_pretrained(str(base / "tokenizer"))
            # the shipped loader rule: encoder config read from the checkpoint's encoder/ directory, strict load
            return LayaWrapper(cfg, tok, encoder_config=str(base / "encoder"), weights=str(base / "model.safetensors"),
                               **kw)
        cfg, enc_cfg = base
        return LayaWrapper(cfg, tokenizer, encoder_config=enc_cfg, **kw)
    if family in ("startlux", "qwen_control", "qwen_reason"):
        if isinstance(base, (str, Path)):
            import transformers
            from transformers import AutoConfig, AutoTokenizer
            dtype = kw.pop("dtype", torch.float32)
            arch = AutoConfig.from_pretrained(str(base)).architectures[0]
            base = getattr(transformers, arch).from_pretrained(str(base), dtype=dtype, attn_implementation="sdpa")
            tokenizer = tokenizer or AutoTokenizer.from_pretrained(str(kw.pop("tokenizer_path", base.name_or_path)))
        cls = {"startlux": StartLuxWrapper, "qwen_control": BinTokenWrapper, "qwen_reason": ReasonThenBinWrapper}[family]
        return cls(base, tokenizer, **kw)
    raise ValueError(f"unknown family {family!r}; one of {FAMILIES}")


__all__ = ["BinTokenWrapper", "FAMILIES", "HEAD_FORMS", "HeadWrapper", "IntegrityError", "LayaWrapper", "PointerWrapper",
           "ReasonThenBinWrapper", "StartLuxBidirectional", "StartLuxWrapper", "build_model", "cumulative_probs",
           "sha256_file"]
