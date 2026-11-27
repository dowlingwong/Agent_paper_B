"""G.5 audit hosts beyond the TASL pair (sweep2/t1_tasl/g5_audit_hosts.py and its uses in g5_tasl, g5_job, g5_seal):
the signed TASL-pair behaviour unchanged without an addendum, the addendum spec and note, the per-node admission
(cross-host PASS, host check, hardware class), the card-share check, the Ada cross-check spec, and an audit chunk on an
addendum host end to end (claim on TASL-2, run, registration, final log, seal check). Synthetic only: no GPU, no host,
no label is read.
"""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sweep2" / "t1_tasl"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import g5_tasl as S  # noqa: E402
import g5_audit_hosts as AH  # noqa: E402
import g5_job as J  # noqa: E402
import g1b_tasl as G  # noqa: E402
import g5_pin_check as PC  # noqa: E402
import test_t1_g5_tasl as TT  # noqa: E402
import test_t1_g5_job as TJ  # noqa: E402

world, jspec, two, keys = TJ.world, TJ.jspec, TJ.two, TT.keys          # the fixtures of the G.5 tests, reused

SPEC_PATH = ROOT / "sweep2" / "t1_tasl" / "g5_tasl_spec.json"
SPEC = json.loads(SPEC_PATH.read_text())
# The signed configuration as on main at this unit's base (6684e840): the spec's bytes and its rendered key lines.
SIGNED_SPEC_SHA = "16b39b475e5ccccd9143de06b0a69996e5274d73033521d5cac8c1db0470627f"
KEY_LINES_SHA = "74f93fa574ab5e4d3e1b115ae5dfa115bff25c8a93793264ee85c8b36d95fe8f"
KEY_LINES_SHA_GPUH_B = "1c892d6eb24c563e4c5d8eb3ddc508dc8c9a5f25af2192404c1e85ffb9c236e6"
ADA_XC_REL = "sweep2/t1_tasl/g5_audit_host_xc_ada_spec.json"
ADA_MODEL = "NVIDIA RTX 6000 Ada Generation"
UUIDA = "GPU-0a1b2c3d-0000-4000-8000-00000000ada0"
DRIVERA = "550.54.15"
HOSTCHECK_A = "docs/r1/reports/ada_20261201/ADA_ISOLATION_HOST_CHECK_20261201.md"
CLASS_ROW_TEXT = ("| R1-G5-AUDIT-HOST-CLASS | **For the G.5 audit chunks of a G5-7 node, a card of NVIDIA RTX 6000 "
                  "Ada Generation is one hardware class with the RTX 4090 pair once the node has a cross-host PASS** "
                  "(synthetic) |")
ROWS = {"R1-HOST-FREE": "| R1-HOST-FREE | (synthetic) further hosts join it through an addendum note; a node's results "
                        "need a cross-host PASS |",
        "R1-G5-SIGNATURE": "| R1-G5-SIGNATURE | (synthetic) further hosts and the expansion nodes join by addendum "
                           "notes |",
        "R1-CARD-SHARE": "| R1-CARD-SHARE | (synthetic) New launchers check free memory, not an empty card. |"}
COPY_FILES = ["sweep2/t1_tasl/g1b_tasl_spec.json", "sweep2/t1_tasl/g1b_tasl_ar_spec.json", S.XC3_SPEC_REL,
              AH.AR_REFERENCE_RECORD, ADA_XC_REL] + [AH.XC2_STEP1.format(node=n) for n in S.X_NODES]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def stop(match, fn, *a, **kw):
    with pytest.raises(S.Stop, match=match):
        fn(*a, **kw)


# =============================================================================================== synthetic world
def fake_repo(tmp_path, monkeypatch, *, name="Ada", model=ADA_MODEL):
    """A checkout copy with the files the cross-check spec is checked against, and that spec (its host renamed and of
    ``model`` for a same-model test); ``g5_audit_hosts`` reads this checkout."""
    repo = tmp_path / "repo"
    xc3 = json.loads((ROOT / S.XC3_SPEC_REL).read_text())
    for rel in COPY_FILES + list(xc3["verdicts"].values()):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, repo / rel)
    xc = json.loads((ROOT / ADA_XC_REL).read_text())
    xc["host"].update(name=name, gpu_model=model, gpu_uuid=UUIDA, driver=DRIVERA)
    xc["verdicts"] = {n: v.replace("_Ada_", f"_{name}_") for n, v in xc["verdicts"].items()}
    rel = ADA_XC_REL if (name, model) == ("Ada", ADA_MODEL) else "sweep2/t1_tasl/xc_host_test.json"
    (repo / rel).write_text(json.dumps(xc, indent=1) + "\n")
    monkeypatch.setattr(AH, "REPO_ROOT", repo)
    return repo, xc, rel


def verdict(xc, node_, **kw) -> bytes:
    node = node_
    ref, host = xc["references"][node], xc["host"]["name"]
    g = xc["g1b_specs"][ref["family"]]
    v = {"schema": "g1b_tasl_crosscheck_verdict/1", "label": "ENGINEERING_ONLY", "node": node, "mode": "short",
         "verdict": "PASS", "reason": None, "complete": True, "rule": "R1-HOST-FREE",
         "harness_commit": g["harness_commit"], "g1b_spec_sha256": g["sha256"], "g1b_run_id": g["run_id"],
         "crosscheck_run_id": xc["run_id"],
         "sides": {"TASL-2": {**{k: ref[k] for k in AH.SIDE_FIELDS}, "deterministic": True},
                   host: {"run_id": f"{xc['run_id']}-{host}", "spec_sha256": "3" * 64,
                          "job_record_sha256": "4" * 64, "attempt": 1, "deterministic": True,
                          "gpu_uuid": xc["host"]["gpu_uuid"], "driver": xc["host"]["driver"]}}}
    v.update(kw)
    return json.dumps(v, sort_keys=True).encode()


def host_check_bytes(hostname="ucrtasl") -> bytes:
    return (f"host_check_host: {hostname}\nhost_check_harness_commit: {PC.PIN_SEVEN}\nhost_check_items: 1-7 PASS\n"
            "host_check_verdict: PASS\n").encode()


