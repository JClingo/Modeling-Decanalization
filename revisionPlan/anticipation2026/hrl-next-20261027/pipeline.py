"""Audited sequential HRL studies; all decisions and budgets frozen up front."""
from pathlib import Path
from dataclasses import replace
import argparse,ctypes,gzip,hashlib,itertools,json,math,os,shutil,statistics,subprocess,sys,time,traceback
HERE=Path(__file__).resolve().parent
WORKSPACE=HERE.parents[2]
sys.path.insert(0,str(WORKSPACE/'learning/hrl_next'))
import run as native
from profiles import BASE,PROFILES,load_profile
sys.path.insert(0,str(HERE.parent/'hrl-learning-20261026'))
from compare import training_history,wear_rows
import share_scratch_storage as storage
ROOT=Path('/private/tmp/hrl-canalization-study-20261026')
SEEDS=[1201,2301,3401]
LIB=ctypes.CDLL('/usr/lib/libSystem.B.dylib',use_errno=True)
LIB.clonefile.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int]

def cowcopy(source,target):
    source,target=Path(source),Path(target)
    if target.exists():
        assert native.sha(source)==native.sha(target),'Evidence changed: '+str(target)
        return str(target)
    if LIB.clonefile(os.fsencode(source),os.fsencode(target),0):shutil.copy2(source,target)
    else:shutil.copystat(source,target)
    return str(target)

def copytree(source,target):
    shutil.copytree(source,target,dirs_exist_ok=True,copy_function=cowcopy,
        ignore=shutil.ignore_patterns('__pycache__','*.pyc'))

def status(stage,**details):
    native.write(HERE/'status.json',dict(stage=stage,updated_at=native.stamp(),**details))
    print(stage+' '+json.dumps(details),flush=True)

def prepare():
    original=native.read(HERE.parent/'hrl-learning-20261026/comparison_protocol.json')
    for name,digest in original['source_sha256'].items():assert native.sha(WORKSPACE/'learning/hrl'/name)==digest
    assert native.source_files()==native.read(ROOT/'source_preservation.json')
    protocol=dict(purpose='Audit, isolated reward and PPO tests, adaptive duration, matched static costs, conditional fresh-seed confirmation',
        raw_root=str(ROOT),screen_training_seeds=SEEDS,training_environment_seed_rule='100000 + training seed',
        confirmation_training_seeds=[4501,5601,6701,7801,8901],
        max_gathers=200,transitions_per_gather=10000,checkpoint_every_gathers=20,early_stopping=False,
        checkpoint_selection=dict(environment_seeds=[41011,41021,41031],trials_per_seed=4,
            criterion='Equal-weight mean continuous-CCC time-MAE across all three seed pools'),
        comparison=dict(environment_seeds=[51011,51021],trials_per_seed=8,continuous_homeostasis=True,order='ccc'),
        audit=dict(environment_seed=43001,trials=8,action_noise_scales=[0.,1.],
            policies=['selected-reference','baseline-1201','baseline-2301','combined-1201']),
        primary_action_noise=0.,diagnostic_action_noise=1.,
        stage_order=['audit','reward','optimizer','duration','mechanism','confirmation-if-promising'],
        reward_profiles=[BASE.contract(),PROFILES['absolute-25'].contract()],
        optimizer='Only change original log surrogate to standard probability-ratio surrogate; retain original sampler, optimizers, rates, update count, losses, shared encoder and clipping',
        duration=dict(stages_seconds=[100,200,300],minimum_transitions=[500000,1000000],
            gate='Last ten gathers mean training time-MAE <=25 and mean true terminations per transition <=0.0025; advance only at a physical world reset',
            baseline='Winning 100-second learning setup; retain reset-on-update behavior in both'),
        mechanism=dict(environment_seeds=[53011,53021],trials_per_seed=8,
            control='Keep traversal counters, geometry, resources and passive loss; fix every physical tile-cost denominator and anticipated tile-cost denominator at 2 (first-entry cost)',
            scope='Within-policy dependence on traversal-sensitive costs; no claim of matched-control training or proof of beneficial habits'),
        screening_gate=dict(relative_mean_mae_improvement=.10,minimum_better_paired_seeds=2,
            maximum_increase_in_extreme_fraction=.01,
            interpretation='Preregistered practical screening rule, not a significance claim'),
        confirmation=dict(conditional='Run only if a changed setup passes screening; compare with original baseline on five fresh matched training seeds',
            final_environment_seed=61001,continuous_ccc_trials=32,paper_boundary_ccc_trials=16,paper_boundary_cdr_trials=16,
            rule='Freeze candidate and all ten selected policies before opening final test; no test-based reselection or automatic promotion'),
        physical_protocol='Traversal +1 throughout; existing half-floor after decanalization. Timed and failure resets remain. No production or manuscript mutation.',
        execution_storage_guard='Two measured template copies plus 2 GiB headroom; preserve completed evidence with independent copy-on-write copies',
        inference_limit='CCC h and tile history carry between three 100-second windows; inherited phase-start velocity initialization remains. Paper-boundary CCC/CDR use separate h resets and are not pooled with continuous CCC.',
        source_sha256={p.name:native.sha(p) for p in native.HERE.glob('*.py')},
        asset_bundle_sha256={p.name:native.sha(p) for p in (native.HERE/'assets').glob('*') if p.is_file()},
        orchestration_sha256={p.name:native.sha(p) for p in HERE.glob('*.py')},
        legacy_helper_sha256={str(p.relative_to(WORKSPACE)):native.sha(p) for p in [
            HERE.parent/'hrl-learning-20261026/compare.py',HERE.parent/'hrl-learning-20261026/share_scratch_storage.py']},
        template_dependencies_sha256={str(f.relative_to(ROOT/'template/TestProject')):native.sha(f)
            for folder in ['Content/Python','analysis/homeostatic','analysis/trial_metrics','analysis/timing']
            for f in (ROOT/'template/TestProject'/folder).rglob('*.py')},
        graph_helper_sha256={name:native.sha(native.SOURCE/'analysis/timing'/name) for name in ['graph_asset.py','patch_graphs.py']},
        engine_python_sha256={str(f):native.sha(f)
            for folder in [native.EXE.parents[2]/'Plugins/Experimental/LearningAgents/Content/Python',
                           native.EXE.parents[2]/'Plugins/Experimental/NNERuntimeBasicCpu/Content/Python']
            for f in folder.glob('*.py')})
    path=HERE/'protocol.json'
    if path.exists():assert native.read(path)==protocol,'Frozen staged protocol changed'
    else:native.write(path,protocol)
    frozen=HERE/'frozen_runner'
    if not frozen.exists():copytree(native.HERE,frozen)
    dependencies=HERE/'frozen_dependencies'
    if not dependencies.exists():
        for folder in ['Content/Python','analysis/homeostatic','analysis/trial_metrics','analysis/timing']:
            copytree(ROOT/'template/TestProject'/folder,dependencies/folder)
    return protocol

