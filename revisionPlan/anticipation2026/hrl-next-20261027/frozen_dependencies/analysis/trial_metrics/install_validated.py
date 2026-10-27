"""Install validated assets after the project is closed; refuse intervening edits."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
work=ROOT/'Saved/TrialMetricsFix'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for name,folder in [('BFL_Common','Libraries'),('BP_AgentTrainingEnv','Learning'),('BP_GameMode','Agent')]:
    dest=ROOT/'Content'/folder/(name+'.uasset');old=work/'backup'/dest.name;new=work/'compiled'/dest.name
    assert sha(dest) in (sha(old),sha(new)),'Production asset changed since backup: '+str(dest)
    records.append(dict(path=str(dest.relative_to(ROOT)),before=sha(old),after=sha(new)))
for record in records:
    dest=ROOT/record['path']
    if sha(dest)!=record['after']:shutil.copy2(work/'compiled'/dest.name,dest)
    assert sha(dest)==record['after']
(ROOT/'analysis/trial_metrics/installed_assets.json').write_text(json.dumps(records,indent=2))
print('Installed three validated production-default assets; original backups preserved.')
