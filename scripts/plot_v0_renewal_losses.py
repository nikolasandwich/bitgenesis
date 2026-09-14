"""Plot all sixty retrospective world-level renewal loss comparisons."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=Path('docs/research/results/renewal-stocks-020-summary.json'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();targets=[args.output.with_suffix(ext) for ext in ('.png','.svg','.json')]
    if any(p.exists() for p in targets):raise FileExistsError('Choose a new output prefix')
    source=json.loads(args.input.read_text(encoding='utf-8'))
    rows=[r for r in source['rows'] if r['partition']=='all']
    names=('frequent-small','reference','rare-large')
    expected={('block',t,n,s) for t in (40,160) for n in names for s in range(1700,1710)}
    index={(r['arm'],r['birth_threshold'],r['renewal'],r['seed']):r for r in rows}
    if len(rows)!=60 or set(index)!=expected:raise ValueError('Incomplete full-window cohort')
    if any(r['ticks']!=100 or any(r[k] is None or not 0<=r[k]<=1 for k in ('realized_discard_fraction','expected_loss_fraction')) for r in rows):
        raise ValueError('Invalid full-window fractions')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none'})
    fig,axes=plt.subplots(1,3,figsize=(15,8),sharex=True,sharey=True)
    fig.subplots_adjust(left=.075,right=.97,top=.78,bottom=.21,wspace=.16)
    colors={40:'#bb6c32',160:'#277e74'}
    for ax,name in zip(axes,names):
        for y,seed in enumerate(range(1700,1710)):
            for threshold,offset in ((40,-.17),(160,.17)):
                r=index['block',threshold,name,seed];height=y+offset
                actual=100*r['realized_discard_fraction'];conditional=100*r['expected_loss_fraction']
                ax.plot([actual,conditional],[height,height],color=colors[threshold],alpha=.5,lw=1)
                ax.scatter(actual,height,color=colors[threshold],s=30,zorder=3)
                ax.scatter(conditional,height,edgecolor=colors[threshold],facecolor='none',marker='D',s=33,zorder=4)
        ax.set_title(name.replace('-',' ').title(),loc='left',fontsize=13)
        ax.set_yticks(range(10),range(1700,1710));ax.set_ylim(9.7,-.7)
        ax.tick_params(labelleft=True)
        ax.set_xlim(0,17);ax.set_xticks([0,4,8,12,16],['0%','4%','8%','12%','16%'])
        ax.grid(axis='x',alpha=.18);ax.spines[['top','right']].set_visible(False)
        ax.set_xlabel('Full-window loss fraction (ticks 1–100)')
    axes[0].set_ylabel('Original seed block')
    fig.suptitle('Capacity losses along the observed early trajectories',y=.975,fontsize=16)
    fig.text(.5,.916,'Campaign 020 retrospective replay: all 60 worlds, including any empty-world ticks.',ha='center')
    handles=[Line2D([],[],color=colors[t],lw=2,label=f'Birth threshold {t}') for t in (40,160)]
    handles.extend([Line2D([],[],marker='o',linestyle='',color='#555555',label='Actual discard / sampled arrivals'),
        Line2D([],[],marker='D',linestyle='',markerfacecolor='none',color='#555555',label='Expected cap loss / nominal mean')])
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,.875),ncol=4,frameon=False)
    fig.text(.5,.11,'Segments connect two different-denominator summaries for the same world; they are not confidence intervals.',ha='center',fontsize=9)
    fig.text(.5,.066,'Conditional expectations use observed stocks. Neither quantity isolates a causal effect on survival.',ha='center',fontsize=9)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for p in targets[:2]:fig.savefig(p,dpi=180)
    plt.close(fig)
    targets[2].write_text(json.dumps(dict(figure='renewal-losses-020-1',rows=rows,
        input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
