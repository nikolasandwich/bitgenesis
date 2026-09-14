"""Plot every preregistered buffer-capacity world with explicit right censoring."""
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
    parser.add_argument('--input',type=Path,default=Path('docs/research/results/campaign-021-verification.json'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();targets=[args.output.with_suffix(s) for s in ('.png','.svg','.json')]
    if any(p.exists() for p in targets):raise FileExistsError('Choose a new figure prefix')
    rows=json.loads(args.input.read_text(encoding='utf-8'))['runs']
    index={(r['arm'],r['birth_threshold'],r['renewal'],r['food_capacity'],r['seed']):r for r in rows}
    if len(rows)!=120 or set(index)!={(a,t,c,b,s) for a in ('block',) for t in (40,160) for c in ("frequent-small","reference","rare-large") for b in (24,96) for s in range(1800,1810)}:
        raise ValueError('Incomplete outcome grid')
    for r in rows:
        if r['tick']!=10000 or type(r['right_censored']) is not bool or r['right_censored']!=(r['population']>0) or (r['extinction_tick'] is None)!=r['right_censored']:
            raise ValueError('Invalid censoring status')
        if r['extinction_tick'] is not None and not 1<=r['extinction_tick']<=10000:
            raise ValueError('Invalid extinction time')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none'})
    fig,axes=plt.subplots(2,3,figsize=(15,12),sharex=True)
    fig.subplots_adjust(left=.10,right=.97,top=.83,bottom=.14,wspace=.20,hspace=.38)
    colors={24:'#bb6c32',96:'#277e74'}
    for i,threshold in enumerate((40,160)):
        for j,renewal in enumerate(("frequent-small","reference","rare-large")):
            ax=axes[i,j]
            for y,seed in enumerate(range(1800,1810)):
                for capacity,offset in ((24,-.15),(96,.15)):
                    r=index['block',threshold,renewal,capacity,seed]
                    endpoint=10000 if r['right_censored'] else r['extinction_tick']
                    ax.scatter(endpoint,y+offset,marker='>' if r['right_censored'] else 'o',
                               color=colors[capacity],s=35,zorder=3)
            ax.set_yticks(range(10),range(1800,1810));ax.set_ylim(9.7,-.7)
            ax.set_xscale('log');ax.set_xlim(min([50]+[.8*r['extinction_tick'] for r in rows if r['extinction_tick'] is not None]),13000)
            ax.set_xticks([100,1000,10000],['100','1,000','10,000'])
            ax.axvline(10000,color='#aaaaaa',linestyle=':',linewidth=.8)
            ax.grid(axis='x',alpha=.18);ax.spines[['top','right']].set_visible(False)
            ax.set_title(f"{renewal.replace('-', ' ').title()} / threshold {threshold}",loc='left',fontsize=12)
            ax.tick_params(labelbottom=True)
            if i==1:ax.set_xlabel('Extinction tick / horizon (log scale)')
            if j==0:ax.set_ylabel('Matched seed')
    fig.suptitle('Does a larger environmental buffer change persistence?',fontsize=16,y=.98)
    fig.text(.5,.94,'Campaign 021: all 120 worlds. Initial food is identical; capacity is 24 or 96.',ha='center',fontsize=10)
    handles=[Line2D([],[],marker='o',linestyle='',color=colors[t],label=f'Food capacity {t}') for t in (24,96)]
    handles += [Line2D([],[],marker='o',linestyle='',color='#555555',label='Extinct'),
                Line2D([],[],marker='>',linestyle='',color='#555555',label='Alive at 10,000 (right-censored)')]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,.915),ncol=4,frameon=False)
    fig.text(.5,.075,'More storage changes resource retention and later trajectories; it does not isolate cap-loss mediation.',ha='center',fontsize=9)
    fig.text(.5,.042,'Finite-horizon outcomes do not establish permanent survival or a unique causal mediator.',ha='center',fontsize=9)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for p in targets[:2]:fig.savefig(p,dpi=180)
    plt.close(fig)
    targets[2].write_text(json.dumps(dict(figure='campaign-021-buffer-capacity-survival-1',rows=rows,
        input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