def make_addendum(spec, spec_path, xc, xc_rel, *, host="Ada-g0", model=ADA_MODEL, admitted=("mlab_imdb",),
                  uuid=UUIDA, lease="~/r1_locks/ada_gpu0.lock"):
    adm = {}
    for n in S.SEVEN:
        if n in admitted:
            raw = verdict(xc, n)
            adm[n] = [{"record": xc["verdicts"][n], "sha256": sha(raw), "mode": "short",
                       "crosscheck_run_id": xc["run_id"]}]
        else:
            adm[n] = S.xc_pending(n)
    entry = {"host": host, "hostname": "ucrtasl", "gpu_model": model, "gpu_uuid": uuid, "driver": DRIVERA,
             "hardware_class": "same_gpu_model" if model == spec["gpu_model"] else "cross_model_row",
             "lease": lease, "card_share": {"rule": "R1-CARD-SHARE", "min_free_mib": 24576},
             "families": ["G5-7"], "harness_dir": spec["harness_families"]["G5-7"]["harness_dir"],
             "base": "/data1/dowling/r1_tracks/t1_tasl", "runs_root": spec["worker"]["runs_root"],
             "uv": "/data1/dowling/.local/bin/uv", "cpus": "0-7", "node_cpus": {"mlgym_houseprice": "16-23"},
             "env_python": {"torch312": "/data1/dowling/envs/torch312/bin/python",
                            "jax312": "/data1/dowling/envs/jax312/bin/python"},
             "extra_env": {"XLA_FLAGS": "--xla_gpu_cuda_data_dir=/usr/local/cuda-12.2"},
             "node_extra_env": {"mlgym_houseprice": {"AR_HOUSEPRICE_TRAIN_CSV": "/data1/dowling/hp/train.csv"}},
             "isolation_host_check": {"record": HOSTCHECK_A, "sha256": sha(host_check_bytes())}, "c12": None,
             "crosscheck": {"spec": xc_rel, "sha256": sha((AH.REPO_ROOT / xc_rel).read_bytes()),
                            "host": xc["host"]["name"]},
             "admission": adm}
    return {"schema": AH.ADDENDUM_SCHEMA, "label": "EVIDENCE", "comment": "synthetic",
            "authority": "R1-HOST-FREE (3); R1-G5-SIGNATURE (3)", "run_id": spec["run_id"],
            "g5_spec": {"path": "sweep2/t1_tasl/g5_tasl_spec.json", "sha256": G.L._sha_file(Path(spec_path))},
            "hosts": [entry]}


def put_main(m, xc, add, *, class_row=True):
    """What main holds for the addendum's admitted nodes: the host check record, the verdicts, the rows."""
    m[HOSTCHECK_A] = host_check_bytes()
    for h in add["hosts"]:
        for n, e in h["admission"].items():
            if isinstance(e, list):
                m[e[0]["record"]] = verdict(xc, n)
    plan = (m.get("docs/r1/PLAN.md") or b"# PLAN\n").decode()
    extra = dict(ROWS, **({"R1-G5-AUDIT-HOST-CLASS": CLASS_ROW_TEXT} if class_row else {}))
    plan += "".join(v + "\n" for k, v in extra.items() if f"| {k} |" not in plan)
    m["docs/r1/PLAN.md"] = plan.encode()


def write_json(path: Path, obj) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1) + "\n")
    return path


# =============================================================================================== backward compatibility
def test_signed_spec_and_its_key_lines_are_unchanged():
    """The signed configuration: the spec's bytes and every key line it renders are the ones at the base; the list of
    audit hosts without an addendum is TASL-7 alone, read from tasl7_audits."""
    assert sha(SPEC_PATH.read_bytes()) == SIGNED_SPEC_SHA
    assert sha(json.dumps(S.note_lines(SPEC), sort_keys=True).encode()) == KEY_LINES_SHA
    assert sha(json.dumps(S.note_lines(S.apply_options(SPEC, {"G5-TASL-GPUH": "B"})),
                          sort_keys=True).encode()) == KEY_LINES_SHA_GPUH_B
    hosts = AH.audit_hosts(SPEC)
    assert [h["host"] for h in hosts] == ["TASL-7"] and AH.audit_hosts(SPEC, None) == hosts
    t = SPEC["tasl7_audits"]
    assert (hosts[0]["hostname"], hosts[0]["gpu_uuid"], hosts[0]["lease"], hosts[0]["gpu_model"]) == \
        (t["hostname"], t["gpu_uuid"], t["lease"], SPEC["gpu_model"])
    assert S.JOB_HOSTS == ("TASL-2", "TASL-7") and S.AUDIT_HOST == "TASL-7"


def test_switch_on_the_tasl_pair_takes_no_addendum(tmp_path, keys):
    s, sp, note, m = TT.ready(tmp_path)
    calls = []
    TT.go(sp, note, m, node="mlab_cifar10", job="audits-wave1", host="TASL-7", chunk=1, calls=calls)
    ctx = calls[0][2]
    assert "admission" not in ctx and "audit_host" not in ctx and "addendum" not in ctx
    assert ctx["crosshost_pass"]["source"] == "spec"
    TT.go(sp, note, m, calls=calls)                                       # TASL-2: as before
    stop("host must be one of", TT.go, sp, note, m, node="mlab_cifar10", job="audits-wave1", host="Ada-g0", chunk=1)
    for host in ("TASL-7", "TASL-2"):
        stop("a job on the TASL pair takes neither", TT.go, sp, note, m, node="mlab_cifar10", job="audits-wave1",
             host=host, chunk=1, addendum=tmp_path / "a.json", addendum_note=tmp_path / "n.md")
    stop("both", TT.go, sp, note, m, node="mlab_cifar10", job="audits-wave1", host="Ada-g0", chunk=1,
         addendum=tmp_path / "a.json")


def test_tasl7_claim_keeps_its_signed_fields(two):
    TJ.first_wave(two)
    c = TJ.claim(two, "mlab_imdb", 1, 1)
    keys_ = set(c) - {"claim", "sha256"}
    assert keys_ == {"schema", "label", "run_id", "node", "job", "wave", "chunk", "chunks", "K", "host",
                     "plan_index_sha256", "plan_json_sha256", "plan_tar_sha256", "spec_sha256", "gpu_hours_at_claim",
                     "registered_attempts_at_claim", "crosshost_pass", "utc", "rule"}
    assert c["host"] == "TASL-7" and c["rule"] == S.TWO_CARDS_ROW
    stop("a TASL-7 claim takes none", J.claim_chunk, two["spec"], two["sp"], "mlab_imdb", 1, 2,
         addendum=Path("x.json"), **TJ.mkw(two))


