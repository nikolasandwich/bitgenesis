import unittest
from scripts.analyze_v4_tradeoff import cohort_state, event_counts


class TradeoffTests(unittest.TestCase):
    def test_state_uses_ancestry_and_detects_contamination(self):
        parents=[None,None,None,0]
        self.assertEqual(cohort_state([[0,3],[2]],parents,{0,1}), 'closed_multi')
        self.assertEqual(cohort_state([[0,3,2]],parents,{0,1}), 'mixed')
        self.assertEqual(cohort_state([[0],[3],[2]],parents,{0,1}), 'fragmented')
        self.assertEqual(cohort_state([[2]],parents,{0,1}), 'extinct')
        self.assertEqual(cohort_state([[3],[2]],parents,{0,1}), 'closed_singleton')

    def test_short_lived_descendant_and_same_site_refill(self):
        rows=[dict(site_ids=[0,2],physical=dict(material=dict(dissolved=[1],proposals=[dict(reason='formed',target=1)]))),
              dict(site_ids=[0,None],physical=dict(material=dict(dissolved=[1],proposals=[])))]
        births,deaths=event_counts([0,1],rows,[None,None,0])
        self.assertEqual(births,[2])
        self.assertEqual(deaths,[1,2])
        with self.assertRaises(ValueError):event_counts([0,1],rows,[None,None,None])
