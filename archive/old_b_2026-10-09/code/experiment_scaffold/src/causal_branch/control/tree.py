"""Closed three-leaf fixtures; no sequential learner or external execution."""
from dataclasses import dataclass, asdict
import math

REGIMES = ('verify_now', 'verify_later', 'never')

@dataclass(frozen=True)
class Root:
    root_id: str
    template_family_id: str
    split: str
    budget: float
    cost_now: float
    cost_later: float
    reaches_after_continue: bool
    reaches_after_verify: bool
    terminated_after_continue: bool
    available_now: bool
    available_later: bool
    never: float
    now: float
    later: float
    immediate_gain: float = 0.0


def build_tree(root):
    """One fixed regime consumes at most one intervention; reachability is action-specific."""
    for x in (root.budget, root.cost_now, root.cost_later):
        if not math.isfinite(x) or x < 0:
            raise ValueError('invalid budget/cost')
    for x in (root.never, root.now, root.later, root.immediate_gain):
        if not math.isfinite(x): raise ValueError('nonfinite outcome')
    leaves=[]
    for regime in REGIMES:
        budget=root.budget
        first=regime=='verify_now' and root.available_now and budget>=root.cost_now
        if first: budget-=root.cost_now
        reached=root.reaches_after_verify if first else (root.reaches_after_continue and not root.terminated_after_continue)
        second=regime=='verify_later' and reached and root.available_later and budget>=root.cost_later
        if second: budget-=root.cost_later
        leaves.append(dict(root_id=root.root_id,template_family_id=root.template_family_id,split=root.split,
            regime=regime,action1='verify' if first else 'continue',reached2=reached,
            action2='verify' if second else 'continue',budget_after1=root.budget-(root.cost_now if first else 0),
            budget_final=budget,outcome=root.now if first else root.later if second else root.never))
    return dict(schema_version='b_tree_v1',banner='ENGINEERING_ONLY',root=asdict(root),leaves=leaves)


def validate_trees(trees):
    roots=set();families={}
    for tree in trees:
        if tree.get('schema_version')!='b_tree_v1' or tree.get('banner')!='ENGINEERING_ONLY':
            raise ValueError('unknown tree schema/banner')
        root=Root(**tree['root'])
        if root.root_id in roots: raise ValueError('duplicate original root')
        roots.add(root.root_id)
        if families.setdefault(root.template_family_id,root.split)!=root.split: raise ValueError('descendant family leakage')
        for leaf in tree['leaves']:
            if any(leaf[k]!=getattr(root,k) for k in ('root_id','template_family_id','split')):
                raise ValueError('descendant leakage or root mismatch')
        if tree['leaves']!=build_tree(root)['leaves']: raise ValueError('invalid reachability, budget, leaf or outcome')
    if not roots: raise ValueError('empty original-root population')


def summarize(trees, *, denominator=None):
    validate_trees(trees)
    n=len(trees)
    if denominator is not None and denominator!=n: raise ValueError('wrong original-root denominator')
    return dict(banner='ENGINEERING_ONLY',original_roots=n,
                means={r:sum(next(l['outcome'] for l in t['leaves'] if l['regime']==r) for t in trees)/n for r in REGIMES})


def fixtures():
    base=dict(template_family_id='family',split='engineering',budget=1.,cost_now=1.,cost_later=1.,
              reaches_after_continue=True,reaches_after_verify=False,terminated_after_continue=False,
              available_now=True,available_later=True,never=0.,now=1.,later=.5)
    changes={
        'early_use_optimal':{},'save_for_later':dict(now=.2,later=1.),
        'no_useful_later':dict(later=0.),
        'early_termination':dict(terminated_after_continue=True,later=1.),
        'unreachable_checkpoint2':dict(reaches_after_continue=False,later=1.),
        'exhausted_budget':dict(budget=0.,later=1.),
        'unavailable_later':dict(available_later=False,later=1.),
        'greedy_fails':dict(now=.2,later=1.,immediate_gain=.1),
    }
    return [build_tree(Root(root_id=name,**(base|delta))) for name,delta in changes.items()]
