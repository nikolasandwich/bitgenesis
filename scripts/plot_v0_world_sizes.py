"""Plot all campaign-005 founder trajectories, with medians (not confidence bands)."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
from statistics import median

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/campaign-005"))
    parser.add_argument("--output", type=Path, default=Path("docs/research/figures/campaign-005-lineages"))
    args = parser.parse_args()
    metadata = json.loads((args.input / "metadata.json").read_text(encoding="utf-8"))
    if metadata["status"] != "complete" or metadata["protocol"] != "campaign-005-world-sizes-1":
        raise ValueError("Expected completed campaign-005 data")
    targets = [args.output.with_suffix(extension) for extension in (".png", ".svg", ".json")]
    if any(p.exists() for p in targets):
        raise FileExistsError("Choose a new plot output prefix; existing figures are preserved")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "svg.fonttype": "none"})
    figure, axes = plt.subplots(2, 3, figsize=(12, 7.3), sharex=True)
    inputs = {}
    for column, width in enumerate(metadata["widths"]):
        for row, treatment in enumerate(("evolving", "neutral")):
            axis = axes[row, column]
            trajectories = []
            for seed in metadata["seeds"]:
                path = args.input / f"width-{width}-{treatment}-seed-{seed}.csv"
                inputs[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
                with path.open(encoding="utf-8", newline="") as stream:
                    records = list(csv.DictReader(stream))
                ticks = [int(record["tick"]) for record in records]
                founders = [int(record["founder_lineages"]) for record in records]
                if ticks != list(range(metadata["steps"] + 1)):
                    raise ValueError(f"Incomplete tick sequence: {path}")
                if any(n == 0 for n in founders):
                    raise ValueError("An extinction needs an explicit zero-safe figure; do not hide it on a log axis")
                trajectories.append(founders)
                axis.plot(ticks, founders, color="#84a69a" if treatment == "evolving" else "#a4a8c4",
                          alpha=.65, linewidth=.9)
            central = [median(values) for values in zip(*trajectories)]
            axis.plot(ticks, central, color="#1f5142" if treatment == "evolving" else "#3b4376", linewidth=2)
            axis.set_title(f"{width} x {width} | {'Evolving traits' if treatment == 'evolving' else 'Neutral founder labels'}", loc="left", fontsize=11)
            axis.set_yscale("log")
            initial = width * width * 5 // 64
            axis.set_ylim(.8, initial * 1.25)
            axis.set_yticks([n for n in (1, 5, 20, 80, 320) if n <= initial])
            axis.yaxis.set_major_formatter(ScalarFormatter())
            axis.grid(axis="y", which="major", alpha=.2)
            axis.set_xlim(0, metadata["steps"])
            axis.set_xticks([0, 5000, 10000], ["0", "5,000", "10,000"])
            if column == 0:
                axis.set_ylabel("Surviving founder lineages (log)")
            if row == 1:
                axis.set_xlabel("Simulation tick")
    figure.suptitle("Founder persistence depends on world size and the observation horizon", fontsize=16, x=.07, ha="left", y=.98)
    figure.text(.07, .92, "Thin lines: five seeds per condition. Thick line: pointwise median. No confidence interval is shown.", color="#52645c", fontsize=10)
    figure.text(.07, .025, "Initial density: 5/64. Evolving: random founder traits + mutation. Neutral: all traits 250, no mutation.\nFounder labels are ancestry identifiers, not species. No run in this campaign became extinct.", color="#52645c", fontsize=9)
    figure.tight_layout(rect=(.04, .09, 1, .90), h_pad=2, w_pad=2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for target in targets[:2]:
        figure.savefig(target, dpi=180, facecolor="white")
    plt.close(figure)
    provenance = {"campaign_commit": metadata["git_commit"], "matplotlib": matplotlib.__version__,
                  "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  "input_sha256": inputs, "thin_lines": "individual seeds", "thick_line": "pointwise median",
                  "confidence_intervals": False,
                  "output_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in targets[:2]}}
    targets[2].write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print("\n".join(str(path.resolve()) for path in targets))


if __name__ == "__main__":
    main()
