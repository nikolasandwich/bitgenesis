import unittest

from scripts.build_v0_review import require_run_grid, require_followup_records


class ReviewGridTests(unittest.TestCase):
    def followups(self):
        return [dict(movement_cost=c, initial_b=b, treatment="neutral", seed=s, a=1, b=1)
                for c, b, s in ((1,72,1206), (2,8,1200), (2,72,1208), (4,72,1208))]

    def test_conditional_cohort_accepts_reordering(self):
        rows = self.followups()
        require_followup_records(list(reversed(rows)), rows, rows)

    def test_conditional_cohort_rejects_duplicate_and_changed_outcome(self):
        rows = self.followups()
        for replacement in (rows[1], {**rows[0], "a": 9}):
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                require_followup_records([replacement, *rows[1:]], rows, rows)

    def test_conditional_cohort_rejects_unselected_reference(self):
        rows = self.followups()
        with self.assertRaises(ValueError):
            require_followup_records(rows, [{**rows[0], "a": 0}, *rows[1:]], rows)

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
