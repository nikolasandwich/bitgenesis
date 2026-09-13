"""Declared long-window coverage assay within the fixed V0 genome vocabulary."""

import argparse
import csv
from dataclasses import asdict, replace
from pathlib import Path

from bitgenesis.v0.artifacts import write_json_atomic
from bitgenesis.v0.engine import World
from bitgenesis.v0.runner import load_config, provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base = load_config(Path(__file__).resolve().parents[1] / "experiments/v0/darwin-baseline.toml")
    protocol = {"protocol": "campaign-013-genome-coverage-1", "rules_version": "v0-darwin-1",
                "steps": 50000, "seeds": list(range(1100, 1105)),
                "treatments": [["mutation", 100], ["no-mutation", 0]],
                "observation_ticks": [0, 1000, 5000, 10000, 25000, 40000, 50000],
                "baseline_config": asdict(base), **provenance(), "status": "running"}
    args.output.mkdir(parents=True, exist_ok=False)
    def save(name, value):
        write_json_atomic(args.output / name, value)
    save("metadata.json", protocol)
    results = []
    try:
        for treatment, mutation in protocol["treatments"]:
            for seed in protocol["seeds"]:
                world = World(replace(base, seed=seed, mutation_probability=mutation))
                seen = set()
                observations = {}
                extinction = None
                prefix = f"{treatment}-seed-{seed}"
                with (args.output / f"{prefix}.csv").open("w", newline="", encoding="utf-8") as metrics, \
                     (args.output / f"{prefix}-births.csv").open("w", newline="", encoding="utf-8") as births:
                    mw = csv.DictWriter(metrics, fieldnames=[*world.snapshot(), "ever_genome_values"])
                    bw = csv.DictWriter(births, fieldnames=["id", "parent_id", "birth_tick", "genome"])
                    mw.writeheader()
                    bw.writeheader()
                    for tick in range(protocol["steps"] + 1):
                        if tick:
                            world.step()
                        world.check_invariants()
                        for event in world.events:
                            if event["event"] == "birth":
                                organism = world.lineage[event["id"]]
                                bw.writerow({key: getattr(organism, key) for key in bw.fieldnames})
                                seen.add(organism.genome)
                        world.events.clear()
                        row = {**world.snapshot(), "ever_genome_values": len(seen)}
                        mw.writerow(row)
                        if row["population"] == 0 and extinction is None:
                            extinction = tick
                        if tick in protocol["observation_ticks"]:
                            observations[str(tick)] = row.copy()
                results.append({"treatment": treatment, "mutation_probability": mutation,
                    "seed": seed, **row, "initial_genome_values": observations["0"]["ever_genome_values"],
                    "new_values_last_10000": row["ever_genome_values"] - observations["40000"]["ever_genome_values"],
                    "extinction_tick": extinction, "right_censored": extinction is None,
                    "observations": observations})
                save("results.json", results)
                print(f"{prefix}: population={row['population']}, ever_values={len(seen)}", flush=True)
        compact = [{k: v for k, v in row.items() if k != "observations"} for row in results]
        with (args.output / "results.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(compact[0]))
            writer.writeheader()
            writer.writerows(compact)
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
