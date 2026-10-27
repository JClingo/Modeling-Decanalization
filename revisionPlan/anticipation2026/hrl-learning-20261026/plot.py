"""Standalone scientific figures; use the temporary plotting dependencies."""
from pathlib import Path
import argparse,hashlib,json,os,sys,tempfile,time
HERE=Path(__file__).resolve().parent
sys.path.insert(0,'/private/tmp/hrl-study-plot-packages')
os.environ.setdefault('MPLCONFIGDIR',str(Path(tempfile.gettempdir())/'hrl-study-mpl-cache'))
os.environ['XDG_CACHE_HOME']=str(Path(tempfile.gettempdir())/'hrl-study-xdg-cache')
Path(os.environ['XDG_CACHE_HOME']).mkdir(parents=True,exist_ok=True)
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'svg.fonttype':'none'})

COLORS=['#2874A6','#6F42A6','#20856B','#CF6422']
LABELS=['100 s; reset on update','300 s; reset on update','300 s; persistent','300 s; persistent + learning']

def read(p):return json.loads(Path(p).read_text())
def save(fig,name):
    fig.savefig(HERE/(name+'.png'),dpi=200)
    fig.savefig(HERE/(name+'.svg'))
    plt.close(fig)

def curves(interim=False):
    protocol=read(HERE/'comparison_protocol.json');root=Path(protocol['raw_root'])
    fig,ax=plt.subplots(figsize=(8.2,4.8),layout='constrained')
    for name,color,label in zip(protocol['conditions'],COLORS,LABELS):
        added=False
        for seed in protocol['training_seeds']:
            path=root/f'canalization-{name}-{seed}/selection.json'
            if not path.exists():continue
            history=read(path)['history']
            if not history:continue
            x=[h['checkpoint']['steps']/1e6 for h in history]
            raw=np.array([h['mean_time_mae'] for h in history])
            ax.plot(x,np.minimum.accumulate(raw),color=color,lw=1.6,alpha=.8,
                    marker='.',ms=5,label=label if not added else None)
            added=True
    reference=root/'selected-reference-continuous-41001/summary.json'
    if reference.exists():ax.axhline(read(reference)['mean_time_mae'],color='#555555',ls='--',lw=1,label='Preserved selected policy')
    ax.set(xlabel='Collected training transitions (millions)',ylabel='Best selection time-averaged |h| (log scale)',yscale='log')
    fig.suptitle('Interim checkpoint selection — training ongoing' if interim else 'Checkpoint selection across three training seeds',fontsize=12)
    ax.grid(axis='y',alpha=.18);ax.spines[['top','right']].set_visible(False)
    fig.legend(*ax.get_legend_handles_labels(),fontsize=8,loc='upper center',bbox_to_anchor=(.5,.93),ncol=2,frameon=False)
    fig.get_layout_engine().set(rect=(0,.10,1,.70))
    fig.text(.5,.015,'Eight selection trials per checkpoint. Lines show independently trained policies. '
             +('Independent evaluation is pending.' if interim else 'These curves are separate from the independent comparison.'),ha='center',fontsize=7)
    save(fig,'interim_selection' if interim else 'selection_curves')

def final():
    d=read(HERE/'results.json');assert d['complete'];conditions=d['protocol']['conditions']
    fig,axes=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
    for i,(condition,color,label) in enumerate(zip(conditions,COLORS,LABELS)):
        rows=[r for r in d['per_policy'] if r['condition']==condition]
        assert len(rows)==3
        x=i+np.array([-.13,0,.13]);y=[r['time_mae'] for r in rows]
        axes[0].scatter(x,y,color=color,s=40,zorder=3)
        axes[0].scatter(i,np.mean(y),color='black',marker='_',s=170,zorder=4)
        durations=[r['training_history']['last_100_observed_episodes_mean_duration_lower_bound'] for r in rows]
        axes[1].scatter(x,durations,color=color,s=40,zorder=3)
        axes[1].scatter(i,np.mean(durations),color='black',marker='_',s=170,zorder=4)
    axes[0].axhline(d['selected_reference_time_mae'],ls='--',lw=1,color='#555555',label='Preserved selected policy')
    axes[0].set(ylabel='Independent time-averaged |h| (log scale)',yscale='log',title='Regulation across trained policies')
    axes[0].legend(fontsize=7,frameon=False)
    axes[1].set(ylabel='Sampled episode duration (s; lower bound)',title='Training exposure to persistent history',ylim=(0,310))
    ticks=['100 s\nreset','300 s\nreset','300 s\npersistent','300 s\npersistent\n+ learning']
    for ax in axes:
        ax.set_xticks(range(4),ticks,fontsize=8);ax.grid(axis='y',alpha=.18)
        ax.spines[['top','right']].set_visible(False)
    fig.get_layout_engine().set(rect=(0,.12,1,.88))
    fig.text(.5,.015,'Each dot is one training seed; black marks are condition means. Performance uses 16 independent comparison trials per policy.\n'
             'Duration uses the last 100 observed completed training episodes. Three training seeds per condition; exploratory screen.',ha='center',fontsize=8)
    save(fig,'performance_and_exposure');curves()
    meta=dict(matplotlib=matplotlib.__version__,numpy=np.__version__,plot_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              results_sha256=hashlib.sha256((HERE/'results.json').read_bytes()).hexdigest())
    (HERE/'figure_manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
    print('FIGURES_COMPLETE',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--interim',action='store_true');parser.add_argument('--wait',action='store_true')
    args=parser.parse_args()
    if args.wait:
        deadline=time.monotonic()+24*3600
        while not (HERE/'results.json').exists():
            status=HERE/'postprocessing_status.json'
            if status.exists() and read(status).get('status')=='failed':raise RuntimeError(read(status)['error'])
            if time.monotonic()>deadline:raise TimeoutError('Waiting for study results')
            time.sleep(10)
    curves(True) if args.interim else final()
