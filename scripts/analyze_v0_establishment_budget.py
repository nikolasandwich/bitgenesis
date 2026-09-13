"""Post-experiment first-100-tick accounting for campaign 009."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean

from analyze_v0_energy_budget import budget


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/campaign-009"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    metadata = json.loads((args.input / "metadata.json").read_text())
    if (metadata["status"] != "complete" or metadata["protocol"] != "campaign-009-energy-allocation-1"
            or metadata["seeds"] != list(range(800, 810))):
        raise ValueError("Expected completed campaign 009")
    records, hashes = [], {}
    for treatment in ("low", "food", "stored"):
        for seed in range(800, 810):
            path = args.input / f"{treatment}-seed-{seed}.csv"
            hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
            with path.open(encoding="utf-8", newline="") as stream:
                rows = [{k: None if v == "" else float(v) if k == "mean_genome" else int(v)
                         for k, v in row.items()} for row in csv.DictReader(stream)]
            if len(rows) != 10001:
                raise ValueError("Incomplete metric table")
            for row in rows:
                if (row["population"] != 80 + row["births"] - row["deaths"]
                        or row["food_energy"] + row["organism_energy"] + row["dissipated_energy"] != row["supplied_energy"]):
                    raise ValueError("Accounting mismatch")
            config = metadata["baseline_config"]
            totals = budget(rows, 0, 100, config["basal_cost"], config["birth_cost"])
            peak = max(rows[:101], key=lambda row: row["population"])
            records.append({"treatment": treatment, "seed": seed, **totals,
                            "peak_population": peak["population"], "first_peak_tick": peak["tick"],
                            "births_by_10": rows[10]["births"], "births_by_100": rows[100]["births"],
                            "population_at_100": rows[100]["population"],
                            "organism_energy_at_100": rows[100]["organism_energy"],
                            "food_energy_at_100": rows[100]["food_energy"]})
    groups = [{"treatment": treatment, **{key: mean(row[key] for row in records if row["treatment"] == treatment)
               for key in records[0] if key not in ("treatment", "seed")}}
              for treatment in ("low", "food", "stored")]
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "budgets.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    report = {"analysis": "campaign-009-early-budget-1", "exploratory_window": [1, 100],
              "groups": groups, "input_sha256": hashes,
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "budget_helper_sha256": hashlib.sha256(Path(__file__).with_name("analyze_v0_energy_budget.py").read_bytes()).hexdigest()}
    (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(groups, indent=2))


if __name__ == "__main__":
    main()