# =============================================================================================== the addendum spec
def test_addendum_validates_and_fails_closed(tmp_path, monkeypatch):
    repo, xc, xc_rel = fake_repo(tmp_path, monkeypatch)
    sp = tmp_path / "g5.json"
    sp.write_bytes(SPEC_PATH.read_bytes())
    add = make_addendum(SPEC, sp, xc, xc_rel)
    assert AH.validate_addendum(SPEC, sp, add, launch=True) == {"hosts": ["Ada-g0"]}
    assert [h["host"] for h in AH.audit_hosts(SPEC, add)] == ["TASL-7", "Ada-g0"]
    assert AH.audit_hosts(SPEC, add)[1]["card_check"].startswith("free memory at least 24576")

    def bad(match, edit, *, launch=True):
        a = copy.deepcopy(add)
        edit(a)
        stop(match, AH.validate_addendum, SPEC, sp, a, launch=launch)
    bad("must name the signed G.5 spec and its sha256", lambda a: a["g5_spec"].update(sha256="0" * 64))
    bad("run_id must be the G.5 run's", lambda a: a.update(run_id="other"))
    bad("must cite R1-HOST-FREE", lambda a: a.update(authority="R1-G5-SIGNATURE"))
    bad("carry exactly", lambda a: a.update(extra=1))
    bad("simple name other than", lambda a: a["hosts"][0].update(host="TASL-7"))
    bad("on a host of the TASL pair", lambda a: a["hosts"][0].update(hostname="TASL-2"))
    bad("families must be", lambda a: a["hosts"][0].update(families=["G5-7", "G5-AR"]))
    bad("hardware_class must be 'cross_model_row'", lambda a: a["hosts"][0].update(hardware_class="same_gpu_model"))
    bad("gpu_model must be", lambda a: a["hosts"][0].update(gpu_model="PENDING: survey"))
    bad("harness_dir must be the G5-7 checkout", lambda a: a["hosts"][0].update(harness_dir="/x"))
    bad("runs_root must be the table's", lambda a: a["hosts"][0].update(runs_root="/x"))
    bad("card_share must be", lambda a: a["hosts"][0]["card_share"].update(min_free_mib=0))
    bad("card_share must be", lambda a: a["hosts"][0]["card_share"].update(rule="none"))
    bad("node_cpus must give exactly", lambda a: a["hosts"][0].update(node_cpus={}))
    bad("must have the size of its G.1b set", lambda a: a["hosts"][0]["node_cpus"].update(mlgym_houseprice="0-3"))
    bad("env_python must map exactly", lambda a: a["hosts"][0]["env_python"].pop("jax312"))
    bad("gpu_uuid must be filled", lambda a: a["hosts"][0].update(gpu_uuid="PENDING: survey"))
    bad("isolation_host_check.record must be filled",
        lambda a: a["hosts"][0]["isolation_host_check"].update(record="PENDING: x"))
    bad("admission must name exactly the seven", lambda a: a["hosts"][0]["admission"].update({S.AR: "x"}))
    bad("must be exactly one short PASS record",
        lambda a: a["hosts"][0]["admission"].update(mlab_imdb=[{**a["hosts"][0]["admission"]["mlab_imdb"][0],
                                                                "mode": "xc"}]))
    bad("must be exactly one short PASS record",
        lambda a: a["hosts"][0]["admission"]["mlab_imdb"][0].update(
            record="docs/r1/reports/x/G5_AUDIT_HOST_XC_VERDICT_Ada_mlab_cifar10_20261127.json"))
    bad("differs from its sha256", lambda a: a["hosts"][0]["crosscheck"].update(sha256="0" * 64))
    bad("is not this host's", lambda a: a["hosts"][0].update(hostname="otherhost"))
    bad("is not the driver 550.54.15 its cross-check PASS was measured under",
        lambda a: a["hosts"][0].update(driver="545.23.08"))                                     # m2
    two_cards = copy.deepcopy(add)
    two_cards["hosts"].append(dict(copy.deepcopy(add["hosts"][0]), host="Ada-g1"))
    stop("is named by two audit hosts", AH.validate_addendum, SPEC, sp, two_cards)
    two_cards["hosts"][1]["gpu_uuid"] = UUIDA[:-1] + "1"
    stop("share the lease", AH.validate_addendum, SPEC, sp, two_cards)
    two_cards["hosts"][1]["lease"] = "~/r1_locks/ada_gpu1.lock"
    assert AH.validate_addendum(SPEC, sp, two_cards)["hosts"] == ["Ada-g0", "Ada-g1"]
    xc_open = json.loads((repo / xc_rel).read_text())                 # m2: the measured card must be named at launch
    xc_open["host"]["driver"] = "PENDING: survey"
    (repo / xc_rel).write_text(json.dumps(xc_open, indent=1) + "\n")
    unbound = copy.deepcopy(add)
    unbound["hosts"][0]["crosscheck"]["sha256"] = sha((repo / xc_rel).read_bytes())
    stop("hostname, gpu_uuid and driver must be filled", AH.validate_addendum, SPEC, sp, unbound, launch=True)
    AH.validate_addendum(SPEC, sp, unbound, launch=False)
    (repo / xc_rel).write_text(json.dumps(xc, indent=1) + "\n")
    draft = copy.deepcopy(add)                       # placeholders pass only outside launch
    draft["hosts"][0].update(gpu_uuid="PENDING: survey", driver="PENDING: survey")
    draft["hosts"][0]["env_python"]["torch312"] = "PENDING: path"
    AH.validate_addendum(SPEC, sp, draft, launch=False)
    stop("must be filled", AH.validate_addendum, SPEC, sp, draft, launch=True)
    same = make_addendum(SPEC, sp, xc, xc_rel, model=SPEC["gpu_model"])
    stop("is not this host's", AH.validate_addendum, SPEC, sp, same)       # the Ada spec's card is not a 4090


# =============================================================================================== the addendum note
def note_bytes(spec, sp, add, add_path, g5_note, *, approved="true", edit=None):
    lines = {"approved": approved, "g5_note": f"docs/r1/authorizations/{Path(g5_note).name}",
             **AH.note_lines(spec, sp, add, add_path), "addendum_spec_sha256": G.L._sha_file(add_path)}
    if edit:
        edit(lines)
    return ("# G.5 audit-hosts addendum (synthetic)\n\n" + "\n".join(f"{k}: {v}" for k, v in lines.items())
            + "\n").encode()


