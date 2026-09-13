"""Run the preregistered V0 baseline/no-mutation comparison from the repo root."""

import argparse
import csv
from dataclasses import replace
import json
from pathlib import Path
from statistics import mean

from bitgenesis.v0.runner import load_config, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=5000)
    args = parser.parse_args()
    if args.steps < 1:
        parser.error("--steps must be positive")
    args.output.mkdir(parents=True, exist_ok=False)
    base = load_config(Path(__file__).resolve().parents[1] / "experiments/v0/darwin-baseline.toml")
    results = []
    for treatment, mutation in (("baseline", 100), ("no-mutation", 0)):
        for seed in range(5):
            directory = args.output / f"{treatment}-seed-{seed}"
            result = run(replace(base, seed=seed, mutation_probability=mutation),
                         args.steps, directory, frame_interval=50)
            lineage = json.loads((directory / "lineage.json").read_text(encoding="utf-8"))
            founders = [o for o in lineage if o["parent_id"] is None]
            with (directory / "metrics.csv").open(encoding="utf-8", newline="") as stream:
                metrics = list(csv.DictReader(stream))
            late = metrics[-min(1000, len(metrics)):]
            results.append({"treatment": treatment, "seed": seed, **result,
                            "initial_mean_genome": mean(o["genome"] for o in founders),
                            "late_mean_population": mean(int(m["population"]) for m in late),
                            "extinction_tick": next((int(m["tick"]) for m in metrics
                                                     if int(m["population"]) == 0), None),
                            "founder_offspring_min": min(o["offspring"] for o in founders),
                            "founder_offspring_max": max(o["offspring"] for o in founders)})
            (args.output / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
            print(f"{treatment} seed={seed}: population={result['population']}, "
                  f"births={result['births']}, mean_trait={result['mean_genome']}", flush=True)
    with (args.output / "results.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    main()
