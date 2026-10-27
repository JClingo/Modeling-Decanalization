"""Archive scored data and exact local evidence after all checks complete."""
from pathlib import Path
import hashlib,json,zipfile
import run_experiment as ex

HERE=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text())
assert read(HERE/'verification.json')['passed']
assert (HERE/'r_verification.txt').read_text().startswith('PASS:')
manifest=read(HERE/'source_manifest.json')
run=Path(manifest['source_run']);assert read(run/'complete.json')['passed']
destination=HERE/'reproducible-results.zip'
assert not destination.exists(),'Preserve an existing archive; use a new explicit version when regenerating.'
entries={}
def add(path,name):
    path=Path(path)
    assert path.is_file(),path
    assert name not in entries or entries[name]==path,name
    entries[name]=path
# Preserve the on-disk analysis hierarchy: shared.load_inputs verifies historical
# CSV hashes relative to revisionPlan, and the sweep loader imports its parent.
for path in HERE.parent.rglob('*'):
    if path.is_file() and '__pycache__' not in path.parts and path.suffix not in ['.zip','.pyc']:
        if path==HERE/'bundle_manifest.json':continue
        add(path,'paper/revisionPlan/anticipation2026/'+str(path.relative_to(HERE.parent)))
for name in ['trial_metrics.csv','primary_contrasts.csv','phase_summary.csv','README.md']:
    add(HERE.parent.parent/'rerun2026'/name,'paper/revisionPlan/rerun2026/'+name)
for path in run.iterdir():
    if path.is_file():add(path,'native/'+path.name)
for name in [*ex.CONDITIONS,'smoke-half-exact']:
    for path in (run/name).rglob('*'):
        if path.is_file():add(path,'native/'+name+'/'+str(path.relative_to(run/name)))
reference=read(HERE.parent/'plasticity/inputs/factor-1.verified.json')
control=read(ex.EXPORT/'comparison.json')['HRL']['ccc']
for condition,path in [('half-floor',Path(reference['metrics'])),('CCC',Path(control['metrics']))]:
    rid=read(path)['run-id']
    for item in path.parent.iterdir():
        if item.name.startswith(rid):
            if item.is_file():add(item,'native/'+condition+'/TrialResults/'+item.name)
            else:
                for p in item.rglob('*'):
                    if p.is_file():add(p,'native/'+condition+'/TrialResults/'+str(p.relative_to(path.parent)))
for path in (ex.EXPORT/'policies/HRL').rglob('*'):
    if path.is_file():add(path,'selected-policy/HRL/'+str(path.relative_to(ex.EXPORT/'policies/HRL')))
for name in ['BP_Agent.uasset','BP_GameMode.uasset']:
    add(ex.SOURCE/'Content/Agent'/name,'source-assets/Agent/'+name)
add(ex.SOURCE/'Content/Level/BP_Tile.uasset','source-assets/Level/BP_Tile.original.uasset')
for name in ['graph_asset.py','patch_graphs.py']:
    add(ex.SOURCE/'analysis/timing'/name,'tools/'+name)
for path in ex.ASSETCLI.parent.iterdir():
    if path.is_file():add(path,'tools/AssetAudit/'+path.name)
with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name,path in sorted(entries.items()):z.write(path,name)
with zipfile.ZipFile(destination) as z:
    assert z.testzip() is None
    count=len(z.infolist())
receipt=dict(archive=destination.name,bytes=destination.stat().st_size,members=count,
             sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),crc_verified=True,
             created_at=ex.stamp())
(HERE/'bundle_manifest.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
