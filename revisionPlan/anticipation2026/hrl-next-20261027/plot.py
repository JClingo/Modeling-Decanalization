"""Standalone policy-level figures; never pool different boundary protocols."""
from pathlib import Path
import json,os,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,'/private/tmp/hrl-study-plot-packages')
os.environ.setdefault('MPLCONFIGDIR','/private/tmp/hrl-study-mpl-cache')
os.environ['XDG_CACHE_HOME']='/private/tmp/hrl-study-xdg-cache'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    fig,axes=plt.subplots(1,3,figsize=(11,4.5),layout='constrained')
    for ax,stage in zip(axes,['reward','optimizer','duration']):
        path=HERE/stage/'results.json'
        if not path.exists():ax.set_axis_off();continue
        data=json.loads(path.read_text());names=[r['condition'] for r in data['summary']]
        seeds=sorted({r['training_seed'] for r in data['per_policy']})
        for seed in seeds:
            y=[next(r['mean_time_mae'] for r in data['per_policy'] if r['condition']==c and r['training_seed']==seed) for c in names]
            ax.plot(range(len(names)),y,color='#aaaaaa',lw=1,zorder=1)
        for i,c in enumerate(names):
            y=[r['mean_time_mae'] for r in data['per_policy'] if r['condition']==c]
            ax.scatter([i]*len(y),y,s=35,color=['#28649B','#25816E'][i],zorder=2)
        ax.set(title=stage.capitalize(),yscale='log',xlim=(-.3,1.3));ax.set_xticks(range(len(names)),names,fontsize=8)
        ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.15)
    axes[0].set_ylabel('Development comparison time-averaged |h|')
    fig.suptitle('Isolated HRL learning comparisons',fontsize=12)
    fig.get_layout_engine().set(rect=(0,.12,1,.92))
    fig.text(.5,.015,'Each point is a trained policy; lines connect matched training seeds.\nCheckpoint selection and development comparison use separate environment-seed pools. These are not final confirmation tests.',ha='center',fontsize=8)
    for suffix in ['png','svg']:fig.savefig(HERE/('screening_comparisons.'+suffix),dpi=200)
    plt.close(fig)

if __name__=='__main__':main()
