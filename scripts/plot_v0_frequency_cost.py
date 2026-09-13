"""Plot every verified campaign-014 endpoint without survivor-only filtering."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=Path("docs/research/results/campaign-014-verification.json"))
    parser.add_argument("--output",type=Path,default=Path("docs/research/figures/campaign-014-outcomes"))
    args=parser.parse_args()
    targets=[args.output.with_suffix(s) for s in (".png",".svg",".json")]
    if any(p.exists() for p in targets):
        raise FileExistsError("Choose a new figure prefix")
    report=json.loads(args.input.read_text(encoding="utf-8"))
    rows=report["runs"]
    indexed={(r["movement_cost"],r["initial_b"],r["treatment"],r["seed"]):r for r in rows}
    expected={(c,b,t,s) for c in (1,2,3,4) for b in (8,72) for t in ("competition","neutral") for s in range(1200,1210)}
    if len(rows)!=160 or set(indexed)!=expected or any(r["tick"]!=3000 for r in rows):
        raise ValueError("Expected complete endpoint grid")
    outcomes={}
    for key,r in indexed.items():
        if r["a"]+r["b"]!=r["population"] or min(r["a"],r["b"])<0:
            raise ValueError("Invalid group counts")
        outcomes[key]="extinct" if not r["population"] else "a_only" if not r["b"] else "b_only" if not r["a"] else "both_present"
    for group in report["groups"]:
        counts=Counter(outcome for (c,b,t,s),outcome in outcomes.items()
            if (c,b,t)==(group["movement_cost"],group["initial_b"],group["treatment"]))
        if any(counts[k]!=group[k] for k in ("a_only","b_only","both_present","extinct")):
            raise ValueError("Endpoint grid differs from verified group totals")
    colors={"a_only":"#b96842","b_only":"#2b8067","both_present":"#d7b957","extinct":"#3e4549"}
    symbols={"a_only":"A","b_only":"B","both_present":"AB","extinct":"X"}
    labels={"a_only":"A only","b_only":"B only","both_present":"Both present","extinct":"World extinct"}
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"svg.fonttype":"none"})
    figure,axes=plt.subplots(2,2,figsize=(12,7))
    for row,treatment in enumerate(("competition","neutral")):
        for col,initial_b in enumerate((8,72)):
            axis=axes[row,col]
            for cost in (1,2,3,4):
                for seed in range(1200,1210):
                    outcome=outcomes[cost,initial_b,treatment,seed]
                    x,y=seed-1200,cost-1
                    axis.add_patch(Rectangle((x-.47,y-.44),.94,.88,facecolor=colors[outcome],edgecolor="white",linewidth=.6))
                    axis.text(x,y,symbols[outcome],ha="center",va="center",fontsize=10,
                        color="#222222" if outcome=="both_present" else "white")
            axis.set_xlim(-.55,9.55)
            axis.set_ylim(3.55,-.55)
            axis.set_xticks(range(10),[str(s) for s in range(1200,1210)],rotation=45)
            axis.set_yticks(range(4),[str(c) for c in (1,2,3,4)])
            axis.set_ylabel("Movement cost")
            axis.set_title(f"{'Competition: A=250, B=1000' if treatment=='competition' else 'Neutral labels: A=B=250'} | initial B {initial_b}/80",fontsize=11)
            axis.spines[:].set_visible(False)
            axis.tick_params(length=0)
    figure.suptitle("Cost and initial composition change finite-window outcomes",fontsize=15)
    figure.text(.5,.92,"Every square is one world at tick 3,000. All 160 runs shown; labels identify surviving groups.",ha="center",fontsize=10)
    figure.legend([Patch(facecolor=colors[k],label=labels[k]) for k in colors],
        [labels[k] for k in colors],loc="lower center",bbox_to_anchor=(.5,.06),ncol=4,frameon=False)
    figure.text(.5,.025,"Matched seeds share initialization, not future random draws. Both-present endpoints do not establish stable coexistence.",ha="center",fontsize=9)
    figure.subplots_adjust(left=.06,right=.99,top=.84,bottom=.19,wspace=.16,hspace=.5)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for p in targets[:2]:
        figure.savefig(p,dpi=180)
    plt.close(figure)
    targets[2].write_text(json.dumps({"figure":"campaign-014-outcomes-1",
        "outcomes":[{"movement_cost":c,"initial_b":b,"treatment":t,"seed":s,"outcome":v} for (c,b,t,s),v in outcomes.items()],
        "input_sha256":hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+"\n",encoding="utf-8")


if __name__ == "__main__":
    main()
