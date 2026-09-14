"""Reconstruct active IDs from feeding births and terminal records for campaign 017."""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=Path("data/action-replay-017"))
    parser.add_argument("--reference",type=Path,default=Path("data/campaign-017"))
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    verification=json.loads((root/"docs/research/results/campaign-017-verification.json").read_text(encoding="utf-8"))
    previous=json.loads((root/"docs/research/results/movement-observations-017.json").read_text(encoding="utf-8"))
    metadata=json.loads((args.input/"metadata.json").read_text(encoding="utf-8"))
    records=json.loads((args.input/"results.json").read_text(encoding="utf-8"))
    if metadata["status"]!="complete" or metadata["feeding_schema"]!=3 or metadata["terminal_schema"]!=1 or len(records)!=40 or {(r["arm"],r["birth_threshold"],r["seed"]) for r in records}!={
            (a,t,s) for a in ("dispersed","block") for t in (40,160) for s in range(1400,1410)}:
        raise ValueError("Invalid replay scope")
    results=[]
    for record in records:
        prefix=f"{record['arm']}-threshold-{record['birth_threshold']}-seed-{record['seed']}"
        fp=args.input/(prefix+"-feeding.jsonl");dp=args.input/(prefix+"-terminal.jsonl");mp=args.reference/(prefix+".csv")
        for path,digest in ((fp,record["feeding_sha256"]),(dp,record["terminal_sha256"]),(mp,verification["input_sha256"][mp.name])):
            if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError("Input hash differs")
        if record["feeding_sha256"]!=previous["input_sha256"][fp.name]:raise ValueError("Feeding stream changed")
        feeds,deaths=defaultdict(list),defaultdict(list)
        for path,groups in ((fp,feeds),(dp,deaths)):
            for line in path.read_text(encoding="utf-8").splitlines():
                row=json.loads(line)
                if type(row["tick"]) is not int or not 1<=row["tick"]<=100:raise ValueError("Invalid tick")
                groups[row["tick"]].append(row)
        with mp.open(encoding="utf-8",newline="") as stream:
            metrics=list(csv.DictReader(stream))[:101]
        live=set(range(80));next_id=80;dead_total=basal=movement=0
        for tick in range(1,101):
            f,d=feeds[tick],deaths[tick];fi={r["id"] for r in f};di={r["id"] for r in d}
            if len(fi)!=len(f) or len(di)!=len(d) or fi&di or fi|di!=live:
                raise ValueError("Active IDs are not partitioned exactly")
            for r in d:
                if r["observation_schema"]!=1 or type(r["movement_attempted"]) is not bool or r["phase"] not in ("basal","movement"):
                    raise ValueError("Invalid terminal schema")
                moving=r["phase"]=="movement"
                if moving!=r["movement_attempted"] or r["energy_before_action"]!=(2 if moving else 1) or r["position"]!=r["position_before_action"] or not 0<=r["position"]<1024:
                    raise ValueError("Terminal phase differs from pinned unit costs")
                basal+=not moving;movement+=moving
            children=[r["child_id"] for r in f if r["child_id"] is not None]
            if sorted(children)!=list(range(next_id,next_id+len(children))):raise ValueError("Child IDs differ")
            next_id+=len(children);dead_total+=len(d);live=(live-di)|set(children)
            if len(live)!=int(metrics[tick]["population"]) or dead_total!=int(metrics[tick]["deaths"]) or next_id-80!=int(metrics[tick]["births"]):
                raise ValueError("Lifecycle differs from original metrics")
        if dead_total!=record["pre_feeding_deaths"]:raise ValueError("Death count differs")
        results.append(dict(arm=record["arm"],birth_threshold=record["birth_threshold"],seed=record["seed"],
            basal_deaths=basal,movement_payment_deaths=movement,total_deaths=dead_total,
            feeding_sha256=record["feeding_sha256"],terminal_sha256=record["terminal_sha256"]))
    report=dict(replay_source=metadata["git_commit"],runs=40,partitioned_ticks=4000,results=results,
        scope="Historical ID/lifecycle reconstruction and pinned-cost death phases; feeding bytes match prior verified observations. Not independent individual-path reference or a causal mechanism test.",
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/"summary.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(runs=40,partitioned_ticks=4000,basal_deaths=sum(r["basal_deaths"] for r in results),movement_payment_deaths=sum(r["movement_payment_deaths"] for r in results))))


if __name__=="__main__":main()
