import copy
import unittest
from scripts.summarize_v0_renewal_stocks import summarize


class RenewalSummaryTests(unittest.TestCase):
    def fixture(self):
        active=dict(ticks=100,actual_added=6100,uncapped=6200,discarded=100,expected_added='6000',expected_cap_loss='144')
        empty=dict(ticks=0,actual_added=0,uncapped=0,discarded=0,expected_added='0',expected_cap_loss='0')
        return dict(rows=[dict(arm='block',birth_threshold=t,renewal=n,seed=s,partitions=dict(all=active,active=active,empty=empty)) for t in (40,160) for n in ('frequent-small','reference','rare-large') for s in range(1700,1710)])

    def test_empty_window_ratios_are_unavailable(self):
        result=summarize(self.fixture())
        empty=[r for r in result['rows'] if r['partition']=='empty']
        self.assertEqual(len(empty),60)
        self.assertTrue(all(r['realized_discard_fraction'] is None and r['expected_loss_fraction'] is None for r in empty))
        self.assertEqual(result['rows'][0]['actual_minus_expected'],'100')

    def test_partition_and_nominal_corruption_rejected(self):
        bad=copy.deepcopy(self.fixture());bad['rows'][0]['partitions']['empty']['ticks']=1
        with self.assertRaises(ValueError):summarize(bad)
        bad=copy.deepcopy(self.fixture());bad['rows'][0]['partitions']['active']['expected_cap_loss']='145'
        with self.assertRaises(ValueError):summarize(bad)
