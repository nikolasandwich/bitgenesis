"""Recompute energy-allocation experiment outcomes from full metric tables."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/campaign-009"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    metadata = json.loads((args.input / "metadata.json").read_text())
    if metadata["status"] != "complete" or metadata["protocol"] != "campaign-009-energy-allocation-1":
        raise ValueError("Expected complete campaign 009")
    if (metadata["seeds"] != list(range(800, 810)) or metadata["steps"] != 10000
            or metadata["treatments"] != [["low", 0, 24], ["food", 5, 24], ["stored", 0, 88]]
            or metadata["regrowth_probability"] != 15 or metadata["founder_trait"] != 250
            or metadata["mutation_probability"] != 0):
        raise ValueError("Metadata differs from preregistered campaign 009")
    results = json.loads((args.input / "results.json").read_text())
    expected = {(name, s) for name, _, _ in metadata["treatments"] for s in metadata["seeds"]}
    indexed = {(r["treatment"], r["seed"]): r for r in results}
    if len(indexed) != len(results) or set(indexed) != expected:
        raise ValueError("Incomplete or duplicate run grid")
    config = metadata["baseline_config"]
    if (config["width"], config["height"], config["initial_population"]) != (32, 32, 80):
        raise ValueError("Unexpected world size or founding population")
    hashes = {}
    groups = []
    for treatment, food, energy in metadata["treatments"]:
        verified = []
        for seed in metadata["seeds"]:
            if (indexed[treatment, seed]["initial_food"] != food
                    or indexed[treatment, seed]["initial_energy"] != energy):
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
            for row in rows:
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
            if any(indexed[treatment, seed][k] != v for k, v in values.items()):
                raise ValueError(f"Summary differs: {path.name}")
            verified.append(values)
        deaths = [r["extinction_tick"] for r in verified if r["extinction_tick"] is not None]
        groups.append({"treatment": treatment, "initial_food": food, "initial_energy": energy, "runs": len(verified),
                       "alive_at_500": sum(r["population_at_500"] > 0 for r in verified),
                       "alive_at_5000": sum(r["population_at_5000"] > 0 for r in verified),
                       "alive_at_10000": sum(r["population"] > 0 for r in verified),
                       "extinct_only_range": [min(deaths), max(deaths)] if deaths else None,
                       "late_mean_population": mean(r["late_mean_population"] for r in verified), "mean_supplied_energy": mean(r["supplied_energy"] for r in verified), "mean_births": mean(r["births"] for r in verified)})
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"groups": groups, "metric_rows_checked": len(expected) * (metadata["steps"] + 1),
              "input_sha256": hashes, "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(groups, indent=2))


if __name__ == "__main__":
    main()

