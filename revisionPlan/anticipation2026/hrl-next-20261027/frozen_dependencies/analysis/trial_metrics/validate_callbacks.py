"""Exercise real Blueprint callbacks in the isolated runtime, without training."""
import json,math,traceback
from pathlib import Path
import unreal
project=Path(unreal.Paths.project_dir()).resolve();assert project.parent.name=='TrialMetricsFix'
root=project.parent;world=unreal.find_object(None,'/Game/Level/Landscape.Landscape');gm=unreal.GameplayStatics.get_game_mode(world)
m=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.load_class(None,'/Game/Learning/BP_AgentManager.BP_AgentManager_C'))[0]
env=m.get_editor_property('TrainingEnv');la=m.get_editor_property('LearningAgentsManager')
result={'passed':False,'cases':[]}
def put(o,n,v):o.set_editor_property(n,v,notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
try:
    gm.set_actor_tick_enabled(False);m.set_actor_tick_enabled(False)
    lib=unreal.get_default_object(unreal.load_class(None,'/Game/Libraries/BFL_Common.BFL_Common_C'))
    for sample in [[],[7.],[2.,2.,2.],[1.,2.,3.,4.],[-5.,5.]]:
        mean=sum(sample)/len(sample) if sample else 0.
        expected=math.sqrt(sum((v-mean)**2 for v in sample)/len(sample)) if sample else 0.
        actual=lib.call_method('GetStandardDev',args=(sample,world))
        if isinstance(actual,tuple):actual=next(x for x in actual if isinstance(x,(float,int)))
        result['cases'].append(dict(kind='population_sd',sample=sample,actual=actual,expected=expected))
        assert math.isclose(actual,expected,rel_tol=1e-5,abs_tol=1e-7)
    for inference in [False,True]:
        put(m,'Run Inference',inference)
        for hrl in [False,True]:
            for prev,now in [(-40.,-20.),(-20.,-40.),(-10.,0.),(-10.,30.),(50.,50.),(0.,0.),(0.,101.),(0.,-101.)]:
                la.reset_agents([0]);put(gm,'IsHRL',hrl);put(gm,'Setpoints',[prev,now])
                # One completed decision avoids phase-start reset seeding for transition tests.
                put(env,'Episode Steps',1);put(env,'PreviousRewardState',prev);put(env,'HasPreviousRewardState',True)
                env.gather_rewards();actual=env.get_reward(0);dt=unreal.GameplayStatics.get_world_delta_seconds(world)
                expected=dt/(1+(now/25.)**2) if hrl else (max(abs(prev)-abs(now),0)/25. if now<0 else 0.)
                if not inference and abs(now)>100:expected=-1. if hrl else 0.
                result['cases'].append(dict(kind='reward',inference=inference,hrl=hrl,previous=prev,current=now,actual=actual,expected=expected))
                assert math.isclose(actual,expected,rel_tol=1e-5,abs_tol=1e-7),result['cases'][-1]
                assert env.get_editor_property('ShouldTerminate')==(not inference and abs(now)>100)
                env.gather_rewards()
                repeat=0. if not hrl or not inference and abs(now)>100 else expected
                assert math.isclose(env.get_reward(0),repeat,rel_tol=1e-5,abs_tol=1e-7)
    put(m,'Run Inference',True);put(gm,'IsHRL',False)
    for step in [0,2000,4000]:
        la.reset_agents([0]);put(gm,'Setpoints',[-100.,-10.]);put(env,'Episode Steps',step)
        put(env,'PreviousRewardState',-100.);put(env,'HasPreviousRewardState',True)
        env.gather_rewards();assert env.get_reward(0)==0.
        result['cases'].append(dict(kind='phase_reset_no_credit',step=step,reward=env.get_reward(0)))
    result['passed']=True
except Exception:result['error']=traceback.format_exc();unreal.log_error(result['error'])
finally:
    (root/'callback_validation.json').write_text(json.dumps(result,indent=2,default=str))
    unreal.SystemLibrary.execute_console_command(world,'QUIT')
