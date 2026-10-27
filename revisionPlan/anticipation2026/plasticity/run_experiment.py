"""Frozen-HRL traversal-factor experiment in isolated native Unreal copies.

The source project and its model/default settings are read-only inputs. Resume
checks durable receipts rather than treating exit as a successful experiment.
"""
from pathlib import Path
import argparse,concurrent.futures,datetime,gzip,hashlib,json,os,shutil,subprocess,time,traceback
HERE=Path(__file__).resolve().parent
SOURCE=Path('/Users/jingo/Work/PhD/Dissertation Project/decanalization')
OLD=SOURCE/'Saved/AnticipationRetrain20261025'
EXPORT=SOURCE/'analysis/anticipation-retrained-2026-10-25'
RUN=SOURCE/'Saved/AnticipationPlasticity20261026'
EXE=Path('/Users/Shared/Epic Games/UE_5.5/Engine/Binaries/Mac/UnrealEditor-Cmd')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
def write(p,obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2)+'\n');tmp.replace(p)
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def prepare():
 RUN.mkdir(parents=True,exist_ok=True)
 catalog=read(EXPORT/'selected_policy_catalog.json')
 assert sha(SOURCE/'Content/Agent/BP_Agent.uasset')==catalog['anticipation_asset_sha256']
 sourcefiles=[SOURCE/'Content/Level/BP_Tile.uasset',SOURCE/'Content/Agent/BP_Agent.uasset',SOURCE/'Content/Agent/BP_GameMode.uasset',SOURCE/'Content/Level/Landscape.umap',SOURCE/'Content/Learning/BP_AgentManager.uasset']
 if not (RUN/'source_preservation.json').exists():write(RUN/'source_preservation.json',{str(p):sha(p) for p in sourcefiles})
 write(RUN/'protocol.json',dict(created_at=stamp(),family='HRL',fixed_policy=catalog['policies']['HRL'],
      factors=[0,1,2,4,7],new_factors=[1,2,4,7],trials_per_factor=250,baseline_conditions=['CDR-factor-0','CCC'],
      baseline_source=str(EXPORT/'comparison.json'),seed=10001,phases=3,decisions_per_phase=2000,dt=.05,
      primary='phase-3 event/update-sampled mean absolute homeostatic state',secondary=['actual objective reward','population SD','fraction within +/-5'],
      comparisons='Each new factor versus factor 0 and CCC; Welch primary; matched-ID and baseline-change sensitivity; Holm across 8 contrasts x 2 main outcomes',
      selection='Factors fixed before new runs; no policy selection or retraining; no best-factor confirmatory claim'))
 for i in [0,1]:
  p=RUN/f'worker-{i}'/'TestProject'
  if not p.exists():
   p.mkdir(parents=True)
   template=OLD/'HRL/TestProject'
   for folder in ['Content','Config','analysis/homeostatic','analysis/trial_metrics','analysis/timing']:
    shutil.copytree(template/folder,p/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.DS_Store'))
   shutil.copy2(template/'ue_canalization.uproject',p/'ue_canalization.uproject')
   (p/'PLASTICITY_EVALUATION_COPY').write_text('Isolated frozen-policy traversal-factor evaluation.\n')
   (p/'Intermediate').mkdir();(p/'Intermediate/PipInstall').symlink_to(OLD/'python-env',target_is_directory=True)
   assert sha(p/'Content/Agent/BP_Agent.uasset')==catalog['anticipation_asset_sha256']
 for name in ['configure.py','runtime.py','run_experiment.py']:shutil.copy2(HERE/name,RUN/name)
 return catalog
def command(project,script,log,compile=False):
 if compile:
  flags=['-run=pythonscript','-script='+str(RUN/script)]
 else:flags=['/Game/Level/Landscape','-game','-ExecCmds=py '+str(RUN/script),'-EnablePlugins=PythonScriptPlugin','-UseFixedTimeStep','-FPS=20','-FixedSeed','-NoVSync','-NoTrialCompletionDialog']
 return [str(EXE),str(project/'ue_canalization.uproject'),*flags,'-DisablePipInstall','-nullrhi','-nosound','-unattended','-nop4','-stdout','-FullStdOutLogOutput','-abslog='+str(log)]
def evaluate(worker,factor,catalog,trials=250):
 dest=RUN/(f'factor-{factor}' if trials==250 else f'smoke-factor-{factor}');dest.mkdir(exist_ok=True)
 if (dest/'verified.json').exists():return read(dest/'verified.json')
 p=RUN/f'worker-{worker}'/'TestProject';results=p/'Saved/TrialResults'
 assert not results.exists() or not any(results.iterdir()),'Unarchived evaluation data must be inspected before continuing'
 snapshots={k:dict(path=str(EXPORT/v['file']),sha256=v['sha256']) for k,v in catalog['policies']['HRL']['snapshots'].items()}
 for s in snapshots.values():assert sha(s['path'])==s['sha256']
 write(p/'evaluation_settings.json',dict(factor=factor,trials=trials,snapshots=snapshots))
 manifest=read(EXPORT/'policies/HRL/training_manifest.json');manifest.pop('held_out_selection',None)
 write(p/'Content/Python/trial_training_manifests.json',[manifest])
 with (dest/'configure.stdout').open('w') as out:
  result=subprocess.run(command(p,'configure.py',dest/'configure.log',True),stdout=out,stderr=subprocess.STDOUT,timeout=300)
 text=(dest/'configure.stdout').read_text(errors='replace')
 assert result.returncode==0 and 'PLASTICITY_CONFIGURED' in text and 'LogBlueprint: Error:' not in text and 'LogPython: Error:' not in text,text[-4000:]
 for name in ['runtime_result.json','live.json']:
  path=p.parent/name
  if path.exists():path.unlink()
 args=command(p,'runtime.py',dest/'evaluation.log')
 with (dest/'evaluation.stdout').open('w') as out:
  process=subprocess.Popen(args,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
  write(dest/'process.json',dict(pid=process.pid,worker=worker,arguments=args,started_at=stamp()))
  print(f'Started factor {factor}, {trials} trials, PID {process.pid}',flush=True)
  try:code=process.wait(timeout=14700)
  except subprocess.TimeoutExpired:process.terminate();raise
 paths=list(results.glob('*.metrics.json'));assert len(paths)==1
 metric=paths[0];data=read(metric);v=data['provenance']
 receipt=read(metric.with_name(metric.name.replace('.metrics.json','.completed.json')))
 assert code==0 and receipt['results_saved'] and receipt['trials_completed']==receipt['trials_requested']==trials
 assert data['status']=='complete' and len(data['trials'])==trials
 assert v['asset-sha256']['Agent/BP_Agent']==catalog['anticipation_asset_sha256']
 assert v['environment']['IsHRL'] and v['environment']['TrialSequenceOrder']=='cdr'
 assert v['environment']['TrialEnvironmentSeed']==v['environment']['ActiveEnvironmentSeed']==10001
 assert v['simulation-dt-seconds']==.05 and v['phase-decision-ticks']==2000
 models=0;scenes=0;totals={1:[],2:[],3:[]}
 for k,s in v['snapshots'].items():
  assert sha(results/s['loaded-snapshot'])==s['loaded-sha256']==snapshots[k]['sha256'];models+=1
 for trial in data['trials']:
  assert [p['sequence-idx'] for p in trial['phases']]==[1,2,3]
  for phase in trial['phases']:
   assert phase['complete'] and phase['decision-ticks']==2000 and phase['duration-seconds']==100
   blob=gzip.decompress((results/phase['scene-file']).read_bytes())
   assert hashlib.sha256(blob).hexdigest()==phase['scene-sha256']
   scene=json.loads(blob);assert len(scene['tiles'])==2500
   assert all(t['DecanalizationRateFactor']==factor for t in scene['tiles'])
   totals[phase['sequence-idx']].append(sum(t['OverlapCount'] for t in scene['tiles']));scenes+=1
 target=dest/'TrialResults';shutil.move(str(results),target);results.mkdir()
 report=dict(passed=True,factor=factor,trials=trials,phases=3*trials,decisions=6000*trials,metrics=str(target/metric.name),metrics_sha256=sha(target/metric.name),
             scene_hashes_verified=scenes,loaded_models_verified=models,tile_count_totals_by_phase={k:dict(mean=sum(a)/len(a),min=min(a),max=max(a)) for k,a in totals.items()},finished_at=stamp())
 write(dest/'verified.json',report);print('VERIFIED '+json.dumps(report),flush=True)
 return report
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--smoke',action='store_true');args=parser.parse_args()
 catalog=prepare()
 if args.smoke:
  evaluate(0,1,catalog,1);return
 def worker(i,factors):return [evaluate(i,f,catalog) for f in factors]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  futures=[pool.submit(worker,0,[1,4]),pool.submit(worker,1,[2,7])]
  results=[r for f in futures for r in f.result()]
 for path,h in read(RUN/'source_preservation.json').items():assert sha(path)==h,'Source modified: '+path
 write(RUN/'complete.json',dict(passed=True,conditions=results,source_preserved=True,finished_at=stamp()))
 print('PLASTICITY_COMPLETE',flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if RUN.exists():write(RUN/'failure.json',dict(error=traceback.format_exc(),at=stamp()))
  raise
