"""Plot full-window survival fractions from verified campaign-010 compact outcomes."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("docs/research/results/campaign-010.csv"))
    parser.add_argument("--output", type=Path, default=Path("docs/research/figures/campaign-010-survival"))
    args = parser.parse_args()
    targets = [args.output.with_suffix(s) for s in (".png", ".svg", ".json")]
    if any(path.exists() for path in targets):
        raise FileExistsError("Choose a new output prefix")
    with args.input.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    treatments = ("food-40", "stored-40", "food-160", "stored-160")
    keys = [(r["treatment"], int(r["seed"])) for r in rows]
    if len(keys) != 40 or set(keys) != {(t, s) for t in treatments for s in range(900, 910)}:
        raise ValueError("Expected complete campaign 010 grid")
    for row in rows:
        death = int(row["extinction_tick"]) if row["extinction_tick"] else None
        if int(row["tick"]) != 10000 or (death is not None and not 1 <= death <= 10000):
            raise ValueError("Invalid observation horizon or extinction")
        for horizon, field in ((500, "population_at_500"), (5000, "population_at_5000"), (10000, "population")):
            if (int(row[field]) > 0) != (death is None or death > horizon):
                raise ValueError("Survival counts disagree with extinction times")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "svg.fonttype": "none"})
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
    curves = []
    for treatment in treatments:
        selected = [r for r in rows if r["treatment"] == treatment]
        deaths = [int(r["extinction_tick"]) for r in selected if r["extinction_tick"]]
        times = sorted({0, 10000, *deaths})
        fractions = [sum(not r["extinction_tick"] or int(r["extinction_tick"]) > tick for r in selected) / 10 for tick in times]
        color = "#247b62" if treatment.startswith("food") else "#b35a33"
        style = "-" if treatment.endswith("160") else "--"
        for axis in axes:
            axis.step(times, fractions, where="post", color=color, linestyle=style, linewidth=2,
                      label=treatment.replace("-", " / threshold "))
            if fractions[-1] > 0:
                axis.plot(10000, fractions[-1], marker="|", color=color, markersize=10)
        curves.append({"treatment": treatment, "ticks": times, "fraction_alive": fractions})
    axes[0].set_xlim(0, 10000)
    axes[1].set_xlim(0, 500)
    axes[0].set_title("Full observation window")
    axes[1].set_title("Early window (same curves)")
    for axis in axes:
        axis.set_ylim(-0.025, 1.055)
        axis.set_xlabel("Tick")
        axis.grid(alpha=0.2)
        axis.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Fraction of worlds still alive")
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.075), ncol=2, frameon=False)
    figure.suptitle("Reproduction threshold and finite-horizon survival", fontsize=15)
    figure.text(0.5, 0.02, "10 worlds per arm; all included. Endpoint survivors are censored at 10,000. Overlapping curves are retained.", ha="center", fontsize=9)
    figure.subplots_adjust(left=0.08, right=0.98, top=0.82, bottom=0.28, wspace=0.13)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for path in targets[:2]:
        figure.savefig(path, dpi=180)
    plt.close(figure)
    targets[2].write_text(json.dumps({"figure": "campaign-010-survival-1", "curves": curves,
        "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
