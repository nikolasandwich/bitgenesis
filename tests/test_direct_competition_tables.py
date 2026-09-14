from copy import deepcopy
import unittest
from scripts.export_v0_direct_competition_tables import tables
from scripts.verify_v0_direct_competition_histories import source_contrasts

class CompetitionTableTests(unittest.TestCase):
 def test_complete_tables_keep_identity_nulls_and_exact_contrasts(self):
  manifest={'samples':[dict(source_seed=1900,available=True,selected=dict(genome=250,founder_genome=250,id=7,founder_id=7))]}
  runs=[dict(source_seed=1900,replicate=r,swap=s,groups={'sampled':{'population':0 if r==0 else 81},'ancestor':{'population':0}}) for r in range(5) for s in (0,1)]
  gate=dict(**source_contrasts(runs,{1900}),available_sources=1,metric_rows_checked=100010)
  result=tables(gate,manifest)
  self.assertEqual([len(result[k]) for k in ('sources','pairs','runs')],[1,5,10])
  self.assertEqual(result['sources'][0]['source_contrast'],'81/50')
  self.assertEqual(result['sources'][0]['both_extinct'],2)
  self.assertEqual(result['sources'][0]['sampled_individual_id'],7)
  self.assertIsNone(result['runs'][0]['sampled_fraction'])
  bad=deepcopy(gate);bad['runs'].pop()
  with self.assertRaises(ValueError):tables(bad,manifest)
  bad=deepcopy(gate);bad['mean_source_contrast']='0'
  with self.assertRaises(ValueError):tables(bad,manifest)
