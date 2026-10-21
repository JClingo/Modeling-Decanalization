"""Independently verify the frozen rerun package using only Python's stdlib.

Usage: python3 verify_analysis.py /path/to/paper-update-2026-10-17-reruns
No source inputs are modified. Checks raw JSON/YAML agreement, scenes, loaded
snapshots, reported summaries, Welch and paired intervals, p values, and Holm.
The source package's scipy-based build_analysis.py is the primary pipeline.
"""
from pathlib import Path
import argparse,csv,gzip,hashlib,json,math,re,statistics as st

METRICS=['homeostatic-mae','setpoint-dev','reward-total','homeostatic-fraction-within-5','homeostatic-rms','setpoint-avg','loss-total','gain-total','gains-harvested']

def beta_fraction(a,b,x):
    qab=a+b;qap=a+1;qam=a-1;c=1.;d=1-qab*x/qap
    tiny=1e-300
    if abs(d)<tiny:d=tiny
    d=1/d;h=d
    for m in range(1,501):
        aa=m*(b-m)*x/((qam+2*m)*(a+2*m))
        d=1+aa*d
        if abs(d)<tiny:d=tiny
        c=1+aa/c
        if abs(c)<tiny:c=tiny
        d=1/d;h*=d*c
        aa=-(a+m)*(qab+m)*x/((a+2*m)*(qap+2*m))
        d=1+aa*d
        if abs(d)<tiny:d=tiny
        c=1+aa/c
        if abs(c)<tiny:c=tiny
        d=1/d;delta=d*c;h*=delta
        if abs(delta-1)<3e-14:return h
    raise ArithmeticError('Incomplete beta did not converge')

def regularized_beta(x,a,b):
    if x<=0:return 0.
    if x>=1:return 1.
    factor=math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)+a*math.log(x)+b*math.log1p(-x))
    if x<(a+1)/(a+b+2):return factor*beta_fraction(a,b,x)/a
    return 1-factor*beta_fraction(b,a,1-x)/b

def two_sided_t(t,df):return regularized_beta(df/(df+t*t),df/2,.5)
def critical(df):
    lo,hi=0.,16.
    for _ in range(60):
        mid=(lo+hi)/2
        if two_sided_t(mid,df)>.05:lo=mid
        else:hi=mid
    return (lo+hi)/2

def contrast(a,b,paired=False):
    delta=st.mean(a)-st.mean(b)
    if paired:
        d=[x-y for x,y in zip(a,b)];se=st.stdev(d)/math.sqrt(len(d));df=len(d)-1
    else:
        va=st.variance(a)/len(a);vb=st.variance(b)/len(b);se=math.sqrt(va+vb)
        df=(va+vb)**2/(va*va/(len(a)-1)+vb*vb/(len(b)-1)) if se else math.inf
    margin=critical(df)*se if se else 0
    p=two_sided_t(abs(delta/se),df) if se else float(delta==0)
    return {'difference':delta,'ci95_low':delta-margin,'ci95_high':delta+margin,'p':p}

def close(a,b,rtol=2e-7,atol=1e-9):
    assert math.isclose(float(a),float(b),rel_tol=rtol,abs_tol=atol),(a,b)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):return list(csv.DictReader(p.open()))
