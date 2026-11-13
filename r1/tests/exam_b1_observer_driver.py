"""Pinned-harness B1 candidate against a synthetic loopback-only HTTP server."""
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'r1/scripts'))
requests=[]
fail_observer=sys.argv[2]=='fail'
# 'slow': the observer answer is delayed by OBS_DELAY_S; OBS_TIMEOUT_S, if set, replaces the observer timeout
slow_observer=sys.argv[2]=='slow'

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def do_POST(self):
        import c3_fake_ollama as fake
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        prompt=body['messages'][-1]['content']
        observer=prompt.startswith('You proposed the edit below.')
        requests.append({'observer':observer,'body':body})
        if observer and slow_observer:
            import time
            time.sleep(float(os.environ['OBS_DELAY_S']))
        if observer and fail_observer:
            self.send_response(503);self.send_header('Content-Length','0');self.end_headers();return
        answer={'p_no_effect':0.2,'p_positive':0.7,'size':'small'} if observer else fake.proposal_for(prompt,body.get('seed'))
        payload=json.dumps({'id':'fixture','object':'chat.completion','created':1,'model':body['model'],
            'choices':[{'index':0,'finish_reason':'stop','message':{'role':'assistant','content':json.dumps(answer)}}],
            'usage':{'prompt_tokens':7,'completion_tokens':5,'total_tokens':12}}).encode()
        self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)

root=Path(sys.argv[1]);root.mkdir(parents=True,exist_ok=True);(root/'.dryrun').write_text('synthetic')
out=root/'root';out.mkdir()
server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{server.server_address[1]}/v1'
os.environ['LLAMACPP_BASE_URL']=url
for key in ('LLAMACPP_CACHE_PROMPT','OPENAI_API_KEY','OPENAI_BASE_URL'):
    os.environ.pop(key,None)
from r1.exam.campaign import collect
from r1.exam.observer import B1ObserverFatal
if os.environ.get('OBS_TIMEOUT_S'):
    import r1.exam.observer as _observer_module
    _observer_module.OBSERVER_TIMEOUT_S=float(os.environ['OBS_TIMEOUT_S'])
job={'out':str(out),'binding':'fixture','workers':1,'host':'fixture','phase':'b1','node':'digits_mlp','seed':9001,
     'candidate':{'id':'standin_candidate'},'mode':'off','dryrun':True,'W':2,'llm_call_cap':8,
     'audit_seeds':[9101,9102,9103,9104],'base_url':url,'value_grids':str(ROOT/'r1/exam/value_grids.yaml'),
     'proposal_schema':'manager_proposal/v1','authority_config':{'dryrun':True,'dryrun_root':str(root),'rule_sha256':'fixture'}}
(out/'job.json').write_text(json.dumps(job))
try:
    try: collect(job);status='complete'
    except B1ObserverFatal: status='observer_stop'
finally:
    server.shutdown();server.server_close()
(root/'driver_result.json').write_text(json.dumps({'status':status,'requests':requests}))
