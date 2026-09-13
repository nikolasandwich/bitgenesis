from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

from bitgenesis.v0.checkpoint import advance, digest, load_world, save_world
from bitgenesis.v0.engine import Config, World


class CheckpointTests(unittest.TestCase):
    def test_resume_preserves_boundary_states_and_drained_event_buffers(self):
        cases = {
            "empty": Config(width=2, height=2, initial_population=0),
            "extinct": Config(width=2, height=2, initial_population=4,
                              initial_energy=1, initial_food=0, regrowth_probability=0),
            "saturated": Config(width=2, height=2, initial_population=4,
                                regrowth_probability=1000),
            "turnover": Config(width=8, height=8, initial_population=12),
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, config in cases.items():
                for drain in (False, True):
                    with self.subTest(world=name, drain=drain):
                        original = World(config)
                        for _ in range(40):
                            original.step()
                        if name in ("empty", "extinct"):
                            self.assertFalse(original.living)
                        if name == "saturated":
                            self.assertEqual(len(original.living), 4)
                            self.assertEqual(original.next_id, 4)
                        if drain:
                            original.events.clear()
                        before = root / "before.json"
                        save_world(before, original)
                        restored = load_world(before)
                        self.assertEqual(restored.events, original.events)
                        for _ in range(60):
                            original.step()
                            restored.step()
                        save_world(root / "original.json", original)
                        save_world(root / "restored.json", restored)
                        self.assertEqual((root / "original.json").read_bytes(),
                                         (root / "restored.json").read_bytes())
                        if drain:
                            self.assertTrue(all(event["tick"] > 40 for event in restored.events))

    def test_valid_checksum_does_not_bypass_lineage_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            world = World(Config(width=8, height=8, initial_population=12))
            for _ in range(100):
                world.step()
            save_world(path, world)
            original = path.read_text()
            child_id = next(o.id for o in world.lineage.values() if o.parent_id is not None)
            dead_id = next(o.id for o in world.lineage.values() if o.death_tick is not None)
            living_id = next(iter(world.living))
            changes = [(0, "parent_id", 0), (child_id, "parent_id", child_id),
                       (child_id, "generation", 9999), (child_id, "founder_id", 9999),
                       (0, "offspring", world.lineage[0].offspring + 1),
                       (dead_id, "genome", 1001), (dead_id, "energy", 1),
                       (living_id, "position", 1.5)]
            for identity, field, value in changes:
                with self.subTest(field=field, identity=identity):
                    envelope = json.loads(original)
                    envelope["payload"]["lineage"][identity][field] = value
                    envelope["sha256"] = digest(envelope["payload"])
                    path.write_text(json.dumps(envelope), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_world(path)
            with self.subTest(field="living_ids"):
                envelope = json.loads(original)
                envelope["payload"]["living_ids"][0] = float(living_id)
                envelope["sha256"] = digest(envelope["payload"])
                path.write_text(json.dumps(envelope), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "living IDs"):
                    load_world(path)

    def test_checkpoint_rejects_impossible_inherited_genomes(self):
        # A matching checksum checks bytes, not whether inheritance obeys the rules.
        for probability, step in ((0, 100), (100, 0), (1000, 100)):
            with self.subTest(probability=probability, step=step), tempfile.TemporaryDirectory() as directory:
                world = World(Config(width=8, height=8, initial_population=12,
                                     mutation_probability=probability, mutation_step=step))
                for _ in range(40):
                    world.step()
                world.events.clear()  # Historical lineage must stand on its own.
                child = next(o for o in world.lineage.values() if o.parent_id is not None)
                parent = world.lineage[child.parent_id]
                path = Path(directory) / "state.json"
                save_world(path, world)
                self.assertEqual(load_world(path).snapshot(), world.snapshot())
                envelope = json.loads(path.read_text(encoding="utf-8"))
                # Still inside 0..1000, but impossible under this reproduction rule.
                envelope["payload"]["lineage"][child.id]["genome"] = 0 if parent.genome > 500 else 1000
                envelope["sha256"] = digest(envelope["payload"])
                path.write_text(json.dumps(envelope), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "inheritance"):
                    load_world(path)

    def test_pending_events_must_agree_with_lineage(self):
        with tempfile.TemporaryDirectory() as directory:
            world = World(Config(width=8, height=8, initial_population=12))
            for _ in range(40):
                world.step()
            path = Path(directory) / "state.json"
            save_world(path, world)
            original = json.loads(path.read_text(encoding="utf-8"))
            death_index = next(i for i, e in enumerate(world.events) if e["event"] == "death")
            changes = [(0, "event", "unknown"), (0, "tick", 1),
                       (0, "genome", (world.events[0]["genome"] + 1) % 1001),
                       (0, "parent_id", 0), (0, "energy", 0), (0, "position", 64),
                       (death_index, "energy", 1), (death_index, "tick", 0),
                       (death_index, "position", (world.events[death_index]["position"] + 1) % 64)]
            for index, key, value in changes:
                with self.subTest(index=index, key=key):
                    envelope = json.loads(json.dumps(original))
                    envelope["payload"]["events"][index][key] = value
                    envelope["sha256"] = digest(envelope["payload"])
                    path.write_text(json.dumps(envelope), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "event"):
                        load_world(path)
            for kind in ("duplicate", "out-of-order"):
                with self.subTest(kind=kind):
                    envelope = json.loads(json.dumps(original))
                    events = envelope["payload"]["events"]
                    if kind == "duplicate":
                        events.insert(0, events[0].copy())
                    else:
                        events.reverse()
                    envelope["sha256"] = digest(envelope["payload"])
                    path.write_text(json.dumps(envelope), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "event"):
                        load_world(path)

    def test_cli_separate_process_resume_matches_complete_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, steps, resume in (("first", 13, None), ("rest", 17, root / "first" / "state.json"),
                                        ("whole", 30, None)):
                command = [sys.executable, "-m", "bitgenesis", "checkpoint", "--steps", str(steps),
                           "--interval", "7", "--output", str(root / name)]
                if resume:
                    command.extend(["--resume", str(resume)])
                result = subprocess.run(command, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            resumed = json.loads((root / "rest" / "state.json").read_text())
            whole = json.loads((root / "whole" / "state.json").read_text())
            self.assertEqual(resumed, whole)

    def test_resume_matches_uninterrupted_rng_events_lineage_and_space(self):
        with tempfile.TemporaryDirectory() as directory:
            for seed in range(3):
                original = World(Config(seed=seed, width=8, height=8, initial_population=12))
                for _ in range(37):
                    original.step()
                path = Path(directory) / f"{seed}.json"
                save_world(path, original)
                restored = load_world(path)
                for _ in range(80):
                    original.step()
                    restored.step()
                self.assertEqual(original.rng.getstate(), restored.rng.getstate())
                self.assertEqual(original.events, restored.events)
                self.assertEqual(original.food, restored.food)
                self.assertEqual(list(original.living), list(restored.living))
                self.assertEqual([asdict(o) for o in original.lineage.values()],
                                 [asdict(o) for o in restored.lineage.values()])
                self.assertEqual(original.snapshot(), restored.snapshot())

    def test_interruption_recovers_last_complete_tick_not_partial_step(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "part"
            step = World.step
            calls = 0
            def interrupt(world):
                nonlocal calls
                calls += 1
                if calls == 8:
                    world.tick += 1  # Simulate interruption inside a partially changed tick.
                    raise KeyboardInterrupt
                step(world)
            config = Config(width=8, height=8, initial_population=12)
            with patch.object(World, "step", interrupt), self.assertRaises(KeyboardInterrupt):
                advance(output, 20, interval=5, config=config)
            self.assertEqual(load_world(output / "state.json").tick, 5)
            self.assertEqual(json.loads((output / "metadata.json").read_text())["status"], "interrupted")
            resumed = advance(Path(directory) / "rest", 15, resume=output / "state.json")
            baseline = World(config)
            for _ in range(20):
                baseline.step()
            self.assertEqual(resumed, baseline.snapshot())

    def test_corruption_and_incompatible_engine_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            save_world(path, World(Config()))
            with patch("bitgenesis.v0.checkpoint.engine_hash", return_value="changed"):
                with self.assertRaisesRegex(ValueError, "engine source"):
                    load_world(path)
            envelope = json.loads(path.read_text())
            envelope["payload"]["tick"] += 1
            path.write_text(json.dumps(envelope), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "checksum"):
                load_world(path)

    def test_existing_run_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            advance(output, 0)
            before = (output / "state.json").read_bytes()
            with self.assertRaises(FileExistsError):
                advance(output, 10)
            self.assertEqual((output / "state.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
