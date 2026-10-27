"""Matched 100-second comparison: reset versus carry world state on updates."""
from pathlib import Path
from dataclasses import replace
import argparse,csv,gzip,hashlib,json,os,shutil,statistics,subprocess,sys,time,traceback

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import compare as previous
import share_scratch_storage as storage
native=previous.native
from profiles import BASE,load_profile
from study import Selector

CANDIDATE=replace(BASE,name='canalization-100s-persistent',reset_world_on_update=False).validate()

def status(stage,**details):
    native.write(HERE/'status.json',dict(stage=stage,updated_at=native.stamp(),**details))
    print(stage+' '+json.dumps(details),flush=True)

def prepare_protocol():
    old=previous.protocol();root=Path(old['raw_root'])
    differences={k:[BASE.contract()[k],v] for k,v in CANDIDATE.contract().items() if BASE.contract()[k]!=v}
    assert set(differences)=={'name','reset_world_on_update'}
    for name,digest in old['source_sha256'].items():assert native.sha(native.HERE/name)==digest,name
    for seed in old['training_seeds']:
        folder=root/f'canalization-baseline-{seed}'
        assert native.read(folder/'selection.json').get('complete',False)
        assert native.read(folder/'training_verified.json')['passed']
        checkpoint=native.read(folder/'selection.json')['best']['checkpoint']
        assert checkpoint['profile']==BASE.contract()
        assert checkpoint['policy_seed']==seed and checkpoint['environment_seed']==100000+seed
    assert native.source_files()==native.read(root/'source_preservation.json')
    p=dict(purpose='Only disable world resets on policy updates during 100-second training; no promotion',
        raw_root=str(root),conditions=['baseline',CANDIDATE.name],
        profiles={'baseline':BASE.contract(),CANDIDATE.name:CANDIDATE.contract()},
        manipulated_setting='reset_world_on_update',profile_differences=differences,
        training_seeds=old['training_seeds'],training_environment_seeds=old['training_environment_seeds'],
        maximum_transitions_per_policy=old['maximum_transitions_per_policy'],
        minimum_gathers=old['minimum_gathers'],checkpoint_every_gathers=old['checkpoint_every_gathers'],
        plateau_patience=old['plateau_patience'],selection_trials=old['selection_trials'],
        selection_environment_seed=old['selection_environment_seed'],material_improvement_fraction=.005,
        comparison_trials=old['comparison_trials'],comparison_environment_seed=old['comparison_environment_seed'],
        reserved_final_environment_seed=old['reserved_final_environment_seed'],
        metric=old['metric'],secondary=old['secondary'],count_increment=1,
        post_decanalization_retention='Existing half-floor rule; this screen evaluates continuous CCC only',
        baseline_training='Reuse completed seeds and their selected checkpoints from the frozen screen',
        training_completion='Same plateau rule and maximum budget; actual collected transitions may differ',
        inference='Three paired training seeds; repeated evaluation trials do not add training replicates',
        scope='Entire world state carries across policy updates. Timed/failure resets remain. Not tile-only retention or cross-episode persistence.',
        evaluation_boundary_details=old['evaluation_boundary_details'],
        causal_limit=old['causal_limit'],source_sha256=old['source_sha256'],
        baseline_receipts={str(seed):{name:native.sha(root/f'canalization-baseline-{seed}'/name)
            for name in ['selection.json','training_verified.json','trainer_complete.json']}
            for seed in old['training_seeds']},
        orchestration_sha256={str(path.relative_to(HERE.parent)):native.sha(path)
            for path in [Path(__file__),HERE/'plot.py',HERE.parent/'compare.py',HERE.parent/'share_scratch_storage.py']})
    target=HERE/'protocol.json'
    if target.exists():assert native.read(target)==p,'Started comparison contract changed'
    else:native.write(target,p)
    return p

