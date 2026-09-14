"""Preregistered joint-zero-charge necessity probe in block-food worlds."""

import argparse
import csv
from contextlib import ExitStack
from dataclasses import asdict, replace
import hashlib
from itertools import product
import json
from pathlib import Path

from bitgenesis.v0.artifacts import write_json_atomic
from scripts.observe_v0_energy import EnergyWorld
from bitgenesis.v0.runner import load_config, provenance
from scripts.run_v0_food_geometry import food_map


def initialize(base, arm, threshold, cost, seed):
    if arm != "block" or threshold not in (40,160) or type(cost) is not int or cost not in (0,4):
        raise ValueError("Undeclared campaign-019 treatment")
    config=replace(base,seed=seed,initial_food=0,regrowth_probability=15,
                   mutation_probability=0,birth_threshold=threshold,movement_cost=0,birth_cost=cost)
    world=EnergyWorld(config)
    for organism in world.living.values():
        organism.genome=250
    world.food[:]=food_map(arm,seed)
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
    protocol=dict(protocol="campaign-019-joint-zero-charge-1",rules_version="v0-darwin-1",
        seeds=list(range(1600,1610)),arms=["block"],thresholds=[40,160],birth_costs=[0,4],movement_cost=0,steps=10000,
        observation_schemas=dict(feeding=3,terminal=1,energy=1),
        early_window=[0,100],baseline_config=asdict(base),initial_food_energy=5120,
        initial_total_energy=7040,layout_seed_offset=1000000,founder_trait=250,
        regrowth_probability=15,mutation_probability=0,status="running",completed_runs=0,**provenance())
    if protocol["git_dirty"] is not False:
        raise ValueError("Commit source before outcome execution")
    protocol["protocol_sha256"]=hashlib.sha256((Path(__file__).resolve().parents[1]/"experiments/v0/campaign-019.md").read_bytes()).hexdigest()
    args.output.mkdir(parents=True,exist_ok=False)
    def save(name,value):
        write_json_atomic(args.output/name,value)
    save("metadata.json",protocol)
    results=[]
    try:
        for arm,threshold,cost,seed in product(protocol["arms"],protocol["thresholds"],protocol["birth_costs"],protocol["seeds"]):
            world=initialize(base,arm,threshold,cost,seed)
            prefix=f"{arm}-threshold-{threshold}-birth-cost-{cost}-seed-{seed}"
            save(prefix+"-initial.json",dict(arm=arm,birth_threshold=threshold,movement_cost=0,birth_cost=cost,seed=seed,
                config=asdict(world.config),food=world.food,founders=[asdict(o) for o in world.living.values()],
                snapshot=world.snapshot(),rng_sha256=hashlib.sha256(json.dumps(world.rng.getstate()).encode()).hexdigest()))
            on_food=sum(world.food[o.position]>0 for o in world.living.values())
            under_food=sum(world.food[o.position] for o in world.living.values())
            extinction,observations=None,{}
            peak,peak_tick=80,0
            with ExitStack() as stack:
                stream=stack.enter_context((args.output/(prefix+'.csv')).open('x',encoding='utf-8',newline=''))
                targets={kind:stack.enter_context((args.output/(prefix+'-'+kind+'.jsonl')).open('x',encoding='utf-8'))
                         for kind in ('feeding','terminal','energy')}
                writer=csv.DictWriter(stream,fieldnames=list(world.snapshot()));writer.writeheader()
                for tick in range(10001):
                    before=world.snapshot() if tick<=100 else None
                    actors=set(world.living) if tick<=100 else None
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
                    feeds=world.drain_feeding(); deaths=world.drain_pre_feeding_deaths(); ledgers=world.drain_energy()
                    if 1<=tick<=100:
                        if len(ledgers)!=len(actors) or {r['id'] for r in ledgers}!=actors:
                            raise ValueError('Early energy ledger actor coverage differs')
                        paid=sum(r[k] for r in ledgers for k in ('basal_paid','movement_paid','birth_paid'))
                        if paid!=row['dissipated_energy']-before['dissipated_energy']:
                            raise ValueError('Early energy payment total differs')
                        if sum(r['energy_after_action']+r['child_energy'] for r in ledgers)!=row['organism_energy']:
                            raise ValueError('Early ending energy differs')
                        if any(r['movement_paid'] for r in ledgers) or any(r['phase']=='movement' for r in deaths):
                            raise ValueError('Zero-charge movement caused dissipation or payment death')
                        if cost==0 and any(r['birth_paid'] for r in ledgers):
                            raise ValueError('Zero-charge birth dissipated energy')
                        for kind,rows in (('feeding',feeds),('terminal',deaths),('energy',ledgers)):
                            for observation in rows:
                                targets[kind].write(json.dumps(observation,separators=(',',':'))+'\n')
                    world.events.clear()
            results.append(dict(arm=arm,birth_threshold=threshold,movement_cost=0,birth_cost=cost,seed=seed,**row,**observations,
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
