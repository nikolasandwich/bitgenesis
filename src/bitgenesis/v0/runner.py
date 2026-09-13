"""Reproducible run artifacts. Existing output directories are never overwritten."""

import csv
from dataclasses import asdict, fields
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys

from bitgenesis.v0 import RULES_VERSION
from bitgenesis.v0.engine import Config, World
from bitgenesis.v0.artifacts import write_json_atomic


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
    package_root = Path(__file__).resolve().parents[1]
    root = package_root.parent.parent
    source_checkout = package_root == root / "src" / "bitgenesis"
    def git(*arguments):
        if not source_checkout:
            return None
        try:
            return subprocess.check_output(["git", "-C", str(root), *arguments],
                                           text=True, stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.CalledProcessError):
            return None
    hashes = {"src/bitgenesis/" + p.relative_to(package_root).as_posix():
              hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(package_root.rglob("*.py"))}
    script_hashes = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted((root / "scripts").glob("*.py"))} if source_checkout else {}
    dirty = git("status", "--porcelain")
    return {"git_commit": git("rev-parse", "HEAD"),
            "git_dirty": None if dirty is None else bool(dirty),
            "python": platform.python_version(), "platform": platform.platform(),
            "source_sha256": hashes, "research_scripts_sha256": script_hashes,
            "installation_kind": "source" if source_checkout else "installed",
            "invocation": sys.argv}


def frame(world):
    return {"tick": world.tick, "food": world.food.copy(),
            "organisms": [[o.position, o.genome, o.founder_id] for o in world.living.values()],
            "metrics": world.snapshot()}


def run(config, steps, output, frame_interval=10, max_frames=1001):
    if type(steps) is not int or steps < 0:
        raise ValueError("steps must be a nonnegative integer")
    if type(frame_interval) is not int or frame_interval < 1:
        raise ValueError("frame_interval must be a positive integer")
    if type(max_frames) is not int or max_frames < 2:
        raise ValueError("max_frames must be an integer of at least 2")
    effective_frame_interval = max(frame_interval, math.ceil(steps / (max_frames - 1)))
    chart_interval = max(1, math.ceil(steps / 10000))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    metadata = {"schema_version": 1, "output_schema_version": 2, "rules_version": RULES_VERSION,
                "config": asdict(config), "requested_steps": steps,
                "frame_interval": effective_frame_interval,
                "requested_frame_interval": frame_interval, "max_frames": max_frames,
                "chart_interval": chart_interval, **provenance(), "status": "running"}
    def save(name, value):
        write_json_atomic(output / name, value)
    save("metadata.json", metadata)
    snapshots, frames = [], []
    completed_steps = 0
    try:
        world = World(config)
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
                if tick % chart_interval == 0 or tick == steps:
                    snapshots.append(snapshot)
                for event in world.events:
                    events_file.write(json.dumps(event, separators=(",", ":")) + "\n")
                world.events.clear()
                if tick % effective_frame_interval == 0 or tick == steps:
                    frames.append(frame(world))
                completed_steps = tick
        save("lineage.json", [asdict(o) for o in world.lineage.values()])
        save("frames.json", frames)
        save("summary.json", world.snapshot())
        from bitgenesis.v0.viewer import write_viewer
        write_viewer(output / "index.html", config, snapshots, frames)
        from bitgenesis.v0.lineage_viewer import write_lineage_viewer
        write_lineage_viewer(output / "lineage.html", world)
        metadata.update(status="complete", completed_steps=world.tick)
        save("metadata.json", metadata)
    except (Exception, KeyboardInterrupt) as error:
        metadata.update(status="interrupted" if isinstance(error, KeyboardInterrupt) else "failed",
                        error=f"{type(error).__name__}: {error}", completed_steps=completed_steps)
        save("metadata.json", metadata)
        raise
    return world.snapshot()
