from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bitgenesis.v0.engine import Config, World
from bitgenesis.v0.runner import run


class DarwinTests(unittest.TestCase):
    def test_frozen_v0_darwin_1_replay(self):
        # Captured at d789db1 / Python 3.12.10. Changing this digest requires a
        # deliberate rules-version decision, never a routine fixture refresh.
        world = World(Config(seed=314159, width=8, height=8, initial_population=12))
        for _ in range(120):
            world.step()
        payload = {"food": world.food, "snapshot": world.snapshot(),
                   "lineage": [asdict(o) for o in world.lineage.values()], "events": world.events}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                          allow_nan=False).encode()).hexdigest()
        self.assertEqual(digest, "eb92249f0d711cbd6d354ad61fe04498333dad1582c40d613fa7555ec8e46b69")

    def test_replay_matches_events_and_state(self):
        a, b = World(Config(seed=18)), World(Config(seed=18))
        for _ in range(100):
            a.step()
            b.step()
        self.assertEqual(a.events, b.events)
        self.assertEqual(a.snapshot(), b.snapshot())
        self.assertEqual(a.food, b.food)
        self.assertEqual([asdict(o) for o in a.lineage.values()],
                         [asdict(o) for o in b.lineage.values()])

    def test_energy_and_occupancy_hold_across_seeds(self):
        for seed in range(5):
            world = World(Config(seed=seed, width=12, height=12, initial_population=20))
            for _ in range(200):
                world.step()
                world.check_invariants()
            self.assertGreater(len(world.lineage), 20)
            self.assertTrue(any(o.death_tick is not None for o in world.lineage.values()))

    def test_no_mutation_inherits_parent_genome(self):
        world = World(Config(mutation_probability=0))
        for _ in range(50):
            world.step()
        children = [o for o in world.lineage.values() if o.parent_id is not None]
        self.assertTrue(children)
        for child in children:
            parent = world.lineage[child.parent_id]
            self.assertEqual(child.genome, parent.genome)
            self.assertEqual(child.generation, parent.generation + 1)
            self.assertEqual(child.founder_id, parent.founder_id)
        self.assertEqual(sum(o.offspring for o in world.lineage.values()), len(children))

    def test_mutation_can_change_inherited_trait(self):
        world = World(Config(mutation_probability=1000))
        for _ in range(30):
            world.step()
        self.assertTrue(any(o.parent_id is not None and
                            o.genome != world.lineage[o.parent_id].genome
                            for o in world.lineage.values()))
        world.check_invariants()

    def test_no_resources_leads_to_extinction(self):
        world = World(Config(initial_food=0, regrowth_probability=0))
        for _ in range(world.config.initial_energy):
            world.step()
            world.check_invariants()
        self.assertEqual(world.snapshot()["population"], 0)
        self.assertIsNone(world.snapshot()["mean_genome"])
        self.assertEqual(world.snapshot()["births"], 0)

    def test_zero_energy_death_precedes_feeding_even_on_food(self):
        # Both death paths must preserve the published charge-before-feed order.
        for energy, genome in ((1, 0), (2, 1000)):
            with self.subTest(initial_energy=energy, genome=genome):
                world = World(Config(width=3, height=3, initial_population=1,
                                     initial_energy=energy, initial_food=8,
                                     regrowth_probability=0, basal_cost=1,
                                     movement_cost=1))
                organism = next(iter(world.living.values()))
                organism.genome = genome
                food_before = world.food.copy()
                position_before = organism.position
                world.step()
                world.check_invariants()
                self.assertFalse(world.living)
                self.assertEqual(organism.death_tick, 1)
                self.assertEqual(organism.energy, 0)
                self.assertEqual(organism.position, position_before)
                self.assertEqual(world.food, food_before)
                self.assertEqual(world.dissipated_energy, energy)

    def test_positive_energy_after_charges_can_feed(self):
        world = World(Config(width=3, height=3, initial_population=1,
                             initial_energy=3, initial_food=8,
                             regrowth_probability=0, basal_cost=1, movement_cost=1))
        organism = next(iter(world.living.values()))
        organism.genome = 1000
        world.step()
        world.check_invariants()
        self.assertIn(organism.id, world.living)
        self.assertIsNone(organism.death_tick)
        self.assertEqual(organism.energy, 9)
        self.assertEqual(sum(world.food), 64)
        self.assertEqual(world.dissipated_energy, 2)

    def test_torus_and_unique_neighbors(self):
        world = World(Config(width=3, height=3, initial_population=0))
        self.assertEqual(world.neighbors(0), [1, 2, 3, 6])
        narrow = World(Config(width=2, height=2, initial_population=0))
        self.assertEqual(narrow.neighbors(0), [1, 2])

    def test_births_wait_until_next_tick(self):
        world = World(Config(width=3, height=3, initial_population=1, initial_energy=100,
                             movement_cost=0, basal_cost=1, initial_food=0,
                             regrowth_probability=0, birth_threshold=10, birth_cost=0))
        world.step()
        self.assertEqual(len(world.living), 2)
        self.assertEqual(sorted(o.energy for o in world.living.values()), [49, 50])
        world.check_invariants()

    def test_artifacts_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "run"
            result = run(Config(width=8, height=8, initial_population=10), 3, target, 2)
            metadata = json.loads((target / "metadata.json").read_text())
            self.assertEqual(metadata["status"], "complete")
            self.assertEqual(metadata["completed_steps"], 3)
            self.assertIn("src/bitgenesis/v0/engine.py", metadata["source_sha256"])
            self.assertEqual(json.loads((target / "summary.json").read_text()), result)
            self.assertEqual([f["tick"] for f in json.loads((target / "frames.json").read_text())], [0, 2, 3])
            self.assertIn("World replay", (target / "index.html").read_text(encoding="utf-8"))
            self.assertIn("Direct children", (target / "lineage.html").read_text(encoding="utf-8"))
            before = (target / "metadata.json").read_bytes()
            with self.assertRaises(FileExistsError):
                run(Config(), 1, target)
            self.assertEqual((target / "metadata.json").read_bytes(), before)

    def test_configuration_rejects_invalid_values(self):
        for change in ({"width": 1}, {"initial_population": 1025}, {"basal_cost": 0},
                       {"mutation_probability": 1001}, {"seed": True},
                       {"initial_food": 25}, {"birth_threshold": 5}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(Config(), **change)

    def test_frame_budget_preserves_endpoints_and_exact_frame_metrics(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "bounded"
            run(Config(width=3, height=3, initial_population=2), 11, output, 1, max_frames=4)
            frames = json.loads((output / "frames.json").read_text())
            self.assertEqual([f["tick"] for f in frames], [0, 4, 8, 11])
            self.assertTrue(all(f["metrics"]["tick"] == f["tick"] for f in frames))
            self.assertEqual(len((output / "metrics.csv").read_text().splitlines()), 13)
            metadata = json.loads((output / "metadata.json").read_text())
            self.assertEqual(metadata["frame_interval"], 4)
            self.assertEqual(metadata["requested_frame_interval"], 1)

    def test_interruption_is_recorded_without_success_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "interrupted"
            with patch.object(World, "step", side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
                run(Config(), 10, output)
            metadata = json.loads((output / "metadata.json").read_text())
            self.assertEqual(metadata["status"], "interrupted")
            self.assertEqual(metadata["completed_steps"], 0)
            self.assertFalse((output / "index.html").exists())


if __name__ == "__main__":
    unittest.main()
