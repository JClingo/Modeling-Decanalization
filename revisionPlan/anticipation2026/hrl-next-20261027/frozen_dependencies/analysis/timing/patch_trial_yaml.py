"""Create and checkpoint trial YAML in Saved/TrialResults while IsTrialMode is true.

Input is the current exported GameMode under Saved/TrialYamlFix; Unreal must
compile the imported asset before use. Does not change trial/phase timing.
"""
import base64
import copy
import json
import struct
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'timing'))
from patch_graphs import Editor, prop, string
from graph_asset import pins

root = Path('Saved/TrialYamlFix')
ed = Editor(json.loads((root / 'BP_GameMode.json').read_text(encoding='utf-8-sig')))

def graph(i):
    return ed.e(i)['OuterIndex']

def clone(template, label, outer):
    idx = len(ed.a['Exports']) + 1
    e = copy.deepcopy(ed.e(template))
    e['ObjectName'] = 'K2Node_TrialYaml_' + label
    e['OuterIndex'] = outer
    ed.fname(e['ObjectName'])
    ed.a['Exports'].append(e)
    node_guid = next((p for p in e.get('Data', []) if p['Name'] == 'NodeGuid'), None)
    if node_guid:
        node_guid['Value'][0]['Value'] = '{' + str(uuid.uuid5(uuid.NAMESPACE_URL, e['ObjectName'])).upper() + '}'
    data = bytearray(base64.b64decode(e['Extras']))
    for p in pins(ed.a, e):
        guid = uuid.uuid5(uuid.NAMESPACE_URL, e['ObjectName'] + '/' + p['name']).bytes_le
        for offset in (4, 24):
            struct.pack_into('<i', data, p['start'] + offset, idx)
        for offset in (8, 28):
            data[p['start'] + offset:p['start'] + offset + 16] = guid
    e['Extras'] = base64.b64encode(data).decode()
    for p in list(pins(ed.a, e)):
        ed.links(idx, p['name'], [])
    nodes = prop(ed.e(outer), 'Nodes')['Value']
    item = copy.deepcopy(nodes[0]); item['Name'] = str(len(nodes)); item['Value'] = idx
    nodes.append(item)
    ed.changed.add(idx)
    return idx

def default(idx, name, value):
    p = ed.p(idx, name)
    ed.replace(idx, p['default_start'], p['default_end'], string(value))

def function(template, label, name, specs, outer, parent):
    idx = clone(template, label, outer)
    e = ed.e(idx)
    old = pins(ed.a, e)
    tail = base64.b64decode(e['Extras'])[old[-1]['end']:]
    e['Extras'] = base64.b64encode(struct.pack('<i', len(specs)) + b''.join(ed.pin(idx, *s) for s in specs) + tail).decode()
    ref = prop(e, 'FunctionReference')['Value']
    next(p for p in ref if p['Name'] == 'MemberName')['Value'] = name
    next(p for p in ref if p['Name'] == 'MemberParent')['Value'] = parent
    ed.fname(name)
    return idx

create_graph, event_graph = graph(162), graph(706)
system = next(-i for i, e in enumerate(ed.a['Imports'], 1) if e['ObjectName'] == 'KismetSystemLibrary')
guidlib = ed.import_class('KismetGuidLibrary')
# Guid is a CoreUObject script struct, not an Engine class.
guid_import = copy.deepcopy(next(e for e in ed.a['Imports'] if e['ClassName'] == 'ScriptStruct'))
guid_import.update(ObjectName='Guid', OuterIndex=next(-i for i, e in enumerate(ed.a['Imports'], 1) if e['ObjectName']=='/Script/CoreUObject'))
ed.fname('Guid'); ed.a['Imports'].append(guid_import); ed.a['ImportBits'].append(True)
guid_struct = -len(ed.a['Imports'])

saved = function(163, 'SavedDirectory', 'GetProjectSavedDirectory', [
    ('self', 0, 'object', system), ('ReturnValue', 1, 'string')], create_graph, system)
