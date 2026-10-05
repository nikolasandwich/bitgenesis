"""Read-only policy boundaries; new physical steps are engineering-only."""
import unittest
from unittest.mock import patch
from scripts import run_v4_triggered_policy as policy

class TriggeredPolicyTests(unittest.TestCase):
    def test_first_trigger_and_saved_control_exact_old_arm_without_physics(self):
        from scripts.founder_removal_inputs import read
        source=policy.source_case('homogeneous',120001)
        with patch('scripts.run_v4_founder_removal.step',side_effect=AssertionError('physics forbidden')):
            sel=policy.selection(source,'homogeneous')
            self.assertEqual(sel['t0'],9)
            control=policy.observe_arm(source,sel)
            old=read('data/v4-study-036/records.json')
            i=next(i for i,r in enumerate(old) if r['selection']==sel)
            self.assertEqual(control,read(f'data/v4-study-036/cases/branch-{i:03d}.json')['control'])
        self.assertEqual(control['rows'][0]['tick'],10)

    def test_no_trigger_retains_full_physics_not_applicable(self):
        source=policy.source_case('south',120000)
        self.assertIsNone(policy.selection(source,'south'))
        record=policy.produce_record(source,None,None,None)
        self.assertFalse(record['trigger'])
        self.assertEqual(record['remaining'],0)
        self.assertFalse(record['applicability']['formation'])
        self.assertGreater(record['ablation_metrics']['imported'],0)
        self.assertEqual(record['ablation_metrics']['persistent10'],0)
        m=record['ablation_metrics']
        self.assertEqual(m['final_energy'],192+m['imported']-m['spent']-m['energy_export'])
        self.assertEqual(record['delta'],dict.fromkeys(record['delta'],0))

    def test_reuse_rejects_changed_selected_identity(self):
        source=policy.source_case('homogeneous',120001)
        sel=policy.selection(source,'homogeneous')
        control=policy.observe_arm(source,sel)
        sel['offspring_ids'][0]=999
        with self.assertRaises(ValueError):policy.reuse_arm(source,sel,control)

    def test_existing_output_is_not_overwritten(self):
        from pathlib import Path
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(policy,'OUTPUT',Path(directory)),patch.object(policy.subprocess,'check_output',return_value=''):
                with self.assertRaises(FileExistsError):policy.main()

    def test_short_trigger_keeps_future_window_and_full_export_ledger(self):
        from scripts.program_position_inputs import read
        census=read('docs/research/results/v4-study-039-design-census.json')['cases']
        item=next(c for c in census if c['short_window'] and c['encoding']=='north')
        case=policy.source_case(item['encoding'],item['seed']);sel=policy.selection(case,item['encoding'])
        control=policy.observe_arm(case,sel);ablation=policy.reuse_arm(case,sel,control)
        record=policy.produce_record(case,sel,control,ablation)
        self.assertTrue(record['short_window'])
        self.assertTrue(record['applicability']['formation'])
        self.assertEqual(len(ablation['rows']),record['remaining'])
        self.assertEqual(record['ablation_metrics']['persistent10'],0)
        self.assertEqual(record['ablation_metrics']['removals'],2)
        self.assertEqual(record['ablation_metrics']['energy_export'],sel['energy_export_preview'])
        self.assertEqual(ablation['initial']['individuals'],control['initial']['individuals'])
        self.assertGreaterEqual(record['ablation_metrics']['births'],record['ablation_future_metrics']['births'])

    def test_summary_requires_all_negative_cells_and_unique_full_denominators(self):
        from copy import deepcopy
        source=policy.source_case('south',120000)
        base=policy.produce_record(source,None,None,None)
        records=[]
        for encoding in policy.ENCODINGS:
            for seed in policy.SEEDS:
                row=deepcopy(base);row.update(encoding=encoding,seed=seed);records.append(row)
        summary=policy.summarize(records)
        self.assertEqual([c['n'] for c in summary['cells']],[20]*5)
        self.assertEqual(summary['overall']['no_trigger'],100)
        self.assertEqual(len(summary['north_contrasts']),3)
        self.assertEqual(len(summary['homogeneous_contrasts']),5)
        self.assertEqual(summary['cells'][0]['paired_persistent10'][0]['n'],20)
        records[-1]=deepcopy(records[0])
        with self.assertRaisesRegex(ValueError,'hundred'):policy.summarize(records)

    def test_failure_retains_actual_step_count_and_completed_records(self):
        import tempfile
        from pathlib import Path
        from scripts.program_position_inputs import read
        with tempfile.TemporaryDirectory() as parent:
            output=Path(parent)/'failed'
            before=dict(policy.removal._steps)
            def fail(*args):
                policy.removal._steps['ablation']+=3
                raise RuntimeError('injected after three steps')
            try:
                with patch.object(policy,'OUTPUT',output),patch.object(policy.subprocess,'check_output',return_value=''),patch('scripts.triggered_policy_inputs.input_paths',return_value=[]),patch('scripts.triggered_policy_inputs.bindings',return_value={}),patch.object(policy,'source_case',side_effect=fail):
                    with self.assertRaisesRegex(RuntimeError,'injected'):policy.main()
                metadata=read(output/'metadata.json')
                self.assertEqual(metadata['status'],'failed')
                self.assertEqual(metadata['new_treatment_steps'],3)
                self.assertEqual(read(output/'records.json'),[])
            finally:policy.removal._steps.update(before)
