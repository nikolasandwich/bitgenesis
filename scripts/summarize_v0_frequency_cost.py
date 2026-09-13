"""Independently check campaign-014 group and metric series before summarizing."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


def verify_rows(rows, initial_b, b_trait, movement_cost, steps=3000):
    losses = {"a_loss_tick": None, "b_loss_tick": None, "extinction_tick": None}
    previous = None
    count = 0
    for tick, row in enumerate(rows):
        count += 1
        n, a, b = row["population"], row["a"], row["b"]
        integer_fields = set(row) - {"mean_genome", "b_fraction", "max_generation"}
        if (any(type(row[k]) is not int or row[k] < 0 for k in integer_fields)
                or row["tick"] != tick or tick > steps):
            raise ValueError("Invalid integer metric or tick sequence")
        if n != a+b or n > 1024 or n != 80+row["births"]-row["deaths"]:
            raise ValueError("Group/population accounting mismatch")
        if (row["food_energy"] > 24576 or row["organism_energy"] < n
                or row["organism_energy"]+row["food_energy"]+row["dissipated_energy"] != row["supplied_energy"]):
            raise ValueError("Energy accounting or resource bounds")
        expected_mean = (250*a+b_trait*b)/n if n else None
        expected_fraction = b/n if n else None
        for key, expected in (("mean_genome", expected_mean), ("b_fraction", expected_fraction)):
            if ((expected is None and row[key] is not None) or (expected is not None
                    and (row[key] is None or not math.isclose(row[key], expected, rel_tol=0, abs_tol=1e-9)))):
                raise ValueError("Trait/group fraction mismatch")
        variants = len(({250} if a else set()) | ({b_trait} if b else set()))
        if row["genome_variants"] != variants:
            raise ValueError("Group traits disagree with diversity")
        if not (int(a>0)+int(b>0) <= row["founder_lineages"] <= min(80,n)):
            raise ValueError("Founder lineage bounds")
        if n and (type(row["max_generation"]) is not int or row["max_generation"] < 0):
            raise ValueError("Invalid living generation")
        if not n and (row["organism_energy"] or row["max_generation"] is not None):
            raise ValueError("Extinct world retains living metrics")
        if tick == 0:
            if (n, a, b, row["births"], row["deaths"], row["organism_energy"], row["food_energy"],
                    row["supplied_energy"], row["dissipated_energy"], row["founder_lineages"], row["max_generation"]) != (
                    80, 80-initial_b, initial_b, 0, 0, 1920, 8192, 10112, 0, 80, 0):
                raise ValueError("Initial state differs from protocol")
        else:
            if any(row[k] < previous[k] for k in ("births", "deaths", "supplied_energy", "dissipated_energy")):
                raise ValueError("Cumulative metric decreased")
            births, deaths = row["births"]-previous["births"], row["deaths"]-previous["deaths"]
            if (births+deaths > previous["population"]
                    or row["supplied_energy"]-previous["supplied_energy"] > 4096
                    or not previous["population"]+4*births <= row["dissipated_energy"]-previous["dissipated_energy"] <= (1+movement_cost)*previous["population"]+4*births
                    or row["founder_lineages"] > previous["founder_lineages"]
                    or (n and row["max_generation"] > previous["max_generation"]+1)):
                raise ValueError("Per-tick transition bounds")
            if any(previous[k] == 0 and row[k] != 0 for k in ("a", "b", "population")):
                raise ValueError("Lost group reappeared")
        for key, field in (("a_loss_tick", "a"), ("b_loss_tick", "b"), ("extinction_tick", "population")):
            if losses[key] is None and row[field] == 0:
                losses[key] = tick
        previous = row
    if count != steps+1:
        raise ValueError("Truncated metric series")
    return {**previous, **losses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/campaign-014"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    metadata = json.loads((args.input/"metadata.json").read_text(encoding="utf-8"))
    expected_metadata = {"status": "complete", "protocol": "campaign-014-frequency-cost-1", "rules_version": "v0-darwin-1",
        "completed_runs": 160, "steps": 3000, "seeds": list(range(1200,1210)), "initial_b_counts": [8,72], "movement_costs": [1,2,3,4]}
    if any(metadata.get(k) != v for k,v in expected_metadata.items()):
        raise ValueError("Expected complete preregistered campaign 014")
    fixed = dict(seed=42,width=32,height=32,initial_population=80,initial_energy=24,initial_food=8,
        food_capacity=24,regrowth_probability=40,regrowth_amount=4,feeding_rate=8,basal_cost=1,
        movement_cost=1,birth_threshold=40,birth_cost=4,mutation_probability=100,mutation_step=100)
    if metadata["baseline_config"] != fixed:
        raise ValueError("Baseline differs from protocol")
    results = json.loads((args.input/"results.json").read_text(encoding="utf-8"))
    indexed = {(r["movement_cost"],r["initial_b"],r["treatment"],r["seed"]):r for r in results}
    expected = {(c,b,t,s) for c in (1,2,3,4) for b in (8,72) for t in ("competition","neutral") for s in range(1200,1210)}
    if len(results) != 160 or set(indexed) != expected:
        raise ValueError("Incomplete or duplicate run grid")
    hashes, verified, groups = {}, [], []
    for cost in (1,2,3,4):
        for initial_b in (8,72):
            for treatment,b_trait in (("competition",1000),("neutral",250)):
                outcomes = dict(a_only=0,b_only=0,both_present=0,extinct=0)
                for seed in range(1200,1210):
                    path=args.input/f"cost-{cost}-b-{initial_b}-{treatment}-seed-{seed}.csv"
                    with path.open(encoding="utf-8",newline="") as stream:
                        rows = [{k:None if v=="" else float(v) if k in ("mean_genome","b_fraction") else int(v)
                                 for k,v in r.items()} for r in csv.DictReader(stream)]
                    record = {"movement_cost":cost,"initial_b":initial_b,"treatment":treatment,"b_trait":b_trait,"seed":seed,
                              **verify_rows(rows,initial_b,b_trait,cost)}
                    if record != indexed[cost,initial_b,treatment,seed]:
                        raise ValueError("Summary differs from raw series")
                    outcome = "extinct" if not record["population"] else "a_only" if not record["b"] else "b_only" if not record["a"] else "both_present"
                    outcomes[outcome]+=1
                    verified.append(record)
                    hashes[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
                groups.append({"movement_cost":cost,"initial_b":initial_b,"treatment":treatment,**outcomes})
    args.output.mkdir(parents=True,exist_ok=False)
    report={"scope":"Group/trait/energy consistency and endpoint reconstruction; no full individual history or causal proof.",
        "metric_rows_checked":480160,"groups":groups,"runs":verified,"input_sha256":hashes,
        "metadata_sha256":hashlib.sha256((args.input/"metadata.json").read_bytes()).hexdigest(),
        "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.output/"summary.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(groups,indent=2))


if __name__ == "__main__":
    main()
