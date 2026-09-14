from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from bitgenesis.v0.runner import load_config
from scripts.run_v0_direct_competition import initialize,evaluate
from scripts.verify_v0_direct_competition_metrics import read_metrics,read_groups
from scripts.verify_v0_direct_competition_histories import reconstruct

class DirectHistoryTests(unittest.TestCase):
 def test_event_ancestry_and_corrupt_records(self):
  base=load_config(Path(__file__).resolve().parents[1]/'experiments/v0/darwin-baseline.toml')
  for seed in (24,25):
   for a,b in ((0,1000),(256,250),(250,250)):
    for swap in (0,1):
     with tempfile.TemporaryDirectory() as tmp:
      out=Path(tmp)/'run';world,mapping=initialize(base,seed,a,b,swap)
      result=evaluate(world,mapping,out,100,dict(swap=swap,sampled_trait=a,ancestor_trait=b))
      initial=json.loads((out/'initial.json').read_text());rows=read_metrics(out/'metrics.csv');groups=read_groups(out/'groups.csv')
      events=[json.loads(line) for line in (out/'events.jsonl').read_text().splitlines()]
      lineage=json.loads((out/'lineage.json').read_text())
      verified=reconstruct(initial,rows,groups,events,lineage,result)
      self.assertEqual(verified['individuals'],len(lineage))
      self.assertEqual(verified['metric_rows'],101)
      for field,value in (('founder_id',999),('offspring',999),('genome',-1)):
       altered=deepcopy(lineage);altered[-1][field]=value
       with self.assertRaises(ValueError):reconstruct(initial,rows,groups,events,altered,result)
      altered=deepcopy(events);child=next(e for e in altered if e['event']=='birth' and e['parent_id'] is not None);child['genome']=(child['genome']+1)%1001
      with self.assertRaises(ValueError):reconstruct(initial,rows,groups,altered,lineage,result)
      with self.assertRaises(ValueError):reconstruct(initial,rows,groups,events[:-1],lineage,result)

 def test_exact_nested_contrasts_keep_extinction_and_unbounded_scale(self):
  from scripts.verify_v0_direct_competition_histories import source_contrasts
  runs=[]
  for source in (1900,1901):
   for replicate in range(5):
    for swap in (0,1):
     a,b=((160,0) if swap==0 else (0,80)) if source==1900 else (0,0)
     runs.append(dict(source_seed=source,replicate=replicate,swap=swap,groups={'sampled':{'population':a},'ancestor':{'population':b}}))
  result=source_contrasts(runs,{1900,1901})
  self.assertEqual(result['mean_source_contrast'],'1/2')
  self.assertEqual(result['sources'],[{'source_seed':1900,'contrast':'1'},{'source_seed':1901,'contrast':'0'}])
  self.assertEqual(result['runs'][0]['contrast'],'4')
  self.assertTrue(all(r['sampled_fraction'] is None and r['status']=='both_extinct' for r in result['runs'] if r['source_seed']==1901))
  with self.assertRaises(ValueError):source_contrasts(runs[:-1],{1900,1901})
  self.assertIsNone(source_contrasts([],set())['mean_source_contrast'])
