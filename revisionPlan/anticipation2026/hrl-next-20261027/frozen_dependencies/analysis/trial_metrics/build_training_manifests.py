"""Pin the selected retained snapshots to their actual trainer configurations."""
import copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
records=[]
for family,iteration,filename in [
    ('HRL',10000,'Training_homeostatic_ppo_SharedMemory_2026-10-14_16-11-38.json'),
    ('NF',5000,'Training_nf_ppo_SharedMemory_2026-10-16_12-08-21.json')]:
    path=ROOT/'Intermediate/LearningAgents/Configs'/filename
    config=json.loads(path.read_text());effective=copy.deepcopy(config['PPOSettings'])
    if family=='NF':
        for key,cap in [('LearningRatePolicy',3e-5),('LearningRateCritic',3e-4),('IterationsPerGather',8),('EpsilonClip',.1),('GradNormMax',.25)]:effective[key]=min(effective[key],cap)
        effective.update(ActionEntropyWeight=0.,ActionRegularizationWeight=0.,UseGradNormMaxClipping=True,CriticWarmupIterations=0)
    hashes={kind:hashlib.sha256((ROOT/'analysis/snapshots'/('Winning '+family)/(f'{kind}_{iteration} - Copy.bin')).read_bytes()).hexdigest() for kind in ['encoder','policy','decoder']}
    records.append({'reward-family':family,'snapshot-update-label':iteration,'snapshot-sha256':hashes,
        'source-config':str(path.relative_to(ROOT)),'source-config-sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'configured-ppo':config['PPOSettings'],'effective-ppo':effective,
        'trainer':'homeostatic_ppo' if family=='HRL' else 'nf_ppo/NFStable1',
        'nf-stability':None if family=='HRL' else {'ActionStd':.15,'TargetKL':.015,'DiscardInitialActorRollout':True,'CriticUpdatesEncoder':False},
        'selection-criterion':'Mean h closer to zero and highest mean reward relative to other snapshots' if family=='HRL' else 'Highest mean reward relative to other snapshots',
        'selection-source':'Author confirmation, 2026-10-17; selection was performance-based across snapshots, not an independent training-replicate comparison'})
(ROOT/'Content/Python/trial_training_manifests.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print('Wrote two selected-snapshot manifests with effective NFStable1 settings.')
