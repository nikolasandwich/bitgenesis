"""Package tracked source and an explicit set of local review artifacts with hashes."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

from bitgenesis.v0.audit import audit
from audit_v0_world_sizes import audit as audit_world_sizes
from verify_v0_review import verify
from check_v0_campaign_inventory import check as check_inventory


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaigns", type=int, choices=(8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21), default=8)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    names = {8: "review-8", 9: "nine-campaigns", 10: "ten-campaigns", 11: "eleven-campaigns", 12: "twelve-campaigns", 13: "thirteen-campaigns", 14: "fourteen-campaigns", 15: "fifteen-campaigns", 16: "sixteen-campaigns", 17: "seventeen-campaigns", 18: "eighteen-campaigns", 19: "nineteen-campaigns", 20: "twenty-campaigns", 21: "twenty-one-campaigns"}
    args.output = args.output or Path(f"data/bitgenesis-v0-{names[args.campaigns]}.zip")
    if args.output.exists():
        raise ValueError("Review output already exists; choose a new path")
    review_page = f"review-v0-{args.campaigns}.html"
    root = Path(__file__).resolve().parents[1]
    def git(*arguments):
        return subprocess.check_output(["git", "-C", str(root), *arguments], text=True).strip()
    if git("status", "--porcelain"):
        raise ValueError("Commit or resolve working-tree changes before packaging a review")
    files = [root / name for name in git("ls-files").splitlines()]
    directories = [f"campaign-{i:03d}" for i in range(1, args.campaigns + 1)]
    for name in [*directories, "mutation-calibration-001", "acceptance-v0"]:
        directory = root / "data" / name
        if not directory.is_dir():
            raise ValueError(f"Missing review directory: {name}")
        files.extend(path for path in directory.rglob("*") if path.is_file())
    files.append(root / "data" / review_page)
    files = sorted(set(files))
    for path in files:
        if not path.resolve().is_relative_to(root) or not path.is_file():
            raise ValueError(f"Invalid or missing review input: {path}")
    audited = {"acceptance-v0": audit(root / "data" / "acceptance-v0")}
    for directory in sorted((root / "data" / "campaign-001").iterdir()):
        if directory.is_dir():
            audited[f"campaign-001/{directory.name}"] = audit(directory)
    metric_audits = {"campaign-005": audit_world_sizes(root / "data" / "campaign-005")}
    inventory = json.loads((root / "experiments/v0/campaign-inventory.json").read_text(encoding="utf-8"))
    inventory["campaigns"] = inventory["campaigns"][:args.campaigns]
    workload = check_inventory(root, inventory)
    helpers = {9: "summarize_v0_energy_allocation.py",
               10: "summarize_v0_reproduction_threshold.py",
               11: "summarize_v0_long_horizon.py",
               12: "summarize_v0_birth_cost.py",
               13: "summarize_v0_genome_coverage.py",
               14: "summarize_v0_frequency_cost.py",
               15: "summarize_v0_neutral_followup.py",
               16: "summarize_v0_food_geometry.py",
               17: "summarize_v0_geometry_threshold.py",
               18: "summarize_v0_movement_charge.py",
               19: "summarize_v0_joint_zero_charge.py",
               20: "summarize_v0_renewal_granularity.py",
               21: "summarize_v0_buffer_capacity.py"}
    for number, helper in helpers.items():
        if number > args.campaigns:
            continue
        with tempfile.TemporaryDirectory() as temporary:
            summary = Path(temporary) / "verification"
            command = [sys.executable, str(root / "scripts" / helper),
                       "--input", str(root / "data" / f"campaign-{number:03d}"),
                       "--output", str(summary)]
            if number == 11:
                command.extend(["--reference", str(root / "data/campaign-010")])
            if number == 15:
                command.extend(["--reference", str(root / "data/campaign-014")])
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL)
            metric_audits[f"campaign-{number:03d}"] = json.loads((summary / "summary.json").read_text(encoding="utf-8"))
            if number == 18:
                expected = json.loads((root / 'docs/research/results/campaign-018-verification.json').read_text(encoding='utf-8'))
                if metric_audits['campaign-018'] != expected:
                    raise ValueError('Campaign-018 metric report differs from saved review')
                observation_output = Path(temporary) / 'observations'
                subprocess.run([sys.executable, '-S', str(root / 'scripts/verify_v0_movement_charge_observations.py'),
                    '--input', str(root / 'data/campaign-018'), '--metrics-verification', str(summary / 'summary.json'),
                    '--output', str(observation_output)],check=True,stdout=subprocess.DEVNULL)
                actual = json.loads((observation_output / 'summary.json').read_text(encoding='utf-8'))
                expected = json.loads((root / 'docs/research/results/campaign-018-observations.json').read_text(encoding='utf-8'))
                if actual != expected:
                    raise ValueError('Campaign-018 observation report differs from saved review')
                metric_audits['campaign-018-observations'] = actual
            if number == 19:
                expected = json.loads((root / 'docs/research/results/campaign-019-verification.json').read_text(encoding='utf-8'))
                if metric_audits['campaign-019'] != expected:
                    raise ValueError('Campaign-019 metric report differs from saved review')
                observation_output = Path(temporary) / 'observations'
                subprocess.run([sys.executable, '-S', str(root / 'scripts/verify_v0_joint_zero_charge_observations.py'),
                    '--input', str(root / 'data/campaign-019'), '--metrics-verification', str(summary / 'summary.json'),
                    '--output', str(observation_output)],check=True,stdout=subprocess.DEVNULL)
                actual = json.loads((observation_output / 'summary.json').read_text(encoding='utf-8'))
                expected = json.loads((root / 'docs/research/results/campaign-019-observations.json').read_text(encoding='utf-8'))
                if actual != expected:
                    raise ValueError('Campaign-019 observation report differs from saved review')
                metric_audits['campaign-019-observations'] = actual
                process_output = Path(temporary) / 'processes'
                subprocess.run([sys.executable, '-I', '-S', str(root / 'scripts/summarize_v0_joint_zero_charge_processes.py'),
                    '--output', str(process_output)], check=True, stdout=subprocess.DEVNULL)
                actual = json.loads((process_output / 'summary.json').read_text(encoding='utf-8'))
                expected = json.loads((root / 'docs/research/results/campaign-019-processes.json').read_text(encoding='utf-8'))
                if actual != expected:
                    raise ValueError('Campaign-019 process report differs from saved review')
                metric_audits['campaign-019-processes'] = actual
            if number == 20:
                expected = json.loads((root / 'docs/research/results/campaign-020-verification.json').read_text(encoding='utf-8'))
                if metric_audits['campaign-020'] != expected:
                    raise ValueError('Campaign-020 metric report differs from saved review')
                observation_output = Path(temporary) / 'observations'
                subprocess.run([sys.executable, '-S', str(root / 'scripts/verify_v0_renewal_granularity_observations.py'),
                    '--input', str(root / 'data/campaign-020'), '--metrics-verification', str(summary / 'summary.json'),
                    '--output', str(observation_output)],check=True,stdout=subprocess.DEVNULL)
                actual = json.loads((observation_output / 'summary.json').read_text(encoding='utf-8'))
                expected = json.loads((root / 'docs/research/results/campaign-020-observations.json').read_text(encoding='utf-8'))
                if actual != expected:
                    raise ValueError('Campaign-020 observation report differs from saved review')
                metric_audits['campaign-020-observations'] = actual
                process_output = Path(temporary) / 'processes'
                subprocess.run([sys.executable, '-I', '-S', str(root / 'scripts/summarize_v0_renewal_granularity_processes.py'),
                    '--output', str(process_output)], check=True, stdout=subprocess.DEVNULL)
                actual = json.loads((process_output / 'summary.json').read_text(encoding='utf-8'))
                expected = json.loads((root / 'docs/research/results/campaign-020-processes.json').read_text(encoding='utf-8'))
                if actual != expected:
                    raise ValueError('Campaign-020 process report differs from saved review')
                metric_audits['campaign-020-processes'] = actual
            if number == 21:
                expected = json.loads((root / 'docs/research/results/campaign-021-verification.json').read_text(encoding='utf-8'))
                if metric_audits['campaign-021'] != expected:
                    raise ValueError('Campaign-021 metric report differs from saved review')
                observation_output = Path(temporary) / 'observations'
                subprocess.run([sys.executable, '-S', str(root / 'scripts/verify_v0_buffer_capacity_observations.py'),
                    '--input', str(root / 'data/campaign-021'), '--metrics-verification', str(summary / 'summary.json'),
                    '--output', str(observation_output)],check=True,stdout=subprocess.DEVNULL)
                actual = json.loads((observation_output / 'summary.json').read_text(encoding='utf-8'))
                expected = json.loads((root / 'docs/research/results/campaign-021-observations.json').read_text(encoding='utf-8'))
                if actual != expected:
                    raise ValueError('Campaign-021 observation report differs from saved review')
                metric_audits['campaign-021-observations'] = actual
                process_output = Path(temporary) / 'processes'
                subprocess.run([sys.executable, '-I', '-S', str(root / 'scripts/summarize_v0_buffer_capacity_processes.py'),
                    '--output', str(process_output)], check=True, stdout=subprocess.DEVNULL)
                actual = json.loads((process_output / 'summary.json').read_text(encoding='utf-8'))
                expected = json.loads((root / 'docs/research/results/campaign-021-processes.json').read_text(encoding='utf-8'))
                if actual != expected:
                    raise ValueError('Campaign-021 process report differs from saved review')
                metric_audits['campaign-021-processes'] = actual


    manifest = {"format": "bitgenesis-review-1", "git_commit": git("rev-parse", "HEAD"),
                "scope": f"Tracked source plus campaigns 001-{args.campaigns:03d}, mutation calibration, acceptance demonstration and Chinese review page. Other local data and environments are excluded.",
                "audits": audited,
                "raw_campaign_workload": workload,
                "metric_campaign_audits": metric_audits,
                "files": {"bitgenesis/" + p.relative_to(root).as_posix():
                          {"sha256": sha256(p), "bytes": p.stat().st_size} for p in files}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            archive.write(path, "bitgenesis/" + path.relative_to(root).as_posix())
        archive.writestr("MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
        archive.writestr("START-HERE.txt", f"BitGenesis V0 review\n\nUnzip the whole archive. Open bitgenesis/data/{review_page} in a browser.\nThe review links to the world replay and lineage inspector; keep the folder structure.\n\nSource and experiment protocols are included under bitgenesis/. See README.md to rerun with Python 3.12+.\nMANIFEST.json records the source commit, file hashes and artifact-consistency checks.\nConsistency checks do not establish biological realism or scientific generality.\n")
    verify(args.output)
    print(json.dumps({"archive": str(args.output.resolve()), "sha256": sha256(args.output),
                      "files": len(files), "bytes": args.output.stat().st_size,
                      "audited_full_runs": len(audited)}, indent=2))


if __name__ == "__main__":
    main()
