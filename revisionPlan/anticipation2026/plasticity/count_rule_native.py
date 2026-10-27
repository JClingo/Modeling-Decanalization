"""Native overlap-handler/count-halving audit in a marked disposable editor copy.

Invokes real Blueprint events directly. It is not a physical collision test or
part of the scored policy trials. Temporary editability flags are never saved.
"""
import json,math,pathlib,traceback,unreal
p=pathlib.Path(unreal.Paths.project_dir()).resolve();assert (p/'COUNT_RULE_AUDIT_COPY').exists()
report={'tests':[],'method':'Direct invocation of native Blueprint overlap and canalization event handlers; isolated transient editor actors; no scored trial data.'}
def check(name,actual,expected):
 actual=float(actual);expected=float(expected)
 report['tests'].append(dict(name=name,actual=actual,expected=expected,passed=math.isclose(actual,expected,abs_tol=1e-8)))
try:
 for path,fields in [('/Game/Agent/BP_GameMode',['IsDecanalized','Setpoints']),('/Game/Level/BP_Tile',['BP Game Mode','OverlapCount','DecanalizationRateFactor']),('/Game/Agent/BP_Agent',['BP Game Mode'])]:
  bp=unreal.load_asset(path)
  for field in fields:unreal.BlueprintEditorLibrary.set_blueprint_variable_instance_editable(bp,field,True)
  unreal.BlueprintEditorLibrary.compile_blueprint(bp)
 world=unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
 subsystem=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 def spawn(path,location):
  cls=unreal.load_class(None,path+'_C');assert cls
  return subsystem.spawn_actor_from_class(cls,unreal.Vector(*location))
 gm=spawn('/Game/Agent/BP_GameMode.BP_GameMode',(0,0,0))
 agent=spawn('/Game/Agent/BP_Agent.BP_Agent',(0,10000,100))
 tile=spawn('/Game/Level/BP_Tile.BP_Tile',(0,-10000,-50))
 gm.set_editor_property('Setpoints',[-15.])
 tile.set_editor_property('BP Game Mode',gm);agent.set_editor_property('BP Game Mode',gm)
 gm.set_editor_property('IsDecanalized',True)
 for factor in [0,1,2,4,7]:
  tile.set_editor_property('DecanalizationRateFactor',float(factor));tile.set_editor_property('OverlapCount',11.)
  tile.call_method('ReceiveActorBeginOverlap',(agent,))
  check(f'Decanalized factor {factor}, one entry',tile.get_editor_property('OverlapCount'),11+factor)
  tile.call_method('ReceiveActorBeginOverlap',(agent,))
  check(f'Decanalized factor {factor}, two entries',tile.get_editor_property('OverlapCount'),11+2*factor)
 gm.set_editor_property('IsDecanalized',False)
 for factor in [0,7]:
  tile.set_editor_property('DecanalizationRateFactor',float(factor));tile.set_editor_property('OverlapCount',11.)
  tile.call_method('ReceiveActorBeginOverlap',(agent,))
  check(f'Ordinary entry independent of factor {factor}',tile.get_editor_property('OverlapCount'),12)
 for count in [0,1,2,7,11]:
  tile.set_editor_property('OverlapCount',float(count));tile.call_method('CanalizationToggled_Event')
  check(f'Recanalization rounds down {count}/2',tile.get_editor_property('OverlapCount'),math.floor(count/2))
 assert all(t['passed'] for t in report['tests']),[t for t in report['tests'] if not t['passed']]
 report['passed']=True;unreal.log('COUNT_RULE_AUDIT_PASSED '+str(len(report['tests'])))
except Exception:
 report['passed']=False;report['error']=traceback.format_exc();raise
finally:
 (p.parent/'count_rule_validation.json').write_text(json.dumps(report,indent=2)+'\n')
 unreal.SystemLibrary.quit_editor()