def test_addendum_note_binds_spec_note_and_rows(tmp_path, monkeypatch):
    repo, xc, xc_rel = fake_repo(tmp_path, monkeypatch)
    s0 = copy.deepcopy(SPEC)
    s0["run_id"] = "c3_t1_labels_20261201"
    sp = tmp_path / "g5.json"
    sp.write_text(json.dumps(s0))
    add = make_addendum(s0, sp, xc, xc_rel)
    add_path = write_json(repo / "sweep2" / "t1_tasl" / "g5_audit_hosts_addendum.json", add)
    lines = AH.note_lines(s0, sp, add, add_path)
    assert lines["addendum_spec"] == "sweep2/t1_tasl/g5_audit_hosts_addendum.json"
    assert lines["audit_hosts"] == f"TASL-7 (the signed note's tasl7_audits, unchanged); Ada-g0 ({ADA_MODEL})"
    assert "no audit chunk runs here unless R1-G5-AUDIT-HOST-CLASS is on main" in lines["audit_host_Ada_g0"]
    assert "mlab_cifar10: PENDING (runs on the TASL pair only)" in lines["audit_host_Ada_g0"]
    assert f"(measured on this card, driver {DRIVERA})" in lines["audit_host_Ada_g0"]
    g1 = copy.deepcopy(add)
    g1["hosts"][0].update(host="Ada-g1", gpu_uuid=UUIDA[:-1] + "1", lease="~/r1_locks/ada_gpu1.lock")
    assert f"measured on Ada's card {UUIDA} and covering this card of the same host, GPU model and driver" in \
        AH.note_lines(s0, sp, g1, add_path)["audit_host_Ada_g1"]                     # per-host coverage, stated (m2)
    assert lines["addendum_cuda_ipc"].startswith("The author accepts, for the G.5 audit chunks on Ada-g0")
    assert "sampled for other compute processes before the job, before the engine and after the engine" in \
        lines["addendum_scope"]                                                                         # m4
    c12 = copy.deepcopy(s0)
    c12["key_values"]["cuda_ipc"]["mode"] = "c12"
    assert AH.note_lines(c12, sp, add, add_path)["addendum_cuda_ipc"] == \
        "no C12 record for Ada-g0: no G.5 audit chunk runs there"
    d = tmp_path / "docs" / "r1" / "authorizations"
    d.mkdir(parents=True)
    g5_note = d / f"{s0['run_id']}.md"
    note = d / "c3_t1_labels_audit_hosts_20261205.md"
    m = TT.Main()
    put_main(m, xc, add)
    note.write_bytes(note_bytes(s0, sp, add, add_path, g5_note, approved="false"))
    AH.check_note(note, add_path, sp, g5_note, spec=s0, add=add, on_main=m.on_main, read_main=m.read, draft=True)
    stop("approved: true and be committed", AH.check_note, note, add_path, sp, g5_note, spec=s0, add=add,
         on_main=m.on_main, read_main=m.read)
    note.write_bytes(note_bytes(s0, sp, add, add_path, g5_note))
    stop("approved: true and be committed", AH.check_note, note, add_path, sp, g5_note, spec=s0, add=add,
         on_main=m.on_main, read_main=m.read)                          # not on main
    m[f"docs/r1/authorizations/{note.name}"] = note.read_bytes()
    AH.check_note(note, add_path, sp, g5_note, spec=s0, add=add, on_main=m.on_main, read_main=m.read)
    stop("g5_note must be", AH.check_note, note, add_path, sp, d / "c3_t1_labels_20990101.md", spec=s0, add=add,
         on_main=m.on_main, read_main=m.read)
    for key in lines:                                # every key line is enforced
        note.write_bytes(note_bytes(s0, sp, add, add_path, g5_note, edit=lambda x, k=key: x.update({k: x[k] + " x"})))
        m[f"docs/r1/authorizations/{note.name}"] = note.read_bytes()
        stop(f"key lines differ.*{key}", AH.check_note, note, add_path, sp, g5_note, spec=s0, add=add,
             on_main=m.on_main, read_main=m.read)
    note.write_bytes(note_bytes(s0, sp, add, add_path, g5_note))
    m[f"docs/r1/authorizations/{note.name}"] = note.read_bytes()
    m["docs/r1/PLAN.md"] = b"# PLAN\n"                # the rows the addendum rests on must be on main
    stop("R1-HOST-FREE must exist", AH.check_note, note, add_path, sp, g5_note, spec=s0, add=add,
         on_main=m.on_main, read_main=m.read)
    bad_name = d / "c3_t1_labels_hosts_20261205.md"
    bad_name.write_bytes(note.read_bytes())
    stop("c3_t1_labels_audit_hosts_", AH.check_note, bad_name, add_path, sp, g5_note, spec=s0, add=add,
         on_main=m.on_main, read_main=m.read)


# =============================================================================================== admission per node
def test_admission_per_node(tmp_path, monkeypatch):
    repo, xc, xc_rel = fake_repo(tmp_path, monkeypatch)
    sp = tmp_path / "g5.json"
    sp.write_bytes(SPEC_PATH.read_bytes())
    add = make_addendum(SPEC, sp, xc, xc_rel, admitted=("mlab_imdb", "mlab_cifar10", "mlgym_houseprice"))
    e = add["hosts"][0]
    m = TT.Main()
    put_main(m, xc, add)
    out = AH.check_admission(SPEC, e, "mlab_imdb", m.read, m.ls)
    assert out["hardware_class"]["class"] == "cross_model_row" and out["host_check"]["record"] == HOSTCHECK_A
    assert out["crosshost_pass"]["records"][0]["record"] == xc["verdicts"]["mlab_imdb"]
    assert AH.check_admission(SPEC, e, "mlab_cifar10", m.read, m.ls)["crosshost_pass"]["source"] == "addendum"
    AH.check_admission(SPEC, e, "mlgym_houseprice", m.read, m.ls)
    # R1-HOST-FREE (2)(a): another GPU model only with the author's row naming it
    m["docs/r1/PLAN.md"] = m["docs/r1/PLAN.md"].replace(CLASS_ROW_TEXT.encode() + b"\n", b"")
    stop("one hardware class .*R1-G5-AUDIT-HOST-CLASS", AH.check_admission, SPEC, e, "mlab_imdb", m.read, m.ls)
    m["docs/r1/PLAN.md"] += CLASS_ROW_TEXT.replace(ADA_MODEL, "NVIDIA L40S").encode() + b"\n"
    stop("does not name", AH.check_admission, SPEC, e, "mlab_imdb", m.read, m.ls)
    m["docs/r1/PLAN.md"] = m["docs/r1/PLAN.md"].replace(
        CLASS_ROW_TEXT.replace(ADA_MODEL, "NVIDIA L40S").encode() + b"\n", b"")
    weak = (f"| R1-G5-AUDIT-HOST-CLASS | not one hardware class: {ADA_MODEL} stays out, whatever its cross-host PASS "
            f"(synthetic) |")                          # names every term, but not as the row's lead sentence (m3)
    m["docs/r1/PLAN.md"] += weak.encode() + b"\n"
    stop("does not open with", AH.check_admission, SPEC, e, "mlab_imdb", m.read, m.ls)
    m["docs/r1/PLAN.md"] = m["docs/r1/PLAN.md"].replace(weak.encode() + b"\n", b"")
    put_main(m, xc, add)
    AH.check_admission(SPEC, e, "mlab_imdb", m.read, m.ls)
    # the TASL pair's nodes and autoresearch
    stop("audits stay on TASL-2", AH.check_admission, SPEC, e, S.AR, m.read, m.ls)
    stop("no short cross-check PASS is listed", AH.check_admission, SPEC, e, "mlgym_fmnist", m.read, m.ls)
    # the verdict: on main at its sha256, a PASS of this node against its declared reference, the one file
    rel = xc["verdicts"]["mlab_imdb"]
    good = m[rel]
    for kw in (dict(verdict="STOP", reason="cross_host_mismatch"), dict(node="mlab_cifar10"), dict(mode="xc"),
               dict(complete=False), dict(rule="R1-G5-AUDIT-TWO-CARDS"), dict(crosscheck_run_id="x")):
        raw = verdict(xc, "mlab_imdb", **kw)
        m[rel] = raw
        e2 = copy.deepcopy(e)
        e2["admission"]["mlab_imdb"][0]["sha256"] = sha(raw)
        stop("is not a short cross-check PASS", AH.check_admission, SPEC, e2, "mlab_imdb", m.read, m.ls)
    for side_edit in ({"driver": "535.309.01"}, {"gpu_uuid": UUIDA[:-1] + "9"}, {"driver": None}):   # m2
        v = json.loads(good)
        v["sides"]["Ada"].update(side_edit)
        if side_edit.get("driver", 1) is None:
            v["sides"]["Ada"].pop("driver")
        m[rel] = json.dumps(v, sort_keys=True).encode()
        e2 = copy.deepcopy(e)
        e2["admission"]["mlab_imdb"][0]["sha256"] = sha(m[rel])
        stop("sides", AH.check_admission, SPEC, e2, "mlab_imdb", m.read, m.ls)
    v = json.loads(good)
    v["sides"]["TASL-2"]["job_record_sha256"] = "9" * 64            # not the declared sealed TASL-2 attempt
    m[rel] = json.dumps(v, sort_keys=True).encode()
    e2 = copy.deepcopy(e)
    e2["admission"]["mlab_imdb"][0]["sha256"] = sha(m[rel])
    stop("sides", AH.check_admission, SPEC, e2, "mlab_imdb", m.read, m.ls)
    m[rel] = good + b" "
    stop("is not on published main with sha256", AH.check_admission, SPEC, e, "mlab_imdb", m.read, m.ls)
    m[rel] = good
    m[rel.replace("20261127", "20261128")] = good                   # a second verdict file of the node and host
    stop("2 cross-check verdicts of mlab_imdb on Ada", AH.check_admission, SPEC, e, "mlab_imdb", m.read, m.ls)
    m.pop(rel.replace("20261127", "20261128"))
    m.pop(HOSTCHECK_A)
    stop("not on published main", AH.check_admission, SPEC, e, "mlab_imdb", m.read, m.ls)
    m[HOSTCHECK_A] = host_check_bytes()
    e3 = copy.deepcopy(e)
    e3["node_extra_env"]["mlgym_houseprice"]["AR_HOUSEPRICE_TRAIN_CSV"] = "PENDING: path"
    stop("environment on Ada-g0 is not filled", AH.check_admission, SPEC, e3, "mlgym_houseprice", m.read, m.ls)
    stop("not built under G5-TASL-GPUH B", AH.check_admission, S.apply_options(SPEC, {"G5-TASL-GPUH": "B"}), e,
         "mlab_imdb", m.read, m.ls)
    c12 = copy.deepcopy(SPEC)
    c12["key_values"]["cuda_ipc"]["mode"] = "c12"
    stop("needs its C12 PASS record", AH.check_admission, c12, e, "mlab_imdb", m.read, m.ls)
    m["docs/r1/reports/x/C12_ADA.md"] = b"c12_host: ucrtasl\nc12_verdict: PASS\n"
    e4 = dict(e, c12={"record": "docs/r1/reports/x/C12_ADA.md", "sha256": sha(m["docs/r1/reports/x/C12_ADA.md"]),
                      "review": None})
    assert AH.check_admission(c12, e4, "mlab_imdb", m.read, m.ls)["cuda_ipc"]["host"] == "Ada-g0"


