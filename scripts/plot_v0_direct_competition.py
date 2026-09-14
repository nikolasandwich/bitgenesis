"""Show all competition sources and repeated allocation contrasts after full verification."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
if __package__:
    from .verify_v0_direct_competition_histories import source_contrasts
else:
    from verify_v0_direct_competition_histories import source_contrasts


def validated_data(gate,manifest):
    samples={s['source_seed']:s['selected'] for s in manifest['samples'] if s['available']}
    if gate['available_sources']!=len(samples) or gate['metric_rows_checked']!=len(samples)*10*10001:
        raise ValueError('Incomplete verification scope')
    runs=[dict(source_seed=r['source_seed'],replicate=r['replicate'],swap=r['swap'],
               groups={'sampled':{'population':r['sampled_population']},'ancestor':{'population':r['ancestor_population']}})
          for r in gate['runs']]
    comparison=source_contrasts(runs,set(samples))
    if any(gate[k]!=v for k,v in comparison.items()):
        raise ValueError('Saved source contrasts differ from verified counts')
    return samples,comparison


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verification',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    targets=[args.output.with_suffix(ext) for ext in ('.png','.svg','.json')]
    if any(p.exists() for p in targets):raise FileExistsError('Choose a new output prefix')
    gate=json.loads(args.verification.read_text(encoding='utf-8'))
    mp=root/'docs/research/results/campaign-023-samples.json'
    if gate['manifest_sha256']!=sha(mp):raise ValueError('Frozen sample linkage differs')
    samples,comparison=validated_data(gate,json.loads(mp.read_text(encoding='utf-8')))
    if not samples:raise ValueError('No available source to plot')
    sources=sorted(samples)
    means={s['source_seed']:float(Fraction(s['contrast'])) for s in comparison['sources']}
    fig,(ax,counts_ax)=plt.subplots(1,2,figsize=(13,11),sharey=True,gridspec_kw={'width_ratios':[1.35,1]})
    fig.subplots_adjust(left=.21,right=.97,top=.81,bottom=.16,wspace=.18)
    statuses=('both_present','sampled_only','ancestor_only','both_extinct')
    colors=('#95b4a5','#277e74','#bb6c32','#d7d7d2')
    status_counts=[]
    for y,source in enumerate(sources):
        if y%2==0:ax.axhspan(y-.5,y+.5,color='#f3f4ef',zorder=0)
        pairs=[p for p in comparison['pairs'] if p['source_seed']==source]
        for p in pairs:
            ax.scatter(float(Fraction(p['contrast'])),y+(p['replicate']-2)*.1,s=18,color='#8da5b3',zorder=2)
        ax.scatter(means[source],y,s=48,marker='D',color='#223e4d',zorder=3)
        counts=Counter(r['status'] for r in comparison['runs'] if r['source_seed']==source)
        status_counts.append(dict(source_seed=source,counts={k:counts[k] for k in statuses}))
        left=0
        for status,color in zip(statuses,colors):
            value=counts[status]
            counts_ax.barh(y,value,left=left,color=color,height=.66)
            if value:counts_ax.text(left+value/2,y,str(value),ha='center',va='center',fontsize=9,color='white' if status in ('sampled_only','ancestor_only') else '#263b34')
            left+=value
    ax.axvline(0,color='#999999',linewidth=.8,zorder=1)
    limit=max([.25]+[abs(float(Fraction(p['contrast']))) for p in comparison['pairs']])*1.15
    ax.set_xlim(-limit,limit)
    ax.set_yticks(range(len(sources)),[f"{s}   {samples[s]['genome']} / {samples[s]['founder_genome']}" for s in sources])
    ax.set_ylim(len(sources)-.5,-.5)
    ax.set_xlabel('Signed terminal abundance per 40 founders')
    ax.set_ylabel('Source seed   sampled / ancestor trait')
    ax.grid(axis='x',alpha=.15)
    counts_ax.set_xlim(0,10);counts_ax.set_xticks([0,5,10])
    counts_ax.set_xlabel('Allocation runs at tick 10,000 (out of ten)')
    for panel in (ax,counts_ax):panel.spines[['top','right']].set_visible(False)
    fig.suptitle('Direct competition: preserve repeats and extinction outcomes',fontsize=18,y=.97)
    fig.text(.5,.926,f"Campaign 024 | {len(sources)} sources | five paired allocation swaps per source",ha='center',fontsize=11)
    fig.text(.5,.892,f"Exact mean source contrast: {comparison['mean_source_contrast']} | Positive / zero / negative: "
             f"{comparison['positive_sources']} / {comparison['zero_sources']} / {comparison['negative_sources']}",ha='center',fontsize=11)
    handles=[Line2D([],[],marker='o',linestyle='',color='#8da5b3',label='Swap-pair mean'),Line2D([],[],marker='D',linestyle='',color='#223e4d',label='Source mean')]
    handles += [Line2D([],[],marker='s',linestyle='',color=c,label=s.replace('_',' ').capitalize()) for s,c in zip(statuses,colors)]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,.862),ncol=3,frameon=False,fontsize=9)
    fig.text(.5,.09,'D = (sampled descendants - ancestor descendants) / 40. Average swaps, repeats, then sources.',ha='center',fontsize=10)
    fig.text(.5,.055,'Dots are repeated evaluations, not independent evolved samples. Bars retain both-extinct outcomes.',ha='center',fontsize=10)
    fig.text(.5,.025,'Finite-horizon opponent-specific abundance; not the earlier monoculture survival endpoint or a selection claim.',ha='center',fontsize=9)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for p in targets[:2]:fig.savefig(p,dpi=180)
    plt.close(fig)
    report=dict(**comparison,samples=samples,status_counts=status_counts,verification_sha256=sha(args.verification),manifest_sha256=sha(mp),script_sha256=sha(Path(__file__)))
    targets[2].write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
