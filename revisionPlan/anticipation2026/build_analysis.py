"""Freeze and analyze corrected-anticipation trials without modifying Unreal data.

First import: python3 build_analysis.py --import-source /path/to/anticipation-retrained-2026-10-25
Reproduce from the frozen compact inputs: python3 build_analysis.py
All statistics use Python's standard library. R independently verifies Welch
statistics and draws figures (verify_and_plot.R). Scenes/models remain in the
source archive; their bytes are audited on import, not copied into this folder.
"""
from pathlib import Path
import argparse, csv, gzip, hashlib, json, math, re, shutil, statistics as st

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / 'rerun2026'
METRICS = ['homeostatic-mae', 'setpoint-dev', 'reward-total',
           'homeostatic-fraction-within-5', 'homeostatic-rms', 'setpoint-avg',
           'loss-total', 'gain-total', 'gains-harvested']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(name, obj):
    (ROOT / name).write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


def save(name, rows):
    with (ROOT / name).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def read_csv(path):
    return list(csv.DictReader(path.open()))


# Incomplete-beta Student-t calculation from the October 18 stdlib verifier.
def beta_fraction(a, b, x):
    qab = a+b; qap = a+1; qam = a-1; c = 1.; d = 1-qab*x/qap
    tiny = 1e-300
    if abs(d) < tiny: d = tiny
    d = 1/d; h = d
    for m in range(1, 501):
        aa = m*(b-m)*x/((qam+2*m)*(a+2*m))
        d = 1+aa*d
        if abs(d) < tiny: d = tiny
        c = 1+aa/c
        if abs(c) < tiny: c = tiny
        d = 1/d; h *= d*c
        aa = -(a+m)*(qab+m)*x/((a+2*m)*(qap+2*m))
        d = 1+aa*d
        if abs(d) < tiny: d = tiny
        c = 1+aa/c
        if abs(c) < tiny: c = tiny
        d = 1/d; delta = d*c; h *= delta
        if abs(delta-1) < 3e-14: return h
    raise ArithmeticError('Incomplete beta did not converge')


def regularized_beta(x, a, b):
    if x <= 0: return 0.
    if x >= 1: return 1.
    factor = math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)
                      + a*math.log(x)+b*math.log1p(-x))
    if x < (a+1)/(a+b+2): return factor*beta_fraction(a,b,x)/a
    return 1-factor*beta_fraction(b,a,1-x)/b


def two_sided_t(t, df):
    return regularized_beta(df/(df+t*t), df/2, .5)


def critical(df):
    lo, hi = 0., 16.
    for _ in range(60):
        mid = (lo+hi)/2
        if two_sided_t(mid, df) > .05: lo = mid
        else: hi = mid
    return (lo+hi)/2


def describe(a):
    mean = st.mean(a); sd = st.stdev(a); margin = critical(len(a)-1)*sd/math.sqrt(len(a))
    return dict(n=len(a), mean=mean, sd=sd, median=st.median(a),
                ci95_low=mean-margin, ci95_high=mean+margin)


def compare(a, b, paired=False):
    delta = st.mean(a)-st.mean(b)
    if paired:
        se = st.stdev([x-y for x,y in zip(a,b)])/math.sqrt(len(a)); df = len(a)-1
    else:
        va = st.variance(a)/len(a); vb = st.variance(b)/len(b); se = math.sqrt(va+vb)
        df = (va+vb)**2/(va*va/(len(a)-1)+vb*vb/(len(b)-1)) if se else 1
    margin = critical(df)*se if se else 0
    p = two_sided_t(abs(delta/se),df) if se else float(delta == 0)
    return dict(n_cdr=len(a), n_ccc=len(b), difference=delta,
                ci95_low=delta-margin, ci95_high=delta+margin, p=p)


