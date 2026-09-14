"""Show all campaign-017 outcomes and predeclared early births, preserving censoring."""

import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, NullLocator, StrMethodFormatter


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verification",type=Path,default=Path("docs/research/results/campaign-017-verification.json"))
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    targets=[args.output.with_suffix(s) for s in (".png",".svg",".json")]
    if any(p.exists() for p in targets):
        raise FileExistsError("Choose a new figure prefix")
    report=json.loads(args.verification.read_text(encoding="utf-8"))
    rows=report["runs"];seeds=list(range(1400,1410));arms=("dispersed","block")
    indexed={(r["arm"],r["birth_threshold"],r["seed"]):r for r in rows}
    if len(rows)!=40 or set(indexed)!={(a,t,s) for a in arms for t in (40,160) for s in seeds}:
        raise ValueError("Incomplete verified treatment grid")
    for r in rows:
        dead=r["extinction_tick"] is not None
        if r["tick"]!=10000 or r["right_censored"]!= (not dead) or (r["population"]==0)!=dead:
            raise ValueError("Inconsistent endpoint censoring")
        if dead and not 0<r["extinction_tick"]<=10000:
            raise ValueError("Invalid extinction tick")
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"svg.fonttype":"none"})
    fig,axes=plt.subplots(2,2,figsize=(12,10))
    fig.subplots_adjust(left=.10,right=.97,bottom=.12,top=.81,hspace=.36,wspace=.18)
    colors={40:"#b6693a",160:"#267d68"};offsets={40:-.13,160:.13}
    for col,arm in enumerate(arms):
        for i,seed in enumerate(seeds):
            for row_index,key in ((0,"extinction_tick"),(1,"births_at_100")):
                ax=axes[row_index,col]
                values=[indexed[arm,t,seed][key] for t in (40,160)]
                if row_index==1:
                    ax.plot(values,[i+offsets[t] for t in (40,160)],color="#cbd2cf",lw=1,zorder=1)
                for t,value in zip((40,160),values):
                    censored=row_index==0 and value is None
                    ax.scatter(10000 if censored else value,i+offsets[t],s=43,
                        marker=">" if censored else "o",color=colors[t],zorder=3)
        for row_index in (0,1):
            ax=axes[row_index,col];ax.set_ylim(9.6,-.6);ax.set_yticks(range(10),seeds)
            ax.spines[["top","right"]].set_visible(False);ax.grid(axis="x",color="#e4e8e6")
            if col==0:ax.set_ylabel("Matched seed")
            else:ax.set_yticklabels([])
        ax=axes[0,col];ax.set_xscale("log");ax.set_xlim(90,12500)
        ax.xaxis.set_major_locator(FixedLocator([100,300,1000,3000,10000]))
        ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"));ax.xaxis.set_minor_locator(NullLocator())
        ax.set_title(arm.capitalize()+" food",fontsize=13,pad=12)
        ax.set_xlabel("Extinction tick / observation limit (log scale)")
        axes[1,col].set_xlim(-5,125);axes[1,col].set_xlabel("Births during ticks 1–100")
    legend=[Line2D([],[],color=colors[t],marker="o",linestyle="none",label=f"Threshold {t}") for t in (40,160)]
    legend += [Line2D([],[],color="#424b47",marker="o",linestyle="none",label="Observed extinction (top)"),
               Line2D([],[],color="#424b47",marker=">",linestyle="none",label="Alive at 10,000 (top)")]
    fig.legend(handles=legend,loc="upper center",bbox_to_anchor=(.53,.90),ncol=2,frameon=False)
    fig.suptitle("Reproduction threshold changes early births and finite-horizon survival",fontsize=15,y=.975)
    fig.text(.5,.938,"All 40 worlds shown. Founder/RNG states match by seed; food maps match within each layout.",ha="center",fontsize=10)
    fig.text(.5,.060,"Triangles are right-censored observations, not extinction times. Bottom lines pair seeds; they do not show time trajectories.",ha="center",fontsize=9)
    fig.text(.5,.036,"Twenty high-threshold survivors do not prove permanent stability or identify a unique causal mechanism.",ha="center",fontsize=9)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for path in targets[:2]:fig.savefig(path,dpi=180)
    plt.close(fig)
    targets[2].write_text(json.dumps(dict(figure="campaign-017-threshold-1",outcome_points=rows,
        verification_sha256=hashlib.sha256(args.verification.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope="All forty outcomes and early birth counts. No trajectory interpolation or extinction imputation for censored survivors."),indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
