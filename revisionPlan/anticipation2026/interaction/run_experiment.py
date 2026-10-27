"""Run the two author-approved missing cells of the 2 x 3 HRL experiment."""
from pathlib import Path
import concurrent.futures,gzip,hashlib,importlib.util,json,shutil,subprocess,sys,traceback

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('native_base',HERE.parent/'recanalization/run_experiment.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
RUN=Path('/private/tmp/anticipation-interaction-20261026')
base.RUN=RUN
SOURCE=base.SOURCE;EXPORT=base.EXPORT
read=base.read;write=base.write;sha=base.sha
CONDITIONS={'k7-zero':(0.,True),'k7-keep':(1.,False)}

def prepare():
    RUN.mkdir(parents=True,exist_ok=True)
    catalog=read(EXPORT/'selected_policy_catalog.json')
    assert sha(SOURCE/'Content/Agent/BP_Agent.uasset')==catalog['anticipation_asset_sha256']
    paths=[SOURCE/p for p in ['Content/Level/BP_Tile.uasset','Content/Agent/BP_Agent.uasset',
           'Content/Agent/BP_GameMode.uasset','Content/Level/Landscape.umap','Content/Learning/BP_AgentManager.uasset']]
    if not (RUN/'source_preservation.json').exists():write(RUN/'source_preservation.json',{str(p):sha(p) for p in paths})
    for p,h in read(RUN/'source_preservation.json').items():assert sha(p)==h
    original=RUN/'BP_Tile.original.json'
    if not original.exists():base.asset_command('export',SOURCE/'Content/Level/BP_Tile.uasset',original)
    if not (RUN/'protocol.json').exists():
        write(RUN/'protocol.json',dict(created_at=base.stamp(),family='HRL',fixed_policy=catalog['policies']['HRL'],
            new_conditions={n:dict(factor=7,retain=r,floor=f) for n,(r,f) in CONDITIONS.items()},
            factors=[1,7],retention_rules=['zero','half-floor','keep'],trials_per_cell=250,
            seed=10001,phases=3,decisions_per_phase=2000,dt=.05,pre_post_entry_increment=1,
            analysis_plan_sha256=sha(HERE/'ANALYSIS_PLAN.md'),
            primary='Differences of 7-minus-1 effects across retention rules; six-test interaction Holm family',
            main_paper_condition='k1-half-floor',no_policy_retraining=True))
    assert sha(HERE/'ANALYSIS_PLAN.md')==read(RUN/'protocol.json')['analysis_plan_sha256']
    for name in ['configure.py','validate_native.py','runtime.py','launch_validation.py','run_experiment.py','ANALYSIS_PLAN.md']:
        target=RUN/name
        if not target.exists():shutil.copy2(HERE/name,target)
        else:assert target.read_bytes()==(HERE/name).read_bytes(),'Executed source copy changed: '+name
    shutil.copy2(HERE.parent/'recanalization/run_experiment.py',RUN/'native_base.py')
    for name,(retain,floor) in CONDITIONS.items():
        output=RUN/(name+'.json')
        if not output.exists():
            args=[sys.executable,str(HERE.parent/'recanalization/patch_tile.py'),str(original),str(output),
                  '--retain',str(retain),'--helpers',str(SOURCE/'analysis/timing')]
            if not floor:args.append('--exact')
            subprocess.run(args,check=True)
    return catalog

def configure(worker,name,catalog):
    dest=RUN/name;dest.mkdir(exist_ok=True)
    if (dest/'verified.json').exists():return
    p=base.project(worker);(p/'INTERACTION_EVALUATION_COPY').write_text('Approved HRL rate x retention interaction evaluation.\n')
    results=p/'Saved/TrialResults'
    assert not results.exists() or not any(results.iterdir()),'Preserve and inspect existing scored data'
    retain,floor=CONDITIONS[name]
    snapshots={k:dict(path=str(EXPORT/v['file']),sha256=v['sha256']) for k,v in catalog['policies']['HRL']['snapshots'].items()}
    for s in snapshots.values():assert sha(s['path'])==s['sha256']
    write(p/'evaluation_settings.json',dict(condition=name,factor=7,retain=retain,floor=floor,trials=250,snapshots=snapshots))
    manifest=read(EXPORT/'policies/HRL/training_manifest.json');manifest.pop('held_out_selection',None)
    write(p/'Content/Python/trial_training_manifests.json',[manifest])
    base.asset_command('import',RUN/(name+'.json'),p/'Content/Level/BP_Tile.uasset')
    base.native(p,dest,'configure.py','configure','compile',300)
    assert 'RECANALIZATION_CONFIGURED '+name in (dest/'configure.stdout').read_text(errors='replace')
    tile=p/'Content/Level/BP_Tile.uasset';h=sha(tile)
    shutil.copy2(tile,dest/'BP_Tile.compiled.uasset')
    base.native(p,dest,'launch_validation.py','native_audit','audit',240)
    audit=read(p.parent/'native_validation.json')
    assert audit['passed'] and audit['condition']==name and len(audit['tests'])==15
    assert sha(tile)==h,'Transient validation edits were saved'
    audit.update(asset_sha256=h,asset_unchanged_after_audit=True)
    write(dest/'native_validation.json',audit)
    print('NATIVE_VALIDATED '+name,flush=True)

def evaluate(worker,name,catalog):
    dest=RUN/name
    if (dest/'verified.json').exists():return read(dest/'verified.json')
    p=RUN/f'worker-{worker}/TestProject';settings=read(p/'evaluation_settings.json')
    assert settings['condition']==name and settings['factor']==7 and settings['trials']==250
    for filename in ['runtime_result.json','live.json']:
        path=p.parent/filename
        if path.exists():path.unlink()
    print('START '+name+' 250 trials '+base.stamp(),flush=True)
    base.native(p,dest,'runtime.py','evaluation')
    if (p.parent/'runtime_result.json').exists():assert read(p.parent/'runtime_result.json')['passed']
    results=p/'Saved/TrialResults';paths=list(results.glob('*.metrics.json'));assert len(paths)==1
    metric=paths[0];data=read(metric);v=data['provenance']
    receipt=read(metric.with_name(metric.name.replace('.metrics.json','.completed.json')))
    assert receipt['results_saved'] and receipt['trials_completed']==receipt['trials_requested']==250
    assert data['status']=='complete' and len(data['trials'])==250
    tilehash=sha(dest/'BP_Tile.compiled.uasset')
    assert sha(p/'Content/Level/BP_Tile.uasset')==tilehash==v['asset-sha256']['Level/BP_Tile']
    assert v['asset-sha256']['Agent/BP_Agent']==catalog['anticipation_asset_sha256']
    e=v['environment'];assert e['IsHRL'] and e['TrialSequenceOrder']=='cdr'
    assert e['TrialEnvironmentSeed']==e['ActiveEnvironmentSeed']==10001
    assert v['simulation-dt-seconds']==.05 and v['phase-decision-ticks']==2000
    models=0;scenes=0;totals={1:[],2:[],3:[]}
    for k,s in v['snapshots'].items():
        assert sha(results/s['loaded-snapshot'])==s['loaded-sha256']==settings['snapshots'][k]['sha256'];models+=1
    for trial in data['trials']:
        assert [phase['sequence-idx'] for phase in trial['phases']]==[1,2,3]
        for phase in trial['phases']:
            assert phase['complete'] and phase['decision-ticks']==2000 and phase['duration-seconds']==100
            blob=gzip.decompress((results/phase['scene-file']).read_bytes())
            assert hashlib.sha256(blob).hexdigest()==phase['scene-sha256']
            scene=json.loads(blob);assert len(scene['tiles'])==2500
            assert all(t['DecanalizationRateFactor']==7 and t['OverlapCount']>=0 for t in scene['tiles'])
            totals[phase['sequence-idx']].append(sum(t['OverlapCount'] for t in scene['tiles']));scenes+=1
    target=dest/'TrialResults';shutil.move(str(results),target);results.mkdir()
    retain,floor=CONDITIONS[name]
    report=dict(passed=True,condition=name,factor=7,retain=retain,floor=floor,trials=250,
        phases=750,decisions=1500000,metrics=str(target/metric.name),metrics_sha256=sha(target/metric.name),
        tile_asset_sha256=tilehash,scene_hashes_verified=scenes,loaded_models_verified=models,
        tile_count_totals_by_phase={k:dict(mean=sum(a)/len(a),min=min(a),max=max(a)) for k,a in totals.items()},
        finished_at=base.stamp())
    write(dest/'verified.json',report)
    print('VERIFIED '+name,flush=True)
    return report

def main():
    catalog=prepare()
    if '--prepare-only' in sys.argv:return
    # Serial editor startup avoids the previous concurrent-editor setup stall.
    for worker,name in enumerate(CONDITIONS):configure(worker,name,catalog)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(evaluate,i,n,catalog) for i,n in enumerate(CONDITIONS)]
        reports=[f.result() for f in futures]
    for path,h in read(RUN/'source_preservation.json').items():assert sha(path)==h
    write(RUN/'complete.json',dict(passed=True,conditions=reports,source_preserved=True,finished_at=base.stamp()))
    print('INTERACTION_NATIVE_COMPLETE',flush=True)
if __name__=='__main__':
    try:main()
    except Exception:
        if RUN.exists():write(RUN/'failure.json',dict(error=traceback.format_exc(),at=base.stamp()))
        raise