def holm(rows):
    running = 0.
    for rank, row in enumerate(sorted(rows, key=lambda x:x['p'])):
        running = max(running, min(1., (len(rows)-rank)*row['p']))
        row['p_holm'] = running


def close(a, b):
    assert math.isclose(float(a),float(b),rel_tol=2e-6,abs_tol=2e-6), (a,b)


def import_source(source):
    source = source.resolve()
    comparison = json.loads((source/'comparison.json').read_text())
    catalog = json.loads((source/'selected_policy_catalog.json').read_text())
    inputs = ROOT/'inputs'; inputs.mkdir(exist_ok=True)
    files = {}; selection = {}; audit = []; scene_count = 0; model_count = 0
    for family in ['HRL','NF']:
        for kind,s in catalog['policies'][family]['snapshots'].items():
            assert sha(source/s['file']) == s['sha256']; model_count += 1
        for order in ['cdr','ccc']:
            metrics = Path(comparison[family][order]['metrics'])
            run = json.loads(metrics.read_text()); v = run['provenance']; rid = run['run-id']
            assert v['asset-sha256']['Agent/BP_Agent'] == catalog['anticipation_asset_sha256']
            assert v['matched-training-record']['reward-family'] == family
            assert v['training-record-match-count'] == 1
            for kind,s in v['snapshots'].items():
                assert sha(metrics.parent/s['loaded-snapshot']) == s['loaded-sha256'] == catalog['policies'][family]['snapshots'][kind]['sha256']
                model_count += 1
            rates = set(); start_counts = []
            for trial in run['trials']:
                for phase in trial['phases']:
                    blob = gzip.decompress((metrics.parent/phase['scene-file']).read_bytes())
                    assert hashlib.sha256(blob).hexdigest() == phase['scene-sha256']
                    scene = json.loads(blob)
                    assert len(scene['tiles']) == phase['environment-tile-count'] == 2500
                    assert len(scene['resources']) == phase['environment-pellet-count']
                    rates.update(t['DecanalizationRateFactor'] for t in scene['tiles'])
                    if phase['sequence-idx'] == 1:
                        start_counts.append(sum(t['OverlapCount'] for t in scene['tiles']))
                    scene_count += 1
            assert rates == {0}
            for suffix in ['.metrics.json','.yml','.completed.json']:
                original = metrics.parent/(rid+suffix)
                target = inputs/original.name
                shutil.copyfile(original, target)
                files[str(target.relative_to(ROOT))] = dict(source=str(original),sha256=sha(target),bytes=target.stat().st_size)
            selection[family+'-'+order.upper()] = rid
            audit.append(dict(condition=family+'-'+order.upper(),scene_hashes_verified=750,
                              traversal_rate_factors=sorted(rates),
                              phase1_total_tile_counts_min=min(start_counts),
                              phase1_total_tile_counts_max=max(start_counts)))
    for name in ['selected_policy_catalog.json','selection.json','final_verification.json',
                 'contrasts.json','confirmation_contrasts.json','PROTOCOL.md','training_closeout.json']:
        target = inputs/name; shutil.copyfile(source/name,target)
        files[str(target.relative_to(ROOT))] = dict(source=str(source/name),sha256=sha(target),bytes=target.stat().st_size)
    for name in ['README.md','validation.json','change_manifest.json']:
        original = source.parent/'anticipation'/name; target = inputs/('anticipation-'+name)
        shutil.copyfile(original,target)
        files[str(target.relative_to(ROOT))] = dict(source=str(original),sha256=sha(target),bytes=target.stat().st_size)
    dump('selection.json',selection)
    dump('source_audit.json',dict(passed=True,scene_hashes_verified=scene_count,
                                 model_files_verified=model_count,conditions=audit))
    dump('source_manifest.json',dict(source=str(source),files=files,
                                    historical_analysis={str(p.relative_to(ROOT.parent.parent)):sha(p) for p in [OLD/'trial_metrics.csv',OLD/'primary_contrasts.csv',OLD/'phase_summary.csv']}))


