"""Scientific figures for the matched 100-second history comparison."""
from pathlib import Path
import hashlib,json,os,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,'/private/tmp/hrl-study-plot-packages')
os.environ.setdefault('MPLCONFIGDIR','/private/tmp/hrl-study-mpl-cache')
os.environ['XDG_CACHE_HOME']='/private/tmp/hrl-study-xdg-cache'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    data=json.loads((HERE/'results.json').read_text());assert data['complete']
    conditions=data['protocol']['conditions'];seeds=data['protocol']['training_seeds']
    fig,axes=plt.subplots(1,2,figsize=(8,4.7),layout='constrained')
    colors=['#28649B','#25816E']
    for seed in seeds:
        rows=[next(r for r in data['per_policy'] if r['condition']==c and r['training_seed']==seed) for c in conditions]
        axes[0].plot([0,1],[r['time_mae'] for r in rows],color='#aaaaaa',lw=1,zorder=1)
        axes[1].plot([0,1],[r['training_history']['last_100_observed_episodes_mean_duration_lower_bound'] for r in rows],color='#aaaaaa',lw=1,zorder=1)
    for i,c in enumerate(conditions):
        rows=[r for r in data['per_policy'] if r['condition']==c]
        axes[0].scatter([i]*len(rows),[r['time_mae'] for r in rows],color=colors[i],s=40,zorder=2)
        axes[1].scatter([i]*len(rows),[r['training_history']['last_100_observed_episodes_mean_duration_lower_bound'] for r in rows],color=colors[i],s=40,zorder=2)
    axes[0].set(ylabel='Independent time-averaged |h|',title='Homeostatic regulation',yscale='log')
    axes[1].set(ylabel='Observed episode duration (s; lower bound)',title='Training history exposure',ylim=(0,105))
    for ax in axes:
        ax.set_xticks([0,1],['Reset on updates','Preserve on updates'],fontsize=8);ax.set_xlim(-.25,1.25)
        ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.15)
    fig.suptitle('100-second training worlds; original learning settings',fontsize=12)
    fig.get_layout_engine().set(rect=(0,.13,1,.93))
    fig.text(.5,.02,'Each point is a trained policy; lines connect matched initialization seeds.\n16 comparison trials per policy. Duration: last 100 observed completed episodes, sampled every 100 decisions.',ha='center',fontsize=7)
    for suffix in ['png','svg']:fig.savefig(HERE/('comparison.'+suffix),dpi=200)
    plt.close(fig)
    (HERE/'figure_manifest.json').write_text(json.dumps(dict(matplotlib=matplotlib.__version__,
        plot_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),results_sha256=hashlib.sha256((HERE/'results.json').read_bytes()).hexdigest()),indent=2)+'\n')

if __name__=='__main__':main()
