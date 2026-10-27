"""Patch reset graphs exported from the current assets into Saved/ResetFix.

Compile the staged assets with Unreal before running reset validation.
"""
import copy
import base64
import json
from pathlib import Path
from patch_graphs import Editor, prop
from graph_asset import pins

root = Path('Saved/ResetFix')

def read(name):
    return Editor(json.loads((root / (name + '.json')).read_text(encoding='utf-8')))

def write(ed, name):
    ed.save(name)
    (root / (name + '.patched.json')).write_text(json.dumps(ed.a), encoding='utf-8')

def call(ed, function, parent, specs, pure=False):
    idx = ed.node(95 if not pure else 126, 'K2Node_CallFunction_Reset' + function + str(len(ed.a['Exports'])),
                  function, specs, 800, 1800 + len(ed.changed) * 100)
    ref = prop(ed.e(idx), 'FunctionReference')
    template = next(p for e in ed.a['Exports'] for p in e.get('Data', [])
                    if p['Name'] == 'FunctionReference' and
                    any(q['Name'] == 'MemberParent' for q in p['Value']))
    member = copy.deepcopy(next(q for q in template['Value'] if q['Name'] == 'MemberParent'))
    member['Value'] = parent
    ref['Value'] = [member, next(q for q in ref['Value'] if q['Name'] == 'MemberName')]
    return idx

env = read('BP_AgentTrainingEnv')
# Keep the >1 gate solely for reporting the previous episode. Every branch
# must run Initialize before resetting the pawn, including training start.
env.rewire(210, 'else', 143, 'execute')
# Immediately after reset there is only the seeded homeostatic value. Treat it
# as the previous value until a second sample exists, avoiding index -1.
original_outer = env.e(142)['OuterIndex']
env.e(142)['OuterIndex'] = env.e(301)['OuterIndex']
clamp = env.node(142, 'K2Node_CallFunction_ResetPreviousSetpoint', 'Max', [
    ('self',0,'object',-28), ('A',0,'int',0,'0'), ('B',0,'int',0,'0'),
    ('ReturnValue',1,'int',0,'0')], 400, 300)
env.e(142)['OuterIndex'] = original_outer
ref = prop(env.e(clamp), 'FunctionReference')
parent = copy.deepcopy(next(q for q in prop(env.e(301),'FunctionReference')['Value'] if q['Name']=='MemberParent'))
ref['Value'] = [parent, next(q for q in ref['Value'] if q['Name']=='MemberName')]
env.rewire(181, 'Dimension 1', clamp, 'ReturnValue')
env.connect(301, 'ReturnValue', clamp, 'A')
write(env, 'BP_AgentTrainingEnv')

a = read('BP_Agent')
char = a.import_class('Character')
pawn = a.import_class('Pawn')
movement = a.import_class('CharacterMovementComponent')
controller = a.import_class('Controller')
actor = a.import_class('Actor')
math = a.import_class('KismetMathLibrary')

def impure(function, parent, extra=(), target=None):
    idx = call(a, function, parent,
               [('execute', 0, 'exec'), ('then', 1, 'exec'), ('self', 0, 'object', parent)] + list(extra))
    if target: a.connect(*target, idx, 'self')
    return idx

# Consume twice: the first clears pending input; the second clears LastInput.
stop_jump = impure('StopJumping', char)
uncrouch = impure('UnCrouch', char, [('bClientSimulation', 0, 'bool', 0, 'false')])
forces = impure('ClearAccumulatedForces', movement, target=(318, 'CharacterMovement'))
stop = impure('StopMovementImmediately', movement, target=(318, 'CharacterMovement'))
vector = next(-i for i,x in enumerate(a.a['Imports'],1) if x['ObjectName']=='Vector' and x['ClassName']=='ScriptStruct')
consume = impure('ConsumeMovementInputVector', pawn, [('ReturnValue', 1, 'struct', vector)])
consume2 = impure('ConsumeMovementInputVector', pawn, [('ReturnValue', 1, 'struct', vector)])
rotator = next(-i for i,x in enumerate(a.a['Imports'],1) if x['ObjectName']=='Rotator' and x['ClassName']=='ScriptStruct')
get_controller = call(a, 'GetController', pawn,
                      [('self', 0, 'object', pawn), ('ReturnValue', 1, 'object', controller)], pure=True)
