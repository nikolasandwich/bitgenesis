from copy import deepcopy
import unittest
from scripts.verify_v0_early_trait_samples import reconstruct
from scripts.sample_v0_early_traits import choose_sample


class EarlySampleVerificationTests(unittest.TestCase):
    def fixtures(self):
        events=[dict(event='birth',id=i,tick=0,birth_tick=0,parent_id=None,genome=250) for i in range(80)]
        lineage=[dict(id=i,parent_id=None,founder_id=i,birth_tick=0,death_tick=None,genome=250) for i in range(80)]
        events.append(dict(event='birth',id=80,tick=50,birth_tick=50,parent_id=0,genome=300))
        lineage.append(dict(id=80,parent_id=0,founder_id=0,birth_tick=50,death_tick=None,genome=300))
        events += [dict(event='death',id=1,tick=100),dict(event='death',id=2,tick=101)]
        lineage[1]['death_tick']=100;lineage[2]['death_tick']=101
        return events,lineage

    def test_event_reconstruction_agrees_with_lineage_boundary_and_priority(self):
        events,lineage=self.fixtures()
        actual,counts=reconstruct(events,23)
        self.assertEqual(actual,choose_sample(lineage,23));self.assertEqual(counts['eligible'],80)
        ids={c['id'] for c in actual['candidates']}
        self.assertNotIn(1,ids);self.assertIn(2,ids);self.assertIn(80,ids)
        damaged=deepcopy(events);damaged.pop(-2)
        self.assertNotEqual(reconstruct(damaged,23)[0],actual)

    def test_missing_founder_invalid_parent_and_duplicate_death_rejected(self):
        events,_=self.fixtures()
        for kind in ('founder','parent','death'):
            bad=deepcopy(events)
            if kind=='founder':bad.pop(0)
            elif kind=='parent':bad[80]['parent_id']=80
            else:bad.insert(-1,dict(event='death',id=1,tick=100))
            with self.assertRaises(ValueError,msg=kind):reconstruct(bad,23)


if __name__=='__main__':unittest.main()
