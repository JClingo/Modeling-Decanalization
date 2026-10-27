"""Compare startup/reset trajectories without modifying the production project.

Matched cases restore the startup scene after a full reset. This is an audit
intervention, not a proposed production reset: native policy/movement reset is
retained unless the explicit restore-velocity ablation is requested.
"""
import hashlib
import json
import math
from pathlib import Path
import time
import traceback
import unreal

project = Path(unreal.Paths.project_dir()).resolve()
assert project.parent.name == 'ResetPerformanceAudit'
root = project.parent
args = unreal.SystemLibrary.get_command_line().split()
label = next(a.split('=', 1)[1] for a in args if a.startswith('-AuditLabel='))
matched = '-MatchedScene' in args
restore_velocity = '-RestoreVelocity' in args
restore_stream = '-RestoreStream' in args
world = unreal.find_object(None, '/Game/Level/Landscape.Landscape')
gm = unreal.GameplayStatics.get_game_mode(world)
def actors(name, folder):
    cls = unreal.load_class(None, '/Game/' + folder + '/' + name + '.' + name + '_C')
    return sorted(unreal.GameplayStatics.get_all_actors_of_class(world, cls), key=lambda a: a.get_name())
manager = actors('BP_AgentManager', 'Learning')[0]
agent = actors('BP_Agent', 'Agent')[0]
resources = actors('BP_Resource', 'Resource')
tiles = actors('BP_Tile', 'Level')
la = manager.get_editor_property('LearningAgentsManager')
policy = manager.get_editor_property('Policy')
interactor = manager.get_editor_property('Interactor')
aid = la.get_agent_id(agent)
movement = agent.get_editor_property('character_movement')
def get(o, n): return o.get_editor_property(n)
def setp(o, n, v): o.set_editor_property(n, v, notify_mode=unreal.PropertyAccessChangeNotifyMode.NEVER)
def vec(v): return [v.x, v.y, v.z]
def scene():
    return {'position': vec(agent.get_actor_location()), 'yaw': agent.get_actor_rotation().yaw,
            'setpoints': list(get(gm, 'Setpoints')),
            'resources': [[a.get_name(), vec(a.get_actor_location()), get(a, 'BaseHomeostaticImpact'),
                           get(a, 'HomeostaticImpact'), get(a, 'OverlapCount')] for a in resources],
            'tiles': [[a.get_name(), get(a, 'HomeostaticImpact'), get(a, 'OverlapCount')] for a in tiles]}
def status():
    return {'position': vec(agent.get_actor_location()), 'yaw': agent.get_actor_rotation().yaw,
            'control_yaw': agent.get_controller().get_control_rotation().yaw,
            'velocity': vec(agent.get_velocity()), 'memory': list(policy.get_memory_state(aid)),
            'setpoints': list(get(gm, 'Setpoints')),
            'max_speed': get(agent, 'MaxSpeed'), 'max_walk_speed': get(movement, 'max_walk_speed'),
            'anticipated_gain': get(agent, 'AnticipatedResourceGain'),
            'anticipated_loss': get(agent, 'AnticipatedResourceLoss'),
            'agent_delta': get(agent, 'Delta Seconds'), 'gm_delta': get(gm, 'Delta Seconds'),
            'tile_cost': get(agent, 'TileCostTotal'), 'time_alive': get(agent, 'TimeAlive'),
            'resource_hits': len(get(agent, 'CollidingDriveReducers')),
            'tile_hits': len(get(agent, 'CollidingDriveIncreasers')),
            'passive_loss': get(gm, 'PassiveLossRate'), 'decanalized': get(gm, 'IsDecanalized')}
result = {'label': label, 'matched_scene': matched, 'restore_velocity': restore_velocity,
          'restore_stream': restore_stream,
          'startup': status(), 'samples': [], 'phases': {}}