def test_same_gpu_model_host_needs_no_class_row(tmp_path, monkeypatch):
    repo, xc, xc_rel = fake_repo(tmp_path, monkeypatch, name="Box", model=SPEC["gpu_model"])
    sp = tmp_path / "g5.json"
    sp.write_bytes(SPEC_PATH.read_bytes())
    add = make_addendum(SPEC, sp, xc, xc_rel, host="Box-g0", model=SPEC["gpu_model"])
    AH.validate_addendum(SPEC, sp, add, launch=True)
    m = TT.Main()
    put_main(m, xc, add, class_row=False)
    out = AH.check_admission(SPEC, add["hosts"][0], "mlab_imdb", m.read, m.ls)
    assert out["hardware_class"] == {"class": "same_gpu_model", "gpu_model": SPEC["gpu_model"]}


# =============================================================================================== the Ada cross-check spec
def test_ada_crosscheck_spec_is_valid_and_bound_to_its_references():
    xc = json.loads((ROOT / ADA_XC_REL).read_text())
    proj = AH.check_host_xc_spec(xc)
    assert xc["nodes"] == list(S.T1_NODES) and xc["host"]["gpu_model"] == ADA_MODEL
    assert xc["status"] == AH.XC_STATUS                               # a draft: not launched
    assert proj["estimate"]["gpu_hours"] == 2.94 and proj["sensitivity"]["gpu_hours"] == 3.535
    assert proj["sensitivity"]["gpu_hours"] <= xc["caps"]["max_gpu_hours"]
    assert all(v["runs"] == 10 for v in proj["estimate"]["per_node"].values())
    refs = xc["references"]
    assert refs["mlab_cifar10"]["run_id"] == "g1b-tasl-20261121-b-xc2-TASL-2"            # xc2's TASL-2 attempt
    assert refs["mlgym_fmnist"]["attempt"] == 3                                           # xc3's declared attempt
    assert refs[S.AR]["run_id"] == "g1b-ar-tasl-20261122-a" and refs[S.AR]["family"] == "G5-AR"

    def bad(match, edit):
        x = copy.deepcopy(xc)
        edit(x)
        stop(match, AH.check_host_xc_spec, x)
    bad("differs from its recorded sealed TASL-2 attempt",
        lambda x: x["references"]["mlab_imdb"].update(job_record_sha256="0" * 64))
    bad("differs from its recorded sealed TASL-2 attempt", lambda x: x["references"]["mlgym_fmnist"].update(attempt=1))
    bad("is not the sealed G.1b-AR TASL-2 attempt",
        lambda x: x["references"][S.AR].update(job_record_sha256="0" * 64))
    bad("source must name a file", lambda x: x["references"]["mlab_cifar10"]["source"].update(sha256="0" * 64))
    bad("nodes must be the eight", lambda x: x.update(nodes=list(S.SEVEN)))
    bad("verdicts.mlab_imdb must be", lambda x: x["verdicts"].update(mlab_imdb="docs/r1/reports/x/V_mlab_imdb.json"))
    bad("exceeds caps.max_gpu_hours", lambda x: x["caps"].update(max_gpu_hours=3.0))
    bad("g1b_specs.G5-7 must be", lambda x: x["g1b_specs"]["G5-7"].update(sha256="0" * 64))
    bad("status as drafted", lambda x: x.update(status="launched"))
    bad("rule is R1-HOST-FREE", lambda x: x.update(rule="R1-G5-AUDIT-TWO-CARDS"))


