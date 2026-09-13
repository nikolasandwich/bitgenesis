"""Declared intervention assay: fixed founder traits and movement cost treatments."""

import argparse
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
    metadata = {"protocol": "campaign-002-fixed-trait-assay-1", "rules_version": "v0-darwin-1",
                "steps": 2000, "seeds": list(range(100, 110)), "traits": [0, 250, 500, 750, 1000],
                "movement_costs": [1, 4], "baseline_config": asdict(base),
                "intervention": "After ordinary initialization, replace every founder genome with the treatment trait. Disable mutation. Preserve initialization RNG consumption and positions.",
                **provenance(), "status": "running"}
    def save(name, value):
        (args.output / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    save("metadata.json", metadata)
    results = []
    for cost in metadata["movement_costs"]:
        for trait in metadata["traits"]:
            for seed in metadata["seeds"]:
                world = World(replace(base, seed=seed, mutation_probability=0, movement_cost=cost))
                for organism in world.living.values():
                    organism.genome = trait
                # Do not retain pre-intervention birth events as if they described the assay.
                world.events.clear()
                history = [world.snapshot()]
                for _ in range(metadata["steps"]):
                    world.step()
                    world.check_invariants()
                    world.events.clear()
                    history.append(world.snapshot())
                record = {"movement_cost": cost, "trait": trait, "seed": seed,
                          **world.snapshot(), "late_mean_population": mean(m["population"] for m in history[-500:]),
                          "extinction_tick": next((m["tick"] for m in history if m["population"] == 0), None)}
                results.append(record)
                with (args.output / f"cost-{cost}-trait-{trait}-seed-{seed}.csv").open("w", newline="", encoding="utf-8") as stream:
                    writer = csv.DictWriter(stream, fieldnames=list(history[0]))
                    writer.writeheader()
                    writer.writerows(history)
                save("results.json", results)
            group = results[-len(metadata["seeds"]):]
            print(f"cost={cost} trait={trait}: late_population={mean(r['late_mean_population'] for r in group):.3f}, "
                  f"extinct={sum(r['extinction_tick'] is not None for r in group)}/10", flush=True)
    metadata["status"] = "complete"
    save("metadata.json", metadata)
    with (args.output / "results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    main()
