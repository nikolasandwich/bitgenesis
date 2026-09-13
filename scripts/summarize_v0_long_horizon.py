"""Stream-verify long-horizon metrics and their campaign-010 observable prefixes."""

import argparse
from collections import deque
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean


def parsed(row):
    return {key: None if value == "" else float(value) if key == "mean_genome" else int(value)
            for key, value in row.items()}


def verify_run(path, reference_path, *, steps=100000, prefix_ticks=10000,
               initial_population=80, observations=(10000, 50000), late_window=1000):
    if not 0 <= prefix_ticks <= steps or not 1 <= late_window <= steps + 1:
        raise ValueError("Invalid verification window")
    late = deque(maxlen=late_window)
    extinction, previous, checkpoints = None, None, {}
    with path.open(encoding="utf-8", newline="") as stream, reference_path.open(encoding="utf-8", newline="") as reference:
        rows, originals = csv.DictReader(stream), csv.DictReader(reference)
        for tick, raw in enumerate(rows):
            row = parsed(raw)
            if row["tick"] != tick or tick > steps:
                raise ValueError("Incomplete or unordered tick sequence")
            if tick <= prefix_ticks:
                original = next(originals, None)
                if original is None or row != parsed(original):
                    raise ValueError(f"Historical prefix mismatch at tick {tick}")
            if (any(row[k] < 0 for k in ("population", "births", "deaths", "food_energy", "organism_energy", "supplied_energy", "dissipated_energy"))
                    or row["population"] != initial_population + row["births"] - row["deaths"]
                    or row["food_energy"] + row["organism_energy"] + row["dissipated_energy"] != row["supplied_energy"]):
                raise ValueError(f"Accounting mismatch at tick {tick}")
            if previous is not None and any(row[k] < previous[k] for k in ("births", "deaths", "supplied_energy", "dissipated_energy")):
                raise ValueError("Cumulative counters decreased")
            if row["population"]:
                if extinction is not None or row["mean_genome"] != 250 or row["genome_variants"] != 1:
                    raise ValueError("Extinction persistence or fixed trait mismatch")
            elif extinction is None:
                extinction = tick
            if tick in observations:
                checkpoints[f"population_at_{tick}"] = row["population"]
                checkpoints[f"births_at_{tick}"] = row["births"]
            late.append(row["population"])
            previous = row
        if previous is None or previous["tick"] != steps or next(originals, None) is not None:
            raise ValueError("Incomplete run or unexpected reference length")
    return {**previous, **checkpoints, "extinction_tick": extinction,
            "right_censored": extinction is None, "late_mean_population": mean(late)}


def file_hash(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def validate_fixed_parameters(metadata):
    if metadata.get("rules_version") != "v0-darwin-1":
        raise ValueError("Unexpected rules version")
    for key, expected in {"regrowth_probability": 15, "founder_trait": 250, "mutation_probability": 0}.items():
        if type(metadata.get(key)) is not int or metadata[key] != expected:
            raise ValueError(f"Unexpected protocol parameter: {key}")
    config = metadata.get("baseline_config", {})
    for key, expected in {"width": 32, "height": 32, "initial_population": 80,
                          "food_capacity": 24, "regrowth_amount": 4, "feeding_rate": 8,
                          "basal_cost": 1, "movement_cost": 1, "birth_cost": 4}.items():
        if type(config.get(key)) is not int or config[key] != expected:
            raise ValueError(f"Unexpected fixed world parameter: {key}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/campaign-011"))
    parser.add_argument("--reference", type=Path, default=Path("data/campaign-010"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    metadata = json.loads((args.input / "metadata.json").read_text())
    validate_fixed_parameters(metadata)
    treatments = [["food-160", 5, 24, 160], ["stored-160", 0, 88, 160]]
    if (metadata["status"] != "complete" or metadata["protocol"] != "campaign-011-long-horizon-1"
            or metadata["steps"] != 100000 or metadata["reference_prefix_ticks"] != 10000
            or metadata["seeds"] != list(range(900, 910)) or metadata["treatments"] != treatments):
        raise ValueError("Expected complete preregistered campaign 011")
    results = json.loads((args.input / "results.json").read_text())
    indexed = {(r["treatment"], r["seed"]): r for r in results}
    expected = {(name, seed) for name, _, _, _ in treatments for seed in range(900, 910)}
    if len(results) != 20 or set(indexed) != expected:
        raise ValueError("Incomplete or duplicate cohort")
    hashes, reference_hashes, groups = {}, {}, []
    for treatment, food, energy, threshold in treatments:
        verified = []
        for seed in range(900, 910):
            name = f"{treatment}-seed-{seed}.csv"
            hashes[name] = file_hash(args.input / name)
            reference_hashes[name] = file_hash(args.reference / name)
            if metadata["reference_sha256"][name] != reference_hashes[name]:
                raise ValueError("Reference file changed since execution")
            saved = indexed[treatment, seed]
            if (saved["initial_food"], saved["initial_energy"], saved["birth_threshold"]) != (food, energy, threshold):
                raise ValueError("Treatment summary mismatch")
            values = verify_run(args.input / name, args.reference / name)
            if any(saved[key] != value for key, value in values.items()):
                raise ValueError("Summary differs from full metrics")
            verified.append(values)
        deaths = [r["extinction_tick"] for r in verified if r["extinction_tick"] is not None]
        groups.append({"treatment": treatment, "runs": 10,
                       "alive_at_10000": sum(r["population_at_10000"] > 0 for r in verified),
                       "alive_at_50000": sum(r["population_at_50000"] > 0 for r in verified),
                       "alive_at_100000": sum(r["population"] > 0 for r in verified),
                       "extinct_only_range": [min(deaths), max(deaths)] if deaths else None,
                       "late_mean_population": mean(r["late_mean_population"] for r in verified)})
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"groups": groups, "metric_rows_checked": 2000020, "prefix_rows_matched": 200020,
              "computational_ticks": 2000000, "repeated_prefix_ticks": 200000,
              "additional_observation_ticks": 1800000, "new_independent_seed_replicates": 0,
              "input_sha256": hashes, "reference_sha256": reference_hashes,
              "script_sha256": file_hash(Path(__file__))}
    (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(groups, indent=2))


if __name__ == "__main__":
    main()
