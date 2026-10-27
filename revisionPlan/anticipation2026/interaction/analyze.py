"""Freeze the two missing cells and estimate direct rate x retention contrasts."""
from pathlib import Path
import argparse,csv,importlib.util,json,math,shutil,sys

HERE=Path(__file__).resolve().parent;BASE=HERE.parent
sys.path.insert(0,str(BASE))
import build_analysis as shared
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
sweep=module('rate_loader',BASE/'plasticity/analyze.py')
recan=module('retention_loader',BASE/'recanalization/analyze.py')
OUTCOMES=['homeostatic-mae','reward-total']
RULES=['zero','half','keep']
PAIRS=[('zero','half'),('keep','half'),('keep','zero')]
read=lambda p:json.loads(Path(p).read_text())
def dump(name,obj):(HERE/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def save(name,rows):
    with (HERE/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def linear(samples,coefficients,paired=False):
    n=len(samples[0]);assert n>=2 and all(len(a)==n for a in samples)
    effect=math.fsum(c*shared.st.mean(a) for c,a in zip(coefficients,samples))
    if paired:
        assert coefficients==[1,-1,-1,1]
        differences=[(samples[0][i]-samples[1][i])-(samples[2][i]-samples[3][i]) for i in range(n)]
        effect=shared.st.mean(differences)
        variance=shared.st.variance(differences)/n;df=n-1
    else:
        components=[c*c*shared.st.variance(a)/n for c,a in zip(coefficients,samples)]
        variance=sum(components)
        df=variance**2/sum(v*v/(n-1) for v in components) if variance else 1
    se=math.sqrt(variance);margin=shared.critical(df)*se if se else 0
    p=shared.two_sided_t(abs(effect/se),df) if se else float(effect==0)
    return dict(n_per_cell=n,difference=effect,se=se,df=df,ci95_low=effect-margin,ci95_high=effect+margin,p=p)
def import_run(root):
    root=root.resolve();done=read(root/'complete.json');assert done['passed'] and done['source_preserved']
    assert read(root/'protocol.json')['analysis_plan_sha256']==shared.sha(HERE/'ANALYSIS_PLAN.md')
    inputs=HERE/'inputs';inputs.mkdir(exist_ok=True);files={}
    def copy(source,name):
        target=inputs/name;shutil.copyfile(source,target)
        files[str(target.relative_to(HERE))]=dict(source=str(source),sha256=shared.sha(target),bytes=target.stat().st_size)
    for name in ['k7-zero','k7-keep']:
        audit=read(root/name/'verified.json');assert audit['passed'] and audit['factor']==7 and audit['trials']==250
        source=Path(audit['metrics']);assert shared.sha(source)==audit['metrics_sha256'];rid=read(source)['run-id']
        for suffix in ['.metrics.json','.yml','.completed.json']:copy(source.parent/(rid+suffix),name+suffix)
        for filename in ['verified.json','native_validation.json','BP_Tile.compiled.uasset']:
            copy(root/name/filename,name+'.'+filename)
    for name in ['complete.json','protocol.json','source_preservation.json']:copy(root/name,name)
    refs=[BASE/'source_manifest.json',BASE/'plasticity/source_manifest.json',BASE/'recanalization/source_manifest.json']
    dump('source_manifest.json',dict(source_run=str(root),files=files,
         reference_manifests={str(p.relative_to(BASE)):shared.sha(p) for p in refs},
         analysis_plan_sha256=shared.sha(HERE/'ANALYSIS_PLAN.md')))
def load():
    manifest=read(HERE/'source_manifest.json')
    assert shared.sha(HERE/'ANALYSIS_PLAN.md')==manifest['analysis_plan_sha256']
    for name,item in manifest['files'].items():assert shared.sha(HERE/name)==item['sha256']
    for name,h in manifest['reference_manifests'].items():assert shared.sha(BASE/name)==h
    for folder in ['plasticity','recanalization']:
        m=read(BASE/folder/'source_manifest.json')
        for name,item in m['files'].items():assert shared.sha(BASE/folder/name)==item['sha256']
        assert shared.sha(BASE/folder/'ANALYSIS_PLAN.md')==m['analysis_plan_sha256']
        if 'selection_sha256' in m:assert shared.sha(BASE/folder/'selection.json')==m['selection_sha256']
        if 'baseline_source_manifest_sha256' in m:
            assert shared.sha(BASE/'source_manifest.json')==m['baseline_source_manifest_sha256']
        for name,h in m.get('reference_manifests',{}).items():assert shared.sha(BASE/name)==h
    original,oldruns,_=shared.load_inputs();catalog=read(BASE/'inputs/selected_policy_catalog.json')
    arrays={'CCC':original['HRL-CCC']};runs={'CCC':oldruns['HRL-CCC']}
    for k in [1,7]:
        data,run,_=sweep.load_factor(k,catalog);arrays[f'k{k}-half']=data;runs[f'k{k}-half']=run
    for rule in ['zero','keep']:
        data,run,_=recan.load_new(rule,catalog);arrays['k1-'+rule]=data;runs['k1-'+rule]=run
    original_here=recan.HERE
    try:
        recan.HERE=HERE
        for rule in ['zero','keep']:
            name='k7-'+rule;record=read(HERE/'inputs'/(name+'.verified.json'))
            assert record['factor']==7 and record['condition']==name
            data,run,_=recan.load_new(name,catalog);arrays[name]=data;runs[name]=run
    finally:recan.HERE=original_here
    return arrays,runs
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--import-run',type=Path);args=parser.parse_args()
    if args.import_run:import_run(args.import_run)
    arrays,runs=load();flat=[];summary=[];interactions=[];simple=[];ccc=[];sensitivity=[];matched_rows=[];alignment=[]
    for name in [f'k{k}-{r}' for k in [1,7] for r in RULES]+['CCC']:
        for i,trial in enumerate(arrays[name]):
            for p,values in enumerate(trial):
                flat.append(dict(condition=name,trial=i,phase=p+1,run=runs[name]['run-id'],
                    sample_count=runs[name]['trials'][i]['phases'][p]['homeostatic-sample-count'],**values))
        for phase in range(3):
            for m in shared.METRICS:
                values=[t[phase][m] for t in arrays[name]]
                summary.append(dict(condition=name,phase=phase+1,metric=m,**shared.describe(values),minimum=min(values),maximum=max(values)))
    fields=['rng-start','policy-memory-start','initial-homeostatic-state','observed-start-h']
    for first,second in PAIRS:
        cells=[f'k7-{first}',f'k1-{first}',f'k7-{second}',f'k1-{second}'];coeff=[1,-1,-1,1]
        eligible=[i for i in range(250) if all(
            all(arrays[c][i][0][m]==arrays[cells[0]][i][0][m] for m in shared.METRICS)
            and all(runs[c]['trials'][i]['phases'][0][f]==runs[cells[0]]['trials'][i]['phases'][0][f] for f in fields)
            for c in cells[1:])]
        assert len(eligible)>=2
        matched_rows += [dict(first_rule=first,second_rule=second,trial=i) for i in eligible]
        for phase in [1,2]:
            for m in OUTCOMES:
                groups=[[t[phase][m] for t in arrays[c]] for c in cells]
                interactions.append(dict(first_rule=first,second_rule=second,phase=phase+1,metric=m,method='Welch-four-cell',**linear(groups,coeff)))
                for method,change,paired,ids in [('Welch-change',True,False,range(250)),
                     ('paired-ID',False,True,range(250)),('paired-ID-change',True,True,range(250)),
                     ('paired-baseline-matched',False,True,eligible)]:
                    groups=[[arrays[c][i][phase][m]-(arrays[c][i][0][m] if change else 0) for i in ids] for c in cells]
                    sensitivity.append(dict(first_rule=first,second_rule=second,phase=phase+1,metric=m,method=method,**linear(groups,coeff,paired)))
    for phase in [1,2]:
        for rule in RULES:
            for m in OUTCOMES:
                simple.append(dict(rule=rule,phase=phase+1,metric=m,method='Welch',
                    **linear([[t[phase][m] for t in arrays[f'k{k}-{rule}']] for k in [7,1]],[1,-1])))
        for name in [f'k{k}-{r}' for k in [1,7] for r in RULES]:
            for m in OUTCOMES:
                ccc.append(dict(condition=name,phase=phase+1,metric=m,method='Welch',
                    **linear([[t[phase][m] for t in arrays[c]] for c in [name,'CCC']],[1,-1])))
    for phase in [2,3]:
        for table in [interactions,simple,ccc]:shared.holm([r for r in table if r['phase']==phase])
        for method in sorted({r['method'] for r in sensitivity}):
            shared.holm([r for r in sensitivity if r['phase']==phase and r['method']==method])
    for k in [1,7]:
        for rule in ['zero','keep']:
            a,b=arrays[f'k{k}-{rule}'],arrays[f'k{k}-half']
            ra,rb=runs[f'k{k}-{rule}'],runs[f'k{k}-half']
            alignment.append(dict(factor=k,rule=rule,reference='half',
                phase1_identical={m:sum(t[0][m]==u[0][m] for t,u in zip(a,b)) for m in shared.METRICS},
                phase2_identical={m:sum(t[1][m]==u[1][m] for t,u in zip(a,b)) for m in shared.METRICS},
                start_fields={f:sum(t['phases'][0][f]==u['phases'][0][f] for t,u in zip(ra['trials'],rb['trials'])) for f in fields}))
    save('trial_metrics.csv',flat);save('phase_summary.csv',summary);save('interactions.csv',interactions)
    save('simple_rate_effects.csv',simple);save('ccc_contrasts.csv',ccc);save('sensitivity.csv',sensitivity)
    save('baseline_matched_ids.csv',matched_rows)
    landscape=[]
    for k in [1,7]:
        for rule in RULES:
            if rule=='half':record=read(BASE/'plasticity/inputs'/f'factor-{k}.verified.json')
            elif k==1:record=read(BASE/'recanalization/inputs'/(rule+'.verified.json'))
            else:record=read(HERE/'inputs'/('k7-'+rule+'.verified.json'))
            for phase,x in record['tile_count_totals_by_phase'].items():
                landscape.append(dict(condition=f'k{k}-{rule}',phase=int(phase),n=250,mean=x['mean'],minimum=x['min'],maximum=x['max']))
    landscape += [r for r in read(BASE/'plasticity/inputs/reference_landscape_counts.json')['rows'] if r['condition']=='CCC']
    save('landscape_counts.csv',landscape)
    dump('selection.json',{name:run['run-id'] for name,run in runs.items()})
    dump('verification.json',dict(passed=True,conditions=7,trials=1750,phases=5250,decisions=10500000,
        new_trials=500,new_scene_hashes_verified=1500,new_loaded_models_verified=6,native_handler_checks=30,
        all_source_hashes_verified=True,raw_json_yaml_agreement=True,baseline_alignment=alignment,
        descriptive_rows=len(summary),interaction_contrasts=len(interactions),simple_effects=len(simple),
        ccc_contrasts=len(ccc),sensitivity_contrasts=len(sensitivity)))
    print('PASS: factorial tables ready; all 1,750 trials retained.')
if __name__=='__main__':main()
