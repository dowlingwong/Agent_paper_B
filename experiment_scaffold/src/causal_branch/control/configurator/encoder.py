"""B-DAC2: history encoders for the configurator (mock on CPU; CLM stubbed until Ada).

Design reference: ``docs/paper_split/B_DAC_CONFIGURATOR_AMENDMENT_20261004.md`` §4.2.

An encoder maps serialised decision-time texts to fixed-width vectors.  It is
**frozen**: nothing in the B pipeline updates encoder weights.  Every
controller receives the same encoder output (design v2 §4, matched
information), so the encoder is part of the shared state representation, not
part of any one controller.

Encoders
--------
``MockEncoder``
    Deterministic signed feature hashing of word unigrams and bigrams, L2
    normalised.  CPU, numpy only.  It has no semantics beyond token overlap and
    exists to exercise the pipeline on scripted trees.  Never a result.

``CLMEncoder``  (variant ``clm_state_head`` or ``backbone_raw``)
    Qwen3-8B last-token pooled embedding from an OpenAI-compatible
    ``/v1/embeddings`` pooling server (CLM's reference serving recipe), then,
    for ``clm_state_head``, CLM's frozen state projection head (4096 -> 512).
    ``backbone_raw`` skips the head; it is the ablation that separates CLM's
    agentic post-training from the backbone.  **Stubbed**: it refuses to run
    unless a complete ``CLMBinding`` is supplied *and* ``allow_network=True``.
    The request and projection code below is UNEXERCISED until the Ada
    qualification step binds the artifacts (RUNBOOK §12.3 gate 2).

``KevEncoder``
    Frozen Kev (open Jev-style typed-decision model) answering a frozen set of
    typed questions about each history; the feature vector is the calibrated
    answer probabilities (low-dimensional, interpretable, runs offline on a Mac
    through MLX).  **Stubbed** until a ``KevBinding`` is complete; the response
    parsing is exercised on CPU through an injected fake transport.

Which slot is primary is an author decision recorded before any pilot outcome
(amendment §5).  The other is an ablation.

``EmbeddingCache`` keys every vector by (encoder fingerprint, text sha256), so a
changed model, head, variant or serialiser can never reuse a stale vector.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import base64
import hashlib
import json
from pathlib import Path
import re
from typing import Protocol

import numpy as np

ENCODER_SCHEMA = "b_dac_encoder_v1"


class EncoderError(RuntimeError):
    """An encoder request violates its binding or contract."""


class EncoderUnavailable(EncoderError):
    """The encoder is stubbed or its artifacts are not bound."""


class Encoder(Protocol):
    name: str
    dim: int

    def fingerprint(self) -> dict: ...
    def embed(self, texts: list[str]) -> np.ndarray: ...


def _l2(x: np.ndarray) -> np.ndarray:
    return x / (np.linalg.norm(x, axis=-1, keepdims=True) + 1e-12)


def fingerprint_digest(fp: dict) -> str:
    return hashlib.sha256(json.dumps(fp, sort_keys=True).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# Mock encoder (CPU)
# --------------------------------------------------------------------------

_TOKEN = re.compile(r"[a-z0-9_.]+")


@dataclass
class MockEncoder:
    """Signed feature hashing of unigrams + bigrams.  ENGINEERING ONLY."""

    dim: int = 64
    salt: str = "b-dac-mock-v1"
    name: str = "mock_hashing"

    def fingerprint(self) -> dict:
        return {"schema": ENCODER_SCHEMA, "kind": "mock", "name": self.name,
                "dim": self.dim, "salt": self.salt}

    def _vec(self, text: str) -> np.ndarray:
        toks = _TOKEN.findall(text.lower())
        grams = toks + [f"{a}__{b}" for a, b in zip(toks, toks[1:])]
        v = np.zeros(self.dim)
        for g in grams:
            h = hashlib.sha256(f"{self.salt}:{g}".encode()).digest()
            idx = int.from_bytes(h[:4], "little") % self.dim
            v[idx] += 1.0 if h[4] & 1 else -1.0
        return np.sign(v) * np.log1p(np.abs(v))

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim))
        return _l2(np.stack([self._vec(t) for t in texts]))


# --------------------------------------------------------------------------
# CLM encoder (stubbed until Ada)
# --------------------------------------------------------------------------

CLM_VARIANTS = ("clm_state_head", "backbone_raw")


@dataclass(frozen=True)
class CLMBinding:
    """Exact artifacts the CLM encoder may use.  Bound at Ada qualification.

    ``head_sha256`` is checked against the head file before use; the backbone
    revision is recorded and must match the pooling server's reported model.
    """

    backbone_model: str = "Qwen/Qwen3-8B"
    backbone_revision: str = ""          # HF commit hash, bound at qualification
    served_model_name: str = "qwen3-8b"
    url: str = ""                        # e.g. http://127.0.0.1:8090/v1/embeddings
    head_path: str = ""                  # CLM_v0.1-8B.pt (or a later frozen head)
    head_sha256: str = ""
    max_tokens: int = 2048
    pooling: str = "last"

    def missing(self, variant: str) -> list[str]:
        need = ["backbone_revision", "url"]
        if variant == "clm_state_head":
            need += ["head_path", "head_sha256"]
        return [k for k in need if not getattr(self, k)]


@dataclass
class CLMEncoder:
    """CLM (frozen Qwen3-8B + frozen state head).  STUB until Ada qualification."""

    binding: CLMBinding
    variant: str = "clm_state_head"
    allow_network: bool = False
    batch: int = 32
    timeout: float = 300.0
    name: str = "clm"

    def __post_init__(self) -> None:
        if self.variant not in CLM_VARIANTS:
            raise EncoderError(f"unknown CLM variant {self.variant!r}")
        self._head = None
        self.last_prompt_tokens: list[int] = []

    @property
    def dim(self) -> int:
        return 512 if self.variant == "clm_state_head" else 4096

    def fingerprint(self) -> dict:
        return {"schema": ENCODER_SCHEMA, "kind": "clm", "variant": self.variant,
                **{k: v for k, v in asdict(self.binding).items() if k != "url"}}

    def _guard(self) -> None:
        missing = self.binding.missing(self.variant)
        if missing:
            raise EncoderUnavailable(
                f"CLM encoder not bound (missing {missing}); it is stubbed until "
                "Ada qualification binds the backbone and head artifacts")
        if not self.allow_network:
            raise EncoderUnavailable(
                "CLM encoder requires allow_network=True on an authorised host; "
                "CPU tests use MockEncoder")

    # -- UNEXERCISED below this line until Ada --------------------------------
    def _fetch(self, texts: list[str]) -> np.ndarray:
        import urllib.request
        body = {"model": self.binding.served_model_name, "input": texts,
                "encoding_format": "base64",
                "truncate_prompt_tokens": self.binding.max_tokens}
        req = urllib.request.Request(self.binding.url, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            j = json.loads(resp.read())
        if j.get("model") not in (None, self.binding.served_model_name):
            raise EncoderError(f"server model {j.get('model')!r} != binding")
        out = [None] * len(texts)
        for d in j["data"]:
            e = d["embedding"]
            v = (np.frombuffer(base64.b64decode(e), dtype=np.float32) if isinstance(e, str)
                 else np.asarray(e, dtype=np.float32))
            out[d["index"]] = v
        tokens = int((j.get("usage") or {}).get("prompt_tokens", 0) or 0)
        self.last_prompt_tokens.append(tokens)
        return _l2(np.stack(out).astype(np.float64))

    def _load_head(self):
        if self._head is not None:
            return self._head
        digest = hashlib.sha256(Path(self.binding.head_path).read_bytes()).hexdigest()
        if digest != self.binding.head_sha256:
            raise EncoderError("CLM head sha256 does not match the binding")
        import torch  # only on the Ada host
        from clm.heads import make_head  # CLM package, pinned at qualification
        blob = torch.load(self.binding.head_path, map_location="cpu")
        cfg = blob["cfg"]
        head = make_head(cfg["width"], cfg.get("depth", 2), cfg.get("projection_dim", 512),
                         cfg.get("activation", "gelu"), cfg.get("layernorm", False),
                         cfg.get("residual", False))
        head.load_state_dict(blob["state_head"])
        head.eval()
        self._head = (torch, head)
        return self._head

    def embed(self, texts: list[str]) -> np.ndarray:
        self._guard()
        chunks = [self._fetch(texts[i:i + self.batch]) for i in range(0, len(texts), self.batch)]
        x = np.vstack(chunks) if chunks else np.zeros((0, 4096))
        if self.variant == "backbone_raw":
            return x
        torch, head = self._load_head()
        with torch.no_grad():
            z = head(torch.as_tensor(x, dtype=torch.float32)).numpy()
        return _l2(z.astype(np.float64))


# --------------------------------------------------------------------------
# Kev typed-question encoder (stubbed until bound)
# --------------------------------------------------------------------------

#: DRAFT question set.  The author freezes the final set (wording, levels,
#: order) before any pilot outcome exists; the frozen set's digest enters the
#: encoder fingerprint, so a changed question invalidates cached vectors.
KEV_QUESTIONS_DRAFT: dict = {
    "candidate_stale": {"type": "noul", "instructions":
        "Is the agent's current candidate likely to be made outdated by information that "
        "arrives later in the task?"},
    "shift_suspected": {"type": "noul", "instructions":
        "Does the history show signs that the data distribution has shifted or will shift?"},
    "candidate_quality": {"type": "score", "instructions":
        "How good is the agent's current candidate on the evidence so far?",
        "criteria": ["Poor", "Adequate", "Good"]},
    "verification_gain": {"type": "score", "instructions":
        "How much would an independent check of the current candidate likely improve it?",
        "criteria": ["None", "Some", "Large"]},
    "progress": {"type": "score", "instructions": "How far through the task is the agent?",
                 "criteria": ["Early", "Middle", "Late"]},
}


def kev_feature_names(questions: dict) -> list[str]:
    names = []
    for qid, q in questions.items():
        if q["type"] in ("noul", "score"):
            names.append(qid)
        elif q["type"] == "choice":
            names += [f"{qid}={k}" for k in list(q["criteria"])[:-1]]   # drop one (sums to 1)
        else:
            raise EncoderError(f"unknown question type {q['type']!r}")
    return names


def kev_features(answers: dict, questions: dict) -> list[float]:
    """Map a /v1/systemone response's answers onto a fixed feature vector.

    noul -> P(true); score -> expected level / (levels - 1) in [0, 1];
    choice -> probabilities of all options but the last.
    """

    out = []
    for qid, q in questions.items():
        a = answers.get(qid)
        if a is None or a.get("type", q["type"]) != q["type"]:
            raise EncoderError(f"answer for {qid!r} missing or of the wrong type")
        if q["type"] == "noul":
            out.append(float(a["noul"]))
        elif q["type"] == "score":
            out.append(float(a["score"]) / (len(q["criteria"]) - 1))
        else:
            probs = a["probabilities"]
            out += [float(probs[k]) for k in list(q["criteria"])[:-1]]
    if not all(np.isfinite(out)):
        raise EncoderError("non-finite Kev answer")
    return out


@dataclass(frozen=True)
class KevBinding:
    """Exact Kev artifacts.  ``revision`` is a Hub commit or the ``v1.0`` tag hash."""

    model_repo: str = "jaredpalmer/kev-4b"
    revision: str = ""
    temperature: float | None = None     # the checkpoint's shipped temperature, recorded
    url: str = ""                        # e.g. http://127.0.0.1:8009/v1/systemone
    backend: str = ""                    # "mlx" or "torch", recorded

    def missing(self) -> list[str]:
        return [k for k in ("revision", "url", "backend") if not getattr(self, k)]


@dataclass
class KevEncoder:
    """Frozen Kev answering a frozen typed-question set.  STUB until bound.

    ``transport`` (request dict -> response dict) defaults to an HTTP POST and
    can be replaced by a fake server in CPU tests; the response parsing is
    therefore exercised before any model is bound.
    """

    binding: KevBinding
    questions: dict = None  # type: ignore[assignment]
    allow_network: bool = False
    transport: object = None
    timeout: float = 120.0
    name: str = "kev"

    def __post_init__(self) -> None:
        if self.questions is None:
            self.questions = KEV_QUESTIONS_DRAFT
        self.feature_names = kev_feature_names(self.questions)

    @property
    def dim(self) -> int:
        return len(self.feature_names)

    def fingerprint(self) -> dict:
        q = hashlib.sha256(json.dumps(self.questions, sort_keys=True).encode()).hexdigest()
        return {"schema": ENCODER_SCHEMA, "kind": "kev", "questions_sha256": q,
                **{k: v for k, v in asdict(self.binding).items() if k != "url"}}

    def _post(self, body: dict) -> dict:
        if self.transport is not None:
            return self.transport(body)
        missing = self.binding.missing()
        if missing:
            raise EncoderUnavailable(
                f"Kev encoder not bound (missing {missing}); stubbed until the author "
                "binds the checkpoint revision and serving backend")
        if not self.allow_network:
            raise EncoderUnavailable("Kev encoder requires allow_network=True")
        import urllib.request   # UNEXERCISED until bound
        req = urllib.request.Request(self.binding.url, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read())

    def embed(self, texts: list[str]) -> np.ndarray:
        rows = []
        for t in texts:
            resp = self._post({"state": t, "model": self.binding.model_repo,
                               "questions": self.questions})
            rows.append(kev_features(resp["answers"], self.questions))
        return np.array(rows, dtype=float).reshape(len(texts), self.dim)


# --------------------------------------------------------------------------
# Cache
# --------------------------------------------------------------------------


class EmbeddingCache:
    """Vectors keyed by (encoder fingerprint digest, text sha256)."""

    def __init__(self) -> None:
        self._store: dict[str, np.ndarray] = {}

    @staticmethod
    def key(fp_digest: str, text: str) -> str:
        return f"{fp_digest}:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"

    def embed(self, encoder: Encoder, texts: list[str]) -> np.ndarray:
        fp = fingerprint_digest(encoder.fingerprint())
        keys = [self.key(fp, t) for t in texts]
        todo = [t for t, k in dict(zip(texts, keys)).items() if k not in self._store]
        if todo:
            for t, v in zip(todo, encoder.embed(todo)):
                self._store[self.key(fp, t)] = np.asarray(v, dtype=np.float64)
        return np.stack([self._store[k] for k in keys]) if keys else np.zeros((0, encoder.dim))

    def __len__(self) -> int:
        return len(self._store)

    def save(self, path: Path) -> None:
        np.savez_compressed(path, keys=np.array(list(self._store)),
                            vecs=np.stack(list(self._store.values())))

    @classmethod
    def load(cls, path: Path) -> "EmbeddingCache":
        data = np.load(path, allow_pickle=False)
        cache = cls()
        cache._store = {str(k): v for k, v in zip(data["keys"], data["vecs"])}
        return cache
