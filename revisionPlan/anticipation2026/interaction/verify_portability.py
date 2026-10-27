"""Reproduce all factorial CSVs using only the archived paper inputs."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
TABLES = [
    'trial_metrics.csv', 'phase_summary.csv', 'interactions.csv',
    'simple_rate_effects.csv', 'ccc_contrasts.csv', 'sensitivity.csv',
    'baseline_matched_ids.csv', 'landscape_counts.csv',
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    manifest = json.loads((HERE / 'bundle_manifest.json').read_text())
    archive = HERE / manifest['archive']
    assert sha(archive) == manifest['sha256']
    with tempfile.TemporaryDirectory(prefix='hrl-interaction-portability-', dir='/private/tmp') as temporary:
        root = Path(temporary)
        with zipfile.ZipFile(archive) as bundle:
            members = [item for item in bundle.infolist() if item.filename.startswith('paper/')]
            assert members
            for item in members:
                assert '..' not in Path(item.filename).parts
                bundle.extract(item, root)
        paper = root / 'paper'
        analysis = paper / 'revisionPlan/anticipation2026/interaction'
        command = subprocess.run(
            [sys.executable, str(analysis / 'analyze.py')], cwd=paper,
            capture_output=True, text=True, timeout=180, check=True,
        )
        tables = {}
        for name in TABLES:
            actual, expected = sha(analysis / name), sha(HERE / name)
            assert actual == expected, name
            tables[name] = actual
    receipt = dict(
        passed=True, archive_sha256=manifest['sha256'],
        check='Fresh extraction of archived paper inputs; all eight regenerated CSVs are byte-identical.',
        tables=tables, reproduction_output=command.stdout.strip(),
    )
    (HERE / 'portability_validation.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(receipt['check'])


if __name__ == '__main__':
    main()
