"""Evaluate approved post-decanalization transforms in isolated Unreal projects."""
from pathlib import Path
import argparse,concurrent.futures,datetime,gzip,hashlib,json,os,shutil,subprocess,sys,traceback

HERE=Path(__file__).resolve().parent
SOURCE=Path('/Users/jingo/Work/PhD/Dissertation Project/decanalization')
EXPORT=SOURCE/'analysis/anticipation-retrained-2026-10-25'
OLD=SOURCE/'Saved/AnticipationRetrain20261025'
RUN=Path('/private/tmp/anticipation-recanalization-20261026')
EXE=Path('/Users/Shared/Epic Games/UE_5.5/Engine/Binaries/Mac/UnrealEditor-Cmd')
DOTNET=Path('/Users/Shared/Epic Games/UE_5.5/Engine/Binaries/ThirdParty/DotNet/8.0.300/mac-arm64/dotnet')
ASSETCLI=Path('/private/tmp/anticipation-fix/bin/AssetAudit.dll')
CONDITIONS={'zero':(0.,True),'quarter-floor':(.25,True),'three-quarter-floor':(.75,True),
            'keep':(1.,False),'half-exact':(.5,False)}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
def write(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2)+'\n');tmp.replace(path)
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def asset_command(*args):
    env=dict(os.environ,DOTNET_CLI_HOME=str(RUN/'dotnet-home'),DOTNET_SKIP_FIRST_TIME_EXPERIENCE='1')
    subprocess.run([str(DOTNET),str(ASSETCLI),*map(str,args)],check=True,env=env)
def prepare():
    RUN.mkdir(parents=True,exist_ok=True)
    catalog=read(EXPORT/'selected_policy_catalog.json')
    assert sha(SOURCE/'Content/Agent/BP_Agent.uasset')==catalog['anticipation_asset_sha256']
    sourcefiles=[SOURCE/p for p in ['Content/Level/BP_Tile.uasset','Content/Agent/BP_Agent.uasset',
                 'Content/Agent/BP_GameMode.uasset','Content/Level/Landscape.umap','Content/Learning/BP_AgentManager.uasset']]
    if not (RUN/'source_preservation.json').exists():
        write(RUN/'source_preservation.json',{str(p):sha(p) for p in sourcefiles})
    for path,h in read(RUN/'source_preservation.json').items():assert sha(path)==h
    original=RUN/'BP_Tile.original.json'
    if not original.exists():asset_command('export',SOURCE/'Content/Level/BP_Tile.uasset',original)
    if not (RUN/'protocol.json').exists():
        write(RUN/'protocol.json',dict(created_at=stamp(),family='HRL',fixed_policy=catalog['policies']['HRL'],
            conditions={k:dict(retain=v[0],floor=v[1]) for k,v in CONDITIONS.items()},
            reused_conditions=['half-floor: factor-1 CDR','CCC'],trials_per_condition=250,
            entry_increment_all_phases=1,seed=10001,phases=3,decisions_per_phase=2000,dt=.05,
            analysis_plan_sha256=sha(HERE/'ANALYSIS_PLAN.md'),
            primary_family='six CDR conditions versus CCC, phase-3 MAE/reward, 12-test Holm',
            selection='Author-approved transforms before new outcomes; no retraining or best-condition primary replacement'))
    assert sha(HERE/'ANALYSIS_PLAN.md')==read(RUN/'protocol.json')['analysis_plan_sha256']
    for name in ['configure.py','runtime.py','validate_native.py','launch_validation.py','patch_tile.py','run_experiment.py','ANALYSIS_PLAN.md']:
        target=RUN/name
        if not target.exists() or target.read_bytes()!=(HERE/name).read_bytes():shutil.copy2(HERE/name,target)
    for name,(retain,floor) in CONDITIONS.items():
        output=RUN/(name+'.json')
        if not output.exists():
            args=[sys.executable,str(HERE/'patch_tile.py'),str(original),str(output),'--retain',str(retain),
                  '--helpers',str(SOURCE/'analysis/timing')]
            if not floor:args.append('--exact')
            subprocess.run(args,check=True)
    return catalog
