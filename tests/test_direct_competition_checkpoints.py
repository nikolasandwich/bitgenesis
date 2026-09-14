import unittest
from scripts.summarize_v0_direct_competition_checkpoints import summarize,CHECKPOINTS

class DirectCheckpointTests(unittest.TestCase):
 def test_balanced_labels_and_empty_groups_remain_distinct(self):
  rows=[]
  for source in (1900,1901):
   for replicate in range(5):
    for swap in (0,1):
     for tick in CHECKPOINTS:
      a,b=(40,40) if tick==0 else ((50,0) if swap==0 else (0,50)) if source==1900 else (0,0)
      rows.append(dict(source_seed=source,replicate=replicate,swap=swap,tick=tick,
        groups={'sampled':{'population':a},'ancestor':{'population':b}}))
  reports=summarize(rows,{1900,1901})
  self.assertEqual(len(reports),6)
  self.assertTrue(all(r['mean_source_contrast']=='0' for r in reports))
  self.assertEqual(reports[0]['status_counts']['both_present'],20)
  self.assertEqual(reports[-1]['status_counts'],dict(both_present=0,sampled_only=5,ancestor_only=5,both_extinct=10))
  for broken in (rows[:-1],rows+[rows[0]],rows[:-1]+[rows[0]]):
   with self.assertRaises(ValueError):summarize(broken,{1900,1901})
