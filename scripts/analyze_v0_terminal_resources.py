"""Post hoc campaign-019 terminal stock audit; no simulation or spatial reconstruction."""
import argparse
import csv
import hashlib
import json
from pathlib import Path


def analyze(root, verification_path):
    verification=json.loads(verification_path.read_text(encoding="utf-8"))
    runs=verification["runs"]
    fields=("arm","birth_threshold","birth_cost","seed")
    grid={("block",t,c,s) for t in (40,160) for c in (0,4) for s in range(1600,1610)}
    if len(runs)!=40 or {tuple(r[k] for k in fields) for r in runs}!=grid:
        raise ValueError("Expected complete forty-world grid")
    output=[];hashes={}
    for run in runs:
        key={k:run[k] for k in fields}
        prefix=f"block-threshold-{run['birth_threshold']}-birth-cost-{run['birth_cost']}-seed-{run['seed']}"
        path=root/(prefix+".csv");digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if digest!=verification["input_sha256"][path.name]:
            raise ValueError("Metric-verified input changed")
        hashes[path.name]=digest
        with path.open(encoding="utf-8",newline="") as stream:
            rows=list(csv.DictReader(stream))
        if len(rows)!=10001 or any(int(r["tick"])!=i for i,r in enumerate(rows)):
            raise ValueError("Incomplete tick grid")
        extinction=next((i for i,r in enumerate(rows) if int(r["population"])==0),None)
        if extinction!=run["extinction_tick"] or (extinction is None)!=run["right_censored"]:
            raise ValueError("Extinction status differs")
        if extinction is None:
            output.append(dict(**key,status="right_censored",extinction_tick=None,terminal=None))
            continue
        if extinction==0:raise ValueError("Unexpected empty founder world")
        before,after=rows[extinction-1],rows[extinction]
        before={k:int(before[k]) for k in ("population","organism_energy","food_energy","births","dissipated_energy","supplied_energy")}
        after={k:int(after[k]) for k in ("population","organism_energy","food_energy","births","dissipated_energy","supplied_energy")}
        supplied=after["supplied_energy"]-before["supplied_energy"]
        uptake=supplied+before["food_energy"]-after["food_energy"]
        paid=after["dissipated_energy"]-before["dissipated_energy"]
        if after["population"] or after["organism_energy"] or after["births"]!=before["births"] or uptake!=0 or paid!=before["population"] or before["organism_energy"]!=before["population"]:
            raise ValueError("Terminal transition contradicts unit-basal death before feeding")
        output.append(dict(**key,status="extinct",extinction_tick=extinction,terminal=dict(
            prior_population=before["population"],prior_organism_energy=before["organism_energy"],
            prior_food_energy=before["food_energy"],food_energy=after["food_energy"],
            resource_added=supplied,food_eaten=uptake,dissipated=paid)))
    extinct=[r for r in output if r["status"]=="extinct"]
    return dict(analysis="campaign-019-terminal-resources-posthoc-1",rows=output,
        extinct_worlds=len(extinct),right_censored_worlds=len(output)-len(extinct),
        extinct_with_positive_food=sum(r["terminal"]["food_energy"]>0 for r in extinct),
        input_sha256=hashes,metric_report_sha256=hashlib.sha256(verification_path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope="Post hoc inspection of all campaign-019 outcomes. Terminal stock quantities condition on extinction; survivors have no terminal extinction measurement. Positive global food does not establish local accessibility. The basal-death interpretation uses unchanged unit-basal V0 rules, not retained terminal actor observations beyond tick 100. No new replicate or unique causal mechanism.")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=Path("data/campaign-019"))
    parser.add_argument("--verification",type=Path,default=Path("docs/research/results/campaign-019-verification.json"))
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();result=analyze(args.input,args.verification)
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/"summary.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("extinct_worlds","right_censored_worlds","extinct_with_positive_food")}))


if __name__=="__main__":main()
