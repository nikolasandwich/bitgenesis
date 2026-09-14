"""Plot post hoc paired survival differences at every campaign-021 horizon."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analyze_v0_capacity_horizons import analyze


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('docs/research/results/capacity-horizons-021.json'))
    parser.add_argument('--metrics',type=Path,default=Path('docs/research/results/campaign-021-verification.json'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    targets=[args.output.with_suffix(s) for s in ('.png','.svg','.json')]
    if any(p.exists() for p in targets):raise FileExistsError('Choose a new figure prefix')
    report=json.loads(args.input.read_text(encoding='utf-8'))
    if report['metric_report_sha256']!=hashlib.sha256(args.metrics.read_bytes()).hexdigest():
        raise ValueError('Metric report changed')
    expected=analyze(json.loads(args.metrics.read_text(encoding='utf-8')))
    if report['groups']!=expected['groups']:raise ValueError('Horizon report differs from complete cohort')
    index={(g['birth_threshold'],g['renewal']):g for g in report['groups']}
    fig,axes=plt.subplots(2,3,figsize=(15,9),sharex=True,sharey=True)
    fig.subplots_adjust(top=.80,bottom=.17,hspace=.32,wspace=.16)
    for i,t in enumerate((40,160)):
        for j,n in enumerate(('frequent-small','reference','rare-large')):
            ax=axes[i,j];g=index[t,n]
            for segment in g['intervals']:
                lo=max(1,segment['start_tick']);hi=min(10000,segment['end_tick']+1)
                y=segment['signed_discordance']
                if hi>lo:
                    ax.fill_between([lo,hi],0,y,color='#277e74' if y>0 else '#bb6c32',alpha=.18)
            edges=[max(1,s['start_tick']) for s in g['intervals']]+[10001]
            ax.stairs([s['signed_discordance'] for s in g['intervals']],edges,baseline=None,color='#354c46',linewidth=1.4)
            final=g['intervals'][-1]['signed_discordance']
            ax.scatter([10000],[final],color='#354c46',s=24,zorder=4)
            ax.annotate(f'{final:+d}',(10000,final),xytext=(5,5),textcoords='offset points',fontsize=10)
            ax.axhline(0,color='#888888',linewidth=.6)
            ax.axvline(10000,color='#999999',linestyle=':',linewidth=.8)
            ax.set_xscale('log');ax.set_xlim(1,18000);ax.set_ylim(-5.5,3)
            ax.set_xticks([1,10,100,1000,10000],['1','10','100','1,000','10,000'])
            ax.set_yticks(range(-5,4));ax.grid(alpha=.15)
            ax.spines[['top','right']].set_visible(False)
            ax.set_title(f"{n.replace('-',' ').title()} / threshold {t}",fontsize=12,loc='left')
            ax.tick_params(labelbottom=True)
            if j==0:ax.set_ylabel('Paired survival difference (96 minus 24)')
            if i==1:ax.set_xlabel('Observation horizon: post-step state (log scale)')
    fig.suptitle('Changing the observation horizon can change the comparison',fontsize=20,y=.96)
    fig.text(.5,.885,'All 120 worlds / 10 matched seeds per panel. Positive favors capacity 96; negative favors capacity 24.',ha='center',fontsize=11)
    fig.text(.5,.085,'Post hoc descriptive analysis. The registered 10,000-step endpoint remains unchanged (marked dots).',ha='center',fontsize=11)
    fig.text(.5,.045,'Neighboring horizons are correlated views, not independent replicates. Shaded area is not a confidence interval.',ha='center',fontsize=10)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(targets[0],dpi=180);fig.savefig(targets[1]);plt.close(fig)
    targets[2].write_text(json.dumps(dict(groups=report['groups'],input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),metric_report_sha256=report['metric_report_sha256'],script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
