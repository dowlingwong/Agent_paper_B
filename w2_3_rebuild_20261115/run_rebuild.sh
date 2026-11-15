#!/bin/bash
# W2 v3 rebuild unit (Track P data rebuild): c3_features/v3 feature table + trackp_prompt/v2 confirmation.
# Runs on deepthought, read-only on the sweep-1 ledgers, into a NEW versioned output directory.
# Authority: author rows R1-W2-3-STOP, R1-B2-REPAIR-SCOPE-ACK and R1-SWEEP1-CLASSIFY
# (author-ack-w23-20261115 @ b0c8a48d, PLAN §10); W2_V3_REBUILD_20261115 §2.
# Review: docs/r1/reviews/W2_3_REBUILD_REVIEW_20261115.md (round 1); this revision answers R1-R6/NITs.
set -u
set -o pipefail
umask 077
export PYTHONDONTWRITEBYTECODE=1
CODE_COMMIT=d8aa956193ba1b24ae0b568a724b841beaa1651e
SWEEP_INDEX=/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/agent_paper_B/results/r1/pilot/C3_sweep_index_20261028T033315Z.json
SWEEP_INDEX_SHA=812468e26c0901a6cb5b3241f44a46fd4d1d2e498d172b76d63b1e91f6d835ab
PAPER_ROOT=/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/agent_paper_B
CHECKOUT=/work/dwong/htcondor_prep_20261114/w2_v3
CLASSIFICATION="$PAPER_ROOT/results/r1/evidence/C3_sweep_classification_20261028.json"  # R1-SWEEP1-CLASSIFY (must be inside the paper root)
CLASSIFICATION_SHA=bb6d891c499f0fc187726ed7c8c1e1bce107a029b9106ccb95115989c0c0f1dc
BASE=/work/dwong/htcondor_prep_20261114/w2_3_rebuild_20261115
PY=python3
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="$BASE/tables/c3_features_v3_${STAMP}"
LOGS="$BASE/logs/rebuild_${STAMP}"
MANIFEST="$OUT/manifest.json"
EVIDENCE_JSON=/work/dwong/htcondor_prep_20261114/w2/w2_3_check_20261115.json
EVIDENCE_SHA=b11217d041728389cd5b83de0c9685294d312fb77f6246efc99a0945e6ec396e
EVIDENCE_REPO=docs/r1/reports/w2_3_check_20261115/w2_3_check_20261115.json
BUILD_CMD="python3 -B -m r1.c3.dataset build-sweep --index $PAPER_ROOT/results/r1/pilot/C3_sweep_index_20261028T033315Z.json --paper-root $PAPER_ROOT --classification $CLASSIFICATION --out $OUT"
stop() { echo "STOP: $*" >&2; exit 2; }

