"""Tree packing (RUNBOOK Track P.1.5; spec §2.4). ENGINEERING_ONLY; AI-assisted (Claude).

One sequence holds one state and its Q proposal branches, ``[state | branch_1 | ... | branch_Q]``:

* mask M_ij = 1[j <= i] * 1[g_j = 0 or g_j = g_i] (g = 0 on state tokens, q on branch q): a branch sees the state and
  itself, never a sibling;
* position ids by tree depth: every branch restarts at position S (the state length), so a packed branch is
  position-for-position the sequence ``[state | branch]`` alone;
* readout at each branch's last token.

Packing is an efficiency option, never a selection criterion. It is off for backbones that cannot take an arbitrary
4D mask: Gated DeltaNet (linear-attention) layers ignore it (Qwen3.5 hybrids: Kev, the control, StartLux), and any
other backbone that fails ``self_check`` (packed = unpacked on a random example). Kev's own packed form
(``kev.model.branch_mask`` with branch positions restarting after the state) is the same construction;
``PointerWrapper`` uses it on attention-only bases.
"""
from __future__ import annotations

from dataclasses import dataclass

import torch

PACKING_VERSION = "tree_pack/v1"
TOL_FP32 = 1e-5


@dataclass
class TreeLayout:
    ids: list[int]
    seg: list[int]        # 0 = state, q = branch q (1-based)
    pos: list[int]        # tree-depth position ids
    last: list[int]       # index of each branch's last token


def tree_layout(state_ids: list[int], branches: list[list[int]]) -> TreeLayout:
    if not branches or any(len(b) == 0 for b in branches):
        raise ValueError("every branch needs at least one token")
    S = len(state_ids)
    ids, seg, pos, last = list(state_ids), [0] * S, list(range(S)), []
    for q, br in enumerate(branches, start=1):
        ids += br
        seg += [q] * len(br)
        pos += list(range(S, S + len(br)))
        last.append(len(ids) - 1)
    return TreeLayout(ids, seg, pos, last)


def tree_mask(segs: list[list[int]], dtype=torch.float32, device="cpu") -> torch.Tensor:
    """Additive [B, 1, L, L] mask for right-padded layouts. Pad keys are masked for every query; pad query rows keep
    their diagonal so no row is fully masked (finfo.min, not -inf)."""
    L = max(len(s) for s in segs)
    g = torch.full((len(segs), L), -1, device=device)
    for b, s in enumerate(segs):
        g[b, :len(s)] = torch.tensor(s, device=device)
    causal = torch.tril(torch.ones(L, L, dtype=torch.bool, device=device))
    same = (g[:, None, :] == g[:, :, None]) | (g[:, None, :] == 0)
    allow = causal[None] & same & (g != -1)[:, None, :]
    allow = allow | torch.eye(L, dtype=torch.bool, device=device)[None]
    return torch.zeros(len(segs), L, L, dtype=dtype, device=device).masked_fill(~allow, torch.finfo(dtype).min)[:, None]


def text_config(config):
    """The language-model config (composite multimodal configs keep layer_types / vocab_size in ``text_config``)."""
    get = getattr(config, "get_text_config", None)
    return get() if callable(get) else config


def has_linear_attention(config) -> bool:
    return "linear_attention" in set(getattr(text_config(config), "layer_types", None) or [])


def packed_hidden(backbone, layouts: list[TreeLayout], pad_id: int = 0) -> list[torch.Tensor]:
    """Hidden states at each branch's last token, one [Q, d] tensor per layout."""
    dev = next(backbone.parameters()).device
    dtype = next(backbone.parameters()).dtype
    L = max(len(t.ids) for t in layouts)
    ids = torch.full((len(layouts), L), pad_id, dtype=torch.long, device=dev)
    pos = torch.zeros((len(layouts), L), dtype=torch.long, device=dev)
    for b, t in enumerate(layouts):
        ids[b, :len(t.ids)] = torch.tensor(t.ids, device=dev)
        pos[b, :len(t.pos)] = torch.tensor(t.pos, device=dev)
    mask = tree_mask([t.seg for t in layouts], dtype=dtype, device=dev)
    h = backbone(input_ids=ids, position_ids=pos, attention_mask=mask).last_hidden_state
    return [h[b, t.last] for b, t in enumerate(layouts)]


def unpacked_hidden(backbone, state_ids: list[int], branches: list[list[int]]) -> torch.Tensor:
    """Reference: each branch run alone as ``[state | branch]`` (causal), hidden at its last token. [Q, d]."""
    dev = next(backbone.parameters()).device
    out = []
    for br in branches:
        ids = torch.tensor([list(state_ids) + list(br)], device=dev)
        out.append(backbone(input_ids=ids).last_hidden_state[0, -1])
    return torch.stack(out)


@torch.no_grad()
def self_check(backbone, vocab: int | None = None, seed: int = 0) -> dict:
    """Packed = unpacked (max |diff| <= 1e-5 in fp32) on a random state with three branches of unequal length.
    Never raises: returns {"ok": bool, "reason": str, "max_diff": float | None}."""
    cfg = backbone.config
    if has_linear_attention(cfg):
        return {"ok": False, "reason": "linear-attention (Gated DeltaNet) layers cannot take a tree mask",
                "max_diff": None}
    vocab = vocab or min(1000, text_config(cfg).vocab_size)
    g = torch.Generator().manual_seed(seed)
    rnd = lambda n: torch.randint(0, vocab, (n,), generator=g).tolist()  # noqa: E731
    state, branches = rnd(9), [rnd(5), rnd(3), rnd(7)]
    was = backbone.training
    backbone.eval()
    try:
        packed = packed_hidden(backbone, [tree_layout(state, branches)])[0].float()
        ref = unpacked_hidden(backbone, state, branches).float()
    except Exception as exc:  # a backbone that rejects a 4D mask or explicit position ids
        return {"ok": False, "reason": f"{type(exc).__name__}: {exc}", "max_diff": None}
    finally:
        backbone.train(was)
    diff = float((packed - ref).abs().max())
    tol = TOL_FP32 if next(backbone.parameters()).dtype == torch.float32 else 1e-2
    return {"ok": diff <= tol, "reason": "" if diff <= tol else f"packed != unpacked (max diff {diff:.2e})",
            "max_diff": diff}


def supports_packing(backbone) -> tuple[bool, str]:
    r = self_check(backbone)
    return r["ok"], r["reason"]


__all__ = ["PACKING_VERSION", "TreeLayout", "packed_hidden", "self_check", "supports_packing", "tree_layout",
           "tree_mask", "unpacked_hidden"]
