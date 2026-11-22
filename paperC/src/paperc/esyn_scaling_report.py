"""Report layer for ``esyn_scaling``. ENGINEERING_ONLY.

AI-assisted (Claude, chat session, 22 Nov 2026). Not evidence, not an author decision.

``esyn_scaling.py`` is kept byte-identical to the run that wrote ``esyn/scaling_v1.json``, so that the stored
code hash can be checked. This module renders the report from that file: sections 1-5 come from
``esyn_scaling.markdown``; section 6 is rendered here with a corrected last column (the first rendering called a
world "not resolved" when a hand-built rule already reached the oracle member); section 7 is a written reading
of the stored numbers and applies to ``scaling_v1.json`` only.
"""
from __future__ import annotations

import json
import sys

from paperc import esyn_scaling as es


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
    h, ref = result["headroom"], result["reference"]
    gap = ref["gap"]
    sigma = es._sigma_short()
    lines = [
        "## 6. Headroom table (stored P3 and P4 tables, no new simulation)", "",
        f"Each world's P4 ladder was tested on {h['n_test']:,} common roots. The gap is oracle member − N1, "
        "where N1 is the static rule tuned on dev roots. Two groups of hand-built rows are compared with it:", "",
        f"- **one-step rules** ({', '.join(es.ONE_STEP)}): each proposal is decided on its own forecast;",
        f"- **hand-built sequential rules** ({', '.join(es.SEQUENTIAL)}): they read the campaign state, such as "
        "the budget left or earlier measurements of the same configuration.", "",
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

    def row(n, m):
        return es._cell(result, n, 0)["methods"][m]["selected"]["extended"]

    r0 = {n: row(n, "R0")["gain_share"] for n in result["design"]["sizes"]}
    r1 = {n: row(n, "R1")["gain_share"] for n in result["design"]["sizes"]}
    n6 = {n: row(n, "N6")["gain_share"] for n in result["design"]["sizes"]}
    last = result["design"]["sizes"][-1]
    r0_last = row(last, "R0")["vs_best_static"]
    r1_last = row(last, "R1")["vs_best_static"]
    gates = {n: [c["prefit"]["status"] == es.OK for c in result["cells"] if c["n_roots"] == n]
             for n in result["design"]["sizes"]}
    first_pass = min(n for n, g in gates.items() if all(g))
    ext = {m: sum(c["methods"][m]["selected"]["extended"].get("candidate", 0) >= es.N_P8[m]
                  for c in result["cells"]) for m in ("R0", "R1")}
    above = sum(c["methods"][m]["selected"]["extended"]["vs_best_static"]["ci"][0] > 0
                for c in result["cells"] for m in ("N6", "R0", "R1")
                if c["methods"][m]["selected"]["extended"].get("status") == "evaluated")
    h = result["headroom"]["worlds"]
    room = [name for name, w in h.items() if verdict(w) == "yes"]
    return [
        "## 7. Reading (written by the recorder for `scaling_v1.json`; AI-assisted)", "",
        f"On the test roots the best static rule reads {es._pct(static_read)} of the exact gap and the DP "
        f"{es._pct(dp_read)}. A learner that matters has to land between those two numbers.", "",
        "**1. P8's result is not an effect of the training size, within the sizes this world can log.**",
        f"- **R0 (fitted Q iteration)** depends strongly on the data: {es._pct(r0[256])} of the gap at 256 roots, "
        f"{es._pct(r0[1024])} at 1,024, {es._pct(r0[4096])} at 4,096 and {es._pct(r0[last])} at {last:,}. "
        f"The curve flattens: the last doubling adds {100 * (r0[last] - r0[4096]):.1f} points. At {last:,} roots "
        f"it is still {-1e5 * r0_last['mean']:.1f} × 10⁻⁵ below the static rule "
        f"(interval {1e5 * r0_last['ci'][0]:+.1f} to {1e5 * r0_last['ci'][1]:+.1f}). "
        f"The added larger setting was selected in {ext['R0']} of the {len(result['cells'])} training sets.",
        f"- **R1 (IQL)** saturates early: {es._pct(r1[256])} at 256 roots and between "
        f"{es._pct(min(v for n, v in r1.items() if n >= 512))} and "
        f"{es._pct(max(v for n, v in r1.items() if n >= 512))} from 512 roots on, with no trend. "
        f"In draw 0 it stays below the static rule at every size ({1e5 * r1_last['mean']:+.1f} × 10⁻⁵ at "
        f"{last:,} roots, interval {1e5 * r1_last['ci'][0]:+.1f} to {1e5 * r1_last['ci'][1]:+.1f}). "
        f"The wider, longer-trained setting was selected in {ext['R1']} of the {len(result['cells'])} training "
        "sets, without a consistent gain. Other draws move the share by up to about ten points, so "
        "single-draw differences of that size are not signal.",
        f"- **N6 (supervised corrector on fork labels)** is flat from 512 roots on "
        f"({es._pct(min(v for n, v in n6.items() if n >= 512))} to "
        f"{es._pct(max(v for n, v in n6.items() if n >= 512))}) and is not separable from the static rule "
        "at any of those sizes.",
        f"- In {above} of the {3 * len(result['cells'])} learner-by-training-set results, the interval of the "
        "difference to the static rule lies above zero.", "",
        "**2. The support gate sets the smallest usable training set.** It fails in every draw up to 1,024 roots "
        f"and passes in every draw from {first_pass:,} roots. Rows below the gate show what the learners do "
        "there; they are not deployable policies under P8's rules.", "",
        "**3. This world cannot show a learner beating simple rules, whatever the data size.** "
        f"The static rule already takes {es._pct(ref['static_share_exact'])} of the gap. The room above it is "
        f"{1e5 * (ref['DP'] - ref['best_static_bayes_keep']):.1f} × 10⁻⁵, about twice the half-width of a "
        "paired comparison on the 6,000 test roots for N6 and R1. P8 used this world to validate the learners' code path, and it "
        "serves that purpose. It does not serve as a test of whether learned sequential control pays.", "",
        "**4. Where room exists (§6).** A hand-built sequential rule reaches the oracle member in the budget "
        "world (N4, the DP with an estimated law) and in keep_feedback (N3). Room above every hand-built row "
        f"is resolved in {', '.join(room)}. Those worlds reward re-measuring a candidate, re-auditing the "
        "incumbent, or tracking which recurring keys enable each other. The present learners have none of these "
        "actions or state features.", "",
        "**5. What this suggests for the plan (input to R1-PAPERC-CORE; not a decision).**",
        "- The budget-pacing channel alone is unlikely to carry a claim that learned multi-step control beats "
        "hand-built rules: a static rule or an estimated-law DP takes the gap in both budget worlds.",
        "- A learner comparison that can come out either way needs a world, and later a node, where §6 shows "
        "room, and learners that have the actions of that channel. The first step would be an E-SYN learner "
        "validation in shared_error or eval_allocation with a re-audit or re-measure action.",
        "- The static rule tuned on dev campaigns is the baseline every learned arm has to be reported against.",
        "- A longer curve in this world needs a new seed-registry block; given point 3 it is not worth one.", "",
        "**Limits.** One synthetic world for the curve. Draw 0 is nested, so its points share data. At most "
        "three training draws per size, two at 4,096 and one at 8,192. The intervals cover test roots, not "
        "training draws. Grids are small and were not re-tuned per size beyond the declared settings. "
        "R1's training steps do not grow with the data except in the one added setting.", "",
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
