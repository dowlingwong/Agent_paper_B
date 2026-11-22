"""Report layer for ``esyn_scaling``. ENGINEERING_ONLY.

AI-assisted (Claude, chat session, 22 Nov 2026). Not evidence, not an author decision.

``esyn_scaling.py`` is kept byte-identical to the run that wrote ``esyn/scaling_v1.json``, so that the stored
code hash can be checked. This module renders the report from that file: sections 1-5 come from
``esyn_scaling.markdown``; section 6 is recomputed here from the stored P3 and P4 tables with two corrections
made after the run and after independent review; section 7 is a written reading of the stored numbers and applies
to ``scaling_v1.json`` only. The corrections to section 6:

- the ``margin`` rung (``policies.BudgetMargin``) reads runs used / W, so it is grouped with the hand-built
  sequential rules, not with the one-step rules as in ``esyn_scaling.ONE_STEP``;
- the last column's rule: the first rendering called a world "not resolved" when a hand-built rule already
  reached the oracle member.

``python -m paperc.esyn_scaling --report-only`` would overwrite the report with the first rendering. Render with
this module; ``tests/test_esyn_scaling.py`` checks that the committed report is this module's output.
"""
from __future__ import annotations

import json
import sys

from paperc import esyn_scaling as es, learner_validation as lv
from paperc.esyn import dp, sim
from paperc.esyn import policies as esyn_policies

ONE_STEP = ("N2", "N2b", "shrink", "rawkeep")
SEQUENTIAL = ("N3", "N4", "margin", "kg", "race", "sprt")


def headroom():
    """``esyn_scaling.headroom`` with the corrected grouping (the stored JSON keeps the run's grouping)."""
    old = es.ONE_STEP, es.SEQUENTIAL
    es.ONE_STEP, es.SEQUENTIAL = ONE_STEP, SEQUENTIAL
    try:
        return es.headroom()
    finally:
        es.ONE_STEP, es.SEQUENTIAL = old


def dp_minus_static(result):
    """Paired DP − best static rule on the test roots (a few seconds; deterministic)."""
    world, _, _ = lv.setup()
    oracle = esyn_policies.Threshold(dp.solve(world).table)
    static = esyn_policies.Static(result["reference"]["best_static_threshold"], 0.0)
    return lv._paired(sim.campaign_values(world, oracle, lv.TEST) - sim.campaign_values(world, static, lv.TEST))


def verdict(w):
    """Room for a learned policy above the best hand-built row of one world."""
    if not w["gap_clear"]:
        return "none: no gap"
    if w["left_clear"]:
        return "yes"
    if w["left"] <= w["left_half_width"]:
        return "none shown: a hand-built rule reaches the oracle member"
    return "not resolved"


