"""Display every mutation-assay pair, including both counterexample directions."""
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
    parser.add_argument('--metrics',type=Path,default=Path('docs/research/results/campaign-022-verification.json'))
    parser.add_argument('--histories',type=Path,default=Path('docs/research/results/campaign-022-histories.json'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();targets=[args.output.with_suffix(s) for s in ('.png','.svg','.json')]
    if any(p.exists() for p in targets):raise FileExistsError('Choose a new figure prefix')
    metrics=json.loads(args.metrics.read_text(encoding='utf-8'));history=json.loads(args.histories.read_text(encoding='utf-8'))
    if history['metric_verification_sha256']!=hashlib.sha256(args.metrics.read_bytes()).hexdigest():raise ValueError('Verification reports differ')
    rows=metrics['runs'];grid={(s,m) for s in range(1900,1920) for m in (0,100)}
    if len(rows)!=40 or {(r['seed'],r['mutation_probability']) for r in rows}!=grid:raise ValueError('Incomplete cohort')
    index={(r['seed'],r['mutation_probability']):r for r in rows}
    pairs={p['seed']:p for p in history['pairs']}
    if len(history['pairs'])!=20 or set(pairs)!=set(range(1900,1920)):raise ValueError('Incomplete pair records')
    for seed in pairs:
        a,b=(index[seed,m]['population']>0 for m in (0,100))
        status='both_alive' if a and b else 'mutation_only' if b else 'no_mutation_only' if a else 'both_extinct'
        if pairs[seed]['status']!=status:raise ValueError('Pair classification differs')
    counts={name:sum(p['status']==name for p in pairs.values()) for name in ('both_alive','mutation_only','no_mutation_only','both_extinct')}
    net=counts['mutation_only']-counts['no_mutation_only']
    if counts!=history['counts'] or net!=history['signed_discordance']:raise ValueError('Pair totals differ')
    for r in rows:
        t=r['extinction_tick']
        if r['tick']!=10000 or type(r['right_censored']) is not bool or r['right_censored']!=(t is None) or (r['population']>0)!=(t is None) or (t is not None and (type(t) is not int or not 1<=t<=10000)):raise ValueError('Invalid censoring')
    fig,ax=plt.subplots(figsize=(12,12));fig.subplots_adjust(left=.12,right=.73,top=.80,bottom=.14)
    colors={0:'#bb6c32',100:'#277e74'}
    labels={'both_alive':'Both alive','mutation_only':'Mutation only','no_mutation_only':'No mutation only','both_extinct':'Both extinct'}
    for y,seed in enumerate(range(1900,1920)):
        if y%2==0:ax.axhspan(y-.5,y+.5,color='#f3f4ef',zorder=0)
        for mutation,offset in ((0,-.15),(100,.15)):
            r=index[seed,mutation];x=r['extinction_tick'] if r['extinction_tick'] is not None else 10000
            ax.scatter(x,y+offset,color=colors[mutation],marker='>' if r['right_censored'] else 'o',s=38,zorder=3)
        ax.text(1.03,y,labels[pairs[seed]['status']],transform=ax.get_yaxis_transform(),va='center',fontsize=10)
    ax.set_yticks(range(20),range(1900,1920));ax.set_ylim(19.6,-.6)
    ax.set_xscale('log');ax.set_xlim(min([50]+[.8*r['extinction_tick'] for r in rows if r['extinction_tick'] is not None]),13000)
    ax.set_xticks([100,1000,10000],['100','1,000','10,000']);ax.grid(axis='x',alpha=.2)
    ax.axvline(10000,color='#999999',linestyle=':',linewidth=.8)
    ax.spines[['top','right']].set_visible(False)
    ax.set_xlabel('Extinction tick / observation horizon (log scale)');ax.set_ylabel('Matched seed')
    fig.suptitle('Mutation changes outcomes in both directions',fontsize=21,y=.965)
    fig.text(.5,.925,'Campaign 022: 40 worlds, 20 paired seeds. Every founder starts at genome 250.',ha='center',fontsize=11)
    handles=[Line2D([],[],marker='o',linestyle='',color=colors[m],label='No mutation' if m==0 else 'Mutation 100/1000') for m in (0,100)]
    handles += [Line2D([],[],marker='o',linestyle='',color='#555555',label='Extinct'),Line2D([],[],marker='>',linestyle='',color='#555555',label='Alive at 10,000')]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,.899),ncol=4,frameon=False)
    fig.text(.5,.843,f"Both alive: {counts['both_alive']} | Mutation only: {counts['mutation_only']} | No mutation only: {counts['no_mutation_only']} | Both extinct: {counts['both_extinct']}",ha='center',fontsize=11)
    fig.text(.5,.072,f"Paired net survival advantage: {net:+d}. Right-censored survival does not mean permanent persistence.",ha='center',fontsize=10)
    fig.text(.5,.039,'Finite-cohort mutation treatment effect; not a significance test or proof of adaptive improvement.',ha='center',fontsize=10)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for p in targets[:2]:fig.savefig(p,dpi=180)
    plt.close(fig)
    targets[2].write_text(json.dumps(dict(rows=rows,pairs=history['pairs'],metric_report_sha256=hashlib.sha256(args.metrics.read_bytes()).hexdigest(),history_report_sha256=hashlib.sha256(args.histories.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
