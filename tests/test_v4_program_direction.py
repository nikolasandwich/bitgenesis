import unittest
from copy import deepcopy
from scripts.run_v4_program_direction import run_case,pair_record,summarize,METRICS
from scripts.run_v4_copy_ablation import run_case as baseline

class DirectionTest(unittest.TestCase):
    def test_saved_tapes_and_ledger(self):
        old=baseline(120000,'random-direction',False);new=run_case(old)
        self.assertEqual(new['initial']['units'][85]['program'],[0,0,0,1])
        self.assertEqual(new['initial']['units'][86]['program'],[0,0,0,2])
        for a,b in zip(new['rows'],old['rows']):
            for k in ('directions','mutation_tickets'):self.assertEqual(a['physical'][k],b['physical'][k])
            self.assertEqual([v['proposed'] for v in a['physical']['driven']['inputs']],[v['proposed'] for v in b['physical']['driven']['inputs']])
        self.assertEqual(new['summary']['final_mass'],7)
        self.assertEqual(new['summary']['final_energy'],192+new['summary']['imported']-new['summary']['spent'])
        p=pair_record(new,old);self.assertEqual(set(p['delta']),set(METRICS))
        self.assertEqual(p['heterogeneous']['nonzero_births'],p['heterogeneous']['north_births'])
        self.assertGreater(p['heterogeneous']['north_births'],0)
    def test_paired_positive_negative_zero_and_inventory(self):
        rows=[]
        for seed in range(120000,120020):
            for exchange in (False,True):
                a=dict.fromkeys(METRICS,0);b=dict(a)
                a['births']=2;b['births']=3 if seed%3==0 else 1 if seed%3==1 else 2
                rows.append(dict(seed=seed,exchange=exchange,homogeneous=a,heterogeneous=b,delta={k:b[k]-a[k] for k in METRICS}))
        s=summarize(rows)
        self.assertEqual(s['contrasts'][0]['positive']['births'],7)
        self.assertEqual(s['contrasts'][0]['negative']['births'],7)
        self.assertEqual(s['contrasts'][0]['tie']['births'],6)
        self.assertEqual(s['contrasts'][0]['mean_delta']['births'],'0')
        for bad in (rows[:-1],rows[:-1]+[rows[0]]):
            with self.assertRaises((AssertionError,ValueError)):summarize(bad)
        bad=deepcopy(rows);bad[0]['delta']['births']=99
        with self.assertRaises((AssertionError,ValueError)):summarize(bad)

    def test_failed_run_preserves_partial_provenance(self):
        import tempfile,json,hashlib,types,sys
        from pathlib import Path
        from unittest.mock import patch
        from scripts import run_v4_program_direction as runner
        def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'run'
            helper=types.SimpleNamespace(bindings=lambda:{'bound':'same'},digest=digest,read=lambda p:{},source_cases=lambda:iter([Path('source.json')]),save=lambda p,x:p.write_text(json.dumps(x)))
            def git(command,**kwargs):return '' if command[1]=='status' else 'a'*40
            with patch.object(runner,'OUTPUT',out),patch.object(runner.subprocess,'check_output',git),patch.object(runner,'run_case',side_effect=RuntimeError('test failure')),patch.dict(sys.modules,{'scripts.program_direction_inputs':helper}):
                with self.assertRaisesRegex(RuntimeError,'test failure'):runner.main()
            meta=json.loads((out/'metadata.json').read_text())
            self.assertEqual(meta['status'],'failed');self.assertEqual(meta['input_sha256'],meta['input_sha256_after'])
            self.assertEqual(meta['output_sha256'],{'results.json':digest(out/'results.json')})
            self.assertEqual(meta['completed_cases'],0)
