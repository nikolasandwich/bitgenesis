"""Reconcile complete movement-attempt denominators from verified action observations."""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]/"docs/research/results"
    paths=[root/"movement-observations-017.json",root/"action-replay-017.json"]
    movement,terminal=[json.loads(p.read_text(encoding="utf-8")) for p in paths]
    key=lambda r:(r["arm"],r["birth_threshold"],r["seed"])
    a={key(r):r for r in movement["results"]};b={key(r):r for r in terminal["results"]}
    expected={(arm,t,s) for arm in ("dispersed","block") for t in (40,160) for s in range(1400,1410)}
    if len(movement["results"])!=40 or len(terminal["results"])!=40 or set(a)!=expected or set(b)!=expected:
        raise ValueError("Incomplete or mismatched verified grids")
    rows=[]
    for identity,m in a.items():
        d=b[identity];name=f"{identity[0]}-threshold-{identity[1]}-seed-{identity[2]}-feeding.jsonl"
        if d["feeding_sha256"]!=movement["input_sha256"][name]:raise ValueError("Incompatible feeding observations")
        if m["movement_attempts"]!=m["successful_moves"]+m["blocked_moves"] or d["total_deaths"]!=d["basal_deaths"]+d["movement_payment_deaths"]:
            raise ValueError("Component accounting differs")
        total=m["movement_attempts"]+d["movement_payment_deaths"]
        if total<=0:raise ValueError("No attempts in declared dataset")
        rows.append(dict(arm=identity[0],birth_threshold=identity[1],seed=identity[2],
            all_movement_attempts=total,successful_moves=m["successful_moves"],occupied_target_blocks=m["blocked_moves"],
            movement_payment_deaths=d["movement_payment_deaths"],
            success_fraction=m["successful_moves"]/total,blocked_fraction=m["blocked_moves"]/total,
            payment_death_fraction=d["movement_payment_deaths"]/total,
            prior_feeding_conditioned_blocked_fraction=m["blocked_fraction"]))
    groups=[]
    for arm in ("dispersed","block"):
        for threshold in (40,160):
            subset=[r for r in rows if r["arm"]==arm and r["birth_threshold"]==threshold]
            groups.append(dict(arm=arm,birth_threshold=threshold,ranges={k:[min(r[k] for r in subset),max(r[k] for r in subset)]
                for k in ("all_movement_attempts","blocked_fraction","payment_death_fraction","success_fraction")}))
    report=dict(scope="Retrospective all movement attempts in ticks 1–100, including lethal payments. Three outcomes partition attempts. Per-world descriptive ranges, not independent-action or causal estimates.",
        results=rows,groups=groups,input_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/"summary.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    with (args.output/"movements.csv").open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(json.dumps(groups,indent=2))


if __name__=="__main__":main()
