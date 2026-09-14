from copy import deepcopy
import hashlib
import unittest
from scripts.sample_v0_early_traits import choose_sample


class EarlyTraitSampleTests(unittest.TestCase):
    def fixture(self):
        return [dict(id=0,parent_id=None,founder_id=0,birth_tick=0,death_tick=101,genome=250),dict(id=1,parent_id=0,founder_id=0,birth_tick=10,death_tick=100,genome=270),dict(id=2,parent_id=0,founder_id=0,birth_tick=100,death_tick=None,genome=300)]

    def test_boundary_candidates_and_hash_choice_ignore_trait(self):
        records=self.fixture();sample=choose_sample(records,23)
        self.assertEqual([r['id'] for r in sample['candidates']],[0,2])
        expected=min((hashlib.sha256(f'bitgenesis-c023-sample-v1:23:{i}'.encode()).hexdigest(),i) for i in (0,2))[1]
        self.assertEqual(sample['selected']['id'],expected)
        changed=deepcopy(records);changed[2]['genome']=999
        self.assertEqual(choose_sample(changed,23)['selected']['id'],expected)
        self.assertEqual(choose_sample(list(reversed(records)),23),sample)

    def test_unavailable_and_invalid_ancestor_are_distinct(self):
        records=self.fixture()
        for r in records:r['death_tick']=100
        self.assertEqual(choose_sample(records,23)['selected'],None)
        records=self.fixture();records[0]['genome']=249;records[0]['death_tick']=100
        with self.assertRaises(ValueError):choose_sample(records,23)
        records=self.fixture();records[0]['death_tick']=100;records[2]['parent_id']=2
        with self.assertRaises(ValueError):choose_sample(records,23)


if __name__=='__main__':unittest.main()
