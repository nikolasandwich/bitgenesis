from dataclasses import asdict, replace
import json
from pathlib import Path
import tempfile
import unittest

from bitgenesis.v0.engine import Config, World
from bitgenesis.v0.runner import run


class DarwinTests(unittest.TestCase):
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
            self.assertEqual(json.loads((target / "summary.json").read_text()), result)
            self.assertEqual([f["tick"] for f in json.loads((target / "frames.json").read_text())], [0, 2, 3])
            self.assertIn("World replay", (target / "index.html").read_text(encoding="utf-8"))
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


if __name__ == "__main__":
    unittest.main()
