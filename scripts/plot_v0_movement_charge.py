"""Plot every preregistered movement-charge world with explicit right censoring."""
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
    parser.add_argument('--input',type=Path,default=Path('docs/research/results/campaign-018-verification.json'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();targets=[args.output.with_suffix(s) for s in ('.png','.svg','.json')]
    if any(p.exists() for p in targets):raise FileExistsError('Choose a new figure prefix')
    rows=json.loads(args.input.read_text(encoding='utf-8'))['runs']
    index={(r['arm'],r['birth_threshold'],r['movement_cost'],r['seed']):r for r in rows}
    if len(rows)!=80 or set(index)!={(a,t,c,s) for a in ('dispersed','block') for t in (40,160) for c in (0,1) for s in range(1500,1510)}:
        raise ValueError('Incomplete outcome grid')
    for r in rows:
        if r['tick']!=10000 or type(r['right_censored']) is not bool or r['right_censored']!=(r['population']>0) or (r['extinction_tick'] is None)!=r['right_censored']:
            raise ValueError('Invalid censoring status')
        if r['extinction_tick'] is not None and not 1<=r['extinction_tick']<=10000:
            raise ValueError('Invalid extinction time')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none'})
    fig,axes=plt.subplots(2,2,figsize=(12,9),sharex=True)
    fig.subplots_adjust(left=.10,right=.97,top=.83,bottom=.12,wspace=.20,hspace=.28)
    colors={40:'#bb6c32',160:'#277e74'}
    for i,arm in enumerate(('dispersed','block')):
        for j,cost in enumerate((0,1)):
            ax=axes[i,j]
            for y,seed in enumerate(range(1500,1510)):
                for threshold,offset in ((40,-.15),(160,.15)):
                    r=index[arm,threshold,cost,seed]
                    endpoint=10000 if r['right_censored'] else r['extinction_tick']
                    ax.scatter(endpoint,y+offset,marker='>' if r['right_censored'] else 'o',
                               color=colors[threshold],s=35,zorder=3)
            ax.set_yticks(range(10),range(1500,1510));ax.set_ylim(9.7,-.7)
            ax.set_xscale('log');ax.set_xlim(50,13000)
            ax.set_xticks([100,1000,10000],['100','1,000','10,000'])
            ax.axvline(10000,color='#aaaaaa',linestyle=':',linewidth=.8)
            ax.grid(axis='x',alpha=.18);ax.spines[['top','right']].set_visible(False)
            ax.set_title(f'{arm.capitalize()} food / movement charge {cost}',loc='left',fontsize=12)
            if i==1:ax.set_xlabel('First extinction tick, or alive at fixed horizon (log scale)')
            if j==0:ax.set_ylabel('Matched seed')
    fig.suptitle('Does failure require a positive movement charge?',fontsize=17,y=.976)
    fig.text(.5,.934,'Campaign 018: all 80 worlds. Each seed has eight initial treatments; later trajectories may diverge.',ha='center',fontsize=10)
    handles=[Line2D([],[],marker='o',linestyle='',color=colors[t],label=f'Birth threshold {t}') for t in (40,160)]
    handles += [Line2D([],[],marker='o',linestyle='',color='#555555',label='Extinct'),
                Line2D([],[],marker='>',linestyle='',color='#555555',label='Alive at 10,000 (right-censored)')]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,.90),ncol=4,frameon=False)
    fig.text(.5,.055,'Zero charge removes movement energy payment, not occupancy or spatial competition. Every seed and failure is retained.',ha='center',fontsize=9)
    fig.text(.5,.030,'Finite-horizon outcomes do not establish permanent survival or a unique causal mediator.',ha='center',fontsize=9)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for p in targets[:2]:fig.savefig(p,dpi=180)
    plt.close(fig)
    targets[2].write_text(json.dumps(dict(figure='campaign-018-movement-charge-survival-1',rows=rows,
        input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
