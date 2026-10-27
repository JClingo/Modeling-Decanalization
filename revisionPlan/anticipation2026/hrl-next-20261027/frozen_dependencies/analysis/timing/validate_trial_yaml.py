"""Validate real standalone trial YAML checkpoints in the isolated test project."""
import json
import pathlib
import traceback
import unreal

project=pathlib.Path(unreal.Paths.project_dir()).resolve()
assert project.parent.name=='TrialYamlFix' and project.name=='TestProject'
world=unreal.find_object(None,'/Game/Level/Landscape.Landscape')
root=project.parent
label=next((s.split('=',1)[1] for s in unreal.SystemLibrary.get_command_line().split() if s.startswith('-YamlLabel=')), 'hrl_cdr')
root=root/label;root.mkdir(exist_ok=True)
result={'passed':False,'checkpoints':[]}
mode='-YamlMode=off' not in unreal.SystemLibrary.get_command_line().split()
try:
    gm=unreal.GameplayStatics.get_game_mode(world)
    mc=unreal.load_class(None,'/Game/Learning/BP_AgentManager.BP_AgentManager_C')
    manager=unreal.GameplayStatics.get_all_actors_of_class(world,mc)[0]
    manager.set_actor_tick_enabled(False)
    gm.set_actor_tick_enabled(False)
    assert gm.get_editor_property('IsTrialMode')==mode
    out=pathlib.Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()))/'TrialResults'
    initial_files=list(out.glob('*.yml'))
    filename=gm.get_editor_property('TrialFileName')
    if mode:
        assert filename, 'BeginPlay did not initialize TrialFileName'
        path=pathlib.Path(unreal.Paths.convert_relative_path_to_full(filename))
        assert path.parent==out and path.exists(), (str(path),str(out))
        initial_text=path.read_text(encoding='utf-8-sig')
        assert 'trials:' in initial_text and '- id: 0' in initial_text, initial_text
        result['path']=str(path)
        def checkpoint(label):
            assert gm.get_editor_property('TrialFileName')==filename
            text=path.read_text(encoding='utf-8-sig')
            assert text==gm.get_editor_property('TrialYML').replace('\r\n','\n')
            target=root/(label+'.yml');target.write_text(text,encoding='utf-8')
            result['checkpoints'].append({'label':label,'file':str(target)})
        checkpoint('initial')
        # Avoid editor change notifications, which rerun construction and reset state.
        is_cdr=gm.get_editor_property('TrialSequenceOrder').lower()=='cdr'
        gm.set_editor_property('TrialsToRun',3,notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
        for n in range(3):
            for tick in (6000,12000,18000):
                gm.set_editor_property('TotalTickCount',tick,notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
                gm.call_method('RunTrial',args=(filename,is_cdr))
                checkpoint('trial%d_tick%d'%(n,tick))
            gm.set_editor_property('TotalTickCount',18002,notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
            gm.call_method('RunTrial',args=(filename,is_cdr))
            assert gm.get_editor_property('TrialsRun')==n+1
            checkpoint('trial%d_reset'%n)
        assert len(list(out.glob('*.yml')))==len(initial_files), 'Extra run file created during resets'
        # Force the existing final save/quit branch. Script finishes before queued quit.
        checkpoint('final')
        assert len(list(out.glob('*.yml')))==len(initial_files), 'Final save created another run file'
        # IsTrialMode false must suppress even an explicit SaveTrial call.
        before=path.read_bytes()
        gm.set_editor_property('IsTrialMode',False,notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
        gm.call_method('ReadyTrial',args=(filename,999,'NF','cdr'))
        gm.call_method('StoreTrial',args=(filename,'canalized',3000,1.0,2.0,3.0,4,5.0,1,6.0))
        gm.call_method('SaveTrial')
        assert path.read_bytes()==before
    else:
        gm.call_method('ReadyTrial',args=('',999,'NF','cdr'))
        gm.call_method('StoreTrial',args=('','canalized',3000,1.0,2.0,3.0,4,5.0,1,6.0))
        gm.call_method('SaveTrial')
        baseline=json.loads((project.parent/'before_off_files.json').read_text())
        assert not filename and sorted(str(p) for p in out.glob('*.yml'))==baseline
    result['passed']=True
except Exception:
    result['error']=traceback.format_exc()
finally:
    (root/('runtime_on.json' if mode else 'runtime_off.json')).write_text(json.dumps(result,indent=2))
    unreal.SystemLibrary.execute_console_command(world,'QUIT')