def test_cli_host_xc_spec_and_addendum_lines(tmp_path, monkeypatch, capsys):
    assert S.main(["host-xc-spec", str(ROOT / ADA_XC_REL)]) == 0
    assert json.loads(capsys.readouterr().out)["sensitivity"]["gpu_hours"] == 3.535
    repo, xc, xc_rel = fake_repo(tmp_path, monkeypatch)
    sp = tmp_path / "g5.json"
    sp.write_bytes(SPEC_PATH.read_bytes())
    add_path = write_json(repo / "add.json", make_addendum(SPEC, sp, xc, xc_rel))
    assert S.main(["addendum-lines", str(sp), "--addendum", str(add_path)]) == 0
    out = capsys.readouterr().out
    assert out.startswith("approved: false\ng5_note: docs/r1/authorizations/")
    assert "audit_host_Ada_g0: ucrtasl" in out and f"addendum_spec_sha256: {G.L._sha_file(add_path)}" in out
    assert S.main(["cpus", str(sp), "--node", "mlgym_houseprice", "--host", "Ada-g0", "--addendum", str(add_path)]) == 0
    assert capsys.readouterr().out.strip() == "16-23"
    assert S.main(["cpus", str(sp), "--node", "mlab_imdb", "--host", "Ada-g0", "--addendum", str(add_path)]) == 0
    assert capsys.readouterr().out.strip() == "0-7"
    assert S.main(["cpus", str(sp), "--node", "mlab_imdb", "--host", "TASL-7"]) == 0       # TASL-7: as before
    assert capsys.readouterr().out.strip() == SPEC["tasl7_audits"]["cpus"]
    assert S.main(["cpus", str(sp), "--node", "mlab_imdb", "--host", "Ada-g0"]) != 0
    assert S.main(["cpus", str(sp), "--node", "mlab_imdb", "--host", "TASL-7", "--addendum", str(add_path)]) != 0


# =============================================================================================== card share
def test_card_share_check_records_others_and_needs_free_memory():
    e = {"host": "Ada-g0", "card_share": {"rule": "R1-CARD-SHARE", "min_free_mib": 24576}}
    state = {"free": 40000, "apps": ""}

    def smi(argv, **kw):
        if "--query-compute-apps" in " ".join(argv):
            return subprocess.CompletedProcess(argv, 0, state["apps"], "")
        return subprocess.CompletedProcess(argv, 0, f"{UUIDA}, {state['free']}\n", "")
    out = AH.card_share_check(e, UUIDA, "before the job", smi)
    assert (out["other_processes"], out["other_memory_mib"], out["free_mib"]) == (0, 0, 40000)
    state["apps"] = f"{UUIDA}, 4242, 8000 MiB\n{UUIDA}, 4343, 2000 MiB\nGPU-other, 1, 5 MiB\n"
    out = AH.card_share_check(e, UUIDA, "before the job", smi)
    assert (out["other_processes"], out["other_memory_mib"]) == (2, 10000) and AH.shared([out])
    assert "pid" not in json.dumps(out)                                  # count and memory only
    stop("other compute process", AH.card_share_check, e, UUIDA, "before the job", smi, refuse_shared=True)
    state["free"] = 1000
    stop("below the 24576 MiB", AH.card_share_check, e, UUIDA, "before the job", smi)
    assert AH.card_share_check(e, None, "x")["device"] == "cpu"


# =============================================================================================== the job on an addendum host
@pytest.fixture
def ada(two, tmp_path, monkeypatch):
    """``two`` plus an Ada card admitted by an addendum (the class row on main), its runs tree, its nvidia-smi."""
    repo, xc, xc_rel = fake_repo(tmp_path, monkeypatch)
    s, sp = two["spec"], two["sp"]
    add = make_addendum(s, sp, xc, xc_rel, admitted=("mlab_imdb",))
    add_path = write_json(tmp_path / "addendum.json", add)
    put_main(two["main"], xc, add)
    two["roots"]["Ada-g0"] = tmp_path / "ada" / s["run_id"]
    state = {"model": ADA_MODEL, "free": 40000, "apps": "", "driver": DRIVERA}

    def smi(argv, **kw):
        j = " ".join(argv)
        if "--query-compute-apps" in j:
            return subprocess.CompletedProcess(argv, 0, state["apps"], "")
        if "memory.free" in j:
            return subprocess.CompletedProcess(argv, 0, f"{UUIDA}, {state['free']}\n", "")
        return subprocess.CompletedProcess(argv, 0, f"{UUIDA}, {state['model']}, {state['driver']}, 49140\n", "")
    return dict(two, add=add, add_path=add_path, xc=xc, smi_ada=smi, ada_state=state)


def claim_ada(w, node="mlab_imdb", wave=1, chunk=1):
    return J.claim_chunk(w["spec"], w["sp"], node, wave, chunk, host="Ada-g0", addendum=w["add_path"], **TJ.mkw(w))


def copy_to(w, host, node, wave, chunk):
    src, dst = w["roots"]["TASL-2"], w["roots"][host]
    rels = [J.claim_path(w["spec"], node, wave, chunk).relative_to(src)]
    rels += [p.relative_to(src) for p in (src / node / f"audits-wave{wave}").glob("plan*")]
    for rel in rels:
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        (dst / rel).write_bytes((src / rel).read_bytes())


def run_ada(w, chunk, engine, node="mlab_imdb", job="audits-wave1"):
    entry = w["add"]["hosts"][0]
    adm = AH.check_admission(w["spec"], entry, node, w["main"].read, w["main"].ls)
    ctx = {"K": 10, "K_row": None, "host": "Ada-g0", "chunk": chunk, "crosshost_pass": adm["crosshost_pass"],
           "audit_host": entry, "addendum": {"sha256": G.L._sha_file(w["add_path"])}}
    return J.run_job(w["sp"], node, job, ctx, smi=w["smi_ada"], engine=engine, setup=w["setup"],
                     get=TJ.Server(up=True), git=w["git"])


def back_from(w, tmp_path, host, node, job, chunk, attempt, tag=""):
    w["on"](host)
    src = J.job_dir(w["spec"], node, job, chunk) / f"attempt-{attempt}"
    stage = tmp_path / f"staged_{host}{tag}" / f"attempt-{attempt}"
    stage.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, stage)
    log = tmp_path / f"staged_{host}{tag}" / f"access_log_{attempt}.jsonl"
    log.write_bytes((J.run_root(w["spec"]) / "_access_log.jsonl").read_bytes())
    w["on"]("TASL-2")
    return stage, log


