"""Check immediate phase-start speed and state preservation in an isolated world."""
import json
from pathlib import Path
import traceback
import unreal
root=Path(unreal.Paths.project_dir()).resolve().parent
assert root.name=='PhaseVelocityFix'
world=unreal.find_object(None,'/Game/Level/Landscape.Landscape')
gm=unreal.GameplayStatics.get_game_mode(world)
def actors(n,f):return unreal.GameplayStatics.get_all_actors_of_class(world,unreal.load_class(None,'/Game/'+f+'/'+n+'.'+n+'_C'))
agent=actors('BP_Agent','Agent')[0];manager=actors('BP_AgentManager','Learning')[0]
la=manager.get_editor_property('LearningAgentsManager');policy=manager.get_editor_property('Policy');aid=la.get_agent_id(agent)
movement=agent.get_editor_property('character_movement')
resources=actors('BP_Resource','Resource')
def get(o,n):return o.get_editor_property(n)
def put(o,n,v):o.set_editor_property(n,v,notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
def xyz(v):return [v.x,v.y,v.z]
result={'passed':False,'checks':[]}
result['trial_starts']=[]
def check(label):
    speed=get(agent,'BaseMaxSpeed');velocity=agent.get_velocity();forward=agent.get_actor_forward_vector()
    entry={'label':label,'speed':velocity.length(),'expected_speed':speed,'velocity':xyz(velocity),'forward':xyz(forward),
           'cached_speed':get(agent,'MaxSpeed'),'max_walk_speed':get(movement,'max_walk_speed'),
           'homeostatic_state':get(gm,'Setpoints')[-1],'trial_start':get(gm,'TrialStartingHomeostaticState')}
    result['checks'].append(entry)
    assert abs(velocity.length()-speed)<.01,entry
    assert (velocity-forward*speed).length()<.01,entry
    assert abs(entry['cached_speed']-speed)<.01 and abs(entry['max_walk_speed']-speed)<.01,entry
def flags():return [(get(r,'hidden'),r.get_actor_enable_collision(),get(get(r,'Cylinder'),'generate_overlap_events'),
                     unreal.SystemLibrary.is_timer_active(r,'Respawn'),get(r,'OverlapCount'),get(r,'HomeostaticImpact'),xyz(r.get_actor_location())) for r in resources]
def run():
    try:
        check('BeginPlay')
        manager.set_actor_tick_enabled(False);gm.set_actor_tick_enabled(False)
        put(gm,'HasInitializedTrialRun',True)
        assert get(gm,'Setpoints')[-1]==get(gm,'TrialStartingHomeostaticState')
        for index in range(5):
            put(gm,'IsHRL',index<2)
            put(manager,'Run Inference',index<4)
            put(agent,'BaseMaxSpeed',5000. if index%2==0 else 2375.)
            la.reset_all_agents()
            check('FullReset'+str(index))
            start=get(gm,'TrialStartingHomeostaticState')
            assert get(gm,'Setpoints')[-1]==start
            if index<4:
                assert -15<=start<=15
                result['trial_starts'].append(start)
            else:assert start==-15
            assert max(map(abs,policy.get_memory_state(aid)))==0
            policy.set_memory_state(aid,[.75]*policy.get_memory_state_size())
            resources[index].call_method('ReceiveActorBeginOverlap',args=(agent,))
            resources[index].call_method('ReceiveActorEndOverlap',args=(agent,))
            for boundary in (6000,12000):
                movement.stop_movement_immediately()
                position=xyz(agent.get_actor_location());rotation=agent.get_actor_rotation().yaw
                resource_state=flags();memory=list(policy.get_memory_state(aid))
                put(gm,'Setpoints',[123.456])
                put(gm,'TotalTickCount',boundary)
                gm.call_method('RunTrial',args=(get(gm,'TrialFileName'),bool(index%2)))
                check(('CDR' if index%2 else 'CCC')+str(index)+'-'+str(boundary))
                assert list(get(gm,'Setpoints'))==[start]
                assert get(gm,'TrialStartingHomeostaticState')==start
                assert xyz(agent.get_actor_location())==position
                assert agent.get_actor_rotation().yaw==rotation
                assert list(policy.get_memory_state(aid))==memory
                # CDR deliberately changes active impacts; availability, timers,
                # harvest counters and layout must be preserved.
                after=flags()
                assert all(a[:5]==b[:5] and a[6]==b[6] for a,b in zip(resource_state,after))
            # Direct calls set speed only; they leave homeostasis and memory intact.
            points=list(get(gm,'Setpoints'));memory=list(policy.get_memory_state(aid));state=flags()
            agent.call_method('InitializePhaseVelocity')
            check('Direct'+str(index))
            assert list(get(gm,'Setpoints'))==points and list(policy.get_memory_state(aid))==memory and flags()==state
        assert len(set(result['trial_starts']))==4
        result['passed']=True
    except Exception:result['error']=traceback.format_exc()
    (root/'validation.json').write_text(json.dumps(result,indent=2))
    unreal.SystemLibrary.execute_console_command(world,'QUIT')
run()
