"""Share identical completed scratch assets with APFS copy-on-write clones.

Every asset remains present and runnable. Later writes are independent. This
never uses hard links and never alters protected production files or models.
"""
from pathlib import Path
import ctypes,hashlib,json,os,shutil

ROOTS=[Path('/private/tmp')/name for name in [
    'hrl-learning-final-20261026','hrl-study-pipeline-check-final-20261026',
    'hrl-canalization-study-20261026']]
lib=ctypes.CDLL('/usr/lib/libSystem.B.dylib',use_errno=True)
clone=lib.clonefile;clone.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int];clone.restype=ctypes.c_int
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    before=shutil.disk_usage('/private/tmp').free;total=0;count=0
    for root in ROOTS:
        template=root/'template/TestProject/Content'
        for verified in sorted(root.glob('*/training_verified.json')):
            folder=verified.parent;project=folder/'TestProject';receipt=folder/'cow_storage_receipt.json'
            if receipt.exists() or not json.loads(verified.read_text())['passed']:continue
            if not (project/'HRL_LEARNING_COPY').exists():continue
            selection=folder/'selection.json'
            if selection.exists() and not json.loads(selection.read_text()).get('complete'):continue
            assert json.loads((folder/'engine_result.json').read_text())['passed']
            shared={}
            for target in (project/'Content').rglob('*'):
                if not target.is_file() or target.is_symlink():continue
                relative=target.relative_to(project/'Content');source=template/relative
                if not source.is_file() or source.stat().st_size!=target.stat().st_size:continue
                digest=sha(target)
                if sha(source)!=digest:continue
                temporary=target.with_name(target.name+'.cow-tmp');assert not temporary.exists()
                if clone(os.fsencode(source),os.fsencode(temporary),0):raise OSError(ctypes.get_errno(),os.strerror(ctypes.get_errno()))
                assert sha(temporary)==digest
                shutil.copystat(target,temporary);os.replace(temporary,target)
                shared[str(relative)]=digest;total+=target.stat().st_size;count+=1
            receipt.write_text(json.dumps(dict(method='APFS copy-on-write clone; no hard links',
                template=str(template),all_asset_bytes_preserved=True,shared_files=shared),indent=2)+'\n')
    print(json.dumps(dict(files_shared=count,logical_gib_shared=round(total/2**30,2),
        free_gib_before=round(before/2**30,2),free_gib_after=round(shutil.disk_usage('/private/tmp').free/2**30,2))))

if __name__=='__main__':main()
