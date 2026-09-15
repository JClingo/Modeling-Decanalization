"""Materialize a Git revision into a separate, read-only-source export project."""
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

PROJECT = Path(r"C:\Users\jingo\Documents\Unreal Projects\decanalization")
revision = sys.argv[1]
commit = subprocess.check_output(["git", "-C", str(PROJECT), "rev-parse", revision], text=True).strip()
target = PROJECT / "Saved" / "SettingsExportSnapshots" / commit[:12]
target.mkdir(parents=True, exist_ok=True)
archive = subprocess.check_output(["git", "-C", str(PROJECT), "archive", "--format=zip", commit, "Content", "Config", "ue_canalization.uproject"])
with zipfile.ZipFile(io.BytesIO(archive)) as z:
    for entry in z.infolist():
        dest = (target / entry.filename).resolve()
        if not dest.is_relative_to(target.resolve()):
            raise ValueError(entry.filename)
    z.extractall(target)
(target / "source_revision.json").write_text(json.dumps({"source_project": str(PROJECT), "revision": commit}, indent=2))
print(target)
