"""Plot all ten retrospective campaign-001 mean-trait decompositions."""

import argparse
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("docs/research/results/trait-change-001.json"))
    parser.add_argument("--output", type=Path, default=Path("docs/research/figures/trait-change-001"))
    args = parser.parse_args()
    targets = [args.output.with_suffix(s) for s in (".png", ".svg", ".json")]
    if any(p.exists() for p in targets):
        raise FileExistsError("Choose a new figure prefix")
    report = json.loads(args.input.read_text(encoding="utf-8"))
    rows = report["runs"]
    keys = [(r["treatment"], r["seed"]) for r in rows]
    if len(keys) != 10 or set(keys) != {(t, s) for t in ("baseline", "no-mutation") for s in range(5)}:
        raise ValueError("Expected complete ten-world grid")
    fields = ("birth_sorting", "death_sorting", "transmitted_mutation")
    for row in rows:
        if (row["ticks_checked"] != 5000
                or not all(math.isfinite(row[k]) for k in (*fields, "net_change", "initial_mean", "final_mean"))
                or not math.isclose(sum(row[k] for k in fields), row["net_change"], abs_tol=1e-9)
                or not math.isclose(row["final_mean"] - row["initial_mean"], row["net_change"], abs_tol=1e-9)):
            raise ValueError("Invalid decomposition totals")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "svg.fonttype": "none"})
    figure, axes = plt.subplots(1, 2, figsize=(11, 5.5), sharex=True, sharey=True)
    colors = ("#287b63", "#537fa3", "#ba603d")
    labels = ("Birth sorting", "Death sorting", "Transmitted mutation")
    for axis, treatment, title in zip(axes, ("baseline", "no-mutation"), ("Mutation enabled", "No mutation")):
        selected = sorted((r for r in rows if r["treatment"] == treatment), key=lambda r: r["seed"])
        for y, row in enumerate(selected):
            positive = negative = 0
            for field, color, label in zip(fields, colors, labels):
                value = row[field]
                left = positive if value >= 0 else negative
                axis.barh(y, value, left=left, height=0.6, color=color,
                          label=label if y == 0 else None)
                if value >= 0:
                    positive += value
                else:
                    negative += value
            axis.plot(row["net_change"], y, "D", color="#182321", markeredgecolor="white",
                      markersize=7, label="Net mean change" if y == 0 else None)
        axis.set_title(title)
        axis.axvline(0, color="#555555", linewidth=0.8)
        axis.set_yticks(range(5), [f"Seed {s}" for s in range(5)])
        axis.tick_params(axis="y", labelleft=True)
        axis.set_xlim(-200, 700)
        axis.set_xlabel("Cumulative contribution (genome units)")
        axis.grid(axis="x", alpha=0.15)
        axis.set_axisbelow(True)
        axis.spines[["top", "right", "left"]].set_visible(False)
    axes[0].invert_yaxis()
    handles, names = axes[0].get_legend_handles_labels()
    figure.legend(handles, names, loc="lower center", bbox_to_anchor=(0.5, 0.065), ncol=4, frameon=False)
    figure.suptitle("Mean trait rises despite negative transmitted mutation", fontsize=15)
    figure.text(0.5, 0.91, "All ten worlds, ticks 1–5,000. Same axes; positive and negative contributions stack separately.", ha="center", fontsize=9)
    figure.text(0.5, 0.025, "Post hoc accounting on realized trajectories; not a causal effect estimate. Diamonds show the signed sum.", ha="center", fontsize=9)
    figure.subplots_adjust(left=0.075, right=0.985, top=0.82, bottom=0.23, wspace=0.25)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for target in targets[:2]:
        figure.savefig(target, dpi=180)
    plt.close(figure)
    targets[2].write_text(json.dumps({"figure": "trait-change-001-1", "runs": rows,
        "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
