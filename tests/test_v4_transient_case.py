import copy
import unittest
from scripts import analyze_v4_transient_case as a

PARAMETERS=dict(bond_cost=1,construction_cost=4,copy_cost=1)
def u(e):return dict(energy=e,material=0)

def fixture(kind='birth'):
    if kind=='birth':
        initial=dict(site_ids=[0,1,2,None],units=[u(15),u(3),u(10),None],observation=dict(components=dict(material=[[0,1],[2]])))
        physical=dict(driven=dict(inputs=[dict(site=i,accepted=0,leakage=0) for i in range(4)],interaction=dict(bonds=[[0,1]],transfers=[dict(donor=0,recipient=1,amount=1)])),interaction_units=[u(13),u(3),u(10),None],interaction_components=[[0,1],[2]],material=dict(dissolved=[],proposals=[dict(source=0,target=3,reason='formed',cost=5,parent_energy=4,child_energy=4)]),units=[u(4),u(3),u(10),u(4)])
        row=dict(tick=1,site_ids=[0,1,2,3],physical=physical,observation=dict(components=dict(material=[[0,1,3],[2]])))
        final=dict(parents=[None,None,None,0],death_ticks=[None]*4,site_ids=row['site_ids'],units=physical['units'])
    else:
        initial=dict(site_ids=[0,1,2],units=[u(1),u(5),u(17)],observation=dict(components=dict(material=[[0,1],[2]])))
        physical=dict(driven=dict(inputs=[dict(site=i,accepted=0,leakage=int(i<2)) for i in range(3)],interaction=dict(bonds=[],transfers=[])),interaction_units=[u(0),u(4),u(17)],interaction_components=[[0],[1],[2]],material=dict(dissolved=[0],proposals=[dict(source=2,target=0,reason='formed',cost=5,parent_energy=6,child_energy=6)]),units=[u(6),u(4),u(6)])
        row=dict(tick=1,site_ids=[3,1,2],physical=physical,observation=dict(components=dict(material=[[3,1],[2]])))
        final=dict(parents=[None,None,None,2],death_ticks=[1,None,None,None],site_ids=row['site_ids'],units=physical['units'])
    return initial,[row],final

