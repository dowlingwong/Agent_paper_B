import concurrent.futures, datetime, json, os, pathlib, urllib.request, urllib.parse, urllib.error
repos = [
'Qwen/Qwen3.8-27B','Qwen/Qwen3.6-27B','google/gemma-4-31B-it','meta-models/Muse-Glimmer-30B',
'allenai/Olmo-3.1-32B-Instruct','allenai/Olmo-3.1-32B-Think','mistralai/Devstral-Small-2-24B-Instruct-2512',
'ornith-ai/Ornith-1.0-31B','Qwen/Qwen3.6-35B-A3B','google/gemma-4-26B-A4B-it',
'nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16','zai-org/GLM-4.7-Flash','LiquidAI/LFM2.5-24B-A2B',
'poolside/Laguna-XS-2.1','ornith-ai/Ornith-1.0-35B-A3B','Qwen/Qwen3-Coder-30B-A3B-Instruct','openai/gpt-oss-20b',
'Qwen/Qwen3.5-9B','google/gemma-4-12B-it','ornith-ai/Ornith-1.0-9B','mistralai/Ministral-3-14B-Instruct-2512',
'rico03/Qwen3.6-27B-Claude-Opus-Reasoning-Distilled','skiboyvv/Qwopus3.6-27B-v4','Qwen/Qwen2.5-Coder-7B-Instruct']
def request(url, method='GET', auth=None):
    headers={'User-Agent':'PaperB-Phase0-readonly'}
    if auth: headers['Authorization']='Bearer '+auth
    try:
        with urllib.request.urlopen(urllib.request.Request(url,method=method,headers=headers),timeout=20) as r:
            return r.status, (json.load(r) if method=='GET' else None), r.headers.get('X-Error-Code')
    except urllib.error.HTTPError as e: return e.code,None,e.headers.get('X-Error-Code')
    except Exception as e: return None,None,type(e).__name__+': '+str(e)
# Read existing conventional credentials only; never print a token or write an auth cache.
hfhome=pathlib.Path(os.environ.get('HF_HOME', str(pathlib.Path(os.environ.get('XDG_CACHE_HOME',str(pathlib.Path.home()/'.cache')))/'huggingface')))
paths=[pathlib.Path(os.environ.get('HF_TOKEN_PATH',str(hfhome/'token'))),pathlib.Path.home()/'.huggingface/token']
token=os.environ.get('HF_TOKEN') or os.environ.get('HUGGING_FACE_HUB_TOKEN')
source='environment' if token else None
for path in paths:
    if not token and path.is_file():
        try: token=path.read_text().strip(); source=str(path)
        except OSError: pass
identity={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'kind':'auth','token_present':bool(token),'source':source,'credential_values_logged':False}
if token:
    status,data,error=request('https://huggingface.co/api/whoami-v2',auth=token)
    identity.update(status=status,username=data.get('name') if data else None,error=error)
print(json.dumps(identity),flush=True)
def fetch(repo):
    url='https://huggingface.co/api/models/'+repo
    status,m,error=request(url)
    row={'repo':repo,'api_url':url,'api_status':status,'error':error}
    if m:
        card=m.get('cardData') or {}
        row.update(canonical_id=m.get('id'),sha=m.get('sha'),gated=m.get('gated'),license=card.get('license'),license_name=card.get('license_name'),license_link=card.get('license_link'),license_tags=[t for t in m.get('tags',[]) if t.startswith('license:')])
        revision=m['sha']
        config='https://huggingface.co/'+repo+'/resolve/'+revision+'/config.json'
        code,_,err=request(config,'HEAD')
        row.update(config_head_url=config,anonymous_head_status=code,anonymous_error_code=err)
        if token:
            code,_,err=request(config,'HEAD',token)
            row.update(authenticated_head_status=code,authenticated_error_code=err)
    return row
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    for row in pool.map(fetch,repos): print(json.dumps(row),flush=True)
for query in ['Ornith-1.0-31','Ornith-1.0-35B-A3B','LFM2.5-24B-A2B']:
    url='https://huggingface.co/api/models?'+urllib.parse.urlencode({'search':query,'limit':100,'full':'true'})
    status,data,error=request(url)
    print(json.dumps({'kind':'extra_discovery','query':query,'url':url,'status':status,'ids':[x['id'] for x in (data or [])],'error':error}),flush=True)