initial = scene()
result['initial_scene_sha256'] = hashlib.sha256(json.dumps(initial, sort_keys=True).encode()).hexdigest()
(root / (label + '.scene.json')).write_text(json.dumps(initial))
if matched:
    transform = agent.get_actor_transform()
    rotation = agent.get_controller().get_control_rotation()
    # get_editor_property returns a live struct wrapper; copy its coordinates
    # before ResetAllAgents mutates the underlying velocity.
    velocity = unreal.Vector(*vec(agent.get_velocity()))
    random_stream = get(gm, 'RandomStream').copy()
    resource_transforms = [a.get_actor_transform() for a in resources]
    points = list(get(gm, 'Setpoints'))
    la.reset_all_agents()
    # Bypass the new bootstrap since this explicit reset already exercised it.
    try: setp(gm, 'HasInitializedTrialRun', True)
    except Exception: pass
    agent.set_actor_transform(transform, False, True)
    agent.get_controller().set_control_rotation(rotation)
    for a, transform, state in zip(resources, resource_transforms, initial['resources']):
        a.set_actor_transform(transform, False, True)
        setp(a, 'BaseHomeostaticImpact', state[2])
        setp(a, 'HomeostaticImpact', state[3])
        setp(a, 'OverlapCount', state[4])
    # Teleport overlap callbacks may add impacts; restore after all teleports.
    for a, state in zip(tiles, initial['tiles']):
        setp(a, 'HomeostaticImpact', state[1])
        setp(a, 'OverlapCount', state[2])
    setp(gm, 'Setpoints', points)
    if restore_velocity: setp(movement, 'velocity', velocity)
    if restore_stream: setp(gm, 'RandomStream', random_stream)
    if restore_velocity: assert vec(agent.get_velocity()) == result['startup']['velocity']
    result['matched_scene_sha256'] = hashlib.sha256(json.dumps(scene(), sort_keys=True).encode()).hexdigest()
    assert result['matched_scene_sha256'] == result['initial_scene_sha256']
result['before_first_tick'] = status()
if '-BypassBootstrap' in args:
    setp(gm, 'HasInitializedTrialRun', True)
receipt = Path(unreal.Paths.convert_relative_path_to_full(get(gm, 'TrialFileName'))).with_suffix('.completed.json')
started = time.monotonic()
done = False
counter = 0
previous = agent.get_actor_location()
def save():
    result['wall_seconds'] = time.monotonic() - started
    (root / (label + '.json')).write_text(json.dumps(result, indent=2))
def finish(error=None):
    global done
    if done: return
    done = True
    result.update(passed=error is None, error=error)
    if receipt.exists(): result['completion'] = json.loads(receipt.read_text())
    for p in result['phases'].values():
        n = p['steps']
        p.update(mean=p['sum']/n, mae=p['absolute_sum']/n,
                 rms=math.sqrt(p['square_sum']/n), fraction_within_5=p['within_5']/n)
    save()
    unreal.unregister_slate_post_tick_callback(handle)
    unreal.SystemLibrary.execute_console_command(world, 'QUIT')
def tick(dt):
    global counter, previous
    try:
        if time.monotonic()-started > 160: raise RuntimeError('Comparison timed out')
        count = get(gm, 'TotalTickCount')
        phase = 'canalized' if count < 6000 else ('decanalized' if count < 12000 else 'recanalized')
        points = get(gm, 'Setpoints')
        h = points[-1]
        p = result['phases'].setdefault(phase, dict(steps=0, sum=0., absolute_sum=0., square_sum=0., within_5=0, distance=0.))
        p['steps'] += 1; p['sum'] += h; p['absolute_sum'] += abs(h); p['square_sum'] += h*h
        p['within_5'] += int(abs(h) <= 5)
        location = agent.get_actor_location()
        p['distance'] += (location-previous).length(); previous = location
        if counter < 200 or counter % 1000 == 0:
            observation, _ = interactor.get_observation_vector(aid)
            action, _ = interactor.get_action_vector(aid)
            sample = status()
            sample.pop('setpoints')
            sample.update(tick=count, homeostatic_state=h, observation=list(observation), action=list(action))
            result['samples'].append(sample)
        counter += 1
        if counter % 2000 == 0: result['progress'] = count; save()
        if receipt.exists(): finish()
    except Exception: finish(traceback.format_exc())
handle = unreal.register_slate_post_tick_callback(tick)
