"""Native handler validation; modifies transient editor actors, never saved assets."""
import json,math,pathlib,traceback,unreal
p=pathlib.Path(unreal.Paths.project_dir()).resolve()
assert (p/'INTERACTION_EVALUATION_COPY').exists()
s=json.loads((p/'evaluation_settings.json').read_text())
report={'condition':s['condition'],'tests':[],'method':'Direct real Blueprint event invocation on transient editor actors, not scored collision trials.'}
def check(name,value,expected):
    report['tests'].append(dict(name=name,actual=float(value),expected=float(expected),
                               passed=math.isclose(value,expected,abs_tol=1e-8,rel_tol=1e-12)))
try:
    for path,fields in [('/Game/Agent/BP_GameMode',['IsDecanalized','Setpoints']),
                        ('/Game/Level/BP_Tile',['BP Game Mode','OverlapCount','DecanalizationRateFactor']),
                        ('/Game/Agent/BP_Agent',['BP Game Mode'])]:
        bp=unreal.load_asset(path)
        for field in fields:unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,field,True)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    world=unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    subsystem=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    def spawn(path,location):
        return subsystem.spawn_actor_from_class(unreal.load_class(None,path+'_C'),unreal.Vector(*location))
    gm=spawn('/Game/Agent/BP_GameMode.BP_GameMode',(0,0,0))
    agent=spawn('/Game/Agent/BP_Agent.BP_Agent',(0,10000,100))
    tile=spawn('/Game/Level/BP_Tile.BP_Tile',(0,-10000,-50))
    gm.set_editor_property('Setpoints',[-15.])
    agent.set_editor_property('BP Game Mode',gm)
    tile.set_editor_property('BP Game Mode',gm)
    gm.set_editor_property('IsDecanalized',False)
    for n in [0,1,2,3,7,11,100,101,1001]:
        tile.set_editor_property('OverlapCount',float(n))
        tile.call_method('CanalizationToggled_Event')
        expected=s['retain']*n
        if s['floor']:expected=math.floor(expected)
        check('Transform '+str(n),tile.get_editor_property('OverlapCount'),expected)
    for state in [False,True]:
        gm.set_editor_property('IsDecanalized',state)
        tile.set_editor_property('OverlapCount',11.)
        check('Configured entry factor '+str(state),tile.get_editor_property('DecanalizationRateFactor'),float(s['factor']))
        tile.call_method('ReceiveActorBeginOverlap',(agent,))
        check('One entry '+str(state),tile.get_editor_property('OverlapCount'),11.+(s['factor'] if state else 1))
        tile.call_method('ReceiveActorBeginOverlap',(agent,))
        check('Two entries '+str(state),tile.get_editor_property('OverlapCount'),11.+2*(s['factor'] if state else 1))
    assert all(t['passed'] for t in report['tests']),report['tests']
    report['passed']=True
    unreal.log('RECANALIZATION_NATIVE_PASSED '+s['condition'])
except Exception:
    report['passed']=False
    report['error']=traceback.format_exc()
    raise
finally:
    (p.parent/'native_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    unreal.SystemLibrary.quit_editor()
