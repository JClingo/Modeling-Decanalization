"""Bundle analysis, all six HRL raw conditions, selected models and asset overrides.

Writes only inside this paper-analysis folder. No source experiment files are
modified. Unreal itself and the remaining project assets are not redistributed.
"""
from pathlib import Path
import datetime,hashlib,json,zipfile
HERE=Path(__file__).resolve().parent
SOURCE=Path('/Users/jingo/Work/PhD/Dissertation Project/decanalization')
RUN=SOURCE/'Saved/AnticipationPlasticity20261026'
EXPORT=SOURCE/'analysis/anticipation-retrained-2026-10-25'
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert read(RUN/'complete.json')['passed'] and read(HERE/'verification.json')['passed']
assert (HERE/'r_verification.txt').read_text().startswith('PASS:')
files={}
def add(path,name):
 path=Path(path);assert path.is_file() and name not in files
 files[name]=path
def tree(root,prefix):
 for p in sorted(root.rglob('*')):
  if not p.is_file() or '__pycache__' in p.parts or p.suffix in ['.pyc','.zip'] or p.name in ['bundle_manifest.json','postprocess_status.json']:continue
  add(p,prefix+'/'+str(p.relative_to(root)))
tree(HERE.parent,'paper/revisionPlan/anticipation2026')
tree(HERE.parent.parent/'rerun2026','paper/revisionPlan/rerun2026')
for factor in [1,2,4,7]:
 folder=RUN/f'factor-{factor}';tree(folder,f'native/factor-{factor}')
 worker=read(folder/'process.json')['worker']
 add(RUN/f'worker-{worker}/TestProject/Content/Level/BP_Tile.uasset',f'assets/tiles/factor-{factor}/BP_Tile.uasset')
add(SOURCE/'Saved/AnticipationRetrain20261025/HRL/TestProject/Content/Level/BP_Tile.uasset','assets/tiles/factor-0/BP_Tile.uasset')
comparison=read(EXPORT/'comparison.json')
for order,label in [('cdr','CDR-factor-0'),('ccc','CCC')]:
 tree(Path(comparison['HRL'][order]['metrics']).parent,'native/'+label+'/TrialResults')
catalog=read(EXPORT/'selected_policy_catalog.json')
for kind,x in catalog['policies']['HRL']['snapshots'].items():
 path=EXPORT/x['file'];assert sha(path)==x['sha256'];add(path,'models/HRL/'+path.name)
add(EXPORT/'policies/HRL/training_manifest.json','models/HRL/training_manifest.json')
add(EXPORT/'selected_policy_catalog.json','models/selected_policy_catalog.json')
agent=SOURCE/'Content/Agent/BP_Agent.uasset';assert sha(agent)==catalog['anticipation_asset_sha256']
add(agent,'assets/Agent/BP_Agent.uasset')
for name in ['protocol.json','complete.json','source_preservation.json','parallel_extension.json']:
 add(RUN/name,'native/'+name)
for name in ['count_rule_validation.json','audit.stdout','audit.log','commandlet-attempt-audit.stdout','commandlet-attempt-audit.log','attempt-1-audit.stdout','attempt-1-audit.log']:
 path=RUN/'count-audit'/name
 if path.exists():add(path,'native/count-audit/'+name)
entries=[dict(path=name,bytes=path.stat().st_size,sha256=sha(path)) for name,path in sorted(files.items())]
archive=HERE/'hrl-traversal-factor-results.zip';assert not archive.exists(),'Preserve the existing archive before repackaging'
partial=archive.with_suffix('.partial.zip')
guide='''HRL traversal-factor results, 26 October 2026

Read paper/revisionPlan/anticipation2026/plasticity/RESULTS.md.
To reproduce the statistics and figures, change into paper/ and follow the
commands in that folder's README.md. Python stdlib and base R are sufficient.
All six HRL raw result sets, including compressed scene records and captured
inference snapshots, are in native/. Models and repaired/factor-specific asset
overrides are included. These overrides require the original Unreal project
and Unreal Engine 5.5.4 to run; this archive is not a standalone Unreal project.
File-manifest.json records every archived source file's SHA-256 and size.
Only source files and generated analysis are packaged; original inputs are not
modified. Native setup-audit failures are retained alongside the successful
17-check handler audit and are separate from scored trial data.
'''
with zipfile.ZipFile(partial,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name,path in sorted(files.items()):z.write(path,name,compress_type=zipfile.ZIP_STORED if path.suffix=='.gz' else zipfile.ZIP_DEFLATED)
 z.writestr('README.txt',guide);z.writestr('file-manifest.json',json.dumps(entries,indent=2)+'\n')
with zipfile.ZipFile(partial) as z:
 assert z.testzip() is None
 assert len(z.namelist())==len(entries)+2
partial.replace(archive)
manifest=dict(created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),path=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(entries)+2,crc_verified=True)
(HERE/'bundle_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest,indent=2))
