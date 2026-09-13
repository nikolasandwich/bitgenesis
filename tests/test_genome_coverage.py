import csv
from pathlib import Path
import tempfile
import unittest

from scripts.summarize_v0_genome_coverage import birth_catalog


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