def space():
    storage.main()
    # The isolated static validation has no trial outputs. Keep its authored
    # and compiled variants and code before removing the finished disposable copy.
    folder=ROOT/'next-engineering-static-20261027';project=folder/'TestProject'
    if (folder/'static_validation.json').exists() and native.read(folder/'static_validation.json')['passed'] and project.exists():
        assert (project/'HRL_LEARNING_COPY').exists()
        for relative in ['Agent/BP_Agent.uasset','Level/BP_Tile.uasset','Learning/BP_AgentManager.uasset','Learning/BP_AgentTrainingEnv.uasset']:
            target=folder/'native_assets'/relative;target.parent.mkdir(parents=True,exist_ok=True);cowcopy(project/'Content'/relative,target)
        copytree(project/'analysis/hrl_learning',folder/'code')
        for name in ['run_settings.json','configured.json']:cowcopy(project/name,folder/name)
        shutil.rmtree(project);native.write(folder/'compacted.json',dict(passed=True,reason='Completed static validation; variants, code and receipts retained'))
    free=shutil.disk_usage(ROOT).free
    template=ROOT/'template/TestProject'
    copy_bytes=sum(f.stat().st_size for folder in ['Content','Config','analysis']
        for f in (template/folder).rglob('*') if f.is_file())
    required=2*copy_bytes+2*2**30
    if free<required:raise RuntimeError(f'Need {required/2**30:.2f} GiB for two isolated copies plus headroom; have {free/2**30:.2f}')

def retain(label,source,result):
    destination=HERE/'inputs/evaluation'/label;destination.mkdir(parents=True,exist_ok=True)
    for name in ['TrialResults','native_assets','Config','code']:copytree(source/name,destination/name)
    for name in ['summary.json','run_settings.json','configured.json','code_manifest.json','compacted.json']:cowcopy(source/name,destination/name)
    retained=dict(result,source_root=str(source),metrics=str(destination/'TrialResults'/Path(result['metrics']).name))
    native.write(destination/'retained_summary.json',retained)
    native.write(destination/'input_manifest.json',{str(f.relative_to(destination)):native.sha(f)
        for f in destination.rglob('*') if f.is_file() and f.name!='input_manifest.json'})
    return retained

