#!/bin/bash
# W2 v3 rebuild unit (Track P data rebuild): c3_features/v3 feature table + trackp_prompt/v2 confirmation.
# Runs on deepthought, read-only on the sweep-1 ledgers, into a NEW versioned output directory.
# Authority: author rows R1-W2-3-STOP + R1-B2-REPAIR-SCOPE-ACK (author-ack-w23-20261115 @ b0c8a48d);
# W2_V3_REBUILD_20261115.md §2 (rebuild every Track P feature table/prompt set from this branch).
set -u
set -o pipefail
umask 077
CODE_COMMIT=d8aa956193ba1b24ae0b568a724b841beaa1651e
SWEEP_INDEX=/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/agent_paper_B/results/r1/pilot/C3_sweep_index_20261028T033315Z.json
SWEEP_INDEX_SHA=812468e26c0901a6cb5b3241f44a46fd4d1d2e498d172b76d63b1e91f6d835ab
PAPER_ROOT=/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/agent_paper_B
CHECKOUT=/work/dwong/htcondor_prep_20261114/w2_v3
BASE=/work/dwong/htcondor_prep_20261114/w2_3_rebuild_20261115
PY=python3
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="$BASE/tables/c3_features_v3_${STAMP}"
MANIFEST="$OUT/manifest.json"
EVIDENCE_JSON=/work/dwong/htcondor_prep_20261114/w2/w2_3_check_20261115.json
EVIDENCE_SHA=b11217d041728389cd5b83de0c9685294d312fb77f6246efc99a0945e6ec396e
stop() { echo "STOP: $*" >&2; exit 2; }

[ -d "$CHECKOUT/.git" ] || stop "clean checkout missing: $CHECKOUT"
[ "$(git -C "$CHECKOUT" rev-parse HEAD)" = "$CODE_COMMIT" ] || stop "checkout HEAD is not the reviewed code commit $CODE_COMMIT"
[ -z "$(git -C "$CHECKOUT" status --porcelain)" ] || stop "checkout is dirty"
[ -f "$SWEEP_INDEX" ] || stop "sweep index missing"
[ "$(sha256sum "$SWEEP_INDEX" | awk '{print $1}')" = "$SWEEP_INDEX_SHA" ] || stop "sweep index sha256 mismatch"
[ -d "$PAPER_ROOT" ] || stop "paper root missing"
[ -s "$EVIDENCE_JSON" ] || stop "W2-3 evidence JSON missing"
[ "$(sha256sum "$EVIDENCE_JSON" | awk '{print $1}')" = "$EVIDENCE_SHA" ] || stop "W2-3 evidence sha256 mismatch"
case "$(readlink -f "$OUT")" in *r1_sealed*) stop "refusing r1_sealed output path";; esac
[ ! -e "$OUT" ] || stop "output directory already exists (never overwrite; new versioned dir required)"
mkdir -p "$BASE/tables" || stop "cannot create tables base"
mkdir -m 700 "$OUT" || stop "cannot create the new versioned output directory"

# versions from the reviewed code (recorded in the manifest)
FEAT=$(cd "$CHECKOUT" && PYTHONPATH=. "$PY" -c 'from r1.c3.features import FEATURIZER_VERSION as v; print(v)') || stop "cannot read FEATURIZER_VERSION"
PROMPT=$(cd "$CHECKOUT" && PYTHONPATH=. "$PY" -c 'from r1.c3.train.types import PROMPT_VERSION as v; print(v)') || stop "cannot read PROMPT_VERSION"
[ "$FEAT" = "c3_features/v3" ] || stop "unexpected FEATURIZER_VERSION: $FEAT"
[ "$PROMPT" = "trackp_prompt/v2" ] || stop "unexpected PROMPT_VERSION: $PROMPT"
# prompt-version mixing guard: the branch must define exactly one prompt version and it must be v2
PCOUNT=$(cd "$CHECKOUT" && grep -rhoE "trackp_prompt/v[0-9]+" r1/c3/train/types.py r1/c3/train/serialize.py | sort -u | wc -l)
[ "$PCOUNT" = 1 ] || stop "prompt-version definitions in the code are mixed ($PCOUNT distinct)"

# build-sweep (read-only on the ledgers; D8 guard inside the code checks the pinned index)
( cd "$CHECKOUT" && PYTHONPATH=. "$PY" -m r1.c3.dataset build-sweep \
    --index "$SWEEP_INDEX" --paper-root "$PAPER_ROOT" --out "$OUT" ) > "$OUT/build.stdout" 2> "$OUT/build.stderr"
