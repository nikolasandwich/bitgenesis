from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

from bitgenesis.v0.checkpoint import advance, load_world, save_world
from bitgenesis.v0.engine import Config, World


class CheckpointTests(unittest.TestCase):
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
