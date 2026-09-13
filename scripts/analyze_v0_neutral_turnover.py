"""Measure demographic turnover after label loss using audited campaign-015 records."""

import argparse
import csv
import hashlib
import json
from pathlib import Path


def window(rows, start, end):
    """Count events on (start, end]; state ranges include both endpoints."""
    if not 0 <= start < end < len(rows):
        raise ValueError("Invalid observation window")
    selected = rows[start:end+1]
    if [r["tick"] for r in selected] != list(range(start, end+1)):
        raise ValueError("Disordered or incomplete observation window")
    births = selected[-1]["births"]-selected[0]["births"]
    deaths = selected[-1]["deaths"]-selected[0]["deaths"]
    if min(births, deaths) < 0 or selected[-1]["population"]-selected[0]["population"] != births-deaths:
        raise ValueError("Birth/death accounting mismatch")
    return dict(start_tick=start, end_tick=end, births=births, deaths=deaths,
                population_start=selected[0]["population"], population_end=selected[-1]["population"],
                population_min=min(r["population"] for r in selected),
                population_max=max(r["population"] for r in selected),
                founders_min=min(r["founder_lineages"] for r in selected),
                founders_max=max(r["founder_lineages"] for r in selected),
                variants_min=min(r["genome_variants"] for r in selected),
                variants_max=max(r["genome_variants"] for r in selected))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/campaign-015"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    reference = root / "docs/research/results/campaign-015-verification.json"
    report = json.loads(reference.read_text(encoding="utf-8"))
    keys = [(r["movement_cost"], r["initial_b"], r["seed"]) for r in report["runs"]]
    if keys != [(1,72,1206),(2,8,1200),(2,72,1208),(4,72,1208)]:
        raise ValueError("Expected complete selected cohort")
    results, hashes = [], {}
    for record in report["runs"]:
        cost, initial_b, seed = record["movement_cost"], record["initial_b"], record["seed"]
        path = args.input / f"cost-{cost}-b-{initial_b}-neutral-seed-{seed}.csv"
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        if hashes[path.name] != report["input_sha256"][path.name]:
            raise ValueError("Input differs from independent audit")
        with path.open(encoding="utf-8", newline="") as stream:
            rows = [{k: int(r[k]) for k in ("tick", "births", "deaths", "population", "founder_lineages", "genome_variants", "a", "b")}
                    for r in csv.DictReader(stream)]
        if len(rows) != 30001:
            raise ValueError("Incomplete record")
        loss = record["a_loss_tick"] if record["a_loss_tick"] is not None else record["b_loss_tick"]
        if loss is None or not 3000 < loss < 5000:
            raise ValueError("Expected previously verified early group loss")
        lost = "a" if record["a_loss_tick"] is not None else "b"
        if any(r[lost] for r in rows[loss:]):
            raise ValueError("Lost group reappeared")
        for name, start in (("after_group_loss", loss), ("common_late_window", 5000)):
            results.append(dict(movement_cost=cost, initial_b=initial_b, seed=seed, window=name,
                                **window(rows, start, 30000)))
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "turnover.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    result = dict(analysis="neutral-turnover-015-1", retrospective=True, runs=results,
                  input_sha256=hashes, reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  scope="Event differences on (start,end]; state ranges include endpoints. Selected worlds and overlapping windows are not independent samples. No mutation, new trait or functional innovation claim.")
    (args.output / "summary.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
