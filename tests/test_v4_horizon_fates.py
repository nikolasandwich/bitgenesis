import copy
import unittest
from itertools import product
from scripts import analyze_v4_horizon_fates as f


def component(d=2,o=2,b=None,r=None,state='never'):
    return dict(component=0,anchor_members=[0,1],checkpoints={str(t):dict(category=f.fate(d,o,b is None or b>t),descendants=d,original_survivors=o,continuous=b is None or b>t) for t in f.TICKS},first_break_tick=b,first_complete_replacement_tick=r,first_break_state=state,order=f.event_order(b,r))


def grid():
    return [dict(history=h,seed=s,mutation=m,exchange=e,components=[component()]) for h,s,m,e in product((True,False),range(112000,112005),(0,100),(True,False))]


class Fates(unittest.TestCase):
    def test_extinction_not_replacement_and_reclosure(self):
        self.assertEqual(f.fate(0,0,False),'extinct')
        self.assertEqual(f.fate(2,0,False),'broken_replaced')
        self.assertEqual(f.fate(2,1,False),'broken_retained')
        self.assertEqual(f.fate(2,0,True),'continuous_replaced')
    def test_event_order_survives_terminal_extinction(self):
        self.assertEqual(f.event_order(20,10),'replacement_first')
        self.assertEqual(f.event_order(10,10),'same_tick')
        self.assertEqual(f.event_order(None,None),'neither')
        self.assertEqual(f.event_order(1,None),'break_only')
        self.assertEqual(f.event_order(None,1),'replacement_only')
        self.assertEqual(f.event_order(1,2),'break_first')
        self.assertEqual(f.fate(0,0,False),'extinct')
    def test_bins_and_invalid_types(self):
        self.assertEqual([f.event_bin(t) for t in (1,100,101,200,201,300,301,400,None)],['001-100','001-100','101-200','101-200','201-300','201-300','301-400','301-400','never'])
        for t in (0,401,True,1.0):
            with self.assertRaises(ValueError):f.event_bin(t)
        for args in ((0,1,False),(1,0,1),(-1,0,False),(True,0,False)):
            with self.assertRaises(ValueError):f.fate(*args)
    def test_break_state_uses_living_only(self):
        parents=[None,None,None,0,1,3]
        founders={0,1,2}
        self.assertEqual(f.first_break_state([[0],[1],[2]],parents,founders,[0,1]),'fragmented')
        self.assertEqual(f.first_break_state([[3,2]],parents,founders,[0,1]),'mixed')
        self.assertEqual(f.first_break_state([[3]],parents,founders,[0,1]),'closed_singleton')
        self.assertEqual(f.first_break_state([[2]],parents,founders,[0,1]),'extinct')
    def test_complete_grid_equal_weight_missing(self):
        rows=grid()
        for row in rows:
            if row['seed']==112000:
                row['components']=[dict(component(d=0,o=0,b=1,state='extinct'),component=i,anchor_members=[i*2,i*2+1]) for i in range(9)]
            elif row['seed']==112004:row['components']=[]
        results,summary=f.summarize_records(rows)
        self.assertEqual(summary['checkpoint_cells'][0]['metrics']['extinct'],dict(mean='1/4',available=4,missing=1))
        self.assertEqual([len(summary[k]) for k in ('checkpoint_cells','checkpoint_pairs','checkpoint_groups','timing_cells','timing_pairs','timing_groups')],[32,20,16,8,20,4])
        self.assertEqual(results[0]['eligible'],9)
        for mutate in (lambda r:r.pop(),lambda r:r.append(copy.deepcopy(r[0])),lambda r:r[0].update(history=1)):
            bad=copy.deepcopy(rows);mutate(bad)
            with self.assertRaises(ValueError):f.summarize_records(bad)
    def test_reject_invalid_results(self):
        results,_=f.summarize_records(grid())
        changes=[lambda r:r[0].update(status='failed'),lambda r:r[0].update(eligible=True),lambda r:r[0]['checkpoints']['100']['fractions'].update(extinct=None),lambda r:r[0]['checkpoints']['100']['counts'].update(extinct=1),lambda r:r[0]['checkpoints']['100']['fractions'].update(extinct='0/2')]
        for change in changes:
            bad=copy.deepcopy(results);change(bad)
            with self.assertRaises(ValueError):f.aggregate_results(bad)

