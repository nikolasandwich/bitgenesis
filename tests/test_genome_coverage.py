import csv
from pathlib import Path
import tempfile
import unittest

from scripts.summarize_v0_genome_coverage import birth_catalog, verify_metrics
from bitgenesis.v0.engine import Config, World


class GenomeCoverageTests(unittest.TestCase):
    def catalog(self, rows, mutation=100):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "births.csv"
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(["id", "parent_id", "birth_tick", "genome"])
                writer.writerows(rows)
            return birth_catalog(path, mutation, steps=3, founders=2)

    def test_first_appearance_counts_values_once(self):
        seen, births, total = self.catalog([(0, "", 0, 100), (1, "", 0, 200),
            (2, 0, 1, 150), (3, 2, 2, 150)])
        self.assertEqual(seen, {100: 0, 200: 0, 150: 1})
        self.assertEqual(dict(births), {0: 2, 1: 1, 2: 1})
        self.assertEqual(total, 4)

    def test_no_mutation_rejects_different_parental_genome(self):
        with self.assertRaisesRegex(ValueError, "Inheritance"):
            self.catalog([(0, "", 0, 100), (1, "", 0, 200), (2, 0, 1, 200)], mutation=0)

    def test_newborn_cannot_reproduce_in_birth_tick(self):
        with self.assertRaisesRegex(ValueError, "Parent must"):
            self.catalog([(0, "", 0, 100), (1, "", 0, 200), (2, 0, 1, 150), (3, 2, 1, 150)])

    def test_duplicate_identity_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "birth identity"):
            self.catalog([(0, "", 0, 100), (0, "", 0, 200)])


class CoverageMetricTests(unittest.TestCase):
    def rows(self):
        world = World(Config(seed=53, mutation_probability=0))
        for organism in world.living.values():
            organism.genome = 100
        rows = [{**world.snapshot(), "ever_genome_values": 1}]
        for _ in range(2):
            world.step()
            rows.append({**world.snapshot(), "ever_genome_values": 1})
        self.assertEqual(rows[-1]["births"], 0)
        return rows

    def verify(self, rows):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metrics.csv"
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            from collections import Counter
            return verify_metrics(path, {100: 0}, Counter({0: 80}), 80,
                                  steps=2, horizons=[0, 1, 2])

    def test_real_short_run_matches_birth_catalog(self):
        rows = self.rows()
        final, observations, extinction = self.verify(rows)
        self.assertEqual(final, rows[-1])
        self.assertEqual(observations, {str(i): row for i, row in enumerate(rows)})
        self.assertIsNone(extinction)

    def test_unrecorded_genome_discovery_is_rejected(self):
        rows = self.rows()
        rows[1]["ever_genome_values"] = 2
        with self.assertRaisesRegex(ValueError, "birth catalog"):
            self.verify(rows)

    def test_intermediate_energy_mismatch_is_rejected(self):
        rows = self.rows()
        rows[1]["organism_energy"] += 1
        with self.assertRaisesRegex(ValueError, "Energy accounting"):
            self.verify(rows)

    def test_truncated_window_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Truncated"):
            self.verify(self.rows()[:-1])