def evaluate(label,checkpoint,seed,trials,noise=0.,static=False,continuous=True,order='ccc'):
    name=f'next-{label}-e{seed}-n{int(noise)}-s{int(static)}-{order}-c{int(continuous)}'
    overrides=HERE/'evaluation_run_overrides.json'
    if overrides.exists():name=native.read(overrides).get(name,name)
    folder=ROOT/name;receipt=folder/'summary.json'
    if receipt.exists():result=native.read(receipt)
    else:
        assert not folder.exists(),'Inspect incomplete evaluation before retry: '+str(folder)
        result=native.evaluate(ROOT,name,load_profile(checkpoint['profile']),checkpoint,trials,seed,order,continuous,
            inference_action_noise=noise,static_tile_costs=static)
    assert result['passed'] and result['evaluation_seed']==seed and len(result['trials'])==trials
    assert result['checkpoint']['snapshots']==checkpoint['snapshots']
    assert result['inference_action_noise']==noise and result['static_tile_costs']==static
    assert result['continuous_homeostasis']==continuous and result['order']==order
    return retain(name,folder,result)

def pool(results,checkpoint):
    return dict(checkpoint=checkpoint,mean_time_mae=statistics.mean(r['mean_time_mae'] for r in results),
        mean_fraction_within_5=statistics.mean(r['mean_fraction_within_5'] for r in results),
        mean_fraction_above_100=statistics.mean(phase['fraction_above_100'] for r in results for t in r['trials'] for phase in t['phases']),
        trials=[dict(**t,environment_seed=r['evaluation_seed']) for r in results for t in r['trials']],
        evaluations=results)

def matched(results):
    reference=None
    for result in results:
        path=Path(result['metrics']);current=[]
        for trial in native.read(path)['trials']:
            scene=json.loads(gzip.decompress((path.parent/trial['phases'][0]['scene-file']).read_bytes()))
            resources=[{k:r[k] for k in ['name','position','BaseHomeostaticImpact','MaxHomeostaticImpact','RespawnRate']} for r in scene['resources']]
            current.append(dict(trial=trial['id'],h=trial['initial-homeostatic-state'],
                resources=hashlib.sha256(json.dumps(resources,sort_keys=True).encode()).hexdigest(),counts=[t['OverlapCount'] for t in scene['tiles']]))
        if reference is None:reference=current
        else:assert reference==current,'Initial evaluation environments do not match'

def audit(p):
    target=HERE/'audit/results.json'
    if target.exists():assert native.read(target)['complete'];return
    status('audit',detail='Paired deterministic and sampled-action rollouts')
    checkpoints={'selected-reference':native.selected_reference(),
        'baseline-1201':native.read(ROOT/'canalization-baseline-1201/selection.json')['best']['checkpoint'],
        'baseline-2301':native.read(ROOT/'canalization-baseline-2301/selection.json')['best']['checkpoint'],
        'combined-1201':native.read(ROOT/'canalization-canalization-aware-1201/selection.json')['best']['checkpoint']}
    rows=[];evaluations=[]
    for label,checkpoint in checkpoints.items():
        for noise in p['audit']['action_noise_scales']:
            status('audit',policy=label,action_noise=noise)
            result=evaluate('audit-'+label,checkpoint,p['audit']['environment_seed'],p['audit']['trials'],noise)
            evaluations.append(result);row=pool([result],checkpoint);row.update(policy=label,action_noise=noise);rows.append(row)
            native.write(HERE/'audit/progress.json',dict(completed=len(rows),total=8))
    matched(evaluations)
    native.write(target,dict(complete=True,rows=rows,initial_environments_matched=True,
        findings=['Training RunInference uses default action noise 1; authored inference graph uses 0.',
        'The observation schema is shared: 11 floats, signed h scaled by 100; no separate train/evaluation observation definition.',
        'Native ResetAgents clears recurrent state; buffer-only truncations do not reset the physical world.',
        'Training terminates beyond absolute h=100; fixed-horizon inference continues. This is a distribution mismatch, not an evaluation counter failure.',
        'Primary learning selection remains deterministic (noise 0); noise 1 is a diagnostic, with no automatic inference change.']))
    lines=['Training/evaluation audit: paired rollouts on identical initial environments.',
        '| Saved policy | Mean-action MAE (noise 0) | Sampled-action MAE (noise 1) |','|---|---:|---:|']
    for label in checkpoints:
        group=[r for r in rows if r['policy']==label]
        lines.append(f"| {label} | {group[0]['mean_time_mae']:.3f} | {group[1]['mean_time_mae']:.3f} |")
    lines.extend(['','These are repeated rollouts of fixed policies, not new independent training replicates. Noise changes behavior and is diagnostic; all primary screens retain mean-action evaluation. Training ends outside |h|=100, whereas inference records the entire fixed horizon. Observation scaling and native memory-reset semantics were checked against the authored graphs and installed engine source.'])
    (HERE/'audit/RESULTS.md').write_text('\n'.join(lines)+'\n')

