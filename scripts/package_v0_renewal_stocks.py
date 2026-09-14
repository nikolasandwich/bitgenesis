"""Package the campaign-020 renewal-stock supplement with its complete reanalysis inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

from verify_v0_review import verify


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    def git(*args):return subprocess.check_output(["git","-C",str(root),*args],text=True).strip()
    if git("status","--porcelain"):raise ValueError("Commit source before packaging")
    if args.output.exists():raise FileExistsError("Choose a new archive path")
    checks={"summarize_v0_renewal_granularity.py":"campaign-020-verification.json",
            "verify_v0_renewal_granularity_observations.py":"campaign-020-observations.json",
            "summarize_v0_renewal_granularity_processes.py":"campaign-020-processes.json",
            "analyze_v0_supply_windows.py":"supply-windows-020.json",
            "calibrate_v0_renewal_capacity.py":"renewal-capacity-020.json",
            "verify_v0_renewal_stocks.py":"renewal-stocks-020-verification.json",
            "summarize_v0_renewal_stocks.py":"renewal-stocks-020-summary.json"}
    with tempfile.TemporaryDirectory() as temp:
        outputs={script:Path(temp)/str(i) for i,script in enumerate(checks)}
        for script,reference in checks.items():
            command=[sys.executable,"-S",str(root/"scripts"/script),"--output",str(outputs[script])]
            if script=="verify_v0_renewal_granularity_observations.py":
                command.extend(["--metrics-verification",str(outputs["summarize_v0_renewal_granularity.py"]/"summary.json")])
            if script=="summarize_v0_renewal_stocks.py":
                command.extend(["--input",str(outputs["verify_v0_renewal_stocks.py"]/"summary.json")])
            subprocess.run(command,cwd=root,check=True,stdout=subprocess.DEVNULL)
            actual=json.loads((outputs[script]/"summary.json").read_text(encoding="utf-8"))
            expected=json.loads((root/"docs/research/results"/reference).read_text(encoding="utf-8"))
            if actual!=expected:raise ValueError(f"Reanalysis differs: {script}")
    files=[root/name for name in git("ls-files").splitlines()]
    datasets=("campaign-020","renewal-stocks-020")
    for name in datasets:
        directory=root/"data"/name
        if not directory.is_dir():raise ValueError(f"Missing dataset: {name}")
        files.extend(p for p in directory.rglob("*") if p.is_file())
    files=sorted(set(files))
    def digest(p):
        with p.open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()
    if any(not p.resolve().is_relative_to(root) for p in files):raise ValueError("Payload escapes source")
    manifest=dict(format="bitgenesis-review-1",git_commit=git("rev-parse","HEAD"),observation_revision=1,observation_campaign="020",
        scope="Renewal-stock supplement: tracked source, campaign-020 original records and registered first-100-tick stock replay. Earlier campaigns raw data, other retrospective datasets and visual review pages are not included.",
        datasets=list(datasets),reanalysis_reports_equal=list(checks.values()),
        files={"bitgenesis/"+p.relative_to(root).as_posix():dict(sha256=digest(p),bytes=p.stat().st_size) for p in files})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.output,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,"bitgenesis/"+p.relative_to(root).as_posix())
        z.writestr("MANIFEST.json",json.dumps(manifest,indent=2)+"\n")
        z.writestr("START-HERE.txt",f"BitGenesis campaign-020 renewal-stock supplement\n\nExtract into a NEW folder; keep earlier archives unchanged.\nRead bitgenesis/docs/research/renewal-stocks-020.md and docs/design/renewal-stock-supplement.md.\nIncludes original campaign 020 and its first-100-tick stock replay, not all twenty campaigns.\n{len(checks)} reanalyses matched saved reports before packaging. Fresh extracted verification is separate.\n")
    result=verify(args.output)
    sha=digest(args.output)
    args.output.with_suffix(args.output.suffix+".sha256").write_text(sha+"  "+args.output.name+"\n",encoding="utf-8")
    print(json.dumps(dict(**result,bytes=args.output.stat().st_size),indent=2))


if __name__=="__main__":main()
