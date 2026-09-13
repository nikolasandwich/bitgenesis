"""Verify campaign-016 initialization and metric records without stepping the engine."""

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import random


BASE = dict(seed=42,width=32,height=32,initial_population=80,initial_energy=24,
    initial_food=8,food_capacity=24,regrowth_probability=40,regrowth_amount=4,
    feeding_rate=8,basal_cost=1,movement_cost=1,birth_threshold=40,birth_cost=4,
    mutation_probability=100,mutation_step=100)
INITIAL = dict(tick=0,population=80,births=0,deaths=0,organism_energy=1920,
    food_energy=5120,supplied_energy=7040,dissipated_energy=0,mean_genome=250.0,
    genome_variants=1,founder_lineages=80,max_generation=0)


def verify_initial(initial, arm, seed):
    expected_config = {**BASE,"seed":seed,"initial_food":0,"regrowth_probability":15,"mutation_probability":0}
    if (initial["arm"] != arm or initial["seed"] != seed or initial["config"] != expected_config
            or initial["snapshot"] != INITIAL):
        raise ValueError("Initial identity/config/snapshot differs")
    food = initial["food"]
    if len(food) != 1024 or any(type(v) is not int or not 0 <= v <= 24 for v in food) or sum(food) != 5120:
        raise ValueError("Invalid initial food energy or bounds")
    layout = random.Random(1000000+seed)
    if arm == "uniform":
        expected_food = [5]*1024
    else:
        if Counter(food) != {0:810,8:1,24:213}:
            raise ValueError("Concentrated food multiset differs")
        if arm == "dispersed":
            order = list(range(1024))
            layout.shuffle(order)
        elif arm == "block":
            offset_x, offset_y = layout.randrange(32), layout.randrange(32)
            order = [((y+offset_y)%32)*32+(x+offset_x)%32 for y in range(32) for x in range(32)]
        else:
            raise ValueError("Unknown food geometry")
        expected_food = [0]*1024
        for rank, position in enumerate(order[:214]):
            expected_food[position] = 24 if rank < 213 else 8
    if food != expected_food:
        raise ValueError("Food layout differs from declared construction")
    rng = random.Random(seed)
    positions = rng.sample(range(1024),80)
    expected_founders = []
    for identity, position in enumerate(positions):
        rng.randrange(1001)  # Preserved founding draw, then overwritten by assay.
        expected_founders.append(dict(id=identity,parent_id=None,founder_id=identity,generation=0,
            birth_tick=0,genome=250,position=position,energy=24,offspring=0,death_tick=None))
    digest = hashlib.sha256(json.dumps(rng.getstate()).encode()).hexdigest()
    if initial["founders"] != expected_founders or initial["rng_sha256"] != digest:
        raise ValueError("Founder placement or initial world RNG differs")
    return dict(founders_on_food=sum(food[p]>0 for p in positions),food_under_founders=sum(food[p] for p in positions))


def verify_rows(rows, steps=10000):
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
                    or supply > 4096 or not previous["population"]+4*births <= dissipated <= 2*previous["population"]+4*births
                    or row["founder_lineages"] > previous["founder_lineages"]):
                raise ValueError("Per-tick transition bounds differ")
            if previous["population"] == 0 and n:
                raise ValueError("Population reappeared after extinction")
            if n and row["max_generation"] > previous["max_generation"]+1:
                raise ValueError("Generation jump")
        if not n and extinction is None:
            extinction = tick
        previous = row
    if count != steps+1:
        raise ValueError("Truncated metric series")
    return {**previous,"extinction_tick":extinction,"right_censored":extinction is None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=Path("data/campaign-016"))
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    metadata = json.loads((args.input/"metadata.json").read_text(encoding="utf-8"))
    expected = dict(protocol="campaign-016-food-geometry-1",rules_version="v0-darwin-1",steps=10000,
        seeds=list(range(1300,1310)),arms=["uniform","dispersed","block"],initial_food_energy=5120,
        initial_total_energy=7040,layout_seed_offset=1000000,founder_trait=250,regrowth_probability=15,
        mutation_probability=0,baseline_config=BASE,status="complete",completed_runs=30)
    if any(metadata.get(k) != v for k,v in expected.items()):
        raise ValueError("Expected complete preregistered campaign")
    records = json.loads((args.input/"results.json").read_text(encoding="utf-8"))
    indexed = {(r["arm"],r["seed"]):r for r in records}
    if len(records) != 30 or set(indexed) != {(a,s) for a in expected["arms"] for s in expected["seeds"]}:
        raise ValueError("Incomplete or duplicate run grid")
    hashes, verified, groups, paired = {}, [], [], {}
    for arm in expected["arms"]:
        group = []
        for seed in expected["seeds"]:
            initial_path = args.input/f"{arm}-seed-{seed}-initial.json"
            initial = json.loads(initial_path.read_text(encoding="utf-8"))
            exposure = verify_initial(initial,arm,seed)
            pairing = (initial["founders"],initial["rng_sha256"])
            if seed in paired and pairing != paired[seed]:
                raise ValueError("Cross-arm initial pairing differs")
            paired[seed] = pairing
            path = args.input/f"{arm}-seed-{seed}.csv"
            with path.open(encoding="utf-8",newline="") as stream:
                rows = [{k:None if v=="" else float(v) if k=="mean_genome" else int(v)
                         for k,v in r.items()} for r in csv.DictReader(stream)]
            row = dict(arm=arm,seed=seed,**verify_rows(rows),population_at_500=rows[500]["population"],
                       population_at_5000=rows[5000]["population"],**exposure)
            if row != indexed[arm,seed]:
                raise ValueError("Saved summary differs from raw records")
            verified.append(row)
            group.append(row)
            for p in (initial_path,path):
                hashes[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
        deaths = [r["extinction_tick"] for r in group if r["extinction_tick"] is not None]
        groups.append(dict(arm=arm,runs=10,alive_at_500=sum(r["population_at_500"]>0 for r in group),
            alive_at_5000=sum(r["population_at_5000"]>0 for r in group),alive_at_10000=sum(r["population"]>0 for r in group),
            extinct_only_range=[min(deaths),max(deaths)] if deaths else None))
    args.output.mkdir(parents=True,exist_ok=False)
    report = dict(scope="Declared initial geometry, founder/RNG pairing and metric consistency; no full individual history, exact dynamic replay or general causal claim.",
        metric_rows_checked=300030,initial_states_checked=30,matched_seed_triplets=10,runs=verified,groups=groups,
        input_sha256=hashes,metadata_sha256=hashlib.sha256((args.input/"metadata.json").read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (args.output/"summary.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(groups,indent=2))


if __name__ == "__main__":
    main()
