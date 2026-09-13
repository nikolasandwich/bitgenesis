"""Show every campaign-009 population trajectory in the exploratory early window."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/campaign-009"))
    parser.add_argument("--output", type=Path, default=Path("docs/research/figures/campaign-009-early"))
    args = parser.parse_args()
    targets = [args.output.with_suffix(suffix) for suffix in (".png", ".svg", ".json")]
    if any(path.exists() for path in targets):
        raise FileExistsError("Choose a new output prefix")
    metadata = json.loads((args.input / "metadata.json").read_text())
    if metadata["status"] != "complete" or metadata["protocol"] != "campaign-009-energy-allocation-1":
        raise ValueError("Expected completed campaign 009")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "svg.fonttype": "none"})
    figure, axes = plt.subplots(1, 3, figsize=(12, 4.6), sharex=True, sharey=True)
    hashes = {}
    maximum = 0
    treatments = [("low", "Low: 1,920 initial energy", "#657b83"),
                  ("food", "Food: 7,040 initial energy", "#247b62"),
                  ("stored", "Stored: 7,040 initial energy", "#b35a33")]
    for axis, (treatment, title, color) in zip(axes, treatments):
        traces = []
        for seed in range(800, 810):
            path = args.input / f"{treatment}-seed-{seed}.csv"
            hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
            with path.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            if [int(row["tick"]) for row in rows] != list(range(10001)):
                raise ValueError("Incomplete trajectory")
            population = [int(row["population"]) for row in rows[:101]]
            if any(value < 0 for value in population) or population[0] != 80:
                raise ValueError("Invalid population trace")
            traces.append(population)
            maximum = max(maximum, max(population))
            axis.plot(range(101), population, color=color, alpha=0.28, linewidth=1)
        axis.plot(range(101), [mean(values) for values in zip(*traces)], color=color, linewidth=2.8)
        axis.set_title(title, fontsize=11, pad=12)
        axis.set_xlabel("Tick")
        axis.set_xlim(0, 100)
        axis.grid(axis="y", alpha=0.2)
        axis.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Living individuals")
    axes[0].set_ylim(0, maximum * 1.08)
    figure.suptitle("Initial energy allocation and early population trajectories", fontsize=15, y=0.98)
    figure.text(0.5, 0.045, "Thin lines: all 10 seeds per arm. Thick line: mean. Same axes. Exploratory ticks 0–100; full runs last 10,000 ticks.", ha="center", fontsize=9)
    figure.subplots_adjust(left=0.07, right=0.98, bottom=0.18, top=0.80, wspace=0.15)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for path in targets[:2]:
        figure.savefig(path, dpi=180)
    plt.close(figure)
    targets[2].write_text(json.dumps({"figure": "campaign-009-early-1", "seeds": list(range(800, 810)),
                         "window": [0, 100], "input_sha256": hashes,
                         "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
