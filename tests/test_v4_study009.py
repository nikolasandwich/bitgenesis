from copy import deepcopy
from itertools import product
import unittest
from scripts.summarize_v4_study009 import summarize, aggregate


def fixture():
    interaction = dict(components=dict(contact=[[0, 1]], material=[[0, 1]], bond=[[0], [1]]))
    final = dict(components=dict(contact=[[0, 1]], material=[[0, 1]]))
    links = dict(splits=[0], merges=[], current_without_overlap=[1])
    return dict(observations=[dict(tick=tick, interaction=deepcopy(interaction), final=deepcopy(final),
        interaction_continuity=None if tick == 1 else {n: deepcopy(links) for n in interaction['components']},
        final_continuity={n: deepcopy(links) for n in final['components']}) for tick in range(1, 501)])


class Study009Tests(unittest.TestCase):
    def test_windows_nulls_and_destination_tick_continuity(self):
        data = fixture()
        result = summarize(data)
        self.assertEqual(result['primary'], dict(mean='1', available=400, missing=0))
        early, late = result['windows']
        self.assertEqual(early['continuity']['interaction/bond']['transitions'], 99)
        self.assertEqual(early['continuity']['final/material']['transitions'], 100)
        self.assertEqual(late['continuity']['interaction/bond']['splits'], 400)
        self.assertEqual(late['boundaries']['interaction/bond']['largest_fraction']['mean'], '1/2')
        for row in data['observations'][100:]:
            for phase in ('interaction', 'final'):
                for name in row[phase]['components']:
                    row[phase]['components'][name] = []
        empty = summarize(data)
        self.assertEqual(empty['primary'], dict(mean=None, available=0, missing=400))
        self.assertEqual(empty['windows'][1]['boundaries']['final/contact']['component_count']['mean'], '0')
        with self.assertRaises(ValueError):
            summarize(dict(observations=data['observations'][:-1]))

    def test_seed_means_have_equal_weight_and_missing_coverage_is_explicit(self):
        rows = [dict(seed=s, drive=d, mutation=m, summary=dict(primary=dict(
            mean=['0', '1', None, '1/2', '1/2'][s-96000], available=0 if s == 96002 else s-95999,
            missing=400 if s == 96002 else 400-(s-95999))))
            for s, d, m in product(range(96000, 96005), (250, 500), (0, 100))]
        windows = summarize(fixture())['windows']
        for row in rows:
            row['summary']['windows'] = windows
        for group in aggregate(rows):
            self.assertEqual(group['primary'], dict(mean='1/2', available=4, missing=1))
        for broken in (rows[:-1], rows[:-1]+[rows[0]], rows+[rows[0]]):
            with self.assertRaises(ValueError):
                aggregate(broken)
