from copy import deepcopy
import json
from pathlib import Path
import unittest

from scripts.check_v0_campaign_inventory import check


class CampaignInventoryTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.inventory = json.loads((self.root / "experiments/v0/campaign-inventory.json").read_text())
        self.inventory["campaigns"] = self.inventory["campaigns"][:15]

    def test_selected_followup_counts_include_replay(self):
        report = check(self.root, self.inventory)
        self.assertEqual(report["executions"], 714)
        self.assertEqual(report["replayed_prefix_ticks"], 212000)
        self.assertEqual(report["computed_ticks_excluding_declared_replays"], 6128000)

    def test_wrong_sparse_seed_distribution_is_rejected(self):
        changed = deepcopy(self.inventory)
        changed["campaigns"][-1]["seed_counts"] = {"1200": 2, "1206": 1, "1208": 1}
        with self.assertRaisesRegex(ValueError, "seed grid"):
            check(self.root, changed)

    def test_ambiguous_seed_specification_is_rejected(self):
        self.inventory["campaigns"][-1]["seed_range"] = [1200, 1208]
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            check(self.root, self.inventory)
