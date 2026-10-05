"""Synthetic and mocked Study043 boundaries; never run research physics."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import run_v4_middle_north_policy as policy


class MiddleNorthPolicyTests(unittest.TestCase):
    def test_mask_all_sites_without_mutating_source(self):
        directions=[i%4 for i in range(256)]
        original=list(directions)
        changed=policy.north_directions(directions)
        self.assertEqual(directions,original)
        self.assertEqual(changed[101:103],[3,3])
        self.assertEqual([v for i,v in enumerate(changed) if i not in (101,102)],
                         [v for i,v in enumerate(original) if i not in (101,102)])
        with self.assertRaises(ValueError):policy.north_directions(directions[:-1])
        with self.assertRaises(ValueError):policy.north_directions([4]*256)

    def test_summary_difference_in_differences_and_full_denominator(self):
        records=[]
        for enc in policy.ENCODINGS:
            for seed in policy.SEEDS:
                c=dict.fromkeys(policy.METRICS,0);a=dict(c)
                c['imported']=100 if enc=='east' else 50
                a['imported']=c['imported']+(3 if enc=='east' else 1)
                records.append(dict(encoding=enc,seed=seed,trigger=False,short_window=False,remaining=0,
                    control_metrics=c,ablation_metrics=a,delta={k:a[k]-c[k] for k in c}))
        result=policy.summarize(records)
        self.assertEqual(result['north_contrasts'][0]['totals']['imported'],40)
        self.assertEqual(result['north_contrasts'][0]['mean_delta']['imported'],'2')
        self.assertEqual(result['cells'][0]['mean_delta']['imported'],'3')
        self.assertEqual([r['n'] for r in result['cells']],[20]*5)
        with self.assertRaises(ValueError):policy.summarize(records[:-1])

    def test_existing_output_is_exclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(policy,'OUTPUT',Path(directory)),patch.object(policy.subprocess,'check_output',return_value=''):
                with self.assertRaises(FileExistsError):policy.main()

    def test_no_trigger_reuses_old_ablation_metrics_without_physics(self):
        old=dict(trigger=False,control_metrics={'a':99},ablation_metrics={'a':5},
                 control_future_metrics={'a':1},ablation_future_metrics={'a':0},
                 control_episodes=[[1,2]],ablation_episodes=[],delta={'a':-94})
        original=deepcopy(old)
        new=policy.no_trigger_record(old)
        self.assertEqual(old,original)
        self.assertEqual(new['control_metrics'],{'a':5})
        self.assertEqual(new['ablation_metrics'],{'a':5})
        self.assertEqual(new['delta'],{'a':0})
        self.assertEqual(new['control_future_metrics'],{'a':0})
        with self.assertRaises(ValueError):policy.no_trigger_record(dict(old,trigger=True))

    def synthetic(self,t0=31):
        from bitgenesis.v4.lineage import Observer
        units=[None]*256
        for s in (85,86):units[s]=dict(material=1,energy=96,program=[0,1,2,3])
        source=dict(initial=dict(units=deepcopy(units)),rows=[])
        for t in range(1,33):
            source['rows'].append(dict(tick=t,site_ids=[0 if s==85 else 1 if s==86 else None for s in range(256)],physical=dict(tick=t,units=deepcopy(units),raw=[0]*256,material=dict(dissolved=[],proposals=[]),directions=[i%4 for i in range(256)],mutation_tickets=[[0,0] for _ in range(256)],driven=dict(inputs=[dict(site=i,proposed=7) for i in range(256)]))))
        observer=Observer(units)
        for row in source['rows'][:t0]:observer.accept(row['physical'])
        raw=[int(i in (85,86)) for i in range(256)]
        initial=dict(tick=t0,units=[None]*256,raw=raw,site_ids=[None]*256,
            individuals=deepcopy(observer.individuals),parents=[None,None],energy_before=192,energy_export=192,energy_after=0,
            removals=[dict(identity=i,site=s,energy=96) for i,s in enumerate((85,86))])
        return source,dict(t0=t0,offspring_ids=[],exchange=False),dict(initial=initial)

    def test_strict_future_exact_initial_and_all_other_tapes_unchanged(self):
        source,selection,old=self.synthetic()
        original=deepcopy(source);before=deepcopy(old)
        event=dict(imported=0,spent=0,material_before=2,material_after=2,material=dict(dissolved=[],proposals=[]))
        seen=[]
        def fake_step(units,raw,**kwargs):
            seen.append(kwargs)
            return units,raw,event
        baseline=dict(policy._steps)
        try:
            with patch.object(policy,'step',side_effect=fake_step),patch.object(policy,'match_copies',return_value=[]):
                result=policy.run_arm(source,selection,old)
            self.assertEqual(result['initial'],before['initial'])
            self.assertEqual(source,original)
            self.assertEqual(old,before)
            self.assertEqual([r['tick'] for r in result['rows']],[32])
            self.assertEqual(result['metrics']['persistent10'],0)
            self.assertEqual(result['final']['individuals'],before['initial']['individuals'])
            self.assertEqual(seen[0]['directions'],policy.north_directions(original['rows'][31]['physical']['directions']))
            self.assertEqual(seen[0]['proposals'],[7]*256)
            self.assertEqual(seen[0]['mutation_tickets'],[(0,0)]*256)
            self.assertEqual(policy._steps['ablation']-baseline['ablation'],1)
        finally:policy._steps.update(baseline)

    def test_no_future_at_t32_and_rejects_future_history(self):
        source,selection,old=self.synthetic(32)
        with patch.object(policy,'step',side_effect=AssertionError('physics forbidden')):
            result=policy.run_arm(source,selection,old)
            self.assertEqual(result['rows'],[])
            self.assertEqual(result['metrics']['persistent10'],0)
            old['initial']['individuals'].append(dict(id=2))
            with self.assertRaisesRegex(ValueError,'prefix history'):policy.run_arm(source,selection,old)

    def test_failure_preserves_actual_steps_and_records(self):
        from scripts.program_position_inputs import read
        baseline=dict(policy._steps)
        def fail(*args):
            policy._steps['ablation']+=3
            raise RuntimeError('injected')
        try:
            with tempfile.TemporaryDirectory() as directory:
                output=Path(directory)/'failed'
                with patch.object(policy,'OUTPUT',output),patch.object(policy.subprocess,'check_output',return_value=''),patch('scripts.middle_north_policy_inputs.input_paths',return_value=[]),patch('scripts.middle_north_policy_inputs.bindings',return_value={}),patch.object(policy,'read',side_effect=fail):
                    with self.assertRaisesRegex(RuntimeError,'injected'):policy.main()
                meta=read(output/'metadata.json')
                self.assertEqual(meta['status'],'failed')
                self.assertEqual(meta['new_treatment_steps'],3)
                self.assertEqual(read(output/'records.json'),[])
        finally:policy._steps.update(baseline)
