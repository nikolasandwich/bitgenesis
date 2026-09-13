"""Summarize recorded founder loss and living-generation depth in campaign 011."""

import argparse
import csv
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/campaign-011"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    metadata = json.loads((args.input / "metadata.json").read_text())
    if metadata["status"] != "complete" or metadata["protocol"] != "campaign-011-long-horizon-1":
        raise ValueError("Expected complete campaign 011")
    records, hashes = [], {}
    for treatment in ("food-160", "stored-160"):
        for seed in range(900, 910):
            path = args.input / f"{treatment}-seed-{seed}.csv"
            with path.open("rb") as stream:
                hashes[path.name] = hashlib.file_digest(stream, "sha256").hexdigest()
            record = {"treatment": treatment, "seed": seed, "first_single_founder_tick": None}
            previous_founders = 80
            count = 0
            with path.open(newline="", encoding="utf-8") as stream:
                for tick, row in enumerate(csv.DictReader(stream)):
                    count += 1
                    population, founders = int(row["population"]), int(row["founder_lineages"])
                    variants = int(row["genome_variants"])
                    if (int(row["tick"]) != tick or not 0 <= founders <= min(previous_founders, population)
                            or (population > 0) != (founders > 0) or variants != int(population > 0)):
                        raise ValueError("Invalid founder-count or fixed-genome sequence")
                    if tick == 0 and (population, founders) != (80, 80):
                        raise ValueError("Unexpected founding population")
                    if founders == 1 and record["first_single_founder_tick"] is None:
                        record["first_single_founder_tick"] = tick
                    if tick in (10000, 100000):
                        record[f"population_at_{tick}"] = population
                        record[f"founders_at_{tick}"] = founders
                        record[f"max_living_generation_at_{tick}"] = int(row["max_generation"]) if row["max_generation"] else None
                    previous_founders = founders
            if count != 100001:
                raise ValueError("Incomplete long record")
            records.append(record)
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "lineages.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    report = {"analysis": "campaign-011-recorded-lineages-1", "metric_rows_checked": 2000020,
              "scope": "Recorded count consistency; no reconstruction of unexported genealogy",
              "input_sha256": hashes, "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.output / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
