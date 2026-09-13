import unittest

from scripts.build_v0_review import require_run_grid


class ReviewGridTests(unittest.TestCase):
    def test_complete_grid_accepts_reordered_records(self):
        rows = [{"treatment": treatment, "seed": seed}
                for treatment in ("food", "stored") for seed in range(3)]
        require_run_grid(list(reversed(rows)), ("food", "stored"), range(3))

    def test_same_count_duplicate_or_wrong_seed_is_rejected(self):
        rows = [{"treatment": treatment, "seed": seed}
                for treatment in ("food", "stored") for seed in range(3)]
        for replacement in (rows[1], {"treatment": "food", "seed": 99}):
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                require_run_grid([replacement, *rows[1:]], ("food", "stored"), range(3))
