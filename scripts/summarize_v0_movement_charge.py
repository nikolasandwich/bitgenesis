"""Independently verify campaign-018 initialization, metrics and observations."""

import argparse
import csv
import hashlib
from itertools import product
import json
from pathlib import Path

if __package__:
    from .summarize_v0_food_geometry import BASE, verify_initial as verify_geometry, verify_rows as verify_geometry_rows
else:
    from summarize_v0_food_geometry import BASE, verify_initial as verify_geometry, verify_rows as verify_geometry_rows


def verify_initial(initial, arm, threshold, cost, seed):
    if threshold not in (40,160) or initial.get("birth_threshold") != threshold:
        raise ValueError("Initial threshold differs")
    if cost not in (0,1) or initial.get("movement_cost")!=cost:
        raise ValueError("Initial movement cost differs")
    expected={**BASE,"seed":seed,"initial_food":0,"regrowth_probability":15,
              "mutation_probability":0,"birth_threshold":threshold,"movement_cost":cost}
    if initial["config"]!=expected:
        raise ValueError("Initial configuration differs")
    # Threshold and movement cost do not affect construction. Reuse the existing independent
    # map/founder/RNG verifier after explicitly checking the real configuration.
    normalized={**initial,"config":{**expected,"birth_threshold":40,"movement_cost":1}}
    return verify_geometry(normalized,arm,seed)



def verify_rows(rows, cost, steps=10000):
    result=verify_geometry_rows(rows,steps)
    if cost==0:
        for previous,current in zip(rows,rows[1:]):
            births=current['births']-previous['births']
            if current['dissipated_energy']-previous['dissipated_energy']!=previous['population']+4*births:
                raise ValueError('Zero-charge dissipation differs from basal plus birth costs')
    return result