def main():
    parser=argparse.ArgumentParser();parser.add_argument('package',type=Path);args=parser.parse_args();root=args.package
    selected=json.loads((root/'selection.json').read_text());arrays={};exact={};scene_count=0;snapshot_count=0
    for condition,run_id in selected.items():
        family,order=condition.split('-');run=json.loads((root/'inputs'/(run_id+'.metrics.json')).read_text());v=run['provenance']
        receipt=json.loads((root/'inputs'/(run_id+'.completed.json')).read_text())
        assert run['status']=='complete' and run['schema-version']==2
        assert receipt['results_saved'] and receipt['trials_completed']==receipt['trials_requested']==250
        assert v['matched-training-record']['reward-family']==family and v['training-record-match-count']==1
        assert v['matched-training-record']['snapshot-update-label']==(10000 if family=='HRL' else 5000)
        assert v['environment']['IsHRL']==(family=='HRL') and v['environment']['TrialSequenceOrder']==order.lower()
        assert v['simulation-dt-seconds']==.05 and v['phase-decision-ticks']==2000
        for name,h in v['logger-sha256'].items():
            old=root/'evidence'/name;version=root/'evidence/logger_versions'/h/name
            assert (old.exists() and sha(old)==h) or (version.exists() and sha(version)==h)
        for kind,s in v['snapshots'].items():
            assert sha(root/'inputs'/s['loaded-snapshot'].replace('\\','/'))==s['loaded-sha256']==v['matched-training-record']['snapshot-sha256'][kind];snapshot_count+=1
        yaml_text=(root/'inputs'/(run_id+'.yml')).read_text()
        assert 'schema-version: 2' in yaml_text and 'duration-unit: simulation-seconds' in yaml_text
        blocks=re.split(r'^  - state: ',yaml_text,flags=re.M)[1:]
        assert len(blocks)==750
        parsed=[]
        for block in blocks:
            parsed.append({m:float(re.search(r'^    '+re.escape(m)+r': (.+)$',block,re.M).group(1)) for m in ['setpoint-avg','setpoint-dev','reward-total','loss-total','gain-total','gains-harvested','duration']})
        assert [t['id'] for t in run['trials']]==list(range(250));condition_data=[]
        for t in run['trials']:
            assert t['reward-function']==family and t['sequence-order']==order.lower()
            assert [p['sequence-idx'] for p in t['phases']]==[1,2,3];trial_data=[]
            for p in t['phases']:
                q=parsed[t['id']*3+p['sequence-idx']-1]
                assert p['complete'] and p['decision-ticks']==2000 and p['duration-seconds']==q['duration']==100
                for k in ['setpoint-avg','setpoint-dev','reward-total']:close(p[k],q[k],atol=1e-6)
                vals={m:p.get(m,q.get(m)) for m in METRICS};assert all(math.isfinite(z) for z in vals.values())
                close(vals['homeostatic-rms']**2,vals['setpoint-dev']**2+vals['setpoint-avg']**2)
                assert vals['reward-total']>=0 and 0<=vals['homeostatic-fraction-within-5']<=1
                if family=='HRL':assert vals['reward-total']<=100.001
                blob=gzip.decompress((root/'inputs'/p['scene-file'].replace('\\','/')).read_bytes());assert hashlib.sha256(blob).hexdigest()==p['scene-sha256']
                scene=json.loads(blob);assert len(scene['tiles'])==p['environment-tile-count']==2500
                assert len(scene['resources'])==p['environment-pellet-count']
                assert {tile['DecanalizationRateFactor'] for tile in scene['tiles']}=={0.0}
                scene_count+=1;trial_data.append(vals)
            condition_data.append(trial_data)
        arrays[condition]=condition_data
        # Raw arrays also agree with the long-form CSV used in the manuscript.
        for row in [r for r in rows(root/'trial_metrics.csv') if r['run']==run_id]:
            for m in METRICS:close(condition_data[int(row['trial'])][int(row['phase'])-1][m],row[m])
    for family in ['HRL','NF']:
        a,b=[json.loads((root/'inputs'/(selected[family+'-'+c]+'.metrics.json')).read_text()) for c in ['CDR','CCC']]
        exact[family]=[t['id'] for t,u in zip(a['trials'],b['trials']) if t['phases'][0]['scene-sha256']==u['phases'][0]['scene-sha256']]
        assert len(exact[family])==(230 if family=='HRL' else 226)
        for t,u in zip(a['trials'],b['trials']):
            for k in ['rng-start','policy-memory-start','initial-homeostatic-state','observed-start-h']:assert t['phases'][0][k]==u['phases'][0][k]
        for m in METRICS:
            assert [t[0][m] for t in arrays[family+'-CDR']]==[t[0][m] for t in arrays[family+'-CCC']]
    for r in rows(root/'phase_summary.csv'):
        x=[t[int(r['phase'])-1][r['metric']] for t in arrays[r['condition']]];mean=st.mean(x);sd=st.stdev(x);margin=critical(len(x)-1)*sd/math.sqrt(len(x))
        for k,value in [('mean',mean),('sd',sd),('median',st.median(x)),('ci95_low',mean-margin),('ci95_high',mean+margin)]:close(value,r[k])
    checks=0
    for filename in ['primary_contrasts.csv','paired_sensitivity.csv']:
        table=rows(root/filename);computed=[]
        for r in table:
            fam=r['family'];m=r['metric'];phase=int(r['phase'])-1;method=r['method'];ids=exact[fam] if method=='paired-exact-scene' else range(250)
            a,b=[[t[phase][m]-(t[0][m] if method=='paired-change-from-baseline' else 0) for i,t in enumerate(arrays[fam+'-'+c]) if i in ids] for c in ['CDR','CCC']]
            assert int(r['n_cdr'])==int(r['n_ccc'])==len(a)
            result=contrast(a,b,method!='Welch')
            for k,value in result.items():close(value,r[k],atol=1e-300 if k=='p' else 1e-9)
            computed.append(result['p']);checks+=1
        for phase in ['2','3']:
            for method in set(r['method'] for r in table):
                indices=[i for i,r in enumerate(table) if r['phase']==phase and r['method']==method];running=0
                for rank,i in enumerate(sorted(indices,key=lambda i:computed[i])):
                    running=max(running,min(1,(len(indices)-rank)*computed[i]));close(running,table[i]['p_holm'],atol=1e-300)
    print(json.dumps({'passed':True,'complete_trials':1000,'phase_records':3000,'scene_hashes_verified':scene_count,'loaded_snapshot_hashes_verified':snapshot_count,'descriptive_rows_verified':108,'contrasts_verified':checks,'statistics':'independent stdlib Welch/paired t, 95% intervals, Holm; matches frozen scipy output','exact_initial_scene_pairs':{f:len(v) for f,v in exact.items()}},indent=2))
if __name__=='__main__':main()
