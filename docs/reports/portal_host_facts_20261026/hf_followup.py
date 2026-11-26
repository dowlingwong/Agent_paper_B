import json, urllib.request, urllib.parse, urllib.error, datetime
print(json.dumps({'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}))
urls=[
'https://huggingface.co/api/models?author=ornith-ai&limit=100',
'https://huggingface.co/api/models?author=deepreinforce-ai&limit=100',
'https://huggingface.co/api/models/jashepp/Ornith-1.0-35B-A3B-MXFP4_MOE_Hybrid-Imatrix-GGUF',
'https://huggingface.co/ornith-ai/Ornith-1.0-31B/resolve/main/config.json',
'https://huggingface.co/ornith-ai/Ornith-1.0-35B-A3B/resolve/main/config.json',
]
for url in urls:
    method='GET' if '/api/' in url else 'HEAD'
    try:
        with urllib.request.urlopen(urllib.request.Request(url,method=method),timeout=15) as r:
            d=json.load(r) if method=='GET' else None
            row={'url':url,'method':method,'status':r.status}
            if isinstance(d,list): row['ids']=[x['id'] for x in d]
            elif isinstance(d,dict): row['cardData']=d.get('cardData'); row['sha']=d.get('sha')
            print(json.dumps(row),flush=True)
    except urllib.error.HTTPError as e: print(json.dumps({'url':url,'method':method,'status':e.code,'error_code':e.headers.get('X-Error-Code')}),flush=True)
    except Exception as e: print(json.dumps({'url':url,'error':type(e).__name__+': '+str(e)}),flush=True)
