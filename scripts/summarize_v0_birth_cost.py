"""Recompute birth-cost factorial experiment outcomes from full metric tables."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/campaign-012"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    metadata = json.loads((args.input / "metadata.json").read_text(encoding="utf-8"))
    if metadata["status"] != "complete" or metadata["protocol"] != "campaign-012-birth-cost-1":
        raise ValueError("Expected complete campaign 012")
    if (metadata["seeds"] != list(range(1000, 1010)) or metadata["steps"] != 10000
            or metadata["treatments"] != [[f"{a}-{t}-cost-{c}", f, e, t, c]
                for a, f, e in (("food", 5, 24), ("stored", 0, 88))
                for t in (40, 160) for c in (0, 4)]
            or metadata["regrowth_probability"] != 15 or metadata["founder_trait"] != 250
            or metadata["mutation_probability"] != 0):
        raise ValueError("Metadata differs from preregistered campaign 012")
    results = json.loads((args.input / "results.json").read_text(encoding="utf-8"))
    expected = {(name, s) for name, _, _, _, _ in metadata["treatments"] for s in metadata["seeds"]}
    indexed = {(r["treatment"], r["seed"]): r for r in results}
    if len(indexed) != len(results) or set(indexed) != expected:
        raise ValueError("Incomplete or duplicate run grid")
    config = metadata["baseline_config"]
    if (config["width"], config["height"], config["initial_population"]) != (32, 32, 80):
        raise ValueError("Unexpected world size or founding population")
    if metadata.get("rules_version") != "v0-darwin-1" or metadata.get("completed_runs") != 80:
        raise ValueError("Unexpected rules or completion count")
    for key, value in {"food_capacity": 24, "regrowth_amount": 4, "feeding_rate": 8,
                       "basal_cost": 1, "movement_cost": 1}.items():
        if type(config.get(key)) is not int or config[key] != value:
            raise ValueError(f"Unexpected fixed parameter: {key}")
    hashes = {}
    groups = []
    late_turnover = []
    for treatment, food, energy, threshold, cost in metadata["treatments"]:
        verified = []
        for seed in metadata["seeds"]:
            if (indexed[treatment, seed]["initial_food"] != food
                    or indexed[treatment, seed]["initial_energy"] != energy or indexed[treatment, seed]["birth_threshold"] != threshold
                    or indexed[treatment, seed]["birth_cost"] != cost):
                raise ValueError("Treatment summary differs from protocol")
            path = args.input / f"{treatment}-seed-{seed}.csv"
            hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
            with path.open(newline="", encoding="utf-8") as stream:
                rows = [{k: None if v == "" else float(v) if k == "mean_genome" else int(v)
                         for k, v in row.items()} for row in csv.DictReader(stream)]
            if [r["tick"] for r in rows] != list(range(metadata["steps"] + 1)):
                raise ValueError(f"Tick sequence: {path.name}")
            if rows[0]["food_energy"] != food * config["width"] * config["height"] or rows[0]["organism_energy"] != config["initial_population"] * energy:
                raise ValueError(f"Initial energy: {path.name}")
            previous = None
            for row in rows:
                if any(row[k] < 0 for k in ("population", "births", "deaths", "food_energy", "organism_energy", "dissipated_energy", "supplied_energy")):
                    raise ValueError("Negative metric")
                if row["population"] > 1024 or row["food_energy"] > 1024 * 24:
                    raise ValueError("Spatial or resource bounds")
                if previous and any(row[k] < previous[k] for k in ("births", "deaths", "dissipated_energy", "supplied_energy")):
                    raise ValueError("Cumulative metric decreased")
                previous = row
                if (row["population"] != config["initial_population"] + row["births"] - row["deaths"]
                    or row["organism_energy"] + row["food_energy"] + row["dissipated_energy"] != row["supplied_energy"]
                    or (row["population"] and (row["mean_genome"] != 250 or row["genome_variants"] != 1))):
                    raise ValueError(f"Accounting or fixed-trait invariant: {path.name}")
            extinction = next((r["tick"] for r in rows if r["population"] == 0), None)
            if extinction is not None and any(r["population"] for r in rows[extinction:]):
                raise ValueError("Population reappeared after extinction")
            values = {**rows[-1], "population_at_500": rows[500]["population"],
                      "population_at_5000": rows[5000]["population"], "extinction_tick": extinction,
                      "right_censored": extinction is None,
                      "late_mean_population": mean(r["population"] for r in rows[-1000:])}
            for tick in (10, 100, 500, 5000):
                values[f"population_at_{tick}"] = rows[tick]["population"]
                values[f"births_at_{tick}"] = rows[tick]["births"]
            if any(indexed[treatment, seed][k] != v for k, v in values.items()):
                raise ValueError(f"Summary differs: {path.name}")
            late_births = rows[10000]["births"] - rows[9000]["births"]
            late_deaths = rows[10000]["deaths"] - rows[9000]["deaths"]
            if (min(late_births, late_deaths) < 0
                    or rows[10000]["population"] - rows[9000]["population"] != late_births - late_deaths):
                raise ValueError("Invalid late-window turnover")
            values.update(late_births=late_births, late_deaths=late_deaths,
                          early_peak_population=max(r["population"] for r in rows[:101]))
            values["early_peak_tick"] = next(r["tick"] for r in rows[:101]
                if r["population"] == values["early_peak_population"])
            if any(indexed[treatment, seed][k] != v for k, v in values.items()):
                raise ValueError(f"Early/late summary differs: {path.name}")
            late_turnover.append({"treatment": treatment, "seed": seed,
                                  "start_population": rows[9000]["population"],
                                  "end_population": rows[10000]["population"],
                                  "births": late_births, "deaths": late_deaths})
            verified.append(values)
        deaths = [r["extinction_tick"] for r in verified if r["extinction_tick"] is not None]
        groups.append({"treatment": treatment, "initial_food": food, "initial_energy": energy, "birth_threshold": threshold, "birth_cost": cost,
                       "mean_early_peak_population": mean(r["early_peak_population"] for r in verified),
                       "mean_early_peak_tick": mean(r["early_peak_tick"] for r in verified), "runs": len(verified), "mean_births_at_10": mean(r["births_at_10"] for r in verified), "mean_births_at_100": mean(r["births_at_100"] for r in verified),
                       "alive_at_500": sum(r["population_at_500"] > 0 for r in verified),
                       "alive_at_5000": sum(r["population_at_5000"] > 0 for r in verified),
                       "alive_at_10000": sum(r["population"] > 0 for r in verified),
                       "mean_late_births": mean(r["late_births"] for r in verified),
                       "mean_late_deaths": mean(r["late_deaths"] for r in verified),
                       "extinct_only_range": [min(deaths), max(deaths)] if deaths else None,
                       "late_mean_population": mean(r["late_mean_population"] for r in verified), "mean_supplied_energy": mean(r["supplied_energy"] for r in verified), "mean_births": mean(r["births"] for r in verified)})
    cells = {g["treatment"]: g for g in groups}
    contrasts = []
    for allocation in ("food", "stored"):
        for horizon in (500, 5000, 10000):
            key = f"alive_at_{horizon}"
            delta = {cost: (cells[f"{allocation}-160-cost-{cost}"][key]
                           - cells[f"{allocation}-40-cost-{cost}"][key]) / 10
                     for cost in (0, 4)}
            contrasts.append({"allocation": allocation, "horizon": horizon,
                "threshold_survival_difference_cost_0": delta[0],
                "threshold_survival_difference_cost_4": delta[4],
                "difference_of_differences": delta[0] - delta[4]})
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"groups": groups, "descriptive_survival_contrasts": contrasts, "late_turnover_window": [9001, 10000], "late_turnover": late_turnover,
              "metric_rows_checked": len(expected) * (metadata["steps"] + 1),
              "input_sha256": hashes, "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(groups, indent=2))


if __name__ == "__main__":
    main()
