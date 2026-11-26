import concurrent.futures, datetime, json, urllib.request, urllib.parse, urllib.error
queries = ['Qwen3.8-27B','Qwen3.6-27B','gemma-4-31B','Muse-Glimmer','OLMo-3.1-32B','Devstral-Small-2-24B','Ornith-1.0-31B','Qwen3.6-35B-A3B','gemma-4-26B','Nemotron-3.5-Lightning','GLM-4.7-Flash','LFM2.5-24B-A2B','Laguna-XS-2.1','Ornith-1.0-35B-A3B','Qwen3-Coder-30B-A3B-Instruct','gpt-oss-20b','Qwen3.5-9B','gemma-4-12B','Ornith-1.0-9B','Ministral-3-14B','rico03/Qwen3.6-27B-Claude-Opus-Reasoning-Distilled','skiboyvv/Qwopus3.6-27B-v4','Qwen2.5-Coder-7B-Instruct']
def fetch(q):
    url='https://huggingface.co/api/models?'+urllib.parse.urlencode({'search':q,'limit':10,'full':'true','sort':'downloads','direction':-1})
    try:
        with urllib.request.urlopen(url, timeout=20) as r: data=json.load(r)
        return {'query':q,'url':url,'models':[{'id':m['id'],'gated':m.get('gated'),'sha':m.get('sha'),'license':(m.get('cardData') or {}).get('license'),'private':m.get('private')} for m in data]}
    except Exception as e: return {'query':q,'url':url,'error':type(e).__name__+': '+str(e)}
print(json.dumps({'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'purpose':'Unauthenticated model-repository discovery only; no weights or installation'}), flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    for item in pool.map(fetch,queries): print(json.dumps(item),flush=True)
