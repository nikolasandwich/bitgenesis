import unittest
from copy import deepcopy
from scripts import analyze_v4_position_barriers as a
from scripts import verify_v4_position_barriers as v

class PositionBarrierTests(unittest.TestCase):
    def test_empty_cells_preserved(self):
        for module in (a,v):
            result=module.summarize([])
            self.assertEqual(len(result['cells']),4)
            self.assertEqual([c['n'] for c in result['cells']],[0]*4)
    def test_wrong_north_template_not_silently_used(self):
        from scripts.analyze_v4_reformation_barriers import observe
        units=[None]*256;ids=[None]*256
        template=[dict(material=0,program=[1,0,0,0]),dict(material=0,program=[2,0,0,0])]
        people=[dict(id=i,parent=None,birth_tick=0,death_tick=None) for i in range(4)]
        for s,i,t in zip((85,86),(2,3),template):units[s]=dict(t);ids[s]=i
        row=observe(2,units,ids,people,template,[],1)
        self.assertTrue(row['slots'][0]['genetic_match'])
        north=[dict(material=0,program=[0,0,0,1]),dict(material=0,program=[0,0,0,2])]
        self.assertFalse(observe(2,units,ids,people,north,[],1)['slots'][0]['genetic_match'])
    def test_inconsistent_encoding_rejected(self):
        from scripts.position_barrier_inputs import validate_key
        with self.assertRaises(ValueError):validate_key('north',120005)
        with self.assertRaises(ValueError):validate_key('east',True)

    def test_both_entries_use_own_template_and_strict_future(self):
        from scripts.position_barrier_inputs import read
        branch=read('data/v4-study-039/cases/east-120005.json');source=read(branch['selection']['source'])
        actual=a.analyze_case('east',branch,source);expected=v.verify_case('east',branch,source)
        self.assertEqual(actual,expected)
        self.assertEqual([r['tick'] for r in actual['rows']],list(range(20,33)))
        self.assertEqual(actual['diagnostic']['tick'],19)
        for module in (a,v):
            summary=module.summarize([actual])
            self.assertEqual([r['n'] for r in summary['cells']],[0,1,0,0])
        corrupted=deepcopy(source)
        for site in (85,86):corrupted['initial']['units'][site]['program']=[9]*4
        for function in (a.analyze_case,v.verify_case):
            with self.assertRaises(ValueError):function('east',branch,corrupted)

    def test_failure_preserves_empty_records_and_hash_errors(self):
        from unittest.mock import patch
        from scripts.position_barrier_inputs import read
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'new'
            with patch.object(a,'OUTPUT',root),patch.object(a.subprocess,'check_output',return_value=''),patch.object(a,'input_paths',return_value=['absent-source']),patch.object(a,'bindings',side_effect=ValueError('injected')):
                with self.assertRaises(ValueError):a.main()
            self.assertEqual(read(root/'records.json'),[])
            meta=read(root/'metadata.json')
            self.assertEqual(meta['status'],'failed')
            self.assertIn('absent-source',meta['input_read_errors_after'])
            with patch.object(a,'OUTPUT',root),patch.object(a.subprocess,'check_output',return_value=''):
                with self.assertRaises(FileExistsError):a.main()

    def test_finalization_time_failure_is_saved(self):
        from unittest.mock import patch
        from scripts.position_barrier_inputs import read
        from pathlib import Path
        import tempfile
        clock=[0];captures=[0]
        def capture(paths):
            captures[0]+=1
            if captures[0]==2:clock[0]=601
            return {},{}
        fake=[dict(rows=[{}]*n) for n in [13]*7+[25]]
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'audit'
            with patch.object(a,'OUTPUT',output),patch.object(a.subprocess,'check_output',return_value=''),patch.object(a,'input_paths',return_value=[]),patch.object(a,'bindings',return_value={}),patch.object(a,'capture',side_effect=capture),patch.object(a,'monotonic',side_effect=lambda:clock[0]),patch.object(a,'sources',return_value=[('east','unused','unused')]*8),patch.object(a,'read',return_value={}),patch.object(a,'analyze_case',side_effect=fake),patch.object(a,'summarize',return_value={}):
                with self.assertRaisesRegex(ValueError,'final time budget'):a.main()
            self.assertEqual(read(output/'metadata.json')['status'],'failed')
