"""Build (d), the second delivery of the TASL launch chain (R1-T1-DATA-MANIFEST): the AR spec. ENGINEERING_ONLY.

Usage:
  python sweep2/t1_tasl/build_launch_chain_ar.py build <build_config_ar.json> --worktree <clean worktree>

On top of the delivered (a)–(c) (``base``: the chain tip with its review record), it writes one launch commit (d) that
changes exactly one spec outside docs/, ``sweep2/t1_tasl/g1b_tasl_ar_spec.json``, with ``paper.commit`` = its parent:
- ``seven_node_spec.sha256``: the seven-node spec re-issued in (a);
- ``env_decision.authority``: R1-G1B-AR-ENV (option A of decision AR-ENV), with its env comment; R1-G1B-AR-PY amends it
  only on the host (the venv's interpreter symlinks), so the spec's environment fields stay unchanged (Python 3.12.15);
- ``hosts.TASL-2.isolation_host_check.sha256``: the TASL-2 host-check binding record at harness ``2d09f9a9`` (PASS),
  whose bytes are checked against ``host_check.source_ref`` (the experiment agent's branch, or origin/main once
  published) before anything is written;
and the third-note draft bound to that spec (paper_commit, spec_sha256, env_row, P2, P3, P4, P7 filled; approved: false).
Then the tail (``tail_paths`` from ``tail_ref``) and the launch table with the AR run appended. Author and committer
dates are pinned, so the same config gives the same shas. **Never run it again once the AR run has launched.**
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_launch_chain as B  # noqa: E402

AR = B.AR
NOTE3 = B.PROP + "G1B_AR_T1_TASL_NOTE3_DRAFT_20261122.md"
TABLE_JSON = "docs/r1/reports/tasl_chain_20261122/launch_table.json"
TABLE_MD = "docs/r1/reports/tasl_chain_20261122/LAUNCH_TABLE.md"
FIRST_SEVEN_SHA = "060aac91ba452a69e4e898b66b92ebd5bfc0887c2933cfd2e438d93d17ecb465"
ENV_TODO = ('"authority": "TODO: the PLAN row admitting the AR census environment ar-cond7a (Python 3.12.15) beside '
            'R1-T1-TASL-ENV\'s torch312/jax312 (decision AR-ENV)"')
ENV_COMMENT_TODO = ('"env_python_comment": "AR-ENV option A (recommended in the third note draft): the AR census venv '
                    'in place, unchanged; option B moves it to <base>/envs/ar-cond7a (only this path changes)"')
HC_TODO = ('"sha256": "TODO: sha256 of the binding record on published main (procedure '
           'docs/r1/reports/g1b_ar_20261122/TASL2_AR_PIN_HOST_CHECK_PROCEDURE_20261122.md)"')
PROCEDURE = "docs/r1/reports/g1b_ar_20261122/TASL2_AR_PIN_HOST_CHECK_PROCEDURE_20261122.md"
REVIEW_HC = "docs/r1/reviews/TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_REVIEW_R4_20261122.md"


def main() -> dict:
    cfg = B.CFG
    base, hc = cfg["base"], cfg["host_check"]
    if B.git("status", "--porcelain"):
        raise SystemExit("build-ar: the worktree must be clean (it resets the branch)")
    if not re.fullmatch(r"[0-9a-f]{64}", hc["sha256"]) or not hc["record"].startswith("docs/r1/reports/"):
        raise SystemExit("build-ar: host_check.record must be a docs/r1/reports/ path and sha256 64 hex")
    blob = subprocess.run(["git", "-C", str(B.W), "show", f"{hc['source_ref']}:{hc['record']}"], capture_output=True,
                          env=B._env())
    if blob.returncode != 0 or hashlib.sha256(blob.stdout).hexdigest() != hc["sha256"]:
        raise SystemExit(f"build-ar: {hc['record']} at {hc['source_ref']} is missing or not sha256 {hc['sha256']}")
    fields = {m.group(1): m.group(2) for m in re.finditer(r"^(host_check_[a-z_]+):\s*(.*?)\s*$",
                                                           blob.stdout.decode(), re.M)}
    if (fields.get("host_check_host"), fields.get("host_check_verdict"), fields.get("host_check_items")) != \
            ("TASL-2", "PASS", "1-7 PASS"):
        raise SystemExit(f"build-ar: the record is not a PASS for TASL-2: {fields}")
    B.git("checkout", "-q", "-f", "-B", cfg["branch"], base)
    table = json.loads(B.read(TABLE_JSON))
    if not str(table.get("ar", "")).startswith("deferred") or any(r["run"] == "g1b-ar" for r in table["runs"]):
        raise SystemExit("build-ar: the base's launch table must have (d) deferred")
    g1b = next(r for r in table["runs"] if r["spec"] == "sweep2/t1_tasl/g1b_tasl_spec.json")
    g1b_sha = B.sha("sweep2/t1_tasl/g1b_tasl_spec.json")
    if g1b_sha != g1b["spec_sha256"]:
        raise SystemExit("build-ar: the seven-node spec at the base is not (a)'s")
    if fields.get("host_check_harness_commit") != json.loads(B.read(AR))["harness"]["commit"]:
        raise SystemExit("build-ar: the record names another harness commit than the AR spec's")

    # ------------------------------------------------------------------ (d) the AR spec
    t = B.read(AR)
    t = B.sub1(t, f'"sha256": "{FIRST_SEVEN_SHA}"', f'"sha256": "{g1b_sha}"', "ar seven sha")
    t = B.sub1(t, ENV_TODO, '"authority": "R1-G1B-AR-ENV (option A of decision AR-ENV: ar-cond7a in place, read-only, '
                            'freeze 11def6ad…; interpreter 3.12.15 by R1-G1B-AR-PY)"', "ar env")
    t = B.sub1(t, ENV_COMMENT_TODO, '"env_python_comment": "R1-G1B-AR-ENV (AR-ENV option A): the AR census venv in '
                                    'place, read-only, for this node only; R1-G1B-AR-PY re-pointed its interpreter '
                                    'symlinks to uv\'s versioned CPython 3.12.15 (the only change to the venv)"',
               "ar env comment")
    t = B.sub1(t, f'"record": "{hc["record"]}",\n    {HC_TODO}', f'"record": "{hc["record"]}",\n    "sha256": '
                                                               f'"{hc["sha256"]}"', "ar host check")
    B.write(AR, t)
    parent = B.git("rev-parse", "HEAD")
    B.set_paper_commit(AR, parent)
    ar_sha = B.sha(AR)
    note3 = B.fields_replace(B.read(NOTE3), {
        "paper_commit": parent,
        "spec_sha256": ar_sha,
        "spec": "sweep2/t1_tasl/g1b_tasl_ar_spec.json (schema g1b_tasl_ar_job/v1); binds the seven-node spec "
                f"sweep2/t1_tasl/g1b_tasl_spec.json by sha256 {g1b_sha} (the spec re-issued under R1-T1-DATA-MANIFEST, "
                "run g1b-tasl-20261121-b) only to keep the two runs apart and to add up R1-G1B-CAP",
        "env_row": "R1-G1B-AR-ENV",
        "P2": f"PASS — TASL-2 harness-isolation host check at harness 2d09f9a9: {hc['record']} sha256 {hc['sha256']} "
              f"(procedure {PROCEDURE}; rerun after the interpreter fix of R1-G1B-AR-PY; independently reviewed, "
              f"{REVIEW_HC} ACCEPTED for this sha256); its sha256 is in the spec",
        "P3": "PASS — independent review of harness 2d09f9a9 (mac-trackg-t1-ar-20261121): "
              "docs/r1/reviews/TRACKG_T1_AR_HARNESS_REVIEW_20261122.md (ACCEPTED, minors only; on main)",
        "P4": "PASS — independent review of the autoresearch-only spec support, the spec and this note: "
              "docs/r1/reviews/G1B_AR_SPEC_SUPPORT_REVIEW_20261122.md (accepted at 6617d8cb, confirmed at 740c48f3; on "
              f"main); the spec's re-binding in the launch chain: {B.REVIEW}",
        "P7": "PASS — R1-G1B-AR-ENV, amended by R1-G1B-AR-PY: the AR census environment ar-cond7a in place, read-only "
              "(Python 3.12.15 through uv's versioned CPython, freeze 11def6ad…), for this node only, beside "
              "R1-T1-TASL-ENV's torch312/jax312 (Python 3.12.16); option A of decision AR-ENV",
    }, "note3")
    B.write(NOTE3, note3)
    cd, specs = B.commit(
        "t1 tasl chain (d): AR spec (TASL-2 host check at 2d09f9a9 PASS); binds the re-issued seven-node spec; "
        "env_decision R1-G1B-AR-ENV (R1-G1B-AR-PY); third note bound",
        [AR, NOTE3], ["T1-Launch-Run: g1b-ar", f"T1-Launch-Spec: {AR} {ar_sha}", f"T1-Paper-Commit: {parent}"])
    if specs != [AR]:
        raise SystemExit(f"build-ar: (d) changes {specs}")

    # ------------------------------------------------------------------ the tail, then the launch table
    if cfg.get("tail_ref"):
        B.git("checkout", cfg["tail_ref"], "--", *cfg["tail_paths"])
        B.commit(cfg["tail_message"], cfg["tail_paths"], [])
    run = {"run": "g1b-ar", "nodes": ["autoresearch_fixedtokens"], "run_id": "g1b-ar-tasl-20261122-a",
           "spec": AR, "spec_sha256": ar_sha, "paper_commit": parent, "launch_commit": cd, "note_draft": NOTE3}
    table["runs"].append(run)
    table["ar"] = {"delivered": "second delivery (d)", "host_check": {k: hc[k] for k in ("record", "sha256")},
                   "env_rows": ["R1-G1B-AR-ENV", "R1-G1B-AR-PY"]}
    B.write(TABLE_JSON, json.dumps(table, indent=1) + "\n")
    md = B.read(TABLE_MD)
    cut = md.find("\n(d), the AR spec")
    md = (md[:cut] if cut >= 0 else md.rstrip("\n")) + "\n\n" + "\n".join([
        "## (d), second delivery",
        "",
        "| run | nodes | launch commit | paper_commit | spec | spec sha256 | note draft |",
        "|---|---|---|---|---|---|---|",
        f"| g1b-ar | autoresearch_fixedtokens (run `g1b-ar-tasl-20261122-a`) | `{cd}` | `{parent}` | `{AR}` | "
        f"`{ar_sha}` | `{NOTE3}` |",
        "",
        f"The TASL-2 host check at harness `2d09f9a9`: `{hc['record']}` sha256 `{hc['sha256']}` (PASS; published on",
        "`main` before or with the chain). Environment: R1-G1B-AR-ENV, amended by R1-G1B-AR-PY (Python 3.12.15). (d)'s",
        "parent is the delivered (a)–(c) tip with its review record; between (d) and the table commit, the tail updates the",
        "tests and adds this builder. At (d) itself `test_t1_tasl_chain.py` and `test_t1_tasl_g1b_ar.py` still expect",
        "(d) deferred; the tail updates them.",
    ]) + "\n"
    B.write(TABLE_MD, md)
    B.commit("docs(r1): TASL launch chain — launch table: (d), the AR run, appended", [TABLE_JSON, TABLE_MD], [])
    table["tip"] = B.git("rev-parse", "HEAD")
    return table


def cli(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=("build",))
    ap.add_argument("config")
    ap.add_argument("--worktree", required=True)
    a = ap.parse_args(argv)
    B.CFG = json.loads(Path(a.config).read_text())
    B.W = Path(a.worktree)
    print(json.dumps(main(), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(cli())
