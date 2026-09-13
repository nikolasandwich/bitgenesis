"""Synthetic accounting records test follow-up validation, not engine biology."""

import unittest

from scripts.summarize_v0_neutral_followup import verify_followup


class NeutralFollowupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = [dict(tick=t, population=80, a=8, b=72, b_fraction=0.9,
                         births=0, deaths=0, organism_energy=1920, food_energy=8192,
                         supplied_energy=10112+80*t, dissipated_energy=80*t,
                         mean_genome=250.0, genome_variants=1, founder_lineages=80,
                         max_generation=0) for t in range(30001)]

    def test_complete_followup_keeps_observations(self):
        result = verify_followup(self.rows, self.rows[:3001], 1, 72)
        self.assertEqual(result["observations"]["10000"], self.rows[10000])
        self.assertIsNone(result["a_loss_tick"])
        self.assertIsNone(result["b_loss_tick"])

    def test_different_or_truncated_prefix_rejected(self):
        changed = list(self.rows[:3001])
        changed[2000] = {**changed[2000], "food_energy": 8191}
        for prefix in (changed, self.rows[:3000]):
            with self.subTest(length=len(prefix)):
                with self.assertRaisesRegex(ValueError, "prefix"):
                    verify_followup(self.rows, prefix, 1, 72)

    def test_truncated_followup_rejected(self):
        with self.assertRaisesRegex(ValueError, "Truncated"):
            verify_followup(self.rows[:-1], self.rows[:3001], 1, 72)


if __name__ == "__main__":
    unittest.main()
