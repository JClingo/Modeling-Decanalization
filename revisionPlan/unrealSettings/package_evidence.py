"""Validate the extraction and package the native exports without changing sources."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
PROJECT = Path(r"C:\Users\jingo\Documents\Unreal Projects\decanalization")
LABELS = ("current", "committed_b2ec222", "study_candidate_5e508dd")
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--package-retained-exports", action="store_true",
                    help="Package the existing capture even if the source workspace has since changed; record the differences without refreshing exports or their original hashes.")
args = parser.parse_args()

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

original = read(ROOT / "source_manifest.json")
changed = []
for record in original["assets"]:
    path = PROJECT / record["file"]
    current_sha = sha(path) if path.exists() else None
    if current_sha != record["sha256"]:
        changed.append({"file": record["file"], "export_source_sha256": record["sha256"],
                        "workspace_sha256_at_packaging": current_sha})
assert not changed or args.package_retained_exports, "Source assets differ from the original export: " + str(changed)

settings = read(ROOT / "settings.json")
assert settings["run_configs"]["HRL"]["PPOSettings"] == settings["run_configs"]["NF"]["PPOSettings"]
assert settings["run_configs"]["HRL"]["Schemas"] == settings["run_configs"]["NF"]["Schemas"]
assert settings["run_configs"]["HRL"]["PPOSettings"]["PolicyBatchSize"] == 2056
for label in LABELS:
    models = settings["models"][label]
    assert sum(m["trainable_parameters"] for m in models) == 143637
    assert len([m for m in models if m["matching_checkpoints"]]) == 3

files = set()
exports = 0
for label in LABELS:
    report_path = ROOT / "raw" / label / "export_report.json"
    report = read(report_path)
    assert not report["errors"], report["errors"]
    files.add(report_path)
    for record in report["exports"]:
        assert record["success"] and not record["errors"], record
        path = report_path.parent / record["file"]
        assert path.stat().st_size > 0
        files.add(path)
        exports += 1
    files.update(report_path.parent.glob("*.bin"))
    valid_names = {Path(x["file"]).stem for x in report["exports"]}
    files.update(p for p in (ROOT / "derived" / label).iterdir() if p.stem in valid_names)

files.update((ROOT / "raw/trainer_configs").glob("*.json"))
config_dir = ROOT / "raw/project_config_current"
config_dir.mkdir(exist_ok=True)
for path in [PROJECT / "ue_canalization.uproject", *PROJECT.joinpath("Config").glob("*.ini")]:
    target = config_dir / path.name
    if args.package_retained_exports:
        assert target.exists(), "Missing original captured project config: " + str(target)
    else:
        target.write_bytes(path.read_bytes())
    files.add(target)

for filename in ("README.md", "settings.json", "source_manifest.json", "training_configs.json", "checkpoint_inventory.json",
                 "checkpoint_architectures.json", "evaluation_data_provenance.json", "training_event_summary.json",
                 "representative_training_dashboard.png"):
    files.add(ROOT / filename)
files.update(ROOT.glob("*.py"))
files.add(ROOT / "run_exports.ps1")

manifest = {"source_assets_checked": len(original["assets"]), "source_asset_changes": changed,
            "source_assets_match_current_workspace": not changed,
            "capture_scope": "Retained native exports from the original extraction; latest workspace changes were not re-exported." if args.package_retained_exports else "Native exports validated against the current workspace.",
            "successful_native_exports": exports, "labels": list(LABELS),
            "files": [{"file": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)} for p in sorted(files)]}
manifest_path = ROOT / "evidence_manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
files.add(manifest_path)
archive = ROOT / "unreal-settings-evidence.zip"
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for path in sorted(files):
        z.write(path, path.relative_to(ROOT).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for entry in manifest["files"]:
        assert hashlib.sha256(z.read(entry["file"])).hexdigest() == entry["sha256"]
print(json.dumps({"archive": str(archive), "bytes": archive.stat().st_size,
                  "source_assets_still_matching_original_export": len(original["assets"]) - len(changed),
                  "source_assets_changed_since_export": changed, "successful_exports": exports,
                  "archive_entries": len(files), "archive_verified": True}, indent=2))
