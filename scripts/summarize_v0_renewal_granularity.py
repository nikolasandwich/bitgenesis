"""Independently verify campaign-020 initialization, metrics and observations."""

import argparse
import csv
import hashlib
from itertools import product
import json
from pathlib import Path

if __package__:
    from .summarize_v0_food_geometry import BASE, INITIAL, verify_initial as verify_geometry
else:
    from summarize_v0_food_geometry import BASE, INITIAL, verify_initial as verify_geometry


REGIMES = {"frequent-small": (60,1), "reference": (15,4), "rare-large": (5,12)}


def verify_initial(initial, arm, threshold, renewal, seed):
    if arm != "block" or threshold not in (40,160) or renewal not in REGIMES:
        raise ValueError("Undeclared treatment")
    probability, amount = REGIMES[renewal]
    expected={**BASE,"seed":seed,"initial_food":0,"regrowth_probability":probability,
              "regrowth_amount":amount,"mutation_probability":0,"birth_threshold":threshold,
              "movement_cost":0,"birth_cost":0}
    if (initial.get("birth_threshold") != threshold or initial.get("renewal") != renewal
            or initial.get("birth_cost") != 0 or initial.get("movement_cost") != 0
            or initial["config"] != expected):
        raise ValueError("Initial treatment/configuration differs")
    # Renewal settings do not consume construction draws; validate actual settings first.
    normalized={**initial,"config":{**expected,"birth_threshold":40,"movement_cost":1,
        "birth_cost":4,"regrowth_probability":15,"regrowth_amount":4}}
    return verify_geometry(normalized,arm,seed)


def verify_rows(rows, amount, steps=10000):
    if type(amount) is not int or amount not in (1,4,12):
        raise ValueError("Undeclared renewal packet")
    previous, extinction, count = None, None, 0
    for tick, row in enumerate(rows):
        count += 1
        if set(row) != set(INITIAL) or row["tick"] != tick:
            raise ValueError("Metric schema or tick sequence differs")
        if any(type(v) is not int or v < 0 for k,v in row.items() if k not in ("mean_genome","max_generation")):
            raise ValueError("Invalid integer metric")
        n = row["population"]
        if n != 80+row["births"]-row["deaths"] or not 0 <= n <= 1024:
            raise ValueError("Population accounting mismatch")
        if (row["food_energy"] > 24576 or row["organism_energy"] < n
                or row["organism_energy"]+row["food_energy"]+row["dissipated_energy"] != row["supplied_energy"]):
            raise ValueError("Energy accounting mismatch")
        if (row["mean_genome"] != (250 if n else None) or row["genome_variants"] != int(n>0)
                or not int(n>0) <= row["founder_lineages"] <= min(80,n)):
            raise ValueError("Fixed trait or founder bounds differ")
        if (n and (type(row["max_generation"]) is not int or row["max_generation"] < 0)) or (
                not n and (row["max_generation"] is not None or row["organism_energy"] != 0)):
            raise ValueError("Invalid living generation or extinct energy")
        if tick == 0:
            if row != INITIAL:
                raise ValueError("Initial metric differs")
        else:
            births, deaths = row["births"]-previous["births"], row["deaths"]-previous["deaths"]
            supply, dissipated = row["supplied_energy"]-previous["supplied_energy"], row["dissipated_energy"]-previous["dissipated_energy"]
            if (min(births,deaths,supply,dissipated) < 0 or births+deaths > previous["population"]
                    or supply > 1024*amount or dissipated != previous["population"]
                    or row["founder_lineages"] > previous["founder_lineages"]):
                raise ValueError("Per-tick transition bounds differ")
            if previous["population"] == 0 and n:
                raise ValueError("Population reappeared after extinction")
            if n and row["max_generation"] > previous["max_generation"]+1:
                raise ValueError("Generation jump")
        if previous is not None:
            uptake = row["supplied_energy"]-previous["supplied_energy"]+previous["food_energy"]-row["food_energy"]
            if not 0 <= uptake <= 8*previous["population"]:
                raise ValueError("Per-tick uptake bounds differ")
        if not n and extinction is None:
            extinction = tick
        previous = row
    if count != steps+1:
        raise ValueError("Truncated metric series")
    return {**previous,"extinction_tick":extinction,"right_censored":extinction is None}



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


