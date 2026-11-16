"""Read-only GGUF metadata receiving; run with pinned llama.cpp/gguf-py on PYTHONPATH. No inference."""
import collections,json
from pathlib import Path
from gguf import GGUFReader,GGMLQuantizationType

work=Path('/home/dowling/exam-x/work');registry=json.loads((work/'agent_paper_B/r1/exam/registry.yaml').read_text())
out=work/'phase2/gguf_headers';out.mkdir(exist_ok=True)
for spec in registry['candidates']+registry.get('sensitivities',[]):
    certificate=work/'phase2/downloads'/(spec['id']+'.json')
    if not certificate.exists():continue
    target=Path(spec['runtime']['model_path']);reader=GGUFReader(target,'r')
    architecture=reader.get_field('general.architecture').contents()
    selected={key:field.contents() for key,field in reader.fields.items()
              if key.startswith(architecture+'.') or key in ('general.architecture','general.file_type','general.quantization_version','general.name','general.size_label')}
    names={t.name for t in reader.tensors}
    report={'candidate':spec['id'],'source_label':spec['source_label'],'artifact_sha256_pin':spec['quant_source']['sha256'],
            'architecture':architecture,'fields':selected,'tensor_count':len(reader.tensors),
            'tensor_types':dict(collections.Counter(GGMLQuantizationType(t.tensor_type).name for t in reader.tensors)),
            'has_split_mla_k_b':any('.attn_k_b.' in n for n in names),'has_split_mla_v_b':any('.attn_v_b.' in n for n in names),
            'reader_source_commit':'620d2225cc436ab0b001e3200e590e3b286ef9ab'}
    (out/(spec['id']+'.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(spec['id'],architecture,len(reader.tensors))
    del reader
