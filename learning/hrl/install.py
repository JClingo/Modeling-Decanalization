"""Install only a new opt-in module directory; never replace production assets."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,tempfile

HERE=Path(__file__).resolve().parent
DEFAULT=Path('/Users/jingo/Work/PhD/Dissertation Project/decanalization/analysis/hrl_learning')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--destination',type=Path,default=DEFAULT)
    args=parser.parse_args();destination=args.destination.resolve()
    receipt=HERE/'validation/summary.json'
    assert receipt.exists(),'Finish validation before installing'
    validation=json.loads(receipt.read_text())
    assert validation['passed'],'Finish validation before installing'
    for relative,expected in validation['validated_artifacts'].items():
        assert hashlib.sha256((HERE/relative).read_bytes()).hexdigest()==expected,'Changed since validation: '+relative
    assert not destination.exists(),'Refusing to overwrite an existing module directory'
    assert destination.parent.is_dir()
    staging=Path(tempfile.mkdtemp(prefix='.hrl-learning-install-',dir=destination.parent))
    try:
        for path in HERE.rglob('*'):
            if not path.is_file() or '__pycache__' in path.parts or path.suffix=='.pyc':continue
            relative=path.relative_to(HERE);target=staging/relative
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
        hashes={str(p.relative_to(staging)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in staging.rglob('*') if p.is_file()}
        (staging/'installation_manifest.json').write_text(json.dumps(dict(source=str(HERE),files=hashes,
            production_assets_modified=False,mode='opt-in isolated project runner'),indent=2)+'\n')
        os.rename(staging,destination)
    except BaseException:
        shutil.rmtree(staging);raise
    print('INSTALLED '+str(destination))

if __name__=='__main__':main()
