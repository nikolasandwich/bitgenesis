"""Replay complete energy ledgers on all campaign-017 first-100-tick prefixes."""

import argparse
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from bitgenesis.v0.engine import Config
from bitgenesis.v0.artifacts import write_json_atomic
from bitgenesis.v0.runner import provenance
from scripts.observe_v0_energy import EnergyWorld


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
    metadata=dict(status="running",completed_runs=0,reference_campaign="017",window=[1,100],feeding_schema=3,terminal_schema=1,energy_schema=1,
        scope="Retrospective observation of all existing prefixes; no independent seed or causal mechanism claim.",
        verification_sha256=hashlib.sha256(vp.read_bytes()).hexdigest(),**provenance())
    if metadata["git_dirty"] is not False:
        raise ValueError("Commit source before observation replay")
    args.output.mkdir(parents=True,exist_ok=False)
    def save(name,value):write_json_atomic(args.output/name,value)
    save("metadata.json",metadata)
    previous=json.loads((root/"docs/research/results/action-replay-017.json").read_text(encoding="utf-8"))["results"]
    old_index={(r["arm"],r["birth_threshold"],r["seed"]):r for r in previous}
    results=[]
    try:
        for record in records:
            prefix=f"{record['arm']}-threshold-{record['birth_threshold']}-seed-{record['seed']}"
            ip=args.input/(prefix+"-initial.json");mp=args.input/(prefix+".csv")
            for p in (ip,mp):
                if hashlib.sha256(p.read_bytes()).hexdigest()!=verified["input_sha256"][p.name]:
                    raise ValueError("Input differs from verified campaign")
            initial=json.loads(ip.read_text(encoding="utf-8"))
            world=EnergyWorld(Config(**initial["config"]))
            world.food[:]=initial["food"];world.supplied_energy+=sum(world.food)
            for o in world.living.values():o.genome=250
            world.events.clear()
            if ([asdict(o) for o in world.living.values()]!=initial["founders"] or
                hashlib.sha256(json.dumps(world.rng.getstate()).encode()).hexdigest()!=initial["rng_sha256"]):
                raise ValueError("Initial founder/RNG replay differs")
            attempts=eaten=zero=death_count=energy_count=0
            output=args.output/(prefix+"-feeding.jsonl")
            death_output=args.output/(prefix+"-terminal.jsonl")
            energy_output=args.output/(prefix+"-energy.jsonl")
            with mp.open(encoding="utf-8",newline="") as stream,output.open("x",encoding="utf-8") as target,death_output.open("x",encoding="utf-8") as death_target,energy_output.open("x",encoding="utf-8") as energy_target:
                reader=csv.DictReader(stream)
                for tick in range(101):
                    before_ids=set(world.living)
                    before=world.snapshot()
                    if tick:world.step()
                    row={k:None if v=="" else float(v) if k=="mean_genome" else int(v) for k,v in next(reader).items()}
                    if world.snapshot()!=row:raise ValueError(f"Metric replay differs at {prefix} tick {tick}")
                    feeding_rows=world.drain_feeding();terminal_rows=world.drain_pre_feeding_deaths()
                    energy_rows=world.drain_energy()
                    if tick:
                        feed_ids={r["id"] for r in feeding_rows};dead_ids={r["id"] for r in terminal_rows}
                        if feed_ids & dead_ids or feed_ids | dead_ids != before_ids or len(feed_ids)!=len(feeding_rows) or len(dead_ids)!=len(terminal_rows):
                            raise ValueError("Observer does not partition all active individuals")
                    if tick:
                        if len(energy_rows)!=len(before_ids) or {r['id'] for r in energy_rows}!=before_ids:
                            raise ValueError('Energy ledger omits or duplicates actors')
                        paid=sum(r[k] for r in energy_rows for k in ('basal_paid','movement_paid','birth_paid'))
                        if paid!=row['dissipated_energy']-before['dissipated_energy']:
                            raise ValueError('Energy ledger costs differ from global accounting')
                        if sum(r['energy_after_action']+r['child_energy'] for r in energy_rows)!=row['organism_energy']:
                            raise ValueError('Energy ledger ending stocks differ')
                        if sum(r['eaten'] for r in energy_rows)!=sum(r['eaten'] for r in feeding_rows):
                            raise ValueError('Energy ledger intake differs')
                    for energy in energy_rows:
                        energy_target.write(json.dumps(energy,separators=(',',':'))+'\n')
                        energy_count+=1
                    for terminal in terminal_rows:
                        death_target.write(json.dumps(terminal,separators=(",",":"))+"\n")
                        death_count+=1
                    for feeding in feeding_rows:
                        target.write(json.dumps(feeding,separators=(",",":"))+"\n")
                        attempts+=1;eaten+=feeding["eaten"];zero+=feeding["eaten"]==0
                    world.events.clear()
            if eaten!=record["food_eaten_by_100"]:raise ValueError("Observed intake differs from verified early total")
            old=old_index[record['arm'],record['birth_threshold'],record['seed']]
            for p,kind in ((output,'feeding'),(death_output,'terminal')):
                if hashlib.sha256(p.read_bytes()).hexdigest()!=old[kind+'_sha256']:
                    raise ValueError('Old observation stream changed')
            results.append(dict(arm=record["arm"],birth_threshold=record["birth_threshold"],seed=record["seed"],
                feeding_attempts=attempts,zero_intake_attempts=zero,food_eaten=eaten,matched_metric_rows=101,
                feeding_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                energy_records=energy_count,energy_sha256=hashlib.sha256(energy_output.read_bytes()).hexdigest(),
                pre_feeding_deaths=death_count,terminal_sha256=hashlib.sha256(death_output.read_bytes()).hexdigest()))
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
