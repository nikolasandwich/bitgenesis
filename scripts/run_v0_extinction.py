"""Preregistered scarce-resource extinction assay; unchanged V0 dynamics."""

import argparse
from collections import deque
import csv
from dataclasses import asdict, replace
from pathlib import Path
from statistics import mean

from bitgenesis.v0.artifacts import write_json_atomic
from bitgenesis.v0.engine import World
from bitgenesis.v0.runner import load_config, provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base = load_config(Path(__file__).resolve().parents[1] / "experiments/v0/darwin-baseline.toml")
    protocol = {"protocol": "campaign-006-extinction-1", "rules_version": "v0-darwin-1",
                "steps": 5000, "seeds": list(range(500, 510)),
                "regrowth_probabilities": [10, 15, 20, 30, 40], "baseline_config": asdict(base),
                **provenance(), "status": "running"}
    args.output.mkdir(parents=True, exist_ok=False)
    def save(name, value):
        write_json_atomic(args.output / name, value)
    save("metadata.json", protocol)
    results = []
    try:
        for probability in protocol["regrowth_probabilities"]:
            for seed in protocol["seeds"]:
                world = World(replace(base, seed=seed, regrowth_probability=probability))
                late = deque(maxlen=1000)
                extinction = None
                with (args.output / f"regrowth-{probability}-seed-{seed}.csv").open("w", newline="", encoding="utf-8") as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(world.snapshot()))
                    writer.writeheader()
                    for tick in range(protocol["steps"] + 1):
                        if tick:
                            world.step()
                        world.check_invariants()
                        row = world.snapshot()
                        writer.writerow(row)
                        late.append(row["population"])
                        if row["population"] == 0 and extinction is None:
                            extinction = tick
                        world.events.clear()
                record = {"regrowth_probability": probability, "seed": seed, **row,
                          "late_mean_population": mean(late), "extinction_tick": extinction,
                          "right_censored": extinction is None}
                results.append(record)
                save("results.json", results)
                print(f"regrowth={probability} seed={seed}: extinct={extinction}, final={row['population']}", flush=True)
        with (args.output / "results.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(results[0]))
            writer.writeheader()
            writer.writerows(results)
        protocol["status"] = "complete"
    except (Exception, KeyboardInterrupt) as error:
        protocol["status"] = "interrupted" if isinstance(error, KeyboardInterrupt) else "failed"
        protocol["error"] = type(error).__name__ + ": " + str(error)
        raise
    finally:
        protocol["completed_runs"] = len(results)
        save("metadata.json", protocol)


if __name__ == "__main__":
    main()