def resource_checkpoints(rows):
    result={}
    for tick in (100,500,5000,10000):
        row=rows[tick]
        result[f"resources_added_by_{tick}"]=row["supplied_energy"]-7040
        result[f"cumulative_uptake_by_{tick}"]=row["supplied_energy"]-7040+5120-row["food_energy"]
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=Path("data/campaign-020"))
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    metadata=json.loads((args.input/"metadata.json").read_text(encoding="utf-8"))
    expected=dict(protocol="campaign-020-renewal-granularity-1",rules_version="v0-darwin-1",
        seeds=list(range(1700,1710)),arms=["block"],thresholds=[40,160],renewal_regimes={k:list(v) for k,v in REGIMES.items()},movement_cost=0,birth_cost=0,steps=10000,
        observation_schemas=dict(feeding=3,terminal=1,energy=1),
        early_window=[0,100],baseline_config=BASE,initial_food_energy=5120,initial_total_energy=7040,
        layout_seed_offset=1000000,founder_trait=250,nominal_supply_per_thousand=60,mutation_probability=0,
        status="complete",completed_runs=60)
    if any(metadata.get(k)!=v for k,v in expected.items()):
        raise ValueError("Expected complete preregistered campaign")
    if metadata.get("git_dirty") is not False:
        raise ValueError("Outcome source was not clean")
    protocol_path=Path(__file__).resolve().parents[1]/"experiments/v0/campaign-020.md"
    if metadata.get("protocol_sha256")!=hashlib.sha256(protocol_path.read_bytes()).hexdigest():
        raise ValueError("Protocol differs from registered source")
    records=json.loads((args.input/"results.json").read_text(encoding="utf-8"))
    indexed={(r["arm"],r["birth_threshold"],r["renewal"],r["seed"]):r for r in records}
    grid=list(product(expected["arms"],expected["thresholds"],expected["renewal_regimes"],expected["seeds"]))
    if len(records)!=60 or set(indexed)!=set(grid):
        raise ValueError("Incomplete or duplicate run grid")
    hashes,verified,founders,maps={},{},{},{}
    for arm,threshold,renewal,seed in grid:
        prefix=f"{arm}-threshold-{threshold}-renewal-{renewal}-seed-{seed}"
        initial_path=args.input/(prefix+"-initial.json")
        initial=json.loads(initial_path.read_text(encoding="utf-8"))
        exposure=verify_initial(initial,arm,threshold,renewal,seed)
        pair=(initial["founders"],initial["rng_sha256"])
        if seed in founders and founders[seed]!=pair:
            raise ValueError("Founder/RNG sextuplet differs")
        founders[seed]=pair
        if (arm,seed) in maps and maps[arm,seed]!=initial["food"]:
            raise ValueError("Threshold/renewal sextuplet initial maps differ")
        maps[arm,seed]=initial["food"]
        path=args.input/(prefix+".csv")
        with path.open(encoding="utf-8",newline="") as stream:
            rows=[{k:None if v=="" else float(v) if k=="mean_genome" else int(v)
                   for k,v in r.items()} for r in csv.DictReader(stream)]
        record=dict(arm=arm,birth_threshold=threshold,movement_cost=0,birth_cost=0,renewal=renewal,seed=seed,**verify_rows(rows,REGIMES[renewal][1]),
            population_at_500=rows[500]["population"],population_at_5000=rows[5000]["population"],
            **early_observations(rows),**resource_checkpoints(rows),**exposure)
        if record!=indexed[arm,threshold,renewal,seed]:
            raise ValueError("Saved result differs from reconstructed observations")
        verified[arm,threshold,renewal,seed]=record
        for p in (initial_path,path):
            hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    groups=[]
    for arm,threshold,renewal in product(expected["arms"],expected["thresholds"],expected["renewal_regimes"]):
        group=[verified[arm,threshold,renewal,seed] for seed in expected["seeds"]]
        deaths=[r["extinction_tick"] for r in group if r["extinction_tick"] is not None]
        groups.append(dict(arm=arm,birth_threshold=threshold,movement_cost=0,birth_cost=0,renewal=renewal,runs=10,
            alive_at_500=sum(r["population_at_500"]>0 for r in group),
            alive_at_5000=sum(r["population_at_5000"]>0 for r in group),
            alive_at_10000=sum(r["population"]>0 for r in group),
            extinct_only_range=[min(deaths),max(deaths)] if deaths else None,
            resource_ranges={k:[min(r[k] for r in group),max(r[k] for r in group)] for k in resource_checkpoints(rows)},
            early_ranges={k:[min(r[k] for r in group),max(r[k] for r in group)] for k in early_observations(rows)}))
    pairs=[]
    for arm,renewal,seed in product(expected['arms'],expected['renewal_regimes'],expected['seeds']):
        low,high=verified[arm,40,renewal,seed],verified[arm,160,renewal,seed]
        status=('both_alive' if high['population'] else 'low_only') if low['population'] else ('high_only' if high['population'] else 'both_extinct')
        pairs.append(dict(arm=arm,movement_cost=0,birth_cost=0,renewal=renewal,seed=seed,status=status,
            low_population=low['population'],high_population=high['population']))
    renewal_pairs=[]
    for threshold,renewal,seed in product((40,160),("frequent-small","rare-large"),expected["seeds"]):
        treatment,reference=verified["block",threshold,renewal,seed],verified["block",threshold,"reference",seed]
        status=("both_alive" if reference["population"] else "treatment_only") if treatment["population"] else ("reference_only" if reference["population"] else "both_extinct")
        renewal_pairs.append(dict(birth_threshold=threshold,renewal=renewal,seed=seed,status=status,
            treatment_population=treatment["population"],reference_population=reference["population"]))
    with (args.input/"results.csv").open(encoding="utf-8",newline="") as stream:
        csv_records=list(csv.DictReader(stream))
    expected_csv=[{k:"" if v is None else str(v) for k,v in r.items()} for r in records]
    if csv_records != expected_csv:
        raise ValueError("CSV results differ from JSON results")
    hashes["results.csv"]=hashlib.sha256((args.input/"results.csv").read_bytes()).hexdigest()
    hashes["results.json"]=hashlib.sha256((args.input/"results.json").read_bytes()).hexdigest()
    report=dict(renewal_pairs=renewal_pairs,threshold_pairs=pairs,scope="Initial construction and pairing; metric accounting and predeclared observations. Early observer/energy records require a separate verifier; no independent dynamic replay or unique causal mediation claim.",
        metric_rows_checked=600060,initial_states_checked=60,matched_seed_sextuplets=10,
        matched_threshold_renewal_map_sextuplets=10,uptake_transitions_checked=600000,runs=list(verified.values()),groups=groups,
        input_sha256=hashes,metadata_sha256=hashlib.sha256((args.input/"metadata.json").read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        geometry_helper_sha256=hashlib.sha256(Path(__file__).with_name("summarize_v0_food_geometry.py").read_bytes()).hexdigest())
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/"summary.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(groups,indent=2))


if __name__=="__main__":
    main()
