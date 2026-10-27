"""Invoke the project Python notifier after final save and before QuitGame."""
import base64
import copy
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from patch_graphs import Editor,prop,string
from graph_asset import pins

root=Path('Saved/TrialCompletionFix')
ed=Editor(json.loads((root/'BP_GameMode.json').read_text(encoding='utf-8-sig')))
def scope(e):return ed.e(e['OuterIndex'])['ObjectName'] if e['OuterIndex']>0 else ''
def called(i):return next(q['Value'] for q in prop(ed.e(i),'FunctionReference')['Value'] if q['Name']=='MemberName')
def call(name):return next(i for i,e in enumerate(ed.a['Exports'],1) if scope(e)=='RunTrial' and e['ObjectName'].startswith('K2Node_CallFunction') and called(i)==name)
notice=call('PrintString');quit_game=call('QuitGame')
package=copy.deepcopy(next(e for e in ed.a['Imports'] if e['ClassName']=='Package'))
package['ObjectName']='/Script/PythonScriptPlugin';ed.fname(package['ObjectName'])
ed.a['Imports'].append(package);ed.a['ImportBits'].append(True)
package_index=-len(ed.a['Imports'])
python_lib=ed.import_class('PythonScriptLibrary')
ed.a['Imports'][-python_lib-1]['OuterIndex']=package_index
oldpins=pins(ed.a,ed.e(notice));tail=base64.b64decode(ed.e(notice)['Extras'])[oldpins[-1]['end']:]
notify=ed.node(notice,'K2Node_TrialCompletion_Notify','ExecutePythonCommand',[
 ('execute',0,'exec'),('then',1,'exec'),('self',0,'object',python_lib),
 ('PythonCommand',0,'string',0,'import trial_notifications; trial_notifications.notify_completed_trials()'),
 ('ReturnValue',1,'bool')],1200,700)
next(q for q in prop(ed.e(notify),'FunctionReference')['Value'] if q['Name']=='MemberParent')['Value']=python_lib
ed.e(notify)['Extras']=base64.b64encode(base64.b64decode(ed.e(notify)['Extras'])+tail).decode()
p=ed.p(notify,'PythonCommand')
ed.replace(notify,p['default_end'],p['default_end']+len(string(p['auto_default'])),string(''))
ed.rewire(notice,'then',notify,'execute');ed.connect(notify,'then',quit_game,'execute')
ed.save('BP_GameMode')
(root/'BP_GameMode.patched.json').write_text(json.dumps(ed.a))
