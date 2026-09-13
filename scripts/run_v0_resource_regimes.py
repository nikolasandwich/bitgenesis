"""Resource-regime robustness assay with unchanged V0 dynamics."""

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
    protocol = {"protocol": "campaign-004-resource-regimes-1", "rules_version": "v0-darwin-1",
                "steps": 10000, "seeds": list(range(300, 305)),
                "regrowth_probabilities": [10, 40, 200, 1000], "baseline_config": asdict(base),
                **provenance(), "status": "running"}
    def save(name, value):
        (args.output / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    save("metadata.json", protocol)
    results = []
    for probability in protocol["regrowth_probabilities"]:
        for seed in protocol["seeds"]:
            world = World(replace(base, seed=seed, regrowth_probability=probability))
            late = deque(maxlen=1000)
            extinction = None
            last_birth_tick = last_death_tick = None
            late_births = late_deaths = 0
            with (args.output / f"regrowth-{probability}-seed-{seed}.csv").open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(world.snapshot()))
                writer.writeheader()
                for tick in range(protocol["steps"] + 1):
                    if tick:
                        world.step()
                    world.check_invariants()
                    row = world.snapshot()
                    writer.writerow(row)
                    late.append(row)
                    if row["population"] == 0 and extinction is None:
                        extinction = tick
                    for event in world.events:
                        if event["event"] == "birth" and event["parent_id"] is not None:
                            last_birth_tick = tick
                            late_births += tick > protocol["steps"] - 1000
                        elif event["event"] == "death":
                            last_death_tick = tick
                            late_deaths += tick > protocol["steps"] - 1000
                    world.events.clear()
            record = {"regrowth_probability": probability, "seed": seed, **world.snapshot(),
                      "late_mean_population": mean(r["population"] for r in late),
                      "late_births": late_births, "late_deaths": late_deaths,
                      "last_birth_tick": last_birth_tick, "last_death_tick": last_death_tick,
                      "extinction_tick": extinction}
            results.append(record)
            save("results.json", results)
            print(f"regrowth={probability} seed={seed}: population={record['population']}, "
                  f"late_births={late_births}, late_deaths={late_deaths}, "
                  f"founders={record['founder_lineages']}", flush=True)
    protocol["status"] = "complete"
    save("metadata.json", protocol)
    with (args.output / "results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    main()
