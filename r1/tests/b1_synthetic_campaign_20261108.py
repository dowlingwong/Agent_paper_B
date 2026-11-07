"""Run the real campaign child with test-owned DRYRUN output retention."""
from pathlib import Path
import sys
from r1.exam import campaign
from r1.tests.b1_synthetic_retention_20261108 import guarded_json, retire
from autoresearch.control_plane import campaign as control

campaign.write_json=guarded_json(campaign.write_json)
original_trial=campaign.FixtureWorker.run_trial
original_text=Path.write_text

def trial(self,proposal,node_spec,budget_index):
    targets={self.node_root/p for p in node_spec.editable_paths}
    def write(path,*args,**kwargs):
        if path in targets: retire(path)
        return original_text(path,*args,**kwargs)
    Path.write_text=write
    try: return original_trial(self,proposal,node_spec,budget_index)
    finally: Path.write_text=original_text

campaign.FixtureWorker.run_trial=trial
original_restore=control._restore_editable_state

def restore(snapshot):
    if snapshot is not None:
        for name in snapshot.contents:
            retire(control._editable_path(snapshot.root,name))
    return original_restore(snapshot)

control._restore_editable_state=restore
if __name__=='__main__': campaign.main(sys.argv[1:])
