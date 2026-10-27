"""Finish this single running study after its training processes exit."""
from pathlib import Path
import argparse,json,os,subprocess,time,traceback
import compare

HERE=Path(__file__).resolve().parent

def alive(pid):
    try:os.kill(pid,0);return True
    except ProcessLookupError:return False

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--wait-for',nargs='+',type=int,required=True)
    args=parser.parse_args();p=compare.protocol();root=Path(p['raw_root'])
    compare.native.write(HERE/'postprocessing_process.json',dict(pid=os.getpid(),training_pids=args.wait_for))
    # Ends with this process. It does not keep the display awake.
    subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        last=None
        while any(alive(pid) for pid in args.wait_for):
            completed=sum((root/f'canalization-{name}-{seed}'/'selection.json').exists() and
                compare.native.read(root/f'canalization-{name}-{seed}'/'selection.json').get('complete',False)
                for name in p['conditions'] for seed in p['training_seeds'])
            if completed!=last:
                compare.native.write(HERE/'postprocessing_status.json',dict(status='waiting-for-training',completed_policies=completed,total_policies=12))
                print('COMPLETED_POLICIES '+str(completed)+'/12',flush=True);last=completed
            time.sleep(10)
        compare.native.write(HERE/'postprocessing_status.json',dict(status='independent-evaluation'))
        compare.evaluate()
        compare.native.write(HERE/'postprocessing_status.json',dict(status='analyzing'))
        compare.summarize()
        compare.native.write(HERE/'postprocessing_status.json',dict(status='plotting'))
        subprocess.run([str(compare.native.PYTHON_ENV/'bin/python'),str(HERE/'plot.py')],check=True)
        compare.native.write(HERE/'postprocessing_status.json',dict(status='complete',results=str(HERE/'results.json')))
    except BaseException:
        compare.native.write(HERE/'postprocessing_status.json',dict(status='failed',error=traceback.format_exc()))
        raise

if __name__=='__main__':main()
