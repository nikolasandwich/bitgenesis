"""Reproducible run artifacts. Existing output directories are never overwritten."""

import csv
from dataclasses import asdict, fields
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

from bitgenesis.v0 import RULES_VERSION
from bitgenesis.v0.engine import Config, World


def load_config(path):
    import tomllib
    with Path(path).open("rb") as stream:
        values = tomllib.load(stream)
    version = values.pop("schema_version", None)
    if type(version) is not int or version != 1:
        raise ValueError("schema_version must be integer 1")
    if values.pop("stage", None) != "v0" or values.pop("rules_version", None) != RULES_VERSION:
        raise ValueError(f"Expected v0 / {RULES_VERSION}")
    unknown = values.keys() - {f.name for f in fields(Config)}
    if unknown:
        raise ValueError(f"Unknown configuration keys: {', '.join(sorted(unknown))}")
    return Config(**values)


def provenance():
    root = Path(__file__).resolve().parents[3]
    def git(*arguments):
        try:
            return subprocess.check_output(["git", "-C", str(root), *arguments],
                                           text=True, stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.CalledProcessError):
            return None
    hashes = {str(p.relative_to(root)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted((root / "src" / "bitgenesis").rglob("*.py"))}
    dirty = git("status", "--porcelain")
    return {"git_commit": git("rev-parse", "HEAD"),
            "git_dirty": None if dirty is None else bool(dirty),
            "python": platform.python_version(), "platform": platform.platform(),
            "source_sha256": hashes, "invocation": sys.argv}


def frame(world):
    return {"tick": world.tick, "food": world.food.copy(),
            "organisms": [[o.position, o.genome, o.founder_id] for o in world.living.values()]}


def run(config, steps, output, frame_interval=10):
    if type(steps) is not int or steps < 0:
        raise ValueError("steps must be a nonnegative integer")
    if type(frame_interval) is not int or frame_interval < 1:
        raise ValueError("frame_interval must be a positive integer")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    metadata = {"schema_version": 1, "rules_version": RULES_VERSION,
                "config": asdict(config), "requested_steps": steps,
                "frame_interval": frame_interval, **provenance(), "status": "running"}
    def save(name, value):
        (output / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    save("metadata.json", metadata)
    world = World(config)
    snapshots, frames = [], []
    try:
        with (output / "metrics.csv").open("w", newline="", encoding="utf-8") as metrics_file, \
                (output / "events.jsonl").open("w", encoding="utf-8") as events_file:
            writer = csv.DictWriter(metrics_file, fieldnames=list(world.snapshot()))
            writer.writeheader()
            for tick in range(steps + 1):
                if tick:
                    world.step()
                world.check_invariants()
                snapshot = world.snapshot()
                writer.writerow(snapshot)
                snapshots.append(snapshot)
                for event in world.events:
                    events_file.write(json.dumps(event, separators=(",", ":")) + "\n")
                world.events.clear()
                if tick % frame_interval == 0 or tick == steps:
                    frames.append(frame(world))
        save("lineage.json", [asdict(o) for o in world.lineage.values()])
        save("frames.json", frames)
        save("summary.json", world.snapshot())
        from bitgenesis.v0.viewer import write_viewer
        write_viewer(output / "index.html", config, snapshots, frames)
        metadata.update(status="complete", completed_steps=world.tick)
        save("metadata.json", metadata)
    except Exception as error:
        metadata.update(status="failed", error=f"{type(error).__name__}: {error}", completed_steps=world.tick)
        save("metadata.json", metadata)
        raise
    return world.snapshot()
