"""Retrospective geometric access to initial food; no movement or causal inference."""

import argparse
from collections import Counter, deque
import csv
import hashlib
import json
from pathlib import Path


def distances(food, width, height):
    """Shortest cardinal distances to positive food on a torus, ignoring occupancy."""
    if width < 2 or height < 2 or len(food) != width * height:
        raise ValueError("Invalid food map dimensions")
    result = [None] * len(food)
    queue = deque()
    for position, amount in enumerate(food):
        if type(amount) is not int or amount < 0:
            raise ValueError("Invalid food energy")
        if amount:
            result[position] = 0
            queue.append(position)
    if not queue:
        raise ValueError("No initial food source")
    while queue:
        p = queue.popleft()
        x, y = p % width, p // width
        for q in (y*width+(x+1)%width, y*width+(x-1)%width,
                  ((y+1)%height)*width+x, ((y-1)%height)*width+x):
            if result[q] is None:
                result[q] = result[p] + 1
                queue.append(q)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--input", type=Path, default=root/"data/campaign-016")
    parser.add_argument("--verification", type=Path,
                        default=root/"docs/research/results/campaign-016-verification.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    verification = json.loads(args.verification.read_text(encoding="utf-8"))
    expected = {(arm, seed) for arm in ("uniform", "dispersed", "block") for seed in range(1300,1310)}
    records = verification["runs"]
    if len(records) != 30 or {(r["arm"],r["seed"]) for r in records} != expected:
        raise ValueError("Incomplete verified run grid")
    rows, histograms, hashes = [], {}, {}
    for record in records:
        name = f"{record['arm']}-seed-{record['seed']}-initial.json"
        path = args.input/name
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != verification["input_sha256"][name]:
            raise ValueError(f"Initial map hash differs: {name}")
        initial = json.loads(path.read_text(encoding="utf-8"))
        config = initial["config"]
        ds = distances(initial["food"],config["width"],config["height"])
        founder_distances = [ds[o["position"]] for o in initial["founders"]]
        if len(founder_distances) != 80 or founder_distances.count(0) != record["founders_on_food"]:
            raise ValueError("Founder exposure differs from verified report")
        food_under = sum(initial["food"][o["position"]] for o in initial["founders"])
        if food_under != record["food_under_founders"]:
            raise ValueError("Founder food energy differs from verified report")
        row = dict(arm=record["arm"], seed=record["seed"], founders_on_food=record["founders_on_food"],
                   food_under_founders=food_under, mean_distance=sum(founder_distances)/80,
                   max_distance=max(founder_distances), extinction_tick=record["extinction_tick"])
        row.update({f"founders_within_{radius}":sum(d<=radius for d in founder_distances)
                    for radius in (1,2,4,8)})
        rows.append(row)
        histograms[name] = dict(sorted(Counter(founder_distances).items()))
        hashes[name] = digest
    groups = []
    for arm in ("uniform","dispersed","block"):
        group = [r for r in rows if r["arm"]==arm]
        groups.append(dict(arm=arm, **{key:[min(r[key] for r in group),max(r[key] for r in group)]
            for key in ("founders_on_food","food_under_founders","mean_distance","max_distance",
                        "founders_within_1","founders_within_2","founders_within_4","founders_within_8")}))
    indexed = {(r["arm"],r["seed"]):r for r in rows}
    paired = {comparison:sum((indexed["block",seed]["founders_on_food"] -
                             indexed["dispersed",seed]["founders_on_food"])*sign > 0
                             for seed in range(1300,1310))
              for comparison,sign in (("block_more_founders_on_food",1),("block_fewer_founders_on_food",-1))}
    paired["equal_founders_on_food"] = 10-sum(paired.values())
    paired["block_extinct_earlier"] = sum(indexed["block",s]["extinction_tick"] <
                                         indexed["dispersed",s]["extinction_tick"] for s in range(1300,1310))
    report = dict(scope="Retrospective initial-map geometry. Distances ignore occupancy, consumption, replenishment, movement probability and energy; they are not observed paths or expected arrival times. No new world executions or causal mechanism identification.",
        rows=rows,groups=groups,paired=paired,founder_distance_histograms=histograms,input_sha256=hashes,
        verification_sha256=hashlib.sha256(args.verification.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/"summary.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    with (args.output/"founder-access.csv").open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps(groups,indent=2))


if __name__ == "__main__":
    main()
