"""Independently recompute establishment endpoints from complete per-tick CSV."""

import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/campaign-007"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    metadata = json.loads((args.input / "metadata.json").read_text())
    if metadata["status"] != "complete" or metadata["protocol"] != "campaign-007-establishment-1":
        raise ValueError("Expected completed campaign 007")
    saved = json.loads((args.input / "results.json").read_text())
    expected = {(t, m, s) for t in metadata["founder_traits"] for m in metadata["mutation_probabilities"] for s in metadata["seeds"]}
    indexed = {(r["founder_trait"], r["mutation_probability"], r["seed"]): r for r in saved}
    if len(indexed) != len(saved) or set(indexed) != expected:
        raise ValueError("Missing/duplicate treatment runs")
    groups = defaultdict(list)
    hashes = {}
    row_count = 0
    for trait, mutation, seed in sorted(expected):
        name = f"founder-{trait}-mutation-{mutation}-seed-{seed}.csv"
        path = args.input / name
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        with path.open(newline="", encoding="utf-8") as stream:
            rows = [{k: (None if v == "" else float(v) if k == "mean_genome" else int(v))
                     for k, v in raw.items()} for raw in csv.DictReader(stream)]
        if [r["tick"] for r in rows] != list(range(metadata["steps"] + 1)):
            raise ValueError(f"Incomplete tick sequence: {name}")
        row_count += len(rows)
        initial = metadata["baseline_config"]["initial_population"]
        for row in rows:
            if row["population"] != initial + row["births"] - row["deaths"]:
                raise ValueError(f"Population accounting: {name}")
            if row["organism_energy"] + row["food_energy"] + row["dissipated_energy"] != row["supplied_energy"]:
                raise ValueError(f"Energy accounting: {name}")
            if trait != "random" and mutation == 0 and row["population"]:
                if row["mean_genome"] != int(trait) or row["genome_variants"] != 1:
                    raise ValueError(f"Fixed trait changed: {name}")
        if trait != "random" and rows[0]["mean_genome"] != int(trait):
            raise ValueError(f"Founder initialization differs: {name}")
        extinction = next((r["tick"] for r in rows if r["population"] == 0), None)
        if extinction is not None and any(r["population"] for r in rows[extinction:]):
            raise ValueError(f"Population reappeared: {name}")
        calculated = {**rows[-1], "late_mean_population": mean(r["population"] for r in rows[-1000:]),
                      "extinction_tick": extinction, "right_censored": extinction is None,
                      "population_at_500": rows[500]["population"], "mean_genome_at_500": rows[500]["mean_genome"]}
        recorded = indexed[trait, mutation, seed]
        for key, value in calculated.items():
            if recorded[key] != value:
                raise ValueError(f"Summary mismatch: {name} / {key}")
        groups[trait, mutation].append(calculated)
    summaries = []
    for (trait, mutation), rows in sorted(groups.items()):
        extinct = [r["extinction_tick"] for r in rows if r["extinction_tick"] is not None]
        summaries.append({"founder_trait": trait, "mutation_probability": mutation,
                          "surviving_at_500": sum(r["population_at_500"] > 0 for r in rows),
                          "surviving_at_5000": sum(r["population"] > 0 for r in rows), "runs": len(rows),
                          "extinct_only_tick_range": [min(extinct), max(extinct)] if extinct else None,
                          "final_population_range": [min(r["population"] for r in rows), max(r["population"] for r in rows)],
                          "late_mean_population": mean(r["late_mean_population"] for r in rows)})
    args.output.mkdir(parents=True, exist_ok=False)
    report = {"groups": summaries, "metric_rows_checked": row_count,
              "scope": "Accounting and endpoint consistency only; no dynamics replay or lifecycle validation.",
              "input_sha256": hashes,
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
