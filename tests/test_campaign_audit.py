import csv
import json
from pathlib import Path
import tempfile
import unittest

from scripts.audit_v0_world_sizes import audit


class CampaignAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        metadata = {"protocol": "campaign-005-world-sizes-1", "rules_version": "v0-darwin-1",
                    "status": "complete", "initial_population_density": "5/64", "steps": 2,
                    "widths": [8], "seeds": [1], "treatments": {"evolving": "", "neutral": ""},
                    "baseline_config": {"initial_energy": 24, "initial_food": 8, "food_capacity": 24}}
        self.write_json("metadata.json", metadata)
        self.rows = [{"tick": tick, "population": 5, "births": 0, "deaths": 0,
                      "organism_energy": 120 - tick * 5, "food_energy": 512,
                      "supplied_energy": 632, "dissipated_energy": tick * 5,
                      "mean_genome": 250, "genome_variants": 1, "founder_lineages": 5,
                      "max_generation": 0} for tick in range(3)]
        summaries = []
        for treatment in ("evolving", "neutral"):
            self.write_csv(f"width-8-{treatment}-seed-1.csv", self.rows)
            summaries.append({"width": 8, "treatment": treatment, "seed": 1, "initial_population": 5,
                              **self.rows[-1], "late_mean_population": 5, "terminal_founder_fraction": 1,
                              "first_single_founder_tick": None, "extinction_tick": None})
        self.write_json("results.json", summaries)
        self.write_csv("results.csv", summaries)

    def write_json(self, name, value):
        (self.root / name).write_text(json.dumps(value), encoding="utf-8")

    def write_csv(self, name, rows):
        with (self.root / name).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def test_complete_dataset(self):
        result = audit(self.root)
        self.assertEqual((result["runs"], result["metric_rows"]), (2, 6))

    def test_summary_corruption_is_rejected(self):
        summaries = json.loads((self.root / "results.json").read_text())
        summaries[0]["late_mean_population"] = 6
        self.write_json("results.json", summaries)
        with self.assertRaisesRegex(ValueError, "late_mean_population"):
            audit(self.root)

    def test_intermediate_energy_corruption_is_rejected(self):
        self.rows[1]["supplied_energy"] += 1
        self.write_csv("width-8-evolving-seed-1.csv", self.rows)
        with self.assertRaisesRegex(ValueError, "energy accounting"):
            audit(self.root)

    def test_missing_terminal_tick_is_rejected(self):
        self.write_csv("width-8-evolving-seed-1.csv", self.rows[:-1])
        with self.assertRaisesRegex(ValueError, "incomplete tick range"):
            audit(self.root)
