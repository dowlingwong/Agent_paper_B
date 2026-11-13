"""Per-root LLM completion usage of a B1 run, for the completion cap of R1-EXAM-B1-TRUNCATION-INVALID.

ENGINEERING_ONLY; AI-assisted (Claude). Read only. The input is a copy of a B1 work tree: ``batch_state.json``
at the top and ``<candidate>/b1/<mode>/<node>__s<seed>/`` root directories that hold ``root_events.jsonl``
(and ``root_trials.jsonl``, ``campaign_manifest.json`` and the observer's events), as delivered by
``proposals/B1_TRUNCATION_HOST_CHECK_HANDOFF_20261111.md``.

For every root it reports:
* whether the batch state lists it as completed, with the manifest's SHA-256 checked against that entry;
* the proposer calls: ``llm_call`` events without a ``purpose`` (first proposals and D25 revisions; the harness's
  ``purpose: self_forecast`` events are the observer's): count, truncated calls, the largest ``completion_tokens``
  and ``prompt_tokens``, the longest ``latency_ms``, and calls above 2,048 completion tokens (the configured
  thinking budget). Each ledger record's ``llm_call`` must equal the last proposer event of its trial (a record
  without one is a D25 skip), and every proposer event must belong to a ledger trial;
* failed proposer calls (``llm_call_failed``), with the usage parsed from the recorded error;
* the observer calls: the ``self_forecast`` events, checked against the charged ``exam_self_forecast`` events, with
  the largest ``completion_tokens`` and the longest server ``predicted_ms`` from the recorded response bodies.
Per candidate and mode it adds the proposer rate (completion tokens / latency) and two bounds at that rate: hours
for a root whose 80 LLM calls all end at the cap (per-root deadline 12 h), and the observer reply length that
reaches the observer's timeout (``OBSERVER_TIMEOUT_S``).

The cap check is: the largest proposer completion over the **completed** roots < ``--cap``.
Output: Markdown on stdout, then one JSON line. Exit 0 if the check passes, 1 if it fails, 2 on bad input.

    python -m r1.scripts.b1_completion_usage --roots <copy of the work tree> [--cap 16384]
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT_RE = re.compile(r'^(?P<cand>[a-z0-9_]+)/b1/(?P<mode>off|on)/(?P<node>[a-z_]+)__s(?P<seed>\d{4})$')
USAGE_RE = re.compile(r'completion_tokens=(\d+), prompt_tokens=(\d+), total_tokens=(\d+)')
THINKING_BUDGET = 2048
SOFTWARE = ('random_valid', 'scripted')
LLM_CALL_CAP = 80           # exam_b1_v2.json llm_call_cap
OBSERVER_TIMEOUT_S = 180.0  # r1/exam/observer.py OBSERVER_TIMEOUT_S (R1-EXAM-B1-OBSERVER-TIMEOUT; was 60 s)
ROOT_DEADLINE_H = 12.0      # exam_b1_v2.json root_timeout_seconds 43200
DEFAULT_CAP = 16384   # equals r1.exam.b1_llm_truncation.B1_MAX_COMPLETION_TOKENS (checked by the test)


def _rows(path: Path) -> list[dict]:
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()] if path.exists() else []


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _int(x):
    return x if type(x) is int else None


def root_usage(root: Path, rel: str, completed: dict) -> dict:
    m = ROOT_RE.match(rel)
    events = _rows(root / 'root_events.jsonl')
    records = _rows(root / 'root_trials.jsonl')
    llm = [e for e in events if e.get('event_type') == 'llm_call']
    # The harness also emits an ``llm_call`` event with ``purpose: self_forecast`` after each observer query;
    # proposer calls (first proposals and D25 revisions) carry no ``purpose``.
    proposer = [e for e in llm if 'purpose' not in (e.get('payload') or {})]
    observer_llm = [e for e in llm if (e.get('payload') or {}).get('purpose') == 'self_forecast']
    if len(proposer) + len(observer_llm) != len(llm):
        raise ValueError(f'{rel}: llm_call event with an unknown purpose')
    calls = [e.get('payload') or {} for e in proposer]
    comp = [_int(c.get('completion_tokens')) for c in calls]
    # Each ledger record's llm_call is the last proposer call of its trial (a D25 revision replaces the
    # proposal); a record without one is a D25 skip. Every proposer call belongs to a ledger trial.
    last: dict[str, dict] = {}
    for e in proposer:
        last[e.get('trial_id')] = e.get('payload') or {}
    trial_ids = set()
    for r in records:
        trial_ids.add(r.get('trial_id'))
        call = ((r.get('extra') or {}).get('manager') or {}).get('llm_call')
        if call and last.get(r.get('trial_id')) != call:
            raise ValueError(f'{rel}: ledger llm_call of {r.get("trial_id")} differs from its last proposer event')
    if set(last) - trial_ids:
        raise ValueError(f'{rel}: proposer events for trials not in the ledger: {sorted(set(last) - trial_ids)}')
    failed = []
    for e in events:
        if e.get('event_type') == 'llm_call_failed':
            p = e.get('payload') or {}
            u = USAGE_RE.search(p.get('error') or '')
            failed.append({'trial_id': e.get('trial_id'), 'error_type': p.get('error_type'),
                           'completion_tokens': int(u.group(1)) if u else None,
                           'prompt_tokens': int(u.group(2)) if u else None})
    forecasts = [e.get('payload') or {} for e in events if e.get('event_type') == 'exam_self_forecast']
    charged = [f for f in forecasts if f.get('status') != 'llm_cap_exhausted']
    if len(charged) != len(observer_llm):
        raise ValueError(f'{rel}: observer forecasts and self_forecast llm_call events disagree')
    obs_comp, obs_ms = [], []
    for f in charged:
        body = (f.get('request_evidence') or {}).get('response_body_b64')
        if not body:
            continue
        reply = json.loads(base64.b64decode(body))
        obs_comp.append(_int((reply.get('usage') or {}).get('completion_tokens')))
        ms = (reply.get('timings') or {}).get('predicted_ms')
        obs_ms.append(float(ms) if isinstance(ms, (int, float)) and not isinstance(ms, bool) else None)
    entry = completed.get(rel)
    manifest = root / 'campaign_manifest.json'
    manifest_ok = None
    if entry is not None:
        manifest_ok = manifest.exists() and _sha(manifest) == entry.get('sha256')
    known = [c for c in comp if c is not None]
    lat = [c.get('latency_ms') for c in calls]
    timed = [(c, l) for c, l in zip(comp, lat) if c is not None and isinstance(l, (int, float)) and l > 0]
    return {'root': rel, 'candidate': m['cand'], 'mode': m['mode'], 'node': m['node'], 'seed': int(m['seed']),
            'completed': entry is not None, 'manifest_sha256_matches_batch_state': manifest_ok,
            'software_anchor': m['cand'] in SOFTWARE, 'trials': len(records),
            'llm_calls': len(calls),
            # a context-overflow call (R1-EXAM-B1-MODEL-OUTPUT-INVALID) has no reply and so no completion count
            'llm_calls_without_usage': sum(c is None and not call.get('context_overflow') for c, call in zip(comp, calls)),
            'truncated': sum(bool(c.get('truncated')) for c in calls),
            'context_overflow': sum(bool(c.get('context_overflow')) for c in calls),
            'unencodable_reply': sum(bool(c.get('unencodable_reply')) for c in calls),
            'max_completion_tokens': max(known) if known else None,
            'sum_completion_tokens': sum(c for c, _ in timed), 'sum_latency_s': sum(l for _, l in timed) / 1000.0,
            'max_prompt_tokens': max([x for x in (_int(c.get('prompt_tokens')) for c in calls) if x is not None], default=None),
            'max_latency_s': (max([l for l in lat if isinstance(l, (int, float))], default=0) / 1000.0) if calls else None,
            'calls_over_thinking_budget': sum(1 for c in known if c > THINKING_BUDGET),
            'failed_calls': failed,
            'observer_calls': len(observer_llm), 'observer_bodies': len(obs_comp),
            'observer_max_completion_tokens': max([x for x in obs_comp if x is not None], default=None),
            'observer_max_predicted_s': (max([x for x in obs_ms if x is not None], default=0) / 1000.0) if obs_comp else None}


def candidate_modes(rows: list[dict], cap: int) -> list[dict]:
    """Per candidate and mode: proposer throughput, and the two time bounds that depend on it."""
    out = []
    for key in sorted({(r['candidate'], r['mode']) for r in rows if not r['software_anchor']}):
        rs = [r for r in rows if (r['candidate'], r['mode']) == key]
        tok, sec = sum(r['sum_completion_tokens'] for r in rs), sum(r['sum_latency_s'] for r in rs)
        rate = tok / sec if sec > 0 else None
        obs = [r['observer_max_predicted_s'] for r in rs if r['observer_max_predicted_s'] is not None]
        out.append({'candidate': key[0], 'mode': key[1], 'roots': len(rs), 'completed_roots': sum(r['completed'] for r in rs),
                    'llm_calls': sum(r['llm_calls'] for r in rs), 'truncated': sum(r['truncated'] for r in rs),
                    'max_completion_tokens': max([r['max_completion_tokens'] for r in rs if r['max_completion_tokens'] is not None], default=None),
                    'tokens_per_s': rate,
                    # every one of the LLM-call cap's 80 calls truncated at the cap (the per-root deadline is 12 h)
                    'all_capped_root_hours_at_80_calls': (LLM_CALL_CAP * cap / rate / 3600.0) if rate else None,
                    # observer replies that would reach its timeout (OBSERVER_TIMEOUT_S) at this rate
                    'observer_timeout_tokens': (OBSERVER_TIMEOUT_S * rate) if rate else None,
                    'observer_max_predicted_s': max(obs) if obs else None})
    return out


def completed_roots(state: dict) -> dict:
    out = {}
    for key, entry in (state.get('completed') or {}).items():
        path = str((entry or {}).get('path') or '')
        hit = re.search(r'/([a-z0-9_]+/b1/(?:off|on)/[a-z_]+__s\d{4})/campaign_manifest\.json$', path)
        if not hit:
            raise ValueError(f'completed entry {key} has an unexpected path {path}')
        out[hit.group(1)] = entry
    return out


def analyse(roots: Path, cap: int) -> dict:
    roots = Path(roots)
    state_path = roots / 'batch_state.json'
    if not state_path.is_file():
        raise ValueError(f'no batch_state.json in {roots}')
    state = json.loads(state_path.read_text())
    completed = completed_roots(state)
    dirs = sorted(p.parent for p in roots.glob('*/b1/*/*/root_events.jsonl'))
    rows = []
    for d in dirs:
        rel = d.relative_to(roots).as_posix()
        if not ROOT_RE.match(rel):
            raise ValueError(f'unexpected root directory {rel}')
        rows.append(root_usage(d, rel, completed))
    missing = sorted(set(completed) - {r['root'] for r in rows})
    if missing:
        raise ValueError(f'completed roots without events in the copy: {missing}')
    done = [r for r in rows if r['completed']]
    llm_done = [r for r in done if not r['software_anchor']]
    if any(r['llm_calls'] == 0 or r['llm_calls_without_usage'] for r in llm_done):
        raise ValueError('a completed LLM root has no proposer calls or a call without completion_tokens')
    if any(r['manifest_sha256_matches_batch_state'] is not True for r in done):
        raise ValueError('a completed root manifest differs from its batch-state SHA-256')
    peak = max(r['max_completion_tokens'] for r in llm_done) if llm_done else None
    return {'batch_state_sha256': _sha(state_path), 'cap': cap, 'roots': rows,
            'candidate_modes': candidate_modes(rows, cap),
            'completed_roots': len(done), 'completed_llm_roots': len(llm_done),
            'max_completion_tokens_completed': peak,
            'cap_check': 'PASS' if peak is not None and peak < cap else 'FAIL',
            'margin_tokens': (cap - peak) if peak is not None else None}


def _f(x):
    if x is None:
        return '–'
    return f'{x:.1f}' if isinstance(x, float) else str(x)


def markdown(res: dict) -> str:
    lines = [f"batch_state.json SHA-256 `{res['batch_state_sha256']}`; completed roots {res['completed_roots']} "
             f"(LLM {res['completed_llm_roots']}); cap {res['cap']}; largest proposer completion over completed roots "
             f"**{res['max_completion_tokens_completed']}** → cap check **{res['cap_check']}** (margin {res['margin_tokens']}).", '',
             '| root | completed | trials | proposer calls | truncated | max completion | max prompt | max latency s | calls > 2,048 | failed calls | observer calls | observer max completion | observer max predicted s |',
             '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for r in res['roots']:
        failed = '; '.join(f"{f['error_type']} ({f['completion_tokens']} tok)" for f in r['failed_calls']) or '–'
        if r['software_anchor']:
            lines.append(f"| `{r['root']}` | {'yes' if r['completed'] else 'no'} | {r['trials']} | software anchor, none | – | – | – | – | – | – | – | – | – |")
            continue
        lines.append(f"| `{r['root']}` | {'yes' if r['completed'] else 'no'} | {r['trials']} | {r['llm_calls']} | {r['truncated']} | "
                     f"{_f(r['max_completion_tokens'])} | {_f(r['max_prompt_tokens'])} | {_f(r['max_latency_s'])} | "
                     f"{r['calls_over_thinking_budget']} | {failed} | {r['observer_calls']} | "
                     f"{_f(r['observer_max_completion_tokens'])} | {_f(r['observer_max_predicted_s'])} |")
    lines += ['', f'Per candidate and mode (all roots in the copy; time bounds at the measured proposer rate; per-root deadline {ROOT_DEADLINE_H:.0f} h, observer timeout {OBSERVER_TIMEOUT_S:.0f} s):', '',
              f'| candidate / mode | roots (completed) | proposer calls | truncated | max completion | tokens/s | h if all 80 calls hit the cap | observer reply tokens at {OBSERVER_TIMEOUT_S:.0f} s | observer max predicted s |',
              '|---|---|---|---|---|---|---|---|---|']
    for c in res['candidate_modes']:
        lines.append(f"| `{c['candidate']}` / {c['mode']} | {c['roots']} ({c['completed_roots']}) | {c['llm_calls']} | {c['truncated']} | "
                     f"{_f(c['max_completion_tokens'])} | {_f(c['tokens_per_s'])} | {_f(c['all_capped_root_hours_at_80_calls'])} | "
                     f"{_f(c['observer_timeout_tokens'])} | {_f(c['observer_max_predicted_s'])} |")
    return '\n'.join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--roots', required=True, type=Path)
    ap.add_argument('--cap', type=int, default=DEFAULT_CAP)
    a = ap.parse_args(argv)
    cap = a.cap
    try:
        res = analyse(a.roots, cap)
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print(f'b1_completion_usage: {exc}', file=sys.stderr)
        return 2
    print(markdown(res))
    print(json.dumps(res, sort_keys=True))
    return 0 if res['cap_check'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
