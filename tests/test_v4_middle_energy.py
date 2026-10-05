import json
import unittest
from pathlib import Path
from copy import deepcopy
from scripts import analyze_v4_middle_energy as a

class MiddleEnergyTest(unittest.TestCase):
    def test_window_threshold_birth_death_and_censor(self):
        rows=[dict(phase='birth',tick=4,end_energy=17),
              dict(phase='action',tick=5,preformation_energy=16,direction=0,reason='occupied',end_energy=16),
              dict(phase='action',tick=6,preformation_energy=15,direction=3,reason='energy',end_energy=15),
              dict(phase='action',tick=7,preformation_energy=0,direction=3,reason='dissolved',end_energy=0)]
        w=a.window(rows,False)
        self.assertEqual(w['eligible_ticks'],[5]);self.assertTrue(w['eligible_prefix'])
        self.assertEqual(w['first_north_ticket'],6);self.assertEqual(w['first_north_proposal'],6)
        self.assertEqual(w['north_proposals'],1);self.assertFalse(w['right_censored'])
        self.assertEqual(a.window(rows[:1],True)['eligible_steps'],0)
        self.assertTrue(a.window(rows[:1],True)['right_censored'])
        self.assertIsNone(a.window([rows[-1]],False)['first_north_proposal'])

    def test_nonprefix_rejected_and_split_boundary(self):
        rows=[dict(phase='action',tick=t,preformation_energy=e,direction=0,reason='energy',end_energy=e) for t,e in [(1,15),(2,16)]]
        with self.assertRaisesRegex(ValueError,'prefix'):a.window(rows,True)
        for e in (16,28):
            child=(e-5)//2
            self.assertEqual(a.split(e,dict(cost=5,child_energy=child,parent_energy=e-5-child)),(4,1,child,e-5-child))
        with self.assertRaises(ValueError):a.split(16,dict(cost=5,child_energy=6,parent_energy=5))

    def test_engineering_first_only(self):
        b=json.loads(Path('data/v4-study-039/cases/east-120005.json').read_text())
        r=a.analyze_case('east',b)
        self.assertEqual(r['saved_steps'],13);self.assertEqual(len(r['identities']),4)
        for i in r['identities']:
            self.assertFalse(i['left_censored']);self.assertEqual(i['rows'][0]['phase'],'birth')
            self.assertTrue(all(v['tick']>i['birth_tick'] for v in i['rows'] if v['phase']=='action'))
        s=a.summarize([r]);self.assertEqual(len(s['cells']),24)
        self.assertEqual(s['overall']['identities'],4)
        bad=deepcopy(b);bad['ablation']['rows'][0]['physical']['driven']['inputs'][101]['proposed']=1
        with self.assertRaisesRegex(ValueError,'middle input'):a.analyze_case('east',bad)

    def test_same_site_death_refill_keeps_two_energy_records(self):
        b=json.loads(Path('data/v4-study-039/cases/east-120005.json').read_text())
        result=a.analyze_case('east',b);ids={i['identity']:i for i in result['identities']}
        old=ids[12]['rows'][-1];new=ids[13]['rows'][0]
        self.assertEqual((old['tick'],new['tick']),(29,29))
        self.assertEqual((old['end_energy'],old['reason'],old['proposal']),(0,'dissolved',None))
        self.assertEqual((new['phase'],new['end_energy']),('birth',28))
        self.assertEqual(ids[13]['rows'][1]['tick'],30)
        self.assertTrue(ids[13]['window']['right_censored'])
        self.assertFalse(ids[12]['window']['right_censored'])
        self.assertTrue(ids[11]['window']['qualification_loss_after_success'])

    def test_initial_failure_keeps_empty_records_and_hash_errors(self):
        import tempfile,types,sys,hashlib
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'run';missing=str(Path(directory)/'missing')
            helper=types.SimpleNamespace(input_paths=lambda:[missing],capture=lambda paths:({}, {missing:'missing'}),
                bindings=lambda:{},sources=lambda:[],read=lambda p: {},save=lambda p,v:p.write_text(json.dumps(v)),
                digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest())
            with patch.object(a,'OUTPUT',out),patch.object(a.subprocess,'check_output',return_value=''),patch.dict(sys.modules,{'scripts.middle_energy_inputs':helper}):
                with self.assertRaisesRegex(ValueError,'validated initial bindings'):a.main()
                with self.assertRaises(FileExistsError):a.main()
            meta=json.loads((out/'metadata.json').read_text())
            self.assertEqual(meta['status'],'failed');self.assertEqual(meta['completed_cases'],0)
            self.assertEqual(meta['input_read_errors_after'],{missing:'missing'})
            self.assertIn('records.json',meta['output_sha256'])

    def test_left_censor_uses_historical_birth_and_observed_energy(self):
        b=json.loads(Path('data/v4-study-039/cases/east-120005.json').read_text())
        row=b['ablation']['rows'][4];p=row['physical']
        b['selection'].update(t0=24,remaining_steps=8)
        b['ablation']['initial']=dict(tick=24,units=p['units'],raw=p['raw'],site_ids=row['site_ids'])
        b['ablation']['rows']=b['ablation']['rows'][5:]
        result=a.analyze_case('east',b);person=result['identities'][0]
        self.assertTrue(person['left_censored']);self.assertEqual(person['birth_tick'],24)
        self.assertEqual(person['rows'][0]['phase'],'initial')
        self.assertEqual(person['source_region'],'lower')
        self.assertEqual(person['rows'][1]['tick'],25)