def test_addendum_host_claim_run_register_final_seal(ada, tmp_path):
    w = ada
    s, sp = w["spec"], w["sp"]
    eng, chunks = TJ.first_wave(w)
    stop("a claim is made for TASL-7 or for an audit host of an addendum", J.claim_chunk, s, sp, "mlab_imdb", 1, 1,
         host="Ada-g0", **TJ.mkw(w))
    stop("no short cross-check PASS is listed", claim_ada, w, node="mlab_cifar10")
    c = claim_ada(w)
    assert (c["host"], c["gpu_model"], c["hardware_class"]["class"]) == ("Ada-g0", ADA_MODEL, "cross_model_row")
    assert c["addendum_sha256"] == G.L._sha_file(w["add_path"]) and c["rule"] == "R1-HOST-FREE (3)"
    stop("one Ada-g0 chunk at a time", claim_ada, w, chunk=2)
    assert TJ.claim(w, "mlab_imdb", 1, 2)["host"] == "TASL-7"           # one open claim per host
    copy_to(w, "Ada-g0", "mlab_imdb", 1, 1)
    w["on"]("Ada-g0")
    rec = run_ada(w, 1, eng)
    assert rec["stop"] is None and rec["worker_host"] == "Ada-g0" and rec["gpu"]["name"] == ADA_MODEL
    assert rec["audit_host"]["gpu_model"] == ADA_MODEL and "server_stopped" not in rec      # no proposer here
    assert [c_["other_processes"] for c_ in rec["foreign_checks"]] == [0, 0, 0]
    assert rec["foreign_checks"][-1]["enforced"] is False
    assert rec["lease"]["lease"].endswith("r1_locks/ada_gpu0.lock")
    assert rec["crosshost_pass"]["records"][0]["record"] == w["xc"]["verdicts"]["mlab_imdb"]
    w["on"]("TASL-2")
    stage, log = back_from(w, tmp_path, "Ada-g0", "mlab_imdb", "audits-wave1", 1, 1)
    stop("a claim is made for TASL-7 or for an audit host", J.register_attempt, s, sp, stage, "mlab_imdb", 1, 1, log,
         **TJ.mkw(w))                                                    # the addendum is needed
    reg = J.register_attempt(s, sp, stage, "mlab_imdb", 1, 1, log, addendum=w["add_path"], **TJ.mkw(w))
    assert reg["host"] == "Ada-g0" and reg["crosshost_pass"]["same_as_claim"] is True
    assert (J.run_root(s) / "_remote" / "Ada-g0" / "access_log-1.jsonl").is_file()
    assert not (J.run_root(s) / "_remote" / "TASL-7").exists()
    assert J.complete_attempt(J.job_dir(s, "mlab_imdb", "audits-wave1", 1))[0]["worker_host"] == "Ada-g0"
    # the TASL-7 claim (chunk 2) runs and registers as before
    copy_to(w, "TASL-7", "mlab_imdb", 1, 2)
    w["on"]("TASL-7")
    TJ.run7(w, "mlab_imdb", "audits-wave1", 2, eng)
    w["on"]("TASL-2")
    stage7, log7 = TJ.back(w, tmp_path, "mlab_imdb", "audits-wave1", 2, 1)
    assert TJ.register(w, stage7, log7, chunk=2)["host"] == "TASL-7"
    while not J.audits_done(s, "mlab_imdb", 1):
        assert TJ.run(w, "mlab_imdb", "audits-wave1", eng)["chunk"] not in (1, 2)
    last = J.complete_attempt(J.job_dir(s, "mlab_imdb", "audits-wave1", chunks - 1))[1]
    assert last["wave_e5"]["audited"] == 41                 # E5 over every chunk, both remote ones included
    # each host's own final registration; the seal check reads both
    stop("Ada-g0 ran audit chunks but its access log has no final registration", J.SE.check_remote_final, s)
    fa = J.finalize_remote(s, sp, log, hostname=TJ.HOST2, host="Ada-g0")
    assert fa["host"] == "Ada-g0" and fa["registered_attempts"] == 1
    stop("TASL-7 ran audit chunks but its access log has no final registration", J.SE.check_remote_final, s)
    f7 = J.finalize_remote(s, sp, log7, hostname=TJ.HOST2)
    assert f7["registered_attempts"] == 1
    res = J.SE.check_remote_final(s)
    assert sorted(res["hosts"]) == ["Ada-g0", "TASL-7"] and res["hosts"]["Ada-g0"]["utc"] == fa["utc"]
    stop("Ada-g0's access log has its final registration", claim_ada, w, chunk=3)


def test_addendum_host_job_refusals_and_shared_card(ada, tmp_path):
    w = ada
    s = w["spec"]
    eng, _ = TJ.first_wave(w)
    claim_ada(w)
    copy_to(w, "Ada-g0", "mlab_imdb", 1, 1)
    w["on"]("Ada-g0")
    w["ada_state"]["model"] = "NVIDIA GeForce RTX 4090"                 # not the addendum's GPU model
    stop("not NVIDIA RTX 6000 Ada Generation", run_ada, w, 1, eng)
    w["ada_state"]["model"] = ADA_MODEL
    w["ada_state"]["driver"] = "535.309.01"
    stop("runs driver 535.309.01", run_ada, w, 1, eng)
    w["ada_state"]["driver"] = DRIVERA
    w["ada_state"]["free"] = 2000                                       # R1-CARD-SHARE: not enough free memory
    stop("below the 24576 MiB", run_ada, w, 1, eng)
    w["ada_state"]["free"] = 40000
    stop("only audit chunks run on Ada-g0", run_ada, w, 1, eng, job="campaigns-wave1")
    with G.gpu_lease(w["add"]["hosts"][0]["lease"]):                    # our other job holds this card's lease
        stop("held by another job", run_ada, w, 1, eng)
    stop("audits stay on TASL-2", J.worker_shim, s, S.node_entry(s, S.AR),
         {"host": "Ada-g0", "audit_host": w["add"]["hosts"][0]})
    shim, node = J.worker_shim(s, S.node_entry(s, "mlgym_houseprice"),
                               {"host": "Ada-g0", "audit_host": w["add"]["hosts"][0]})
    assert node["cpus"] == "16-23" and shim["hosts"]["Ada-g0"]["extra_env"]["AR_HOUSEPRICE_TRAIN_CSV"] == \
        "/data1/dowling/hp/train.csv"
    # a card shared at the start: refused before an attempt is taken (m4)
    w["ada_state"]["apps"] = f"{UUIDA}, 4242, 8000 MiB\n"
    stop("other compute process.*before the job", run_ada, w, 1, eng)
    assert not (J.job_dir(s, "mlab_imdb", "audits-wave1", 1) / "attempt-1").exists()
    w["ada_state"]["apps"] = ""

    class Arrives:                   # another process arrives while the engine runs (seen only after the engine)
        def __init__(self, inner):
            self.inner = inner

        def __call__(self, argv, **kw):
            w["ada_state"]["apps"] = f"{UUIDA}, 4242, 8000 MiB\n"
            return self.inner(argv, **kw)
    # another compute process on the card during the attempt: an infrastructure failure, repeated (R1-NO-TIMEOUT (2))
    with pytest.raises(S.Stop, match="another compute process was on the card"):
        run_ada(w, 1, Arrives(eng))
    a1 = J.job_dir(s, "mlab_imdb", "audits-wave1", 1) / "attempt-1" / "job_record.json"
    r1 = json.loads(a1.read_text())
    assert r1["stop_class"] == "infrastructure" and [c["other_processes"] for c in r1["foreign_checks"]] == [0, 0, 1]
    assert r1["foreign_checks"][-1]["other_memory_mib"] == 8000
    w["on"]("TASL-2")
    stage, log = back_from(w, tmp_path, "Ada-g0", "mlab_imdb", "audits-wave1", 1, 1)
    J.register_attempt(s, w["sp"], stage, "mlab_imdb", 1, 1, log, addendum=w["add_path"], **TJ.mkw(w))
    assert [c["chunk"] for c in J.open_claims(s)] == [1]                # the claim stays open: attempt 2 follows
    w["on"]("Ada-g0")
    w["ada_state"]["apps"] = ""
    assert run_ada(w, 1, eng)["attempt"] == 2
    # a registration under another addendum is refused
    w["on"]("TASL-2")
    stage2, log2 = back_from(w, tmp_path, "Ada-g0", "mlab_imdb", "audits-wave1", 1, 2, tag="b")
    other = copy.deepcopy(w["add"])
    other["comment"] = "another addendum"
    other_path = write_json(tmp_path / "other_addendum.json", other)
    stop("the claim names another addendum spec", J.register_attempt, s, w["sp"], stage2, "mlab_imdb", 1, 1, log2,
         addendum=other_path, **TJ.mkw(w))
    J.register_attempt(s, w["sp"], stage2, "mlab_imdb", 1, 1, log2, addendum=w["add_path"], **TJ.mkw(w))
    assert J.open_claims(s) == []


