"""Preregistered food geometry by reproduction threshold experiment."""

import argparse
import csv
from dataclasses import asdict, replace
import hashlib
from itertools import product
import json
from pathlib import Path

from bitgenesis.v0.artifacts import write_json_atomic
from bitgenesis.v0.engine import World
from bitgenesis.v0.runner import load_config, provenance
if __package__:
    from .run_v0_food_geometry import food_map
else:
    from run_v0_food_geometry import food_map


def initialize(base, arm, threshold, seed):
    if arm not in ("dispersed","block") or threshold not in (40,160):
        raise ValueError("Undeclared campaign-017 treatment")
    config=replace(base,seed=seed,initial_food=0,regrowth_probability=15,
                   mutation_probability=0,birth_threshold=threshold)
    world=World(config)
    for organism in world.living.values():
        organism.genome=250
    world.food=food_map(arm,seed)
    if sum(world.food)!=5120:
        raise ValueError("Incorrect initial food energy")
    world.supplied_energy+=sum(world.food)
    world.events.clear()
    world.check_invariants()
    return world


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    base=load_config(Path(__file__).resolve().parents[1]/"experiments/v0/darwin-baseline.toml")
    protocol=dict(protocol="campaign-017-geometry-threshold-1",rules_version="v0-darwin-1",
        seeds=list(range(1400,1410)),arms=["dispersed","block"],thresholds=[40,160],steps=10000,
        early_window=[0,100],baseline_config=asdict(base),initial_food_energy=5120,
        initial_total_energy=7040,layout_seed_offset=1000000,founder_trait=250,
        regrowth_probability=15,mutation_probability=0,status="running",completed_runs=0,**provenance())
    args.output.mkdir(parents=True,exist_ok=False)
    def save(name,value):
        write_json_atomic(args.output/name,value)
    save("metadata.json",protocol)
    results=[]
    try:
        for arm,threshold,seed in product(protocol["arms"],protocol["thresholds"],protocol["seeds"]):
            world=initialize(base,arm,threshold,seed)
            prefix=f"{arm}-threshold-{threshold}-seed-{seed}"
            save(prefix+"-initial.json",dict(arm=arm,birth_threshold=threshold,seed=seed,
                config=asdict(world.config),food=world.food,founders=[asdict(o) for o in world.living.values()],
                snapshot=world.snapshot(),rng_sha256=hashlib.sha256(json.dumps(world.rng.getstate()).encode()).hexdigest()))
            on_food=sum(world.food[o.position]>0 for o in world.living.values())
            under_food=sum(world.food[o.position] for o in world.living.values())
            extinction,observations=None,{}
            peak,peak_tick=80,0
            with (args.output/(prefix+".csv")).open("w",encoding="utf-8",newline="") as stream:
                writer=csv.DictWriter(stream,fieldnames=list(world.snapshot()));writer.writeheader()
                for tick in range(10001):
                    if tick:
                        world.step()
                    world.check_invariants()
                    row=world.snapshot();writer.writerow(row)
                    if row["population"]==0 and extinction is None:
                        extinction=tick
                    if tick in (500,5000):
                        observations[f"population_at_{tick}"]=row["population"]
                    if tick<=100 and row["population"]>peak:
                        peak,peak_tick=row["population"],tick
                    if tick==100:
                        observations.update(population_at_100=row["population"],births_at_100=row["births"],
                            early_peak_population=peak,first_peak_tick=peak_tick,
                            food_eaten_by_100=row["supplied_energy"]-7040+5120-row["food_energy"],
                            food_at_100=row["food_energy"],organism_energy_at_100=row["organism_energy"])
                    world.events.clear()
            results.append(dict(arm=arm,birth_threshold=threshold,seed=seed,**row,**observations,
                extinction_tick=extinction,right_censored=extinction is None,
                founders_on_food=on_food,food_under_founders=under_food))
            save("results.json",results)
            protocol["completed_runs"]=len(results);save("metadata.json",protocol)
            print(f"{prefix}: extinction={extinction}, population={row['population']}",flush=True)
        with (args.output/"results.csv").open("w",encoding="utf-8",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=list(results[0]));writer.writeheader();writer.writerows(results)
        protocol["status"]="complete"
    except (Exception,KeyboardInterrupt) as error:
        protocol["status"]="interrupted" if isinstance(error,KeyboardInterrupt) else "failed"
        protocol["error"]=f"{type(error).__name__}: {error}"
        raise
    finally:
        save("metadata.json",protocol)


if __name__=="__main__":
    main()
