"""Freeze native factor data, reproduce all descriptive and planned contrasts.

python3 analyze.py --import-run /path/to/Saved/AnticipationPlasticity20261026
python3 analyze.py                      # reproduce from frozen compact inputs
Rscript --vanilla bootstrap_and_plot.R  # independent checks, relative effects
python3 write_report.py
"""
from pathlib import Path
import argparse,csv,gzip,hashlib,itertools,json,math,re,shutil,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import build_analysis as shared
METRICS=shared.METRICS
OUTCOMES=['homeostatic-mae','reward-total']
FACTORS=[0,1,2,4,7]
read=lambda p:json.loads(Path(p).read_text())
def dump(name,obj):
 (HERE/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def save(name,rows):
 with (HERE/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def import_run(root):
 root=root.resolve();complete=read(root/'complete.json');assert complete['passed'] and complete['source_preserved']
 inputs=HERE/'inputs';inputs.mkdir(exist_ok=True);files={};selection={}
 def copy(source,name):
  target=inputs/name;shutil.copyfile(source,target)
  files[str(target.relative_to(HERE))]=dict(source=str(source),sha256=shared.sha(target),bytes=target.stat().st_size)
 for factor in FACTORS[1:]:
  record=read(root/f'factor-{factor}/verified.json');assert record['passed'] and record['factor']==factor and record['trials']==250
  source=Path(record['metrics']);assert shared.sha(source)==record['metrics_sha256']
  run=read(source);rid=run['run-id'];selection[str(factor)]=rid
  for suffix in ['.metrics.json','.yml','.completed.json']:
   copy(source.parent/(rid+suffix),f'factor-{factor}'+suffix)
  copy(root/f'factor-{factor}/verified.json',f'factor-{factor}.verified.json')
 for name in ['protocol.json','complete.json','source_preservation.json']:
  copy(root/name,name)
 audit=read(HERE/'count_rule_validation.json')
 assert audit['passed'] and len(audit['tests'])==17 and audit['asset_unchanged_after_audit']
 baseline_run=read(next((HERE.parent/'inputs').glob('HRL-CDR*.metrics.json')))
 assert audit['asset_sha256']==baseline_run['provenance']['asset-sha256']['Level/BP_Tile']
 copy(HERE/'count_rule_validation.json','count_rule_validation.json')
 # Summarize actual phase-start landscape counts in both original reference
 # conditions, with a fresh audit of the 1,500 reference scene hashes.
 reference_counts=[]
 comparison=read(root.parents[1]/'analysis/anticipation-retrained-2026-10-25/comparison.json')
 for order,label in [('cdr','CDR-0'),('ccc','CCC')]:
  raw=Path(comparison['HRL'][order]['metrics']);run=read(raw);totals={1:[],2:[],3:[]}
  for trial in run['trials']:
   for phase in trial['phases']:
    blob=gzip.decompress((raw.parent/phase['scene-file']).read_bytes())
    assert hashlib.sha256(blob).hexdigest()==phase['scene-sha256']
    scene=json.loads(blob);assert len(scene['tiles'])==2500
    assert all(t['DecanalizationRateFactor']==0 for t in scene['tiles'])
    totals[phase['sequence-idx']].append(sum(t['OverlapCount'] for t in scene['tiles']))
  for phase,counts in totals.items():reference_counts.append(dict(condition=label,phase=phase,n=len(counts),mean=sum(counts)/len(counts),minimum=min(counts),maximum=max(counts)))
 # Keep analysis artifacts in the paper package, not the native source folder.
 target=inputs/'reference_landscape_counts.json';target.write_text(json.dumps(dict(scene_hashes_verified=1500,rows=reference_counts),indent=2)+'\n')
 files[str(target.relative_to(HERE))]=dict(source='Derived from hashed native reference scenes named by '+str(root.parents[1]/'analysis/anticipation-retrained-2026-10-25/comparison.json'),sha256=shared.sha(target),bytes=target.stat().st_size)
 dump('selection.json',selection)
 dump('source_manifest.json',dict(source_run=str(root),files=files,
   baseline_source_manifest_sha256=shared.sha(HERE.parent/'source_manifest.json'),
   analysis_plan_sha256=shared.sha(HERE/'ANALYSIS_PLAN.md')))
def load_factor(factor,catalog):
 name=f'factor-{factor}';run=read(HERE/'inputs'/(name+'.metrics.json'));v=run['provenance']
 receipt=read(HERE/'inputs'/(name+'.completed.json'));record=read(HERE/'inputs'/(name+'.verified.json'))
 assert receipt['results_saved'] and receipt['trials_completed']==receipt['trials_requested']==250
 assert record['passed'] and record['scene_hashes_verified']==750 and record['loaded_models_verified']==3
 assert shared.sha(HERE/'inputs'/(name+'.metrics.json'))==record['metrics_sha256']
 assert run['status']=='complete' and run['schema-version']==2
 e=v['environment'];assert e['IsHRL'] and e['TrialSequenceOrder']=='cdr'
 assert e['TrialEnvironmentSeed']==e['ActiveEnvironmentSeed']==10001
 assert e['BasePassiveLossRate']==.5 and e['PeriodTickLength']==5
 assert v['simulation-dt-seconds']==.05 and v['phase-decision-ticks']==2000
 assert v['asset-sha256']['Agent/BP_Agent']==catalog['anticipation_asset_sha256']
 for k,s in v['snapshots'].items():assert s['loaded-sha256']==catalog['policies']['HRL']['snapshots'][k]['sha256']
 text=(HERE/'inputs'/(name+'.yml')).read_text()
 assert 'schema-version: 2' in text and 'duration-unit: simulation-seconds' in text
 blocks=re.split(r'^  - state: ',text,flags=re.M)[1:];assert len(blocks)==750
 logged=[{m:float(re.search(r'^    '+re.escape(m)+r': (.+)$',b,re.M).group(1)) for m in ['setpoint-avg','setpoint-dev','reward-total','loss-total','gain-total','gains-harvested','duration']} for b in blocks]
 assert [t['id'] for t in run['trials']]==list(range(250));data=[];flat=[]
 for t in run['trials']:
  assert t['reward-function']=='HRL' and t['sequence-order']=='cdr'
  assert [p['sequence-idx'] for p in t['phases']]==[1,2,3];phases=[]
  for p in t['phases']:
   q=logged[t['id']*3+p['sequence-idx']-1]
   assert p['complete'] and p['decision-ticks']==2000 and p['duration-seconds']==q['duration']==100
   for m in ['setpoint-avg','setpoint-dev','reward-total']:shared.close(p[m],q[m])
   shared.close(p['homeostatic-rms']**2,p['setpoint-dev']**2+p['setpoint-avg']**2)
   vals={m:p[m] if m in p else q[m] for m in METRICS}
   assert all(math.isfinite(x) for x in vals.values())
   assert vals['homeostatic-mae']>=0 and vals['setpoint-dev']>=0 and 0<=vals['reward-total']<=100.001
   assert 0<=vals['homeostatic-fraction-within-5']<=1 and p['homeostatic-sample-count']>0
   phases.append(vals)
   flat.append(dict(condition='CDR-'+str(factor),factor=factor,trial=t['id'],phase=p['sequence-idx'],sample_count=p['homeostatic-sample-count'],**vals))
  data.append(phases)
 return data,run,flat
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--import-run',type=Path);args=parser.parse_args()
 if args.import_run:import_run(args.import_run)
 manifest=read(HERE/'source_manifest.json')
 for name,x in manifest['files'].items():assert shared.sha(HERE/name)==x['sha256']
 assert shared.sha(HERE.parent/'source_manifest.json')==manifest['baseline_source_manifest_sha256']
 assert shared.sha(HERE/'ANALYSIS_PLAN.md')==manifest['analysis_plan_sha256']
 original,runs,baseline_flat=shared.load_inputs()
 arrays={'CDR-0':original['HRL-CDR'],'CCC':original['HRL-CCC']}
 rawruns={'CDR-0':runs['HRL-CDR'],'CCC':runs['HRL-CCC']}
 flat=[]
 for r in baseline_flat:
  if r['family']!='HRL':continue
  flat.append(dict(condition='CDR-0' if r['order']=='cdr' else 'CCC',factor=0 if r['order']=='cdr' else '',trial=r['trial'],phase=r['phase'],sample_count=r['sample_count'],**{m:r[m] for m in METRICS}))
 catalog=read(HERE.parent/'inputs/selected_policy_catalog.json')
 for factor in FACTORS[1:]:
  data,run,rows=load_factor(factor,catalog);arrays['CDR-'+str(factor)]=data;rawruns['CDR-'+str(factor)]=run;flat+=rows
 summary=[];primary=[];pairwise=[];sensitivity=[];alignment=[];relative=[];matched_rows=[]
 pairs=[('CDR-'+str(f),reference) for f in FACTORS[1:] for reference in ['CDR-0','CCC']]
 for name,a in arrays.items():
  for phase in range(3):
   for m in METRICS:
    x=[t[phase][m] for t in a]
    summary.append(dict(condition=name,phase=phase+1,metric=m,**shared.describe(x),minimum=min(x),maximum=max(x)))
 for condition,reference in pairs:
  a,b=arrays[condition],arrays[reference];ra,rb=rawruns[condition],rawruns[reference]
  start_fields=['rng-start','policy-memory-start','initial-homeostatic-state','observed-start-h']
  matched=[i for i in range(250) if all(a[i][0][m]==b[i][0][m] for m in METRICS) and all(ra['trials'][i]['phases'][0][k]==rb['trials'][i]['phases'][0][k] for k in start_fields)]
  assert len(matched)>=2
  matched_rows.extend(dict(condition=condition,reference=reference,trial=i) for i in matched)
  alignment.append(dict(condition=condition,reference=reference,
    baseline_matched_trials=len(matched),
    identical_baseline_metrics={m:sum(t[0][m]==u[0][m] for t,u in zip(a,b)) for m in METRICS},
    matching_start_fields={k:sum(t['phases'][0][k]==u['phases'][0][k] for t,u in zip(ra['trials'],rb['trials'])) for k in ['rng-start','policy-memory-start','initial-homeostatic-state','observed-start-h']}))
  for phase in [1,2]:
   for m in OUTCOMES:
    x=[t[phase][m] for t in a];y=[t[phase][m] for t in b]
    primary.append(dict(condition=condition,reference=reference,phase=phase+1,metric=m,method='Welch',**shared.compare(x,y)))
    for method,change,paired,indices in [('Welch-change',True,False,range(250)),('paired-ID',False,True,range(250)),('paired-ID-change',True,True,range(250)),('paired-baseline-matched',False,True,matched)]:
     xx=[a[i][phase][m]-(a[i][0][m] if change else 0) for i in indices]
     yy=[b[i][phase][m]-(b[i][0][m] if change else 0) for i in indices]
     sensitivity.append(dict(condition=condition,reference=reference,phase=phase+1,metric=m,method=method,**shared.compare(xx,yy,paired)))
 for lower,higher in itertools.combinations(FACTORS,2):
  a,b=arrays['CDR-'+str(higher)],arrays['CDR-'+str(lower)]
  for phase in [1,2]:
   for m in OUTCOMES:
    pairwise.append(dict(higher_factor=higher,lower_factor=lower,phase=phase+1,metric=m,method='Welch',**shared.compare([t[phase][m] for t in a],[t[phase][m] for t in b])))
 for phase in [2,3]:
  shared.holm([r for r in primary if r['phase']==phase])
  shared.holm([r for r in pairwise if r['phase']==phase])
  for method in ['Welch-change','paired-ID','paired-ID-change','paired-baseline-matched']:
   shared.holm([r for r in sensitivity if r['phase']==phase and r['method']==method])
 # Relative effects against both factor 0, ordinary counting, and CCC.
 for factor in FACTORS:
  condition='CDR-'+str(factor)
  for reference in ['CDR-0','CDR-1','CCC']:
   if condition==reference:continue
   for m in OUTCOMES:
    a=shared.st.mean(t[2][m] for t in arrays[condition]);b=shared.st.mean(t[2][m] for t in arrays[reference])
    direction=-1 if m=='homeostatic-mae' else 1
    relative.append(dict(condition=condition,reference=reference,metric=m,condition_mean=a,reference_mean=b,
                         difference=a-b,improvement_percent=direction*100*(a-b)/b))
 save('trial_metrics.csv',flat);save('phase_summary.csv',summary);save('primary_contrasts.csv',primary)
 save('factor_pairwise.csv',pairwise);save('sensitivity.csv',sensitivity);save('relative_effects.csv',relative)
 save('baseline_matched_ids.csv',matched_rows)
 landscape=read(HERE/'inputs/reference_landscape_counts.json')['rows']
 for factor in FACTORS[1:]:
  record=read(HERE/'inputs'/f'factor-{factor}.verified.json')
  for phase,x in record['tile_count_totals_by_phase'].items():
   landscape.append(dict(condition='CDR-'+str(factor),phase=int(phase),n=250,mean=x['mean'],minimum=x['min'],maximum=x['max']))
 save('landscape_counts.csv',landscape)
 dump('verification.json',dict(passed=True,conditions=6,trials=1500,phases=4500,decisions=9000000,
      new_trials=1000,reused_reference_trials=500,new_scene_hashes_verified=3000,new_loaded_models_verified=12,
      all_fixed_input_hashes_verified=True,raw_json_yaml_agreement=True,baseline_alignment=alignment,
      descriptive_rows=len(summary),primary_contrasts=len(primary),factor_pairwise_contrasts=len(pairwise),sensitivity_contrasts=len(sensitivity)))
 print('Analysis ready; primary phase-3 contrasts:')
 for r in primary:
  if r['phase']==3:print(r)
if __name__=='__main__':main()
