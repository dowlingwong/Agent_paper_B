"""Tiny random-weight stand-ins of every Track P family, for CPU dry runs and tests. ENGINEERING_ONLY; AI-assisted (Claude).

Backbones are built from small configs (random weights); the tokenizers are the real ones of the pool at their
Phase 0 revisions, read from the local Hugging Face cache (tokenizer files only, never weights). Nothing built here
is a model of the pool: it exercises the code paths (``trackp.py --tiny``) and nothing else.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import torch

QWEN = ("Qwen/Qwen3.5-0.8B-Base", "dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68")
STARTLUX = ("startlux-models/StartLux-Decision-v1.1-0.8B-Instant", "6496ae641cc71b149ce9dad69bd97f2a44e7bf11")
LAYA = ("convaiinnovations/laya-typed-decisions", "e929ae5cf69bc34259cd2f95c9e91145b818b1f0")


def tokenizer(repo: str, rev: str, subfolder: str | None = None, local_only: bool = True):
    from huggingface_hub import hf_hub_download
    from transformers import AutoTokenizer
    if subfolder:  # a tokenizer folder without its own config.json: load it as a local directory
        path = hf_hub_download(repo, f"{subfolder}/tokenizer.json", revision=rev, local_files_only=local_only)
        hf_hub_download(repo, f"{subfolder}/tokenizer_config.json", revision=rev, local_files_only=local_only)
        return AutoTokenizer.from_pretrained(os.path.dirname(path))
    return AutoTokenizer.from_pretrained(repo, revision=rev, local_files_only=local_only)


def qwen35_config(hybrid: bool = True, vocab: int = 248320):
    from transformers import Qwen3_5TextConfig
    types = ["linear_attention", "full_attention", "linear_attention", "full_attention"] if hybrid \
        else ["full_attention"] * 3
    return Qwen3_5TextConfig(vocab_size=vocab, hidden_size=64, intermediate_size=128, num_hidden_layers=len(types),
                             num_attention_heads=4, num_key_value_heads=2, head_dim=16, linear_num_key_heads=2,
                             linear_num_value_heads=4, linear_key_head_dim=16, linear_value_head_dim=16,
                             layer_types=types, tie_word_embeddings=True)


def causal_lm(hybrid: bool = True, seed: int = 0):
    from transformers import AutoModelForCausalLM
    torch.manual_seed(seed)
    return AutoModelForCausalLM.from_config(qwen35_config(hybrid), attn_implementation="sdpa").float()


def laya_parts():
    from huggingface_hub import hf_hub_download
    from transformers import ModernBertConfig
    tok = tokenizer(*LAYA, subfolder="tokenizer")
    cfg = json.loads(open(hf_hub_download(LAYA[0], "rl_agent_config.json", revision=LAYA[1],
                                          local_files_only=True)).read())
    cfg["head_layers"] = 1
    enc = ModernBertConfig(vocab_size=len(tok), hidden_size=64, intermediate_size=128, num_hidden_layers=3,
                           num_attention_heads=4, global_attn_every_n_layers=3, local_attention=16,
                           max_position_embeddings=1024, pad_token_id=tok.pad_token_id,
                           cls_token_id=tok.cls_token_id, sep_token_id=tok.sep_token_id)
    return cfg, enc, tok


def build_tiny(family: str, work_dir: Path | str, *, head_form: str = "softmax12", seed: int = 0, hybrid: bool = True):
    """A tiny wrapper of ``family`` (same constructor path as the real bases where possible)."""
    from r1.c3.train import model as M
    work_dir = Path(work_dir)
    torch.manual_seed(seed)
    if family == "kev":
        d = work_dir / f"tiny_qwen35_{'hybrid' if hybrid else 'full'}"
        if not (d / "config.json").is_file():
            tok = tokenizer(*QWEN)
            causal_lm(hybrid, seed).save_pretrained(d)
            tok.save_pretrained(d)
        return M.build_model("kev", str(d), head_form=head_form)
    if family in ("qwen_control", "qwen_reason"):
        return M.build_model(family, causal_lm(hybrid, seed), tokenizer(*QWEN), head_form=head_form)
    if family == "startlux":
        return M.build_model("startlux", causal_lm(True, seed), tokenizer(*STARTLUX), head_form=head_form)
    if family == "laya":
        cfg, enc, tok = laya_parts()
        return M.build_model("laya", (cfg, enc), tok, head_form=head_form)
    raise ValueError(f"unknown family {family!r}")


class HashBagModel(torch.nn.Module):
    """CPU hash-bag text model with the DecisionModel contract (``family = "hashbag"``): words of the rendered
    state and proposal hashed into an EmbeddingBag, a linear 12-bin belief head. No tokenizer or download; for the
    offline SFT dry run (``trackp.py sft-dev --tiny --family hashbag``) and tests only."""

    family = "hashbag"
    packing = False

    def __init__(self, dim: int = 16, buckets: int = 4093, seed: int = 0):
        super().__init__()
        torch.manual_seed(seed)
        self.buckets = buckets
        self.emb = torch.nn.EmbeddingBag(buckets, dim)
        self.heads = torch.nn.ModuleDict({"belief": torch.nn.Linear(dim, 12)})
        self.tok = None

    @property
    def device(self):
        return self.emb.weight.device

    def _ids(self, p) -> torch.Tensor:
        import hashlib
        words = (p.state + " " + p.proposal).split() or ["<empty>"]
        return torch.tensor([int(hashlib.md5(w.encode()).hexdigest()[:8], 16) % self.buckets for w in words])

    def forward(self, batch):
        ids = [self._ids(p) for p in batch]
        offsets = torch.tensor([0] + [len(x) for x in ids[:-1]]).cumsum(0)
        h = self.emb(torch.cat(ids), offsets)
        return {"belief_logits": self.heads["belief"](h), "action_logit": None}

    def trainable_parameters(self):
        return self.parameters()

    def save(self, path):
        import hashlib
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        torch.save(self.state_dict(), path / "heads.pt")
        digest = hashlib.sha256((path / "heads.pt").read_bytes()).hexdigest()
        rec = {"family": self.family, "files": {"heads.pt": digest}}
        (path / "record.json").write_text(json.dumps(rec, sort_keys=True))
        return rec

    def load(self, path):
        import hashlib
        path = Path(path)
        rec = json.loads((path / "record.json").read_text())
        if hashlib.sha256((path / "heads.pt").read_bytes()).hexdigest() != rec["files"]["heads.pt"]:
            raise RuntimeError(f"STOP: {path}/heads.pt does not match its recorded sha256")
        self.load_state_dict(torch.load(path / "heads.pt", map_location="cpu"))
        return rec


def build_hashbag(seed: int = 0) -> HashBagModel:
    return HashBagModel(seed=seed)
