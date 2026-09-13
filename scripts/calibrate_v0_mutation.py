"""Exhaustively calibrate the specified V0 mutation kernel, without selection."""

import argparse
import csv
from fractions import Fraction
import json
from pathlib import Path

from bitgenesis.v0.runner import load_config, provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = load_config(Path(__file__).resolve().parents[1] / "experiments/v0/darwin-baseline.toml")
    args.output.mkdir(parents=True, exist_ok=False)
    probability = Fraction(config.mutation_probability, 1000)
    step = config.mutation_step
    values = []
    for genome in range(1001):
        destinations = [max(0, min(1000, genome + delta)) for delta in range(-step, step + 1)]
        drift = probability * (Fraction(sum(destinations), len(destinations)) - genome)
        changed = probability * Fraction(sum(value != genome for value in destinations), len(destinations))
        values.append({"genome": genome, "expected_change_per_birth": float(drift),
                       "expected_change_exact": str(drift), "probability_of_actual_change": float(changed)})
    # Exact arithmetic validates the reflection identity, not a Monte Carlo fit.
    if any(Fraction(values[g]["expected_change_exact"]) != -Fraction(values[1000-g]["expected_change_exact"])
           for g in range(1001)):
        raise AssertionError("Mutation kernel lost reflection symmetry")
    with (args.output / "kernel.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)
    result = {"analysis": "v0-mutation-kernel-calibration-1", "rules_version": "v0-darwin-1",
              "scope": "Exact one-birth expectation under the documented mutation rule; no population, resource competition or selection is simulated.",
              "mutation_probability_per_thousand": config.mutation_probability,
              "mutation_step": step, "genomes_enumerated": len(values),
              "reflection_symmetry": True, "examples": [values[g] for g in (0, 50, 100, 500, 900, 950, 1000)],
              **provenance()}
    (args.output / "calibration.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["examples"], indent=2))


if __name__ == "__main__":
    main()
