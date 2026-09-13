"""Paired-trait competition with neutral founder-label controls."""

import argparse
import csv
from dataclasses import asdict, replace
import json
from pathlib import Path

from bitgenesis.v0.engine import World
from bitgenesis.v0.runner import load_config, provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    base = load_config(Path(__file__).resolve().parents[1] / "experiments/v0/darwin-baseline.toml")
    metadata = {"protocol": "campaign-003-competition-1", "rules_version": "v0-darwin-1",
                "steps": 3000, "seeds": list(range(200, 210)), "initial_b_counts": [8, 40],
                "movement_costs": [1, 4], "baseline_config": asdict(base),
                "intervention": "Disable mutation. First B founder IDs receive B trait, remaining founders receive A=250. Competition B=1000; neutral B=250. Track B ancestry via founder ID, including after extinction.",
                **provenance(), "status": "running"}
    def save(name, value):
        (args.output / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    save("metadata.json", metadata)
    results = []
    for cost in metadata["movement_costs"]:
        for initial_b in metadata["initial_b_counts"]:
            for treatment, b_trait in (("competition", 1000), ("neutral", 250)):
                group = []
                for seed in metadata["seeds"]:
                    world = World(replace(base, seed=seed, mutation_probability=0, movement_cost=cost))
                    for organism in world.living.values():
                        organism.genome = b_trait if organism.founder_id < initial_b else 250
                    world.events.clear()
                    history = []
                    for tick in range(metadata["steps"] + 1):
                        if tick:
                            world.step()
                        world.check_invariants()
                        world.events.clear()
                        n = len(world.living)
                        count_b = sum(o.founder_id < initial_b for o in world.living.values())
                        history.append({"tick": tick, "population": n, "a": n-count_b, "b": count_b,
                                        "b_fraction": count_b/n if n else None})
                    terminal = history[-1]
                    record = {"movement_cost": cost, "initial_b": initial_b, "treatment": treatment,
                              "b_trait": b_trait, "seed": seed, **terminal,
                              "a_loss_tick": next((m["tick"] for m in history if m["a"] == 0), None),
                              "b_loss_tick": next((m["tick"] for m in history if m["b"] == 0), None),
                              "extinction_tick": next((m["tick"] for m in history if m["population"] == 0), None)}
                    group.append(record)
                    results.append(record)
                    with (args.output / f"cost-{cost}-b-{initial_b}-{treatment}-seed-{seed}.csv").open("w", newline="", encoding="utf-8") as stream:
                        writer = csv.DictWriter(stream, fieldnames=list(history[0]))
                        writer.writeheader()
                        writer.writerows(history)
                    save("results.json", results)
                fixed = sum(r["b"] > 0 and r["a"] == 0 for r in group)
                lost = sum(r["b"] == 0 and r["a"] > 0 for r in group)
                extinct = sum(r["population"] == 0 for r in group)
                print(f"cost={cost} initial_b={initial_b} {treatment}: B-only={fixed}, A-only={lost}, "
                      f"extinct={extinct}, coexist={10-fixed-lost-extinct}", flush=True)
    metadata["status"] = "complete"
    save("metadata.json", metadata)
    with (args.output / "results.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    main()