RC=$?
[ "$RC" -eq 0 ] || stop "build-sweep failed rc=$RC (see $OUT/build.stderr)"
[ -s "$OUT/proposals.jsonl" ] || stop "proposals.jsonl missing"
[ -s "$OUT/configs.json" ] || stop "configs.json missing"
[ -s "$OUT/build.json" ] || stop "build.json missing"

# table manifest: versions + provenance + hashes (author requirement: FEATURIZER_VERSION and prompt version
# in every table manifest; no v1/v2 prompt mixing)
"$PY" - "$OUT" "$MANIFEST" "$CODE_COMMIT" "$SWEEP_INDEX" "$SWEEP_INDEX_SHA" "$EVIDENCE_JSON" "$EVIDENCE_SHA" "$FEAT" "$PROMPT" <<'PY'
import hashlib, json, pathlib, sys
out = pathlib.Path(sys.argv[1]); manifest = pathlib.Path(sys.argv[2])
argv = sys.argv[3:]
code_commit, sweep_index, sweep_sha, ev, ev_sha, feat, prompt = argv
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
build = json.loads((out / "build.json").read_text())
files = {p.name: sha(p) for p in (out / "proposals.jsonl", out / "configs.json", out / "build.json")}
m = {
  "schema": "w2_v3_rebuild_manifest/1",
  "unit": "W2 v3 Track P data rebuild (author rows R1-W2-3-STOP, R1-B2-REPAIR-SCOPE-ACK)",
  "created_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
  "code_commit": code_commit,
  "featurizer_version": feat,
  "prompt_version": prompt,
  "prompt_version_mixing": "none: the reviewed code defines exactly one prompt version (trackp_prompt/v2); this table is a c3 feature table and the recorded prompt version is the one used to build Track P prompt sets from it",
  "sweep_index": {"path": sweep_index, "sha256": sweep_sha},
  "paper_root": str(pathlib.Path(out).parent),
  "w2_3_evidence": {"path": ev, "sha256": ev_sha, "status": json.load(open(ev))["status"], "ledgers": json.load(open(ev))["ledgers"]},
  "table": {"label": build.get("label"), "n_proposals": build.get("n_proposals"), "n_configs": build.get("n_configs"),
            "replay_checks_total": build.get("replay_checks_total"), "sweep_index": build.get("sweep_index"),
            "sources": build.get("sources")},
  "files": files,
  "v1_policy": "new versioned directory; v1 tables are never overwritten (this manifest is the v3 record)",
  "disclosure": "sweep-1 ledgers were produced by the historical v1 code; this rebuild re-derives the feature table with c3_features/v3 from those read-only ledgers and records trackp_prompt/v2 as the prompt version for downstream prompt sets. No v1/v2 prompt mixing in this table.",
}
manifest.write_text(json.dumps(m, indent=1) + "\n")
print(json.dumps({"manifest": str(manifest), "files": files}, indent=1))
PY
[ -s "$MANIFEST" ] || stop "manifest.json missing"
"$PY" - "$OUT" <<'PY' || stop "manifest/table verification failed"
import json, pathlib, sys
out = pathlib.Path(sys.argv[1]); m = json.loads((out/"manifest.json").read_text())
b = json.loads((out/"build.json").read_text())
assert m["featurizer_version"] == "c3_features/v3" and m["prompt_version"] == "trackp_prompt/v2"
assert m["table"]["n_proposals"] == b["n_proposals"] and m["table"]["n_configs"] == b["n_configs"]
assert m["table"]["n_proposals"] > 0
assert set(m["files"]) == {"proposals.jsonl", "configs.json", "build.json"}
assert b.get("sweep_index", {}).get("sha256") == m["sweep_index"]["sha256"]
print("MANIFEST_VERIFY_OK", b["n_proposals"])
PY
( cd "$OUT" && sha256sum proposals.jsonl configs.json build.json manifest.json > SHA256SUMS )
# post-build no-mixing scan (no v1 prompt token in the generated table files)
if grep -RIl "trackp_prompt/v1" "$OUT" >/dev/null 2>&1; then stop "generated table mentions trackp_prompt/v1 (mixing)"; fi
set -C
printf 'REBUILD_OK\nfeaturizer=%s\nprompt=%s\nout=%s\n' "$FEAT" "$PROMPT" "$OUT" > "$OUT/REBUILD_OK" || stop "cannot write REBUILD_OK"
echo "REBUILD_OK $OUT (featurizer=$FEAT prompt=$PROMPT)"
