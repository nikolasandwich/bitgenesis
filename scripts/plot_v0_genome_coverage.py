"""Plot verified cumulative and living genome diversity for all campaign-013 worlds."""

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
    parser.add_argument("--input", type=Path, default=Path("data/campaign-013"))
    parser.add_argument("--output", type=Path, default=Path("docs/research/figures/campaign-013-coverage"))
    args = parser.parse_args()
    targets = [args.output.with_suffix(s) for s in (".png", ".svg", ".json")]
    if any(p.exists() for p in targets):
        raise FileExistsError("Choose a new output prefix")
    reference_path = Path(__file__).resolve().parents[1] / "docs/research/results/campaign-013-verification.json"
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    curves, hashes = [], {}
    for treatment in ("mutation", "no-mutation"):
        for seed in range(1100, 1105):
            path = args.input / f"{treatment}-seed-{seed}.csv"
            hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
            if hashes[path.name] != reference["input_sha256"].get(path.name):
                raise ValueError("Metrics differ from verified campaign")
            ever, living, previous = [], [], None
            with path.open(newline="", encoding="utf-8") as stream:
                count = 0
                for tick, row in enumerate(csv.DictReader(stream)):
                    if int(row["tick"]) != tick:
                        raise ValueError("Invalid tick sequence")
                    value = int(row["ever_genome_values"])
                    if previous is None or value != previous or tick == 50000:
                        ever.append([tick, value])
                    if tick % 100 == 0:
                        living.append([tick, int(row["genome_variants"])])
                    previous = value
                    count += 1
            if count != 50001:
                raise ValueError("Incomplete observation horizon")
            curves.append({"treatment": treatment, "seed": seed, "ever": ever, "living": living})
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "svg.fonttype": "none"})
    figure, axes = plt.subplots(1, 2, figsize=(11, 5))
    for curve in curves:
        mutation = curve["treatment"] == "mutation"
        color = "#247b62" if mutation else "#697887"
        label = ("Mutation" if mutation else "No mutation") if curve["seed"] == 1100 else None
        x, y = zip(*curve["ever"])
        axes[0].step(x, y, where="post", color=color, alpha=0.7, linewidth=1.4, label=label)
        x, y = zip(*curve["living"])
        axes[1].plot(x, y, color=color, alpha=0.5, linewidth=1)
    axes[0].axhline(1001, color="#a87d44", linestyle=":", linewidth=1.5, label="1001 encoded settings")
    axes[0].set_ylim(0, 1050)
    axes[1].set_ylim(bottom=0)
    axes[0].set_title("Distinct values ever born (exact steps)")
    axes[1].set_title("Distinct values alive (sampled every 100 ticks)")
    for axis in axes:
        axis.set_xlim(0, 50000)
        axis.set_xlabel("Tick")
        axis.set_ylabel("Number of genome values")
        axis.grid(alpha=0.2)
        axis.spines[["top", "right"]].set_visible(False)
    figure.suptitle("More historical variants within the same inherited vocabulary", fontsize=14)
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.06), ncol=3, frameon=False)
    figure.text(0.5, 0.02, "Five worlds per arm; all shown. Living curves may omit brief changes. New scalar values are not new functions.", ha="center", fontsize=9)
    figure.subplots_adjust(left=0.07, right=0.98, top=0.84, bottom=0.25, wspace=0.23)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for path in targets[:2]:
        figure.savefig(path, dpi=180)
    plt.close(figure)
    report = {"figure": "campaign-013-coverage-1", "living_stride": 100, "curves": curves,
              "input_sha256": hashes, "verification_sha256": hashlib.sha256(reference_path.read_bytes()).hexdigest(),
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    targets[2].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
