"""Conditional follow-up of all four campaign-014 neutral two-group endpoints."""

import argparse
import csv
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path

from bitgenesis.v0.artifacts import write_json_atomic
from bitgenesis.v0.engine import World
from bitgenesis.v0.runner import load_config, provenance


CASES = [(1,72,1206),(2,8,1200),(2,72,1208),(4,72,1208)]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--reference",type=Path,default=Path("data/campaign-014"))
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    verified=json.loads((root/"docs/research/results/campaign-014-verification.json").read_text(encoding="utf-8"))
    selected=[(r["movement_cost"],r["initial_b"],r["seed"]) for r in verified["runs"]
              if r["treatment"]=="neutral" and r["a"]>0 and r["b"]>0]
    if selected!=CASES:
        raise ValueError("Conditional reference cohort differs")
    base=load_config(root/"experiments/v0/darwin-baseline.toml")
    metadata={"protocol":"campaign-015-neutral-followup-1","rules_version":"v0-darwin-1",
        "steps":30000,"reference_prefix_ticks":3000,"cases":CASES,"baseline_config":asdict(base),
        "reference_sha256":{},"completed_runs":0,"status":"running",**provenance()}
    args.output.mkdir(parents=True,exist_ok=False)
    def save(name,value):
        write_json_atomic(args.output/name,value)
    save("metadata.json",metadata)
    results=[]
    try:
        for cost,initial_b,seed in CASES:
            filename=f"cost-{cost}-b-{initial_b}-neutral-seed-{seed}.csv"
            prior=args.reference/filename
            digest=hashlib.sha256(prior.read_bytes()).hexdigest()
            if digest!=verified["input_sha256"][filename]:
                raise ValueError("Reference differs from verified campaign")
            metadata["reference_sha256"][filename]=digest
            with prior.open(encoding="utf-8",newline="") as stream:
                prefix=[{k:None if v=="" else float(v) if k in ("mean_genome","b_fraction") else int(v)
                         for k,v in r.items()} for r in csv.DictReader(stream)]
            if len(prefix)!=3001:
                raise ValueError("Truncated reference")
            world=World(replace(base,seed=seed,movement_cost=cost,mutation_probability=0))
            for organism in world.living.values():
                organism.genome=250
            world.events.clear()
            losses={"a_loss_tick":None,"b_loss_tick":None,"extinction_tick":None}
            observations={}
            with (args.output/filename).open("w",encoding="utf-8",newline="") as stream:
                writer=None
                for tick in range(30001):
                    if tick:
                        world.step()
                    world.check_invariants()
                    n=len(world.living)
                    b=sum(o.founder_id<initial_b for o in world.living.values())
                    row={**world.snapshot(),"a":n-b,"b":b,"b_fraction":b/n if n else None}
                    if tick<=3000 and row!=prefix[tick]:
                        raise ValueError(f"Historical prefix differs: {filename} at {tick}")
                    if writer is None:
                        writer=csv.DictWriter(stream,fieldnames=list(row))
                        writer.writeheader()
                    writer.writerow(row)
                    for field,key in (("a","a_loss_tick"),("b","b_loss_tick"),("population","extinction_tick")):
                        if losses[key] is None and row[field]==0:
                            losses[key]=tick
                    if tick in (3000,10000,30000):
                        observations[str(tick)]=row.copy()
                    world.events.clear()
            result={"movement_cost":cost,"initial_b":initial_b,"treatment":"neutral","b_trait":250,
                    "seed":seed,**row,**losses,"observations":observations}
            results.append(result)
            save("results.json",results)
            metadata["completed_runs"]=len(results)
            save("metadata.json",metadata)
            print(f"cost={cost} seed={seed} initial_b={initial_b}: A={row['a']} B={row['b']} losses={losses}",flush=True)
        with (args.output/"results.csv").open("w",encoding="utf-8",newline="") as stream:
            compact=[{k:v for k,v in r.items() if k!="observations"} for r in results]
            writer=csv.DictWriter(stream,fieldnames=list(compact[0]))
            writer.writeheader()
            writer.writerows(compact)
        metadata["status"]="complete"
    except (Exception,KeyboardInterrupt) as error:
        metadata["status"]="interrupted" if isinstance(error,KeyboardInterrupt) else "failed"
        metadata["error"]=f"{type(error).__name__}: {error}"
        raise
    finally:
        save("metadata.json",metadata)


if __name__=="__main__":
    main()