new_guid = function(163, 'NewRunId', 'NewGuid', [
    ('self', 0, 'object', guidlib), ('ReturnValue', 1, 'struct', guid_struct)], create_graph, guidlib)
guid_string = function(163, 'RunIdString', 'Conv_GuidToString', [
    ('self', 0, 'object', guidlib), ('InGuid', 0, 'struct', guid_struct), ('ReturnValue', 1, 'string')], create_graph, guidlib)
ed.connect(new_guid, 'ReturnValue', guid_string, 'InGuid')
path_prefix = clone(301, 'TrialResultsDirectory', create_graph)
ed.connect(saved, 'ReturnValue', path_prefix, 'A'); default(path_prefix, 'B', 'TrialResults/')
ed.rewire(292, 'A', path_prefix, 'ReturnValue')
default(292, 'E', '-')
ed.rewire(292, 'F', guid_string, 'ReturnValue')
filename = clone(301, 'YamlFilename', create_graph)
ed.connect(292, 'ReturnValue', filename, 'A'); default(filename, 'B', '.yml')
# Cache the pure GUID-based filename ONCE, before creating the file and returning
# it. Otherwise repeated evaluation of NewGuid would select different files.
cache_path = clone(739, 'CacheRunPath', create_graph)
get_path = clone(673, 'CachedRunPath', create_graph)
ed.connect(filename, 'ReturnValue', cache_path, 'TrialFileName')
for setter in (683, 684):
    ed.rewire(setter, 'then', cache_path, 'execute')
ed.connect(cache_path, 'then', 162, 'execute')
ed.rewire(162, 'FileName', get_path, 'TrialFileName')
ed.rewire(426, 'InputPin', get_path, 'TrialFileName')

# The existing IsTrialMode-gated BeginPlay initialization creates the run file
# before Reset broadcasts prepare the first trial header.
create_call = clone(236, 'CreateRunAtBeginPlay', event_graph)
save_initial = clone(233, 'WriteInitialDocument', event_graph)
ed.rewire(706, 'then', create_call, 'execute')
ed.connect(create_call, 'then', save_initial, 'execute')
ed.connect(save_initial, 'then', 115, 'execute')
# Keep one run file; the final trial must not create a second empty file.
ed.disconnect(739, 'then')
ed.rewire(414, 'then', 233, 'execute')

# Persist the complete document after each trial header and phase record.
# The existing append writer omitted headers until the final save.
ready_save = clone(233, 'CheckpointTrialHeader', graph(727))
ed.rewire(727, 'then', ready_save, 'execute')
ed.connect(ready_save, 'then', 366, 'execute')
phase_save = clone(233, 'CheckpointPhaseResults', graph(744))
ed.rewire(744, 'then', phase_save, 'execute')

# Central writer also rejects direct calls when trial mode is disabled.
gate = clone(396, 'WriteOnlyInTrialMode', graph(243))
trial_mode = clone(595, 'IsTrialMode', graph(243))
ed.connect(trial_mode, 'IsTrialMode', gate, 'Condition')
ed.rewire(344, 'then', gate, 'execute')
ed.connect(gate, 'then', 243, 'execute')
default(243, 'Encoding', 'ForceUTF8WithoutBOM')
# Report write failures to the Unreal log instead of silently losing a trial.
write_ok = clone(396, 'WriteSucceeded', graph(243))
error = clone(228, 'ReportWriteFailure', graph(243))
msg = clone(301, 'WriteFailureMessage', graph(243))
default(msg, 'A', 'ERROR: Failed to save trial YAML: ')
get_error_path = clone(673, 'FailedOutputPath', graph(243))
ed.connect(get_error_path, 'TrialFileName', msg, 'B')
ed.rewire(error, 'InString', msg, 'ReturnValue')
default(error, 'bPrintToScreen', 'false')
ed.connect(243, 'then', write_ok, 'execute')
ed.connect(243, 'ReturnValue', write_ok, 'Condition')
ed.connect(write_ok, 'else', error, 'execute')

ed.save('BP_GameMode')
(root / 'BP_GameMode.patched.json').write_text(json.dumps(ed.a), encoding='utf-8')