make_rotation = call(a, 'MakeRotator', math,
                     [('self', 0, 'object', math), ('Roll', 0, 'real', 0, '0.0', 'double'),
                      ('Pitch', 0, 'real', 0, '0.0', 'double'), ('Yaw', 0, 'real', 0, '0.0', 'double'),
                      ('ReturnValue', 1, 'struct', rotator)], pure=True)
set_control = impure('SetControlRotation', controller, [('NewRotation', 0, 'struct', rotator)],
                     target=(get_controller, 'ReturnValue'))
set_actor = impure('K2_SetActorRotation', actor,
                   [('NewRotation', 0, 'struct', rotator), ('bTeleportPhysics', 0, 'bool', 0, 'true'),
                    ('ReturnValue', 1, 'bool', 0, 'false')])
# Evaluate random yaw once by storing it before feeding both actor/controller.
# SetControlRotation's input and SetActorRotation share a pure expression, so
# use actor's control rotation getter for the latter after the controller set.
get_rotation = call(a, 'GetControlRotation', controller,
                    [('self', 0, 'object', controller), ('ReturnValue', 1, 'struct', rotator)], pure=True)
a.connect(get_controller, 'ReturnValue', get_rotation, 'self')
a.connect(126, 'ReturnValue', make_rotation, 'Yaw')
a.connect(make_rotation, 'ReturnValue', set_control, 'NewRotation')
a.connect(get_rotation, 'ReturnValue', set_actor, 'NewRotation')
a.disconnect(136, 'execute')
a.disconnect(136, 'Val')
a.rewire(95, 'then', set_control, 'execute')
a.connect(set_control, 'then', set_actor, 'execute')
# Clear stale collision cache before moving; teleport overlap callbacks may
# populate the new location's resource reference.
clear_collision = a.node(416, 'K2Node_VariableSet_ResetCollision', '', [
    ('execute', 0, 'exec'), ('then', 1, 'exec'),
    ('CollidingResource', 0, 'object', next(-i for i,x in enumerate(a.a['Imports'],1) if x['ObjectName']=='BP_Resource_C')),
    ('Output_Get', 1, 'object', next(-i for i,x in enumerate(a.a['Imports'],1) if x['ObjectName']=='BP_Resource_C')),
    ('self', 0, 'object', 0)], 800, 1600)
# Resolve the world GameMode at reset time as well as BeginPlay. A reset can
# arrive before the pawn's cached GameMode has been initialized.
gm_type = next(-i for i,x in enumerate(a.a['Imports'],1) if x['ObjectName']=='BP_GameMode_C')
gm_cast = a.node(174, 'K2Node_DynamicCast_ResetGameMode', '', [
    ('execute',0,'exec'), ('then',1,'exec'), ('CastFailed',1,'exec'),
    ('Object',0,'object',a.import_class('Object')),
    ('AsBP Game Mode',1,'object',gm_type), ('bSuccess',1,'bool',0,'false')], 400, 1400)
# DynamicCast serializes its purity flag after the standard graph pin payload.
original_extras = base64.b64decode(a.e(174)['Extras'])
tail = original_extras[pins(a.a,a.e(174))[-1]['end']:]
a.e(gm_cast)['Extras'] = base64.b64encode(base64.b64decode(a.e(gm_cast)['Extras']) + tail).decode()
cache_gm = a.node(406, 'K2Node_VariableSet_ResetGameMode', '', [
    ('execute',0,'exec'), ('then',1,'exec'), ('BP Game Mode',0,'object',gm_type),
    ('Output_Get',1,'object',gm_type), ('self',0,'object',0)], 600, 1400)
a.connect(117,'ReturnValue',gm_cast,'Object')
a.connect(gm_cast,'AsBP Game Mode',cache_gm,'BP Game Mode')
a.connect(gm_cast,'then',cache_gm,'execute')
a.connect(cache_gm,'then',stop_jump,'execute')
a.rewire(169, 'then', gm_cast, 'execute')
chain = [stop_jump, uncrouch, forces, stop, consume, consume2, clear_collision]
for left,right in zip(chain,chain[1:]): a.connect(left, 'then', right, 'execute')
a.connect(clear_collision, 'then', 219, 'execute')
write(a, 'BP_Agent')
