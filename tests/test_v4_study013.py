import json
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from bitgenesis.v4.hereditary_runner import run as source_run
from bitgenesis.v4.exchange_branch_audit import physical_step
from scripts import run_v4_study013 as study

class ImmediateTests(unittest.TestCase):
    def test_replay_reset_full_records_and_single_source_audit(self):
        with TemporaryDirectory() as d:
            root=Path(d); source=root/'source'
            source_run(source,106000,steps=8,width=4,height=4,mutation_per_thousand=100,leak=4)
            before=study.hashes(source)
            with patch.object(study,'source_audit',wraps=study.source_audit) as audit:
                summary=study.run_source(root/'out',source,start=2,end=8)
            self.assertEqual(audit.call_count,1)
            rows=[json.loads(s) for s in (root/'out/paired-steps.jsonl').read_text().splitlines()]
            history=[json.loads(s) for s in (source/'steps.jsonl').read_text().splitlines()]
            config=study.read(source/'metadata.json')
            self.assertEqual([r['tick'] for r in rows],list(range(2,9)))
            self.assertEqual(summary['steps'],7)
            for row in rows:
                origin=history[row['tick']-2]
                self.assertEqual(row['on'],history[row['tick']-1])
                self.assertEqual(row['off'],physical_step(origin['units'],origin['raw'],config,history[row['tick']-1],False))
                self.assertEqual(sum(map(sum,row['metrics']['actor_matrix'])),sum(u is not None for u in origin['units']))
            self.assertEqual(before,study.hashes(source))
            self.assertTrue(any(r['metrics']['counts']['on']['energy_eligible']>r['metrics']['counts']['on']['births'] for r in rows))
            with self.assertRaises(FileExistsError):study.run_source(root/'out',source,2,8)
            with patch.object(study,'step',side_effect=RuntimeError('injected')):
                with self.assertRaisesRegex(RuntimeError,'injected'):study.run_source(root/'failed',source,2,8)
            self.assertEqual(study.read(root/'failed/metadata.json')['status'],'failed')

    def test_summary_grid_and_coverage(self):
        zero=dict(initial_occupied=0,counts={s:dict.fromkeys(study.METRICS,0) for s in ('on','off')},differences=dict.fromkeys(study.METRICS,0),actor_matrix=[[0]*6 for _ in range(6)],birth_gains=0,birth_losses=0)
        summary=study.summarize([zero]*400)
        rows=[dict(seed=s,drive=250,mutation=m,status='complete',summary=summary) for s,m in product(range(96000,96005),(0,100))]
        self.assertEqual(study.aggregate(rows)['groups'][0]['metrics']['births'],dict(mean='0',available=5,missing=0))
        for bad in (rows[:-1],rows[:-1]+rows[:1]):
            with self.assertRaises(ValueError):study.aggregate(bad)
        rows[0]=dict(rows[0],summary=study.summarize([zero]*399))
        with self.assertRaises(ValueError):study.aggregate(rows)

    def test_clean_exclusive_failure_and_budgets(self):
        with patch.object(study.subprocess,'check_output',return_value='dirty'):
            with self.assertRaisesRegex(ValueError,'clean'):study.main()
        sources=[dict(seed=s,drive=250,mutation=m) for s,m in product(range(96000,96005),(0,100))]
        for budget in ('STORAGE_LIMIT','TIME_LIMIT'):
            with TemporaryDirectory() as d, patch.object(study,'OUTPUT',Path(d)/'out'), patch.object(study.subprocess,'check_output',return_value=''), patch.object(study,'binding_paths',return_value=[]), patch.object(study,'preflight',return_value=(sources,Path(d),{},{})), patch.object(study,'source_bindings',return_value={}), patch.object(study,'check_source_bindings'), patch.object(study,budget,0), patch.object(study,'run_source') as run:
                study.main();run.assert_not_called()
                self.assertIn(study.read(Path(d)/'out/metadata.json')['status'],('storage_limit','time_limit'))
                self.assertFalse((Path(d)/'out/summary.json').exists())
        with TemporaryDirectory() as d, patch.object(study,'OUTPUT',Path(d)/'out'), patch.object(study.subprocess,'check_output',return_value=''), patch.object(study,'binding_paths',return_value=[]), patch.object(study,'preflight',side_effect=ValueError('preflight')):
            with self.assertRaisesRegex(ValueError,'preflight'):study.main()
            self.assertEqual(study.read(Path(d)/'out/metadata.json')['status'],'failed')

    def test_no_transfer_and_boolean_flags(self):
        with TemporaryDirectory() as d:
            root=Path(d);source=root/'source'
            source_run(source,106000,steps=3,width=4,height=4,occupancy=0)
            study.run_source(root/'out',source,1,3)
            for line in (root/'out/paired-steps.jsonl').read_text().splitlines():
                row=json.loads(line);self.assertEqual(row['on'],row['off'])
            with self.assertRaisesRegex(ValueError,'boolean'):
                study.production_step({}, {}, {}, 1)
            with self.assertRaisesRegex(ValueError,'interval'):
                study.run_source(root/'bad',source,True,3)

    def test_cancellation_and_gain_loss_matrix(self):
        from copy import deepcopy
        initial=[dict(energy=20),dict(energy=20),None,None]
        common=dict(driven=dict(inputs=[],energy_after=40,interaction=dict(bonds=[],spent=0,transfers=[dict(amount=1)])),directions=[0]*4,mutation_tickets=[],interaction_units=initial)
        on=dict(common,units=[dict(energy=15),dict(energy=20),dict(energy=0),None],material=dict(dissolved=[],proposals=[dict(source=0,reason='formed'),dict(source=1,reason='occupied')]))
        off=deepcopy(on);off['driven']['interaction']['transfers']=[]
        off['material']['proposals']=[dict(source=0,reason='occupied'),dict(source=1,reason='formed')]
        metrics=study.measure(initial,on,off,16)
        self.assertEqual(metrics['birth_gains'],1);self.assertEqual(metrics['birth_losses'],1)
        self.assertEqual(metrics['differences']['births'],0)
        self.assertEqual(metrics['counts']['on']['energy_eligible'],2)
        self.assertEqual(metrics['counts']['on']['births'],1)
        on['driven']['interaction']['transfers']=[]
        with self.assertRaisesRegex(ValueError,'zero transfer'):study.measure(initial,on,off,16)

    def test_after_source_budget_and_partial_failure(self):
        sources=[dict(seed=s,drive=250,mutation=m) for s,m in product(range(96000,96005),(0,100))]
        for mode in ('time','failure'):
            with self.subTest(mode=mode), TemporaryDirectory() as d:
                root=Path(d)/'out';calls=[]
                def run(directory,source):
                    calls.append(source)
                    if len(calls)==2:raise ValueError('audit failed')
                    directory.mkdir();summary=dict(steps=400)
                    study.save(directory/'metadata.json',dict(status='complete'))
                    study.save(directory/'summary.json',summary)
                    (directory/'paired-steps.jsonl').write_text('')
                    return summary
                def clock():return 2000 if calls and mode=='time' else 0
                with patch.object(study,'OUTPUT',root), patch.object(study.subprocess,'check_output',return_value=''), patch.object(study,'binding_paths',return_value=[]), patch.object(study,'preflight',return_value=(sources,Path(d),{},{})), patch.object(study,'source_bindings',return_value={}), patch.object(study,'check_source_bindings'), patch.object(study,'run_source',side_effect=run), patch.object(study.time,'monotonic',side_effect=clock):
                    if mode=='failure':
                        with self.assertRaisesRegex(ValueError,'audit failed'):study.main()
                    else:study.main()
                meta=study.read(root/'metadata.json')
                self.assertEqual(meta['status'],'time_limit' if mode=='time' else 'failed')
                self.assertEqual(meta['completed_sources'],1)
                self.assertEqual(meta['completed_pairs'],400)
                self.assertEqual(len(study.read(root/'results.json')),1)
                self.assertFalse((root/'summary.json').exists())

    def test_independent_disagreement_fails_and_source_exchange_required(self):
        with TemporaryDirectory() as d:
            root=Path(d);source=root/'source'
            source_run(source,106000,steps=3,width=4,height=4)
            with patch.object(study,'physical_step',return_value={}):
                with self.assertRaisesRegex(ValueError,'independent'):study.run_source(root/'bad',source,1,3)
            self.assertEqual(study.read(root/'bad/metadata.json')['status'],'failed')
            source_run(root/'off',106000,steps=3,width=4,height=4,exchange=False)
            with self.assertRaisesRegex(ValueError,'exchange'):study.run_source(root/'bad-off',root/'off',1,3)
