"""Validate schema-2 native smoke-test logs without mixing historical results."""
from pathlib import Path
import gzip,hashlib,json,math,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'Saved/AnalysisPython'))
import yaml

def validate(path):
    path=path.resolve();run=json.loads(path.read_text());assert run['schema-version']==2 and run['status']=='complete'
    source=path.with_name(run['results-file']);data=yaml.safe_load(source.read_text())
    receipt=json.loads(source.with_suffix('.completed.json').read_text());assert receipt['results_saved'] and receipt['trials_completed']==2
    assert data['schema-version']==2 and data['duration-unit']=='simulation-seconds'
    assert source.read_text().count('schema-version:')==1
    assert run['provenance']['training-record-match-count']==1
    for value in run['provenance']['snapshots'].values():
        assert hashlib.sha256((path.parent/value['loaded-snapshot']).read_bytes()).hexdigest()==value['loaded-sha256']
    assert len(data['trials'])==len(run['trials'])==2
    for trial,logged in zip(run['trials'],data['trials']):
        assert trial['id']==logged['id'] and len(trial['phases'])==3
        for phase,seq in zip(trial['phases'],logged['sequences']):
            assert phase['complete'] and phase['decision-ticks']==2000
            assert seq['duration']==phase['duration-seconds']==100
            for key in ['reward-total','setpoint-avg','setpoint-dev']:
                assert math.isclose(phase[key],seq[key],rel_tol=1e-6,abs_tol=1e-6),(key,phase[key],seq[key])
            assert phase['setpoint-dev']>=0 and phase['homeostatic-sample-count']>0
            assert 0<=phase['homeostatic-fraction-within-5']<=1
            assert phase['reward-total']>=0
            if trial['reward-function']=='HRL':assert phase['reward-total']<=100.0001
            assert hashlib.sha256(gzip.decompress((path.parent/phase['scene-file']).read_bytes())).hexdigest()==phase['scene-sha256']
    return dict(file=str(path.relative_to(ROOT)),family=run['trials'][0]['reward-function'],order=run['trials'][0]['sequence-order'],trials=2,phases=6,passed=True)

if __name__=='__main__':
    results=[validate(Path(p)) for p in sys.argv[1:]]
    assert results,'Provide completed smoke-test metrics JSON paths'
    target=ROOT/'analysis/trial_metrics/runtime_validation.json'
    target.write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
