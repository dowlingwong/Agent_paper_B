#!/usr/bin/env python3
"""Build the TASL launch chain (R1-T1-DATA-MANIFEST) on a base commit, reproducibly. Not used by any job.

Usage:
  python sweep2/t1_tasl/build_launch_chain.py build <config.json> --worktree <clean worktree> [--table-out <file>]

``build`` resets the config's branch to the config's base and writes (a) G.1b, (b) cross-check and (c) G.4 spec commits,
one spec file (plus docs/) per commit, each spec's paper.commit its commit's parent; then the tail (the files
``tail_paths`` taken from ``tail_ref``) and the generated launch table. Author and committer dates are pinned from the
config, so the same config and base give the same shas. **Never run ``build`` again once any run of the chain has
launched**: the shas would change. (d), the AR spec, is not built here: it is a later delivery, one commit on top of
the published (a)–(c) (the TASL-2 host check at the AR pin STOPped on Python 3.12.16 vs 3.12.15, 22 Nov 2026).
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

CFG: dict = {}
W = Path(".")
OLD = {"mlgym_fmnist": "8d28287b819353ee725561bbeec10a7aa0b53a7b76e08c606167e61edd082b9c",
       "mlgym_cifar10": "c0ef1168e9c575fe367b607fc3c945e021323d307edd674c832bab5dd112ba40"}
G1B = "sweep2/t1_tasl/g1b_tasl_spec.json"
XC = "sweep2/t1_tasl/g1b_crosscheck_spec.json"
G4 = "sweep2/t1_tasl/g4_tasl_spec.json"
AR = "sweep2/t1_tasl/g1b_tasl_ar_spec.json"
PROP = "docs/r1/proposals/"
AUTH = "docs/r1/authorizations/"
REVIEW = "docs/r1/reviews/TASL_LAUNCH_CHAIN_REVIEW_20261122.md"
OLD_G1B_SHA = "060aac91ba452a69e4e898b66b92ebd5bfc0887c2933cfd2e438d93d17ecb465"


def _env():
    import os
    d = CFG["commit_date"]
    return dict(os.environ, GIT_AUTHOR_DATE=d, GIT_COMMITTER_DATE=d, GIT_AUTHOR_NAME=CFG["author_name"],
                GIT_AUTHOR_EMAIL=CFG["author_email"], GIT_COMMITTER_NAME=CFG["author_name"],
                GIT_COMMITTER_EMAIL=CFG["author_email"])


def git(*a, check=True):
    r = subprocess.run(["git", "-C", str(W), *a], capture_output=True, text=True, env=_env())
    if check and r.returncode:
        raise SystemExit(f"git {' '.join(a)}: {r.stderr}")
    return r.stdout.strip()


def sha(rel):
    return hashlib.sha256((W / rel).read_bytes()).hexdigest()


def sub1(text, old, new, what):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{what}: expected one occurrence, found {n}: {old[:80]!r}")
    return text.replace(old, new)


def set_paper_commit(rel, commit):
    t = (W / rel).read_text()
    m = re.search(r'"paper": \{\s*"repo": "[^"]+",\s*"commit": "([^"]+)"', t)
    if not m:
        raise SystemExit(f"no paper block in {rel}")
    t = t[:m.start(1)] + commit + t[m.end(1):]
    (W / rel).write_text(t)


def read(rel):
    return (W / rel).read_text()


def write(rel, text):
    p = W / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def commit(msg, files, trailers):
    git("add", "--", *files)
    changed = git("diff", "--cached", "--name-only").splitlines()
    specs = [f for f in changed if not f.startswith("docs/")]
    body = msg + "\n\n" + ("\n".join(trailers) + "\n\n" if trailers else "") + CFG["trailer_lines"]
    subprocess.run(["git", "-C", str(W), "commit", "-q", "-m", body], check=True, env=_env())
    return git("rev-parse", "HEAD"), specs


def fields_replace(text, mapping, what):
    """Replace whole 'key: value' lines (keys must exist exactly once)."""
    for key, value in mapping.items():
        rx = re.compile(rf"^{re.escape(key)}: .*$", re.M)
        hits = rx.findall(text)
        if len(hits) != 1:
            raise SystemExit(f"{what}: field {key} found {len(hits)} times")
        text = rx.sub(lambda _m: f"{key}: {value}", text)
    return text


def node_line_value(text, node, new, what):
    rx = re.compile(rf"^(node_{node}: .*data_manifest_sha256 ){OLD[node]}(;.*)$", re.M)
    if len(rx.findall(text)) != 1:
        raise SystemExit(f"{what}: node line {node}")
    return rx.sub(lambda m: m.group(1) + new + " (census erratum, R1-T1-DATA-MANIFEST; was " + OLD[node][:8]
                  + "…)" + m.group(2), text)


def p4_with(body: str, er, p4_er: str) -> str:
    """The note's P4 (the reviews) with the launch-chain review and the census erratum record appended; PASS with the
    record's path, sha256 and review, PENDING with <FILL> fields while it is not given (``g1b_tasl.check_note`` refuses a P4 that is not PASS)."""
    orig = re.search(r"^P4: (.*)$", body, re.M).group(1)
    text = re.sub(r"^(PASS|PENDING) [—-] ", "", orig)
    return ("PASS — " if er else "PENDING — ") + text + f"; the launch chain of R1-T1-DATA-MANIFEST: {REVIEW}; the " + p4_er


