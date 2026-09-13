"""Long-horizon follow-up of both high-threshold arms, with verified historical prefixes."""

import argparse
from collections import deque
import csv
import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path
from statistics import mean

from bitgenesis.v0.artifacts import write_json_atomic
from bitgenesis.v0.engine import World
from bitgenesis.v0.runner import load_config, provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference", type=Path, default=Path("data/campaign-010"))
    args = parser.parse_args()
    reference = json.loads((args.reference / "metadata.json").read_text())
    if reference["status"] != "complete" or reference["protocol"] != "campaign-010-reproduction-threshold-1":
        raise ValueError("Expected complete campaign 010 reference")
    base = load_config(Path(__file__).resolve().parents[1] / "experiments/v0/darwin-baseline.toml")
    protocol = {"protocol": "campaign-011-long-horizon-1", "rules_version": "v0-darwin-1",
                "steps": 100000, "seeds": list(range(900, 910)), "treatments": [("food-160", 5, 24, 160), ("stored-160", 0, 88, 160)],
                "regrowth_probability": 15, "founder_trait": 250, "mutation_probability": 0,
                "reference_prefix_ticks": 10000, "reference_sha256": {}, "baseline_config": asdict(base), **provenance(), "status": "running"}
    args.output.mkdir(parents=True, exist_ok=False)
    def save(name, value):
        write_json_atomic(args.output / name, value)
    save("metadata.json", protocol)
    results = []
    try:
        for treatment, food, energy, threshold in protocol["treatments"]:
            for seed in protocol["seeds"]:
                reference_path = args.reference / f"{treatment}-seed-{seed}.csv"
                protocol["reference_sha256"][reference_path.name] = hashlib.sha256(reference_path.read_bytes()).hexdigest()
                with reference_path.open(newline="", encoding="utf-8") as reference_stream:
                    reference_rows = [{k: None if v == "" else float(v) if k == "mean_genome" else int(v)
                                       for k, v in r.items()} for r in csv.DictReader(reference_stream)]
                if len(reference_rows) != 10001:
                    raise ValueError("Incomplete reference prefix")
                world = World(replace(base, seed=seed, initial_food=food, initial_energy=energy,
                                      regrowth_probability=15, mutation_probability=0, birth_threshold=threshold))
                for organism in world.living.values():
                    organism.genome = 250
                world.events.clear()
                late = deque(maxlen=1000)
                extinction = None
                observations = {}
                with (args.output / f"{treatment}-seed-{seed}.csv").open("w", newline="", encoding="utf-8") as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(world.snapshot()))
                    writer.writeheader()
                    for tick in range(protocol["steps"] + 1):
                        if tick:
                            world.step()
                        world.check_invariants()
                        row = world.snapshot()
                        if tick <= 10000 and row != reference_rows[tick]:
                            raise ValueError(f"Historical prefix differs: {treatment} seed={seed} tick={tick}")
                        writer.writerow(row)
                        if tick and tick % 10000 == 0:
                            print(f"progress {treatment} seed={seed}: tick={tick}, population={row['population']}", flush=True)
                        late.append(row["population"])
                        if row["population"] == 0 and extinction is None:
                            extinction = tick
                        if tick in (10000, 50000):
                            observations[f"population_at_{tick}"] = row["population"]
                            observations[f"births_at_{tick}"] = row["births"]
                        world.events.clear()
                results.append({"treatment": treatment, "initial_food": food, "initial_energy": energy, "birth_threshold": threshold, "seed": seed, **row, **observations,
                                "extinction_tick": extinction, "right_censored": extinction is None,
                                "late_mean_population": mean(late)})
                save("results.json", results)
                print(f"treatment={treatment} seed={seed}: extinct={extinction}, final={row['population']}", flush=True)
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
