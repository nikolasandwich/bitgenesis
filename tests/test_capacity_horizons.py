from itertools import product
import unittest

from scripts.analyze_v0_capacity_horizons import survival_intervals


class CapacityHorizonTests(unittest.TestCase):
    def test_all_small_censoring_and_extinction_pairs_match_direct_states(self):
        horizon = 4
        cases = list(product((None, 1, 2, 4), repeat=2))
        for first, second in product(cases, repeat=2):
            pairs = [first, second]
            intervals = survival_intervals(pairs, horizon)
            expanded = {}
            for interval in intervals:
                for tick in range(interval['start_tick'], interval['end_tick'] + 1):
                    self.assertNotIn(tick, expanded)
                    expanded[tick] = interval
            self.assertEqual(set(expanded), set(range(horizon + 1)))
            for tick, interval in expanded.items():
                states = [(a is None or a > tick, b is None or b > tick) for a, b in pairs]
                for name, state in [('both_alive', (True, True)), ('capacity_96_only', (False, True)),
                                    ('capacity_24_only', (True, False)), ('both_extinct', (False, False))]:
                    self.assertEqual(interval[name], states.count(state))
                self.assertEqual(interval['signed_discordance'], sum(b-a for a, b in states))

    def test_invalid_and_beyond_horizon_deaths_rejected(self):
        for death in (0, -1, 5, True, 1.5):
            with self.assertRaises(ValueError):
                survival_intervals([(None, death)], 4)


if __name__ == '__main__':
    unittest.main()
