"""Restore fresh-world tile/pellet state on existing full reset broadcasts.

Phase transition graphs are unchanged. Inputs are exports of the current assets
under Saved/TrialWorldResetFix; compile imported assets before using them.
"""
import base64
import copy
import json
from pathlib import Path
import struct
import sys
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parent))
from patch_graphs import Editor,prop,string
from graph_asset import pins

root=Path('Saved/TrialWorldResetFix')
def clone(ed,template,label):
 idx=len(ed.a['Exports'])+1;e=copy.deepcopy(ed.e(template))
 e['ObjectName']='K2Node_WorldReset_'+label;ed.fname(e['ObjectName']);ed.a['Exports'].append(e)
 prop(e,'NodeGuid')['Value'][0]['Value']='{'+str(uuid.uuid5(uuid.NAMESPACE_URL,e['ObjectName'])).upper()+'}'
 data=bytearray(base64.b64decode(e['Extras']))
 for p in pins(ed.a,e):
  g=uuid.uuid5(uuid.NAMESPACE_URL,e['ObjectName']+'/'+p['name']).bytes_le
  for offset in (4,24):struct.pack_into('<i',data,p['start']+offset,idx)
  for offset in (8,28):data[p['start']+offset:p['start']+offset+16]=g
 e['Extras']=base64.b64encode(data).decode()
 for p in list(pins(ed.a,e)):ed.links(idx,p['name'],[])
 nodes=prop(ed.e(e['OuterIndex']),'Nodes')['Value'];item=copy.deepcopy(nodes[0]);item.update(Name=str(len(nodes)),Value=idx);nodes.append(item)
 ed.changed.add(idx);return idx

def write(ed,name):
 ed.save(name);(root/(name+'.patched.json')).write_text(json.dumps(ed.a))

tile=Editor(json.loads((root/'BP_Tile.json').read_text(encoding='utf-8-sig')))
# Fresh unvisited tiles expose zero impact, not a previous trial's observation.
impact=clone(tile,96,'ClearObservedTileImpact')
tile.rewire(99,'then',impact,'execute');tile.connect(impact,'then',22,'execute')
write(tile,'BP_Tile')

resource=Editor(json.loads((root/'BP_Resource.json').read_text(encoding='utf-8-sig')))
# Cancel the actual Respawn event timer, not an unrelated actor timer.
system=next(-i for i,e in enumerate(resource.a['Imports'],1) if e['ObjectName']=='KismetSystemLibrary')
old=pins(resource.a,resource.e(27));tail=base64.b64decode(resource.e(27)['Extras'])[old[-1]['end']:]
clear=resource.node(27,'K2Node_WorldReset_ClearRespawnTimer','K2_ClearTimer',[
 ('execute',0,'exec'),('then',1,'exec'),('self',0,'object',system),
 ('Object',0,'object',resource.import_class('Object')),('FunctionName',0,'string',0,'Respawn')],200,600)
resource.e(clear)['Extras']=base64.b64encode(base64.b64decode(resource.e(clear)['Extras'])+tail).decode()
p=resource.p(clear,'FunctionName');resource.replace(clear,p['default_end'],p['default_end']+len(string(p['auto_default'])),string(''))
resource.connect(57,'self',clear,'Object')
resource.rewire(33,'then',clear,'execute');resource.connect(clear,'then',91,'execute')
# Reuse Respawn's visibility, overlap-event and actor-collision restoration.
# No timer is started and the phase toggle paths remain untouched.
resource.connect(24,'then',25,'execute')
write(resource,'BP_Resource')
