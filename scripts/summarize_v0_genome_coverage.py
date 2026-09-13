"""Reconstruct campaign-013 genome coverage from birth records and full metrics."""

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path


HORIZONS = [0, 1000, 5000, 10000, 25000, 40000, 50000]


def birth_catalog(path, mutation, steps=50000, founders=80):
    records, first_seen, counts = {}, {}, Counter()
    last_tick = 0
    with path.open(newline="", encoding="utf-8") as stream:
        for raw in csv.DictReader(stream):
            identity, tick, genome = (int(raw[k]) for k in ("id", "birth_tick", "genome"))
            parent = None if raw["parent_id"] == "" else int(raw["parent_id"])
            if identity != len(records) or not last_tick <= tick <= steps or not 0 <= genome <= 1000:
                raise ValueError("Invalid birth identity, time or genome")
            if identity < founders:
                if parent is not None or tick != 0:
                    raise ValueError("Invalid founder")
            else:
                if parent not in records or parent >= identity or records[parent][0] >= tick:
                    raise ValueError("Parent must be born before its child")
                parental_genome = records[parent][1]
                if (mutation == 0 and genome != parental_genome) or abs(genome - parental_genome) > 100:
                    raise ValueError("Inheritance violates declared mutation")
            records[identity] = (tick, genome)
            first_seen.setdefault(genome, tick)
            counts[tick] += 1
            last_tick = tick
    if len(records) < founders:
        raise ValueError("Missing founders")
    return first_seen, counts, len(records)


def verify_metrics(path, first_seen, birth_counts, total_born, steps=50000, horizons=HORIZONS):
    cumulative = 0
    discoveries = Counter(first_seen.values())
    ever = 0
    observations = {}
    extinction = None
    previous = None
    with path.open(newline="", encoding="utf-8") as stream:
        count = 0
        for tick, raw in enumerate(csv.DictReader(stream)):
            row = {k: None if v == "" else float(v) if k == "mean_genome" else int(v) for k, v in raw.items()}
            count += 1
            if row["tick"] != tick or tick > steps:
                raise ValueError("Invalid metric tick sequence")
            cumulative += birth_counts[tick]
            ever += discoveries[tick]
            if row["births"] != cumulative - 80 or row["ever_genome_values"] != ever:
                raise ValueError("Metrics disagree with birth catalog")
            if row["population"] != cumulative - row["deaths"] or not 0 <= row["population"] <= 1024:
                raise ValueError("Population accounting differs")
            if (row["food_energy"] + row["organism_energy"] + row["dissipated_energy"] != row["supplied_energy"]
                    or any(row[k] < 0 for k in ("food_energy", "organism_energy", "births", "deaths", "dissipated_energy", "supplied_energy"))
                    or row["food_energy"] > 24576):
                raise ValueError("Energy accounting or bounds differ")
            if tick == 0 and (row["population"], row["deaths"], row["food_energy"], row["organism_energy"], row["supplied_energy"], row["dissipated_energy"]) != (80, 0, 8192, 1920, 10112, 0):
                raise ValueError("Invalid initial state")
            if previous and (any(row[k] < previous[k] for k in ("births", "deaths", "supplied_energy", "dissipated_energy"))
                             or row["founder_lineages"] > previous["founder_lineages"]):
                raise ValueError("Invalid cumulative metric or founder increase")
            if row["population"]:
                if (extinction is not None or not 1 <= row["genome_variants"] <= min(ever, row["population"])
                        or not 1 <= row["founder_lineages"] <= min(80, row["population"])
                        or row["mean_genome"] is None or not 0 <= row["mean_genome"] <= 1000
                        or row["max_generation"] is None or row["max_generation"] < 0):
                    raise ValueError("Invalid living diversity")
            else:
                if any(row[k] != 0 for k in ("organism_energy", "genome_variants", "founder_lineages")) or row["mean_genome"] is not None or row["max_generation"] is not None:
                    raise ValueError("Invalid extinct state")
                if extinction is None:
                    extinction = tick
            if tick in horizons:
                observations[str(tick)] = row.copy()
            previous = row
    if count != steps + 1 or cumulative != total_born:
        raise ValueError("Truncated metrics or uncounted births")
    return previous, observations, extinction


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/campaign-013"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    metadata = json.loads((args.input / "metadata.json").read_text(encoding="utf-8"))
    if (metadata["status"] != "complete" or metadata["protocol"] != "campaign-013-genome-coverage-1"
            or metadata["rules_version"] != "v0-darwin-1" or metadata["steps"] != 50000
            or metadata["completed_runs"] != 10 or metadata["seeds"] != list(range(1100, 1105))
            or metadata["treatments"] != [["mutation", 100], ["no-mutation", 0]]
            or metadata["observation_ticks"] != HORIZONS):
        raise ValueError("Expected completed preregistered campaign 013")
    fixed = dict(seed=42, width=32, height=32, initial_population=80, initial_energy=24,
        initial_food=8, food_capacity=24, regrowth_probability=40, regrowth_amount=4,
        feeding_rate=8, basal_cost=1, movement_cost=1, birth_threshold=40, birth_cost=4,
        mutation_probability=100, mutation_step=100)
    if metadata["baseline_config"] != fixed:
        raise ValueError("Unexpected baseline configuration")
    results = json.loads((args.input / "results.json").read_text(encoding="utf-8"))
    indexed = {(r["treatment"], r["seed"]): r for r in results}
    expected = {(t, s) for t in ("mutation", "no-mutation") for s in range(1100, 1105)}
    if len(results) != 10 or set(indexed) != expected:
        raise ValueError("Incomplete or duplicate run grid")
    verified, hashes = [], {}
    for treatment, mutation in metadata["treatments"]:
        for seed in metadata["seeds"]:
            prefix = f"{treatment}-seed-{seed}"
            births = args.input / f"{prefix}-births.csv"
            metrics = args.input / f"{prefix}.csv"
            first_seen, counts, born = birth_catalog(births, mutation)
            final, observations, extinction = verify_metrics(metrics, first_seen, counts, born)
            values = {"treatment": treatment, "mutation_probability": mutation, "seed": seed, **final,
                      "initial_genome_values": sum(t == 0 for t in first_seen.values()),
                      "new_values_last_10000": sum(t > 40000 for t in first_seen.values()),
                      "observations": observations, "extinction_tick": extinction,
                      "right_censored": extinction is None}
            if values != indexed[treatment, seed]:
                raise ValueError(f"Summary differs from observations: {prefix}")
            verified.append(values)
            hashes[births.name], hashes[metrics.name] = digest(births), digest(metrics)
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"runs": verified, "metric_rows_checked": 500010,
              "birth_rows_checked": sum(r["births"] + 80 for r in verified),
              "scope": "Birth catalog and metric consistency; living traits are bounded but not independently reconstructed from unsaved death records.",
              "input_sha256": hashes, "script_sha256": digest(Path(__file__))}
    (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps([{k: r[k] for k in ("treatment", "seed", "ever_genome_values", "new_values_last_10000", "population")} for r in verified], indent=2))


if __name__ == "__main__":
    main()
