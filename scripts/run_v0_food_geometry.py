"""Initial food geometry assay with matched total energy and unchanged V0 dynamics."""

import argparse
import csv
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import random

from bitgenesis.v0.artifacts import write_json_atomic
from bitgenesis.v0.engine import World
from bitgenesis.v0.runner import load_config, provenance


def food_map(arm, seed):
    if arm == "uniform":
        return [5]*1024
    rng = random.Random(1_000_000+seed)
    if arm == "dispersed":
        positions = list(range(1024))
        rng.shuffle(positions)
    elif arm == "block":
        dx, dy = rng.randrange(32), rng.randrange(32)
        positions = [((i//32+dy)%32)*32+(i%32+dx)%32 for i in range(1024)]
    else:
        raise ValueError("Unknown food geometry")
    food = [0]*1024
    for position in positions[:213]:
        food[position] = 24
    food[positions[213]] = 8
    return food


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base = load_config(Path(__file__).resolve().parents[1]/"experiments/v0/darwin-baseline.toml")
    protocol = dict(protocol="campaign-016-food-geometry-1", rules_version="v0-darwin-1", steps=10000,
        seeds=list(range(1300,1310)), arms=["uniform","dispersed","block"], initial_food_energy=5120,
        initial_total_energy=7040, layout_seed_offset=1000000, founder_trait=250,
        regrowth_probability=15, mutation_probability=0, baseline_config=asdict(base),
        initialization="Construct initial_food=0, replace food map and add 5120 supplied energy before tick zero",
        status="running", completed_runs=0, **provenance())
    args.output.mkdir(parents=True, exist_ok=False)
    def save(name, value):
        write_json_atomic(args.output/name, value)
    save("metadata.json", protocol)
    results = []
    try:
        for arm in protocol["arms"]:
            for seed in protocol["seeds"]:
                config = replace(base, seed=seed, initial_food=0, regrowth_probability=15, mutation_probability=0)
                world = World(config)
                for organism in world.living.values():
                    organism.genome = 250
                world.food = food_map(arm, seed)
                if sum(world.food) != 5120:
                    raise ValueError("Initial food energy differs from protocol")
                world.supplied_energy += sum(world.food)
                world.events.clear()
                world.check_invariants()
                initial = dict(arm=arm, seed=seed, config=asdict(config), food=world.food,
                    founders=[asdict(o) for o in world.living.values()],
                    rng_sha256=hashlib.sha256(json.dumps(world.rng.getstate()).encode()).hexdigest(),
                    snapshot=world.snapshot())
                save(f"{arm}-seed-{seed}-initial.json", initial)
                exposure_count = sum(world.food[o.position]>0 for o in world.living.values())
                exposure_energy = sum(world.food[o.position] for o in world.living.values())
                extinction, observations = None, {}
                with (args.output/f"{arm}-seed-{seed}.csv").open("w", encoding="utf-8", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(world.snapshot()))
                    writer.writeheader()
                    for tick in range(10001):
                        if tick:
                            world.step()
                        world.check_invariants()
                        row = world.snapshot()
                        writer.writerow(row)
                        if row["population"] == 0 and extinction is None:
                            extinction = tick
                        if tick in (500,5000):
                            observations[f"population_at_{tick}"] = row["population"]
                        world.events.clear()
                results.append(dict(arm=arm, seed=seed, **row, **observations,
                    extinction_tick=extinction, right_censored=extinction is None,
                    founders_on_food=exposure_count, food_under_founders=exposure_energy))
                save("results.json", results)
                protocol["completed_runs"] = len(results)
                save("metadata.json", protocol)
                print(f"{arm} seed={seed}: extinction={extinction}, final={row['population']}", flush=True)
        with (args.output/"results.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(results[0]))
            writer.writeheader()
            writer.writerows(results)
        protocol["status"] = "complete"
    except (Exception, KeyboardInterrupt) as error:
        protocol["status"] = "interrupted" if isinstance(error, KeyboardInterrupt) else "failed"
        protocol["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        save("metadata.json", protocol)


if __name__ == "__main__":
    main()
