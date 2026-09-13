import csv
from pathlib import Path
import tempfile
import unittest

from bitgenesis.v0.engine import Config, World
from scripts.summarize_v0_long_horizon import verify_run


class LongHorizonVerificationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "run.csv"
        self.reference = Path(self.directory.name) / "reference.csv"
        world = World(Config(width=4, height=4, initial_population=3, mutation_probability=0))
        for organism in world.living.values():
            organism.genome = 250
        self.rows = [world.snapshot()]
        for _ in range(20):
            world.step()
            self.rows.append(world.snapshot())
        self.write(self.path, self.rows)
        self.write(self.reference, self.rows[:6])

    def write(self, path, rows):
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(self.rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def verify(self):
        return verify_run(self.path, self.reference, steps=20, prefix_ticks=5,
                          initial_population=3, observations=(10,), late_window=5)

    def test_complete_observed_prefix_and_late_mean(self):
        result = self.verify()
        self.assertEqual(result["population"], self.rows[-1]["population"])
        self.assertEqual(result["population_at_10"], self.rows[10]["population"])
        self.assertEqual(result["late_mean_population"], sum(r["population"] for r in self.rows[-5:]) / 5)

    def test_changed_reference_is_rejected(self):
        changed = [dict(row) for row in self.rows[:6]]
        changed[3]["food_energy"] += 1
        self.write(self.reference, changed)
        with self.assertRaisesRegex(ValueError, "prefix mismatch"):
            self.verify()

    def test_intermediate_corruption_after_prefix_is_rejected(self):
        changed = [dict(row) for row in self.rows]
        changed[12]["food_energy"] += 1
        self.write(self.path, changed)
        with self.assertRaisesRegex(ValueError, "Accounting mismatch"):
            self.verify()

    def test_missing_terminal_tick_is_rejected(self):
        self.write(self.path, self.rows[:-1])
        with self.assertRaisesRegex(ValueError, "Incomplete run"):
            self.verify()
