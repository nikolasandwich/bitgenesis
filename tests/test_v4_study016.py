import copy
import json
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from scripts import run_v4_study016 as runner


class HorizonTests(unittest.TestCase):
    def grid(self):
        result=[]
        for history,seed,mutation,exchange in product((True,False),range(112000,112005),(0,100),(True,False)):
            checkpoints={}
            for tick in runner.CHECKPOINTS:
                fractions={k:None for k in runner.COMPONENT_METRICS}
                checkpoints[str(tick)]=dict(occupied=(seed-112000 if exchange else 0),components=dict(initial_components=0,eligible_components=0,fractions=fractions))
            result.append(dict(history=history,seed=seed,mutation=mutation,exchange=exchange,anchor=100,horizon=400,status='complete',checkpoints=checkpoints))
        return result

    def test_single_anchor_five_source_means_and_null_components(self):
        result=runner.aggregate(self.grid())
        self.assertEqual([len(result[k]) for k in ('cells','pairs','groups')],[32,20,16])
        self.assertEqual(result['groups'][0]['metrics']['occupied'],dict(mean='2',available=5,missing=0))
        self.assertEqual(result['cells'][0]['metrics']['occupied'],dict(mean='2',available=5,missing=0))
        self.assertEqual(result['groups'][0]['metrics']['replacement'],dict(mean=None,available=0,missing=5))
        self.assertEqual(result['pairs'][0]['checkpoints']['400']['occupied']['difference'],'0')

    def test_invalid_grid_failed_nonboolean_and_pair_denominators(self):
        rows=self.grid();cases=[rows[:-1],rows[:-1]+[rows[0]]]
        for key,value in (('status','failed'),('history',1),('exchange',0),('anchor',200),('horizon',100)):
            bad=copy.deepcopy(rows);bad[0][key]=value;cases.append(bad)
        bad=copy.deepcopy(rows);bad[0]['checkpoints']['100']['components']['eligible_components']=1;cases.append(bad)
        bad=copy.deepcopy(rows);bad[0]['checkpoints']['100']['components']['fractions']['continuous']='1';cases.append(bad)
        for bad in cases:
            with self.assertRaises(ValueError):runner.aggregate(bad)

    def test_same_original_anchor_late_replacement_and_broken_reclosure(self):
        def observation(groups):return dict(components=dict(material=groups))
        initial=dict(observation=observation([[0,1],[2]]))
        rows=[dict(tick=1,observation=observation([[0,3],[2]])),dict(tick=2,observation=observation([[3,4],[2]]))]
        records=runner.checkpoint_records(initial,rows,dict(parents=[None,None,None,1,0]),(1,2))
        self.assertFalse(records['1'][0]['primary']);self.assertTrue(records['2'][0]['primary'])
        rows[0]['observation']=observation([[0],[1],[2]])
        rows[1]['observation']=observation([[0,1],[2]])
        records=runner.checkpoint_records(initial,rows,dict(parents=[None,None,None]),(1,2))
        self.assertFalse(records['2'][0]['continuous_closed_multi'])
        self.assertFalse(records['2'][0]['primary'])
        self.assertTrue(records['2'][0]['endpoint_closed_after_break'])
        for first,last in zip(records['1'],records['2']):
            self.assertLessEqual(last['continuous_closed_multi'],first['continuous_closed_multi'])

    def test_prefix_exact_bytes_and_component_records(self):
        with TemporaryDirectory() as tmp:
            new,old=Path(tmp)/'new',Path(tmp)/'old';new.mkdir();old.mkdir()
            for directory in (new,old):
                (directory/'initial.json').write_text('{}\n')
                (directory/'continuity.json').write_text('[]\n')
            prefix=''.join(json.dumps(dict(tick=t))+'\n' for t in range(1,101))
            (old/'steps.jsonl').write_text(prefix);(new/'steps.jsonl').write_text(prefix+'{}\n')
            runner.verify_prefix(new,old,{'100':[]})
            (new/'initial.json').write_text('{}')
            with self.assertRaises(ValueError):runner.verify_prefix(new,old,{'100':[]})
            (new/'initial.json').write_text('{}\n')
            with self.assertRaises(ValueError):runner.verify_prefix(new,old,{'100':[{}]})
            (new/'steps.jsonl').write_text(prefix.replace('1}', '2}',1)+'{}\n')
            with self.assertRaises(ValueError):runner.verify_prefix(new,old,{'100':[]})

    def test_failure_budget_and_exclusive_output(self):
        from contextlib import ExitStack
        with TemporaryDirectory() as tmp:
            for mode in ('failed','time_limit'):
                root=Path(tmp)/mode
                with ExitStack() as stack:
                    stack.enter_context(patch.object(runner,'ROOT',root))
                    stack.enter_context(patch.object(runner.subprocess,'check_output',side_effect=['','revision']))
                    stack.enter_context(patch.object(runner,'bindings',return_value={}))
                    call=stack.enter_context(patch.object(runner,'branch_run',side_effect=ValueError('branch failed')))
                    if mode=='failed':
                        with self.assertRaisesRegex(ValueError,'branch failed'):runner.main()
                    else:
                        stack.enter_context(patch.object(runner,'SECONDS',-1));runner.main();call.assert_not_called()
                self.assertEqual(json.loads((root/'metadata.json').read_text())['status'],mode)
                before=(root/'metadata.json').read_bytes()
                with patch.object(runner,'ROOT',root),patch.object(runner.subprocess,'check_output',return_value=''):
                    with self.assertRaises(FileExistsError):runner.main()
                self.assertEqual(before,(root/'metadata.json').read_bytes())

    def test_component_means_keep_five_sources_equal_weight(self):
        rows=self.grid()
        for row in rows:
            for checkpoint in row['checkpoints'].values():
                c=checkpoint['components'];c.update(initial_components=4,eligible_components=3)
                value=('0' if row['seed']==112000 else '1/2') if row['exchange'] else '1/4'
                c['fractions']={k:value for k in runner.COMPONENT_METRICS}
        result=runner.aggregate(rows)
        self.assertEqual(result['cells'][0]['metrics']['replacement'],dict(mean='2/5',available=5,missing=0))
        self.assertEqual(result['groups'][0]['metrics']['replacement'],dict(mean='3/20',available=5,missing=0))
