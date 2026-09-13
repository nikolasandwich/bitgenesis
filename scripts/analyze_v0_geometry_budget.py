"""Retrospective first-100-tick food uptake and energy accounting for campaign 016."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

if __package__:
    from .analyze_v0_energy_budget import budget
else:
    from analyze_v0_energy_budget import budget


def uptake(rows):
    """Reconstruct feeding under V0: food changes only through regrowth and feeding."""
    total = 0
    for previous,current in zip(rows,rows[1:]):
        supplied = current["supplied_energy"]-previous["supplied_energy"]
        eaten = supplied+previous["food_energy"]-current["food_energy"]
        if supplied < 0 or not 0 <= eaten <= previous["population"]*8:
            raise ValueError("Food uptake outside V0 feeding bounds")
        if current["organism_energy"]-previous["organism_energy"] != eaten-(
                current["dissipated_energy"]-previous["dissipated_energy"]):
            raise ValueError("Food uptake differs from organism energy accounting")
        total += eaten
    return total


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    root=Path(__file__).resolve().parents[1]
    parser.add_argument("--input",type=Path,default=root/"data/campaign-016")
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    verification_path=root/"docs/research/results/campaign-016-verification.json"
    verification=json.loads(verification_path.read_text(encoding="utf-8"))
    metadata_path=args.input/"metadata.json"
    if hashlib.sha256(metadata_path.read_bytes()).hexdigest()!=verification["metadata_sha256"]:
        raise ValueError("Campaign metadata differs from verified input")
    metadata=json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata["baseline_config"]["basal_cost"]!=1 or metadata["baseline_config"]["birth_cost"]!=4 or metadata["baseline_config"]["feeding_rate"]!=8:
        raise ValueError("Unexpected energy rules")
    records,hashes=[],{}
    for arm in ("uniform","dispersed","block"):
        for seed in range(1300,1310):
            path=args.input/f"{arm}-seed-{seed}.csv"
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            if digest!=verification["input_sha256"][path.name]:
                raise ValueError("Metrics differ from verified input")
            with path.open(encoding="utf-8",newline="") as stream:
                rows=[{k:None if v=="" else float(v) if k=="mean_genome" else int(v)
                       for k,v in r.items()} for r in csv.DictReader(stream)]
            if len(rows)!=10001:
                raise ValueError("Incomplete metrics")
            totals=budget(rows,0,100)
            eaten=uptake(rows[:101])
            peak=max(rows[:101],key=lambda r:r["population"])
            records.append(dict(arm=arm,seed=seed,food_eaten=eaten,**totals,
                population_at_100=rows[100]["population"],births_at_100=rows[100]["births"],
                food_at_100=rows[100]["food_energy"],organism_energy_at_100=rows[100]["organism_energy"],
                peak_population=peak["population"],first_peak_tick=peak["tick"]))
            hashes[path.name]=digest
    groups=[]
    for arm in ("uniform","dispersed","block"):
        group=[r for r in records if r["arm"]==arm]
        groups.append(dict(arm=arm,**{k:[min(r[k] for r in group),max(r[k] for r in group)]
                                     for k in group[0] if k not in ("arm","seed")}))
    report=dict(scope="Retrospective ticks 1–100, not preregistered. Aggregate food and energy accounting, not individual paths, deprivation or causal mediation. No new world executions.",
        records=records,groups=groups,input_sha256=hashes,metric_rows_hash_covered=300030,
        uptake_transitions_checked=3000,verification_sha256=hashlib.sha256(verification_path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        budget_helper_sha256=hashlib.sha256(Path(__file__).with_name("analyze_v0_energy_budget.py").read_bytes()).hexdigest())
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/"summary.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    with (args.output/"budgets.csv").open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    print(json.dumps(groups,indent=2))


if __name__=="__main__":
    main()
