"""Import a completed, correctly identified primary run with all provenance."""
from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def collect(path,family,order):
    path=Path(path).resolve();d=json.loads(path.read_text());v=d['provenance'];record=v['matched-training-record']
    assert d['status']=='complete' and len(d['trials'])==250 and d['schema-version']==2
    assert record and record['reward-family']==family and record['snapshot-update-label']==(10000 if family=='HRL' else 5000)
    assert v['environment']['TrialSequenceOrder']==order and v['environment']['IsHRL']==(family=='HRL')
    y=path.parent/d['results-file'];receipt=y.with_suffix('.completed.json');r=json.loads(receipt.read_text())
    assert r['results_saved'] and r['trials_completed']==r['trials_requested']==250
    for s in v['snapshots'].values():assert sha(path.parent/s['loaded-snapshot'])==s['loaded-sha256']
    assert all(len(t['phases'])==3 and all(p.get('complete') and p['decision-ticks']==2000 for p in t['phases']) for t in d['trials'])
    dest=ROOT/'analysis/data';dest.mkdir(exist_ok=True)
    for p in [path,y,receipt]:
        target=dest/p.name
        if target.exists():assert sha(target)==sha(p),'Refusing to overwrite different input '+str(target)
        else:shutil.copy2(p,target)
    provenance=y.with_suffix('.provenance')
    for p in provenance.iterdir():
        target=dest/provenance.name/p.name;target.parent.mkdir(exist_ok=True)
        if target.exists():assert sha(target)==sha(p)
        else:shutil.copy2(p,target)
    print('Imported '+y.stem,flush=True);return y.stem
if __name__=='__main__':collect(*sys.argv[1:])
