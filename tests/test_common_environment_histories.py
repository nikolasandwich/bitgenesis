from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from bitgenesis.v0.runner import load_config
from scripts.run_v0_common_environment import initialize,evaluate
from scripts.verify_v0_common_environment_metrics import read_metrics
from scripts.verify_v0_common_environment_histories import reconstruct,source_contrasts


class CommonHistoryTests(unittest.TestCase):
    def test_non250_history_checks_actual_genes_before_structural_reuse(self):
        base=load_config(Path(__file__).resolve().parents[1]/'experiments/v0/darwin-baseline.toml')
        for trait in (0,256,1000):
            with tempfile.TemporaryDirectory() as tmp:
                out=Path(tmp)/'world';identity=dict(source_seed=1900,replicate=0,arm='sampled',founder_trait=trait)
                result=evaluate(initialize(base,23,trait),out,100,identity)
                initial=json.loads((out/'initial.json').read_text());rows=read_metrics(out/'metrics.csv')
                events=[json.loads(s) for s in (out/'events.jsonl').read_text().splitlines()];lineage=json.loads((out/'lineage.json').read_text())
                self.assertEqual(reconstruct(initial,rows,events,lineage,result)['terminal_population'],result['population'])
                bad=deepcopy(events);bad[0]['genome']=250
                with self.assertRaises(ValueError):reconstruct(initial,rows,bad,lineage,result)
                bad=deepcopy(lineage);bad[0]['genome']=250
                with self.assertRaises(ValueError):reconstruct(initial,rows,events,bad,result)
                bad=deepcopy(lineage);bad[0]['offspring']+=1
                with self.assertRaises(ValueError):reconstruct(initial,rows,events,bad,result)

    def test_exact_source_contrast_and_incomplete_grid(self):
        rows=[]
        for source in (1,2):
            for replicate in range(5):
                for arm in ('sampled','ancestor'):
                    alive=(source==1 and replicate==0 and arm=='sampled') or (source==2 and replicate<2 and arm=='ancestor')
                    rows.append(dict(source_seed=source,replicate=replicate,arm=arm,population=int(alive)))
        result=source_contrasts(rows,{1,2})
        self.assertEqual(result['mean_source_contrast'],'-1/10')
        self.assertEqual([s['contrast'] for s in result['sources']],['1/5','-2/5'])
        self.assertEqual((result['positive_sources'],result['negative_sources'],result['zero_sources']),(1,1,0))
        with self.assertRaises(ValueError):source_contrasts(rows[:-1],{1,2})
        self.assertIsNone(source_contrasts([],set())['mean_source_contrast'])


if __name__=='__main__':unittest.main()
