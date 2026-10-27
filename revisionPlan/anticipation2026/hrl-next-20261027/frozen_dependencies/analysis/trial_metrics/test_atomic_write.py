"""Test transient/persistent Windows sharing conflicts in atomic metric writes."""
from pathlib import Path
import importlib.util,json,sys,tempfile,threading,types
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.modules.setdefault('unreal',types.ModuleType('unreal'))
spec=importlib.util.spec_from_file_location('metrics_test',ROOT/'Content/Python/trial_metrics.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory(prefix='trial-metrics-retry-') as directory:
    p=Path(directory)/'metrics.json';p.write_text('{"old":true}')
    held=p.open('r');release=threading.Timer(.2,held.close);release.start()
    m.atomic(p,{'new':True});release.join();assert json.loads(p.read_text())=={'new':True}
    original=p.read_bytes()
    with patch.object(m.os,'replace',side_effect=PermissionError('persistent lock')) as replace,patch.object(m.time,'sleep'):
        try:m.atomic(p,{'must_not_replace':True})
        except PermissionError:pass
        else:raise AssertionError('Persistent failure was swallowed')
        assert replace.call_count==20 and p.read_bytes()==original
    with patch.object(m.os,'replace',side_effect=OSError('other failure')) as replace:
        try:m.atomic(p,{'other':True})
        except OSError:pass
        else:raise AssertionError('Unexpected OS error was swallowed')
        assert replace.call_count==1
(ROOT/'analysis/trial_metrics/atomic_write_validation.json').write_text(json.dumps({'passed':True,'checks':['real Windows open-reader conflict resolves after release','persistent conflict raises after 20 attempts and preserves old target','other OS errors are not retried']},indent=2))
print('Atomic-write recovery tests passed.')
