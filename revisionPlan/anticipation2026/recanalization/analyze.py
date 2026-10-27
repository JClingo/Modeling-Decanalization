"""Freeze and analyze completed native recanalization-count evaluations."""
from pathlib import Path
import argparse,csv,importlib.util,itertools,json,math,re,shutil,sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
sys.path.insert(0,str(BASE))
import build_analysis as shared
spec=importlib.util.spec_from_file_location('frozen_count_sweep',BASE/'plasticity/analyze.py')
sweep=importlib.util.module_from_spec(spec);spec.loader.exec_module(sweep)
CONDITIONS=['zero','quarter-floor','half-floor','three-quarter-floor','keep','half-exact']
OUTCOMES=['homeostatic-mae','reward-total']
read=lambda p:json.loads(Path(p).read_text())
def dump(name,obj):(HERE/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def save(name,rows):
    with (HERE/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def import_run(root):
    root=root.resolve();complete=read(root/'complete.json')
    assert complete['passed'] and complete['source_preserved']
    assert read(root/'protocol.json')['analysis_plan_sha256']==shared.sha(HERE/'ANALYSIS_PLAN.md')
    inputs=HERE/'inputs';inputs.mkdir(exist_ok=True)
    files={};selected={}
    def copy(source,name):
        target=inputs/name;shutil.copyfile(source,target)
        files[str(target.relative_to(HERE))]=dict(source=str(source),sha256=shared.sha(target),bytes=target.stat().st_size)
    for name in CONDITIONS:
        if name=='half-floor':continue
        audit=read(root/name/'verified.json')
        assert audit['passed'] and audit['condition']==name and audit['trials']==250
        source=Path(audit['metrics']);assert shared.sha(source)==audit['metrics_sha256']
        rid=read(source)['run-id'];selected[name]=rid
        for suffix in ['.metrics.json','.yml','.completed.json']:
            copy(source.parent/(rid+suffix),name+suffix)
        for filename in ['verified.json','native_validation.json','BP_Tile.compiled.uasset']:
            copy(root/name/filename,name+'.'+filename)
    for filename in ['complete.json','protocol.json','source_preservation.json']:
        copy(root/filename,filename)
    selected['half-floor']=read(BASE/'plasticity/inputs/factor-1.metrics.json')['run-id']
    selected['CCC']=read(BASE/'selection.json')['HRL-CCC']
    dump('selection.json',selected)
    dump('source_manifest.json',dict(source_run=str(root),files=files,
         reference_manifests={str(p.relative_to(BASE)):shared.sha(p) for p in
              [BASE/'source_manifest.json',BASE/'plasticity/source_manifest.json']},
         selection_sha256=shared.sha(HERE/'selection.json'),
         analysis_plan_sha256=shared.sha(HERE/'ANALYSIS_PLAN.md')))
def load_new(name,catalog):
    run=read(HERE/'inputs'/(name+'.metrics.json'))
    receipt=read(HERE/'inputs'/(name+'.completed.json'))
    audit=read(HERE/'inputs'/(name+'.verified.json'))
    native=read(HERE/'inputs'/(name+'.native_validation.json'))
    v=run['provenance'];e=v['environment']
    assert run['status']=='complete' and run['schema-version']==2
    assert receipt['results_saved'] and receipt['trials_completed']==receipt['trials_requested']==250
    assert audit['passed'] and audit['scene_hashes_verified']==750 and audit['loaded_models_verified']==3
    assert native['passed'] and native['asset_unchanged_after_audit'] and len(native['tests'])==15
    assert shared.sha(HERE/'inputs'/(name+'.metrics.json'))==audit['metrics_sha256']
    assert shared.sha(HERE/'inputs'/(name+'.BP_Tile.compiled.uasset'))==audit['tile_asset_sha256']==native['asset_sha256']==v['asset-sha256']['Level/BP_Tile']
    assert e['IsHRL'] and e['TrialSequenceOrder']=='cdr'
    assert e['TrialEnvironmentSeed']==e['ActiveEnvironmentSeed']==10001
    assert v['simulation-dt-seconds']==.05 and v['phase-decision-ticks']==2000
    assert e['BasePassiveLossRate']==.5 and e['PeriodTickLength']==5
    assert v['asset-sha256']['Agent/BP_Agent']==catalog['anticipation_asset_sha256']
    for k,s in v['snapshots'].items():assert s['loaded-sha256']==catalog['policies']['HRL']['snapshots'][k]['sha256']
    text=(HERE/'inputs'/(name+'.yml')).read_text()
    assert 'schema-version: 2' in text and 'duration-unit: simulation-seconds' in text
    blocks=re.split(r'^  - state: ',text,flags=re.M)[1:];assert len(blocks)==750
    logged=[{m:float(re.search(r'^    '+re.escape(m)+r': (.+)$',b,re.M).group(1)) for m in
             ['setpoint-avg','setpoint-dev','reward-total','loss-total','gain-total','gains-harvested','duration']} for b in blocks]
    assert [t['id'] for t in run['trials']]==list(range(250))
    data=[];flat=[]
    for trial in run['trials']:
        assert trial['reward-function']=='HRL' and trial['sequence-order']=='cdr'
        assert [p['sequence-idx'] for p in trial['phases']]==[1,2,3]
        phases=[]
        for p in trial['phases']:
            q=logged[trial['id']*3+p['sequence-idx']-1]
            assert p['complete'] and p['decision-ticks']==2000 and p['duration-seconds']==q['duration']==100
            for m in ['setpoint-avg','setpoint-dev','reward-total']:shared.close(p[m],q[m])
            shared.close(p['homeostatic-rms']**2,p['setpoint-dev']**2+p['setpoint-avg']**2)
            values={m:p[m] if m in p else q[m] for m in shared.METRICS}
            assert all(math.isfinite(x) for x in values.values())
            assert values['homeostatic-mae']>=0 and values['setpoint-dev']>=0
            assert 0<=values['homeostatic-fraction-within-5']<=1
            assert 0<=values['reward-total']<=100.001 and p['homeostatic-sample-count']>0
            phases.append(values)
            flat.append(dict(condition=name,trial=trial['id'],phase=p['sequence-idx'],
                             sample_count=p['homeostatic-sample-count'],**values))
        data.append(phases)
    return data,run,flat
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--import-run',type=Path);args=parser.parse_args()
    if args.import_run:import_run(args.import_run)
    manifest=read(HERE/'source_manifest.json')
    assert shared.sha(HERE/'selection.json')==manifest['selection_sha256']
    selected=read(HERE/'selection.json')
    for name,item in manifest['files'].items():assert shared.sha(HERE/name)==item['sha256']
    for name,h in manifest['reference_manifests'].items():assert shared.sha(BASE/name)==h
    assert shared.sha(HERE/'ANALYSIS_PLAN.md')==manifest['analysis_plan_sha256']
    old,runs,oldflat=shared.load_inputs()
    sm=read(BASE/'plasticity/source_manifest.json')
    for name,item in sm['files'].items():assert shared.sha(BASE/'plasticity'/name)==item['sha256']
    catalog=read(BASE/'inputs/selected_policy_catalog.json')
    a,ra,rows=sweep.load_factor(1,catalog)
    arrays={'half-floor':a,'CCC':old['HRL-CCC']}
    raw={'half-floor':ra,'CCC':runs['HRL-CCC']}
    flat=[dict(condition='half-floor',**{k:v for k,v in r.items() if k not in ['condition','factor']}) for r in rows]
    flat += [dict(condition='CCC',**{k:v for k,v in r.items() if k not in ['family','order','run']})
             for r in oldflat if r['family']=='HRL' and r['order']=='ccc']
    for name in CONDITIONS:
        if name=='half-floor':continue
        a,run,rows=load_new(name,catalog);arrays[name]=a;raw[name]=run;flat+=rows
    assert {name:run['run-id'] for name,run in raw.items()}==selected
    summary=[];primary=[];standard=[];pairwise=[];sensitivity=[];alignment=[];matched_rows=[]
    for name in [*CONDITIONS,'CCC']:
        for phase in range(3):
            for metric in shared.METRICS:
                values=[t[phase][metric] for t in arrays[name]]
                summary.append(dict(condition=name,phase=phase+1,metric=metric,
                                    **shared.describe(values),minimum=min(values),maximum=max(values)))
    comparisons=[(c,'CCC','vs-CCC') for c in CONDITIONS]+[(c,'half-floor','vs-current') for c in CONDITIONS if c!='half-floor']
    fields=['rng-start','policy-memory-start','initial-homeostatic-state','observed-start-h']
    for condition,reference,family in comparisons:
        a,b=arrays[condition],arrays[reference];ra,rb=raw[condition],raw[reference]
        matched=[i for i in range(250) if all(a[i][0][m]==b[i][0][m] for m in shared.METRICS)
                 and all(ra['trials'][i]['phases'][0][k]==rb['trials'][i]['phases'][0][k] for k in fields)]
        assert len(matched)>=2
        matched_rows += [dict(condition=condition,reference=reference,trial=i) for i in matched]
        alignment.append(dict(condition=condition,reference=reference,baseline_matched_trials=len(matched),
            phase1_identical={m:sum(t[0][m]==u[0][m] for t,u in zip(a,b)) for m in shared.METRICS},
            phase2_identical={m:sum(t[1][m]==u[1][m] for t,u in zip(a,b)) for m in shared.METRICS},
            start_fields={k:sum(t['phases'][0][k]==u['phases'][0][k] for t,u in zip(ra['trials'],rb['trials'])) for k in fields}))
        for phase in [1,2]:
            for metric in OUTCOMES:
                row=dict(condition=condition,reference=reference,phase=phase+1,metric=metric,method='Welch',
                         **shared.compare([t[phase][metric] for t in a],[t[phase][metric] for t in b]))
                (primary if family=='vs-CCC' else standard).append(row)
                for method,change,paired,ids in [('Welch-change',True,False,range(250)),
                    ('paired-ID',False,True,range(250)),('paired-ID-change',True,True,range(250)),
                    ('paired-baseline-matched',False,True,matched)]:
                    x=[a[i][phase][metric]-(a[i][0][metric] if change else 0) for i in ids]
                    y=[b[i][phase][metric]-(b[i][0][metric] if change else 0) for i in ids]
                    sensitivity.append(dict(comparison_family=family,condition=condition,reference=reference,
                        phase=phase+1,metric=metric,method=method,**shared.compare(x,y,paired)))
    for condition,reference in itertools.combinations(CONDITIONS,2):
        for phase in [1,2]:
            for metric in OUTCOMES:
                pairwise.append(dict(condition=condition,reference=reference,phase=phase+1,metric=metric,method='Welch',
                     **shared.compare([t[phase][metric] for t in arrays[condition]],[t[phase][metric] for t in arrays[reference]])))
    for phase in [2,3]:
        for table in [primary,standard,pairwise]:shared.holm([r for r in table if r['phase']==phase])
        for family in ['vs-CCC','vs-current']:
            for method in sorted({r['method'] for r in sensitivity}):
                shared.holm([r for r in sensitivity if r['phase']==phase and r['method']==method and r['comparison_family']==family])
    save('trial_metrics.csv',flat);save('phase_summary.csv',summary);save('primary_contrasts.csv',primary)
    save('versus_current.csv',standard);save('all_pairwise.csv',pairwise);save('sensitivity.csv',sensitivity)
    save('baseline_matched_ids.csv',matched_rows)
    landscape=[]
    for name in CONDITIONS:
        if name=='half-floor':record=read(BASE/'plasticity/inputs/factor-1.verified.json')
        else:record=read(HERE/'inputs'/(name+'.verified.json'))
        for phase,x in record['tile_count_totals_by_phase'].items():
            landscape.append(dict(condition=name,phase=int(phase),n=250,mean=x['mean'],minimum=x['min'],maximum=x['max']))
    for r in read(BASE/'plasticity/inputs/reference_landscape_counts.json')['rows']:
        if r['condition']=='CCC':landscape.append(r)
    save('landscape_counts.csv',landscape)
    dump('verification.json',dict(passed=True,conditions=7,trials=1750,phases=5250,decisions=10500000,
        new_trials=1250,new_scene_hashes_verified=3750,new_loaded_models_verified=15,
        native_handler_checks=75,source_hashes_verified=True,raw_json_yaml_agreement=True,
        baseline_alignment=alignment,descriptive_rows=len(summary),primary_contrasts=len(primary),
        versus_current_contrasts=len(standard),all_pairwise_contrasts=len(pairwise),sensitivity_contrasts=len(sensitivity)))
    print('PASS: recanalization tables ready; all 1,750 trials retained.')
if __name__=='__main__':main()
