"""Compare schema-3 observations with prior rows and summarize feeding-conditioned moves."""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=Path("data/feeding-replay-017-schema3"))
    parser.add_argument("--previous",type=Path,default=Path("data/feeding-replay-017-schema2"))
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    vp=root/"docs/research/results/birth-opportunities-017.json"
    previous_report=json.loads(vp.read_text(encoding="utf-8"))
    runs=json.loads((args.input/"results.json").read_text(encoding="utf-8"))
    metadata=json.loads((args.input/"metadata.json").read_text(encoding="utf-8"))
    if metadata["status"]!="complete" or len(runs)!=40 or {(r["arm"],r["birth_threshold"],r["seed"]) for r in runs}!={
            (a,t,s) for a in ("dispersed","block") for t in (40,160) for s in range(1400,1410)}:
        raise ValueError("Incomplete replay grid")
    results=[];hashes={}
    for run in runs:
        name=f"{run['arm']}-threshold-{run['birth_threshold']}-seed-{run['seed']}-feeding.jsonl"
        oldpath=args.previous/name;newpath=args.input/name
        for p,digest in ((oldpath,previous_report["input_sha256"][name]),(newpath,run["feeding_sha256"])):
            if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError("Replay hash differs")
        old=[json.loads(x) for x in oldpath.read_text(encoding="utf-8").splitlines()]
        new=[json.loads(x) for x in newpath.read_text(encoding="utf-8").splitlines()]
        if len(old)!=len(new) or len(new)!=run["feeding_attempts"]:raise ValueError("Row counts differ")
        attempted=moved=0
        for before,row in zip(old,new):
            if any(row[k]!=v for k,v in before.items() if k!="observation_schema"):
                raise ValueError("Original observation fields changed")
            if before["observation_schema"]!=2 or row["observation_schema"]!=3:
                raise ValueError("Unexpected observation schema")
            if any(type(row[k]) is not bool for k in ("movement_attempted","moved")):
                raise ValueError("Invalid movement flag")
            start,end=row["position_before_action"],row["position"]
            if type(start) is not int or not 0<=start<1024 or row["moved"]!=(start!=end):
                raise ValueError("Position/displacement mismatch")
            if row["moved"]:
                x,y=start%32,start//32
                neighbors={y*32+(x+1)%32,y*32+(x-1)%32,((y+1)%32)*32+x,((y-1)%32)*32+x}
                if not row["movement_attempted"] or end not in neighbors:raise ValueError("Invalid cardinal move")
            attempted+=row["movement_attempted"];moved+=row["moved"]
        results.append(dict(arm=run["arm"],birth_threshold=run["birth_threshold"],seed=run["seed"],
            feeding_rows=len(new),movement_attempts=attempted,successful_moves=moved,
            blocked_moves=attempted-moved,no_attempt=len(new)-attempted,
            blocked_fraction=(attempted-moved)/attempted if attempted else None))
        hashes[name]=run["feeding_sha256"]
    groups=[]
    for arm in ("dispersed","block"):
        for threshold in (40,160):
            subset=[r for r in results if r["arm"]==arm and r["birth_threshold"]==threshold]
            groups.append(dict(arm=arm,birth_threshold=threshold,ranges={k:[min(r[k] for r in subset),max(r[k] for r in subset)]
                for k in ("movement_attempts","successful_moves","blocked_moves","blocked_fraction")}))
    report=dict(scope="Retrospective first hundred ticks; movement among individuals reaching feeding only. No lethal-movement denominator or causal congestion estimate.",
        replay_source=metadata["git_commit"],results=results,groups=groups,input_sha256=hashes,
        previous_report_sha256=hashlib.sha256(vp.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/"summary.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    with (args.output/"moves.csv").open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(results[0]));writer.writeheader();writer.writerows(results)
    print(json.dumps(groups,indent=2))


if __name__=="__main__":main()
