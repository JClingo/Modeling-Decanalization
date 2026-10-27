"""Staged multi-seed optimization with held-out time-MAE checkpoint selection."""
from pathlib import Path
from dataclasses import replace
import argparse,json
import run as native
from profiles import PROFILES,STAGES,load_profile

class Selector:
    def __init__(self,minimum=100,patience=4,material=.005):
        self.minimum,self.patience,self.material=minimum,patience,material
        self.best=None;self.stale=0;self.history=[]
    def update(self,result):
        value=result['mean_time_mae']
        best=self.best['mean_time_mae'] if self.best else None
        material=best is None or value < best-self.material*max(abs(best),1e-8)
        if best is None or value<best:self.best=result
        self.stale=0 if material else self.stale+1
        self.history.append(result)
        return result['checkpoint']['gathers']>=self.minimum and self.stale>=self.patience
    def record(self):
        return dict(best=self.best,stale_checkpoints=self.stale,history=self.history,
                    criterion='held-out time-averaged absolute h; all three CCC phases equally weighted')

def resolve_profiles(names,stage,reward_from='baseline',environment_from=None):
    reward=PROFILES[reward_from]
    environment_name=None if stage=='canalization' else (environment_from or 'canalization-persistent')
    environment=PROFILES[environment_name] if environment_name else None
    effective={}
    for name in names:
        profile=PROFILES[name]
        if stage!='reward':
            profile=replace(profile,reward=reward.reward,distance_scale=reward.distance_scale).validate()
        if environment:
            profile=replace(profile,episode_seconds=environment.episode_seconds,
                            reset_world_on_update=environment.reset_world_on_update).validate()
        effective[name]=profile
    return effective,environment_name

def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=list(STAGES)+['confirm'],required=True)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--reward-from',choices=STAGES['reward'],default='baseline')
    p.add_argument('--environment-from',choices=['baseline','canalization-300s','canalization-persistent'])
    p.add_argument('--profiles',nargs='+',choices=PROFILES)
    p.add_argument('--seeds',nargs='+',type=int);p.add_argument('--gathers',type=int,default=200)
    p.add_argument('--checkpoint-every',type=int,default=10);p.add_argument('--minimum-gathers',type=int,default=100)
    p.add_argument('--patience',type=int,default=4);p.add_argument('--trials',type=int)
    p.add_argument('--pipeline-check',action='store_true',help='Label bounded engineering checks; not a policy performance study')
    a=p.parse_args();root=a.root.resolve()
    if a.gathers<1 or a.checkpoint_every<1 or a.patience<1:p.error('Budgets must be positive')
    if a.stage=='confirm' and not a.profiles:p.error('Specify finalist --profiles, including baseline')
    if a.stage=='canalization' and a.environment_from:p.error('The canalization stage varies world history; do not override its environments')
    names=a.profiles or STAGES[a.stage]
    if 'baseline' not in names:p.error('Include baseline in every stage')
    seeds=a.seeds or ([4501,5601,6701,7801,8901] if a.stage=='confirm' else [1201,2301,3401])
    if len(set(seeds))!=len(seeds):p.error('Training seeds must be distinct')
    if a.stage=='confirm' and len(seeds)<5:p.error('Confirmation requires at least five independent training seeds')
    if a.stage!='confirm' and len(seeds)<3:p.error('Screening requires at least three independent training seeds')
    trials=a.trials or (32 if a.stage=='confirm' else 8)
    if trials<1:p.error('Trials must be positive')
    if a.stage=='confirm' and any(s in [1201,2301,3401] for s in seeds):p.error('Use fresh confirmation initialization seeds')
    effective_profiles,environment_name=resolve_profiles(names,a.stage,a.reward_from,a.environment_from)
    protocol=dict(stage=a.stage,purpose='pipeline-validation' if a.pipeline_check else 'learning-study',names=names,profiles={n:p.contract() for n,p in effective_profiles.items()},seeds=seeds,max_gathers=a.gathers,checkpoint_every=a.checkpoint_every,
                  minimum_gathers=a.minimum_gathers,patience=a.patience,trials=trials,
                  checkpoint_seed=41001,confirmation_seed=51001 if a.stage=='confirm' else None,
                  final_test_seed_reserved=61001,counting='one per entry throughout; half-floor at recanalization',
                  policy_selection='continuous 300-second CCC time-MAE; CDR excluded',reward_from=a.reward_from,
                  training_world_context=environment_name or 'varied by experiment')
    root.mkdir(parents=True,exist_ok=True);path=root/(a.stage+'_protocol.json')
    if path.exists():assert native.read(path)==protocol,'Cannot silently change a started study'
    else:native.write(path,protocol)
    native.prepare(root)
    reference_seed=51001 if a.stage=='confirm' else 41001
    reference_name='selected-reference-continuous-'+str(reference_seed)
    reference_path=root/reference_name/'summary.json'
    reference=native.read(reference_path) if reference_path.exists() else native.evaluate(
        root,reference_name,PROFILES['baseline'],native.selected_reference(),trials,reference_seed,continuous=True)
    assert reference['evaluation_seed']==reference_seed and len(reference['trials'])==trials
    assert reference['checkpoint']['snapshots']==native.selected_reference()['snapshots']
    assert reference['continuous_homeostasis']
    results=[];initial={}
    for name in names:
        profile=effective_profiles[name]
        for seed in seeds:
            label=a.stage+'-'+name+'-'+str(seed);selection=root/label/'selection.json'
            if selection.exists() and native.read(selection).get('complete'):
                record=native.read(selection);results.append(record['confirmed'] if a.stage=='confirm' else record['best']);continue
            assert not (root/label).exists(),'Incomplete run needs inspection before an explicit restart: '+label
            selector=Selector(a.minimum_gathers,a.patience)
            def callback(checkpoint):
                result=native.evaluate(root,label+'-validation-'+str(checkpoint['gathers']),profile,checkpoint,trials,41001,continuous=True)
                stop=selector.update(result)
                native.write(selection,selector.record())
                return stop
            native.train(root,label,profile,seed,100000+seed,a.gathers,a.checkpoint_every,48640,callback)
            record={**selector.record(), 'complete':True,'termination':native.read(root/label/'trainer_complete.json')['reason']}
            assert record['best'],'No held-out checkpoint was selected'
            if a.stage=='confirm':
                record['confirmed']=native.evaluate(root,label+'-confirmation',profile,record['best']['checkpoint'],trials,51001,continuous=True)
            native.write(selection,record)
            result=record['confirmed'] if a.stage=='confirm' else record['best'];results.append(result)
            initial[(name,seed)]=native.read(root/label/'training_verified.json')['initial_policy_sha256']
            # Verify native initialization varies across seeds within a profile.
            hashes=[value for (n,s),value in initial.items() if n==name]
            assert len(hashes)==len(set(hashes)),'Native initialization seeds did not produce distinct policies'
            summary=[]
            for candidate in names:
                values=[r['mean_time_mae'] for r in results if r['checkpoint']['profile']['name']==candidate]
                if values:summary.append(dict(profile=candidate,trained_seeds=len(values),mean_time_mae=sum(values)/len(values),per_seed_mae=values))
            native.write(root/(a.stage+'_summary.json'),dict(protocol=protocol,results=results,summary=summary,
                preserved_policy_reference=reference,
                complete=len(results)==len(names)*len(seeds),unit_of_training_replication='independently initialized policy'))
    print('STUDY_COMPLETE '+str(root/(a.stage+'_summary.json')))

if __name__=='__main__':main()
