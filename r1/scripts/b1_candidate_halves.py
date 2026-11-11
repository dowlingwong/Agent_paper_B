"""B1 report, descriptive only: each candidate's audited increment in the first vs second half of its roots.

ENGINEERING_ONLY; AI-assisted (Claude). PLAN R1-EXAM-B1-ANCHOR-R4-H2 (11 Nov 2026): the B1 STOP diagnosis
(reports/B1_STOP_DIAGNOSIS_20261111.md) found the incumbent-relative audited increment falling from the first
to the second half of random_valid's roots on digits_mlp (H2). The frozen ranking rule x5_rule_v2 ranks on the
pooled audited mean proposal increment, an incumbent-relative quantity, so the B1 report shows this check for
every candidate and anchor. It is descriptive: it enters no ranking, no finalist choice and no STOP, and it
changes nothing in r1/exam or the rule.

Definition (as diagnosis D4): for each root of the primary (thinking-off) mode, its audited proposals in the
order the campaign audited them are split into a first half of ceil(n/2) and a second half; increments are
standardised by the node's sigma_joint (D21 noise floor, NOISE_FLOOR_COMMON_20261022.md Table 1); pooled means
over all roots of the candidate, and per node. "change" = second-half mean - first-half mean (sigma_joint units).

Input: a B1 work directory (read only) holding <candidate>/b1_manifest.json and the root manifests it lists
(<candidate>/b1/<mode>/<node>__s<seed>/campaign_manifest.json; host paths are relocated under --work).
Output (stdout): a Markdown table, then one JSON line. Exit 0; exit 2 on a missing or inconsistent input.

    python -m r1.scripts.b1_candidate_halves --work /home/dowling/exam-x/work/b1_<run id>
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

SIGMA_JOINT = {'digits_mlp': 0.0102, 'openml_credit_approval': 0.0279, 'openml_ionosphere': 0.0410}
ROLE_NOTE = 'descriptive only (R1-EXAM-B1-ANCHOR-R4-H2); not used by x5_rule_v2, finalists or any STOP'


def _mean(xs):
    return math.fsum(xs) / len(xs) if xs else None


def _load_json(path: Path):
    with open(path, 'rb') as fh:
        return json.loads(fh.read())


def _relocate(work: Path, candidate: str, stored: str) -> Path:
    marker = f'/{candidate}/b1/'
    if marker not in stored:
        raise ValueError(f'root manifest path outside {candidate}/b1: {stored}')
    return work / candidate / 'b1' / stored.split(marker, 1)[1]


def candidate_rows(work: Path) -> list[dict]:
    work = Path(work)
    manifests = sorted(work.glob('*/b1_manifest.json'))
    if not manifests:
        raise ValueError(f'no <candidate>/b1_manifest.json under {work}')
    rows = []
    for mpath in manifests:
        m = _load_json(mpath)
        cand, primary = m.get('candidate'), m.get('primary_mode')
        if cand != mpath.parent.name or m.get('phase') != 'b1' or not primary:
            raise ValueError(f'inconsistent manifest {mpath}')
        first: dict[str, list[float]] = {}
        second: dict[str, list[float]] = {}
        roots = 0
        for stored in m.get('root_manifests') or []:
            root = _load_json(_relocate(work, cand, stored))
            if root.get('mode') != primary:
                continue
            roots += 1
            props = root.get('audited_proposals')
            if not isinstance(props, list):
                raise ValueError(f'root without audited_proposals: {stored}')
            for p in props:
                node = p['instance_id'].rsplit('__s', 1)[0]
                if node not in SIGMA_JOINT or not isinstance(p.get('delta_audit'), (int, float)) \
                        or not math.isfinite(p['delta_audit']):
                    raise ValueError(f'unusable audited proposal in {stored}')
            h = (len(props) + 1) // 2
            for part, bucket in ((props[:h], first), (props[h:], second)):
                for p in part:
                    node = p['instance_id'].rsplit('__s', 1)[0]
                    bucket.setdefault(node, []).append(p['delta_audit'] / SIGMA_JOINT[node])
        if roots == 0:
            raise ValueError(f'{cand}: no {primary} root')
        f_all = [z for v in first.values() for z in v]
        s_all = [z for v in second.values() for z in v]
        fm, sm = _mean(f_all), _mean(s_all)
        per_node = {n: (None if not first.get(n) or not second.get(n) else _mean(second[n]) - _mean(first[n]))
                    for n in SIGMA_JOINT}
        rows.append({'candidate': cand, 'role': m.get('role'), 'mode': primary, 'roots': roots,
                     'n_first': len(f_all), 'n_second': len(s_all), 'first_half_mean_z': fm, 'second_half_mean_z': sm,
                     'change_z': None if fm is None or sm is None else sm - fm, 'change_z_by_node': per_node,
                     'role_of_this_check': ROLE_NOTE})
    return rows


def _fmt(x):
    return 'n/a' if x is None else f'{x:+.3f}'


def table(rows) -> str:
    nodes = list(SIGMA_JOINT)
    out = ['| candidate | role | roots | audited (first / second) | first-half mean z | second-half mean z | change z | '
           + ' | '.join(f'change z {n}' for n in nodes) + ' |',
           '|' + '---|' * (7 + len(nodes))]
    for r in rows:
        out.append(f"| {r['candidate']} | {r['role']} | {r['roots']} | {r['n_first']} / {r['n_second']} | "
                   f"{_fmt(r['first_half_mean_z'])} | {_fmt(r['second_half_mean_z'])} | {_fmt(r['change_z'])} | "
                   + ' | '.join(_fmt(r['change_z_by_node'][n]) for n in nodes) + ' |')
    return '\n'.join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--work', required=True)
    args = ap.parse_args(argv)
    try:
        rows = candidate_rows(Path(args.work))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f'refused: {exc}', file=sys.stderr)
        return 2
    print('### Descriptive: audited increment, first vs second half of each root (sigma_joint units)\n')
    print(f'*{ROLE_NOTE}.*\n')
    print(table(rows))
    print('\n' + json.dumps({'schema': 'b1_candidate_halves/v1', 'rows': rows}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
