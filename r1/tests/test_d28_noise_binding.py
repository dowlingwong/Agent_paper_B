"""CPU-only safety tests for the D28 repair noise-source contract."""
import hashlib
import json
from pathlib import Path

import pytest

from r1.scripts import c3_label_sweep as S
from r1.c3 import dataset as D, offline_eval as E
from r1 import harness as H
from r1.headroom.e1b_collect import node_noise


def fixture(tmp_path):
    paper=tmp_path/"paper"; paper.mkdir()
    source=paper/"inputs/noise.json"; source.parent.mkdir()
    source.write_text(json.dumps({"nodes":{"digits_mlp":{"edits":[{"material":True,"sd_joint":0.1,"sd_train":0.04,"sd_split":0.08}]}}}))
    pin={"path":"inputs/noise.json","sha256":hashlib.sha256(source.read_bytes()).hexdigest()}
    cfg=S.load_config(None); cfg["nodes"]=["digits_mlp"]; cfg["noise_source"]=pin
    runner=S.SweepRunner(cfg,batch=tmp_path/"batch",paper=paper,harness=tmp_path/"harness",python="py")
    return paper,source,pin,runner


def test_runner_checks_source_digest_coverage_and_manifest(tmp_path):
    paper,source,pin,runner=fixture(tmp_path)
    assert runner.check_noise_source()==pin
    manifest_dir=paper/"manifest"; manifest_dir.mkdir()
    manifest={"nodes":["digits_mlp"],"noise":{"digits_mlp":node_noise(source,"digits_mlp")},
              "c3_label_sweep":{"noise_source":pin}}
    (manifest_dir/"manifest.json").write_text(json.dumps(manifest))
    runner.check_noise_manifest(manifest_dir)
    manifest["noise"]["digits_mlp"]["sigma_d"] += 1
    (manifest_dir/"manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(S.Stop,match="noise values differ"):
        runner.check_noise_manifest(manifest_dir)
    manifest["noise"]["digits_mlp"] = node_noise(source,"digits_mlp")
    manifest["c3_label_sweep"]["noise_source"]={"path":pin["path"],"sha256":"0"*64}
    (manifest_dir/"manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(S.Stop,match="manifest noise source"):
        runner.check_noise_manifest(manifest_dir)
    source.write_text(json.dumps({"nodes":{"wrong":{}}}))
    with pytest.raises(S.Stop,match="sha256 mismatch"):
        runner.check_noise_source()
    runner.config["noise_source"]["sha256"]=hashlib.sha256(source.read_bytes()).hexdigest()
    with pytest.raises(S.Stop,match="lacks configured nodes"):
        runner.check_noise_source()


def test_runner_passes_actual_pinned_summary_to_collector(tmp_path):
    paper,source,pin,runner=fixture(tmp_path)
    runner.state["steps"]={"liveness":{"eligible_nodes":["digits_mlp"],"out":"fixture_liveness"},"sweep_none":{}}
    runner.state["ollama"]={}
    runner.require_liveness=lambda *args: None
    runner.save=lambda: None
    runner.manager_model_args=lambda: []
    class Capture(Exception): pass
    seen={}
    def collect(command,*args):
        seen["command"]=command
        raise Capture()
    runner.collect=collect
    with pytest.raises(Capture):
        runner.sweep("none")
    command=seen["command"]
    assert Path(command[command.index("--e1-summary")+1]).read_bytes()==source.read_bytes()
    extra=json.loads(command[command.index("--extra-manifest")+1])
    assert extra["c3_label_sweep"]["noise_source"]==pin


def write_index(paper,pin):
    out=paper/"runs/none"; ledgers=out/"ledgers"; (ledgers/"digits_mlp__s1").mkdir(parents=True)
    (ledgers/"digits_mlp__s1/root_trials.jsonl").write_text("")
    manifest={"memory_mode":"none","runs":20,"instances":1,"nodes":["digits_mlp"],
              "noise":{"digits_mlp":node_noise(paper/pin["path"],"digits_mlp")},
              "c3_label_sweep":{"noise_source":pin}}
    (out/"manifest.json").write_text(json.dumps(manifest))
    index={"schema":D.SWEEP_INDEX_SCHEMA,"written_utc":"20261027","nodes":["digits_mlp"],
           "runs":20,"instances":1,"noise_source":pin,
           "sweeps":[{"memory_mode":"none","out":"runs/none","manifest":"runs/none/manifest.json",
                      "ledgers":"runs/none/ledgers"}]}
    path=paper/"index.json"; path.write_text(json.dumps(index))
    return path,out,manifest,index


def test_build_sweep_uses_index_pin_refuses_override_and_tamper(tmp_path,monkeypatch):
    paper,source,pin,_=fixture(tmp_path)
    index,out,manifest,data=write_index(paper,pin)
    used=[]
    monkeypatch.setattr(D,"noise_table",lambda p=None: used.append(p) or {"test":"noise"})
    monkeypatch.setattr(D,"_replay_sources",lambda *a,**k: ([],{},{"one":{}}))
    monkeypatch.setattr(D,"_write_table",lambda out,rows,configs,checks,head,noise: head)
    meta=D.build_from_sweep(index,tmp_path/"table",paper_root=paper)
    assert Path(used[-1])==source.resolve() and meta["noise_source"]==pin
    other=paper/"other.json"; other.write_bytes(source.read_bytes())
    with pytest.raises(ValueError,match="explicit E1 summary differs"):
        D.build_from_sweep(index,tmp_path/"other",paper_root=paper,e1_summary=other)
    manifest["noise"]["digits_mlp"]["sigma_d"] += 1
    (out/"manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match="noise values differ"):
        D.build_from_sweep(index,tmp_path/"badvalue",paper_root=paper)
    manifest["noise"]["digits_mlp"] = node_noise(source,"digits_mlp")
    manifest["c3_label_sweep"]["noise_source"]={"path":pin["path"],"sha256":"f"*64}
    (out/"manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match="noise source differs"):
        D.build_from_sweep(index,tmp_path/"bad",paper_root=paper)
    manifest["c3_label_sweep"]["noise_source"]=pin
    (out/"manifest.json").write_text(json.dumps(manifest))
    source.write_text('{"nodes":{}}')
    with pytest.raises(ValueError,match="sha256 mismatch"):
        D.build_from_sweep(index,tmp_path/"badsha",paper_root=paper)


def test_legacy_index_retains_legacy_noise_behavior(tmp_path,monkeypatch):
    paper,source,pin,_=fixture(tmp_path)
    index,out,manifest,data=write_index(paper,pin)
    data.pop("noise_source"); index.write_text(json.dumps(data))
    used=[]
    monkeypatch.setattr(D,"noise_table",lambda p=None: used.append(p) or {"legacy":1})
    monkeypatch.setattr(D,"_replay_sources",lambda *a,**k:([],{},{"one":{}}))
    monkeypatch.setattr(D,"_write_table",lambda out,rows,configs,checks,head,noise:head)
    meta=D.build_from_sweep(index,tmp_path/"legacy",paper_root=paper)
    assert used==[None] and "noise_source" not in meta


def test_offline_evaluation_checks_table_source_and_uses_its_noise(tmp_path,monkeypatch):
    paper,source,pin,_=fixture(tmp_path)
    table=paper/"table"; table.mkdir()
    expected={"digits_mlp":{"delta_n":0.123}}
    (table/"build.json").write_text(json.dumps({"noise_source":pin,"noise":expected}))
    monkeypatch.setattr(H,"REPO",paper)
    monkeypatch.setattr(E,"noise_table",lambda path: expected)
    assert E.table_noise(table)==expected
    source.write_text("{}")
    with pytest.raises(ValueError,match="sha256 mismatch"):
        E.table_noise(table)
    (table/"build.json").write_text("{}")
    assert E.table_noise(table) is None


def test_both_memory_manifests_must_match_the_same_source(tmp_path):
    paper,source,pin,_=fixture(tmp_path)
    index,out,manifest,data=write_index(paper,pin)
    other=paper/"runs/on"; ledger=other/"ledgers/digits_mlp__s1"; ledger.mkdir(parents=True)
    (ledger/"root_trials.jsonl").write_text("")
    wrong={"path":pin["path"],"sha256":"f"*64}
    manifest["memory_mode"]="append_only_summary"
    manifest["c3_label_sweep"]["noise_source"]=wrong
    (other/"manifest.json").write_text(json.dumps(manifest))
    data["sweeps"].append({"memory_mode":"append_only_summary","out":"runs/on",
                           "manifest":"runs/on/manifest.json","ledgers":"runs/on/ledgers"})
    with pytest.raises(ValueError,match="noise source differs"):
        D.sweep_sources(data,index,paper)


def test_composite_is_reproducible_and_node_sources_are_exact():
    from r1.scripts import build_d28_noise_summary as B
    common=json.loads((B.ROOT/B.OLD).read_text())
    repair=B.check_run(B.ROOT/B.REPAIR,(*B.REPAIRED,"openml_blood_transfusion"))
    climate=B.check_run(B.ROOT/B.CLIMATE,("openml_climate",))
    composite=B.build()
    assert (json.dumps(composite,indent=2,sort_keys=True)+"\n").encode()==(B.ROOT/B.OUT).read_bytes()
    assert all(composite["nodes"][n]==common["nodes"][n] for n in B.UNCHANGED)
    assert all(composite["nodes"][n]==repair["nodes"][n] for n in B.REPAIRED)
    assert composite["nodes"]["openml_climate"]==climate["nodes"]["openml_climate"]
    assert "openml_blood_transfusion" not in composite["nodes"]
    assert set(D.noise_table(B.ROOT/B.OUT))==set(B.UNCHANGED+B.REPAIRED+("openml_climate",))


def test_offline_main_passes_table_noise_to_evaluation(tmp_path,monkeypatch):
    table=tmp_path/"table"; table.mkdir()
    expected={"node":{"delta_n":0.123}}
    monkeypatch.setattr(E,"table_noise",lambda path: expected)
    monkeypatch.setattr(E,"assemble",lambda *args: [])
    class Seen(Exception): pass
    def evaluate(rows,mode,k=3,noise=None,**kwargs):
        assert mode=="instance" and noise is expected
        raise Seen()
    monkeypatch.setattr(E,"evaluate",evaluate)
    with pytest.raises(Seen):
        E.main(["--table",str(table)])


def test_composite_builder_refuses_missing_wrong_seed_or_failed_edit(tmp_path,monkeypatch):
    from r1.scripts import build_d28_noise_summary as B
    root=tmp_path/"run"; root.mkdir()
    (root/"manifest.json").write_text(json.dumps({"harness":{"commit":"6adf3859de66c4814fcf376eed59880fbd8eeaf7","dirty":False},
                                                  "seeds_per_condition":30,"nodes":["openml_climate"]}))
    rows=[]
    for k in range(6):
        base={"node":"openml_climate","config":f"c{k}","success":True,"metric":0.5,
              "edit_applied":True if k else None}
        for condition,offset in (("train",1000),("split",2000),("joint",3000)):
            for i in range(1,31):
                rows.append({**base,"condition":condition,
                             "train_seed":offset+i if condition!="split" else None,
                             "split_seed":offset+i if condition!="train" else None})
        for condition in ("default","default_repeat"):
            rows.append({**base,"condition":condition,"train_seed":None,"split_seed":None})
    def write():
        (root/"runs.jsonl").write_text("".join(json.dumps(row)+"\n" for row in rows))
    monkeypatch.setattr(B,"summarise",lambda path: {"ok":True})
    write(); assert B.check_run(root,("openml_climate",))=={"ok":True}
    rows[0]["train_seed"]=9999; write()
    with pytest.raises(ValueError,match="seed coverage"): B.check_run(root,("openml_climate",))
    rows[0]["train_seed"]=1001; rows[92]["edit_applied"]=False; write()
    with pytest.raises(ValueError,match="edit not applied"): B.check_run(root,("openml_climate",))
    rows[92]["edit_applied"]=True; rows.pop(); write()
    with pytest.raises(ValueError,match="incomplete"): B.check_run(root,("openml_climate",))
