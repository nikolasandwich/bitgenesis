"""Check retrospective campaign counts against committed compact result tables."""

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re


def check(root, inventory):
    entries = inventory["campaigns"]
    if inventory["format"] != "bitgenesis-campaign-inventory-1" or not entries:
        raise ValueError("Unsupported or empty inventory")
    seen, hashes = {}, {}
    executions = ticks = followups = replayed = 0
    for entry in entries:
        identity = entry["id"]
        if not re.fullmatch(r"\d{3}", identity) or identity in seen:
            raise ValueError("Invalid or duplicate campaign ID")
        path = root / "docs/research/results" / f"campaign-{identity}.csv"
        with path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        expected_count, horizon = entry["executions"], entry["ticks_per_execution"]
        keys = [tuple(row[field] for field in entry["identity_fields"]) for row in rows]
        seeds = Counter(int(row["seed"]) for row in rows)
        if "seed_counts" in entry:
            if "seed_range" in entry or any(type(v) is not int or v <= 0 for v in entry["seed_counts"].values()):
                raise ValueError("Ambiguous or invalid explicit seed counts")
            expected_seeds = {int(k): v for k, v in entry["seed_counts"].items()}
        else:
            start, end = entry["seed_range"]
            expected_seeds = {s: expected_count / (end-start+1) for s in range(start, end+1)}
        if (len(rows) != expected_count or len(set(keys)) != expected_count
                or any(int(row["tick"]) != horizon for row in rows)
                or seeds != expected_seeds):
            raise ValueError(f"Count, horizon or unique seed grid differs: {identity}")
        prefix = entry["replayed_prefix_ticks_per_execution"]
        if not 0 <= prefix <= horizon:
            raise ValueError("Invalid replayed prefix length")
        if entry["followup_of"] is not None:
            prior, prior_rows = seen[entry["followup_of"]]
            prior_keys = {tuple(row[field] for field in entry["identity_fields"]) for row in prior_rows}
            if not set(keys) <= prior_keys or prefix != prior["ticks_per_execution"]:
                raise ValueError("Follow-up identities or replayed horizon differ from reference")
            followups += expected_count
        elif prefix:
            raise ValueError("Replayed prefix requires a reference campaign")
        executions += expected_count
        ticks += expected_count * horizon
        replayed += expected_count * prefix
        seen[identity] = (entry, rows)
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"campaigns": len(entries), "executions": executions, "computed_ticks": ticks,
            "followup_executions": followups, "replayed_prefix_ticks": replayed,
            "computed_ticks_excluding_declared_replays": ticks - replayed,
            "scope": "Counting and identity checks only; these totals are not independent replicate counts.",
            "input_sha256": hashes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    path = args.root / "experiments/v0/campaign-inventory.json"
    result = check(args.root, json.loads(path.read_text(encoding="utf-8")))
    result["inventory_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    result["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if args.output:
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2)
            stream.write("\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
