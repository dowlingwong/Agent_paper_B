"""A1 template-check amendment (2026-11-04): byte equality or single-tokenizer-BOS prefix
with equal token ids on the HF side AND the pinned build's own /tokenize endpoint."""
from types import SimpleNamespace
import pytest
from r1.exam.stage_a import a1_template_equal


class FakeTokenizer:
    def __init__(self, bos='<bos>', bos_id=2, prefix_ids=(2,), mapping=None):
        self.bos_token = bos
        self.bos_token_id = bos_id
        self._prefix_ids = list(prefix_ids)
        self._mapping = mapping or {}

    def __call__(self, text, add_special_tokens=False):
        if text in self._mapping:
            return SimpleNamespace(input_ids=list(self._mapping[text]))
        ids = [7 + (ord(ch) % 50) for ch in text]
        if text == self.bos_token:
            return SimpleNamespace(input_ids=list(self._prefix_ids))
        return SimpleNamespace(input_ids=ids)


def _tok(hf, served):
    return FakeTokenizer(mapping={hf: [2] + [7 + (ord(c) % 50) for c in served], served: [7 + (ord(c) % 50) for c in served]})


def test_byte_equal_short_circuits():
    ok, ev = a1_template_equal({}, 'x', 'x', lambda text: None, tokenizer=FakeTokenizer())
    assert ok is True and ev['method'] == 'byte' and ev['a1_version']


def test_single_bos_prefix_with_server_tokenize_passes():
    served = 'hello'
    expected = '<bos>' + served
    ok, ev = a1_template_equal({}, served, expected, lambda text: [2] + [7 + (ord(c) % 50) for c in served], tokenizer=_tok(expected, served))
    assert ok is True and ev['method'] == 'token'
    assert ev['byte_equal'] is False and ev['prefix_token'] == '<bos>' and ev['prefix_token_id'] == 2
    assert ev['tokens_equal'] is True and ev['server_tokenize'] is True


def test_server_tokenize_mismatch_fails():
    served = 'hello'; expected = '<bos>' + served
    ok, ev = a1_template_equal({}, served, expected, lambda text: [9, 9], tokenizer=_tok(expected, served))
    assert ok is False and ev['server_tokenize'] is False and ev['method'] is None


def test_non_bos_prefix_fails():
    served = 'hello'; expected = 'X' + served
    ok, ev = a1_template_equal({}, served, expected, lambda text: [2] + [7 + (ord(c) % 50) for c in served], tokenizer=FakeTokenizer())
    assert ok is False and ev['method'] is None


def test_prefix_but_extra_difference_fails():
    served = 'hello'; expected = '<bos>hellO'
    ok, ev = a1_template_equal({}, served, expected, lambda text: [2] + [7 + (ord(c) % 50) for c in served], tokenizer=_tok(expected, served))
    assert ok is False


def test_missing_bos_fails():
    served = 'hello'; expected = '<bos>' + served
    tokenizer = FakeTokenizer(bos='', bos_id=None)
    ok, ev = a1_template_equal({}, served, expected, lambda text: [2], tokenizer=tokenizer)
    assert ok is False


def test_fallback_tokenize_row_is_gated_on_an_actual_tokenize_attempt():
    """Pre-A1 errors (non-BOS prefix, extra difference, missing BOS) must not expect a
    /tokenize journal row; only an attempted token path does."""
    from r1.exam.stage_a import fallback_tokenize_row
    assert fallback_tokenize_row('served', {'server_tokenize': None}) is None
    assert fallback_tokenize_row('served', {'server_tokenize': False}) == ('/tokenize', {'content': 'served', 'add_special': True})
    assert fallback_tokenize_row('served', {'server_tokenize': True}) == ('/tokenize', {'content': 'served', 'add_special': True})
    # an early-failure A1 call leaves server_tokenize None
    ok, ev = a1_template_equal({}, 'hello', 'Xhello', lambda text: [2], tokenizer=FakeTokenizer())
    assert ok is False and ev['server_tokenize'] is None and fallback_tokenize_row('hello', ev) is None