def ensure_space():
    storage.main()
    free=shutil.disk_usage('/private/tmp').free
    if free<6*1024**3:raise RuntimeError(f'Need 6 GiB free for isolated training and checkpoint evaluation; have {free/1024**3:.2f}')

def train_candidates(p):
    root=Path(p['raw_root']);profile=load_profile(p['profiles'][CANDIDATE.name])
    for seed in p['training_seeds']:
        label=f'history100-{CANDIDATE.name}-{seed}';folder=root/label
        if (folder/'selection.json').exists() and native.read(folder/'selection.json').get('complete',False):
            assert native.read(folder/'training_verified.json')['passed'];continue
        assert not folder.exists(),'Inspect incomplete candidate before explicitly retrying: '+label
        ensure_space();status('training',training_seed=seed,run=label)
        selector=Selector(p['minimum_gathers'],p['plateau_patience'],p['material_improvement_fraction'])
        def callback(checkpoint):
            result=native.evaluate(root,label+'-validation-'+str(checkpoint['gathers']),profile,checkpoint,
                p['selection_trials'],p['selection_environment_seed'],continuous=True)
            stop=selector.update(result);native.write(folder/'selection.json',selector.record());return stop
        native.train(root,label,profile,seed,100000+seed,
            p['maximum_transitions_per_policy']//10000,p['checkpoint_every_gathers'],48720,callback)
        record=dict(**selector.record(),complete=True,termination=native.read(folder/'trainer_complete.json')['reason'])
        assert record['best'];native.write(folder/'selection.json',record)
        baseline=root/f'canalization-baseline-{seed}'
        for kind in ['policy','critic','encoder','decoder']:
            assert native.sha(folder/'initial'/(kind+'.bin'))==native.sha(baseline/'initial'/(kind+'.bin')),(seed,kind,'Initialization mismatch')
        native.write(folder/'matched_initialization.json',dict(passed=True,baseline=str(baseline),seed=seed,
            kinds=['policy','critic','encoder','decoder']))

def retain(label,source,result):
    destination=HERE/'inputs/evaluation'/label;destination.mkdir(parents=True,exist_ok=True)
    for folder in ['TrialResults','native_assets','Config','code']:
        shutil.copytree(source/folder,destination/folder,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for name in ['summary.json','code_manifest.json','configured.json','run_settings.json','compacted.json']:
        shutil.copy2(source/name,destination/name)
    result=dict(result,source_evaluation_root=str(source),metrics=str(destination/'TrialResults'/Path(result['metrics']).name))
    native.write(destination/'retained_summary.json',result)
    native.write(destination/'input_manifest.json',{str(f.relative_to(destination)):native.sha(f)
        for f in destination.rglob('*') if f.is_file() and f.name!='input_manifest.json'})
    return result

def training_folder(p,condition,seed):
    prefix='canalization-' if condition=='baseline' else 'history100-'
    return Path(p['raw_root'])/(prefix+condition+'-'+str(seed))

def evaluate(p):
    root=Path(p['raw_root']);results={}
    cases=[('selected-reference',native.selected_reference())]
    for condition in p['conditions']:
        for seed in p['training_seeds']:
            folder=training_folder(p,condition,seed)
            selection=native.read(folder/'selection.json');assert selection.get('complete',False)
            assert native.read(folder/'training_verified.json')['passed']
            cases.append((f'{condition}-{seed}',selection['best']['checkpoint']))
    ensure_space()
    for label,checkpoint in cases:
        status('independent-evaluation',policy=label,completed=len(results),total=len(cases))
        name='independent-'+label+'-'+str(p['comparison_environment_seed']);source=root/name
        result=native.read(source/'summary.json') if (source/'summary.json').exists() else native.evaluate(
            root,name,load_profile(checkpoint['profile']),checkpoint,p['comparison_trials'],p['comparison_environment_seed'],continuous=True)
        previous.validate_summary(result,checkpoint,p)
        assert result['profile']==checkpoint['profile']
        results[label]=retain(label,source,result)
        native.write(HERE/'independent_evaluations.json',dict(complete=len(results)==len(cases),results=results))
    return results

def audit_matched_environments(results):
    reference=None
    for label,result in results.items():
        metrics=Path(result['metrics']);current=[]
        for trial in native.read(metrics)['trials']:
            scene=json.loads(gzip.decompress((metrics.parent/trial['phases'][0]['scene-file']).read_bytes()))
            resources=[{k:r[k] for k in ['name','position','BaseHomeostaticImpact','MaxHomeostaticImpact','RespawnRate']}
                for r in scene['resources']]
            current.append(dict(trial=trial['id'],initial_h=trial['initial-homeostatic-state'],
                resource_layout_sha256=hashlib.sha256(json.dumps(resources,sort_keys=True).encode()).hexdigest(),
                initial_tile_counts=[t['OverlapCount'] for t in scene['tiles']]))
        if reference is None:reference=current
        else:assert current==reference,'Unmatched comparison environments: '+label
    native.write(HERE/'matched_environments.json',dict(passed=True,policies=len(results),trials=reference))

def summarize(p,results):
    audit_matched_environments(results);rows=[];phases=[];values={};curves=[]
    for condition in p['conditions']:
        values[condition]=[]
        for seed in p['training_seeds']:
            label=f'{condition}-{seed}';folder=training_folder(p,condition,seed);result=results[label]
            if condition!= 'baseline':assert native.read(folder/'matched_initialization.json')['passed']
            completion=native.read(folder/'trainer_complete.json');raw=previous.wear_rows(result);late=[r for r in raw if r['phase']==3]
            values[condition].append(result['mean_time_mae'])
            rows.append(dict(condition=condition,training_seed=seed,time_mae=result['mean_time_mae'],
                fraction_within_5=result['mean_fraction_within_5'],
                fraction_above_100=statistics.mean(r['fraction_above_100'] for r in raw),
                phase_3_time_mae=statistics.mean(r['time_mae'] for r in late),
                phase_3_revisit_fraction=statistics.mean(r['window_revisit_fraction'] for r in late),
                phase_3_maximum_tile_count=statistics.mean(r['maximum_tile_count'] for r in late),
                selected_transitions=result['checkpoint']['steps'],collected_transitions=completion['steps'],
                termination=completion['reason'],training_history=previous.training_history(Path(p['raw_root']),folder.name)))
            phases.extend(dict(condition=condition,training_seed=seed,**r) for r in raw)
            selection=native.read(folder/'selection.json')
            curves.extend(dict(condition=condition,training_seed=seed,steps=r['checkpoint']['steps'],selection_time_mae=r['mean_time_mae']) for r in selection['history'])
            evidence=HERE/'inputs/training'/label;evidence.mkdir(parents=True,exist_ok=True)
            for name in ['selection.json','training_verified.json','trainer_complete.json','engine_result.json','effective_config.json',
                         'native_environment.json','code_manifest.json','landscape_history.jsonl','matched_initialization.json']:
                if (folder/name).exists():shutil.copy2(folder/name,evidence/name)
            shutil.copytree(folder/'initial',evidence/'initial',dirs_exist_ok=True)
            native.write(evidence/'input_manifest.json',{str(f.relative_to(evidence)):native.sha(f) for f in evidence.rglob('*') if f.is_file() and f.name!='input_manifest.json'})
            destination=HERE/'policies'/label;destination.mkdir(parents=True,exist_ok=True);checkpoint=dict(result['checkpoint']);snapshots={}
            for kind,item in checkpoint['snapshots'].items():
                source=Path(item['path']);assert native.sha(source)==item['sha256'];target=destination/(kind+'.bin');shutil.copy2(source,target)
                snapshots[kind]=dict(path=str(target),sha256=native.sha(target))
            checkpoint.update(source_checkpoint=result['checkpoint'],snapshots=snapshots,kind='100-second history comparison candidate; not promoted')
            native.write(destination/'checkpoint.json',checkpoint)
    contrast=previous.paired_contrast(values,*p['conditions'])
    summary=[dict(condition=c,mean_time_mae=statistics.mean(values[c]),sd_between_policies=statistics.stdev(values[c]),per_seed_time_mae=values[c]) for c in p['conditions']]
    assert native.source_files()==native.read(Path(p['raw_root'])/'source_preservation.json')
    output=dict(complete=True,protocol=p,summary=summary,per_policy=rows,paired_contrast=contrast,
        selected_reference_time_mae=results['selected-reference']['mean_time_mae'],production_preserved=True)
    native.write(HERE/'results.json',output);native.write(HERE/'selection_curves.json',curves)
    for name,items in [('per_policy.csv',[{k:v for k,v in r.items() if k!='training_history'} for r in rows]),('per_phase.csv',phases)]:
        with (HERE/name).open('w',newline='') as file:
            writer=csv.DictWriter(file,fieldnames=list(items[0]));writer.writeheader();writer.writerows(items)
    lines=['Both conditions trained with 100-second episodes and the original learning settings. The sole manipulated setting disables whole-world resets on policy updates; timed and failure resets remain.',
        'Three matched initialization seeds per condition, selected on eight CCC trials and compared on 16 separate continuous-homeostasis CCC trials. Baseline training and any matching completed evaluations were reused.',
        '| Condition | Mean time-averaged absolute h | SD across trained policies | Per-seed MAE |','|---|---:|---:|---|']
    for r in summary:lines.append(f"| {r['condition']} | {r['mean_time_mae']:.3f} | {r['sd_between_policies']:.3f} | "+', '.join(f'{v:.3f}' for v in r['per_seed_time_mae'])+' |')
    lo,hi=contrast['paired_t_95_interval']
    lines.extend(['',f"Preserve minus reset: mean MAE difference {contrast['mean_difference']:.3f}; exploratory paired 95% t interval [{lo:.3f}, {hi:.3f}]; exact two-sided sign-flip p={contrast['exact_sign_flip_p']:.3f}. Negative differences favor preserving world state.",
        '', 'Three training seeds limit precision; repeated trials do not increase training replication. This tests the complete reset-on-update behavior, not tile-only persistence or the causal effect of canalization itself. No CDR comparison is included. Evaluation lasts 300 seconds with h and tile history retained between reporting windows; the common inherited phase-start velocity initialization remains. The reserved final-test seed was not used. No candidate is automatically promoted.'])
    (HERE/'RESULTS.md').write_text('\n\n'.join(lines[:2])+'\n\n'+'\n'.join(lines[2:])+'\n')

def alive(pid):
    try:os.kill(pid,0);return True
    except ProcessLookupError:return False

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--wait-for',type=int);parser.add_argument('--prepare-only',action='store_true')
    args=parser.parse_args();p=prepare_protocol()
    if args.prepare_only:print('PROTOCOL_VERIFIED '+str(HERE/'protocol.json'));return
    native.write(HERE/'process.json',dict(pid=os.getpid(),wait_for=args.wait_for,started_at=native.stamp()))
    subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        if args.wait_for and alive(args.wait_for):
            status('queued',wait_for=args.wait_for,reason='Run sequentially after the active study to limit memory pressure')
            deadline=time.monotonic()+24*3600
            while alive(args.wait_for):
                if time.monotonic()>deadline:raise TimeoutError('Active study did not exit within 24 hours')
                time.sleep(10)
        prepare_protocol();train_candidates(p);results=evaluate(p);status('analyzing');summarize(p,results)
        status('plotting');subprocess.run([str(native.PYTHON_ENV/'bin/python'),str(HERE/'plot.py')],check=True)
        status('complete',results=str(HERE/'results.json'))
    except BaseException:
        status('failed',error=traceback.format_exc());raise

if __name__=='__main__':main()
