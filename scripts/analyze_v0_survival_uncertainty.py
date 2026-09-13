"""Exploratory, pointwise Wilson intervals for campaign 008 survival counts."""

import argparse
import csv
import hashlib
import json
from math import sqrt
from pathlib import Path
from statistics import NormalDist


def wilson(successes, trials):
    if type(trials) is not int or type(successes) is not int or not 0 <= successes <= trials or trials == 0:
        raise ValueError("Expected integer counts with 0 <= successes <= positive trials")
    z = NormalDist().inv_cdf(0.975)
    p = successes / trials
    denominator = 1 + z * z / trials
    center = (p + z * z / (2 * trials)) / denominator
    radius = z * sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denominator
    return [0.0 if successes == 0 else max(0.0, center - radius),
            1.0 if successes == trials else min(1.0, center + radius)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("docs/research/results/campaign-008.csv"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with args.input.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    keys = [(int(r["initial_food"]), int(r["seed"])) for r in rows]
    if len(keys) != 20 or set(keys) != {(f, s) for f in (0, 8) for s in range(700, 710)}:
        raise ValueError("Expected complete campaign 008 grid")
    horizons = [(500, "population_at_500"), (5000, "population_at_5000"), (10000, "population")]
    for row in rows:
        if int(row["tick"]) != 10000:
            raise ValueError("Unexpected observation horizon")
        death = int(row["extinction_tick"]) if row["extinction_tick"] else None
        for horizon, field in horizons:
            population = int(row[field])
            if population < 0 or (population > 0) != (death is None or death > horizon):
                raise ValueError("Survival and extinction records disagree")
    groups = []
    for food in (0, 8):
        selected = [row for row in rows if int(row["initial_food"]) == food]
        for horizon, field in horizons:
            alive = sum(int(row[field]) > 0 for row in selected)
            groups.append({"initial_food": food, "horizon": horizon, "alive": alive,
                           "runs": len(selected), "fraction": alive / len(selected),
                           "wilson_95_pointwise": wilson(alive, len(selected))})
    report = {"analysis": "campaign-008-survival-uncertainty-1", "exploratory": True,
              "assumption": "Independent Bernoulli world outcomes within each fixed treatment and horizon",
              "scope": "Model-based, pointwise; not simultaneous, not a treatment-effect interval or permanence estimate",
              "source": "https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm",
              "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "groups": groups}
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(groups, indent=2))


if __name__ == "__main__":
    main()
