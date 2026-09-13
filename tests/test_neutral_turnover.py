import unittest

from scripts.analyze_v0_neutral_turnover import window


class NeutralTurnoverTests(unittest.TestCase):
    def rows(self):
        return [dict(tick=t, births=b, deaths=d, population=n,
                     founder_lineages=1, genome_variants=1)
                for t,b,d,n in ((0,10,8,2),(1,13,9,4),(2,15,14,1))]

    def test_event_window_excludes_start_tick_but_state_range_includes_it(self):
        result = window(self.rows(), 1, 2)
        self.assertEqual((result["births"], result["deaths"]), (2,5))
        self.assertEqual((result["population_min"], result["population_max"]), (1,4))

    def test_bad_accounting_and_disordered_ticks_rejected(self):
        for key in ("population", "tick"):
            rows = self.rows()
            rows[-1][key] += 1
            with self.subTest(key=key), self.assertRaises(ValueError):
                window(rows, 0, 2)

    def test_invalid_or_missing_window_rejected(self):
        for start,end in ((-1,2),(1,1),(0,3)):
            with self.subTest(start=start,end=end), self.assertRaises(ValueError):
                window(self.rows(), start, end)
