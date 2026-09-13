"""Versioned JSON world checkpoints. No executable serialization is loaded."""

from dataclasses import asdict
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import random
import sys

from bitgenesis.v0 import RULES_VERSION, engine
from bitgenesis.v0.artifacts import write_json_atomic
from bitgenesis.v0.engine import Config, Individual, World


def engine_hash():
    # Normalize source line endings so the same checkout on Windows/Linux agrees.
    return hashlib.sha256(Path(engine.__file__).read_text(encoding="utf-8").encode()).hexdigest()


def digest(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def save_world(path, world):
    world.check_invariants()
    payload = {"format": "bitgenesis-state-1", "rules_version": RULES_VERSION,
               "engine_sha256": engine_hash(), "python_minor": list(sys.version_info[:2]),
               "config": asdict(world.config), "tick": world.tick, "food": world.food,
               "lineage": [asdict(o) for o in world.lineage.values()],
               "living_ids": list(world.living), "events": world.events,
               "supplied_energy": world.supplied_energy, "dissipated_energy": world.dissipated_energy,
               "next_id": world.next_id, "rng_state": world.rng.getstate()}
    write_json_atomic(path, {"payload": payload, "sha256": digest(payload)})


def validate_lineage(world, records):
    """Check historical structure as well as currently living state."""
    initial = world.config.initial_population
    cells = world.config.width * world.config.height
    if len(records) < initial:
        raise ValueError("Checkpoint is missing founding individuals")
    children = Counter()
    birth_slots = set()
    for organism in records:
        for field in ("id", "founder_id", "generation", "birth_tick", "genome", "position", "energy", "offspring"):
            value = getattr(organism, field)
            if type(value) is not int or value < 0:
                raise ValueError(f"Invalid checkpoint lineage {field}")
        if not (organism.founder_id < initial and organism.position < cells
                and organism.genome <= 1000 and organism.birth_tick <= world.tick):
            raise ValueError("Checkpoint lineage value outside world bounds")
        if organism.death_tick is None:
            if organism.energy <= 0:
                raise ValueError("Checkpoint living individual has no energy")
        elif (type(organism.death_tick) is not int or not organism.birth_tick < organism.death_tick <= world.tick
              or organism.energy != 0):
            raise ValueError("Invalid checkpoint death state")
        if organism.id < initial:
            if (organism.parent_id is not None or organism.founder_id != organism.id
                    or organism.generation != 0 or organism.birth_tick != 0):
                raise ValueError("Invalid checkpoint founder ancestry")
        else:
            if type(organism.parent_id) is not int or not 0 <= organism.parent_id < organism.id:
                raise ValueError("Invalid checkpoint parent reference")
            parent = world.lineage[organism.parent_id]
            if (organism.generation != parent.generation + 1 or organism.founder_id != parent.founder_id
                    or organism.birth_tick <= parent.birth_tick
                    or (parent.death_tick is not None and organism.birth_tick >= parent.death_tick)):
                raise ValueError("Inconsistent checkpoint ancestry or birth time")
            max_change = world.config.mutation_step if world.config.mutation_probability else 0
            if abs(organism.genome - parent.genome) > max_change:
                raise ValueError("Checkpoint genome inheritance violates mutation bounds")
            slot = (organism.parent_id, organism.birth_tick)
            if slot in birth_slots:
                raise ValueError("Checkpoint parent reproduced twice in one tick")
            birth_slots.add(slot)
            children[organism.parent_id] += 1
    if any(organism.offspring != children[organism.id] for organism in records):
        raise ValueError("Checkpoint offspring counts differ from lineage")


def validate_events(world):
    """Validate retained events; a drained buffer need not contain full history."""
    if not isinstance(world.events, list):
        raise ValueError("Invalid checkpoint pending events")
    seen = set()
    previous_tick = -1
    for event in world.events:
        if (not isinstance(event, dict) or type(event.get("id")) is not int
                or event["id"] not in world.lineage
                or event.get("event") not in ("birth", "death")):
            raise ValueError("Invalid checkpoint pending event")
        kind = event["event"]
        expected = {"tick", "event", "id", "energy", "position"}
        if kind == "birth":
            expected |= {"parent_id", "genome"}
        if set(event) != expected or any(type(event[k]) is not int for k in ("tick", "energy", "position")):
            raise ValueError("Invalid checkpoint event fields")
        identity = (kind, event["id"])
        if identity in seen or not previous_tick <= event["tick"] <= world.tick:
            raise ValueError("Duplicate or out-of-order checkpoint event")
        seen.add(identity)
        previous_tick = event["tick"]
        organism = world.lineage[event["id"]]
        if not 0 <= event["position"] < world.config.width * world.config.height:
            raise ValueError("Checkpoint event position outside world")
        if kind == "birth":
            if (event["tick"] != organism.birth_tick or type(event["genome"]) is not int
                    or event["genome"] != organism.genome
                    or (event["parent_id"] is not None and type(event["parent_id"]) is not int)
                    or event["parent_id"] != organism.parent_id or event["energy"] <= 0
                    or (organism.parent_id is None and event["energy"] != world.config.initial_energy)):
                raise ValueError("Checkpoint birth event differs from lineage or configuration")
        elif (event["tick"] != organism.death_tick or event["energy"] != 0
              or event["position"] != organism.position):
            raise ValueError("Checkpoint death event differs from lineage")


def load_world(path):
    try:
        envelope = json.loads(Path(path).read_text(encoding="utf-8"))
        payload = envelope["payload"]
        if digest(payload) != envelope["sha256"]:
            raise ValueError("Checkpoint checksum mismatch")
        if payload["format"] != "bitgenesis-state-1" or payload["rules_version"] != RULES_VERSION:
            raise ValueError("Unsupported checkpoint format or rules version")
        if payload["engine_sha256"] != engine_hash():
            raise ValueError("Checkpoint requires a different engine source revision")
        if payload["python_minor"] != list(sys.version_info[:2]):
            raise ValueError("Checkpoint requires the same Python major/minor version")
        world = World.__new__(World)  # Do not create fresh founders or consume RNG draws.
        world.config = Config(**payload["config"])
        for name in ("tick", "supplied_energy", "dissipated_energy", "next_id"):
            value = payload[name]
            if type(value) is not int or value < 0:
                raise ValueError(f"Invalid checkpoint {name}")
            setattr(world, name, value)
        world.food = payload["food"]
        records = [Individual(**record) for record in payload["lineage"]]
        world.lineage = {o.id: o for o in records}
        if (len(world.lineage) != len(records) or len(records) != world.next_id
                or any(identity != index for index, identity in enumerate(world.lineage))):
            raise ValueError("Checkpoint organism IDs are duplicated or discontinuous")
        validate_lineage(world, records)
        living_ids = payload["living_ids"]
        if (not isinstance(living_ids, list) or any(type(identity) is not int for identity in living_ids)
                or len(set(living_ids)) != len(living_ids)):
            raise ValueError("Checkpoint has invalid or duplicate living IDs")
        world.living = {identity: world.lineage[identity] for identity in living_ids}
        if set(living_ids) != {o.id for o in records if o.death_tick is None}:
            raise ValueError("Checkpoint living/dead membership mismatch")
        world.occupied = {o.position: o.id for o in world.living.values()}
        world.events = payload["events"]
        validate_events(world)
        def tuples(value):
            return tuple(tuples(item) for item in value) if isinstance(value, list) else value
        world.rng = random.Random(0)
        world.rng.setstate(tuples(payload["rng_state"]))
        # Explicit checks remain active under python -O; engine assertions also run normally.
        if len(world.food) != world.config.width * world.config.height or any(
                type(value) is not int or not 0 <= value <= world.config.food_capacity for value in world.food):
            raise ValueError("Checkpoint resources violate world bounds")
        if len(world.occupied) != len(world.living) or any(
                type(o.energy) is not int or o.energy <= 0 or not 0 <= o.position < len(world.food)
                or type(o.genome) is not int or not 0 <= o.genome <= 1000 for o in world.living.values()):
            raise ValueError("Checkpoint living state violates world bounds")
        if sum(world.food) + sum(o.energy for o in world.living.values()) + world.dissipated_energy != world.supplied_energy:
            raise ValueError("Checkpoint energy accounting mismatch")
        world.check_invariants()
        return world
    except (KeyError, TypeError, IndexError, AssertionError) as error:
        raise ValueError(f"Malformed checkpoint: {error}") from error


def advance(output, steps, interval=1000, config=None, resume=None):
    """Advance into a new directory, preserving the last completed checkpoint on interruption."""
    if type(steps) is not int or steps < 0 or type(interval) is not int or interval < 1:
        raise ValueError("steps must be nonnegative and checkpoint interval must be positive")
    if resume is not None and config is not None:
        raise ValueError("A resumed state cannot override its configuration")
    world = load_world(resume) if resume is not None else World(config or Config())
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    start = world.tick
    metadata = {"format": "bitgenesis-checkpoint-run-1", "start_tick": start,
                "target_tick": start + steps, "checkpoint_interval": interval,
                "python": platform.python_version(), "status": "running",
                "resume_sha256": hashlib.sha256(Path(resume).read_bytes()).hexdigest() if resume else None}
    try:
        save_world(output / "state.json", world)
        metadata["saved_tick"] = world.tick
        write_json_atomic(output / "metadata.json", metadata)
        for elapsed in range(1, steps + 1):
            world.step()
            world.check_invariants()
            if elapsed % interval == 0 or elapsed == steps:
                save_world(output / "state.json", world)
                metadata["saved_tick"] = world.tick
                write_json_atomic(output / "metadata.json", metadata)
        metadata["status"] = "complete"
        write_json_atomic(output / "metadata.json", metadata)
    except (Exception, KeyboardInterrupt) as error:
        metadata["status"] = "interrupted" if isinstance(error, KeyboardInterrupt) else "failed"
        metadata["error"] = type(error).__name__ + ": " + str(error)
        write_json_atomic(output / "metadata.json", metadata)
        raise
    return world.snapshot()
