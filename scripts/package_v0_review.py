"""Package tracked source and an explicit set of local review artifacts with hashes."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

from bitgenesis.v0.audit import audit


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/bitgenesis-v0-review.zip"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    def git(*arguments):
        return subprocess.check_output(["git", "-C", str(root), *arguments], text=True).strip()
    if git("status", "--porcelain"):
        raise ValueError("Commit or resolve working-tree changes before packaging a review")
    files = [root / name for name in git("ls-files").splitlines()]
    for name in ("campaign-001", "campaign-002", "campaign-003", "campaign-004", "acceptance-v0"):
        directory = root / "data" / name
        if not directory.is_dir():
            raise ValueError(f"Missing review directory: {name}")
        files.extend(path for path in directory.rglob("*") if path.is_file())
    files.append(root / "data" / "review-v0-4.html")
    files = sorted(set(files))
    for path in files:
        if not path.resolve().is_relative_to(root) or not path.is_file():
            raise ValueError(f"Invalid or missing review input: {path}")
    audited = {"acceptance-v0": audit(root / "data" / "acceptance-v0")}
    for directory in sorted((root / "data" / "campaign-001").iterdir()):
        if directory.is_dir():
            audited[f"campaign-001/{directory.name}"] = audit(directory)
    manifest = {"format": "bitgenesis-review-1", "git_commit": git("rev-parse", "HEAD"),
                "scope": "Tracked source plus campaigns 001–004, acceptance demonstration and Chinese review page. Other local data and environments are excluded.",
                "audits": audited,
                "files": {"bitgenesis/" + p.relative_to(root).as_posix():
                          {"sha256": sha256(p), "bytes": p.stat().st_size} for p in files}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            archive.write(path, "bitgenesis/" + path.relative_to(root).as_posix())
        archive.writestr("MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
        archive.writestr("START-HERE.txt", "BitGenesis V0 review\n\nUnzip the whole archive. Open bitgenesis/data/review-v0-4.html in a browser.\nThe review links to the world replay and lineage inspector; keep the folder structure.\n\nSource and experiment protocols are included under bitgenesis/. See README.md to rerun with Python 3.12+.\nMANIFEST.json records the source commit, file hashes and artifact-consistency checks.\nConsistency checks do not establish biological realism or scientific generality.\n")
    with zipfile.ZipFile(args.output) as archive:
        for name, entry in manifest["files"].items():
            with archive.open(name) as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if digest != entry["sha256"]:
                raise ValueError(f"Archive verification failed: {name}")
    print(json.dumps({"archive": str(args.output.resolve()), "sha256": sha256(args.output),
                      "files": len(files), "bytes": args.output.stat().st_size,
                      "audited_full_runs": len(audited)}, indent=2))


if __name__ == "__main__":
    main()
