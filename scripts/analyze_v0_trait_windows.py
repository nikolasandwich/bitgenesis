"""Retrospective contiguous 1000-tick decomposition windows for campaign 001."""

import argparse
from collections import defaultdict
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import analyze_v0_trait_change as decomposition


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
            root = args.input / f"{treatment}-seed-{seed}"
            for filename in ("metadata.json", "lineage.json", "events.jsonl", "metrics.csv", "summary.json"):
                if hashlib.sha256((root / filename).read_bytes()).hexdigest() != reference["input_sha256"][f"{root.name}/{filename}"]:
                    raise ValueError("Input differs from audited decomposition")
            lineage = json.loads((root / "lineage.json").read_text(encoding="utf-8"))
            genes = {o["id"]: o["genome"] for o in lineage}
            living = {o["id"]: o["genome"] for o in lineage if o["birth_tick"] == 0}
            events = defaultdict(list)
            with (root / "events.jsonl").open(encoding="utf-8") as stream:
                for line in stream:
                    e = json.loads(line)
                    events[e["tick"]].append(e)
            sums = [Fraction(0) for _ in range(4)]
            all_sums = sums.copy()
            start_mean = Fraction(sum(living.values()), len(living))
            birth_count = death_count = 0
            for tick in range(1, 5001):
                count, total = len(living), sum(living.values())
                parents, children, dead = [], [], []
                for e in events[tick]:
                    if e["event"] == "birth":
                        parents.append(genes[e["parent_id"]])
                        children.append(e["genome"])
                        living[e["id"]] = e["genome"]
                    else:
                        dead.append(living.pop(e["id"]))
                parts = decomposition.components(count, total, parents, children, dead)
                sums = [a+b for a, b in zip(sums, parts)]
                birth_count += len(children)
                death_count += len(dead)
                if tick % 1000 == 0:
                    end_mean = Fraction(sum(living.values()), len(living))
                    if sums[3] != end_mean - start_mean or sum(sums[:3]) != sums[3]:
                        raise ValueError("Window decomposition does not telescope")
                    rows.append({"treatment": treatment, "seed": seed, "start_tick": tick-999,
                        "end_tick": tick, "mean_before_window": float(start_mean), "mean_after_window": float(end_mean),
                        "births": birth_count, "deaths": death_count,
                        **dict(zip(("birth_sorting", "death_sorting", "transmitted_mutation", "net_change"), map(float, sums)))})
                    all_sums = [a+b for a, b in zip(all_sums, sums)]
                    sums = [Fraction(0) for _ in range(4)]
                    birth_count = death_count = 0
                    start_mean = end_mean
            prior = next(r for r in reference["runs"] if r["treatment"] == treatment and r["seed"] == seed)
            if any(float(value) != prior[key] for value, key in zip(all_sums, ("birth_sorting", "death_sorting", "transmitted_mutation", "net_change"))):
                raise ValueError("Window totals differ from complete-run decomposition")
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "windows.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {"scope": "Five contiguous equal windows per existing world; post hoc, not independent replicates or a stationarity test.",
        "windows": rows, "reference_sha256": hashlib.sha256(args.reference.read_bytes()).hexdigest(),
        "input_sha256": reference["input_sha256"],
        "helper_sha256": hashlib.sha256(Path(decomposition.__file__).read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps([r for r in rows if r["start_tick"] == 4001], indent=2))


if __name__ == "__main__":
    main()
