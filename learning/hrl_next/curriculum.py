"""Physical world-duration advancement, independent of optimizer boundaries."""
def next_stage(stage,recent,just_reset):
    if stage not in (0,1,2):raise ValueError('Unknown curriculum stage')
    if stage==2 or not just_reset or len(recent)!=10:return stage
    stable=sum(x['training_time_mae'] for x in recent)/10<=25.
    stable=stable and sum(x['terminated_transitions'] for x in recent)/100000<=.0025
    if stable and recent[-1]['steps'] >= [500000,1000000][stage]:return stage+1
    return stage
