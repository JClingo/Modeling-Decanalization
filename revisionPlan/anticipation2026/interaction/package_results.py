"""Preserve complete scored data for all six factorial cells and shared CCC."""
from pathlib import Path
import hashlib,json,zipfile
import run_experiment as ex

HERE=Path(__file__).resolve().parent;BASE=HERE.parent
read=lambda p:json.loads(Path(p).read_text())
assert read(HERE/'verification.json')['passed']
assert (HERE/'r_verification.txt').read_text().startswith('PASS:')
run=Path(read(HERE/'source_manifest.json')['source_run'])
assert read(run/'complete.json')['passed']
destination=HERE/'reproducible-results.zip'
assert not destination.exists(),'Preserve an existing archive; create a new explicit version if needed.'
entries={}
def add(path,name):
    path=Path(path);assert path.is_file(),path
    assert name not in entries or entries[name]==path,name
    entries[name]=path
for path in BASE.rglob('*'):
    if path.is_file() and '__pycache__' not in path.parts and path.suffix not in ['.zip','.pyc']:
        if path==HERE/'bundle_manifest.json' or path.name=='postprocess_status.json':continue
        add(path,'paper/revisionPlan/anticipation2026/'+str(path.relative_to(BASE)))
for name in ['trial_metrics.csv','primary_contrasts.csv','phase_summary.csv','README.md']:
    add(BASE.parent/'rerun2026'/name,'paper/revisionPlan/rerun2026/'+name)
for path in run.iterdir():
    if path.is_file():add(path,'native/'+path.name)
for condition in ex.CONDITIONS:
    for path in (run/condition).rglob('*'):
        if path.is_file():add(path,'native/'+condition+'/'+str(path.relative_to(run/condition)))
refs={
    'k1-zero':Path(read(BASE/'recanalization/inputs/zero.verified.json')['metrics']),
    'k1-keep':Path(read(BASE/'recanalization/inputs/keep.verified.json')['metrics']),
    'k1-half':Path(read(BASE/'plasticity/inputs/factor-1.verified.json')['metrics']),
    'k7-half':Path(read(BASE/'plasticity/inputs/factor-7.verified.json')['metrics']),
    'CCC':Path(read(ex.EXPORT/'comparison.json')['HRL']['ccc']['metrics'])}
for condition,metric in refs.items():
    rid=read(metric)['run-id']
    for item in metric.parent.iterdir():
        if not item.name.startswith(rid):continue
        if item.is_file():add(item,'native/'+condition+'/TrialResults/'+item.name)
        else:
            for path in item.rglob('*'):
                if path.is_file():add(path,'native/'+condition+'/TrialResults/'+str(path.relative_to(metric.parent)))
    if condition in ['k1-zero','k1-keep']:
        asset=BASE/'recanalization/inputs'/('zero' if condition=='k1-zero' else 'keep')
        asset=asset.with_name(asset.name+'.BP_Tile.compiled.uasset')
    elif condition in ['k1-half','k7-half']:
        oldrun=Path(read(BASE/'plasticity/source_manifest.json')['source_run'])
        worker=0 if condition=='k1-half' else 3
        asset=oldrun/f'worker-{worker}/TestProject/Content/Level/BP_Tile.uasset'
    else:asset=ex.SOURCE/'Content/Level/BP_Tile.uasset'
    assert ex.sha(asset)==read(metric)['provenance']['asset-sha256']['Level/BP_Tile'],condition
    add(asset,'native/'+condition+'/BP_Tile.compiled.uasset')
for path in (ex.EXPORT/'policies/HRL').rglob('*'):
    if path.is_file():add(path,'selected-policy/HRL/'+str(path.relative_to(ex.EXPORT/'policies/HRL')))
for name in ['BP_Agent.uasset','BP_GameMode.uasset']:
    add(ex.SOURCE/'Content/Agent'/name,'source-assets/Agent/'+name)
add(ex.SOURCE/'Content/Level/BP_Tile.uasset','source-assets/Level/BP_Tile.original.uasset')
for name in ['graph_asset.py','patch_graphs.py']:
    add(ex.SOURCE/'analysis/timing'/name,'tools/'+name)
for path in ex.base.ASSETCLI.parent.iterdir():
    if path.is_file():add(path,'tools/AssetAudit/'+path.name)
with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name,path in sorted(entries.items()):z.write(path,name)
with zipfile.ZipFile(destination) as z:
    assert z.testzip() is None;count=len(z.infolist())
receipt=dict(archive=destination.name,bytes=destination.stat().st_size,members=count,
    sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),crc_verified=True,created_at=ex.base.stamp())
(HERE/'bundle_manifest.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
