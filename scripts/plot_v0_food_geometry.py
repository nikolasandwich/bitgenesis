"""Show illustrative initial maps and all campaign-016 extinction times."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, NullLocator, StrMethodFormatter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=Path("data/campaign-016"))
    parser.add_argument("--verification",type=Path,default=Path("docs/research/results/campaign-016-verification.json"))
    parser.add_argument("--output",type=Path,default=Path("docs/research/figures/campaign-016-geometry"))
    args = parser.parse_args()
    targets = [args.output.with_suffix(s) for s in (".png",".svg",".json")]
    if any(p.exists() for p in targets):
        raise FileExistsError("Choose a new figure prefix")
    report = json.loads(args.verification.read_text(encoding="utf-8"))
    arms, seeds = ("uniform","dispersed","block"), list(range(1300,1310))
    records = report["runs"]
    indexed = {(r["arm"],r["seed"]):r for r in records}
    if len(records) != 30 or set(indexed) != {(a,s) for a in arms for s in seeds}:
        raise ValueError("Expected all thirty verified outcomes")
    if any(r["population"] != 0 or type(r["extinction_tick"]) is not int or not 0 < r["extinction_tick"] <= 10000 for r in records):
        raise ValueError("This figure requires the verified complete-extinction cohort")
    initial, hashes = {}, {}
    for arm in arms:
        path = args.input/f"{arm}-seed-1300-initial.json"
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        if hashes[path.name] != report["input_sha256"][path.name]:
            raise ValueError("Illustrative map differs from verified input")
        initial[arm] = json.loads(path.read_text(encoding="utf-8"))
    if any(initial[a]["founders"] != initial["uniform"]["founders"] for a in arms):
        raise ValueError("Illustrative founders do not match")
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"svg.fonttype":"none"})
    fig = plt.figure(figsize=(12,10))
    grid = fig.add_gridspec(2,3,height_ratios=[1,1.25],left=.08,right=.96,top=.88,bottom=.105,hspace=.5,wspace=.15)
    titles = {"uniform":"Uniform: 5 in every cell","dispersed":"Dispersed: same rich-cell multiset","block":"Block: same rich-cell multiset"}
    colors = {"uniform":"#267d68","dispersed":"#b6693a","block":"#65549c"}
    markers = {"uniform":"o","dispersed":"s","block":"^"}
    maps = []
    for j, arm in enumerate(arms):
        ax = fig.add_subplot(grid[0,j])
        maps.append(ax)
        food = initial[arm]["food"]
        pixels = [food[i:i+32] for i in range(0,1024,32)]
        shown = ax.imshow(pixels,vmin=0,vmax=24,cmap="YlGnBu",interpolation="nearest")
        positions = [o["position"] for o in initial[arm]["founders"]]
        ax.scatter([p%32 for p in positions],[p//32 for p in positions],s=9,facecolors="none",edgecolors="#d74449",linewidths=.65)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(titles[arm],fontsize=10)
    colorbar = fig.colorbar(shown,ax=maps,orientation="horizontal",fraction=.055,pad=.07,aspect=55)
    colorbar.set_ticks([0,5,8,24])
    colorbar.set_label("Initial food per cell; red rings = identical founder positions (seed 1300 only)",fontsize=9)
    ax = fig.add_subplot(grid[1,:])
    for i, seed in enumerate(seeds):
        times = [indexed[a,seed]["extinction_tick"] for a in arms]
        offsets = [-.15,0,.15]
        ax.plot(times,[i+offset for offset in offsets],color="#d9dedc",linewidth=1,zorder=1)
        for arm, value, offset in zip(arms,times,offsets):
            ax.scatter(value,i+offset,color=colors[arm],marker=markers[arm],s=43,zorder=3,
                       label=arm.capitalize() if i==0 else None)
    ax.set_xscale("log")
    ax.set_xlim(90,11000)
    ax.set_ylim(9.6,-.6)
    ax.set_yticks(range(10),[str(s) for s in seeds])
    ax.set_ylabel("Matched seed")
    ax.xaxis.set_major_locator(FixedLocator([100,300,1000,3000,10000]))
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xlabel("First extinction tick (logarithmic time axis)")
    ax.grid(axis="x",color="#e5e8e6",linewidth=.8)
    ax.spines[["top","right"]].set_visible(False)
    ax.set_title("All 30 worlds: same final extinction, different persistence",loc="left",fontsize=12,pad=16)
    ax.legend(loc="upper right",ncol=3,bbox_to_anchor=(1,1.17),frameon=False)
    fig.suptitle("Equal initial food energy, different extinction times",fontsize=16,y=.975)
    fig.text(.5,.936,"Each world starts with 5,120 food + 1,920 organism energy. Fixed trait 250, no mutation, unchanged V0 dynamics.",ha="center",fontsize=10)
    fig.text(.5,.032,"Maps show the first declared seed, not an average. Lines connect matched seeds, not identical later random draws. No universal geometry effect claimed.",ha="center",fontsize=9)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for path in targets[:2]:
        fig.savefig(path,dpi=180)
    plt.close(fig)
    targets[2].write_text(json.dumps(dict(figure="campaign-016-geometry-1",illustrative_map_seed=1300,
        extinction_points=[dict(arm=r["arm"],seed=r["seed"],extinction_tick=r["extinction_tick"]) for r in records],
        map_sha256=hashes,verification_sha256=hashlib.sha256(args.verification.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+"\n",encoding="utf-8")


if __name__ == "__main__":
    main()
