"""Offline matching of job bytes to a supplied catalogue; NEVER grants authority.

A hash can bind a local comparison to bytes but does not verify who reviewed the
catalogue, whether its classifications are correct, whether the execution closure
is immutable, or whether any authorisation/site gate is met.  This module does
not connect to submission and cannot make a bundle ready for execution.  The
real-submission configuration defaults to off; EVIDENCE submission is refused.

The proposed catalogue schema is deliberately experimental and has not been
adopted by the author.  An independently established trust root, review evidence,
evidence authorisation and a verified immutable runtime are still required.
"""
import hashlib
import json
import re


class PreviewError(ValueError):
    pass


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PreviewError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _constant(value):
    raise PreviewError("non-finite JSON number: " + value)


def _load(raw):
    if not isinstance(raw, bytes):
        raise PreviewError("input must be bytes")
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
    except (UnicodeDecodeError, ValueError) as exc:
        raise PreviewError("invalid JSON: " + str(exc)) from exc


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def command_digest(argv):
    if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x and "\x00" not in x for x in argv):
        raise PreviewError("argv must be a nonempty string array")
    # JSON array preserves exact argument boundaries and UTF-8 bytes, avoiding
    # ambiguity from joining with spaces or executable names alone.
    return _sha(json.dumps(argv, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def preview_match(manifest_bytes, catalogue_bytes, expected_catalogue_sha256):
    """Compare bytes and phase/command classification with a supplied catalogue.

    The caller-supplied expected digest is not a trust root or a review verdict.
    A successful result is an offline comparison only, not authorisation or a
    claim that the compared bytes will be used at runtime.
    """
    if not isinstance(expected_catalogue_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_catalogue_sha256):
        raise PreviewError("expected catalogue SHA-256 is required")
    if _sha(catalogue_bytes) != expected_catalogue_sha256:
        raise PreviewError("catalogue bytes differ from supplied digest")
    catalogue = _load(catalogue_bytes)
    manifest = _load(manifest_bytes)
    if not isinstance(catalogue, dict) or catalogue.get("schema") != "hk2_catalogue_preview/v1":
        raise PreviewError("invalid catalogue schema")
    if not isinstance(manifest, dict) or manifest.get("schema") != "hk2_job/v1":
        raise PreviewError("invalid manifest schema")
    entries = catalogue.get("entries")
    if not isinstance(entries, list):
        raise PreviewError("catalogue entries must be a list")
    sha = _sha(manifest_bytes)
    matches = [entry for entry in entries if isinstance(entry, dict) and entry.get("manifest_sha256") == sha]
    if len(matches) != 1:
        raise PreviewError("manifest must have exactly one catalogue entry")
    entry = matches[0]
    phase = manifest.get("phase")
    kind = manifest.get("kind")
    production = manifest.get("production")
    if not isinstance(phase, str) or not phase or kind not in ("engineering", "evidence") or type(production) is not bool:
        raise PreviewError("invalid manifest classification")
    for key, value in (("phase", phase), ("kind", kind), ("production", production)):
        if entry.get(key) != value or type(entry.get(key)) is not type(value):
            raise PreviewError("catalogue classification mismatch: " + key)
    command_sha = command_digest(manifest.get("argv"))
    if entry.get("argv_sha256") != command_sha:
        raise PreviewError("command digest mismatch")
    task = entry.get("task")
    if task not in ("setup", "smoke", "census", "qualification", "pilot", "sweep", "audit", "closed_loop"):
        raise PreviewError("unknown task class")
    if task in ("sweep", "audit", "closed_loop") and kind != "evidence":
        raise PreviewError("evidence task declared engineering")
    # The design describes EVIDENCE as T1 sweep, its audits and closed loop.
    # Other uses of these labels remain unsupported until a reviewed schema
    # distinguishes them; the catalogue itself is untrusted in this preview.
    return {"status": "PREVIEW_ONLY", "manifest_sha256": sha, "catalogue_sha256": _sha(catalogue_bytes),
            "argv_sha256": command_sha, "phase": phase, "kind": kind, "task": task,
            "submission_authorized": False, "immutability_verified": False,
            "review_authority_verified": False}
