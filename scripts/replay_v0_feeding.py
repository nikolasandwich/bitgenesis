"""Observe feeding on all campaign-017 first-100-tick prefixes, checking saved metrics."""

import argparse
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from bitgenesis.v0.engine import Config
from bitgenesis.v0.artifacts import write_json_atomic
from bitgenesis.v0.runner import provenance
from observe_v0_feeding import FeedingWorld


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=Path("data/campaign-017"))
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    vp=root/"docs/research/results/campaign-017-verification.json"
    verified=json.loads(vp.read_text(encoding="utf-8"))
    records=verified["runs"]
    if len(records)!=40 or {(r["arm"],r["birth_threshold"],r["seed"]) for r in records}!={
            (a,t,s) for a in ("dispersed","block") for t in (40,160) for s in range(1400,1410)}:
        raise ValueError("Expected all forty verified cases")
    metadata=dict(status="running",completed_runs=0,reference_campaign="017",window=[1,100],
        scope="Retrospective observation of all existing prefixes; no independent seed or causal mechanism claim.",
        verification_sha256=hashlib.sha256(vp.read_bytes()).hexdigest(),**provenance())
    if metadata["git_dirty"] is not False:
        raise ValueError("Commit source before observation replay")
    args.output.mkdir(parents=True,exist_ok=False)
    def save(name,value):write_json_atomic(args.output/name,value)
    save("metadata.json",metadata)
    results=[]
    try:
        for record in records:
            prefix=f"{record['arm']}-threshold-{record['birth_threshold']}-seed-{record['seed']}"
            ip=args.input/(prefix+"-initial.json");mp=args.input/(prefix+".csv")
            for p in (ip,mp):
                if hashlib.sha256(p.read_bytes()).hexdigest()!=verified["input_sha256"][p.name]:
                    raise ValueError("Input differs from verified campaign")
            initial=json.loads(ip.read_text(encoding="utf-8"))
            world=FeedingWorld(Config(**initial["config"]))
            world.food[:]=initial["food"];world.supplied_energy+=sum(world.food)
            for o in world.living.values():o.genome=250
            world.events.clear()
            if ([asdict(o) for o in world.living.values()]!=initial["founders"] or
                hashlib.sha256(json.dumps(world.rng.getstate()).encode()).hexdigest()!=initial["rng_sha256"]):
                raise ValueError("Initial founder/RNG replay differs")
            attempts=eaten=zero=0
            output=args.output/(prefix+"-feeding.jsonl")
            with mp.open(encoding="utf-8",newline="") as stream,output.open("x",encoding="utf-8") as target:
                reader=csv.DictReader(stream)
                for tick in range(101):
                    if tick:world.step()
                    row={k:None if v=="" else float(v) if k=="mean_genome" else int(v) for k,v in next(reader).items()}
                    if world.snapshot()!=row:raise ValueError(f"Metric replay differs at {prefix} tick {tick}")
                    for feeding in world.drain_feeding():
                        target.write(json.dumps(feeding,separators=(",",":"))+"\n")
                        attempts+=1;eaten+=feeding["eaten"];zero+=feeding["eaten"]==0
                    world.events.clear()
            if eaten!=record["food_eaten_by_100"]:raise ValueError("Observed intake differs from verified early total")
            results.append(dict(arm=record["arm"],birth_threshold=record["birth_threshold"],seed=record["seed"],
                feeding_attempts=attempts,zero_intake_attempts=zero,food_eaten=eaten,matched_metric_rows=101,
                feeding_sha256=hashlib.sha256(output.read_bytes()).hexdigest()))
            save("results.json",results);metadata["completed_runs"]=len(results);save("metadata.json",metadata)
        metadata["status"]="complete"
    except (Exception,KeyboardInterrupt) as error:
        metadata["status"]="interrupted" if isinstance(error,KeyboardInterrupt) else "failed"
        metadata["error"]=f"{type(error).__name__}: {error}"
        raise
    finally:save("metadata.json",metadata)
    print(json.dumps(dict(runs=len(results),metric_rows=sum(r["matched_metric_rows"] for r in results),
                         feeding_attempts=sum(r["feeding_attempts"] for r in results))))


if __name__=="__main__":main()