class TransientCaseTests(unittest.TestCase):
    def test_internal_transfer_copy_and_future_birth(self):
        biographies,steps=a.analyze(*fixture(),PARAMETERS,anchor_members=(0,1))
        step=steps[0];ledger=step['ledger']
        self.assertEqual((ledger['population_before'],ledger['population_after']),(2,3))
        self.assertEqual((ledger['energy_before'],ledger['energy_after']),(18,11))
        self.assertEqual((ledger['inflow'],ledger['outflow'],ledger['internal_transfer']),(1,1,1))
        self.assertEqual((ledger['formation_cost'],ledger['energy_to_child'],ledger['birth_energy']),(5,4,4))
        self.assertEqual([m['identity'] for m in step['members']],[0,1])
        self.assertEqual(step['births'],[dict(identity=3,parent=0,founder=0,site=3,energy=4)])
        self.assertEqual((step['interaction']['population'],step['material_final']['population']),(2,3))
        self.assertEqual(biographies[-1],dict(identity=3,parent=0,founder=0,site=3,born_tick=1,died_tick=None,original=False))
    def test_dead_site_replaced_by_foreign_child(self):
        biographies,steps=a.analyze(*fixture('foreign'),PARAMETERS,anchor_members=(0,1))
        step=steps[0]
        self.assertEqual(step['deaths'],[0]);self.assertEqual(step['births'],[])
        self.assertEqual(step['members'][0]['energy_after'],0)
        self.assertEqual(step['members'][0]['status'],'dead')
        self.assertEqual(step['material_final'],dict(state='mixed',population=1,original_survivors=1,destination_components=1,outsiders=1))
        self.assertEqual((step['interaction']['population'],step['material_final']['population']),(2,1))
        self.assertEqual(biographies[0]['died_tick'],1)
        self.assertEqual([b['identity'] for b in biographies],[0,1])
    def test_energy_identity_and_parameters_tamper(self):
        for change in (lambda x:x[1][0]['physical']['units'][0].update(energy=5),lambda x:x[1][0]['site_ids'].__setitem__(3,2),lambda x:x[2]['parents'].__setitem__(3,2),lambda x:x[1][0]['physical']['material']['proposals'][0].update(cost=4)):
            args=copy.deepcopy(fixture());change(args)
            with self.assertRaises(ValueError):a.analyze(*args,PARAMETERS,anchor_members=(0,1))
    def test_complete_extinction_is_retained(self):
        initial,rows,final=fixture('foreign');row=rows[0]
        initial['units'][1]=u(1);row['physical']['interaction_units'][1]=u(0);row['physical']['material']['dissolved']=[0,1]
        row['physical']['units'][1]=None;row['site_ids'][1]=None
        row['observation']['components']['material']=[[3],[2]];final['death_ticks'][1]=1
        biographies,steps=a.analyze(initial,rows,final,PARAMETERS,anchor_members=(0,1))
        self.assertEqual(steps[0]['material_final']['state'],'extinct')
        self.assertEqual(steps[0]['ledger']['energy_after'],0)
        self.assertEqual(steps[0]['deaths'],[0,1])

    def test_boundary_transfer_is_not_internal(self):
        initial,rows,final=fixture();p=rows[0]['physical']
        p['driven']['interaction']['transfers'].append(dict(donor=2,recipient=1,amount=2))
        p['interaction_units'][1]['energy']+=2;p['units'][1]['energy']+=2
        p['interaction_units'][2]['energy']-=2;p['units'][2]['energy']-=2
        _,steps=a.analyze(initial,rows,final,PARAMETERS,anchor_members=(0,1))
        ledger=steps[0]['ledger']
        self.assertEqual((ledger['inflow'],ledger['outflow'],ledger['internal_transfer']),(3,1,1))
        self.assertEqual(ledger['energy_after'],13)

    def test_summary_requires_two_complete_fixed_branches(self):
        biographies,steps=a.analyze(*fixture(),PARAMETERS,anchor_members=(0,1))
        base=dict(history=False,seed=112000,mutation=0,component=7,anchor_members=[8,9],biographies=biographies,steps=[dict(copy.deepcopy(steps[0]),tick=t) for t in range(1,401)])
        branches=[dict(copy.deepcopy(base),exchange=e) for e in (True,False)]
        summary=a.summarize(branches)
        self.assertEqual([x['exchange'] for x in summary],[True,False])
        self.assertEqual([s['tick'] for s in summary[0]['selected_steps']],[20,21,22])
        self.assertEqual(summary[0]['births'],400)
        for change in (lambda x:x.pop(),lambda x:x.reverse(),lambda x:x[0].update(exchange=1),lambda x:x[0]['steps'].pop(),lambda x:x[0].update(seed=112001)):
            bad=copy.deepcopy(branches);change(bad)
            with self.assertRaises(ValueError):a.summarize(bad)

    def test_failed_run_preserves_first_branch(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        biographies,steps=a.analyze(*fixture(),PARAMETERS,anchor_members=(0,1))
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp);(source/'steps.jsonl').write_text('{}\n'*400)
            out=source/'output';cases=[dict(exchange=e,directory=str(source),source=str(source)) for e in (True,False)]
            initial=dict(observation=dict(components=dict(material=[[]]*7+[[8,9]])))
            with patch.object(a,'OUTPUT',out),patch.object(a.subprocess,'check_output',side_effect=['','fixture-commit']),patch('scripts.transient_case_inputs.bindings',return_value={'fixture':'unchanged'}),patch('scripts.transient_case_inputs.cases',return_value=cases),patch('scripts.transient_case_inputs.read',return_value=initial),patch.object(a,'analyze',side_effect=[(biographies,steps),ValueError('second branch failed')]):
                with self.assertRaisesRegex(ValueError,'second branch failed'):a.main()
            meta=json.loads((out/'metadata.json').read_text())
            self.assertEqual(meta['status'],'failed');self.assertEqual(meta['completed_branches'],1)
            self.assertEqual(meta['input_sha256'],meta['input_sha256_after'])
            self.assertEqual(len(json.loads((out/'branches.json').read_text())),1)
            self.assertEqual(meta['new_simulation_steps'],0)
            self.assertEqual(meta['reused_independent_sources'],1)
            with patch.object(a,'OUTPUT',out),patch.object(a.subprocess,'check_output',return_value=''):
                with self.assertRaises(FileExistsError):a.main()
