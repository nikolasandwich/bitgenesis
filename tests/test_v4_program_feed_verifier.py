import unittest
from copy import deepcopy
from scripts import verify_v4_program_feed as v
from scripts.run_v4_copy_ablation import run_case as oldcase
from scripts.run_v4_program_direction import run_case as hetero

def fixture(mode,exchange=False):
    source=oldcase(120000,mode,exchange)
    tape=deepcopy(source);tape['mode']='random-direction'
    case=hetero(tape);case['mode']=mode;case['summary']['mode']=mode
    return case,source

class FeedVerifierTest(unittest.TestCase):
    def test_both_modes_fullphysics_and_corruption(self):
        for mode in v.MODES:
            c,s=fixture(mode);v.verify_case(c,s)
            for field in ('program','feed','summary'):
                bad=deepcopy(c)
                if field=='program':bad['initial']['units'][85]['program'][3]=0
                elif field=='feed':bad['rows'][0]['physical']['driven']['inputs'][0]['proposed']+=8
                else:bad['summary']['longest']=99
                with self.subTest(mode=mode,field=field),self.assertRaises(ValueError):v.verify_case(bad,s)
    def test_full_grid_and_changes(self):
        records=[]
        for mode in v.MODES:
            for e in (False,True):
                c,s=fixture(mode,e);p=v.pair_record(c,s)
                for seed in range(120000,120020):
                    r=deepcopy(p);r['seed']=seed;records.append(r)
        result=v.aggregate(records);self.assertEqual([r['mode'] for r in result],list(v.MODES))
        for bad in (records[:-1],records[:-1]+records[:1]):
            with self.assertRaises(ValueError):v.aggregate(bad)
        bad=deepcopy(records);bad[0]['delta']['births']+=1
        with self.assertRaises(ValueError):v.aggregate(bad)

class FeedMainTests(unittest.TestCase):
    def test_main_inventory_proof_and_rehashed_tamper(self):
        import hashlib,json,sys,types
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        digest=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
        read=lambda p:json.loads(Path(p).read_text())
        for corrupt in (None,'summary','binding','inventory'):
            with self.subTest(corrupt=corrupt),TemporaryDirectory() as d:
                root=Path(d);(root/'cases').mkdir();records=[];sources=[]
                for mode,seed,e in v.GRID:
                    m={k:0 for k in v.METRICS};m.update(living=3,spent=32,final_energy=160)
                    records.append(dict(mode=mode,seed=seed,exchange=e,homogeneous=m,heterogeneous=m,delta={k:0 for k in m}))
                    name=f'seed-{seed}-{mode}-exchange-{str(e).lower()}.json'
                    (root/'cases'/name).write_text(json.dumps(dict(mode=mode,seed=seed,exchange=e)))
                    sources.append(Path('data/v4-study-019/cases')/name)
                (root/'results.json').write_text(json.dumps(records));summary=v.aggregate(records)
                if corrupt=='summary':summary[0]['contrasts'][0]['positive']['births']=1
                (root/'summary.json').write_text(json.dumps(summary))
                bound={f'fixture-{i}':str(i) for i in range(294)};bound['scripts/verify_v4_program_feed.py']=digest(v.__file__) if corrupt!='binding' else '0'*64
                hashes={str(p.relative_to(root)):digest(p) for p in root.rglob('*.json')}
                meta=dict(status='complete',planned_cases=80,completed_cases=80,new_simulation_steps=2560,new_environment_sources=0,reused_environment_sources=20,new_independent_initial_worlds=0,artificial_initial_state=True,time_limit_seconds=600,storage_limit_bytes=268435456,git_commit='a'*40,elapsed_seconds=1,input_sha256=bound,input_sha256_after=bound,output_sha256=hashes)
                (root/'metadata.json').write_text(json.dumps(meta))
                if corrupt=='inventory':next((root/'cases').iterdir()).unlink()
                helper=types.SimpleNamespace(bindings=lambda:bound,read=lambda p:{} if str(p).startswith('data/v4-study-019/') else read(p),digest=digest,source_cases=lambda:iter(sources))
                index={(r['mode'],r['seed'],r['exchange']):r for r in records}
                with patch.dict(sys.modules,{'scripts.program_feed_inputs':helper}),patch.object(v,'OUTPUT',root),patch.object(v,'verify_case') as replay,patch.object(v,'pair_record',side_effect=lambda c,s:index[c['mode'],c['seed'],c['exchange']]):
                    if corrupt:
                        with self.assertRaises(ValueError):v.cli()
                        self.assertEqual(read(root/'verification-failure.json')['status'],'failed')
                        self.assertFalse((root/'independent-verification.json').exists())
                        if corrupt=='binding':replay.assert_not_called()
                    else:
                        v.cli();self.assertEqual(replay.call_count,80)
                        proof=read(root/'independent-verification.json');self.assertEqual(proof['input_files'],295);self.assertEqual(proof['saved_steps'],2560)
                        before=(root/'independent-verification.json').read_bytes()
                        with self.assertRaises(ValueError):v.cli()
                        self.assertEqual(before,(root/'independent-verification.json').read_bytes())
                        self.assertFalse((root/'verification-failure.json').exists())
