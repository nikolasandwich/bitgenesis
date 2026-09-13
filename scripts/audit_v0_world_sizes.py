"""Recompute campaign-005 summaries from saved CSV, without importing the engine."""

import argparse
from collections import deque
import csv
import json
import math
from pathlib import Path
from statistics import mean


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value):
    if value in (None, ""):
        return None
    result = float(value)
    require(math.isfinite(result), "Non-finite metric")
    return result


def audit(directory):
    directory = Path(directory)
    metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
    require(metadata["protocol"] == "campaign-005-world-sizes-1", "Unsupported protocol")
    require(metadata["rules_version"] == "v0-darwin-1", "Unsupported rules")
    require(metadata["status"] == "complete", "Campaign is not complete")
    require(metadata["initial_population_density"] == "5/64", "Unsupported density")
    require(set(metadata["treatments"]) == {"evolving", "neutral"}, "Unexpected treatments")
    steps = metadata["steps"]
    require(type(steps) is int and steps >= 0, "Invalid steps")
    widths, seeds = metadata["widths"], metadata["seeds"]
    require(len(set(widths)) == len(widths) and len(set(seeds)) == len(seeds), "Duplicate protocol values")
    require(widths and seeds and all(type(w) is int and w > 0 for w in widths)
            and all(type(s) is int for s in seeds), "Invalid widths/seeds")
    expected = {(w, t, s) for w in widths for t in metadata["treatments"] for s in seeds}
    summaries = json.loads((directory / "results.json").read_text(encoding="utf-8"))
    with (directory / "results.csv").open(encoding="utf-8", newline="") as stream:
        csv_summaries = list(csv.DictReader(stream))
    def index(rows):
        result = {(int(r["width"]), r["treatment"], int(r["seed"])): r for r in rows}
        require(len(result) == len(rows) and set(result) == expected, "Missing or duplicate summary runs")
        return result
    saved_json, saved_csv = index(summaries), index(csv_summaries)
    checked_rows = 0
    for width, treatment, seed in sorted(expected):
        key = width, treatment, seed
        name = f"width-{width}-{treatment}-seed-{seed}.csv"
        initial = width * width * 5 // 64
        require(initial > 0 and width * width * 5 % 64 == 0, "Non-integral initial density")
        late = deque(maxlen=1000)
        fixation = extinction = None
        previous = None
        with (directory / name).open(encoding="utf-8", newline="") as stream:
            for tick, raw in enumerate(csv.DictReader(stream)):
                row = {k: number(v) for k, v in raw.items()}
                require(row["tick"] == tick and tick <= steps, f"{name}: tick sequence")
                require(all(v is not None and v >= 0 and v.is_integer() for k, v in row.items()
                            if k != "mean_genome"), f"{name}: invalid integer metric")
                population = row["population"]
                require(population == initial + row["births"] - row["deaths"], f"{name}: population accounting")
                require(row["organism_energy"] + row["food_energy"] + row["dissipated_energy"]
                        == row["supplied_energy"], f"{name}: energy accounting")
                require(population <= width * width and row["food_energy"] <= width * width * metadata["baseline_config"]["food_capacity"], f"{name}: capacity")
                require(0 <= row["founder_lineages"] <= min(initial, population)
                        and 0 <= row["genome_variants"] <= population, f"{name}: diversity bounds")
                require((population == 0 and row["mean_genome"] is None)
                        or (population > 0 and row["mean_genome"] is not None and 0 <= row["mean_genome"] <= 1000), f"{name}: mean trait")
                if treatment == "neutral" and population:
                    require(row["mean_genome"] == 250 and row["genome_variants"] == 1, f"{name}: neutral trait changed")
                if previous is not None:
                    require(all(row[k] >= previous[k] for k in ("births", "deaths", "supplied_energy", "dissipated_energy")), f"{name}: cumulative metric decreased")
                    require(row["founder_lineages"] <= previous["founder_lineages"], f"{name}: founder reappeared")
                else:
                    config = metadata["baseline_config"]
                    require(row["births"] == row["deaths"] == row["dissipated_energy"] == 0
                            and row["organism_energy"] == initial * config["initial_energy"]
                            and row["food_energy"] == width * width * config["initial_food"]
                            and row["founder_lineages"] == initial, f"{name}: initial conditions")
                if population == 0 and extinction is None:
                    extinction = tick
                if row["founder_lineages"] == 1 and fixation is None:
                    fixation = tick
                late.append(population)
                previous = row
                checked_rows += 1
        require(previous is not None and previous["tick"] == steps, f"{name}: incomplete tick range")
        calculated = {"width": width, "seed": seed, "initial_population": initial, **previous,
                      "late_mean_population": mean(late), "terminal_founder_fraction": previous["founder_lineages"] / initial,
                      "first_single_founder_tick": fixation, "extinction_tick": extinction}
        for source in (saved_json[key], saved_csv[key]):
            require(set(source) == set(calculated) | {"treatment"}, f"{name}: summary fields")
            for field, value in calculated.items():
                actual = number(source[field])
                require(actual == value or (actual is not None and value is not None
                        and math.isclose(actual, value, rel_tol=1e-12, abs_tol=1e-12)), f"{name}: summary mismatch: {field}")
    return {"protocol": metadata["protocol"], "runs": len(expected), "metric_rows": checked_rows,
            "scope": "CSV accounting and summary consistency; no lifecycle records or dynamics replay verified."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(audit(args.directory), indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