def early_observations(rows):
    if len(rows)<101 or [r["tick"] for r in rows[:101]]!=list(range(101)):
        raise ValueError("Incomplete early window")
    peak=max(rows[:101],key=lambda r:r["population"])
    eaten=0
    for previous,current in zip(rows[:100],rows[1:101]):
        delta=current["supplied_energy"]-previous["supplied_energy"]+previous["food_energy"]-current["food_energy"]
        if not 0<=delta<=8*previous["population"] or delta != (
                current["organism_energy"]-previous["organism_energy"]+
                current["dissipated_energy"]-previous["dissipated_energy"]):
            raise ValueError("Invalid early food uptake")
        eaten+=delta
    return dict(population_at_100=rows[100]["population"],births_at_100=rows[100]["births"],
        early_peak_population=peak["population"],first_peak_tick=peak["tick"],
        food_eaten_by_100=eaten,food_at_100=rows[100]["food_energy"],
        organism_energy_at_100=rows[100]["organism_energy"])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=Path("data/campaign-018"))
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    metadata=json.loads((args.input/"metadata.json").read_text(encoding="utf-8"))
    expected=dict(protocol="campaign-018-movement-charge-1",rules_version="v0-darwin-1",
        seeds=list(range(1500,1510)),arms=["dispersed","block"],thresholds=[40,160],movement_costs=[0,1],steps=10000,
        observation_schemas=dict(feeding=3,terminal=1,energy=1),
        early_window=[0,100],baseline_config=BASE,initial_food_energy=5120,initial_total_energy=7040,
        layout_seed_offset=1000000,founder_trait=250,regrowth_probability=15,mutation_probability=0,
        status="complete",completed_runs=80)
    if any(metadata.get(k)!=v for k,v in expected.items()):
        raise ValueError("Expected complete preregistered campaign")
    if metadata.get("git_dirty") is not False:
        raise ValueError("Outcome source was not clean")
    protocol_path=Path(__file__).resolve().parents[1]/"experiments/v0/campaign-018.md"
    if metadata.get("protocol_sha256")!=hashlib.sha256(protocol_path.read_bytes()).hexdigest():
        raise ValueError("Protocol differs from registered source")
    records=json.loads((args.input/"results.json").read_text(encoding="utf-8"))
    indexed={(r["arm"],r["birth_threshold"],r["movement_cost"],r["seed"]):r for r in records}
    grid=list(product(expected["arms"],expected["thresholds"],expected["movement_costs"],expected["seeds"]))
    if len(records)!=80 or set(indexed)!=set(grid):
        raise ValueError("Incomplete or duplicate run grid")
    hashes,verified,founders,maps={},{},{},{}
    for arm,threshold,cost,seed in grid:
        prefix=f"{arm}-threshold-{threshold}-move-cost-{cost}-seed-{seed}"
        initial_path=args.input/(prefix+"-initial.json")
        initial=json.loads(initial_path.read_text(encoding="utf-8"))
        exposure=verify_initial(initial,arm,threshold,cost,seed)
        pair=(initial["founders"],initial["rng_sha256"])
        if seed in founders and founders[seed]!=pair:
            raise ValueError("Founder/RNG octuplet differs")
        founders[seed]=pair
        if (arm,seed) in maps and maps[arm,seed]!=initial["food"]:
            raise ValueError("Threshold/cost quartet initial maps differ")
        maps[arm,seed]=initial["food"]
        path=args.input/(prefix+".csv")
        with path.open(encoding="utf-8",newline="") as stream:
            rows=[{k:None if v=="" else float(v) if k=="mean_genome" else int(v)
                   for k,v in r.items()} for r in csv.DictReader(stream)]
        record=dict(arm=arm,birth_threshold=threshold,movement_cost=cost,seed=seed,**verify_rows(rows,cost),
            population_at_500=rows[500]["population"],population_at_5000=rows[5000]["population"],
            **early_observations(rows),**exposure)
        if record!=indexed[arm,threshold,cost,seed]:
            raise ValueError("Saved result differs from reconstructed observations")
        verified[arm,threshold,cost,seed]=record
        for p in (initial_path,path):
            hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    groups=[]
    for arm,threshold,cost in product(expected["arms"],expected["thresholds"],expected["movement_costs"]):
        group=[verified[arm,threshold,cost,seed] for seed in expected["seeds"]]
        deaths=[r["extinction_tick"] for r in group if r["extinction_tick"] is not None]
        groups.append(dict(arm=arm,birth_threshold=threshold,movement_cost=cost,runs=10,
            alive_at_500=sum(r["population_at_500"]>0 for r in group),
            alive_at_5000=sum(r["population_at_5000"]>0 for r in group),
            alive_at_10000=sum(r["population"]>0 for r in group),
            extinct_only_range=[min(deaths),max(deaths)] if deaths else None,
            early_ranges={k:[min(r[k] for r in group),max(r[k] for r in group)] for k in early_observations(rows)}))
    pairs=[]
    for arm,cost,seed in product(expected['arms'],expected['movement_costs'],expected['seeds']):
        low,high=verified[arm,40,cost,seed],verified[arm,160,cost,seed]
        status=('both_alive' if high['population'] else 'low_only') if low['population'] else ('high_only' if high['population'] else 'both_extinct')
        pairs.append(dict(arm=arm,movement_cost=cost,seed=seed,status=status,
            low_population=low['population'],high_population=high['population']))
    report=dict(threshold_pairs=pairs,scope="Initial construction and pairing; metric accounting and predeclared observations. Early observer/energy records require a separate verifier; no independent dynamic replay or unique causal mediation claim.",
        metric_rows_checked=800080,initial_states_checked=80,matched_seed_octuplets=10,
        matched_threshold_cost_map_quartets=20,early_uptake_transitions_checked=8000,runs=list(verified.values()),groups=groups,
        input_sha256=hashes,metadata_sha256=hashlib.sha256((args.input/"metadata.json").read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        geometry_helper_sha256=hashlib.sha256(Path(__file__).with_name("summarize_v0_food_geometry.py").read_bytes()).hexdigest())
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/"summary.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(groups,indent=2))


if __name__=="__main__":
    main()