def project(worker):
    p=RUN/f'worker-{worker}'/'TestProject'
    if not p.exists():
        p.mkdir(parents=True)
        template=OLD/'HRL/TestProject'
        for folder in ['Content','Config','analysis/homeostatic','analysis/trial_metrics','analysis/timing']:
            shutil.copytree(template/folder,p/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.DS_Store'))
        shutil.copy2(template/'ue_canalization.uproject',p/'ue_canalization.uproject')
        (p/'RECANALIZATION_EVALUATION_COPY').write_text('Disposable author-approved post-decanalization comparison.\n')
        (p/'Intermediate').mkdir()
        (p/'Intermediate/PipInstall').symlink_to(OLD/'python-env',target_is_directory=True)
    assert (p/'RECANALIZATION_EVALUATION_COPY').exists()
    return p
def command(p,script,log,mode='game'):
    if mode=='compile':flags=['-run=pythonscript','-script='+str(RUN/script),'-nullrhi']
    elif mode=='audit':flags=['-ExecCmds=py '+str(RUN/script)]
    else:flags=['/Game/Level/Landscape','-game','-ExecCmds=py '+str(RUN/script),
                '-EnablePlugins=PythonScriptPlugin','-UseFixedTimeStep','-FPS=20','-FixedSeed',
                '-NoVSync','-NoTrialCompletionDialog','-nullrhi']
    return [str(EXE),str(p/'ue_canalization.uproject'),*flags,'-DisablePipInstall','-nosound',
            '-unattended','-nop4','-stdout','-FullStdOutLogOutput','-abslog='+str(log)]
def native(p,dest,script,label,mode='game',timeout=14700):
    args=command(p,script,dest/(label+'.log'),mode)
    with (dest/(label+'.stdout')).open('w') as out:
        process=subprocess.Popen(args,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
        write(dest/(label+'_process.json'),dict(pid=process.pid,arguments=args,started_at=stamp()))
        try:code=process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill();process.wait(timeout=15)
            raise
    assert code==0,(label,code,(dest/(label+'.stdout')).read_text(errors='replace')[-3000:])
    if mode in ['compile','audit']:
        text=(dest/(label+'.stdout')).read_text(errors='replace')
        assert 'LogBlueprint: Error:' not in text and 'LogPython: Error:' not in text,text[-4000:]
def evaluate(worker,name,catalog,trials=250):
    dest=RUN/('smoke-'+name if trials!=250 else name);dest.mkdir(exist_ok=True)
    if (dest/'verified.json').exists():return read(dest/'verified.json')
    p=project(worker);results=p/'Saved/TrialResults'
    assert not results.exists() or not any(results.iterdir()),'Unarchived trial data must be inspected'
    snapshots={k:dict(path=str(EXPORT/v['file']),sha256=v['sha256']) for k,v in catalog['policies']['HRL']['snapshots'].items()}
    for s in snapshots.values():assert sha(s['path'])==s['sha256']
    retain,floor=CONDITIONS[name]
    settings=dict(condition=name,retain=retain,floor=floor,trials=trials,snapshots=snapshots)
    write(p/'evaluation_settings.json',settings)
    manifest=read(EXPORT/'policies/HRL/training_manifest.json');manifest.pop('held_out_selection',None)
    write(p/'Content/Python/trial_training_manifests.json',[manifest])
    asset_command('import',RUN/(name+'.json'),p/'Content/Level/BP_Tile.uasset')
    native(p,dest,'configure.py','configure','compile',300)
    assert 'RECANALIZATION_CONFIGURED '+name in (dest/'configure.stdout').read_text(errors='replace')
    tile=p/'Content/Level/BP_Tile.uasset';tilehash=sha(tile)
    shutil.copy2(tile,dest/'BP_Tile.compiled.uasset')
    native(p,dest,'launch_validation.py','native_audit','audit',240)
    report=read(p.parent/'native_validation.json')
    assert report['passed'] and report['condition']==name and len(report['tests'])==15
    assert sha(tile)==tilehash,'Transient audit changes were saved'
    report['asset_sha256']=tilehash;report['asset_unchanged_after_audit']=True
    write(dest/'native_validation.json',report)
    for filename in ['runtime_result.json','live.json']:
        path=p.parent/filename
        if path.exists():path.unlink()
    print('START '+name+' '+str(trials)+' trials '+stamp(),flush=True)
    native(p,dest,'runtime.py','evaluation')
    # The native completion handler can quit before the next observer tick.
    # Durable native receipts are authoritative; observer failure is still fatal.
    if (p.parent/'runtime_result.json').exists():assert read(p.parent/'runtime_result.json')['passed']
    return verify_and_archive(p,dest,name,catalog,settings)
def verify_and_archive(p,dest,name,catalog,settings):
    results=p/'Saved/TrialResults';trials=settings['trials']
    snapshots=settings['snapshots'];retain=settings['retain'];floor=settings['floor']
    tilehash=sha(dest/'BP_Tile.compiled.uasset')
    audit=read(dest/'native_validation.json')
    assert audit['passed'] and audit['asset_sha256']==tilehash
    assert sha(p/'Content/Level/BP_Tile.uasset')==tilehash
    paths=list(results.glob('*.metrics.json'));assert len(paths)==1
    metric=paths[0];data=read(metric);v=data['provenance']
    receipt=read(metric.with_name(metric.name.replace('.metrics.json','.completed.json')))
    assert receipt['results_saved'] and receipt['trials_completed']==receipt['trials_requested']==trials
    assert data['status']=='complete' and len(data['trials'])==trials
    assert v['asset-sha256']['Agent/BP_Agent']==catalog['anticipation_asset_sha256']
    assert v['asset-sha256']['Level/BP_Tile']==tilehash
    assert v['environment']['IsHRL'] and v['environment']['TrialSequenceOrder']=='cdr'
    assert v['environment']['TrialEnvironmentSeed']==v['environment']['ActiveEnvironmentSeed']==10001
    assert v['simulation-dt-seconds']==.05 and v['phase-decision-ticks']==2000
    models=0;scenes=0;totals={1:[],2:[],3:[]};fractional={1:0,2:0,3:0}
    for k,s in v['snapshots'].items():
        assert sha(results/s['loaded-snapshot'])==s['loaded-sha256']==snapshots[k]['sha256'];models+=1
    for trial in data['trials']:
        assert [phase['sequence-idx'] for phase in trial['phases']]==[1,2,3]
        for phase in trial['phases']:
            assert phase['complete'] and phase['decision-ticks']==2000 and phase['duration-seconds']==100
            blob=gzip.decompress((results/phase['scene-file']).read_bytes())
            assert hashlib.sha256(blob).hexdigest()==phase['scene-sha256']
            scene=json.loads(blob);assert len(scene['tiles'])==2500
            assert all(t['DecanalizationRateFactor']==1 for t in scene['tiles'])
            counts=[t['OverlapCount'] for t in scene['tiles']]
            assert all(c>=0 for c in counts)
            totals[phase['sequence-idx']].append(sum(counts))
            fractional[phase['sequence-idx']]+=sum(c!=int(c) for c in counts)
            scenes+=1
    target=dest/'TrialResults';shutil.move(str(results),target);results.mkdir()
    report=dict(passed=True,condition=name,retain=retain,floor=floor,trials=trials,phases=3*trials,
                decisions=6000*trials,metrics=str(target/metric.name),metrics_sha256=sha(target/metric.name),
                tile_asset_sha256=tilehash,scene_hashes_verified=scenes,loaded_models_verified=models,
                fractional_tile_counts_by_phase=fractional,
                tile_count_totals_by_phase={k:dict(mean=sum(a)/len(a),min=min(a),max=max(a)) for k,a in totals.items()},
                finished_at=stamp())
    write(dest/'verified.json',report)
    print('VERIFIED '+name+' '+json.dumps(report),flush=True)
    return report
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--smoke',action='store_true');parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args();catalog=prepare()
    if args.prepare_only:return
    if args.smoke:evaluate(0,'half-exact',catalog,1);return
    def worker(i,names):return [evaluate(i,n,catalog) for n in names]
    names=list(CONDITIONS);workers=min(args.workers,len(names))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures=[pool.submit(worker,i,names[i::workers]) for i in range(workers)]
        reports=[r for f in futures for r in f.result()]
    for path,h in read(RUN/'source_preservation.json').items():assert sha(path)==h,'Production source changed: '+path
    write(RUN/'complete.json',dict(passed=True,conditions=reports,source_preserved=True,finished_at=stamp()))
    print('RECANALIZATION_COMPLETE',flush=True)
if __name__=='__main__':
    try:main()
    except Exception:
        if RUN.exists():write(RUN/'failure.json',dict(error=traceback.format_exc(),at=stamp()))
        raise