def training(label,profile,seed,p,curriculum=False):
    folder=ROOT/('next-'+label+'-'+str(seed));receipt=folder/'selection.json'
    if receipt.exists() and native.read(receipt).get('complete'):
        assert native.read(folder/'training_verified.json')['passed'];return native.read(receipt)
    assert not folder.exists(),'Inspect incomplete training before explicit retry: '+str(folder)
    space();status('training',experiment=label,training_seed=seed)
    history=[]
    def checkpoint_callback(checkpoint):
        results=[evaluate(folder.name+'-g'+str(checkpoint['gathers']),checkpoint,envseed,p['checkpoint_selection']['trials_per_seed'])
            for envseed in p['checkpoint_selection']['environment_seeds']]
        item=pool(results,checkpoint);history.append(item)
        native.write(receipt,dict(complete=False,best=min(history,key=lambda r:r['mean_time_mae']),history=history))
        return False # Equal fixed maximum collection budget for both arms.
    native.train(ROOT,folder.name,profile,seed,100000+seed,p['max_gathers'],p['checkpoint_every_gathers'],48760,
        checkpoint_callback,training_curriculum=curriculum)
    assert history
    baseline=ROOT/f'canalization-baseline-{seed}'
    if baseline.exists():
        for kind in native.KINDS:assert native.sha(folder/'initial'/(kind+'.bin'))==native.sha(baseline/'initial'/(kind+'.bin')),(seed,kind)
    record=dict(complete=True,best=min(history,key=lambda r:r['mean_time_mae']),history=history,run=folder.name,
        profile=profile.contract(),curriculum=curriculum,training_seed=seed)
    native.write(receipt,record)
    evidence=HERE/'inputs/training'/folder.name;evidence.mkdir(parents=True,exist_ok=True)
    for name in ['selection.json','training_verified.json','trainer_complete.json','effective_config.json','native_environment.json','code_manifest.json','landscape_history.jsonl','curriculum_history.jsonl']:
        if (folder/name).exists():cowcopy(folder/name,evidence/name)
    copytree(folder/'initial',evidence/'initial')
    return record

def contrast(first,second):
    differences=[b-a for a,b in zip(first,second)];n=len(differences);assert n in (3,5)
    mean=statistics.mean(differences);sd=statistics.stdev(differences);critical={3:4.302652729749464,5:2.7764451051977987}[n]
    null=[abs(statistics.mean(s*x for s,x in zip(signs,differences))) for signs in itertools.product([-1,1],repeat=n)]
    margin=critical*sd/math.sqrt(n)
    return dict(per_seed_difference=differences,mean_difference=mean,exploratory_paired_t_95_interval=[mean-margin,mean+margin],
        exact_sign_flip_p=sum(v>=abs(mean)-1e-12 for v in null)/len(null))

