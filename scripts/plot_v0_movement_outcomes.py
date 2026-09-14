"""Plot all forty per-world movement outcome compositions from verified counts."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=Path("docs/research/results/complete-movement-017.json"))
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();targets=[args.output.with_suffix(x) for x in (".png",".svg",".json")]
    if any(p.exists() for p in targets):raise FileExistsError("Choose a new figure prefix")
    report=json.loads(args.input.read_text(encoding="utf-8"));rows=report["results"]
    indexed={(r["arm"],r["birth_threshold"],r["seed"]):r for r in rows}
    if len(rows)!=40 or set(indexed)!={(a,t,s) for a in ("dispersed","block") for t in (40,160) for s in range(1400,1410)}:
        raise ValueError("Incomplete outcome grid")
    components=("successful_moves","occupied_target_blocks","movement_payment_deaths")
    for r in rows:
        if any(type(r[k]) is not int or r[k]<0 for k in (*components,"all_movement_attempts")) or r["all_movement_attempts"]<=0 or sum(r[k] for k in components)!=r["all_movement_attempts"]:
            raise ValueError("Movement outcomes do not partition attempts")
    colors=("#318472","#d49043","#a65063")
    labels=("Successful displacement","Occupied target","Death on movement payment")
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"svg.fonttype":"none"})
    fig,axes=plt.subplots(2,2,figsize=(12,9),sharex=True)
    fig.subplots_adjust(left=.10,right=.97,bottom=.12,top=.83,hspace=.28,wspace=.22)
    for i,arm in enumerate(("dispersed","block")):
        for j,threshold in enumerate((40,160)):
            ax=axes[i,j]
            for y,seed in enumerate(range(1400,1410)):
                r=indexed[arm,threshold,seed];left=0
                for component,color in zip(components,colors):
                    width=r[component]/r["all_movement_attempts"]*100
                    ax.barh(y,width,left=left,height=.68,color=color,edgecolor="white",linewidth=.3)
                    left+=width
            ax.set_yticks(range(10),range(1400,1410));ax.set_ylim(9.7,-.7);ax.set_xlim(0,100)
            ax.set_title(f"{arm.capitalize()} food / threshold {threshold}",loc="left",fontsize=12)
            ax.set_xticks([0,25,50,75,100]);ax.spines[["top","right"]].set_visible(False)
            if j==0:ax.set_ylabel("Matched seed")
            if i==1:ax.set_xlabel("Share of all movement attempts (%)")
    fig.suptitle("Movement outcomes: all attempts, including lethal payments",fontsize=16,y=.972)
    fig.text(.5,.932,"Campaign 017, ticks 1–100. Every world shown separately; bar widths use each world's own attempt count.",ha="center",fontsize=10)
    fig.legend([Patch(color=c) for c in colors],labels,loc="upper center",bbox_to_anchor=(.5,.899),ncol=3,frameon=False)
    fig.text(.5,.055,"A death on payment occurs before destination selection; it is not an occupied-target block. Basal deaths never attempt movement.",ha="center",fontsize=9)
    fig.text(.5,.030,"These are retrospective process descriptions, not independent action samples or a causal explanation of extinction.",ha="center",fontsize=9)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for path in targets[:2]:fig.savefig(path,dpi=180)
    plt.close(fig)
    targets[2].write_text(json.dumps(dict(figure="campaign-017-movement-composition-1",rows=rows,
        input_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":main()
