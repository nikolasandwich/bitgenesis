import unittest
from itertools import product
from scripts.summarize_v1_study001 import summarize


class StudyAggregationTests(unittest.TestCase):
    def test_sources_are_units_and_missing_trials_fail(self):
        rows=[]
        for source,kind,control,seed,renewal,swap in product((72001,72003),('descendant','founder','randomized'),('blind','shuffled','intact'),range(73000,73005),(15,30),(0,1)):
            n=18 if source==72001 and kind=='descendant' and control=='blind' else 16
            rows.append(dict(source=source,kind=kind,control=control,seed=seed,renewal=renewal,swap=swap,
                             groups={'intact':{'population':n},'control':{'population':16}},
                             initial_per_group=16,contrast='1/8' if n==18 else '0'))
        result=summarize(rows,[72001,72003])
        self.assertEqual(result['primary_mean'],'1/16')
        self.assertEqual(result['exploratory_95pct_interval'],['0','1/8'])
        self.assertFalse(result['sufficient_available_sources'])
        self.assertEqual(len(result['unavailable_sources']),8)
        with self.assertRaises(ValueError):
            summarize(rows[:-1],[72001,72003])
        with self.assertRaises(ValueError):
            summarize(rows+[rows[0]],[72001,72003])