def compare_groups(stage,groups,p,settings=None):
    target=HERE/stage/'results.json'
    if target.exists():return native.read(target)
    space();settings=settings or p['comparison'];rows=[];evaluations_by_seed={};values={}
    initial_by_seed={}
    for records in groups.values():
        hashes=[]
        for record in records:
            initial={kind:native.sha(ROOT/record['run']/'initial'/(kind+'.bin')) for kind in native.KINDS}
            seed=record['training_seed']
            if seed in initial_by_seed:assert initial==initial_by_seed[seed],'Unmatched initialized networks'
            else:initial_by_seed[seed]=initial
            hashes.append(initial['policy'])
        assert len(set(hashes))==len(hashes),'Training seeds did not produce distinct policies'
    for condition,records in groups.items():
        values[condition]=[]
        for record in records:
            checkpoint=record['best']['checkpoint'];seed=record['training_seed']
            status('comparison',experiment=stage,condition=condition,training_seed=seed)
            results=[evaluate(f'{stage}-{condition}-{seed}',checkpoint,e,settings['trials_per_seed'],
                static=settings.get('static',False),continuous=settings.get('continuous_homeostasis',True),order=settings.get('order','ccc')) for e in settings['environment_seeds']]
            for result in results:evaluations_by_seed.setdefault(result['evaluation_seed'],[]).append(result)
            pooled=pool(results,checkpoint);values[condition].append(pooled['mean_time_mae'])
            folder=ROOT/record['run'];row=dict(condition=condition,training_seed=seed,**pooled,
                training_history=training_history(ROOT,record['run']),
                selected_transitions=checkpoint['steps'],collected_transitions=native.read(folder/'trainer_complete.json')['steps'],
                curriculum=record.get('curriculum',False))
            rows.append(row)
            export=HERE/'policies'/stage/condition/str(seed);export.mkdir(parents=True,exist_ok=True);snapshots={}
            for kind,item in checkpoint['snapshots'].items():
                assert native.sha(item['path'])==item['sha256'];cowcopy(item['path'],export/(kind+'.bin'))
                snapshots[kind]=dict(path=str(export/(kind+'.bin')),sha256=item['sha256'])
            native.write(export/'checkpoint.json',dict(checkpoint,source_checkpoint=checkpoint,snapshots=snapshots,kind='Unpromoted staged-study candidate'))
    for results in evaluations_by_seed.values():matched(results)
    names=list(groups);summary=[dict(condition=c,mean_time_mae=statistics.mean(values[c]),sd_between_policies=statistics.stdev(values[c]),per_seed_time_mae=values[c]) for c in names]
    output=dict(complete=True,stage=stage,summary=summary,per_policy=rows,settings=settings,
        contrast=contrast(values[names[0]],values[names[1]]) if len(names)==2 else None,
        initial_environments_matched=True,replication='independently trained policies; trials are repeated measurements')
    native.write(target,output)
    lines=[f'{stage}: independent-from-checkpoint-selection evaluation of the frozen candidates.',
        '| Condition | Mean time-MAE | SD across policies | Per-seed MAE |','|---|---:|---:|---|']
    for r in summary:lines.append(f"| {r['condition']} | {r['mean_time_mae']:.3f} | {r['sd_between_policies']:.3f} | "+', '.join(f'{x:.3f}' for x in r['per_seed_time_mae'])+' |')
    phase_note=('Final evaluation of five fresh training seeds per condition; selected policies were frozen before opening this test. '
        if stage.startswith('confirmation-') else 'Development comparisons guide the next stage and are not final tests. Three screening seeds give limited precision. ')
    lines.extend(['','```json',json.dumps(output['contrast'],indent=2),'```','',phase_note+
        'Negative paired differences favor the second condition. Raw rewards from different reward functions are not compared. No candidate is promoted.'])
    (target.parent/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    return output

def choose(stage,result,control,candidate,p):
    path=HERE/stage/'decision.json'
    a=[r for r in result['per_policy'] if r['condition']==control];b=[r for r in result['per_policy'] if r['condition']==candidate]
    assert [r['training_seed'] for r in a]==[r['training_seed'] for r in b]
    gate=p['screening_gate'];ma=statistics.mean(r['mean_time_mae'] for r in a);mb=statistics.mean(r['mean_time_mae'] for r in b)
    better=sum(y['mean_time_mae']<x['mean_time_mae'] for x,y in zip(a,b))
    extremes=statistics.mean(r['mean_fraction_above_100'] for r in b)-statistics.mean(r['mean_fraction_above_100'] for r in a)
    passed=mb<=ma*(1-gate['relative_mean_mae_improvement']) and better>=gate['minimum_better_paired_seeds'] and extremes<=gate['maximum_increase_in_extreme_fraction']
    decision=dict(selected=candidate if passed else control,candidate_passed=passed,control_mean=ma,candidate_mean=mb,
        better_paired_seeds=better,extreme_fraction_increase=extremes,rule=gate)
    native.write(path,decision);return decision['selected']

def run(p):
    engineering=native.read(HERE/'engineering_verified.json')
    assert engineering['passed'] and len(engineering['cases'])==6
    assert all(c['passed'] for c in engineering['cases'])
    assert any(c.get('checks',0)>=29 for c in engineering['cases']),'Static contact and anticipation checks must pass'
    assert any(c.get('initial_duration')==100. for c in engineering['cases'])
    space();audit(p)
    reward_profiles={'quality':BASE,'absolute':PROFILES['absolute-25']}
    rewards={name:[training('reward-'+name,profile,s,p) for s in SEEDS] for name,profile in reward_profiles.items()}
    result=compare_groups('reward',rewards,p);reward=choose('reward',result,'quality','absolute',p)
    profile=reward_profiles[reward];control_records=rewards[reward]
    ratio=replace(profile,name='ratio-only-'+reward,objective='ratio').validate()
    ratio_records=[training('optimizer-ratio-'+reward,ratio,s,p) for s in SEEDS]
    result=compare_groups('optimizer',{'original':control_records,'ratio-only':ratio_records},p)
    optimizer=choose('optimizer',result,'original','ratio-only',p)
    if optimizer=='ratio-only':profile,control_records=ratio,ratio_records
    curriculum=replace(profile,name='duration-curriculum-'+reward+'-'+optimizer,episode_seconds=300.).validate()
    duration_records=[training('duration-'+reward+'-'+optimizer,curriculum,s,p,True) for s in SEEDS]
    result=compare_groups('duration',{'fixed-100s':control_records,'curriculum':duration_records},p)
    duration=choose('duration',result,'fixed-100s','curriculum',p)
    if duration=='curriculum':profile,control_records=curriculum,duration_records
    mechanism_settings=dict(environment_seeds=p['mechanism']['environment_seeds'],trials_per_seed=p['mechanism']['trials_per_seed'])
    active=compare_groups('mechanism-canalizing',{'selected':control_records},p,mechanism_settings)
    static=compare_groups('mechanism-static',{'selected':control_records},p,dict(mechanism_settings,static=True))
    matched_by_seed={}
    for data in [active,static]:
        for row in data['per_policy']:
            for ev in row['evaluations']:matched_by_seed.setdefault(ev['evaluation_seed'],[]).append(ev)
    for data in matched_by_seed.values():matched(data)
    native.write(HERE/'mechanism/results.json',dict(complete=True,
        static_minus_canalizing=contrast([r['mean_time_mae'] for r in active['per_policy']],[r['mean_time_mae'] for r in static['per_policy']]),
        initial_environments_matched=True,interpretation=p['mechanism']['scope']))
    changed=reward!='quality' or optimizer!='original' or duration!='fixed-100s'
    native.write(HERE/'screening_decisions.json',dict(reward=reward,optimizer=optimizer,duration=duration,
        confirmation_required=changed,selected_profile=profile.contract()))
    if changed:
        # Select both arms fully before any final evaluation is opened.
        records={}
        for condition,pr,curr in [('original-baseline',BASE,False),('candidate',profile,duration=='curriculum')]:
            records[condition]=[training('confirmation-'+condition,pr,s,p,curr) for s in p['confirmation_training_seeds']]
        native.write(HERE/'confirmation/frozen_candidates.json',dict(complete=True,groups=records,profile=profile.contract()))
        settings=dict(environment_seeds=[p['confirmation']['final_environment_seed']],trials_per_seed=32)
        compare_groups('confirmation-continuous-ccc',records,p,settings)
        for order in ['ccc','cdr']:
            compare_groups('confirmation-paper-'+order,records,p,dict(settings,trials_per_seed=16,continuous_homeostasis=False,order=order))
    else:native.write(HERE/'confirmation/skipped.json',dict(reason='No changed setup passed the frozen practical screening gate'))
    assert native.source_files()==native.read(ROOT/'source_preservation.json')
    native.write(HERE/'complete.json',dict(complete=True,decisions=native.read(HERE/'screening_decisions.json'),production_preserved=True))
    subprocess.run([str(native.PYTHON_ENV/'bin/python'),str(HERE/'plot.py')],check=True)
    status('complete',decisions=str(HERE/'screening_decisions.json'))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--wait-for',type=int)
    args=parser.parse_args();p=prepare()
    if args.prepare_only:print('STAGED_PROTOCOL_VERIFIED');return
    native.write(HERE/'process.json',dict(pid=os.getpid(),wait_for=args.wait_for,started_at=native.stamp()))
    subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        if args.wait_for:
            status('waiting-for-engineering',pid=args.wait_for)
            while True:
                try:os.kill(args.wait_for,0)
                except ProcessLookupError:break
                time.sleep(10)
        run(p)
    except BaseException:
        status('failed',error=traceback.format_exc());raise

if __name__=='__main__':main()
