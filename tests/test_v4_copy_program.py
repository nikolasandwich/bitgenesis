import unittest
from copy import deepcopy
from scripts.run_v4_copy_program import run_case,run_probe,summarize
from scripts.run_v4_copy_control import run_case as old_case

class ProgramTest(unittest.TestCase):
    def test_transmission_and_expression(self):
        c=run_case('constructed-off')
        self.assertEqual(c['initial']['units'][85]['program'],[0,0,0,1])
        self.assertEqual(c['initial']['units'][86]['program'],[0,0,0,2])
        self.assertTrue(c['summary']['persistent10'])
        for identity,program,material in ((5,[0,0,0,1],1),(6,[0,0,0,2],2)):
            p=run_probe(c,identity)
            self.assertEqual(p['source']['program'],program)
            self.assertEqual(p['physical']['units'][69]['material'],material)
            self.assertEqual(p['physical']['units'][69]['program'],program)
    def test_all_controls_and_summary(self):
        names=('constructed-off','constructed-on','no-raw-off')
        cases=[run_case(n) for n in names];probes=[run_probe(cases[0],i) for i in (5,6)]
        s=summarize(cases,probes,[old_case(n) for n in names])
        self.assertTrue(s['expectations_met']);self.assertEqual(cases[2]['summary']['births'],0)
        self.assertFalse(cases[1]['summary']['persistent10'])
        self.assertEqual(s['formation_directions'][0]['counts'],[0,0,4,0])
        self.assertEqual(s['formed_programs'][0]['counts'],[{'program':[0,0,0,1],'count':2},{'program':[0,0,0,2],'count':2}])
    def test_unavailable_is_retained(self):
        cases=[run_case(n) for n in ('constructed-off','constructed-on','no-raw-off')]
        p=run_probe(cases[2],5)
        self.assertEqual(p,dict(source_id=5,status='unavailable',source=None,initial=None,physical=None))
        s=summarize(cases,[p,run_probe(cases[0],6)],[old_case(n) for n in ('constructed-off','constructed-on','no-raw-off')])
        self.assertFalse(s['expectations_met']);self.assertEqual(len(s['cases']),3)

    def test_failed_run_retains_source_and_partial_hashes(self):
        import tempfile,json,hashlib,types,sys
        from pathlib import Path
        from unittest.mock import patch
        from scripts import run_v4_copy_program as runner
        def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
        for changed in (False,True):
            with self.subTest(changed=changed),tempfile.TemporaryDirectory() as directory:
                out=Path(directory)/'run';calls=[]
                def bound():
                    calls.append(1);return {'source':'after' if changed and len(calls)>1 else 'before'}
                helper=types.SimpleNamespace(bindings=bound,digest=digest,read=lambda p:[],save=lambda p,x:p.write_text(json.dumps(x)))
                def git(command,**kwargs):return '' if command[1]=='status' else 'a'*40
                with patch.object(runner,'OUTPUT',out),patch.object(runner.subprocess,'check_output',git),patch.object(runner,'run_case',side_effect=RuntimeError('original failure')),patch.dict(sys.modules,{'scripts.copy_program_inputs':helper}):
                    with self.assertRaisesRegex(RuntimeError,'original failure'):runner.main()
                meta=json.loads((out/'metadata.json').read_text())
                self.assertEqual(meta['status'],'failed')
                self.assertEqual(meta['input_sha256_after'],{'source':'after' if changed else 'before'})
                self.assertEqual(meta['output_sha256'],{n:digest(out/n) for n in ('cases.json','probes.json')})
                if changed:self.assertIn('changed',meta['finalization_error'])
