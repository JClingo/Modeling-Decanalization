"""Restore only test-created side effects, preserving copies for inspection.

The four networks were backed up before this repair. The listed external actor
was clean in the initial git status; the tests saved it after transient CDO
snapshot overrides. Never use this script on a later checkout without checking
whether that external actor has acquired independent work.
"""
import hashlib
import shutil
import subprocess
from pathlib import Path

root=Path(__file__).resolve().parents[2]
saved=root/'Saved/TimingFix'
for name in ['DA_AgentEncoder','DA_AgentPolicy','DA_AgentDecoder','DA_AgentCritic']:
    rel=Path('Content/Learning')/(name+'.uasset')
    current,backup=root/rel,saved/'backup'/rel
    side=saved/'test_saved'/rel
    side.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(current,side)
    shutil.copy2(backup,current)
    assert hashlib.sha256(current.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()

rel=Path('Content/__ExternalActors__/Level/Landscape/E/OC/47RXQXA54PZRMOUO7PJBGB.uasset')
side=saved/'test_saved'/rel
side.parent.mkdir(parents=True,exist_ok=True)
shutil.copy2(root/rel,side)
original=subprocess.check_output(['git','show','HEAD:'+rel.as_posix()],cwd=root)
(root/rel).write_bytes(original)
print('Restored four original network assets and the initially clean external actor.')
