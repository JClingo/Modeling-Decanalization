"""Use the existing seeded Bernoulli decision for initial pellet population."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'timing'))
from patch_graphs import Editor

root=Path('Saved/RngSeedFix')
ed=Editor(json.loads((root/'BP_ResourceSpawner.json').read_text(encoding='utf-8-sig')))
# SpawnRate now means expected occupancy, rather than a fixed floor(p*N).
# The existing ShouldSpawn function consumes the shared stream by reference.
ed.rewire(76,'LastIndex',95,'ReturnValue')
ed.rewire(76,'LoopBody',29,'execute')
ed.rewire(66,'then',98,'execute')
# The existing completion still shuffles unique grid locations and positions
# the resulting pellet list; reset/phase behavior is unchanged.
ed.save('BP_ResourceSpawner')
(root/'spawner.patched.json').write_text(json.dumps(ed.a))
