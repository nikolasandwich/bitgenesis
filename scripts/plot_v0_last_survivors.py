"""Plot all seven outcome-selected terminal individuals without extending their windows."""
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
    parser.add_argument('--input',type=Path,default=Path('docs/research/results/last-survivors-019.json'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();targets=[args.output.with_suffix(s) for s in ('.png','.svg','.json')]
    if any(p.exists() for p in targets):raise FileExistsError('Choose a new figure prefix')
    source=json.loads(args.input.read_text(encoding='utf-8'));traces=source['traces']
    if len(traces)!=7 or len(source['excluded_worlds'])!=33:raise ValueError('Expected complete selected/excluded cohort')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none'})
    fig,axes=plt.subplots(4,2,figsize=(12,12),sharex=True,sharey=True)
    fig.subplots_adjust(left=.08,right=.97,top=.85,bottom=.10,hspace=.46,wspace=.21)
    for ax,trace in zip(axes.flat,traces):
        rows=trace['timeline'];end=trace['endpoint']
        if len(rows)!=20 or [r['tick'] for r in rows]!=list(range(end-19,end+1)):raise ValueError('Incomplete trace window')
        x=[r['tick']-end for r in rows];y=[r['energy_after'] for r in rows]
        ax.plot([-20,*x],[rows[0]['energy_before'],*y],color='#286957',linewidth=1.8)
        for xx,row in zip(x,rows):
            if row['eaten']:
                ax.scatter(xx,row['energy_after'],marker='o',s=40,color='#b76025',zorder=4)
                ax.annotate(f"+{row['eaten']}",(xx,row['energy_after']),xytext=(3,7),textcoords='offset points',fontsize=9)
            if row['free_neighbor_food']:ax.scatter(xx,-1.5,marker='s',s=9,color='#7e9d8c')
        ax.scatter(0,0,marker='x',s=45,color='#a13e3e',zorder=5)
        ax.set_title(f"Seed {trace['seed']} / birth charge {trace['birth_cost']} / ID {trace['id']}",loc='left',fontsize=10)
        ax.set_xlim(-20.7,.7);ax.set_ylim(-3,23);ax.set_xticks([-20,-15,-10,-5,0]);ax.set_yticks([0,5,10,15,20])
        ax.grid(alpha=.15);ax.spines[['top','right']].set_visible(False)
        ax.text(.02,.91,f"Start {trace['initial_energy']} + intake {trace['total_eaten']} = basal 20",transform=ax.transAxes,fontsize=9)
    axes.flat[-1].axis('off')
    axes.flat[-1].text(0,.9,'Reading this figure',fontsize=12,weight='bold',transform=axes.flat[-1].transAxes)
    axes.flat[-1].text(0,.72,'Energy is shown after each action.\nAt -20: energy before the first recorded action.\nAt 0: basal death, before movement or feeding.\nSquares: an empty food-containing neighbor\nwas present before the actor paid basal cost.\nNearby food is not actual food intake.',va='top',linespacing=1.6,transform=axes.flat[-1].transAxes)
    fig.suptitle('Seven final survivors: nearby food did not guarantee intake',fontsize=17,y=.98)
    fig.text(.5,.944,'Campaign 019 / post hoc selection: all seven extinctions; 33 censored worlds excluded.',ha='center',fontsize=10)
    handles=[Line2D([],[],color='#286957',label='Individual energy'),Line2D([],[],marker='o',linestyle='',color='#b76025',label='Positive intake'),Line2D([],[],marker='x',linestyle='',color='#a13e3e',label='Death'),Line2D([],[],marker='s',linestyle='',color='#7e9d8c',label='Empty neighbor with food')]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,.915),ncol=4,frameon=False)
    fig.supxlabel("Tick relative to this individual's extinction (different absolute ages)",y=.06)
    fig.supylabel('Energy',x=.018)
    fig.text(.5,.025,'No birth or movement payment in these individual windows. This is not a causal rescue or sensory-advantage test.',ha='center',fontsize=9)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for p in targets[:2]:fig.savefig(p,dpi=160)
    plt.close(fig)
    targets[2].write_text(json.dumps(dict(traces=traces,excluded_worlds=source['excluded_worlds'],input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