def main():
    base = CFG["base"]
    vals = CFG["values"]
    er = CFG.get("erratum")
    er_text = (f"{er['record']} sha256 {er['sha256']}" if er else
               "<FILL at signature: the independently reviewed census erratum record of R1-T1-DATA-MANIFEST "
               "(path on main and sha256); its two corrected manifest sha256 must equal the values on the node lines>")
    p4_er = (f"census erratum record {er['record']} sha256 {er['sha256']} (review {er['review']})" if er else
             "census erratum record <FILL: the path on main> sha256 <FILL> (its independent review "
             "docs/r1/reviews/<FILL>)")
    er_bullet = (
        f"- **The census erratum** is part of P4, which cites the independently reviewed erratum record `{er['record']}`\n"
        f"  (sha256 `{er['sha256'][:8]}…`, the bytes its review fixes; review `{er['review']}`), published on `main`\n"
        "  byte-identical, with the review's editorial conditions in a separate addendum beside it. The cited sha256\n"
        "  must be one a review fixes: if the record on `main` differs, STOP (no correction at signature).\n"
        "  `python sweep2/t1_tasl/g1b_tasl_join.py publication-check <note> --p4` checks it against `origin/main`.\n") if er else (
        "- **The census erratum** is part of P4: P4 stays PENDING until the independently reviewed erratum record of\n"
        "  R1-T1-DATA-MANIFEST is on `main`, and `g1b_tasl.launch` refuses the note while P4 is not PASS.\n")
    er_sign = ("check P4's erratum sha256 against the published record" if er else
               "complete P4 with the erratum record")
    if git("status", "--porcelain"):
        raise SystemExit("build: the worktree must be clean (it resets the branch)")
    git("checkout", "-q", "-f", "-B", CFG["branch"], base)
    table = []

    # ------------------------------------------------------------------ (a) G.1b spec
    t = read(G1B)
    for node, new in vals.items():
        t = sub1(t, f'"data_manifest_sha256": "{OLD[node]}"', f'"data_manifest_sha256": "{new}"', f"g1b {node}")
    write(G1B, t)
    set_paper_commit(G1B, base)
    g1b_sha = sha(G1B)
    first = read(AUTH + "g1b_t1_tasl_20261121.md")
    head_end = re.search(r"^approved: true$", first, re.M).start()
    amend_head = (
        "# G.1b on the TASL pair — amendment note for `mlgym_fmnist` on TASL-2 (R1-T1-DATA-MANIFEST) — DRAFT for "
        "signature\n\n"
        "This draft amends the signed first note `docs/r1/authorizations/g1b_t1_tasl_20261121.md` under\n"
        "R1-T1-DATA-MANIFEST (option A) and changes only what that row changes. The census data manifests of\n"
        "`mlgym_fmnist` and `mlgym_cifar10` become the manifests the frozen environment produces (their four data\n"
        "arrays are byte-identical to the census; only `source.datasets` differs). The spec\n"
        f"`{G1B}` is re-issued with those two values and `paper.commit` `{base}`;\n"
        "nothing else in it changes, and the run id stays `g1b-tasl-20261121-b`.\n\n"
        "- **What it launches:** `mlgym_fmnist` on TASL-2 only, as a new attempt of the same run (its two\n"
        "  infrastructure attempts under the first note stay in the runs tree, unsealed). The three sealed TASL-2 nodes\n"
        "  (`mlab_ogbn_arxiv`, `mlab_imdb`, `mlgym_houseprice`) stay under the first note and are not rerun: their\n"
        "  complete attempts refuse a new attempt (`next_attempt`, on TASL-2's runs tree: the note's text does not\n"
        "  limit `launch` to one node, so those attempt directories must be kept). The TASL-7 nodes run under note 2\n"
        "  (P7 here is PENDING, so `launch` refuses them under this note).\n"
        + er_bullet +
        "- **Launch:** from the published commit that changes the G.1b spec to `spec_sha256` below (its parent is\n"
        "  `paper_commit`), or a docs-only descendant of it (`verify_launch_tasl`), with the signed note copied from\n"
        "  `origin/main` into that checkout's `docs/r1/authorizations/` (an untracked docs file). The launch table is\n"
        "  `docs/r1/reports/tasl_chain_20261122/LAUNCH_TABLE.md`.\n"
        "- **Code.** The first note's three attempts ran the code of `10fd3343`; this note's attempt runs that of\n"
        f"  `{base[:8]}`. Between them the job path changes only by the autoresearch-only branches of `g1b_tasl.py` (the\n"
        "  AR spec kind, its validation and summary schema) and the cross-check kind of `t1_tasl_node.sh`; `g1b_lib.py`\n"
        "  and `r1/noise` are unchanged (decision G1B-JOIN in the chain report).\n"
        "- **Assembly:** the seven-node row joins the first note's three sealed attempts (old spec sha256 `060aac91…`)\n"
        "  with this note's and note 2's attempts (this spec). That needs the assembly rule of decision G1B-JOIN\n"
        "  (in the chain report); until an author row decides it, `g1b_tasl.assemble` STOPs on the two spec sha256s.\n"
        "- **Signature:** copy to `docs/r1/authorizations/g1b_t1_tasl_<YYYYMMDD>.md` (a date not used by another G.1b\n"
        "  note: not 20261121), set `approved: true`, " + er_sign + ", and publish byte-identically\n"
        "  on `main`.\n"
        "  The coordinating chat signs it under R1-T1-DATA-MANIFEST's pre-authorization.\n\n"
        "Prepared by the Mac-desk agent (Claude), AI-assisted, 22 Nov 2026; independently reviewed with the launch\n"
        "chain (P10).\n\n")
    body = first[head_end:]
    body = fields_replace(body, {
        "approved": "false",
        "paper_commit": base,
        "spec_sha256": g1b_sha,
        "spec": f"{G1B}; the signed first note's spec (sha256 {OLD_G1B_SHA}) re-issued under R1-T1-DATA-MANIFEST with "
                "two data_manifest_sha256 values (mlgym_fmnist, mlgym_cifar10) and paper.commit changed; run_id "
                "unchanged",
        "nodes": "the seven nodes of R1-TRACKG-G3-EARLY as in the first note; this amendment launches mlgym_fmnist "
                 "only; autoresearch_fixedtokens runs under the third note (R1-G1B-NOTE2-DECISIONS)",
        "P4": p4_with(body, er, p4_er),
        "P10": "PASS — the launch chain of R1-T1-DATA-MANIFEST (specs, this amendment, note 2, the re-issued "
               f"cross-check and G.4 notes), independently reviewed: {REVIEW}; the launch binding and check_note as "
               "for the first note (docs/r1/reviews/G1B_TASL_NOTE_REVIEW_20261121.md)",
    }, "amendment")
    for node, new in vals.items():
        body = node_line_value(body, node, new, "amendment")
    body = sub1(body, "\nP1: ", "\namends: docs/r1/authorizations/g1b_t1_tasl_20261121.md (the first note; its three "
                "sealed TASL-2 attempts stay under it and are not rerun)" +
                "\nscope: this amendment launches mlgym_fmnist of run g1b-tasl-20261121-b on TASL-2; the three sealed "
                "TASL-2 nodes stay under the first note; the TASL-7 nodes run under note 2\nP1: ", "amendment P1")
    write(PROP + "G1B_T1_TASL_AMEND_FMNIST_DRAFT_20261122.md", amend_head + body)

    n2 = read(PROP + "G1B_T1_TASL_NOTE2_DRAFT_20261121.md")
    n2_end = re.search(r"^approved: false$", n2, re.M).start()
    n2_head = (
        "# G.1b on the TASL pair — second authorization note (the three TASL-7 nodes) — DRAFT for signature "
        "(revised 22 Nov 2026 for R1-T1-DATA-MANIFEST)\n\n"
        "This draft is the second note of R1-G1B-TASL-DECISIONS (XC A) for the three TASL-7 nodes (`mlab_cifar10`,\n"
        "`mlgym_cifar10`, `mlgym_breakout_minatar`) of run `g1b-tasl-20261121-b`. R1-T1-DATA-MANIFEST amends\n"
        "R1-G1B-NOTE2-DECISIONS' \"same run_id, paper_commit and spec_sha256\" in two of its three parts: note 2 binds the\n"
        f"re-issued spec (the same as the amendment note for `mlgym_fmnist`), `spec_sha256` `{g1b_sha[:8]}…`, and so the\n"
        f"`paper_commit` its launch binding needs, `{base}` (the row's \"each with the paper_commit its launch binding\n"
        "needs\"). The run id and harness are the first note's. The TASL-7 attempts therefore run the code of\n"
        f"`{base[:8]}`, not `10fd3343`; between them the job path changes only by the autoresearch-only branches of\n"
        "`g1b_tasl.py` and the cross-check kind of `t1_tasl_node.sh` (`g1b_lib.py` and `r1/noise` unchanged; decision\n"
        "G1B-JOIN in the chain report).\n\n"
        "**Changes against the 21 Nov draft:** `paper_commit`, `spec_sha256`, the `spec` line, the corrected manifest\n"
        "values on the `mlgym_fmnist` and `mlgym_cifar10` node lines; P4 and P10 (the launch-chain review and the census\n"
        "erratum record); P12 (autoresearch now under the third note: PASS, it is not in this run); the `nodes` and\n"
        "`scope` lines (the amendment note and the joined assembly); the re-issued cross-check run id in P7's template.\n\n"
        "- **Launch:** the TASL-7 nodes launch from the published commit that changes the G.1b spec to this\n"
        "  `spec_sha256` (or a docs-only descendant), not from `985dd45d` (launch table:\n"
        "  `docs/r1/reports/tasl_chain_20261122/TASL_CHAIN_20261122.md`).\n"
        "- **P7** stays PENDING until the re-issued cross-check (run `" + CFG["xc_run_id"] + "`) has run and its three\n"
        "  step-1 verdicts are on `main`; then P7 is completed from the template below and checked twice with\n"
        "  `python sweep2/t1_tasl/g1b_crosscheck.py check-note2 sweep2/t1_tasl/g1b_crosscheck_spec.json --note <note>\n"
        "  --verdict <path> (x3)`, first with `--draft` (unsigned, copied to its final name), then strict on the\n"
        "  published note before any TASL-7 node launches.\n"
        "- **Assembly:** all seven nodes assemble into one row through the gated assembly of decision G1B-JOIN (the\n"
        "  first note's three sealed attempts carry the old spec sha256).\n"
        + er_bullet +
        "- **Signature:** copy to `docs/r1/authorizations/g1b_t1_tasl_<YYYYMMDD>.md` with a date no other G.1b note\n"
        "  uses, `approved: true`, and publish byte-identically on `main`; the TASL-7 host copies it from `origin/main`\n"
        "  into its launch checkout's `docs/r1/authorizations/` (an untracked docs file). Signed by the coordinating\n"
        "  chat under R1-T1-DATA-MANIFEST.\n\n"
        "Prepared by the Mac-desk agent (Claude), AI-assisted, 21 Nov 2026, revised 22 Nov 2026; independently reviewed\n"
        "with the cross-check unit and with the launch chain.\n\n")
    b2 = n2[n2_end:]
    b2 = fields_replace(b2, {
        "paper_commit": base,
        "spec_sha256": g1b_sha,
        "spec": f"{G1B}, re-issued under R1-T1-DATA-MANIFEST (the first note's spec sha256 {OLD_G1B_SHA} with two "
                "data_manifest_sha256 values, mlgym_fmnist and mlgym_cifar10, and paper.commit changed); run_id "
                "unchanged; the same spec as the amendment note",
        "nodes": "the seven nodes of R1-TRACKG-G3-EARLY in this run's spec; this note launches the three TASL-7 nodes; "
                 "autoresearch_fixedtokens runs under the third note with its own spec (R1-G1B-NOTE2-DECISIONS)",
        "P10": "PASS — the launch binding verify_launch_tasl, the run_id and harness_commit checks of check_note, and the "
               "first note, independently reviewed: docs/r1/reviews/G1B_TASL_NOTE_REVIEW_20261121.md (decision LB); "
               "the cross-check job, its gated assembly and this second note: "
               "docs/r1/reviews/G1B_CROSSCHECK_REVIEW_20261121.md; the re-issued spec and this revision: " + REVIEW,
        "P4": p4_with(b2, er, p4_er),
        "P12": "PASS — autoresearch_fixedtokens is not in this run: it joins G.1b under the third note with its own "
               "spec (R1-G1B-NOTE2-DECISIONS NOTE2-AR A; R1-G1B-AR-ENV)",
        "scope": "this second note launches the three TASL-7 nodes of run g1b-tasl-20261121-b (spec as the amendment "
                 "note, harness as the first note); the three sealed TASL-2 nodes stay under the first note and "
                 "mlgym_fmnist runs under the amendment note; all seven nodes assemble into one row through the gated "
                 "assembly of decision G1B-JOIN",
    }, "note2")
    for node, new in vals.items():
        b2 = node_line_value(b2, node, new, "note2")
    b2 = b2.replace("docs/r1/authorizations/g1b_xc_t1_tasl_<date>.md;",
                    "docs/r1/authorizations/g1b_xc_t1_tasl_<date>.md (the re-issued note, run " + CFG["xc_run_id"] + ");")
    write(PROP + "G1B_T1_TASL_NOTE2_DRAFT_20261121.md", n2_head + b2)
    ca, specs = commit(
        "t1 tasl chain (a): G.1b spec re-issued under R1-T1-DATA-MANIFEST (mlgym_fmnist, mlgym_cifar10 data "
        "manifests); amendment note and note 2 drafts",
        [G1B, PROP + "G1B_T1_TASL_AMEND_FMNIST_DRAFT_20261122.md", PROP + "G1B_T1_TASL_NOTE2_DRAFT_20261121.md"],
        [f"T1-Launch-Run: g1b-amendment (mlgym_fmnist), g1b-note2 (TASL-7 nodes)", f"T1-Launch-Spec: {G1B} {g1b_sha}",
         f"T1-Paper-Commit: {base}"])
    assert specs == [G1B], specs
    table += [{"run": "g1b-amendment", "nodes": ["mlgym_fmnist"], "run_id": "g1b-tasl-20261121-b", "spec": G1B,
               "spec_sha256": g1b_sha, "paper_commit": base, "launch_commit": ca,
               "note_draft": PROP + "G1B_T1_TASL_AMEND_FMNIST_DRAFT_20261122.md"},
              {"run": "g1b-note2", "nodes": ["mlab_cifar10", "mlgym_breakout_minatar", "mlgym_cifar10"],
               "run_id": "g1b-tasl-20261121-b", "spec": G1B, "spec_sha256": g1b_sha, "paper_commit": base,
               "launch_commit": ca, "note_draft": PROP + "G1B_T1_TASL_NOTE2_DRAFT_20261121.md"}]

    # ------------------------------------------------------------------ (b) cross-check spec
    t = read(XC)
    t = sub1(t, f'"run_id": "g1b-tasl-20261121-b-xc"', f'"run_id": "{CFG["xc_run_id"]}"', "xc run_id")
    t = sub1(t, f'"sha256": "{OLD_G1B_SHA}"', f'"sha256": "{g1b_sha}"', "xc g1b sha")
    t = sub1(t, '"commit": "ea34b1ab72c22769527f902850fe929d1ceccf67"', f'"commit": "{ca}"', "xc paper")
    t = re.sub(r'"comment": "[^"]*"', '"comment": "R1-T1-TASL-ENV cross-host check of the G.1b TASL-7 nodes '
               '(g1b_crosscheck.py), re-issued under R1-T1-DATA-MANIFEST: it binds the re-issued G.1b spec and reruns '
               'in full under a new run id; paper.commit is the parent of the commit that carries this spec in the '
               'launch chain (verify_launch_tasl)."', t, count=1)
    write(XC, t)
    xc_sha = sha(XC)
    xn = read(AUTH + "g1b_xc_t1_tasl_20261122.md")
    xn_end = re.search(r"^approved: true$", xn, re.M).start()
    xc_head = (
        "# G.1b cross-host check — re-issued authorization note (R1-T1-TASL-ENV; R1-T1-DATA-MANIFEST) — DRAFT for "
        "signature\n\n"
        "This draft re-issues `docs/r1/authorizations/g1b_xc_t1_tasl_20261122.md` under R1-T1-DATA-MANIFEST: the\n"
        "cross-check spec binds the re-issued G.1b spec and reruns in full. Changes, and only these:\n"
        f"- `g1b_spec_sha256` `{g1b_sha[:8]}…` (the re-issued G.1b spec, with the corrected `mlgym_fmnist` and\n"
        "  `mlgym_cifar10` data manifests);\n"
        f"- `run_id` `{CFG['xc_run_id']}`: a full rerun cannot reuse `g1b-tasl-20261121-b-xc`, whose TASL-7\n"
        "  `mlab_cifar10` attempt is sealed and complete (`next_attempt` refuses a new attempt, and the sealed target\n"
        "  exists); that attempt is kept as an engineering record (R1-T1-DATA-MANIFEST);\n"
        f"- `paper_commit` `{ca}` and `xc_spec_sha256`; the jobs line's run ids follow the run id.\n\n"
        "- the spec's `comment` describes the re-issue.\n\n"
        "**Supersedes** `g1b_xc_t1_tasl_20261122.md`: that note and its run `g1b-tasl-20261121-b-xc` are not used\n"
        "again (its checkout could still launch the untouched `mlgym_breakout_minatar` under the old run; nobody\n"
        "does). Launch from the published commit that changes the cross-check spec to `xc_spec_sha256` (its parent is\n"
        "`paper_commit`), or a docs-only descendant, with the signed note copied from `origin/main` into its\n"
        "`docs/r1/authorizations/` (launch table: `docs/r1/reports/tasl_chain_20261122/LAUNCH_TABLE.md`). Signature:\n"
        "copy to\n"
        "`docs/r1/authorizations/g1b_xc_t1_tasl_<YYYYMMDD>.md` with a date no other cross-check note uses (not\n"
        "20261122), `approved: true`, and publish byte-identically on `main`; signed by the coordinating chat under\n"
        "R1-T1-DATA-MANIFEST. Prepared by the Mac-desk agent (Claude), AI-assisted, 22 Nov 2026.\n\n")
    xb = xn[xn_end:]
    old_jobs = re.search(r"^jobs: .*$", xb, re.M).group(0)
    new_jobs = old_jobs.replace("g1b-tasl-20261121-b-xc-TASL-7 and g1b-tasl-20261121-b-xc-TASL-2",
                                f"{CFG['xc_run_id']}-TASL-7 and {CFG['xc_run_id']}-TASL-2")
    assert new_jobs != old_jobs
    xb = xb.replace(old_jobs, new_jobs)
    xb = fields_replace(xb, {
        "approved": "false", "run_id": CFG["xc_run_id"], "paper_commit": ca, "xc_spec_sha256": xc_sha,
        "g1b_spec_sha256": g1b_sha,
        "P4": "PASS — independent review of the cross-check unit: docs/r1/reviews/G1B_CROSSCHECK_REVIEW_20261121.md; "
              f"the re-issued spec and this note: {REVIEW}",
    }, "xc note")
    xb = sub1(xb, "\nP1: ", "\nreissue: re-issues docs/r1/authorizations/g1b_xc_t1_tasl_20261122.md under "
              "R1-T1-DATA-MANIFEST (full rerun; the sealed TASL-7 mlab_cifar10 attempt of run "
              "g1b-tasl-20261121-b-xc-TASL-7 is kept as an engineering record)\ncensus_erratum: " + er_text + "\nP1: ",
              "xc P1")
    write(PROP + "G1B_XC_NOTE_REISSUE_DRAFT_20261122.md", xc_head + xb)
    cb, specs = commit("t1 tasl chain (b): cross-check spec re-issued (binds the re-issued G.1b spec; new run id for "
                       "the full rerun); re-issued note draft",
                       [XC, PROP + "G1B_XC_NOTE_REISSUE_DRAFT_20261122.md"],
                       ["T1-Launch-Run: crosscheck", f"T1-Launch-Spec: {XC} {xc_sha}", f"T1-Paper-Commit: {ca}"])
    assert specs == [XC], specs
    table.append({"run": "crosscheck", "nodes": ["mlab_cifar10", "mlgym_breakout_minatar", "mlgym_cifar10"],
                  "run_id": CFG["xc_run_id"], "spec": XC, "spec_sha256": xc_sha, "paper_commit": ca,
                  "launch_commit": cb, "note_draft": PROP + "G1B_XC_NOTE_REISSUE_DRAFT_20261122.md"})

    # ------------------------------------------------------------------ (c) G.4 spec
    t = read(G4)
    t = sub1(t, f'"data_manifest_sha256": "{OLD["mlgym_fmnist"]}"', f'"data_manifest_sha256": "{vals["mlgym_fmnist"]}"',
             "g4 fmnist")
    write(G4, t)
    set_paper_commit(G4, cb)
    g4_sha = sha(G4)
    gn = read(AUTH + "g4_t1_tasl_20261122.md")
    gn_end = re.search(r"^approved: true$", gn, re.M).start()
    g4_head = (
        "# G.4 on the TASL pair — re-issued authorization note (T1 pilot; R1-T1-DATA-MANIFEST) — DRAFT for signature\n\n"
        "This draft re-issues `docs/r1/authorizations/g4_t1_tasl_20261122.md` (its author decisions G4-LB A, G4-ORDER B\n"
        "and G4-NODE3 A stand, R1-G4-DECISIONS) under R1-T1-DATA-MANIFEST. Changes, and only these:\n"
        f"- the G.4 spec's `mlgym_fmnist` data manifest becomes `{vals['mlgym_fmnist'][:8]}…` (the census erratum), as in the\n"
        "  re-issued G.1b spec that `g4_tasl.py validate` compares node pins with;\n"
        f"- `paper_commit` `{cb}` and `spec_sha256`. The run id `g4-tasl-20261121-a` is kept: no pilot job and no\n"
        "  server ran under it (the pilot stopped before its start, `G1B_XC_G4_TASL_RESULT_20261122.md`).\n\n"
        "**Supersedes** `g4_t1_tasl_20261122.md`: that note is not used again. It could still launch pilot nodes under\n"
        "the same run id from its checkout (`02abb367`), and a complete attempt made that way would block this note's\n"
        "attempt of that node (`next_attempt`), so the coordinating chat records the supersession when it publishes.\n\n"
        "**Checkouts.** G.4 launches (TASL-7 `serve`, TASL-2 `run-node`) from the published commit that changes the G.4\n"
        "spec to `spec_sha256` (its parent is `paper_commit`), or a docs-only descendant, with the signed note copied\n"
        "from `origin/main` into its `docs/r1/authorizations/`. The G.1b and cross-check launches use their own commits\n"
        "of the same chain (launch table: `docs/r1/reports/tasl_chain_20261122/LAUNCH_TABLE.md`); a checkout is never\n"
        "switched under a running or\n"
        "unsealed job. Signature: copy to `docs/r1/authorizations/g4_t1_tasl_<YYYYMMDD>.md` with a date no other G.4 note\n"
        "uses (not 20261122), `approved: true`, and publish byte-identically on `main`; signed by the coordinating chat\n"
        "under R1-T1-DATA-MANIFEST. Prepared by the Mac-desk agent (Claude), AI-assisted, 22 Nov 2026.\n\n")
    gb = gn[gn_end:]
    old_nodes = re.search(r"^nodes: .*$", gb, re.M).group(0)
    new_nodes = sub1(old_nodes, f"data_manifest_sha256 {OLD['mlgym_fmnist']}",
                     f"data_manifest_sha256 {vals['mlgym_fmnist']} (census erratum, R1-T1-DATA-MANIFEST)", "g4 nodes")
    gb = gb.replace(old_nodes, new_nodes)
    old_launch = re.search(r"^launch: .*$", gb, re.M).group(0)
    gb = gb.replace(old_launch, "launch: decision G4-LB (R1-G1B-TASL-DECISIONS LB A applied to G.4): TASL-7 (serve) and "
                    "TASL-2 (run-node) each from a published checkout (an ancestor of the freshly fetched origin/main) of "
                    "the launch commit of this spec in the R1-T1-DATA-MANIFEST chain, or of a docs-only descendant of it, "
                    "holding this spec, whose code equals paper_commit outside docs/ and the spec file "
                    "(verify_launch_tasl, rows R1-T1-HOST-TASL, R1-TRACKG-G3-EARLY, R1-G1B-TIMEOUT, R1-T1-TASL-ENV; the "
                    "imported modules checked against their reviewed sources), with this note copied from origin/main "
                    "into its docs/r1/authorizations/; main may move on after the signature; a checkout separate from "
                    "the G.1b and cross-check launch checkouts (each launches from its own commit of the chain)")
    gb = fields_replace(gb, {
        "approved": "false", "paper_commit": cb, "spec_sha256": g4_sha,
        "spec": f"{G4}; the signed G.4 note's spec (sha256 60607099d99c549b03b9b961d1a1478fe5bcc306c1daf35630677c5ad7313015) "
                "re-issued under R1-T1-DATA-MANIFEST with the mlgym_fmnist data manifest and paper.commit changed; no "
                "run has used run_id g4-tasl-20261121-a",
        "P4": "PASS — independent reviews: the code unit docs/r1/reviews/T1_TASL_REVIEW_20261121.md (accepted at "
              "021dbc26 with harness c025f89a); the launch binding of g4_tasl.launch and serve and the note, "
              "docs/r1/reviews/G4_TASL_LAUNCH_REVIEW_20261122.md (ACCEPTED at 874e70f6); the re-issued spec and this "
              f"note, {REVIEW}",
    }, "g4 note")
    gb = sub1(gb, "\nP1: ", "\nreissue: re-issues docs/r1/authorizations/g4_t1_tasl_20261122.md under "
              "R1-T1-DATA-MANIFEST (no pilot job or server ran under it)\ncensus_erratum: " + er_text + "\nP1: ",
              "g4 P1")
    write(PROP + "G4_T1_TASL_NOTE_REISSUE_DRAFT_20261122.md", g4_head + gb)
    cc, specs = commit("t1 tasl chain (c): G.4 spec re-issued (mlgym_fmnist data manifest); re-issued note draft",
                       [G4, PROP + "G4_T1_TASL_NOTE_REISSUE_DRAFT_20261122.md"],
                       ["T1-Launch-Run: g4-pilot", f"T1-Launch-Spec: {G4} {g4_sha}", f"T1-Paper-Commit: {cb}"])
    assert specs == [G4], specs
    table.append({"run": "g4-pilot", "nodes": ["mlab_cifar10", "mlgym_fmnist", "mlgym_breakout_minatar"],
                  "run_id": "g4-tasl-20261121-a", "spec": G4, "spec_sha256": g4_sha, "paper_commit": cb,
                  "launch_commit": cc, "note_draft": PROP + "G4_T1_TASL_NOTE_REISSUE_DRAFT_20261122.md"})

    if CFG.get("tail_ref"):
        git("checkout", CFG["tail_ref"], "--", *CFG["tail_paths"])
        commit(CFG["tail_message"], CFG["tail_paths"], [])
    out = {"schema": "t1_tasl_launch_chain/1", "base": base, "values": vals,
           "values_source": CFG.get("values_source"), "erratum": er, "runs": table,
           "ar": "deferred: a later delivery on top of the published (a)-(c)"}
    rel = "docs/r1/reports/tasl_chain_20261122/launch_table.json"
    write(rel, json.dumps(out, indent=1) + "\n")
    md = ["# TASL launch chain — launch table (generated by the chain builder)", "",
          f"Chain base: published `main` `{base}`. Each run launches from its own commit; that commit changes exactly",
          "its one spec file (plus `docs/`), and the spec's `paper.commit` is the commit's parent. A docs-only descendant",
          "of a launch commit may also launch that run (`verify_launch_tasl`). Do not squash or rebase the chain when",
          "publishing it: the launch commits must stay ancestors of `main` with these shas.", "",
          "| run | nodes | run_id | launch commit | paper_commit | spec | spec sha256 | note draft |",
          "|---|---|---|---|---|---|---|---|"]
    for r in table:
        md.append(f"| {r['run']} | {', '.join(r['nodes'])} | `{r['run_id']}` | `{r['launch_commit']}` | "
                  f"`{r['paper_commit']}` | `{r['spec']}` | `{r['spec_sha256']}` | `{r['note_draft']}` |")
    md += ["", f"(d), the AR spec `{AR}`, is not in this delivery: the TASL-2 host check at harness `2d09f9a9` STOPped",
           "(Python 3.12.16 vs 3.12.15). It is a separately built and reviewed delivery: one commit on top of the",
           "published (a)–(c) (paper.commit = its parent), re-binding the re-issued seven-node spec. Until then the AR",
           "spec on `main` binds the first note's spec and refuses to validate (no AR launch from this chain)."]
    md += ["", "Only the launch binding is checked per commit: the test suites of `sweep2/t1_tasl` fail at the intermediate",
           "chain commits (at (a)–(b) the G.4 spec still binds the old G.1b spec, and at (a)–(c) `test_t1_tasl_g1b_ar.py`",
           "still pins the first seven-node spec; the pinned tests are updated",
           "in the tail). Run any preflight tests at the chain tip, not in a launch checkout.",
           "", "Corrected data manifests (R1-T1-DATA-MANIFEST): " +
           ", ".join(f"`{k}` `{v}`" for k, v in vals.items()) + ".",
           "Source: " + (CFG.get("values_source") or "") + ".",
           ("Census erratum record: `" + er["record"] + "` sha256 `" + er["sha256"] + "`.") if er else
           "Census erratum record: pending. The amendment and note 2 carry it in P4 (PENDING, so `g1b_tasl.launch` "
           "refuses them until it is filled); the cross-check and G.4 notes in `census_erratum` (their checks refuse a "
           "`<FILL …>`). If the record's values differ from these, the chain is rebuilt before any launch.", ""]
    write("docs/r1/reports/tasl_chain_20261122/LAUNCH_TABLE.md", "\n".join(md))
    commit("docs(r1): TASL launch chain — launch table (generated)",
           [rel, "docs/r1/reports/tasl_chain_20261122/LAUNCH_TABLE.md"], [])
    out["tip"] = git("rev-parse", "HEAD")
    return out


def cli(argv=None) -> int:
    global CFG, W
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=("build",))
    ap.add_argument("config")
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--table-out")
    a = ap.parse_args(argv)
    CFG = json.loads(Path(a.config).read_text())
    W = Path(a.worktree)
    out = main()
    if a.table_out:
        Path(a.table_out).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(cli())