[ -d "$CHECKOUT/.git" ] || stop "clean checkout missing: $CHECKOUT"
[ "$(git -C "$CHECKOUT" rev-parse HEAD)" = "$CODE_COMMIT" ] || stop "checkout HEAD is not the reviewed code commit $CODE_COMMIT"
[ -z "$(git -C "$CHECKOUT" status --porcelain)" ] || stop "checkout is dirty"
[ -f "$SWEEP_INDEX" ] || stop "sweep index missing"
[ "$(sha256sum "$SWEEP_INDEX" | awk '{print $1}')" = "$SWEEP_INDEX_SHA" ] || stop "sweep index sha256 mismatch"
[ -d "$PAPER_ROOT" ] || stop "paper root missing"
[ -f "$PAPER_ROOT/docs/r1/PLAN.md" ] || stop "paper-root PLAN.md missing"
grep -q '^| R1-SWEEP1-CLASSIFY ' "$PAPER_ROOT/docs/r1/PLAN.md" || stop "paper-root PLAN has no R1-SWEEP1-CLASSIFY row (author main-merge decision needed)"
grep -q 'C3_sweep_classification_20261028.json' "$PAPER_ROOT/docs/r1/PLAN.md" || stop "paper-root PLAN row does not name the classification sidecar (author main-merge decision needed)"
[ -f "$PAPER_ROOT/docs/r1/authorizations/c3_sweep1_20261027.md" ] || stop "paper-root sweep-1 authorization missing"
[ "$(sha256sum "$PAPER_ROOT/results/r1/pilot/C3_sweep_index_20261028T033315Z.json" 2>/dev/null | awk '{print $1}')" = "$SWEEP_INDEX_SHA" ] || stop "paper-root pinned index missing/mismatched"
[ -f "$CLASSIFICATION" ] || stop "paper-root classification sidecar missing (R1-SWEEP1-CLASSIFY; author main-merge decision needed)"
[ "$(sha256sum "$CLASSIFICATION" | awk '{print $1}')" = "$CLASSIFICATION_SHA" ] || stop "classification sidecar sha256 mismatch"
[ -s "$EVIDENCE_JSON" ] || stop "W2-3 evidence JSON missing"
[ "$(sha256sum "$EVIDENCE_JSON" | awk '{print $1}')" = "$EVIDENCE_SHA" ] || stop "W2-3 evidence sha256 mismatch"
# the W2-3 evidence input is the pinned /work copy; the repo path is recorded in the manifest for provenance
# (the code checkout is pinned to d8aa9561, which predates the evidence commit 03d742cf)
case "$OUT" in *r1_sealed*) stop "refusing r1_sealed output path";; esac
[ ! -e "$OUT" ] || stop "output directory already exists (never overwrite; new versioned dir required)"
# classification mode: the reviewed code creates OUT itself (mkdir exist_ok=False) -> logs go outside OUT
mkdir -p "$BASE/tables" "$BASE/logs" || stop "cannot create the base directories"
mkdir -m 700 "$LOGS" || stop "cannot create the log directory"
PYV=$("$PY" -B -c 'import sys; print(sys.version.split()[0])') || stop "cannot read python version"
NPV=$(cd "$CHECKOUT" && "$PY" -B -c 'import numpy; print(numpy.__version__)') || stop "cannot read numpy version"
DF=$(df -Pk "$BASE" | awk 'NR==2 {print $4}') || stop "df failed"
[ "${DF:-0}" -ge 2097152 ] || stop "less than 2 GiB free on $BASE (df free=${DF:-?} kB)"
FREEZE_KA=$(cd "$CHECKOUT" && PYTHONPATH=. "$PY" -B -c 'from r1.c3.features import FEATURIZER_VERSION as v; print(v)') || stop "cannot read FEATURIZER_VERSION"
PROMPT=$(cd "$CHECKOUT" && PYTHONPATH=. "$PY" -B -c 'from r1.c3.train.types import PROMPT_VERSION as v; print(v)') || stop "cannot read PROMPT_VERSION"
[ "$FREEZE_KA" = "c3_features/v3" ] || stop "unexpected FEATURIZER_VERSION: $FREEZE_KA"
[ "$PROMPT" = "trackp_prompt/v2" ] || stop "unexpected PROMPT_VERSION: $PROMPT"
# prompt-version mixing guard: only the Track P table build path is checked here; the synthetic exam keeps
# the v1 budget line by design (W2-4 open) and is disclosed, not changed.
PCOUNT=$(cd "$CHECKOUT" && grep -rhoE "trackp_prompt/v[0-9]+" r1/c3/train/types.py r1/c3/train/serialize.py r1/c3/train/__init__.py 2>/dev/null | sort -u | wc -l)
[ "$PCOUNT" = 1 ] || stop "prompt-version definitions in the Track P prompt path are mixed ($PCOUNT distinct)"

# the single data-producing step (read-only on the ledgers; the code's D8 guard + refuse_sealed apply)
( cd "$CHECKOUT" && PYTHONPATH=. "$PY" -B -m r1.c3.dataset build-sweep \
    --index "$PAPER_ROOT/results/r1/pilot/C3_sweep_index_20261028T033315Z.json" --paper-root "$PAPER_ROOT" --classification "$CLASSIFICATION" --out "$OUT" ) \
    > "$LOGS/build.stdout" 2> "$LOGS/build.stderr"
RC=$?
[ "$RC" -eq 0 ] || stop "build-sweep failed rc=$RC (logs preserved in $LOGS)"
[ -s "$OUT/proposals.jsonl" ] || stop "proposals.jsonl missing"
[ -s "$OUT/configs.json" ] || stop "configs.json missing"
[ -s "$OUT/build.json" ] || stop "build.json missing"

"$PY" -B - "$OUT" "$MANIFEST" "$PAPER_ROOT" "$CODE_COMMIT" "$SWEEP_INDEX" "$SWEEP_INDEX_SHA" \
  "$CLASSIFICATION" "$CLASSIFICATION_SHA" "$EVIDENCE_JSON" "$EVIDENCE_SHA" "$EVIDENCE_REPO" \
  "$FREEZE_KA" "$PROMPT" "$PYV" "$NPV" "$DF" "$BUILD_CMD" "$LOGS" <<'PY'
import hashlib, json, pathlib, sys
out, manifest, paper_root, code_commit, sweep_index, sweep_sha, class_path, class_sha, ev, ev_sha, ev_repo, \
    feat, prompt, pyv, npv, df_free, build_cmd, logs = sys.argv[1:]
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
build = json.loads((pathlib.Path(out) / "build.json").read_text())
files = {p.name: sha(p) for p in (pathlib.Path(out) / "proposals.jsonl", pathlib.Path(out) / "configs.json",
                                 pathlib.Path(out) / "build.json")}
