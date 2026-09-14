"""Check schema-2 replay equivalence and count realized versus space-blocked births."""

import argparse
import csv
import hashlib
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=Path("data/feeding-replay-017-schema2"))
    parser.add_argument("--previous",type=Path,default=Path("data/feeding-replay-017"))
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    old_report=root/"docs/research/results/feeding-replay-017.json"
    old=json.loads(old_report.read_text(encoding="utf-8"))["results"]
    verified=json.loads((root/"docs/research/results/campaign-017-verification.json").read_text(encoding="utf-8"))["runs"]
    key=lambda r:(r["arm"],r["birth_threshold"],r["seed"])
    originals={key(r):r for r in old};outcomes={key(r):r for r in verified}
    metadata=json.loads((args.input/"metadata.json").read_text(encoding="utf-8"))
    runs=json.loads((args.input/"results.json").read_text(encoding="utf-8"))
    if metadata["status"]!="complete" or metadata["completed_runs"]!=40 or len(runs)!=40 or {key(r) for r in runs}!=set(originals):
        raise ValueError("Incomplete replay grid")
    results=[];hashes={}
    for run in runs:
        identity=key(run);name=f"{identity[0]}-threshold-{identity[1]}-seed-{identity[2]}-feeding.jsonl"
        old_path=args.previous/name;path=args.input/name
        for p,expected in ((old_path,originals[identity]["feeding_sha256"]),(path,run["feeding_sha256"])):
            if hashlib.sha256(p.read_bytes()).hexdigest()!=expected:raise ValueError("Replay file hash differs")
        previous=[json.loads(line) for line in old_path.read_text(encoding="utf-8").splitlines()]
        current=[json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        if len(current)!=len(previous):raise ValueError("Feeding row count changed")
        eligible=blocked=births=0;children=set()
        for before,row in zip(previous,current):
            if {k:row[k] for k in before}!=before:raise ValueError("Original feeding fields changed")
            if row["observation_schema"]!=2 or type(row["birth_eligible"]) is not bool:
                raise ValueError("Expected schema-2 birth observation")
            free=row["empty_neighbors_before_birth"]
            if type(free) is not int or not 0<=free<=4:raise ValueError("Invalid neighbor count")
            actual=row["child_id"] is not None
            if row["birth_eligible"]!=(row["energy_before_feeding"]+row["eaten"]>=identity[1]):
                raise ValueError("Eligibility differs from energy threshold")
            if actual!=(row["birth_eligible"] and free>0):raise ValueError("Birth outcome differs from eligibility/space")
            if actual:
                if type(row["child_id"]) is not int or row["child_id"]<80 or row["child_id"] in children:
                    raise ValueError("Invalid or duplicate child")
                children.add(row["child_id"])
            eligible+=row["birth_eligible"];blocked+=row["birth_eligible"] and free==0;births+=actual
        if births!=outcomes[identity]["births_at_100"] or eligible!=blocked+births:
            raise ValueError("Birth totals differ from original campaign")
        results.append(dict(arm=identity[0],birth_threshold=identity[1],seed=identity[2],
            feeding_attempts=len(current),eligible_attempts=eligible,space_blocked_attempts=blocked,
            births=births,blocked_fraction_of_eligible=blocked/eligible if eligible else None))
        hashes[name]=run["feeding_sha256"]
    groups=[]
    for arm in ("dispersed","block"):
        for threshold in (40,160):
            selected=[r for r in results if r["arm"]==arm and r["birth_threshold"]==threshold]
            groups.append(dict(arm=arm,birth_threshold=threshold,ranges={k:[min(r[k] for r in selected),max(r[k] for r in selected)]
                for k in ("eligible_attempts","space_blocked_attempts","births")}))
    report=dict(scope="Retrospective ticks 1–100, feeding survivors only. A blocked attempt is not a unique individual, lost lifetime birth, or causal mediation estimate.",
        replay_source=metadata["git_commit"],results=results,groups=groups,input_sha256=hashes,
        original_report_sha256=hashlib.sha256(old_report.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/"summary.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    with (args.output/"opportunities.csv").open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(results[0]));writer.writeheader();writer.writerows(results)
    print(json.dumps(groups,indent=2))


if __name__=="__main__":main()
