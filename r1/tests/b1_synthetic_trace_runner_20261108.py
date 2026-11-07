"""Trace server errors and retain B1 DRYRUN-owned evidence in test children."""
import subprocess
import traceback
from r1.exam import campaign, runtime
from r1.scripts import exam_runner
from r1.scripts.llama_server_instance import LlamaServerInstance
from r1.tests.b1_synthetic_retention_20261108 import guarded_json, record_save

original_json=campaign.write_json
campaign.write_json=guarded_json(original_json)
runtime.write_json=campaign.write_json
exam_runner.write_json=campaign.write_json
LlamaServerInstance._save=record_save
original_popen=subprocess.Popen

def synthetic_campaign(args,*a,**kw):
    if len(args)>=3 and args[1:3]==['-m','r1.exam.campaign']:
        args=list(args);args[2]='r1.tests.b1_synthetic_campaign_20261108'
    return original_popen(args,*a,**kw)

runtime.subprocess.Popen=synthetic_campaign
original_server=runtime.ExamRunner.server

def traced_server(self,*args,**kwargs):
    try: return original_server(self,*args,**kwargs)
    except Exception:
        traceback.print_exc()
        raise

runtime.ExamRunner.server=traced_server
if __name__=='__main__': raise SystemExit(exam_runner.main())
