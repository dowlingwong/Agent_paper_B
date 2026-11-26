"""Input-token counts of a prompt under every pool family's own rendering (A3 budget; R1-A3-BUDGET, 26 Oct).
ENGINEERING_ONLY; AI-assisted (Claude).

A3 prepends irrelevant history at 0 / 25 % / 50 % / 100 % of the *remaining token budget*, using the smallest context
limit in the pool (1,024 tokens: Laya's encoder and Kev's state limit) for every model. The budget of a prompt is
``limit - max over pool families of its input length``; a level adds history lines while the longest rendering
stays within ``base + frac * budget``. So the same text fits every pool model at every level, and the levels mean the
same for every model.

Each counter renders the prompt exactly as its wrapper does (``model.py``), with the wrapper's own code but no
weights: Kev ``kev.model.encode`` of the one-question record (state + its branch row), Laya
``laya.common.build_sequence`` without truncation, StartLux ``StartLuxWrapper.prompt_text``, the Qwen control
``BinTokenWrapper.segments`` (reserved tokens added to a copy of its tokenizer).
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Callable

from r1.c3.train.types import DecisionPrompt

POOL_LIMIT = 1024
Counter = Callable[[DecisionPrompt], int]


def kev_counter(tok) -> Counter:
    from kev import model as km
    from r1.c3.train.model import PointerWrapper
    shell = PointerWrapper.__new__(PointerWrapper)

    def count(p: DecisionPrompt) -> int:
        recs, _ = shell.records([p])
        enc = km.encode(tok, recs[0], max_state=10 ** 9, max_branch=10 ** 9, strict=False)
        return len(enc["ids"])
    return count


def laya_counter(laya_dir: Path | str) -> Counter:
    from laya import common as lc
    from transformers import AutoTokenizer
    from r1.c3.train.model import LayaWrapper
    laya_dir = Path(laya_dir)
    cfg = json.loads((laya_dir / "rl_agent_config.json").read_text())
    shell = LayaWrapper.__new__(LayaWrapper)
    shell.lc, shell.cfg = lc, cfg
    shell.tok = AutoTokenizer.from_pretrained(str(laya_dir / "tokenizer"))
    shell.max_len, shell.head_max_len = 10 ** 9, int(cfg.get("head_max_len", 256))

    def count(p: DecisionPrompt) -> int:
        e = shell.encode(p)
        if e["truncated"]:
            raise RuntimeError("Laya counter truncated a prompt")
        return len(e["ids"])
    return count


def startlux_counter(tok) -> Counter:
    from startlux_decide import prompt as sp
    from r1.c3.train.model import StartLuxWrapper
    shell = StartLuxWrapper.__new__(StartLuxWrapper)
    shell.sp, shell.tok = sp, tok
    return lambda p: len(tok.encode(shell.prompt_text(p), add_special_tokens=False))


def qwen_control_counter(tok) -> Counter:
    from r1.c3.labels import N_BINS
    from r1.c3.train.model import BinTokenWrapper, add_reserved_tokens
    tok = copy.deepcopy(tok)
    shell = BinTokenWrapper.__new__(BinTokenWrapper)
    shell.tok, shell.list_bins, shell.bin_order = tok, True, list(range(N_BINS))
    shell.token_ids = add_reserved_tokens(tok)
    return lambda p: len(shell.segments(p)[0])


def pool_counters(cfg: dict) -> dict[str, Counter]:
    """One counter per family of the configured pool (tokenizers from the pinned local model directories)."""
    from transformers import AutoTokenizer
    bases = cfg["bases"]
    first = lambda fam: next(b for b in bases.values() if b["family"] == fam)  # noqa: E731
    out: dict[str, Counter] = {}
    fams = {b["family"] for b in bases.values()}
    if "kev" in fams:
        # Kev's wrapper uses km.load_tokenizer(base): the base tokenizer (Kev reuses existing special tokens)
        out["kev"] = kev_counter(AutoTokenizer.from_pretrained(first("kev")["local_path"]))
    if "laya" in fams:
        out["laya"] = laya_counter(first("laya")["local_path"])
    if "startlux" in fams:
        out["startlux"] = startlux_counter(AutoTokenizer.from_pretrained(first("startlux")["local_path"]))
    if "qwen_control" in fams:
        out["qwen_control"] = qwen_control_counter(AutoTokenizer.from_pretrained(first("qwen_control")["local_path"]))
    return out


def max_tokens(counters: dict[str, Counter], p: DecisionPrompt) -> int:
    return max(c(p) for c in counters.values())
