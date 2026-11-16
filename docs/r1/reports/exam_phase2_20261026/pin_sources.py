import json,urllib.request,hashlib,concurrent.futures
from pathlib import Path
import yaml
ROOT=Path('/Users/wongdowling/Documents/agent_paper_B');OUT=ROOT/'docs/r1/reports/exam_phase2_20261026'
REG=ROOT/'r1/exam/registry.yaml';reg=yaml.safe_load(REG.read_text())
mapping={'qwen38_27b':'bartowski/Qwen3.8-27B-GGUF','qwen36_27b':'bartowski/Qwen_Qwen3.6-27B-GGUF','gemma4_31b':'bartowski/google_gemma-4-31B-it-GGUF','muse_glimmer_30b':'meta-models/Muse-Glimmer-30B-GGUF','olmo31_32b':'bartowski/allenai_Olmo-3.1-32B-Instruct-GGUF','devstral_small2_24b':'bartowski/mistralai_Devstral-Small-2-24B-Instruct-2512-GGUF','qwen36_35b_a3b':'bartowski/Qwen_Qwen3.6-35B-A3B-GGUF','gemma4_26b_a4b':'bartowski/google_gemma-4-26B-A4B-it-GGUF','nemotron35_30b_a3b':'bartowski/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-GGUF','glm47_flash':'bartowski/zai-org_GLM-4.7-Flash-GGUF','lfm25_24b_a2b':'LiquidAI/LFM2.5-24B-A2B-GGUF','laguna_xs21':'poolside/Laguna-XS-2.1-GGUF','ornith10_35b':'ornith-ai/Ornith-1.0-35B-GGUF','gpt_oss_20b':'bartowski/openai_gpt-oss-20b-GGUF','qwen35_9b':'bartowski/Qwen_Qwen3.5-9B-GGUF','gemma4_12b':'bartowski/gemma-4-12B-it-GGUF','ornith10_9b':'ornith-ai/Ornith-1.0-9B-GGUF','ministral3_14b':'mistralai/Ministral-3-14B-Instruct-2512-GGUF','rico03_qwen36_27b':'rico03/Qwen3.6-27B-Claude-Opus-Reasoning-Distilled-GGUF','qwen25_coder_7b':'Qwen/Qwen2.5-Coder-7B-Instruct-GGUF','olmo31_32b_think':'bartowski/allenai_Olmo-3.1-32B-Think-GGUF'}
def resolve(row):
 name=row['id'];data=json.loads((OUT/(name+'.json')).read_text());vendor=[e for e in data['entries'] if e['files'] and e['repo'].split('/')[0]==row['base_repo'].split('/')[0]]
 row['vendor_q4_available']=bool(vendor)
 if name not in mapping:
  row['phase2_status']='NO_APPROVED_SOURCE_FOUND';row['phase2_reason']='No vendor or bartowski Q4_K_M in exact model searches; no substitute authorized.';return
 e=next(e for e in data['entries'] if e['repo']==mapping[name]);files=[f for f in e['files'] if not any(x in f['rfilename'].lower() for x in ['mmproj','dflash','-00001-of-','-00002-of-'])]
 if name=='gpt_oss_20b':files=[f for f in files if f['rfilename'].endswith('-MXFP4.gguf')]
 assert len(files)==1,(name,files)
 f=files[0];q='MXFP4' if name=='gpt_oss_20b' else 'Q4_K_M';kind='native_mxfp4' if name=='gpt_oss_20b' else ('vendor' if vendor else 'bartowski_imatrix')
 source={'kind':kind,'repo':e['repo'],'revision':e['revision'],'file':f['rfilename'],'size_bytes':f['size'],'sha256':f['lfs']['sha256'],'quantization':q,'base_model':row['base_repo']}
 if kind=='bartowski_imatrix':
  assert len(e['imatrix_files'])==1,name
  source.update(imatrix_file=e['imatrix_files'][0]['rfilename'],imatrix_sha256=e['imatrix_files'][0]['lfs']['sha256'])
 readme_url=f"https://huggingface.co/{e['repo']}/resolve/{e['revision']}/README.md"
 try:
  with urllib.request.urlopen(readme_url,timeout=45) as resp:readme=resp.read()
  (OUT/(name+'_quant_README.md')).write_bytes(readme);source['readme_sha256']=hashlib.sha256(readme).hexdigest()
 except Exception as error:source['readme_error']=str(error)
 cfgurl=f"https://huggingface.co/{row['base_repo']}/resolve/{row['base_revision']}/config.json"
 with urllib.request.urlopen(cfgurl,timeout=45) as resp:cfg=resp.read()
 cfgpath=OUT/(name+'_config.json');cfgpath.write_bytes(cfg)
 row['quant_source']=source;row['runtime'].update(model_path=f"/home/dowling/exam-x/models/{name}/{f['rfilename']}",model_config_path=f"/home/dowling/exam-x/work/agent_paper_B/docs/r1/reports/exam_phase2_20261026/{cfgpath.name}",model_config_sha256=hashlib.sha256(cfg).hexdigest())
 row['phase2_status']='SOURCE_PINNED_NOT_DOWNLOADED'
 print(name,kind,f['size'],flush=True)
rows=reg['candidates']+reg.get('sensitivities',[])
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:list(pool.map(resolve,rows))
REG.write_text(json.dumps(reg,indent=2)+'\n')
print('TOTAL_BYTES',sum(r['quant_source']['size_bytes'] for r in rows if r.get('phase2_status')=='SOURCE_PINNED_NOT_DOWNLOADED'))
