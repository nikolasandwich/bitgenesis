"""Retrospective exact decomposition of mean-trait change in campaign 001."""

import argparse
from collections import defaultdict
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from bitgenesis.v0.audit import audit


def components(count, total, parent_traits, child_traits, death_traits):
    """Partition one tick into demographic sorting and transmitted change."""
    if count <= 0 or len(parent_traits) != len(child_traits):
        raise ValueError("Need a living population and paired births")
    next_count = count + len(child_traits) - len(death_traits)
    if next_count <= 0:
        raise ValueError("Mean trait undefined after extinction")
    mean = Fraction(total, count)
    births = (sum(parent_traits) - len(parent_traits) * mean) / next_count
    deaths = (len(death_traits) * mean - sum(death_traits)) / next_count
    mutation = Fraction(sum(child_traits) - sum(parent_traits), next_count)
    next_total = total + sum(child_traits) - sum(death_traits)
    change = Fraction(next_total, next_count) - mean
    if births + deaths + mutation != change:
        raise ValueError("Trait-change accounting mismatch")
    return births, deaths, mutation, change


def analyze(root):
    audit(root)
    metadata = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
    lineage = json.loads((root / "lineage.json").read_text(encoding="utf-8"))
    genes = {o["id"]: o["genome"] for o in lineage}
    living = {o["id"]: o["genome"] for o in lineage if o["birth_tick"] == 0}
    events = defaultdict(list)
    with (root / "events.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            event = json.loads(line)
            events[event["tick"]].append(event)
    initial = Fraction(sum(living.values()), len(living))
    sums = [Fraction(0) for _ in range(4)]
    with (root / "metrics.csv").open(encoding="utf-8", newline="") as stream:
        rows = csv.DictReader(stream)
        next(rows)  # The complete audit already checks tick zero.
        for row in rows:
            tick = int(row["tick"])
            parents, children, dead = [], [], []
            count, total = len(living), sum(living.values())
            for event in events[tick]:
                if event["event"] == "birth":
                    parents.append(genes[event["parent_id"]])
                    children.append(event["genome"])
                    living[event["id"]] = event["genome"]
                else:
                    dead.append(living.pop(event["id"]))
            parts = components(count, total, parents, children, dead)
            sums = [a + b for a, b in zip(sums, parts)]
            mean = Fraction(sum(living.values()), len(living))
            if len(living) != int(row["population"]) or abs(float(mean) - float(row["mean_genome"])) > 1e-10:
                raise ValueError("Reconstructed living mean differs from metrics")
    final = Fraction(sum(living.values()), len(living))
    if sums[3] != final - initial or sum(sums[:3]) != sums[3]:
        raise ValueError("Cumulative decomposition does not telescope")
    return {"seed": metadata["config"]["seed"], "initial_mean": float(initial),
            "final_mean": float(final), "birth_sorting": float(sums[0]),
            "death_sorting": float(sums[1]), "transmitted_mutation": float(sums[2]),
            "net_change": float(sums[3]), "ticks_checked": metadata["completed_steps"]}


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
            result = analyze(root)
            if result["seed"] != seed or result["ticks_checked"] != 5000:
                raise ValueError("Unexpected seed or observation horizon")
            results.append({"treatment": treatment, **result})
            for filename in ("metadata.json", "lineage.json", "events.jsonl", "metrics.csv", "summary.json"):
                hashes[f"{name}/{filename}"] = hashlib.sha256((root / filename).read_bytes()).hexdigest()
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "decomposition.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    report = {"scope": "Post hoc exact identity on realized events; not a causal intervention or an adaptation test.",
              "runs": results, "input_sha256": hashes,
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
