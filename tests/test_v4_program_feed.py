import unittest
from copy import deepcopy
from pathlib import Path
from scripts import run_v4_program_feed as runner
from scripts.program_direction_inputs import read

class FeedTest(unittest.TestCase):
    def test_both_actual_saved_tapes(self):
        for mode in runner.MODES:
            for exchange in (False,True):
                old=read(Path('data/v4-study-019/cases')/f'seed-120000-{mode}-exchange-{str(exchange).lower()}.json')
                new=runner.run_case(old)
                self.assertEqual(new['initial']['units'][85]['program'],[0,0,0,1])
                self.assertEqual(new['initial']['units'][86]['program'],[0,0,0,2])
                for a,b in zip(new['rows'],old['rows']):
                    for k in ('directions','mutation_tickets'):self.assertEqual(a['physical'][k],b['physical'][k])
                    self.assertEqual([v['proposed'] for v in a['physical']['driven']['inputs']],[v['proposed'] for v in b['physical']['driven']['inputs']])
                self.assertEqual(new['summary']['final_mass'],7)
                self.assertEqual(new['summary']['final_energy'],192+new['summary']['imported']-new['summary']['spent'])
                p=runner.pair_record(new,old)
                self.assertEqual(p['mode'],mode)
                self.assertEqual(p['delta'],{k:runner.metrics(new)[k]-runner.metrics(old)[k] for k in runner.METRICS})
                if mode=='random-feed':self.assertEqual(p['heterogeneous']['north_births'],0)

    def records(self):
        rows=[]
        for mode in runner.MODES:
            for seed in range(120000,120020):
                for exchange in (False,True):
                    a=dict.fromkeys(runner.METRICS,0);b=dict(a)
                    a['births']=2;b['births']=3 if seed%3==0 else 1 if seed%3==1 else 2
                    if mode=='random-both':b['spent']=1
                    rows.append(dict(mode=mode,seed=seed,exchange=exchange,homogeneous=a,heterogeneous=b,delta={k:b[k]-a[k] for k in runner.METRICS}))
        return rows

    def test_mode_grid_and_signed_deltas(self):
        rows=self.records();summary=runner.summarize(rows)
        self.assertEqual([r['mode'] for r in summary],list(runner.MODES))
        for mode in summary:
            c=mode['contrasts'][0]
            self.assertEqual([c[k]['births'] for k in ('positive','negative','tie')],[7,7,6])
            self.assertEqual(c['mean_delta']['births'],'0')
        self.assertEqual(summary[0]['contrasts'][0]['mean_delta']['spent'],'0')
        self.assertEqual(summary[1]['contrasts'][0]['mean_delta']['spent'],'1')
        for change in ('missing','duplicate','mode','delta','bool'):
            bad=deepcopy(rows)
            if change=='missing':bad.pop()
            if change=='duplicate':bad[-1]=bad[0]
            if change=='mode':bad[0]['mode']='random-direction'
            if change=='delta':bad[0]['delta']['births']=5
            if change=='bool':bad[0]['exchange']=0
            with self.assertRaises(ValueError):runner.summarize(bad)

    def test_source_order(self):
        from scripts.program_feed_inputs import source_cases
        paths=list(source_cases())
        self.assertEqual(len(paths),80)
        self.assertEqual(len(set(paths)),80)
        self.assertEqual([p.name for p in paths],[f'seed-{s}-{m}-exchange-{str(e).lower()}.json' for m in runner.MODES for s in range(120000,120020) for e in (False,True)])

    def test_failure_preserves_trajectory_and_per_input_errors(self):
        import tempfile,json,hashlib,types,sys
        from unittest.mock import patch
        def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);out=root/'run';present=root/'present';missing=root/'missing'
            present.write_text('original');missing.write_text('original')
            before={str(p):digest(p) for p in (present,missing)}
            def simulate(source):
                if source=='second':
                    present.write_text('changed');missing.unlink();raise RuntimeError('simulation failure')
                return {'kept':'trajectory'}
            count=0
            def bindings():
                nonlocal count
                count+=1
                if count>1:raise ValueError('broken input proof')
                return before
            helper=types.SimpleNamespace(input_paths=lambda errors:list(before),bindings=bindings,digest=digest,read=lambda p:p.stem,source_cases=lambda:iter([Path('first.json'),Path('second.json')]),save=lambda p,x:p.write_text(json.dumps(x)))
            def git(command,**kwargs):return '' if command[1]=='status' else 'a'*40
            with patch.object(runner,'OUTPUT',out),patch.object(runner.subprocess,'check_output',git),patch.object(runner,'run_case',simulate),patch.object(runner,'pair_record',return_value={'pair':1}),patch.dict(sys.modules,{'scripts.program_feed_inputs':helper}):
                with self.assertRaisesRegex(RuntimeError,'simulation failure'):runner.main()
            meta=read(out/'metadata.json')
            self.assertEqual(meta['status'],'failed');self.assertEqual(meta['completed_cases'],1)
            self.assertEqual(meta['new_simulation_steps'],32)
            self.assertEqual(meta['input_sha256'],before)
            self.assertEqual(meta['input_sha256_after'],{str(present):digest(present)})
            self.assertIn(str(missing),meta['input_read_errors'])
            self.assertEqual(read(out/'cases/first.json'),{'kept':'trajectory'})
            self.assertEqual(meta['output_sha256'],{n:digest(out/n) for n in ('results.json','cases/first.json')})

    def test_final_metadata_write_is_within_budget_and_exclusive(self):
        import tempfile,json,types,sys
        from unittest.mock import patch
        from scripts.program_direction_inputs import digest
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'run';expired=False
            def save(path,value):
                nonlocal expired
                path.write_text(json.dumps(value))
                if path.name=='metadata.json' and value['status']=='complete':expired=True
            helper=types.SimpleNamespace(input_paths=lambda errors:[],bindings=lambda:{},digest=digest,read=lambda p:{},source_cases=lambda:iter([]),save=save)
            def git(command,**kwargs):return '' if command[1]=='status' else 'a'*40
            with patch.object(runner,'OUTPUT',out),patch.object(runner.subprocess,'check_output',git),patch.object(runner,'summarize',return_value=[]),patch.object(runner.time,'monotonic',side_effect=lambda:601 if expired else 0),patch.dict(sys.modules,{'scripts.program_feed_inputs':helper}):
                with self.assertRaisesRegex(ValueError,'bounded execution'):runner.main()
                self.assertEqual(read(out/'metadata.json')['status'],'failed')
                with self.assertRaises(FileExistsError):runner.main()

    def test_initial_binding_failure_preserves_full_known_inventory(self):
        import tempfile,json,types,sys
        from unittest.mock import patch
        from scripts.program_direction_inputs import digest
        for failure in ('missing','changed'):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);out=root/'run';present=root/'present';broken=root/'broken'
                present.write_text('original')
                if failure=='changed':broken.write_text('tampered')
                helper=types.SimpleNamespace(input_paths=lambda errors: [str(present),str(broken)],bindings=lambda: (_ for _ in ()).throw(ValueError('initial proof failure')),digest=digest,read=read,source_cases=lambda:iter([]),save=lambda p,x:p.write_text(json.dumps(x)))
                def git(command,**kwargs):return '' if command[1]=='status' else 'a'*40
                with patch.object(runner,'OUTPUT',out),patch.object(runner.subprocess,'check_output',git),patch.dict(sys.modules,{'scripts.program_feed_inputs':helper}):
                    with self.assertRaisesRegex(ValueError,'initial proof failure'):runner.main()
                meta=read(out/'metadata.json')
                self.assertEqual(meta['status'],'failed')
                self.assertEqual(meta['input_sha256'][str(present)],digest(present))
                self.assertEqual(meta['input_sha256_after'][str(present)],digest(present))
                if failure=='missing':
                    self.assertIn(str(broken),meta['input_read_errors_before'])
                    self.assertIn(str(broken),meta['input_read_errors'])
                else:
                    self.assertEqual(meta['input_sha256'][str(broken)],digest(broken))
                    self.assertEqual(meta['input_sha256_after'][str(broken)],digest(broken))

    def test_inventory_uses_archived_metadata_when_root_unreadable(self):
        from unittest.mock import patch
        from scripts import program_feed_inputs as helper
        expected=helper.input_paths();self.assertEqual(len(expected),295)
        root='data/v4-study-024/metadata.json'
        archive='docs/research/results/v4-study-024-metadata.json'
        original_read=helper.read
        def unavailable(path):
            if str(path)==root:raise OSError('unreadable metadata')
            return original_read(path)
        errors={}
        with patch.object(helper,'read',unavailable):self.assertEqual(helper.input_paths(errors),expected)
        self.assertIn(root,errors)
        errors={}
        with patch.object(helper,'read',side_effect=OSError('both unavailable')):
            recovered=helper.input_paths(errors)
        self.assertEqual(len(recovered),12)
        self.assertEqual(set(errors),{root,archive})
