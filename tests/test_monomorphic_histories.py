from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from bitgenesis.v0.runner import load_config
from scripts.run_v0_monomorphic_mutation import initialize,record_world
from scripts.verify_v0_monomorphic_metrics import read_metrics
from scripts.verify_v0_monomorphic_histories import reconstruct


class MonomorphicHistoryTests(unittest.TestCase):
    def test_real_histories_and_independent_corruption_detection(self):
        base=load_config(Path(__file__).resolve().parents[1]/'experiments/v0/darwin-baseline.toml')
        for mutation in (0,100):
            with tempfile.TemporaryDirectory() as tmp:
                out=Path(tmp)/'run';result=record_world(initialize(base,23,mutation),out,100)
                initial=json.loads((out/'initial.json').read_text());rows=read_metrics(out/'metrics.csv')
                events=[json.loads(s) for s in (out/'events.jsonl').read_text().splitlines()]
                lineage=json.loads((out/'lineage.json').read_text())
                checked=reconstruct(initial,rows,events,lineage,result)
                self.assertEqual(checked['terminal_population'],result['population'])
                for damage in ('founder','parent','missing_death','histogram','offspring'):
                    e,l,r=deepcopy(events),deepcopy(lineage),deepcopy(result)
                    if damage=='founder':e[0]['genome']=251
                    elif damage=='parent':next(x for x in e if x['event']=='birth' and x['parent_id'] is not None)['parent_id']=999999
                    elif damage=='missing_death':e.remove(next(x for x in e if x['event']=='death'))
                    elif damage=='histogram':r['observations']['100']['ever_born_genome_histogram']={}
                    else:l[0]['offspring']+=1
                    with self.assertRaises(ValueError,msg=damage):reconstruct(initial,rows,e,l,r)


if __name__=='__main__':unittest.main()
