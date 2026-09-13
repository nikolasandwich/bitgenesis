"""Plot finite-horizon extinction, recomputing outcomes from all saved metric rows."""

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
    parser.add_argument("--input", type=Path, default=Path("data/campaign-006"))
    parser.add_argument("--output", type=Path, default=Path("docs/research/figures/campaign-006-extinction"))
    args = parser.parse_args()
    metadata = json.loads((args.input / "metadata.json").read_text())
    if metadata["status"] != "complete" or metadata["protocol"] != "campaign-006-extinction-1":
        raise ValueError("Expected complete campaign 006")
    results = json.loads((args.input / "results.json").read_text())
    expected = {(p, s) for p in metadata["regrowth_probabilities"] for s in metadata["seeds"]}
    indexed = {(r["regrowth_probability"], r["seed"]): r for r in results}
    if len(indexed) != len(results) or set(indexed) != expected:
        raise ValueError("Missing/duplicate runs")
    targets = [args.output.with_suffix(suffix) for suffix in (".png", ".svg", ".json")]
    if any(path.exists() for path in targets):
        raise FileExistsError("Choose a new figure prefix")
    hashes = {name: hashlib.sha256((args.input / name).read_bytes()).hexdigest()
              for name in ("metadata.json", "results.json")}
    horizon = metadata["steps"]
    groups = []
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "svg.fonttype": "none"})
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    for index, probability in enumerate(metadata["regrowth_probabilities"]):
        times, final, late = [], [], []
        for seed in metadata["seeds"]:
            name = f"regrowth-{probability}-seed-{seed}.csv"
            path = args.input / name
            hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
            with path.open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            if [int(r["tick"]) for r in rows] != list(range(horizon + 1)):
                raise ValueError(f"Incomplete ticks: {name}")
            populations = [int(r["population"]) for r in rows]
            extinct = next((t for t, n in enumerate(populations) if n == 0), None)
            if extinct is not None and any(populations[extinct:]):
                raise ValueError(f"Population reappeared after extinction: {name}")
            for row in rows:
                if int(row["organism_energy"]) + int(row["food_energy"]) + int(row["dissipated_energy"]) != int(row["supplied_energy"]):
                    raise ValueError(f"Energy accounting: {name}")
                if int(row["population"]) != metadata["baseline_config"]["initial_population"] + int(row["births"]) - int(row["deaths"]):
                    raise ValueError(f"Population accounting: {name}")
            summary = indexed[probability, seed]
            if (summary["extinction_tick"] != extinct or summary["right_censored"] != (extinct is None)
                    or summary["population"] != populations[-1]
                    or summary["late_mean_population"] != mean(populations[-1000:])):
                raise ValueError(f"Summary differs from raw metrics: {name}")
            times.append(extinct)
            final.append(populations[-1])
            late.append(summary["late_mean_population"])
        color = f"C{index}"
        ticks = sorted({0, horizon, *(t for t in times if t is not None)})
        survival = [sum(t is None or t > tick for t in times) / len(times) for tick in ticks]
        axes[0].step(ticks, survival, where="post", label=f"{probability}/1000", color=color)
        axes[0].plot(horizon, survival[-1], "|", color=color, markersize=12)
        axes[1].scatter([index + (j - 4.5) * .04 for j in range(len(late))], late, color=color, alpha=.8)
        extinct_times = [t for t in times if t is not None]
        groups.append({"regrowth_probability": probability, "extinct": len(extinct_times), "runs": len(times),
                       "extinct_only_tick_range": [min(extinct_times), max(extinct_times)] if extinct_times else None,
                       "final_population_range": [min(final), max(final)], "late_mean_population": mean(late)})
    axes[0].set(xlabel="Simulation tick", ylabel="Fraction not yet extinct", ylim=(-.03, 1.05), xlim=(0, horizon))
    axes[0].legend(title="Resource regrowth", loc="upper right", fontsize=8)
    axes[1].set(xlabel="Regrowth probability (per 1000)", ylabel="Mean population, ticks 4001–5000",
                xticks=range(len(groups)), xticklabels=[g["regrowth_probability"] for g in groups])
    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="y", alpha=.2)
    figure.suptitle("Scarce resources: extinction depends on both supply and observation time", fontsize=13)
    figure.text(.08, .025, "10 seeds per condition; 32 x 32 world. Points include extinct runs as zero.\nSurvivors are right-censored at tick 5000; this is not an infinite-time survival claim.", fontsize=9)
    figure.tight_layout(rect=(0, .11, 1, .94))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for path in targets[:2]:
        figure.savefig(path, dpi=160)
    plt.close(figure)
    provenance = {"input_sha256": hashes, "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  "matplotlib": matplotlib.__version__, "groups": groups,
                  "output_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in targets[:2]}}
    targets[2].write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(groups, indent=2))


if __name__ == "__main__":
    main()
