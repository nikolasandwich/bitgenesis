"""Retrospective accounting of campaign-002 energy, without replaying its worlds."""

import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean


def budget(rows, start, end, basal_cost=1, birth_cost=4):
    """Charge ticks start+1..end; every pre-tick individual pays exactly one basal unit."""
    if basal_cost != 1:
        raise ValueError("Exact population-based basal reconstruction requires basal_cost=1")
    if not 0 <= start < end < len(rows) or [r["tick"] for r in rows] != list(range(len(rows))):
        raise ValueError("Invalid or incomplete tick window")
    first, last = rows[start], rows[end]
    basal = sum(r["population"] for r in rows[start:end])
    births = last["births"] - first["births"]
    reproduction = births * birth_cost
    dissipation = last["dissipated_energy"] - first["dissipated_energy"]
    movement = dissipation - basal - reproduction
    supplied = last["supplied_energy"] - first["supplied_energy"]
    stock_change = sum(last[k] - first[k] for k in ("food_energy", "organism_energy"))
    if min(basal, births, movement, supplied) < 0 or supplied != basal + reproduction + movement + stock_change:
        raise ValueError("Energy allocation is inconsistent")
    return {"ticks": end - start, "basal": basal, "movement": movement,
            "reproduction": reproduction, "supplied": supplied, "stock_change": stock_change}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/campaign-002"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    metadata = json.loads((args.input / "metadata.json").read_text())
    if metadata["status"] != "complete" or metadata["protocol"] != "campaign-002-fixed-trait-assay-1":
        raise ValueError("Expected completed campaign 002")
    rows_out, hashes, groups = [], {}, defaultdict(list)
    for cost in metadata["movement_costs"]:
        for trait in metadata["traits"]:
            for seed in metadata["seeds"]:
                path = args.input / f"cost-{cost}-trait-{trait}-seed-{seed}.csv"
                hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
                with path.open(newline="", encoding="utf-8") as stream:
                    rows = [{k: None if v == "" else float(v) if k == "mean_genome" else int(v)
                             for k, v in raw.items()} for raw in csv.DictReader(stream)]
                if len(rows) != metadata["steps"] + 1:
                    raise ValueError(f"Incomplete run: {path.name}")
                config = metadata["baseline_config"]
                for row in rows:
                    if (row["population"] != config["initial_population"] + row["births"] - row["deaths"]
                        or row["organism_energy"] + row["food_energy"] + row["dissipated_energy"] != row["supplied_energy"]):
                        raise ValueError(f"Accounting differs: {path.name}")
                totals = budget(rows, 1500, 2000, config["basal_cost"], config["birth_cost"])
                record = {"movement_cost": cost, "trait": trait, "seed": seed, **totals}
                rows_out.append(record)
                groups[cost, trait].append(totals)
    summary = [{"movement_cost": cost, "trait": trait,
                **{k + "_per_tick": mean(r[k] / r["ticks"] for r in values)
                   for k in ("basal", "movement", "reproduction", "supplied", "stock_change")}}
               for (cost, trait), values in sorted(groups.items())]
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "budgets.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows_out[0]))
        writer.writeheader()
        writer.writerows(rows_out)
    result = {"analysis": "retrospective-campaign-002-budget-1", "window": [1501, 2000],
              "groups": summary, "input_sha256": hashes,
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.output / "summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
