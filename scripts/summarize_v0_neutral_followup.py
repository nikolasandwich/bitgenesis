"""Audit the selected campaign-015 cohort against the verified historical records."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

if __package__:
    from .summarize_v0_frequency_cost import verify_rows
else:
    from summarize_v0_frequency_cost import verify_rows


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return [{k: None if v == "" else float(v) if k in ("mean_genome", "b_fraction") else int(v)
                 for k, v in row.items()} for row in csv.DictReader(stream)]


def verify_followup(rows, prefix, cost, initial_b):
    result = verify_rows(rows, initial_b, 250, cost, steps=30000)
    if len(prefix) != 3001 or rows[:3001] != prefix:
        raise ValueError("Historical prefix differs or is truncated")
    if not prefix[-1]["a"] or not prefix[-1]["b"]:
        raise ValueError("Reference is outside the two-group cohort")
    return {**result, "observations": {str(t): rows[t] for t in (3000, 10000, 30000)}}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/campaign-015"))
    parser.add_argument("--reference", type=Path, default=Path("data/campaign-014"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    prior_path = root / "docs/research/results/campaign-014-verification.json"
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    selected = [(r["movement_cost"], r["initial_b"], r["seed"]) for r in prior["runs"]
                if r["treatment"] == "neutral" and r["a"] and r["b"]]
    cases = [(1, 72, 1206), (2, 8, 1200), (2, 72, 1208), (4, 72, 1208)]
    if selected != cases:
        raise ValueError("Historical cohort differs")
    metadata = json.loads((args.input / "metadata.json").read_text(encoding="utf-8"))
    expected = dict(protocol="campaign-015-neutral-followup-1", rules_version="v0-darwin-1",
                    status="complete", completed_runs=4, steps=30000, reference_prefix_ticks=3000,
                    cases=[list(c) for c in cases])
    if any(metadata.get(k) != v for k, v in expected.items()):
        raise ValueError("Incomplete or changed protocol")
    baseline = dict(seed=42, width=32, height=32, initial_population=80, initial_energy=24,
                    initial_food=8, food_capacity=24, regrowth_probability=40, regrowth_amount=4,
                    feeding_rate=8, basal_cost=1, movement_cost=1, birth_threshold=40,
                    birth_cost=4, mutation_probability=100, mutation_step=100)
    if metadata["baseline_config"] != baseline:
        raise ValueError("Baseline differs")
    results = json.loads((args.input / "results.json").read_text(encoding="utf-8"))
    indexed = {(r["movement_cost"], r["initial_b"], r["seed"]): r for r in results}
    if len(results) != 4 or set(indexed) != set(cases):
        raise ValueError("Incomplete or duplicate cohort")
    hashes, reference_hashes, verified = {}, {}, []
    for cost, initial_b, seed in cases:
        filename = f"cost-{cost}-b-{initial_b}-neutral-seed-{seed}.csv"
        path, reference = args.input / filename, args.reference / filename
        reference_hashes[filename] = digest(reference)
        if reference_hashes[filename] != prior["input_sha256"][filename]:
            raise ValueError("Historical input hash differs")
        record = dict(movement_cost=cost, initial_b=initial_b, treatment="neutral", b_trait=250,
                      seed=seed, **verify_followup(read_rows(path), read_rows(reference), cost, initial_b))
        if record != indexed[cost, initial_b, seed]:
            raise ValueError("Summary or observations differ from raw records")
        verified.append(record)
        hashes[filename] = digest(path)
    if metadata["reference_sha256"] != reference_hashes:
        raise ValueError("Recorded reference hashes differ")
    report = dict(scope="Conditional selected cohort; metric consistency and historical prefix, not full individual history or stable coexistence.",
                  metric_rows_checked=120004, prefix_rows_compared=12004, runs=verified,
                  input_sha256=hashes, reference_sha256=reference_hashes,
                  prior_verification_sha256=digest(prior_path),
                  metadata_sha256=digest(args.input / "metadata.json"),
                  script_sha256=digest(Path(__file__)),
                  helper_sha256=digest(Path(__file__).with_name("summarize_v0_frequency_cost.py")))
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps([{k: r[k] for k in ("movement_cost", "initial_b", "seed", "a", "b", "a_loss_tick", "b_loss_tick", "extinction_tick")} for r in verified], indent=2))


if __name__ == "__main__":
    main()
