import json, urllib.request, datetime
repo='ornith-ai/Ornith-1.0-35B'
base='https://huggingface.co/'
with urllib.request.urlopen(base+'api/models/'+repo,timeout=15) as r: data=json.load(r)
sha=data['sha']; card=data.get('cardData') or {}
url=base+repo+'/resolve/'+sha+'/config.json'
with urllib.request.urlopen(urllib.request.Request(url,method='HEAD'),timeout=15) as r: status=r.status
with urllib.request.urlopen(url,timeout=15) as r: config=json.load(r)
print(json.dumps({'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repo':repo,'sha':sha,'gated':data.get('gated'),'license':card.get('license'),'base_model':card.get('base_model'),'config_head_url':url,'anonymous_head_status':status,'config_architecture':{k:config.get(k) for k in ['architectures','model_type','num_experts','num_experts_per_tok','hidden_size','num_hidden_layers']},'text_config':config.get('text_config'),'scope':'Possible name mapping only; no author decision or substitution'}))
