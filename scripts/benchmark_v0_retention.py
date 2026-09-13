"""Operational memory/checkpoint benchmark; tracemalloc timings are not throughput claims."""

import argparse
import gc
import json
from pathlib import Path
import time
import tracemalloc

from bitgenesis.v0.artifacts import write_json_atomic
from bitgenesis.v0.checkpoint import save_world
from bitgenesis.v0.engine import Config, World
from bitgenesis.v0.runner import provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", choices=("drained", "retained"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    metadata = {"benchmark": "v0-retention-1", "events": args.events, "seed": 42,
                "sample_ticks": [1000, 5000, 10000], **provenance(), "status": "running"}
    write_json_atomic(args.output / "metadata.json", metadata)
    rows = []
    tracemalloc.start()
    world = World(Config(seed=42))
    if args.events == "drained":
        world.events.clear()
    elapsed = 0
    phase = time.perf_counter()
    try:
        for tick in range(1, 10001):
            world.step()
            world.check_invariants()
            if args.events == "drained":
                world.events.clear()
            if tick not in metadata["sample_ticks"]:
                continue
            elapsed += time.perf_counter() - phase
            gc.collect()
            current, _ = tracemalloc.get_traced_memory()
            tracemalloc.reset_peak()
            path = args.output / f"state-{tick}.json"
            started = time.perf_counter()
            save_world(path, world)
            save_seconds = time.perf_counter() - started
            _, save_peak = tracemalloc.get_traced_memory()
            row = {"tick": tick, "population": len(world.living), "lineage_records": len(world.lineage),
                   "pending_events": len(world.events), "traced_live_bytes": current,
                   "traced_save_peak_bytes": save_peak, "checkpoint_bytes": path.stat().st_size,
                   "instrumented_stepping_seconds": elapsed, "instrumented_save_seconds": save_seconds}
            rows.append(row)
            write_json_atomic(args.output / "results.json", rows)
            print(json.dumps(row), flush=True)
            phase = time.perf_counter()
        metadata["status"] = "complete"
    except (Exception, KeyboardInterrupt) as error:
        metadata["status"] = "interrupted" if isinstance(error, KeyboardInterrupt) else "failed"
        metadata["error"] = type(error).__name__ + ": " + str(error)
        raise
    finally:
        tracemalloc.stop()
        write_json_atomic(args.output / "metadata.json", metadata)


if __name__ == "__main__":
    main()
