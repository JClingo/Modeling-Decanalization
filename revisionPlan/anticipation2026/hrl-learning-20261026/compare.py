"""Independent evaluation and policy-level analysis of the frozen HRL screen."""
from pathlib import Path
import argparse,csv,gzip,hashlib,itertools,json,math,shutil,statistics,sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/'learning/hrl'))
import run as native
from profiles import PROFILES,load_profile

def protocol():
    return native.read(HERE/'comparison_protocol.json')

def training_label(condition,seed):
    recovery=HERE/'recovery.json'
    overrides=native.read(recovery)['run_directory_overrides'] if recovery.exists() else {}
    return overrides.get(f'{condition}:{seed}',f'canalization-{condition}-{seed}')

def validate_summary(result,checkpoint,p):
    assert result['passed'] and result['continuous_homeostasis']
    assert result['evaluation_seed']==p['comparison_environment_seed']
    assert len(result['trials'])==p['comparison_trials']
    assert result['checkpoint']['snapshots']==checkpoint['snapshots']

def retain_evaluation(label,source,result):
    destination=HERE/'inputs'/label;destination.mkdir(parents=True,exist_ok=True)
    for folder in ['TrialResults','native_assets','Config','code']:
        shutil.copytree(source/folder,destination/folder,dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for name in ['summary.json','code_manifest.json','configured.json','run_settings.json','compacted.json']:
        shutil.copy2(source/name,destination/name)
    retained=dict(result,source_evaluation_root=str(source),
                  metrics=str(destination/'TrialResults'/Path(result['metrics']).name))
    native.write(destination/'retained_summary.json',retained)
    native.write(destination/'input_manifest.json',{str(f.relative_to(destination)):native.sha(f)
        for f in destination.rglob('*') if f.is_file() and f.name!='input_manifest.json'})
    return retained

def evaluate():
    p=protocol();root=Path(p['raw_root'])
    study=native.read(root/'canalization_summary.json')
    selections=[]
    for condition in p['conditions']:
        initial=[]
        for seed in p['training_seeds']:
            folder=root/training_label(condition,seed)
            selection=native.read(folder/'selection.json')
            assert selection.get('complete',False),'Training and checkpoint selection must finish first: '+str(folder)
            assert native.read(folder/'training_verified.json')['passed']
            initial.append({kind:native.sha(folder/'initial'/(kind+'.bin')) for kind in ['policy','critic']})
            selections.append(selection['best'])
        assert all(len({item[k] for item in initial})==len(initial) for k in ['policy','critic'])
    # The original sequential dispatcher does not rewrite its summary after
    # reusing completed selections. Aggregate the audited parallel receipts.
    if not study['complete']:
        native.write(root/'sequential_dispatcher_summary.json',study)
        study.update(complete=True,results=selections,summary=[dict(profile=name,trained_seeds=3,
            mean_time_mae=statistics.mean(r['mean_time_mae'] for r in selections if r['checkpoint']['profile']['name']==name),
            per_seed_mae=[r['mean_time_mae'] for r in selections if r['checkpoint']['profile']['name']==name])
            for name in p['conditions']],aggregation='Audited sequential and parallel completed selection receipts')
        native.write(root/'canalization_summary.json',study)
    for name,expected in p['source_sha256'].items():
        assert native.sha(native.HERE/name)==expected,'Frozen runner changed: '+name
    cases=[('selected-reference',native.selected_reference())]
    for condition in p['conditions']:
        for seed in p['training_seeds']:
            label=training_label(condition,seed)
            selection=native.read(root/label/'selection.json')
            assert selection['complete']
            checkpoint=selection['best']['checkpoint']
            assert checkpoint['profile']['name']==condition and checkpoint['policy_seed']==seed
            cases.append((f'{condition}-{seed}',checkpoint))
    results={}
    for label,checkpoint in cases:
        name='independent-'+label+'-'+str(p['comparison_environment_seed'])
        receipt=root/name/'summary.json'
        result=native.read(receipt) if receipt.exists() else native.evaluate(
            root,name,load_profile(checkpoint['profile']),checkpoint,
            p['comparison_trials'],p['comparison_environment_seed'],continuous=True)
        validate_summary(result,checkpoint,p)
        results[label]=retain_evaluation(label,root/name,result)
        native.write(HERE/'heldout_evaluations.json',dict(complete=len(results)==len(cases),
            protocol=p,results=results,analysis_sha256=native.sha(Path(__file__))))
    print('INDEPENDENT_EVALUATIONS_COMPLETE',flush=True)

def paired_contrast(values,first,second):
    """Second minus first: negative MAE differences favor the second condition."""
    pairs=[b-a for a,b in zip(values[first],values[second])]
    assert len(pairs)==3,'This frozen screen has exactly three matched training seeds'
    mean=statistics.mean(pairs);sd=statistics.stdev(pairs)
    # Exact inverse Student-t CDF for df=2, p=.975. Interval is exploratory.
    y=.95;critical=math.sqrt(2*y*y/(1-y*y));margin=critical*sd/math.sqrt(3)
    null=[abs(statistics.mean(sign*x for sign,x in zip(signs,pairs)))
          for signs in itertools.product([-1,1],repeat=3)]
    pvalue=sum(x>=abs(mean)-1e-12 for x in null)/len(null)
    return dict(first=first,second=second,per_seed_difference=pairs,mean_difference=mean,
                paired_t_95_interval=[mean-margin,mean+margin],exact_sign_flip_p=pvalue)

def audit_environments(results):
    matched=None
    for label,result in results.items():
        metrics=Path(result['metrics']);data=native.read(metrics);current=[]
        for trial in data['trials']:
            phase=trial['phases'][0]
            scene=json.loads(gzip.decompress((metrics.parent/phase['scene-file']).read_bytes()))
            static=[{k:r[k] for k in ['name','position','BaseHomeostaticImpact','MaxHomeostaticImpact','RespawnRate']}
                    for r in scene['resources']]
            current.append(dict(trial=trial['id'],initial_h=trial['initial-homeostatic-state'],
                resource_layout_sha256=hashlib.sha256(json.dumps(static,sort_keys=True).encode()).hexdigest()))
        if matched is None:matched=current
        else:assert current==matched,'Unmatched initial comparison environments: '+label
    native.write(HERE/'matched_comparison_environments.json',dict(passed=True,policies=len(results),trials=matched))

def wear_rows(result):
    data=native.read(result['metrics']);rows=[]
    for trial in data['trials']:
        for phase in trial['phases']:
            u=phase['uniform-decision-metrics'];w=phase['traversal-metrics']
            rows.append(dict(trial=trial['id'],phase=phase['sequence-idx'],
                time_mae=u['time_mae'],fraction_within_5=u['fraction_within_5'],
                fraction_above_100=u['fraction_above_100'],maximum_absolute_h=u['maximum_absolute_h'],
                window_entries=w['window_entries'],window_revisit_fraction=w['window_fraction_entries_revisiting'],
                maximum_tile_count=w['maximum_tile_count'],visited_tiles=w['visited_tiles'],
                next_cost_fraction_proxy=w['mean_visited_next_cost_fraction_of_first']))
    return rows

def training_history(root,label):
    path=root/label/'landscape_history.jsonl'
    episodes={}
    for line in path.read_text().splitlines():
        row=json.loads(line);key=row['observed_episode']
        old=episodes.get(key)
        if old is None or row['episode_decisions']>old['episode_decisions']:episodes[key]=row
    # The last observed episode can be ongoing at training shutdown.
    completed=[v for k,v in episodes.items() if k!=max(episodes)]
    values=[x['episode_seconds'] for x in completed]
    late=completed[-100:]
    return dict(observed_episodes=len(episodes),observed_completed_episodes=len(completed),
        mean_observed_duration_lower_bound=statistics.mean(values) if values else None,
        median_observed_duration_lower_bound=statistics.median(values) if values else None,
        maximum_observed_duration=max(values) if values else None,
        fraction_observed_reaching_95_seconds=statistics.mean(v>=95 for v in values) if values else None,
        fraction_observed_reaching_295_seconds=statistics.mean(v>=295 for v in values) if values else None,
        mean_peak_revisit_fraction=statistics.mean(x['fraction_entries_revisiting'] for x in completed) if completed else None,
        mean_peak_maximum_tile_count=statistics.mean(x['maximum_tile_count'] for x in completed) if completed else None,
        last_100_observed_episodes_mean_duration_lower_bound=statistics.mean(x['episode_seconds'] for x in late) if late else None,
        last_100_observed_episodes_mean_revisit_fraction=statistics.mean(x['fraction_entries_revisiting'] for x in late) if late else None,
        definition='Last sampled state of each observed completed episode. Durations are lower bounds, sampled every 100 decisions. Resets missed between observations are not counted.')

def export_policy(label,result):
    destination=HERE/'policies'/label;destination.mkdir(parents=True,exist_ok=True)
    checkpoint=dict(result['checkpoint']);snapshots={}
    for kind,item in checkpoint['snapshots'].items():
        source=Path(item['path']);assert native.sha(source)==item['sha256']
        target=destination/(kind+'.bin');shutil.copy2(source,target)
        snapshots[kind]=dict(path=str(target),sha256=native.sha(target))
    checkpoint.update(snapshots=snapshots,kind='screened candidate; not promoted',
        source_checkpoint=result['checkpoint'],independent_evaluation_seed=result['evaluation_seed'])
    native.write(destination/'checkpoint.json',checkpoint)

def summarize():
    p=protocol();root=Path(p['raw_root']);data=native.read(HERE/'heldout_evaluations.json')
    assert data['complete'];audit_environments(data['results']);rows=[];phase_rows=[];values={};curves=[]
    for condition in p['conditions']:
        values[condition]=[]
        for seed in p['training_seeds']:
            label=f'{condition}-{seed}';result=data['results'][label]
            run_label=training_label(condition,seed)
            completion=native.read(root/run_label/'trainer_complete.json')
            assert result['checkpoint']['policy_seed']==seed
            raw=wear_rows(result);late=[x for x in raw if x['phase']==3]
            values[condition].append(result['mean_time_mae'])
            row=dict(condition=condition,training_seed=seed,source_training_run=run_label,time_mae=result['mean_time_mae'],
                fraction_within_5=result['mean_fraction_within_5'],
                fraction_above_100=statistics.mean(x['fraction_above_100'] for x in raw),
                phase_3_time_mae=statistics.mean(x['time_mae'] for x in late),
                phase_3_revisit_fraction=statistics.mean(x['window_revisit_fraction'] for x in late),
                phase_3_maximum_tile_count=statistics.mean(x['maximum_tile_count'] for x in late),
                phase_3_next_cost_proxy=statistics.mean(x['next_cost_fraction_proxy'] for x in late),
                selected_transitions=result['checkpoint']['steps'],collected_transitions=completion['steps'],
                termination=completion['reason'],training_history=training_history(root,run_label))
            rows.append(row)
            phase_rows.extend(dict(condition=condition,training_seed=seed,**x) for x in raw)
            selection=native.read(root/run_label/'selection.json')
            curves.extend(dict(condition=condition,training_seed=seed,steps=x['checkpoint']['steps'],
                selection_time_mae=x['mean_time_mae'],training_time_mae=x['checkpoint']['training_time_mae'])
                for x in selection['history'])
            export_policy(label,result)
            evidence=HERE/'inputs/training'/label;evidence.mkdir(parents=True,exist_ok=True)
            for name in ['selection.json','training_verified.json','trainer_complete.json','engine_result.json',
                         'effective_config.json','native_environment.json','code_manifest.json',
                         'landscape_history.jsonl','optimizer_history.jsonl']:
                source=root/run_label/name
                if source.exists():shutil.copy2(source,evidence/name)
            shutil.copytree(root/run_label/'initial',evidence/'initial',dirs_exist_ok=True)
            native.write(evidence/'input_manifest.json',{str(f.relative_to(evidence)):native.sha(f)
                for f in evidence.rglob('*') if f.is_file() and f.name!='input_manifest.json'})
    comparisons=[paired_contrast(values,a,b) for a,b in [
        ('baseline','canalization-300s'),('canalization-300s','canalization-persistent'),
        ('canalization-persistent','canalization-aware')]]
    ordered=sorted(range(len(comparisons)),key=lambda i:comparisons[i]['exact_sign_flip_p']);running=0.
    for rank,i in enumerate(ordered):
        running=max(running,min(1.,(len(ordered)-rank)*comparisons[i]['exact_sign_flip_p']))
        comparisons[i]['holm_exact_p']=running
    summary=[]
    for condition in p['conditions']:
        group=[r for r in rows if r['condition']==condition]
        summary.append(dict(condition=condition,training_seeds=len(group),
            mean_time_mae=statistics.mean(values[condition]),sd_between_policies=statistics.stdev(values[condition]),
            per_seed_time_mae=values[condition],
            mean_fraction_within_5=statistics.mean(r['fraction_within_5'] for r in group),
            mean_phase_3_revisit_fraction=statistics.mean(r['phase_3_revisit_fraction'] for r in group),
            mean_training_duration_lower_bound=statistics.mean(r['training_history']['mean_observed_duration_lower_bound'] for r in group)))
    assert native.source_files()==native.read(root/'source_preservation.json')
    output=dict(complete=True,protocol=p,summary=summary,per_policy=rows,planned_paired_contrasts=comparisons,
        selected_reference_time_mae=data['results']['selected-reference']['mean_time_mae'],
        interpretation='Exploratory comparison of training conditions with three independent policies each. Repeated trials do not increase the training replication count. No causal isolation of traversal-dependent costs; no automatic policy promotion.',
        production_assets_and_selected_policies_preserved=True,analysis_sha256=native.sha(Path(__file__)))
    native.write(HERE/'results.json',output);native.write(HERE/'selection_curves.json',curves)
    for name,items in [('per_policy.csv',[{k:v for k,v in r.items() if k!='training_history'} for r in rows]),('per_phase.csv',phase_rows)]:
        with (HERE/name).open('w',newline='') as file:
            writer=csv.DictWriter(file,fieldnames=list(items[0]));writer.writeheader();writer.writerows(items)
    for row in summary:print(row['condition'],row['per_seed_time_mae'],'mean',row['mean_time_mae'])
    lines=['This exploratory screen compared four HRL training conditions with three matched training seeds per condition.',
        'Each selected policy received 16 continuous-homeostasis CCC trials on an environment seed excluded from checkpoint selection. '
        'The initial h values and resource layouts match across policies. Variation is summarized across trained policies.',
        '', '| Training condition | Mean time-MAE | SD across policies | Per-seed MAE | Time within ±5 | Final-window revisit fraction |',
        '|---|---:|---:|---|---:|---:|']
    for row in summary:
        lines.append('| '+row['condition']+f" | {row['mean_time_mae']:.3f} | {row['sd_between_policies']:.3f} | "+
            ', '.join(f'{x:.3f}' for x in row['per_seed_time_mae'])+
            f" | {100*row['mean_fraction_within_5']:.1f}% | {100*row['mean_phase_3_revisit_fraction']:.1f}% |")
    lines.extend(['',f"The preserved selected HRL policy scored {output['selected_reference_time_mae']:.3f} time-MAE in the same comparison environments. It is one fixed policy benchmark.",
        '', 'Planned contrasts report the second condition minus the first; negative MAE differences favor the second condition.',
        '', '| Contrast | Mean MAE difference | Exploratory paired 95% t interval | Exact sign-flip p, Holm adjusted |',
        '|---|---:|---|---:|'])
    for row in comparisons:
        lo,hi=row['paired_t_95_interval'];lines.append(f"| {row['second']} minus {row['first']} | {row['mean_difference']:.3f} | [{lo:.3f}, {hi:.3f}] | {row['holm_exact_p']:.3f} |")
    lines.extend(['', 'Three training seeds provide limited inferential precision. Repeated evaluation trials do not add independent training replicates. '
        'This screen does not isolate the causal benefit of traversal-dependent costs because it has no matched condition with those costs disabled. '
        'The inherited phase-start velocity initialization is common to every policy; h and tile history carry between reporting windows.',
        '', 'Candidate snapshots, raw comparison scenes, traversal histories, loaded-model receipts and training diagnostics are retained beside this note. '
        'The production assets, selected policies and existing paper data remain preserved. No candidate is promoted automatically.'])
    (HERE/'RESULTS.md').write_text('\n\n'.join(lines[:2])+'\n'+'\n'.join(lines[2:])+'\n')
    print('STUDY_ANALYSIS_COMPLETE '+str(HERE/'results.json'))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['evaluate','summarize'])
    command=parser.parse_args().command
    evaluate() if command=='evaluate' else summarize()
