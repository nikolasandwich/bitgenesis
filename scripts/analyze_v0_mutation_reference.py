"""Compare realized mutation increments with a local kernel reference, post hoc."""

import argparse
import csv
from fractions import Fraction
from functools import cache
import hashlib
import json
from pathlib import Path


@cache
def kernel_reference(genome, probability, step):
    if (type(genome) is not int or not 0 <= genome <= 1000
            or type(probability) is not int or not 0 <= probability <= 1000
            or type(step) is not int or step < 0):
        raise ValueError("Invalid mutation kernel parameters")
    return Fraction(probability, 1000 * (2 * step + 1)) * sum(
        max(0, min(1000, genome + delta)) - genome for delta in range(-step, step + 1))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/campaign-001"))
    parser.add_argument("--reference", type=Path, default=Path("docs/research/results/trait-change-001.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    rows = []
    for treatment in ("baseline", "no-mutation"):
        for seed in range(5):
            name = f"{treatment}-seed-{seed}"
            root = args.input / name
            for filename in ("metadata.json", "lineage.json", "events.jsonl", "metrics.csv", "summary.json"):
                if hashlib.sha256((root / filename).read_bytes()).hexdigest() != reference["input_sha256"][f"{name}/{filename}"]:
                    raise ValueError("Input differs from audited decomposition")
            config = json.loads((root / "metadata.json").read_text(encoding="utf-8"))["config"]
            if config["seed"] != seed or config["mutation_probability"] != (100 if treatment == "baseline" else 0):
                raise ValueError("Unexpected treatment or seed")
            genes = {o["id"]: o["genome"] for o in json.loads((root / "lineage.json").read_text(encoding="utf-8"))}
            with (root / "metrics.csv").open(encoding="utf-8", newline="") as stream:
                populations = {int(r["tick"]): int(r["population"]) for r in csv.DictReader(stream)}
            observed = reference_sum = Fraction(0)
            observed_raw = 0
            reference_raw = Fraction(0)
            births = low = high = 0
            with (root / "events.jsonl").open(encoding="utf-8") as stream:
                for line in stream:
                    event = json.loads(line)
                    if event["event"] != "birth" or event["parent_id"] is None:
                        continue
                    parent = genes[event["parent_id"]]
                    delta = event["genome"] - parent
                    local = kernel_reference(parent, config["mutation_probability"], config["mutation_step"])
                    denominator = populations[event["tick"]]
                    if denominator <= 0:
                        raise ValueError("Undefined living mean")
                    births += 1
                    low += parent < config["mutation_step"]
                    high += parent > 1000 - config["mutation_step"]
                    observed_raw += delta
                    reference_raw += local
                    observed += Fraction(delta, denominator)
                    reference_sum += local / denominator
            prior = next(r for r in reference["runs"] if r["treatment"] == treatment and r["seed"] == seed)
            if float(observed) != prior["transmitted_mutation"]:
                raise ValueError("Observed transmission differs from prior decomposition")
            rows.append({"treatment": treatment, "seed": seed, "births": births,
                         "parents_near_lower_boundary": low, "parents_near_upper_boundary": high,
                         "observed_raw_increment": observed_raw, "kernel_raw_reference": float(reference_raw),
                         "observed_weighted": float(observed), "kernel_weighted_reference": float(reference_sum),
                         "weighted_difference": float(observed - reference_sum)})
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "reference.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {"scope": "Local kernel expectations evaluated along observed parents and post-tick counts; not a counterfactual or unbiased whole-trajectory expectation.",
              "runs": rows, "reference_sha256": hashlib.sha256(args.reference.read_bytes()).hexdigest(),
              "input_sha256": reference["input_sha256"],
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
