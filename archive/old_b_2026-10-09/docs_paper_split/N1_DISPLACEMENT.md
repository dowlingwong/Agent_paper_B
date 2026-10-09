# N1: the allocation-displacement constant m

Status: **derivation; the bound m ≤ 3 was reproduced by the 2026-09-27
independent AI-assisted review (finding N5), and step 3 was reworded after its
finding N4.** This is not a human proof review. N1 lives in
evaluation only. Controllers never read `p`. The population tax applied to a
fixed conclusion is `2·m·p_path`, where `m` is the maximum number of roots whose
realized regime can change when one root's recorded information changes.

## 1. The event

`D_path(i)` is the event that an outcome-relevant discrepancy occurs anywhere in
root `i`'s recorded `H1`, `H2`, or the leaf outcomes used by *any* compared
controller. `p_path` bounds `P(D_path)`. Checkpoint-wise bounds combine by the
union bound `min(1, p1 + p2)` only when each is valid
(`replay_validity.path_allowance`).

## 2. Why a per-root argument is not enough

The controllers share one batch allocator (`control/allocator.py`). A wrong score
at root `j` can change root `i`'s allocation because both compete for the same
hard budget `B = floor(.25·N)`. The per-root `2p` argument of the companion paper
does not cover this interference; the tax is `2·m·p_path` with `m ≥ 1`.

## 3. Derivation of m ≤ 3

Write the allocator's realized selection as two thresholded top-`k` rules:

- Phase 1 selects `k1 = min(#eligible, B − R)` feasible roots ranked by `s1`,
  restricted to `s1 > c1`.
- Phase 2 selects `k2 = B − k1` reached, unverified, feasible roots ranked by
  `s2`, restricted to `s2 > c2`.

Perturb the recorded information of a single root `j` (its `s1`, `s2`, or
`reached2`). Compare the two allocations.

1. **Root `j` itself.** Its own regime may change (now / later / never). Count 1.
2. **Phase 1.** The phase-1 selected set is the top-`k1` of a total order. Changing
   one element's rank changes membership of at most **one** other element: the
   element that crosses the cutoff (the boundary element when `j` enters or
   leaves). If `j` leaves phase 1, at most one root enters in its place; if `j`
   enters, at most one is displaced. Count ≤ 1. The threshold `s1 > c1` can only
   remove elements, never add a second crossing.
3. **Phase 2.** Phase-2 capacity is `B − k1`. By step 2, the phase-1 selected
   set changes by at most one entry and one exit, so `k1` changes by at most
   one, and therefore so does the phase-2 capacity. (When `j` swaps places with
   the boundary root inside phase 1, `k1` does not change at all.) A change of
   one in capacity, together with `j`'s own `s2` change, alters phase-2 membership of at most **one**
   additional root: the element crossing the phase-2 cutoff. A root displaced
   from phase 1 is newly eligible for phase 2, but it can displace at most the
   same single boundary element. Count ≤ 1.

No other root's rank or eligibility changes. Summing, `m ≤ 1 + 1 + 1 = 3`:
the perturbed root, at most one phase-1 displaced root, and at most one phase-2
displaced root. The bound is **tight**: the planted perturbations in
`evaluate_tree.displacement_check` attain 3.

## 4. Empirical check

`displacement_check(n_batches, n_roots, seed)` runs random batches, perturbs one
root at a time, and measures the maximum number of changed roots. Over 300
batches × 24 roots and three seeds the maximum is **3**, consistent with the
bound. A finding greater than 3 would falsify the derivation.

## 5. Use

The evaluation harness uses one explicit mapping (review findings N2/N3):

- each value `p` in the grid {0, .005, .01, .02, .05, .10} is a per-checkpoint
  allowance, `p1 = p2 = p`, declared as a sensitivity assumption;
- `p_path = min(1, p1 + p2)` (`replay_validity.path_allowance`);
- the population tax is `2·m·p_path = 6·p_path`
  (`replay_validity.population_contrast_lower_bound`).

At the working value `p = .02`, `p_path = .04` and the tax is `.24` U. The grid
report, the tax and the reported bound all use this same mapping. The report
states that it covers allocation interference under the derived `m ≤ 3`. It
qualifies conclusions only; it is not a deployment safety guarantee and does
not produce a measurement-aware controller.
