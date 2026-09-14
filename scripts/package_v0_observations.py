"""Package the campaign-017 observation supplement with its complete reanalysis inputs."""
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
    checks={"analyze_v0_feeding_attempts.py":"feeding-attempts-017.json",
            "analyze_v0_birth_opportunities.py":"birth-opportunities-017.json",
            "analyze_v0_movement_observations.py":"movement-observations-017.json",
            "verify_v0_action_replay.py":"action-replay-017.json",
            "analyze_v0_complete_movement.py":"complete-movement-017.json",
            "analyze_v0_individual_intake.py":"individual-intake-017.json",
            "verify_v0_energy_replay.py":"energy-replay-017.json",
            "analyze_v0_cohort_energy.py":"cohort-energy-017.json"}
    for script,reference in checks.items():
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/"checked"
            subprocess.run([sys.executable,"-I","-S",str(root/"scripts"/script),"--output",str(output)],cwd=root,check=True,stdout=subprocess.DEVNULL)
            actual=json.loads((output/"summary.json").read_text(encoding="utf-8"))
            expected=json.loads((root/"docs/research/results"/reference).read_text(encoding="utf-8"))
            if actual!=expected:raise ValueError(f"Reanalysis differs: {script}")
    files=[root/name for name in git("ls-files").splitlines()]
    datasets=("campaign-017","feeding-replay-017","feeding-replay-017-schema2",
              "feeding-replay-017-schema3","action-replay-017","energy-replay-017")
    for name in datasets:
        directory=root/"data"/name
        if not directory.is_dir():raise ValueError(f"Missing dataset: {name}")
        files.extend(p for p in directory.rglob("*") if p.is_file())
    files=sorted(set(files))
    def digest(p):
        with p.open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()
    if any(not p.resolve().is_relative_to(root) for p in files):raise ValueError("Payload escapes source")
    manifest=dict(format="bitgenesis-review-1",git_commit=git("rev-parse","HEAD"),observation_revision=2,
        scope="Observation supplement: tracked source, campaign-017 original records and five successive observer replays including per-action energy. Earlier campaigns' raw data and visual review pages are not included.",
        datasets=list(datasets),reanalysis_reports_equal=list(checks.values()),
        files={"bitgenesis/"+p.relative_to(root).as_posix():dict(sha256=digest(p),bytes=p.stat().st_size) for p in files})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.output,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,"bitgenesis/"+p.relative_to(root).as_posix())
        z.writestr("MANIFEST.json",json.dumps(manifest,indent=2)+"\n")
        z.writestr("START-HERE.txt","BitGenesis observation supplement\n\nExtract into a NEW folder; keep earlier review archives unchanged.\nRead bitgenesis/docs/research/mechanism-summary.zh-CN.md and docs/design/observation-supplement.md.\nThis contains campaign 017 and its observer replays, not raw data for all seventeen campaigns.\nEight standard-library reanalyses matched their complete saved reports before packaging.\nIndependent extracted reanalysis is a separate verification step.\n")
    result=verify(args.output)
    sha=digest(args.output)
    args.output.with_suffix(args.output.suffix+".sha256").write_text(sha+"  "+args.output.name+"\n",encoding="utf-8")
    print(json.dumps(dict(**result,bytes=args.output.stat().st_size),indent=2))


if __name__=="__main__":main()
