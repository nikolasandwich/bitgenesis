import unittest

from scripts.verify_v2_study002 import complete_grid, inheritance


class PopulationAnalysisTests(unittest.TestCase):
    def test_missing_duplicate_and_unregistered_sources_rejected(self):
        rows = [dict(seed=s, mutation_per_thousand=m)
                for s in range(84000, 84010) for m in (100, 0)]
        self.assertEqual(len(complete_grid(rows)), 20)
        for bad in (rows[:-1], rows + [rows[0]], rows[:-1] + [dict(seed=0, mutation_per_thousand=0)]):
            with self.assertRaises(ValueError):
                complete_grid(bad)

    def test_failed_mutant_and_budget_phenotype_change_remain_distinct(self):
        founder = dict(id=0, parent=None, founder=0, generation=0, genome=[1], controller=[2],
                       birth_tick=0, death_tick=None, offspring=1)
        child = dict(founder, id=2, parent=0, generation=1, controller=[3], offspring=0)
        final = {'lineage': [founder, child], 'attempts': [
            dict(id=0, parent=None, genome=[1], valid=True, reason='ok'),
            dict(id=1, parent=0, genome=[4], valid=False, reason='empty_structure'),
            dict(id=2, parent=0, genome=[1], valid=True, reason='ok')]}
        trace = inheritance(final)
        self.assertEqual(trace['changed_genotype_attempts'], 1)
        self.assertEqual(trace['changed_genotype_successes'], 0)
        self.assertEqual(trace['offspring_attempts'], 2)
        self.assertEqual(trace['failure_reasons']['offspring'], {'empty_structure': 1})
        self.assertFalse(trace['individuals'][0]['genome_changed_from_parent'])
        self.assertTrue(trace['individuals'][0]['controller_changed_from_parent'])


if __name__ == '__main__':
    unittest.main()
