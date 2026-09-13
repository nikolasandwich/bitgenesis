"""Retrospective counts of visited movement-trait values, not functional novelty."""

import argparse
import csv
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/campaign-001"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results, hashes = [], {}
    for treatment in ("baseline", "no-mutation"):
        for seed in range(5):
            name = f"{treatment}-seed-{seed}"
            root = args.input / name
            loaded = {}
            for file in ("metadata.json", "lineage.json", "summary.json"):
                data = (root / file).read_bytes()
                hashes[f"{name}/{file}"] = hashlib.sha256(data).hexdigest()
                loaded[file] = json.loads(data)
            metadata, lineage, summary = (loaded[file] for file in ("metadata.json", "lineage.json", "summary.json"))
            if metadata["status"] != "complete" or metadata["rules_version"] != "v0-darwin-1":
                raise ValueError(f"Incomplete or unsupported run: {name}")
            if len({r["id"] for r in lineage}) != len(lineage):
                raise ValueError(f"Duplicate lineage IDs: {name}")
            if any(type(r["genome"]) is not int or not 0 <= r["genome"] <= 1000 for r in lineage):
                raise ValueError(f"Genome outside V0 domain: {name}")
            initial = {r["genome"] for r in lineage if r["parent_id"] is None}
            ever = {r["genome"] for r in lineage}
            final = {r["genome"] for r in lineage if r["death_tick"] is None}
            if len(final) != summary["genome_variants"]:
                raise ValueError(f"Terminal variants differ: {name}")
            if treatment == "no-mutation" and ever != initial:
                raise ValueError(f"New trait in no-mutation control: {name}")
            results.append({"treatment": treatment, "seed": seed, "initial_variants": len(initial),
                            "ever_observed_variants": len(ever), "new_value_count": len(ever - initial),
                            "terminal_variants": len(final), "terminal_max_generation": summary["max_generation"],
                            "lineage_records": len(lineage)})
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "coverage.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    sidecar = {"scope": "Visited scalar values in completed V0 runs; not new functions or intelligence.",
               "input_sha256": hashes, "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.output / "provenance.json").write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
