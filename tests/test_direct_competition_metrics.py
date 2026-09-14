from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from bitgenesis.v0.runner import load_config
from scripts.run_v0_direct_competition import initialize,evaluate
from scripts.verify_v0_direct_competition_metrics import verify_records,read_metrics,read_groups

class DirectMetricsTests(unittest.TestCase):
 def test_mixtures_and_corrupted_group_records(self):
  base=load_config(Path(__file__).resolve().parents[1]/'experiments/v0/darwin-baseline.toml')
  for a,b in ((0,1000),(256,250),(250,250)):
   with tempfile.TemporaryDirectory() as tmp:
    out=Path(tmp)/'run';world,mapping=initialize(base,24,a,b,1)
    result=evaluate(world,mapping,out,100,dict(swap=1,sampled_trait=a,ancestor_trait=b))
    initial=json.loads((out/'initial.json').read_text());rows=read_metrics(out/'metrics.csv');groups=read_groups(out/'groups.csv')
    self.assertEqual(verify_records(initial,rows,groups,result,100)['group_rows'],101)
    for field,value in (('sampled_organism_energy',10000),('sampled_population',99),('sampled_mean_genome',-1),('ancestor_births',99)):
     changed=deepcopy(groups);changed[1][field]=value
     with self.assertRaises(ValueError):verify_records(initial,rows,changed,result,100)
    changed=deepcopy(initial);changed['founder_groups']['0']='sampled'
    with self.assertRaises(ValueError):verify_records(changed,rows,groups,result,100)
    changed=deepcopy(result);changed['observations']['100']['groups']['sampled']['living_genome_histogram']={'999':1}
    with self.assertRaises(ValueError):verify_records(initial,rows,groups,changed,100)
    with self.assertRaises(ValueError):verify_records(initial,rows,groups[:-1],result,100)
