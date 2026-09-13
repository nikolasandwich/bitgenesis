from copy import deepcopy
import unittest

from bitgenesis.v0.engine import Config, World
from scripts.summarize_v0_frequency_cost import verify_rows


class FrequencyCostTests(unittest.TestCase):
    def rows(self, neutral=False, cost=1, initial_b=8, seed=1200, steps=2):
        world = World(Config(seed=seed, mutation_probability=0, movement_cost=cost))
        for o in world.living.values():
            o.genome = 250 if neutral or o.founder_id >= initial_b else 1000
        rows = []
        for tick in range(steps+1):
            if tick:
                world.step()
            n = len(world.living)
            b = sum(o.founder_id < initial_b for o in world.living.values())
            rows.append({**world.snapshot(), "a": n-b, "b": b, "b_fraction": b/n if n else None})
        return rows

    def test_valid_short_series_and_terminal_loss_fields(self):
        final = verify_rows(self.rows(),8,1000,1,steps=2)
        self.assertEqual(final["tick"],2)
        self.assertIsNone(final["a_loss_tick"])
        self.assertIsNone(final["b_loss_tick"])

    def test_extinction_uses_undefined_generation_and_fractions(self):
        rows = self.rows(cost=3, initial_b=72, seed=1205, steps=100)
        result = verify_rows(rows,72,1000,3,steps=100)
        self.assertEqual(result["population"],0)
        self.assertIsNone(result["max_generation"])
        self.assertIsNone(result["b_fraction"])
        self.assertIsNotNone(result["extinction_tick"])

    def test_changed_group_trait_and_energy_are_rejected(self):
        for field in ("a","mean_genome","organism_energy","genome_variants"):
            with self.subTest(field=field):
                rows = self.rows()
                rows[1][field] += 1
                with self.assertRaises(ValueError):
                    verify_rows(rows,8,1000,1,steps=2)

    def test_neutral_label_cannot_reappear_after_loss(self):
        rows = self.rows(neutral=True)
        rows[1].update(a=rows[1]["population"],b=0,b_fraction=0.0)
        with self.assertRaisesRegex(ValueError,"reappeared"):
            verify_rows(rows,8,250,1,steps=2)

    def test_truncation_and_fraction_corruption_are_rejected(self):
        rows = self.rows()
        with self.assertRaisesRegex(ValueError,"Truncated"):
            verify_rows(rows[:-1],8,1000,1,steps=2)
        corrupted = deepcopy(rows)
        corrupted[1]["b_fraction"] = None
        with self.assertRaisesRegex(ValueError,"fraction"):
            verify_rows(corrupted,8,1000,1,steps=2)


if __name__ == "__main__":
    unittest.main()
