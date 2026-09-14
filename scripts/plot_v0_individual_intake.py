"""Show founder/descendant intake and zero-intake founders for all 40 worlds."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path('docs/research/results/individual-intake-017.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    targets = [args.output.with_suffix(s) for s in ('.png', '.svg', '.json')]
    if any(p.exists() for p in targets):
        raise FileExistsError('Choose a new figure prefix')
    rows = json.loads(args.input.read_text(encoding='utf-8'))['results']
    index = {(r['arm'], r['birth_threshold'], r['seed']):r for r in rows}
    grid = {(a,t,s) for a in ('dispersed','block') for t in (40,160) for s in range(1400,1410)}
    if len(rows) != 40 or set(index) != grid:
        raise ValueError('Incomplete world grid')
    for r in rows:
        if r['founders']['individuals'] != 80:
            raise ValueError('Founder denominator differs')
        for group in ('founders','descendants'):
            c = r[group]
            if any(type(c[k]) is not int or c[k] < 0 for k in ('individuals','food_eaten','zero_intake_individuals')):
                raise ValueError('Invalid cohort counts')
            if c['zero_intake_individuals'] > c['individuals']:
                raise ValueError('Zero-intake count exceeds cohort')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none'})
    fig, axes = plt.subplots(4,2,figsize=(12,14),gridspec_kw={'width_ratios':[2,1]})
    fig.subplots_adjust(left=.13,right=.96,bottom=.09,top=.88,hspace=.48,wspace=.22)
    colors = ('#318472','#d49043')
    for i,(arm,threshold) in enumerate((a,t) for a in ('dispersed','block') for t in (40,160)):
        left,right = axes[i]
        for y,seed in enumerate(range(1400,1410)):
            r = index[arm,threshold,seed]
            founder,descendant = r['founders']['food_eaten'],r['descendants']['food_eaten']
            left.barh(y,founder,color=colors[0],height=.68)
            left.barh(y,descendant,left=founder,color=colors[1],height=.68)
            zero = r['founders']['zero_intake_individuals']
            right.barh(y,zero,color='#a65063',height=.68)
            right.text(zero+.8,y,str(zero),va='center',fontsize=8)
        for ax in (left,right):
            ax.set_ylim(9.7,-.7)
            ax.spines[['top','right']].set_visible(False)
        left.set_yticks(range(10),range(1400,1410));right.set_yticks([])
        left.set_xlim(0,6500);right.set_xlim(0,80)
        left.set_xticks([0,2000,4000,6000]);right.set_xticks([0,20,40,60,80])
        left.set_title(f'{arm.capitalize()} food / threshold {threshold}',loc='left',fontsize=12)
        right.set_title('Zero-intake founders / 80',loc='left',fontsize=11)
        left.set_ylabel('Matched seed')
        if i == 3:
            left.set_xlabel('Food eaten, ticks 1–100 (energy units)')
            right.set_xlabel('Number of founders')
    fig.suptitle('More total food intake need not reach more founders',fontsize=17,y=.976)
    fig.text(.5,.948,'Campaign 017: all 40 historical worlds, with fixed cohorts of 80 founders.',ha='center',fontsize=11)
    fig.legend([Patch(color=c) for c in colors],['Founder intake','Intake by later-born individuals'],
               loc='upper center',bbox_to_anchor=(.5,.927),ncol=2,frameon=False)
    fig.text(.5,.042,'Bars show direct feeding, excluding inherited birth energy. Lifespans and opportunities differ across individuals.',ha='center',fontsize=9)
    fig.text(.5,.023,'Retrospective accounting; no new independent seeds or causal attribution of extinction.',ha='center',fontsize=9)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for path in targets[:2]:
        fig.savefig(path,dpi=160)
    plt.close(fig)
    targets[2].write_text(json.dumps(dict(figure='campaign-017-individual-intake-1',rows=rows,
        input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()
