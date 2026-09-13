"""Finite-world size assay with phenotype-neutral founder-label controls."""

import argparse
from collections import deque
import csv
from dataclasses import asdict, replace
import json
from pathlib import Path
from statistics import mean

from bitgenesis.v0.engine import World
from bitgenesis.v0.runner import load_config, provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    base = load_config(Path(__file__).resolve().parents[1] / "experiments/v0/darwin-baseline.toml")
    protocol = {"protocol": "campaign-005-world-sizes-1", "rules_version": "v0-darwin-1",
                "steps": 10000, "seeds": list(range(400, 405)), "widths": [16, 32, 64],
                "initial_population_density": "5/64", "baseline_config": asdict(base),
                "treatments": {"evolving": "Ordinary random founder genomes and baseline mutation.",
                               "neutral": "After initialization set all founder genomes to 250, disable mutation; founder labels have no effect."},
                **provenance(), "status": "running"}
    def save(name, value):
        (args.output / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    save("metadata.json", protocol)
    results = []
    for width in protocol["widths"]:
        initial = width * width * 5 // 64
        for treatment in protocol["treatments"]:
            for seed in protocol["seeds"]:
                config = replace(base, seed=seed, width=width, height=width, initial_population=initial,
                                 mutation_probability=0 if treatment == "neutral" else 100)
                world = World(config)
                if treatment == "neutral":
                    for o in world.living.values():
                        o.genome = 250
                world.events.clear()
                late = deque(maxlen=1000)
                extinction = fixation = None
                with (args.output / f"width-{width}-{treatment}-seed-{seed}.csv").open("w", newline="", encoding="utf-8") as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(world.snapshot()))
                    writer.writeheader()
                    for tick in range(protocol["steps"] + 1):
                        if tick:
                            world.step()
                        world.check_invariants()
                        world.events.clear()
                        row = world.snapshot()
                        writer.writerow(row)
                        late.append(row)
                        if row["population"] == 0 and extinction is None:
                            extinction = tick
                        if row["founder_lineages"] == 1 and fixation is None:
                            fixation = tick
                result = {"width": width, "treatment": treatment, "seed": seed,
                          "initial_population": initial, **world.snapshot(),
                          "late_mean_population": mean(r["population"] for r in late),
                          "terminal_founder_fraction": row["founder_lineages"] / initial,
                          "first_single_founder_tick": fixation, "extinction_tick": extinction}
                results.append(result)
                save("results.json", results)
                print(f"width={width} {treatment} seed={seed}: population={row['population']}, "
                      f"founders={row['founder_lineages']}, first_single={fixation}, extinct={extinction}", flush=True)
    protocol["status"] = "complete"
    save("metadata.json", protocol)
    with (args.output / "results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    main()