def test_addendum_host_claim_needs_the_class_row(ada):
    w = ada
    TJ.first_wave(w)
    m = w["main"]
    m["docs/r1/PLAN.md"] = m["docs/r1/PLAN.md"].replace(CLASS_ROW_TEXT.encode() + b"\n", b"")
    stop("one hardware class", claim_ada, w)
    assert not list((J.run_root(w["spec"]) / "_remote").glob("claims/**/*.json"))


# =============================================================================================== the switch on an addendum host
def test_switch_admits_an_addendum_host_audit_chunk(tmp_path, monkeypatch, keys):
    (tmp_path / "w").mkdir()
    s, sp, note, m = TT.ready(tmp_path / "w")
    repo, xc, xc_rel = fake_repo(tmp_path, monkeypatch)
    add = make_addendum(s, sp, xc, xc_rel, admitted=("mlab_cifar10",))
    add_path = write_json(repo / "sweep2" / "t1_tasl" / "g5_audit_hosts_addendum.json", add)
    put_main(m, xc, add)
    anote = note.parent / "c3_t1_labels_audit_hosts_20261205.md"
    anote.write_bytes(note_bytes(s, sp, add, add_path, note))
    m[f"docs/r1/authorizations/{anote.name}"] = anote.read_bytes()
    t = dict(node="mlab_cifar10", job="audits-wave1", host="Ada-g0", chunk=1, addendum=add_path, addendum_note=anote)
    calls = []
    TT.go(sp, note, m, calls=calls, **t)
    ctx = calls[0][2]
    assert ctx["host"] == "Ada-g0" and ctx["audit_host"]["gpu_model"] == ADA_MODEL
    assert ctx["crosshost_pass"]["source"] == "addendum" and ctx["host_check"]["Ada-g0"]["record"] == HOSTCHECK_A
    assert ctx["addendum"]["sha256"] == G.L._sha_file(add_path) and ctx["pilot_basis"]["main_only"] is True
    stop("only audit chunks run on Ada-g0", TT.go, sp, note, m, **dict(t, job="campaigns-wave1"))
    stop("names its claimed chunk", TT.go, sp, note, m, **dict(t, chunk=None))
    stop("audits stay on TASL-2", TT.go, sp, note, m, **dict(t, node=S.AR))
    stop("no short cross-check PASS is listed", TT.go, sp, note, m, **dict(t, node="mlab_imdb"))
    stop("is not an audit host of the addendum", TT.go, sp, note, m, **dict(t, host="Ada-g7"))
    m["docs/r1/PLAN.md"] = m["docs/r1/PLAN.md"].replace(CLASS_ROW_TEXT.encode() + b"\n", b"")
    stop("one hardware class", TT.go, sp, note, m, **t)
    put_main(m, xc, add)
    m.pop(f"docs/r1/authorizations/{anote.name}")
    stop("addendum note must read approved: true", TT.go, sp, note, m, **t)
    m[f"docs/r1/authorizations/{anote.name}"] = anote.read_bytes()
    bad = copy.deepcopy(add)
    bad["g5_spec"]["sha256"] = "0" * 64
    write_json(add_path, bad)
    stop("name the signed G.5 spec", TT.go, sp, note, m, **t)


def test_shared_attempt_reclassification_covers_baseline_failed():
    """m1 of the review: on a shared addendum card every budget- or memory-related outcome becomes an infrastructure
    failure, the audit engine's STOP 6 baseline_failed (a baseline OOM beside another process) included; STOP 2, STOP 10
    and the left-processes STOP 9 keep their class; an infrastructure STOP stays as it is."""
    b6, cls6 = J.engine_stop({"stop": "x", "stop_kind": "baseline_failed"}, "audit")
    assert b6.startswith("STOP 6") and cls6 == "node"                 # the audit engine can emit it (generic mapping)
    for stop_, cls in ((None, None), (b6, cls6), ("STOP 9: the audit engine stopped at the job deadline", "node"),
                       ("STOP 4: timing", "timing"), ("STOP 8: something else", "node")):
        assert AH.reclassify_shared(stop_, cls), stop_
    for stop_, cls in (("STOP 2: the audit engine stopped on the isolation gate", "node"),
                       ("STOP 10: seed 9001 is not an audit seed", "node"), (J.ORPHANS_EXIT, "node"),
                       ("STOP 7: infrastructure rows", "infrastructure")):
        assert not AH.reclassify_shared(stop_, cls), stop_


def test_shared_baseline_failed_attempt_is_infrastructure_end_to_end(ada):
    w = ada
    s = w["spec"]
    TJ.first_wave(w)
    claim_ada(w)
    copy_to(w, "Ada-g0", "mlab_imdb", 1, 1)
    w["on"]("Ada-g0")
    inner = TJ.Engine(s, chunk_stop="baseline OOM", chunk_stop_kind="baseline_failed")

    def arrives(argv, **kw):
        w["ada_state"]["apps"] = f"{UUIDA}, 4242, 30000 MiB\n"
        return inner(argv, **kw)
    with pytest.raises(S.Stop, match="another compute process was on the card.*recorded before: STOP 6"):
        run_ada(w, 1, arrives)
    r = json.loads((J.job_dir(s, "mlab_imdb", "audits-wave1", 1) / "attempt-1" / "job_record.json").read_text())
    assert r["stop_class"] == "infrastructure"
    w["ada_state"]["apps"] = ""                                       # unshared: STOP 6 keeps its node class
    inner2 = TJ.Engine(s, chunk_stop="baseline", chunk_stop_kind="baseline_failed")
    with pytest.raises(S.Stop, match="STOP 6"):          # (attempt 2 on the card; only its class is checked)
        run_ada(w, 1, inner2)
    r2 = json.loads((J.job_dir(s, "mlab_imdb", "audits-wave1", 1) / "attempt-2" / "job_record.json").read_text())
    assert r2["stop_class"] == "node"


def test_finalize_names_a_claim_host(ada, tmp_path):
    """m6: finalize-remote is for TASL-7 or a host some claim names."""
    w = ada
    log = tmp_path / "log.jsonl"
    log.write_text("")
    stop("neither TASL-7 nor a host any claim of this run names", J.finalize_remote, w["spec"], w["sp"], log,
         hostname=TJ.HOST2, host="Ada-g9")
    stop("has no remote access log", J.finalize_remote, w["spec"], w["sp"], log, hostname=TJ.HOST2, host="TASL-2")
