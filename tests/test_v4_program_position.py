import unittest
from copy import deepcopy
from unittest.mock import patch
from scripts import run_v4_program_position as p
from scripts.run_v4_copy_control import CONFIG
from bitgenesis.v4.structure import snapshot


def fixture(encoding='east', founders=True):
    units=p.initial_units(encoding)
    ids=[None]*256
    for site,i in ((85,0),(86,1),(204,2)):ids[site]=i
    initial=dict(units=units,site_ids=ids,raw=[0]*256,observation=snapshot(units,ids,16,16,phase='final'))
    live=deepcopy(units); liveids=list(ids)
    for site,i,origin in ((117,3,85),(118,4,86)):
        live[site]=deepcopy(units[origin]);liveids[site]=i
    if not founders:
        for site in (85,86):live[site]=None;liveids[site]=None
    row=dict(tick=1,site_ids=liveids,physical=dict(units=live),observation=snapshot(live,liveids,16,16,phase='final'))
    return initial,row,dict(parents=[None,None,None,0,1],site_ids=liveids)


class ProgramPositionTests(unittest.TestCase):
    def test_directions_and_only_program_changes(self):
        h=p.initial_units('homogeneous')
        for d,name in enumerate(('east','west','south','north')):
            units=p.initial_units(name)
            for site in range(256):
                if site not in (85,86):self.assertEqual(units[site],h[site])
                else:
                    self.assertEqual(units[site]['material'],0)
                    self.assertEqual(units[site]['energy'],64)
                    self.assertEqual(units[site]['program'],[site-84 if x==d else 0 for x in range(4)])
    def test_own_template_and_new_exclusion(self):
        initial,row,final=fixture()
        self.assertEqual(p.new_genetic_counts(initial,[row],final),[1])
        wrong=deepcopy(initial);wrong['units']=p.initial_units('north')
        self.assertEqual(p.new_genetic_counts(wrong,[row],final),[0])
        row['site_ids']=initial['site_ids'];row['physical']['units']=initial['units'];row['observation']=initial['observation'];final['site_ids']=row['site_ids']
        self.assertEqual(p.new_genetic_counts(initial,[row],final),[0])
    def test_nine_ten_and_first_one(self):
        self.assertEqual(p.series_summary([2]*9+[0]*23),([[1,9]],9,1,0))
        self.assertEqual(p.series_summary([2]*10+[0]*22),([[1,10]],10,1,1))
        self.assertEqual(p.series_summary([1]*32),([],0,0,0))
    def test_invalid_encoding(self):
        with self.assertRaises(ValueError):p.initial_units('best')
    def test_budget_before_step(self):
        source=dict(seed=120000,mode='random-direction',exchange=False,config=CONFIG,rows=[{}]*32)
        with patch.object(p,'step') as step:
            with self.assertRaisesRegex(ValueError,'budget'):p.run_case(source,'east',lambda:(_ for _ in ()).throw(ValueError('budget')))
            step.assert_not_called()

if __name__=='__main__':unittest.main()

class SavedAndFailureTests(unittest.TestCase):
    def source(self):
        import json
        from pathlib import Path
        return json.loads(Path('data/v4-study-019/cases/seed-120000-random-direction-exchange-false.json').read_text())

    def test_uses_original_proposals_not_accepted(self):
        source=self.source()
        seen={}
        def intercept(*args,**kwargs):
            seen.update(kwargs)
            raise RuntimeError('intercept before physical call')
        with patch.object(p,'step',intercept):
            with self.assertRaisesRegex(RuntimeError,'intercept'):p.run_case(source,'east')
        saved=source['rows'][0]['physical']
        self.assertEqual(seen['proposals'],[v['proposed'] for v in saved['driven']['inputs']])
        self.assertEqual(seen['directions'],saved['directions'])
        self.assertEqual(seen['mutation_tickets'],[tuple(t) for t in saved['mutation_tickets']])

    def test_full_grid_keeps_zero_negative_and_reference_self(self):
        base=p.observe_case(self.source(),'homogeneous')[0]
        records=[]
        for e in p.ENCODINGS:
            for s in p.SEEDS:
                r=deepcopy(base);r.update(encoding=e,seed=s)
                r['metrics']['final_energy']+=(-1 if e=='east' else 1 if e=='west' else 0)
                records.append(r)
        summary=p.summarize(records)
        self.assertEqual(len(summary['cells']),5)
        self.assertEqual(summary['north_contrasts'][0]['negative']['final_energy'],20)
        self.assertEqual(summary['north_contrasts'][1]['positive']['final_energy'],20)
        self.assertEqual(summary['north_contrasts'][2]['tie']['final_energy'],20)
        self.assertTrue(all(v==0 for v in summary['homogeneous_contrasts'][-1]['totals'].values()))
        self.assertEqual(len(records[0]['formations']),16)
        with self.assertRaises(ValueError):p.summarize(records[:-1])

    def test_failed_route_retains_actual_step_count_and_bindings(self):
        import json
        import tempfile
        from pathlib import Path
        from scripts import program_position_inputs as inputs
        def fail(*args):
            p._full_world_steps+=7
            raise ValueError('budget during case')
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'output'
            with patch.object(p,'OUTPUT',output),patch.object(p.subprocess,'check_output',return_value=''),patch.object(inputs,'input_paths',return_value=[]),patch.object(inputs,'bindings',return_value={}),patch.object(inputs,'read',return_value=self.source()),patch.object(p,'run_case',side_effect=fail):
                with self.assertRaisesRegex(ValueError,'budget during'):p.main()
            meta=json.loads((output/'metadata.json').read_text())
            self.assertEqual(meta['status'],'failed')
            self.assertEqual(meta['new_full_world_steps'],7)
            self.assertEqual(meta['completed_cases'],0)
            self.assertEqual(meta['input_sha256'],meta['input_sha256_after'])
            self.assertEqual(json.loads((output/'records.json').read_text()),[])
