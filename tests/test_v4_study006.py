from itertools import product
import unittest
from scripts.verify_v4_study006 import aggregate, primary


class Study006Tests(unittest.TestCase):
    def test_all_tick_denominator_includes_extinction(self):
        rows=[dict(tick=t,units=[dict(material=0) if t==1 else None]+[None]*63) for t in range(1,201)]
        self.assertEqual(primary(rows),dict(numerator=1,denominator=12800,value='1/12800'))
        with self.assertRaises(ValueError):
            primary(rows[:-1])

    def test_aggregation_within_source_before_training_seed_mean(self):
        rows=[dict(source_seed=s,training_drive=t,training_mutation=m,drive=d,
                   descendant_id=i,environment=e,difference='0')
              for s,t,m,d,i,e in product(range(96000,96005),(250,500),(0,100),(250,500),range(3),(98000,98001))]
        rows[0]['difference']='1'
        sources,groups=aggregate(rows)
        self.assertEqual(sources[0]['mean'],'1/6')
        self.assertEqual(groups[0]['mean'],'1/30')
        self.assertEqual(len(sources),40)
        self.assertEqual(len(groups),8)
        with self.assertRaises(ValueError):
            aggregate(rows[:-1])
