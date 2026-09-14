"""Descriptive per-world feeding distributions on campaign-017 historical prefixes."""

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=Path("data/feeding-replay-017"))
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    vp=Path(__file__).resolve().parents[1]/"docs/research/results/feeding-replay-017.json"
    verification=json.loads(vp.read_text(encoding="utf-8"));records=verification["results"]
    if len(records)!=40 or {(r["arm"],r["birth_threshold"],r["seed"]) for r in records}!={
            (a,t,s) for a in ("dispersed","block") for t in (40,160) for s in range(1400,1410)}:
        raise ValueError("Incomplete replay grid")
    results=[]
    for r in records:
        name=f"{r['arm']}-threshold-{r['birth_threshold']}-seed-{r['seed']}-feeding.jsonl"
        path=args.input/name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=r["feeding_sha256"]:
            raise ValueError("Feeding record differs from verified replay")
        hist=Counter();seen=set()
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                row=json.loads(line);key=(row["tick"],row["id"])
                if key in seen or not 1<=row["tick"]<=100 or type(row["eaten"]) is not int or not 0<=row["eaten"]<=8:
                    raise ValueError("Invalid or duplicate feeding record")
                seen.add(key);hist[row["eaten"]]+=1
        count=sum(hist.values());total=sum(k*v for k,v in hist.items())
        if count!=r["feeding_attempts"] or total!=r["food_eaten"] or hist[0]!=r["zero_intake_attempts"]:
            raise ValueError("Replay summary differs from individual rows")
        results.append(dict(arm=r["arm"],birth_threshold=r["birth_threshold"],seed=r["seed"],
            attempts=count,zero_intake_attempts=hist[0],positive_intake_attempts=count-hist[0],
            food_eaten=total,zero_intake_fraction=hist[0]/count,
            mean_intake_per_attempt=total/count,mean_intake_when_positive=total/(count-hist[0]),
            intake_histogram={str(k):hist[k] for k in range(9)}))
    groups=[]
    for arm in ("dispersed","block"):
        for threshold in (40,160):
            subset=[r for r in results if r["arm"]==arm and r["birth_threshold"]==threshold]
            groups.append(dict(arm=arm,birth_threshold=threshold,
                ranges={k:[min(r[k] for r in subset),max(r[k] for r in subset)] for k in (
                    "attempts","zero_intake_fraction","mean_intake_per_attempt","mean_intake_when_positive")}))
    args.output.mkdir(parents=True,exist_ok=False)
    report=dict(scope="Retrospective per-world descriptive ranges, ticks 1–100. Feeding records require survival to feeding; no causal or independent-attempt inference.",
        results=results,groups=groups,verification_sha256=hashlib.sha256(vp.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (args.output/"summary.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    flat=[{k:v for k,v in r.items() if k!="intake_histogram"} for r in results]
    with (args.output/"worlds.csv").open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
    print(json.dumps(groups,indent=2))


if __name__=="__main__":main()