def load_inputs():
    manifest = json.loads((ROOT/'source_manifest.json').read_text())
    for name,item in manifest['files'].items(): assert sha(ROOT/name) == item['sha256']
    for name,h in manifest['historical_analysis'].items(): assert sha(ROOT.parent.parent/name) == h
    selected = json.loads((ROOT/'selection.json').read_text()); arrays = {}; runs = {}; flat = []
    catalog = json.loads((ROOT/'inputs/selected_policy_catalog.json').read_text())
    for condition,rid in selected.items():
        family,order = condition.split('-')
        run = json.loads((ROOT/'inputs'/(rid+'.metrics.json')).read_text())
        v = run['provenance']; e = v['environment']
        assert run['status'] == 'complete' and run['schema-version'] == 2
        assert e['IsHRL'] == (family=='HRL') and e['TrialSequenceOrder'] == order.lower()
        assert e['TrialEnvironmentSeed'] == e['ActiveEnvironmentSeed'] == 10001
        assert v['simulation-dt-seconds'] == .05 and v['phase-decision-ticks'] == 2000
        assert v['asset-sha256']['Agent/BP_Agent'] == catalog['anticipation_asset_sha256']
        for kind,s in v['snapshots'].items():
            assert s['loaded-sha256'] == catalog['policies'][family]['snapshots'][kind]['sha256']
        receipt = json.loads((ROOT/'inputs'/(rid+'.completed.json')).read_text())
        assert receipt['results_saved'] and receipt['trials_completed'] == receipt['trials_requested'] == 250
        text = (ROOT/'inputs'/(rid+'.yml')).read_text()
        assert 'schema-version: 2' in text and 'duration-unit: simulation-seconds' in text
        blocks = re.split(r'^  - state: ',text,flags=re.M)[1:]; assert len(blocks)==750
        logged = [{m:float(re.search(r'^    '+re.escape(m)+r': (.+)$',b,re.M).group(1)) for m in ['setpoint-avg','setpoint-dev','reward-total','loss-total','gain-total','gains-harvested','duration']} for b in blocks]
        assert [t['id'] for t in run['trials']] == list(range(250))
        data = []
        for t in run['trials']:
            assert t['reward-function']==family and t['sequence-order']==order.lower()
            assert [p['sequence-idx'] for p in t['phases']] == [1,2,3]
            phases = []
            for p in t['phases']:
                q = logged[t['id']*3+p['sequence-idx']-1]
                assert p['complete'] and p['decision-ticks']==2000 and p['duration-seconds']==q['duration']==100
                for m in ['setpoint-avg','setpoint-dev','reward-total']: close(p[m],q[m])
                close(p['homeostatic-rms']**2,p['setpoint-dev']**2+p['setpoint-avg']**2)
                vals = {m:p[m] if m in p else q[m] for m in METRICS}
                assert all(math.isfinite(x) for x in vals.values())
                assert 0<=vals['homeostatic-fraction-within-5']<=1
                assert vals['homeostatic-mae']>=0 and vals['setpoint-dev']>=0
                assert p['homeostatic-sample-count']>0
                assert vals['reward-total']>=0
                if family=='HRL': assert vals['reward-total']<=100.001
                flat.append(dict(run=rid,family=family,order=order.lower(),trial=t['id'],
                                 phase=p['sequence-idx'],sample_count=p['homeostatic-sample-count'],**vals))
                phases.append(vals)
            data.append(phases)
        arrays[condition]=data; runs[condition]=run
    return arrays,runs,flat


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--import-source',type=Path); args=parser.parse_args()
    if args.import_source: import_source(args.import_source)
    arrays,runs,flat = load_inputs(); summary=[]; primary=[]; sensitivity=[]; alignment=[]; exact_pairs=[]
    for condition,data in arrays.items():
        for phase in range(3):
            for metric in METRICS:
                summary.append(dict(condition=condition,phase=phase+1,metric=metric,**describe([t[phase][metric] for t in data])))
    for family in ['HRL','NF']:
        a,b=[arrays[family+'-'+o] for o in ['CDR','CCC']]
        ra,rb=[runs[family+'-'+o] for o in ['CDR','CCC']]
        exact=[i for i,(t,u) in enumerate(zip(ra['trials'],rb['trials'])) if t['phases'][0]['scene-sha256']==u['phases'][0]['scene-sha256']]
        exact_pairs += [dict(family=family,trial=i) for i in exact]
        alignment.append(dict(family=family,exact_initial_scene_pairs=len(exact),
                              identical_baseline_metrics={m:sum(t[0][m]==u[0][m] for t,u in zip(a,b)) for m in METRICS},
                              matching_start_fields={k:sum(t['phases'][0][k]==u['phases'][0][k] for t,u in zip(ra['trials'],rb['trials'])) for k in ['rng-start','policy-memory-start','initial-homeostatic-state','observed-start-h']}))
        for phase in [1,2]:
            for m in METRICS:
                x=[t[phase][m] for t in a];y=[t[phase][m] for t in b]
                primary.append(dict(family=family,phase=phase+1,metric=m,method='Welch',estimand='CDR minus CCC',**compare(x,y)))
                for method,indices,change,paired in [('Welch-change',range(250),True,False),('paired-all',range(250),False,True),('paired-exact-scene',exact,False,True),('paired-change',range(250),True,True)]:
                    xx=[a[i][phase][m]-(a[i][0][m] if change else 0) for i in indices]
                    yy=[b[i][phase][m]-(b[i][0][m] if change else 0) for i in indices]
                    sensitivity.append(dict(family=family,phase=phase+1,metric=m,method=method,**compare(xx,yy,paired)))
    for phase in [2,3]:
        holm([r for r in primary if r['phase']==phase])
        for method in ['Welch-change','paired-all','paired-exact-scene','paired-change']:
            holm([r for r in sensitivity if r['phase']==phase and r['method']==method])
    # Existing independent-resampling bootstrap remains a separate
    # delivery estimand; cross-check its point estimate against native sidecars.
    for r in json.loads((ROOT/'inputs/contrasts.json').read_text()):
        metric={'mae':'homeostatic-mae','reward':'reward-total'}[r['metric']]
        s=next(x for x in sensitivity if x['family']==r['family'] and x['phase']==3 and x['metric']==metric and x['method']=='Welch-change')
        close(s['difference'],r['estimate'])
    old=read_csv(OLD/'primary_contrasts.csv'); comparison=[]
    for row in primary:
        prior=next(x for x in old if x['family']==row['family'] and int(x['phase'])==row['phase'] and x['metric']==row['metric'])
        comparison.append(dict(family=row['family'],phase=row['phase'],metric=row['metric'],
                               **{'old_'+k:float(prior[k]) for k in ['difference','ci95_low','ci95_high','p_holm']},
                               **{'new_'+k:row[k] for k in ['difference','ci95_low','ci95_high','p_holm']}))
    save('trial_metrics.csv',flat);save('phase_summary.csv',summary)
    save('exact_scene_pairs.csv',exact_pairs)
    save('primary_contrasts.csv',primary);save('sensitivity.csv',sensitivity);save('old_vs_new.csv',comparison)
    dump('verification.json',dict(passed=True,complete_trials=1000,phase_records=len(flat),
                                 decisions=6000000,descriptive_rows=len(summary),primary_contrasts=len(primary),
                                 sensitivity_contrasts=len(sensitivity),baseline_alignment=alignment,
                                 raw_json_yaml_agreement=True,all_frozen_input_hashes_verified=True))
    for row in primary:
        if row['phase']==3 and row['metric'] in METRICS[:4]:print(row)


if __name__=='__main__':main()
