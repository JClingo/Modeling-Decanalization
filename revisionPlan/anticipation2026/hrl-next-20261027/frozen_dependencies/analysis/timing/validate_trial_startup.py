"""Run actual frozen-policy trials and inspect first-decision reset conditions."""
import json
from pathlib import Path
import time
import traceback
import unreal
project=Path(unreal.Paths.project_dir()).resolve();assert project.parent.name=='TrialStartupAudit'
r=project.parent;world=unreal.find_object(None,'/Game/Level/Landscape.Landscape')
gm=unreal.GameplayStatics.get_game_mode(world)
def actors(n,f):return unreal.GameplayStatics.get_all_actors_of_class(world,unreal.load_class(None,'/Game/'+f+'/'+n+'.'+n+'_C'))
manager=actors('BP_AgentManager','Learning')[0];agent=actors('BP_Agent','Agent')[0]
policy=manager.get_editor_property('Policy');la=manager.get_editor_property('LearningAgentsManager');aid=la.get_agent_id(agent)
path=Path(unreal.Paths.convert_relative_path_to_full(gm.get_editor_property('TrialFileName')))
receipt=path.with_suffix('.completed.json')
result={'passed':False,'starts':[],'yaml':str(path)};started=time.monotonic();last=None;done=False;counter=0
assert not gm.get_editor_property('HasInitializedTrialRun')
def save():
 result['wall_seconds']=time.monotonic()-started
 (r/'natural_batch.json').write_text(json.dumps(result,indent=2))
def finish(error=None):
 global done
 if done:return
 done=True;result['passed']=error is None;result['error']=error;save()
 unreal.unregister_slate_post_tick_callback(handle)
 unreal.SystemLibrary.execute_console_command(world,'QUIT')
def tick(dt):
 global last,counter
 try:
  if time.monotonic()-started>300:raise RuntimeError('Batch timed out')
  trial=gm.get_editor_property('TrialsRun');count=gm.get_editor_property('TotalTickCount');counter+=1
  if gm.get_editor_property('HasInitializedTrialRun') and trial!=last:
   last=trial
   if trial<3:
    entry={'trial':trial,'tick_count':count,'anticipated_gain':agent.get_editor_property('AnticipatedResourceGain'),
     'anticipated_loss':agent.get_editor_property('AnticipatedResourceLoss'),
     'resource_hit_count':len(agent.get_editor_property('CollidingDriveReducers')),
     'tile_hit_count':len(agent.get_editor_property('CollidingDriveIncreasers')),
     'yml_trial_headers':gm.get_editor_property('TrialYML').count('- id: ')}
    result['starts'].append(entry)
    assert count in (0,1),entry
    # This callback runs after the first decision and perception update, which
    # can already populate valid observations at the new location.
    assert entry['yml_trial_headers']==trial+1,entry
   save()
  if counter%2000==0:
   result['progress']={'trial':trial,'tick':count};save()
  if receipt.exists():
   result['completion']=json.loads(receipt.read_text())
   assert result['completion']['trials_completed']==3 and result['completion']['results_saved']
   assert len(result['starts'])==3
   finish()
 except Exception:finish(traceback.format_exc())
handle=unreal.register_slate_post_tick_callback(tick)
