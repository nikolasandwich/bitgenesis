"""Check that changing neutral founder labels leaves recorded physical metrics identical."""

import argparse
import csv
import hashlib
from itertools import zip_longest
import json
from pathlib import Path


LABEL_FIELDS = {"a", "b", "b_fraction"}


def compare_rows(small, large):
    count = 0
    for left, right in zip_longest(small, large):
        if left is None or right is None:
            raise ValueError("Neutral series have unequal lengths")
        if set(left) != set(right) or not LABEL_FIELDS <= set(left):
            raise ValueError("Neutral series have incompatible fields")
        if {k:v for k,v in left.items() if k not in LABEL_FIELDS} != {k:v for k,v in right.items() if k not in LABEL_FIELDS}:
            raise ValueError("Neutral labels changed recorded physical metrics")
        if int(left["b"]) > int(right["b"]) or int(left["a"]) < int(right["a"]):
            raise ValueError("Nested founder-label membership is inconsistent")
        count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=Path("data/campaign-014"))
    parser.add_argument("--reference",type=Path,default=Path("docs/research/results/campaign-014-verification.json"))
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    pairs, hashes = [], {}
    for cost in (1,2,3,4):
        for seed in range(1200,1210):
            paths = [args.input/f"cost-{cost}-b-{b}-neutral-seed-{seed}.csv" for b in (8,72)]
            for path in paths:
                hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
                if hashes[path.name] != reference["input_sha256"][path.name]:
                    raise ValueError("Input differs from independently verified campaign")
            with paths[0].open(encoding="utf-8",newline="") as a, paths[1].open(encoding="utf-8",newline="") as b:
                count = compare_rows(csv.DictReader(a),csv.DictReader(b))
            if count != 3001:
                raise ValueError("Incomplete neutral pair")
            pairs.append({"movement_cost":cost,"seed":seed,"paired_rows_checked":count})
    args.output.mkdir(parents=True,exist_ok=False)
    report = {"scope":"Cross-arm equality of all saved non-label metric fields and nested group counts; unsaved spatial and RNG states are not compared.",
        "pairs":pairs,"paired_rows_checked":sum(r["paired_rows_checked"] for r in pairs),
        "input_sha256":hashes,"reference_sha256":hashlib.sha256(args.reference.read_bytes()).hexdigest(),
        "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.output/"summary.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(f"Verified {len(pairs)} neutral pairs / {report['paired_rows_checked']} paired rows")


if __name__ == "__main__":
    main()
