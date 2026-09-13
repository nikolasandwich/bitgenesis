"""Retrospective death-site observations during verified campaign-012 prefix replays."""

import argparse
import csv
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from bitgenesis.v0.engine import World
from bitgenesis.v0.runner import load_config, provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/campaign-012"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    verification = json.loads((root / "docs/research/results/campaign-012-verification.json").read_text(encoding="utf-8"))
    base = load_config(root / "experiments/v0/darwin-baseline.toml")
    deaths, runs, hashes = [], [], {}
    original_die = World._die
    for cost in (0, 4):
        for seed in range(1000, 1010):
            treatment = f"stored-40-cost-{cost}"
            path = args.input / f"{treatment}-seed-{seed}.csv"
            hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
            if hashes[path.name] != verification["input_sha256"].get(path.name):
                raise ValueError("Reference differs from verified metrics")
            config = replace(base, seed=seed, initial_food=0, initial_energy=88,
                             regrowth_probability=15, mutation_probability=0,
                             birth_threshold=40, birth_cost=cost)
            world = World(config)
            for organism in world.living.values():
                organism.genome = 250
            world.events.clear()
            start = len(deaths)

            def observe(instance, organism):
                neighbors = instance.neighbors(organism.position)
                deaths.append({"treatment": treatment, "seed": seed,
                    "tick": instance.tick, "id": organism.id, "position": organism.position,
                    "energy": organism.energy, "cell_food": instance.food[organism.position],
                    "neighbor_food": sum(instance.food[p] for p in neighbors),
                    "world_food": sum(instance.food)})
                original_die(instance, organism)

            with path.open(newline="", encoding="utf-8") as stream, patch.object(World, "_die", observe):
                reference = csv.DictReader(stream)
                for tick in range(101):
                    if tick:
                        world.step()
                    world.check_invariants()
                    raw = next(reference)
                    expected = {k: None if v == "" else float(v) if k == "mean_genome" else int(v)
                                for k, v in raw.items()}
                    if world.snapshot() != expected:
                        raise ValueError(f"Observed prefix differs: {path.name}, tick {tick}")
                    world.events.clear()
            observed = deaths[start:]
            if world.living or len(observed) != world.snapshot()["deaths"]:
                raise ValueError("Expected complete extinction and observed death count by 100")
            runs.append({"treatment": treatment, "seed": seed, "deaths": len(observed),
                         "deaths_with_cell_food": sum(r["cell_food"] > 0 for r in observed),
                         "deaths_with_neighbor_food": sum(r["neighbor_food"] > 0 for r in observed),
                         "deaths_with_world_food": sum(r["world_food"] > 0 for r in observed)})
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "deaths.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(deaths[0]))
        writer.writeheader()
        writer.writerows(deaths)
    report = {"analysis": "retrospective-death-context-012-1", "prefix_ticks": 100,
              "replayed_worlds": 20, "computed_replay_ticks": 2000,
              "matched_metric_rows": 2020, "new_independent_replicates": 0,
              "runs": runs, "input_sha256": hashes, **provenance()}
    (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(runs, indent=2))


if __name__ == "__main__":
    main()