class ProductionRoute(unittest.TestCase):
    def test_saved_replacement_then_extinction_keeps_first_break_state(self):
        import json
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            initial=dict(observation=dict(components=dict(material=[[0,1],[2]])))
            (root/'initial.json').write_text(json.dumps(initial))
            (root/'final.json').write_text(json.dumps(dict(parents=[None,None,None,0,1])))
            steps=[]
            for t in range(1,401):
                groups=[[3],[4],[2]] if t==1 else [[3,4],[2]] if t<=200 else [[2]]
                steps.append(json.dumps(dict(tick=t,observation=dict(components=dict(material=groups)))))
            (root/'steps.jsonl').write_text('\n'.join(steps)+'\n')
            saved={}
            for t in f.TICKS:
                saved[str(t)]=[dict(component=0,anchor_members=[0,1],anchor_size=2,whole_world_anchor=False,first_break_tick=1,first_complete_replacement_tick=1,continuous_closed_multi=False,endpoint=dict(descendants=2 if t<=200 else 0,original_survivors=0)),dict(component=1)]
            row=dict(history=True,seed=112000,mutation=0,exchange=True,status='complete',directory=str(root),records=saved)
            branch=f.classify_branch(row);c=branch['components'][0]
            self.assertEqual(c['first_break_state'],'fragmented')
            self.assertEqual(c['order'],'same_tick')
            self.assertEqual(c['checkpoints']['200']['category'],'broken_replaced')
            self.assertEqual(c['checkpoints']['400']['category'],'extinct')
            result=f.branch_result(branch)
            self.assertEqual(result['timing']['counts']['replacement_bin:001-100'],1)
            self.assertEqual(result['checkpoints']['400']['counts']['extinct'],1)

    def test_failed_run_preserves_partial_outputs_and_bindings(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        rows=grid()
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'fates'
            calls=[]
            def classify(row):
                calls.append(row)
                if len(calls)==2:raise ValueError('synthetic failed branch')
                return row
            with patch.object(f,'OUTPUT',out),patch.object(f.subprocess,'check_output',side_effect=['','abc']),patch('scripts.horizon_fate_inputs.bindings',return_value={'fixture':'frozen'}),patch('scripts.horizon_fate_inputs.source_rows',return_value=rows),patch.object(f,'classify_branch',side_effect=classify):
                with self.assertRaisesRegex(ValueError,'synthetic failed branch'):f.main()
            meta=json.loads((out/'metadata.json').read_text())
            self.assertEqual(meta['status'],'failed')
            self.assertEqual(meta['completed_branches'],1)
            self.assertEqual(meta['input_sha256'],meta['input_sha256_after'])
            self.assertEqual(len(json.loads((out/'records.json').read_text())),1)
            self.assertEqual(len(json.loads((out/'results.json').read_text())),1)
            with patch.object(f,'OUTPUT',out),patch.object(f.subprocess,'check_output',return_value=''):
                with self.assertRaises(FileExistsError):f.main()

    def test_budget_failure_is_auditable(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'fates'
            with patch.object(f,'OUTPUT',out),patch.object(f,'STORAGE',0),patch.object(f.subprocess,'check_output',side_effect=['','abc']),patch('scripts.horizon_fate_inputs.bindings',return_value={'fixture':'frozen'}),patch('scripts.horizon_fate_inputs.source_rows',return_value=grid()):
                with self.assertRaisesRegex(ValueError,'storage budget exceeded'):f.main()
            meta=json.loads((out/'metadata.json').read_text())
            self.assertEqual(meta['status'],'failed')
            self.assertEqual(meta['completed_branches'],0)