def headroom_section(result):
    h, ref = headroom(), result["reference"]
    if h["sources"] != result["headroom"]["sources"]:
        raise ValueError("the stored P3/P4 tables changed since the run")
    gap = ref["gap"]
    sigma = es._sigma_short()
    lines = [
        "## 6. Headroom table (stored P3 and P4 tables, no new simulation)", "",
        f"Each world's P4 ladder was tested on {h['n_test']:,} common roots. The gap is oracle member − N1, "
        "where N1 is the static rule tuned on dev roots. Two groups of hand-built rows are compared with it:", "",
        f"- **one-step rules** ({', '.join(ONE_STEP)}): each proposal is decided on its own forecast;",
        f"- **hand-built sequential rules** ({', '.join(SEQUENTIAL)}): they read the campaign state, such as "
        "the budget used or earlier measurements of the same configuration.", "",
        "This section was recomputed by the report module after the run: `margin` reads the budget used and "
        "was moved to the sequential group (the data file keeps the run's grouping), and the last column's rule "
        "was corrected. Neither change alters “gap” or “left”.", "",
        "“Left” is what remains between the best hand-built row and the oracle member, with its 95% half-width. "
        "It is the room a learned policy could win over rules written by hand. σ is the world's comparison "
        "noise.", "",
        "| World | Gap, 10⁻³ | Gap / σ | Best one-step rule: share of gap | Best sequential rule: share of gap | "
        "Left, 10⁻³ | Left / σ | Room for a learner |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]

    def group(x):
        return "—" if x is None else f"{x['rung']}: {es._pct(x['share'])}"

    for name, w in h["worlds"].items():
        lines.append(
            f"| {name} | {1e3 * w['gap']:.3f} ± {1e3 * w['gap_half_width']:.3f} | {w['gap_over_sigma']:.2f} | "
            f"{group(w['one_step'])} | {group(w['sequential'])} | "
            f"{1e3 * w['left']:.3f} ± {1e3 * w['left_half_width']:.3f} | {w['left_over_sigma']:.2f} | "
            f"{verdict(w)} |")
    left = ref["DP"] - ref["best_static_bayes_keep"]
    lines += [
        f"| p8_short_budget (exact; §4's world) | {1e3 * gap:.3f} | {gap / sigma:.2f} | "
        f"static threshold: {es._pct(ref['static_share_exact'])} | not run | {1e3 * left:.3f} | "
        f"{left / sigma:.2f} | {es._pct(1 - ref['static_share_exact'])} of the gap, above a one-step rule |",
        "", "Reading rules for this table:", "",
        "- The oracle member is the best member of a declared family, except in the two budget worlds and "
        "strict_null, where an exact DP exists. Elsewhere “left” is a lower bound on the true room, and a "
        "hand-built rule tuned on dev roots can exceed the oracle member.",
        "- A share is shown only where the gap exceeds twice its half-width.",
        "- “yes”: “left” exceeds twice its half-width. “none shown”: “left” does not exceed its half-width. "
        "“not resolved”: in between. The intervals are not corrected for the number of rows read.",
        "- The table says how much room exists. It does not say that R0, R1 or N6 can take it: those learners "
        "act on E1 and E2 only, and the worlds with room need actions they do not have (re-measure, re-audit) "
        "or state they do not see (which keys interact).", "",
    ]
    return lines


def reading(result):
    ref = result["reference"]
    gap = ref["gap"]
    static_read = ref["static_paired_check"]["mean"] / gap
    dp_read = ref["dp_paired_check"]["mean"] / gap
    sizes = result["design"]["sizes"]
    cells = result["cells"]

    def sel(cell, m):
        return cell["methods"][m]["selected"]["extended"]

    def row(n, m):
        return sel(es._cell(result, n, 0), m)

    r0 = {n: row(n, "R0")["gain_share"] for n in sizes}
    r1 = {n: row(n, "R1")["gain_share"] for n in sizes}
    n6 = {n: row(n, "N6")["gain_share"] for n in sizes}
    last = sizes[-1]
    r0_last = row(last, "R0")["vs_best_static"]
    above = {m: sum(sel(c, m)["vs_best_static"]["ci"][0] > 0 for c in cells) for m in ("N6", "R0", "R1")}
    below = {m: sum(sel(c, m)["vs_best_static"]["ci"][1] < 0 for c in cells) for m in ("N6", "R0", "R1")}
    ext = {m: sum(sel(c, m)["candidate"] >= es.N_P8[m] for c in cells) for m in ("R0", "R1")}
    passing = [c for c in cells if c["prefit"]["status"] == es.OK]
    r1_ties = [c for c in passing if sel(c, "R1")["vs_best_static"]["ci"][1] >= 0]
    ties_text = "; ".join(
        f"{c['n_roots']:,} roots, draw {c['draw']}: {1e5 * sel(c, 'R1')['vs_best_static']['mean']:+.1f} "
        f"[{1e5 * sel(c, 'R1')['vs_best_static']['ci'][0]:+.1f}, {1e5 * sel(c, 'R1')['vs_best_static']['ci'][1]:+.1f}]"
        for c in r1_ties)
    r0_4096 = sorted(sel(c, "R0")["gain_share"] for c in cells if c["n_roots"] == 4096)
    gates = {n: [c["prefit"]["status"] == es.OK for c in cells if c["n_roots"] == n] for n in sizes}
    first_pass = min(n for n, g in gates.items() if all(g))
    room_dp = dp_minus_static(result)
    h = headroom()["worlds"]
    room = [name for name, w in h.items() if verdict(w) == "yes"]
    reached = [name for name, w in h.items() if verdict(w).startswith("none shown")]
    n = len(cells)
    return [
        "## 7. Reading (written by the recorder for `scaling_v1.json`; AI-assisted; revised after independent "
        "review)", "",
        f"On the test roots the best static rule reads {es._pct(static_read)} of the exact gap and the DP "
        f"{es._pct(dp_read)}. The “best static rule” is the best static threshold computed from the world's true "
        "law. It is an upper bound on a static rule tuned on dev campaigns, so the comparison is hard on the "
        "learners.", "",
        f"**1. Up to {last:,} roots, more training data did not lift a learner above the static rule.** "
        f"Across the {n} training sets, the interval of the difference to the static rule lies above zero for "
        f"no learner ({above['N6']}, {above['R0']}, {above['R1']} of {n} for N6, R0, R1). It lies below zero in "
        f"{below['R0']} of {n} for R0, {below['R1']} of {n} for R1 and {below['N6']} of {n} for N6.",
        f"- **R0 (fitted Q iteration)** depends strongly on the data: in draw 0, {es._pct(r0[256])} of the gap at "
        f"256 roots, {es._pct(r0[1024])} at 1,024, {es._pct(r0[4096])} at 4,096 and {es._pct(r0[last])} at "
        f"{last:,}, where it is still {-1e5 * r0_last['mean']:.1f} × 10⁻⁵ below the static rule "
        f"(interval {1e5 * r0_last['ci'][0]:+.1f} to {1e5 * r0_last['ci'][1]:+.1f}). The step from 4,096 to "
        f"{last:,} roots is {100 * (r0[last] - r0[4096]):.1f} points in draw 0, but the two draws at 4,096 roots "
        f"read {es._pct(r0_4096[0])} and {es._pct(r0_4096[-1])}, and there is one draw at {last:,}. The slope "
        f"beyond 4,096 roots is therefore not determined. The added larger setting was selected in {ext['R0']} "
        f"of the {n} training sets.",
        f"- **R1 (IQL)** changes little with the data: in draw 0, {es._pct(r1[256])} at 256 roots and between "
        f"{es._pct(min(v for k, v in r1.items() if k >= 512))} and "
        f"{es._pct(max(v for k, v in r1.items() if k >= 512))} from 512 roots on. Draws differ by up to about "
        f"ten points at one size. Among the {len(passing)} training sets that pass the support gate, R1 is not "
        f"separable from the static rule in {len(r1_ties)} (difference × 10⁻⁵: {ties_text}) and below it in the "
        f"rest. The wider, longer-trained setting was selected in {ext['R1']} of the {n} training sets.",
        f"- **N6 (supervised corrector on fork labels)** is flat from 512 roots on (draw 0: "
        f"{es._pct(min(v for k, v in n6.items() if k >= 512))} to "
        f"{es._pct(max(v for k, v in n6.items() if k >= 512))}) and is not separable from the static rule in "
        f"{n - below['N6']} of {n} training sets.",
        f"- What this does not show: behaviour beyond {last:,} roots, or with other model classes and settings.",
        "", "**2. The support gate sets the smallest usable training set.** It fails in every draw up to 1,024 "
        f"roots and passes in every draw from {first_pass:,} roots. Rows below the gate show what the learners "
        "do there; they are not deployable policies under P8's rules.", "",
        "**3. This world leaves little room above the static rule, and no learner took it.** "
        f"The static rule takes {es._pct(ref['static_share_exact'])} of the gap. The DP is above it by "
        f"{1e5 * (ref['DP'] - ref['best_static_bayes_keep']):.1f} × 10⁻⁵ exactly, and by "
        f"{1e5 * room_dp['mean']:.1f} × 10⁻⁵ on the test roots (interval {1e5 * room_dp['ci'][0]:.1f} to "
        f"{1e5 * room_dp['ci'][1]:.1f}), so a policy that used the room would be visible on these roots. "
        "The world is adequate for validating the learners' code path, which is what runbook phase P8 is for. "
        "As a test of whether learned sequential control pays, it is weak: the best possible result is a small "
        "margin over a one-step rule.", "",
        "**4. Where room exists (§6).** A hand-built sequential rule reaches the oracle member in "
        f"{', '.join(reached)} (in the budget world N4, a DP with an estimated law, whose recursion is exact "
        "for that world by construction). Room above every hand-built row is resolved in "
        f"{', '.join(room)}. Those worlds reward re-measuring a candidate, re-auditing the incumbent, or "
        "tracking which recurring keys enable each other. The present learners have none of these actions or "
        "state features.", "",
        "**5. Suggestions (the recorder's; input for the author's R1-PAPERC-CORE, not a decision).**",
        "- In E-SYN's two budget worlds, a static rule or an estimated-law DP takes the gap. Whether budget "
        "pacing leaves room on real nodes is what SPT-1 measures; E-SYN does not answer it.",
        "- Within E-SYN, a learner comparison that can come out either way needs a world where §6 shows room, "
        "and learners with that channel's actions. A candidate next step is a learner validation in "
        "shared_error or eval_allocation with a re-audit or re-measure action.",
        "- A static rule tuned on dev campaigns should be reported beside every learned arm.",
        "- A longer curve in this world needs a new seed-registry block for recorded roots. Point 3 argues "
        "against spending one here.", "",
        "**Limits.** One synthetic world for the curve. Draw 0 is nested, so its points share data. At most "
        "three training draws per size, two at 4,096 and one at 8,192. The intervals cover test roots, not "
        "training draws, and are not corrected for the number of comparisons. Grids are small. R1's training "
        "steps do not grow with the data except in the one added setting.", "",
    ]


def markdown(result):
    text = es.markdown(result)
    head = text[:text.index("## 6. Headroom table")].rstrip("\n")
    head = head.replace("Generated by `python -m paperc.esyn_scaling`;",
                        "Run by `python -m paperc.esyn_scaling`; rendered by `python -m paperc.esyn_scaling_report`;")
    stored = "matches" if result["code_sha256"] == es.code_sha256() else "DOES NOT MATCH"
    note = (f"\n\nCode hash stored in the data file: `{result['code_sha256'][:16]}…`; it {stored} the "
            "committed `esyn_scaling.py` and its sources.")
    return "\n".join([head + note, "", *headroom_section(result), *reading(result)])


def main(argv=None):
    result = json.loads(es.OUT.read_text())
    es.REPORT.write_text(markdown(result))
    return es.REPORT


if __name__ == "__main__":
    print(main(sys.argv[1:]))
