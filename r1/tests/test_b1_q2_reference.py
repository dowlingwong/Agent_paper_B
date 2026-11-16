"""Q2 statistics only: fixtures contain no production labels or inference."""
import ast
import json
from pathlib import Path

from r1.scripts import b1_q2_reference as q2

ROOT=Path(__file__).resolve().parents[2]


def test_reference_expression_matches_b1_dryrun_receipt():
    fixture=json.loads((ROOT/'r1/tests/fixtures/b1_q2/dryrun_novelty.json').read_text())
    assert fixture['label']=='DRYRUN'
    assert q2.novelty_counts(fixture['events'])==fixture['expected']
    # Guard against semantic drift in the actual B1 diagnostics path.
    text=(ROOT/'r1/exam/campaign.py').read_text()
    assert "novelty=[e['payload'] for e in events if e['event_type']=='edit_novelty']" in text
    assert "'duplicates':sum(bool(p.get('active_config_seen_before')) for p in novelty)" in text
    assert 'evaluated=len(novelty)' in text
    assert q2.novelty_counts([{'event_type':'edit_novelty','payload':{'active_config_seen_before':True}},
                              {'event_type':'unrelated','payload':{'active_config_seen_before':True}}]) == {'duplicates':1,'evaluated':1}


def test_quantile_and_prespecified_constants():
    assert q2.SEED==20261107 and q2.DRAWS==10000 and q2.PER_NODE==4
    assert q2.linear_quantile([0.,1.,2.], .25)==.5
    assert q2.linear_quantile([0.,1.,2.], .995)==1.99
