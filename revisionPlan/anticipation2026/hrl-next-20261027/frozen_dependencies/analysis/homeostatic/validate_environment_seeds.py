"""Capture initial world randomness without running the optimizer or policy."""
import json
import pathlib
import unreal

project=pathlib.Path(unreal.Paths.project_dir()).resolve()
assert project.parent.name=='RngSeedFix' and project.name=='TestProject'
args=unreal.SystemLibrary.get_command_line()
label=next(s.split('=',1)[1] for s in args.split() if s.startswith('-SeedLabel='))
world=unreal.find_object(None,'/Game/Level/Landscape.Landscape')
assert world
gm=unreal.GameplayStatics.get_game_mode(world)
mc=unreal.load_class(None,'/Game/Learning/BP_AgentManager.BP_AgentManager_C')
ac=unreal.load_class(None,'/Game/Agent/BP_Agent.BP_Agent_C')
rc=unreal.load_class(None,'/Game/Resource/BP_Resource.BP_Resource_C')
manager=unreal.GameplayStatics.get_all_actors_of_class(world,mc)[0]
manager.set_actor_tick_enabled(False)
agent=unreal.GameplayStatics.get_all_actors_of_class(world,ac)[0]
def vec(v):return [v.x,v.y,v.z]
def layout():
    records=[]
    for r in unreal.GameplayStatics.get_all_actors_of_class(world,rc):
        records.append({'position':vec(r.get_actor_location()),'value':r.get_editor_property('BaseHomeostaticImpact')})
    return sorted(records,key=lambda x:tuple(x['position']))
def state():
    return {'position':vec(agent.get_actor_location()),'yaw':agent.get_actor_rotation().yaw,'pellets':layout()}
result={'mode':manager.get_editor_property('Run Inference'),
        'seed':gm.get_editor_property('ActiveEnvironmentSeed'),'initial':state(),'resets':[]}
for _ in range(2):
    manager.get_editor_property('LearningAgentsManager').reset_all_agents()
    result['resets'].append(state())
(project.parent/(label+'.json')).write_text(json.dumps(result,indent=2))
unreal.SystemLibrary.execute_console_command(world,'QUIT')