evj = json.load(open(ev))
m = {
  "schema": "w2_v3_rebuild_manifest/1",
  "unit": "W2 v3 Track P data rebuild (author rows R1-W2-3-STOP, R1-B2-REPAIR-SCOPE-ACK, R1-SWEEP1-CLASSIFY)",
  "created_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
  "code_commit": code_commit,
  "featurizer_version": feat,
  "prompt_version": prompt,
  "prompt_version_mixing": ("none in this Track P feature-table build path: the reviewed code defines one "
                            "trackp_prompt/v2 version there; this table records c3_features/v3 + trackp_prompt/v2. "
                            "r1/c3/train/exam_synthetic.py intentionally keeps the trackp_prompt/v1 budget line "
                            "(synthetic exam; W2-4 open) and is not part of this table build."),
  "budget_line_change": ("W2-1: the Track P prompt budget line changed from trackp_prompt/v1 (trial number and "
                         "trial total) to trackp_prompt/v2 (worker runs used k of W=20, no trial total); the "
                         "synthetic exam trackp_e0/v1 keeps the v1 line (W2-4 open)."),
  "sweep_index": {"path": sweep_index, "sha256": sweep_sha},
  "paper_root": paper_root,
  "output_parent": str(pathlib.Path(out).parent),
  "classification": {"path": class_path, "sha256": class_sha, "row": "R1-SWEEP1-CLASSIFY (sweep-1 is the EVIDENCE batch)"},
  "w2_3_evidence": {"path": ev, "sha256": ev_sha, "repo_path": ev_repo, "status": evj["status"],
                    "ledgers": evj["ledgers"], "runs_total": evj["runs_total"],
                    "ledgers_differing": evj["ledgers_differing"],
                    "stop_rule_note": "the author adopted W2-3 as a STOP (R1-W2-3-STOP); the JSON's own stop_rule string predates the adoption"},
  "table": {"label": build.get("label"), "n_proposals": build.get("n_proposals"), "n_configs": build.get("n_configs"),
            "replay_checks_total": build.get("replay_checks_total"), "sweep_index": build.get("sweep_index"),
            "sources": build.get("sources")},
  "environment": {"python": pyv, "numpy": npv, "df_free_kb": int(df_free)},
  "exact_build_command": build_cmd,
  "files": files,
  "v1_policy": "new versioned directory; v1 tables are never overwritten (this manifest is the v3 record)",
  "disclosure": ("sweep-1 ledgers were produced by the historical v1 code; this rebuild re-derives the feature "
                 "table with c3_features/v3 from those read-only ledgers under the R1-SWEEP1-CLASSIFY sidecar "
                 "and records trackp_prompt/v2 for downstream Track P prompt sets. No v1/v2 prompt mixing in "
                 "this table; the synthetic exam's retained v1 budget line (W2-4) is disclosed."),
  "logs": logs,
}
pathlib.Path(manifest).write_text(json.dumps(m, indent=1) + "\n")
print(json.dumps({"manifest": manifest, "files": files}, indent=1))
PY
[ -s "$MANIFEST" ] || stop "manifest.json missing"
"$PY" -B - "$OUT" <<'PY' || stop "manifest/table verification failed"
import json, pathlib, sys
out = pathlib.Path(sys.argv[1]); m = json.loads((out/"manifest.json").read_text()); b = json.loads((out/"build.json").read_text())
assert m["featurizer_version"] == "c3_features/v3" and m["prompt_version"] == "trackp_prompt/v2"
assert m["table"]["label"] == "EVIDENCE", m["table"]["label"]
assert m["table"]["n_proposals"] == b["n_proposals"] and m["table"]["n_configs"] == b["n_configs"]
ev = json.loads(pathlib.Path(m["w2_3_evidence"]["path"]).read_text())
assert m["table"]["replay_checks_total"] == ev["ledgers"] * ev["runs_total"] == 288 * 20, m["table"]["replay_checks_total"]
assert m["classification"]["sha256"] == "bb6d891c499f0fc187726ed7c8c1e1bce107a029b9106ccb95115989c0c0f1dc"
assert b.get("sweep_index", {}).get("sha256") == m["sweep_index"]["sha256"]
assert set(m["files"]) == {"proposals.jsonl", "configs.json", "build.json"}
assert (out / "build.json").stat().st_size > 0
if b.get("table_sha256") is not None: assert set(b["table_sha256"]) == {"proposals.jsonl", "configs.json"}
print("MANIFEST_VERIFY_OK", b["n_proposals"], b["replay_checks_total"])
PY
( cd "$OUT" && sha256sum proposals.jsonl configs.json build.json manifest.json > SHA256SUMS ) || stop "cannot write SHA256SUMS"
# R3 substantiation: the build must not have changed any tracked file in the code checkout
[ -z "$(git -C "$CHECKOUT" status --porcelain)" ] || stop "the build changed tracked files in the code checkout"
( cd "$OUT" && sha256sum -c SHA256SUMS >/dev/null ) || stop "SHA256SUMS self-check failed"
# post-build no-mixing scan: only the table files (the manifest disclosure legitimately names v1)
if grep -l "trackp_prompt/v1" "$OUT/proposals.jsonl" "$OUT/configs.json" "$OUT/build.json" >/dev/null 2>&1; then
  stop "generated table mentions trackp_prompt/v1 (mixing)"
fi
set -C
printf 'REBUILD_OK\nfeaturizer=%s\nprompt=%s\nlabel=EVIDENCE\nout=%s\n' "$FREEZE_KA" "$PROMPT" "$OUT" > "$OUT/REBUILD_OK" || stop "cannot write REBUILD_OK"
echo "REBUILD_OK $OUT (featurizer=$FREEZE_KA prompt=$PROMPT label=EVIDENCE logs=$LOGS)"
